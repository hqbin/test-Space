//! Screen recording over the scrcpy video stream.
//!
//! Why not `adb shell screenrecord`: the platform utility caps a single capture
//! at 180 s (documented default *and* maximum), so it can never reach a 5 minute
//! recording. Here we start a **second, independent** scrcpy-server instance
//! (`scid` gives it its own abstract socket name, so it coexists with the screen
//! mirror), consume the H.264 stream on the host and mux it into an MP4 locally.
//! The stream itself has no duration limit.
//!
//! Like `screenrecord`, this needs no root: scrcpy-server runs as the `shell`
//! user via `app_process`.

use std::fs::File;
use std::io::{ErrorKind, Read, Seek, SeekFrom, Write};
use std::net::TcpStream;
use std::process::{Command, Stdio};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{Arc, Mutex};
use std::time::{Duration, Instant};

use serde::Serialize;
use tauri::Emitter;

#[cfg(target_os = "windows")]
use std::os::windows::process::CommandExt;

/// PTS / config flags carried in the scrcpy frame header.
const PACKET_FLAG_CONFIG: u64 = 1 << 63;
const PACKET_FLAG_KEY_FRAME: u64 = 1 << 62;

const MOVIE_TIMESCALE: u32 = 1000;
const MEDIA_TIMESCALE: u32 = 1_000_000; // microseconds: scrcpy PTS unit

#[derive(Serialize, Clone)]
pub struct RecordSummary {
    pub path: String,
    pub duration_ms: u64,
    pub frames: u32,
    pub size_bytes: u64,
    pub width: u32,
    pub height: u32,
    /// True when the stream ended on its own (device unplugged / server died).
    pub interrupted: bool,
}

pub struct RecorderEntry {
    pub serial: String,
    pub port: u16,
    pub scid: u32,
    pub width: u32,
    pub height: u32,
    pub stop: Arc<AtomicBool>,
    pub done: Arc<AtomicBool>,
    pub result: Arc<Mutex<Option<Result<RecordSummary, String>>>>,
}

fn adb_cmd() -> Command {
    let mut cmd = Command::new("adb");
    #[cfg(target_os = "windows")]
    {
        cmd.creation_flags(0x08000000);
    }
    cmd
}

// ── MP4 muxing ───────────────────────────────────────────────────────────────

fn be32(v: u32) -> [u8; 4] {
    v.to_be_bytes()
}

fn be16(v: u16) -> [u8; 2] {
    v.to_be_bytes()
}

fn mkbox(kind: &[u8; 4], body: &[u8]) -> Vec<u8> {
    let mut v = Vec::with_capacity(8 + body.len());
    v.extend_from_slice(&be32((8 + body.len()) as u32));
    v.extend_from_slice(kind);
    v.extend_from_slice(body);
    v
}

fn fullbox(kind: &[u8; 4], version: u8, flags: u32, body: &[u8]) -> Vec<u8> {
    let mut b = Vec::with_capacity(4 + body.len());
    b.push(version);
    b.push(((flags >> 16) & 0xff) as u8);
    b.push(((flags >> 8) & 0xff) as u8);
    b.push((flags & 0xff) as u8);
    b.extend_from_slice(body);
    mkbox(kind, &b)
}

fn unity_matrix() -> Vec<u8> {
    let m: [u32; 9] = [0x0001_0000, 0, 0, 0, 0x0001_0000, 0, 0, 0, 0x4000_0000];
    let mut v = Vec::with_capacity(36);
    for x in m {
        v.extend_from_slice(&be32(x));
    }
    v
}

fn build_avcc(sps: &[u8], pps: &[u8]) -> Vec<u8> {
    let profile = sps.get(1).copied().unwrap_or(0x42);
    let compat = sps.get(2).copied().unwrap_or(0);
    let level = sps.get(3).copied().unwrap_or(0x1e);
    let mut body = Vec::with_capacity(11 + sps.len() + pps.len());
    body.push(1); // configurationVersion
    body.push(profile);
    body.push(compat);
    body.push(level);
    body.push(0xfc | 3); // lengthSizeMinusOne = 3 (4-byte NAL length)
    body.push(0xe0 | 1); // numOfSequenceParameterSets = 1
    body.extend_from_slice(&be16(sps.len() as u16));
    body.extend_from_slice(sps);
    body.push(1); // numOfPictureParameterSets
    body.extend_from_slice(&be16(pps.len() as u16));
    body.extend_from_slice(pps);
    mkbox(b"avcC", &body)
}

/// Split an Annex-B buffer into NAL payload slices (start codes stripped).
fn split_nals(buf: &[u8]) -> Vec<&[u8]> {
    let mut out = Vec::new();
    let mut i = 0usize;
    let mut start: Option<usize> = None;
    while i + 3 <= buf.len() {
        let sc4 = i + 4 <= buf.len() && buf[i] == 0 && buf[i + 1] == 0 && buf[i + 2] == 0 && buf[i + 3] == 1;
        let sc3 = buf[i] == 0 && buf[i + 1] == 0 && buf[i + 2] == 1;
        if sc4 || sc3 {
            if let Some(s) = start {
                let mut e = i;
                while e > s && buf[e - 1] == 0 {
                    e -= 1;
                }
                if e > s {
                    out.push(&buf[s..e]);
                }
            }
            i += if sc4 { 4 } else { 3 };
            start = Some(i);
        } else {
            i += 1;
        }
    }
    if let Some(s) = start {
        let mut e = buf.len();
        while e > s && buf[e - 1] == 0 {
            e -= 1;
        }
        if e > s {
            out.push(&buf[s..e]);
        }
    }
    out
}

struct SampleMeta {
    size: u32,
    pts: u64,
    key: bool,
}

// ── SPS parsing (width/height) ───────────────────────────────────────────────
// The MP4 `avc1` box must describe the real coded size. The size announced in
// the codec-meta header can differ when scrcpy downsizes on encoder error, so
// the SPS is authoritative.

struct BitReader<'a> {
    data: &'a [u8],
    bit: usize,
}

impl<'a> BitReader<'a> {
    fn new(data: &'a [u8]) -> Self {
        Self { data, bit: 0 }
    }
    fn bit(&mut self) -> Option<u32> {
        if self.bit / 8 >= self.data.len() {
            return None;
        }
        let byte = self.data[self.bit / 8];
        let v = (byte >> (7 - (self.bit % 8))) & 1;
        self.bit += 1;
        Some(v as u32)
    }
    fn bits(&mut self, n: usize) -> Option<u32> {
        let mut v = 0u32;
        for _ in 0..n {
            v = (v << 1) | self.bit()?;
        }
        Some(v)
    }
    fn ue(&mut self) -> Option<u32> {
        let mut zeros = 0;
        while self.bit()? == 0 {
            zeros += 1;
            if zeros > 31 {
                return None;
            }
        }
        let rest = self.bits(zeros)?;
        Some((1u32 << zeros) - 1 + rest)
    }
    fn se(&mut self) -> Option<i32> {
        let v = self.ue()? as i64;
        let val = if v % 2 == 1 { (v + 1) / 2 } else { -(v / 2) };
        Some(val as i32)
    }
}

/// Remove 00 00 03 emulation-prevention bytes (without the NAL start code).
fn unescape_rbsp(nal: &[u8]) -> Vec<u8> {
    let mut out = Vec::with_capacity(nal.len());
    let mut zeros = 0;
    for &b in nal {
        if zeros >= 2 && b == 3 {
            zeros = 0;
            continue;
        }
        if b == 0 {
            zeros += 1;
        } else {
            zeros = 0;
        }
        out.push(b);
    }
    out
}

fn skip_scaling_list(r: &mut BitReader, size: usize) -> Option<()> {
    let mut last: i32 = 8;
    let mut next: i32 = 8;
    for _ in 0..size {
        if next != 0 {
            let delta = r.se()?;
            next = (last + delta + 256) % 256;
        }
        if next != 0 {
            last = next;
        }
    }
    Some(())
}

fn parse_sps_dimensions(sps: &[u8]) -> Option<(u32, u32)> {
    if sps.len() < 4 {
        return None;
    }
    let rbsp = unescape_rbsp(&sps[1..]); // skip NAL header byte
    let mut r = BitReader::new(&rbsp);
    let profile_idc = r.bits(8)?;
    r.bits(8)?; // constraint flags + reserved
    r.bits(8)?; // level_idc
    r.ue()?; // seq_parameter_set_id

    let mut chroma_format_idc = 1u32;
    if matches!(profile_idc, 100 | 110 | 122 | 244 | 44 | 83 | 86 | 118 | 128 | 138 | 139 | 134 | 135) {
        chroma_format_idc = r.ue()?;
        if chroma_format_idc == 3 {
            r.bit()?; // separate_colour_plane_flag
        }
        r.ue()?; // bit_depth_luma_minus8
        r.ue()?; // bit_depth_chroma_minus8
        r.bit()?; // qpprime_y_zero_transform_bypass_flag
        if r.bit()? == 1 {
            let count = if chroma_format_idc != 3 { 8 } else { 12 };
            for i in 0..count {
                if r.bit()? == 1 {
                    skip_scaling_list(&mut r, if i < 6 { 16 } else { 64 })?;
                }
            }
        }
    }

    r.ue()?; // log2_max_frame_num_minus4
    let poc_type = r.ue()?;
    if poc_type == 0 {
        r.ue()?; // log2_max_pic_order_cnt_lsb_minus4
    } else if poc_type == 1 {
        r.bit()?; // delta_pic_order_always_zero_flag
        r.se()?; // offset_for_non_ref_pic
        r.se()?; // offset_for_top_to_bottom_field
        let n = r.ue()?;
        for _ in 0..n.min(256) {
            r.se()?;
        }
    }
    r.ue()?; // max_num_ref_frames
    r.bit()?; // gaps_in_frame_num_value_allowed_flag

    let width_mbs = r.ue()?.checked_add(1)?;
    let height_map_units = r.ue()?.checked_add(1)?;
    let frame_mbs_only = r.bit()?;
    if frame_mbs_only == 0 {
        r.bit()?; // mb_adaptive_frame_field_flag
    }
    r.bit()?; // direct_8x8_inference_flag

    let (mut crop_left, mut crop_right, mut crop_top, mut crop_bottom) = (0u32, 0u32, 0u32, 0u32);
    if r.bit()? == 1 {
        crop_left = r.ue()?;
        crop_right = r.ue()?;
        crop_top = r.ue()?;
        crop_bottom = r.ue()?;
    }

    let (sub_w, sub_h) = match chroma_format_idc {
        1 => (2u32, 2u32),
        2 => (2, 1),
        _ => (1, 1),
    };
    let frame_factor = 2 - frame_mbs_only;
    let width = width_mbs * 16 - (crop_left + crop_right) * sub_w;
    let height = height_map_units * 16 * frame_factor - (crop_top + crop_bottom) * sub_h * frame_factor;
    if width == 0 || height == 0 || width > 16384 || height > 16384 {
        return None;
    }
    Some((width, height))
}


/// Minimal progressive MP4 writer: a single H.264 video track.
/// Samples are streamed straight into `mdat`; the index (`moov`) is appended on
/// stop, so memory use stays flat no matter how long the recording runs.
struct Mp4Muxer {
    file: File,
    width: u32,
    height: u32,
    sps: Vec<u8>,
    pps: Vec<u8>,
    samples: Vec<SampleMeta>,
    data_offset: u64,
    data_end: u64,
}

impl Mp4Muxer {
    fn create(path: &str, width: u32, height: u32) -> Result<Self, String> {
        let mut file = File::create(path).map_err(|e| format!("create {}: {}", path, e))?;

        let mut ftyp_body = Vec::new();
        ftyp_body.extend_from_slice(b"isom");
        ftyp_body.extend_from_slice(&be32(0x200));
        for brand in [b"isom", b"iso2", b"avc1", b"mp41"] {
            ftyp_body.extend_from_slice(brand);
        }
        let ftyp = mkbox(b"ftyp", &ftyp_body);
        file.write_all(&ftyp).map_err(|e| e.to_string())?;
        // mdat size is patched in finish()
        file.write_all(&be32(0)).map_err(|e| e.to_string())?;
        file.write_all(b"mdat").map_err(|e| e.to_string())?;

        let data_offset = (ftyp.len() + 8) as u64;
        Ok(Self {
            file,
            width,
            height,
            sps: Vec::new(),
            pps: Vec::new(),
            samples: Vec::new(),
            data_offset,
            data_end: data_offset,
        })
    }

    fn set_codec(&mut self, sps: Vec<u8>, pps: Vec<u8>) {
        if !sps.is_empty() {
            if let Some((w, h)) = parse_sps_dimensions(&sps) {
                self.width = w;
                self.height = h;
            }
            self.sps = sps;
        }
        if !pps.is_empty() {
            self.pps = pps;
        }
    }

    fn has_codec(&self) -> bool {
        !self.sps.is_empty() && !self.pps.is_empty()
    }

    fn push_sample(&mut self, pts: u64, key: bool, annex_b: &[u8]) -> Result<(), String> {
        let nals = split_nals(annex_b);
        if nals.is_empty() {
            return Ok(());
        }
        let mut avcc = Vec::with_capacity(annex_b.len() + 4 * nals.len());
        for nal in nals {
            if nal.is_empty() {
                continue;
            }
            avcc.extend_from_slice(&be32(nal.len() as u32));
            avcc.extend_from_slice(nal);
        }
        if avcc.is_empty() {
            return Ok(());
        }
        self.file.write_all(&avcc).map_err(|e| format!("write sample: {}", e))?;
        let size = avcc.len() as u32;
        self.data_end += size as u64;
        self.samples.push(SampleMeta { size, pts, key });
        Ok(())
    }

    fn finish(mut self) -> Result<(u64, u32), String> {
        let n = self.samples.len();
        if n == 0 {
            return Err("没有采集到任何视频帧".to_string());
        }
        if !self.has_codec() {
            return Err("未收到 H.264 编码参数 (SPS/PPS)".to_string());
        }

        // Durations from PTS deltas; the last sample reuses the previous delta.
        let mut durations: Vec<u32> = Vec::with_capacity(n);
        for i in 0..n {
            let d = if i + 1 < n {
                let delta = self.samples[i + 1].pts.saturating_sub(self.samples[i].pts);
                if delta == 0 { 1 } else { delta.min(5_000_000) as u32 }
            } else if i > 0 {
                durations[i - 1]
            } else {
                33_333
            };
            durations.push(d);
        }
        let total_dur: u64 = durations.iter().map(|d| *d as u64).sum();
        let movie_dur = ((total_dur / 1000) as u32).max(1);

        let mut stts_entries: Vec<(u32, u32)> = Vec::new();
        for d in &durations {
            match stts_entries.last_mut() {
                Some((cnt, last)) if *last == *d => *cnt += 1,
                _ => stts_entries.push((1, *d)),
            }
        }
        let mut stts_body = Vec::new();
        stts_body.extend_from_slice(&be32(stts_entries.len() as u32));
        for (cnt, d) in &stts_entries {
            stts_body.extend_from_slice(&be32(*cnt));
            stts_body.extend_from_slice(&be32(*d));
        }

        let keys: Vec<u32> = self
            .samples
            .iter()
            .enumerate()
            .filter(|(_, s)| s.key)
            .map(|(i, _)| i as u32 + 1)
            .collect();
        let mut stss_body = Vec::new();
        stss_body.extend_from_slice(&be32(keys.len() as u32));
        for k in &keys {
            stss_body.extend_from_slice(&be32(*k));
        }

        let mut stsc_body = Vec::new();
        stsc_body.extend_from_slice(&be32(1)); // one chunk holds every sample
        stsc_body.extend_from_slice(&be32(1));
        stsc_body.extend_from_slice(&be32(n as u32));
        stsc_body.extend_from_slice(&be32(1));

        let mut stsz_body = Vec::new();
        stsz_body.extend_from_slice(&be32(0));
        stsz_body.extend_from_slice(&be32(n as u32));
        for s in &self.samples {
            stsz_body.extend_from_slice(&be32(s.size));
        }

        if self.data_offset > u32::MAX as u64 {
            return Err("录制文件超出 MP4 32 位偏移上限".to_string());
        }
        let mut stco_body = Vec::new();
        stco_body.extend_from_slice(&be32(1));
        stco_body.extend_from_slice(&be32(self.data_offset as u32));

        let mut avc1_body = Vec::new();
        avc1_body.extend_from_slice(&[0u8; 6]); // reserved
        avc1_body.extend_from_slice(&be16(1)); // data_reference_index
        avc1_body.extend_from_slice(&be16(0));
        avc1_body.extend_from_slice(&be16(0));
        avc1_body.extend_from_slice(&[0u8; 12]);
        avc1_body.extend_from_slice(&be16(self.width as u16));
        avc1_body.extend_from_slice(&be16(self.height as u16));
        avc1_body.extend_from_slice(&be32(0x0048_0000)); // 72 dpi
        avc1_body.extend_from_slice(&be32(0x0048_0000));
        avc1_body.extend_from_slice(&be32(0));
        avc1_body.extend_from_slice(&be16(1)); // frame_count
        avc1_body.extend_from_slice(&[0u8; 32]); // compressorname
        avc1_body.extend_from_slice(&be16(0x0018)); // depth
        avc1_body.extend_from_slice(&be16(0xffff)); // pre_defined
        avc1_body.extend_from_slice(&build_avcc(&self.sps, &self.pps));

        let mut stsd_body = Vec::new();
        stsd_body.extend_from_slice(&be32(1));
        stsd_body.extend_from_slice(&mkbox(b"avc1", &avc1_body));

        let stbl = mkbox(
            b"stbl",
            &[
                fullbox(b"stsd", 0, 0, &stsd_body),
                fullbox(b"stts", 0, 0, &stts_body),
                fullbox(b"stss", 0, 0, &stss_body),
                fullbox(b"stsc", 0, 0, &stsc_body),
                fullbox(b"stsz", 0, 0, &stsz_body),
                fullbox(b"stco", 0, 0, &stco_body),
            ]
            .concat(),
        );

        let vmhd = fullbox(b"vmhd", 0, 1, &[0u8; 8]);
        let url = fullbox(b"url ", 0, 1, &[]);
        let mut dref_body = Vec::new();
        dref_body.extend_from_slice(&be32(1));
        dref_body.extend_from_slice(&url);
        let dinf = mkbox(b"dinf", &fullbox(b"dref", 0, 0, &dref_body));
        let minf = mkbox(b"minf", &[vmhd, dinf, stbl].concat());

        let mut mdhd_body = Vec::new();
        mdhd_body.extend_from_slice(&be32(0));
        mdhd_body.extend_from_slice(&be32(0));
        mdhd_body.extend_from_slice(&be32(MEDIA_TIMESCALE));
        mdhd_body.extend_from_slice(&be32(total_dur as u32));
        mdhd_body.extend_from_slice(&be16(0x55c4)); // 'und'
        mdhd_body.extend_from_slice(&be16(0));
        let mdhd = fullbox(b"mdhd", 0, 0, &mdhd_body);

        let mut hdlr_body = Vec::new();
        hdlr_body.extend_from_slice(&be32(0));
        hdlr_body.extend_from_slice(b"vide");
        hdlr_body.extend_from_slice(&[0u8; 12]);
        hdlr_body.extend_from_slice(b"VideoHandler\0");
        let hdlr = fullbox(b"hdlr", 0, 0, &hdlr_body);

        let mdia = mkbox(b"mdia", &[mdhd, hdlr, minf].concat());

        let mut tkhd_body = Vec::new();
        tkhd_body.extend_from_slice(&be32(0));
        tkhd_body.extend_from_slice(&be32(0));
        tkhd_body.extend_from_slice(&be32(1)); // track_id
        tkhd_body.extend_from_slice(&be32(0));
        tkhd_body.extend_from_slice(&be32(movie_dur));
        tkhd_body.extend_from_slice(&[0u8; 8]);
        tkhd_body.extend_from_slice(&be16(0)); // layer
        tkhd_body.extend_from_slice(&be16(0)); // alternate_group
        tkhd_body.extend_from_slice(&be16(0)); // volume
        tkhd_body.extend_from_slice(&be16(0));
        tkhd_body.extend_from_slice(&unity_matrix());
        tkhd_body.extend_from_slice(&be32(self.width << 16));
        tkhd_body.extend_from_slice(&be32(self.height << 16));
        let tkhd = fullbox(b"tkhd", 0, 0x7, &tkhd_body);

        let trak = mkbox(b"trak", &[tkhd, mdia].concat());

        let mut mvhd_body = Vec::new();
        mvhd_body.extend_from_slice(&be32(0));
        mvhd_body.extend_from_slice(&be32(0));
        mvhd_body.extend_from_slice(&be32(MOVIE_TIMESCALE));
        mvhd_body.extend_from_slice(&be32(movie_dur));
        mvhd_body.extend_from_slice(&be32(0x0001_0000)); // rate
        mvhd_body.extend_from_slice(&be16(0x0100)); // volume
        mvhd_body.extend_from_slice(&[0u8; 10]);
        mvhd_body.extend_from_slice(&unity_matrix());
        mvhd_body.extend_from_slice(&[0u8; 24]);
        mvhd_body.extend_from_slice(&be32(2)); // next_track_id
        let mvhd = fullbox(b"mvhd", 0, 0, &mvhd_body);

        let moov = mkbox(b"moov", &[mvhd, trak].concat());

        self.file.write_all(&moov).map_err(|e| e.to_string())?;
        let mdat_size = (8 + (self.data_end - self.data_offset)) as u32;
        self.file
            .seek(SeekFrom::Start(32))
            .map_err(|e| e.to_string())?;
        self.file.write_all(&be32(mdat_size)).map_err(|e| e.to_string())?;
        self.file.flush().map_err(|e| e.to_string())?;
        Ok((total_dur / 1000, n as u32))
    }
}

// ── Stream plumbing ──────────────────────────────────────────────────────────

/// Read exactly `n` bytes, but stay responsive to the stop flag.
/// `Ok(None)` means "stopped by the user before the read completed".
fn read_n(stream: &mut TcpStream, n: usize, stop: &AtomicBool) -> Result<Option<Vec<u8>>, String> {
    let mut out = Vec::with_capacity(n);
    let mut tmp = vec![0u8; 64 * 1024];
    while out.len() < n {
        if stop.load(Ordering::Relaxed) {
            return Ok(None);
        }
        let want = (n - out.len()).min(tmp.len());
        match stream.read(&mut tmp[..want]) {
            Ok(0) => return Err("设备端视频流已断开".to_string()),
            Ok(k) => out.extend_from_slice(&tmp[..k]),
            Err(e) if matches!(e.kind(), ErrorKind::WouldBlock | ErrorKind::TimedOut | ErrorKind::Interrupted) => continue,
            Err(e) => return Err(format!("读取视频流失败: {}", e)),
        }
    }
    Ok(Some(out))
}

/// Retry an adb device operation while adbd is still coming back.
///
/// `adb root` (and `adb remount`, which restarts adbd) tears the daemon down and
/// brings it back a moment later, so an operation issued right after the user
/// rooted the device can fail with "device offline" / "no devices/emulators
/// found". Those are transient — wait for adbd instead of failing the start.
fn with_device_ready<T>(mut op: impl FnMut() -> Result<T, String>) -> Result<T, String> {
    let deadline = Instant::now() + Duration::from_secs(15);
    loop {
        match op() {
            Ok(v) => return Ok(v),
            Err(e) => {
                let transient = e.contains("offline")
                    || e.contains("no devices")
                    || e.contains("failed to get feature set")
                    || e.contains("device not found")
                    || e.contains("closed");
                if !transient || Instant::now() >= deadline {
                    return Err(e);
                }
                std::thread::sleep(Duration::from_millis(400));
            }
        }
    }
}

fn push_server(serial: &str, jar_path: &str) -> Result<(), String> {
    let output = adb_cmd()
        .args(["-s", serial, "push", jar_path, "/data/local/tmp/scrcpy-server.jar"])
        .output()
        .map_err(|e| format!("adb push 失败: {}", e))?;
    if !output.status.success() {
        let err = String::from_utf8_lossy(&output.stderr).to_string();
        return Err(if err.trim().is_empty() {
            String::from_utf8_lossy(&output.stdout).to_string()
        } else {
            err
        });
    }
    Ok(())
}

fn set_forward(serial: &str, port: u16, socket_name: &str) -> Result<(), String> {
    let addr = format!("tcp:{}", port);
    let target = format!("localabstract:{}", socket_name);
    let output = adb_cmd()
        .args(["-s", serial, "forward", &addr, &target])
        .output()
        .map_err(|e| format!("adb forward 失败: {}", e))?;
    if !output.status.success() {
        return Err(String::from_utf8_lossy(&output.stderr).to_string());
    }
    Ok(())
}

fn remove_forward(serial: &str, port: u16) {
    let addr = format!("tcp:{}", port);
    let _ = adb_cmd()
        .args(["-s", serial, "forward", "--remove", &addr])
        .output();
}

/// Kill only *our* server instance (matched by scid) so the mirror keeps running.
fn kill_server(serial: &str, scid: u32) {
    let pattern = format!("scid={:08x}", scid);
    let _ = adb_cmd()
        .args(["-s", serial, "shell", &format!("pkill -f {}", pattern)])
        .output();
}

// ── Public entry points ──────────────────────────────────────────────────────

pub fn start(
    app: tauri::AppHandle,
    window_label: String,
    serial: String,
    out_path: String,
    jar_path: String,
    max_size: u16,
    video_bit_rate: u32,
    max_fps: u8,
    port: u16,
    scid: u32,
) -> Result<RecorderEntry, String> {
    if jar_path.is_empty() {
        return Err("未找到内置 scrcpy-server（应用资源缺失）".to_string());
    }
    with_device_ready(|| push_server(&serial, &jar_path))?;

    let socket_name = format!("scrcpy_{:08x}", scid);
    remove_forward(&serial, port);
    with_device_ready(|| set_forward(&serial, port, &socket_name))?;

    let args = format!(
        "CLASSPATH=/data/local/tmp/scrcpy-server.jar app_process / \
         com.genymobile.scrcpy.Server 3.3.4 log_level=error \
         max_size={} video_bit_rate={} max_fps={} \
         tunnel_forward=true audio=false control=false \
         send_device_meta=false send_codec_meta=true \
         stay_awake=true downsize_on_error=true cleanup=true \
         scid={:08x}",
        max_size, video_bit_rate, max_fps, scid
    );

    let mut child = adb_cmd()
        .args(["-s", &serial, "shell", &args])
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(|e| format!("启动 scrcpy-server 失败: {}", e))?;

    // Drain server output so the pipe never fills up.
    if let Some(mut err) = child.stderr.take() {
        std::thread::spawn(move || {
            let mut buf = [0u8; 4096];
            while let Ok(k) = err.read(&mut buf) {
                if k == 0 {
                    break;
                }
            }
        });
    }
    if let Some(mut out) = child.stdout.take() {
        std::thread::spawn(move || {
            let mut buf = [0u8; 4096];
            while let Ok(k) = out.read(&mut buf) {
                if k == 0 {
                    break;
                }
            }
        });
    }

    // Connect to the forwarded port (server needs a moment to boot).
    // adb accepts the local TCP connect before the device-side socket exists, so
    // the dummy byte is the real readiness signal: retry until it arrives.
    let addr = format!("127.0.0.1:{}", port);
    let sa = addr.parse().map_err(|_| format!("无效端口: {}", port))?;
    let deadline = Instant::now() + Duration::from_secs(20);
    let mut stream: Option<TcpStream> = None;
    while Instant::now() < deadline {
        match TcpStream::connect_timeout(&sa, Duration::from_secs(1)) {
            Ok(mut s) => {
                s.set_nodelay(true).ok();
                s.set_read_timeout(Some(Duration::from_millis(1500))).ok();
                let mut dummy = [0u8; 1];
                match s.read_exact(&mut dummy) {
                    Ok(()) => {
                        stream = Some(s);
                        break;
                    }
                    Err(_) => std::thread::sleep(Duration::from_millis(300)),
                }
            }
            Err(_) => std::thread::sleep(Duration::from_millis(300)),
        }
    }
    let mut stream = match stream {
        Some(s) => s,
        None => {
            kill_server(&serial, scid);
            remove_forward(&serial, port);
            let _ = child.kill();
            return Err("连接 scrcpy-server 超时（20s）".to_string());
        }
    };

    let stop = Arc::new(AtomicBool::new(false));

    // Codec meta: fourcc(4) + width(4) + height(4)
    let mut header = [0u8; 12];
    if let Err(e) = stream.read_exact(&mut header) {
        kill_server(&serial, scid);
        remove_forward(&serial, port);
        let _ = child.kill();
        return Err(format!("读取编码信息失败: {}", e));
    }
    let width = u32::from_be_bytes([header[4], header[5], header[6], header[7]]);
    let height = u32::from_be_bytes([header[8], header[9], header[10], header[11]]);
    if width == 0 || height == 0 {
        kill_server(&serial, scid);
        remove_forward(&serial, port);
        let _ = child.kill();
        return Err("设备返回了无效的分辨率".to_string());
    }

    // Short timeout from here on so the capture loop stays responsive to `stop`.
    stream
        .set_read_timeout(Some(Duration::from_millis(400)))
        .map_err(|e| e.to_string())?;

    let muxer = match Mp4Muxer::create(&out_path, width, height) {
        Ok(m) => m,
        Err(e) => {
            kill_server(&serial, scid);
            remove_forward(&serial, port);
            let _ = child.kill();
            return Err(e);
        }
    };

    let done = Arc::new(AtomicBool::new(false));
    let result: Arc<Mutex<Option<Result<RecordSummary, String>>>> = Arc::new(Mutex::new(None));

    let entry = RecorderEntry {
        serial: serial.clone(),
        port,
        scid,
        width,
        height,
        stop: stop.clone(),
        done: done.clone(),
        result: result.clone(),
    };

    let thread_out = out_path.clone();
    std::thread::spawn(move || {
        let summary = capture_loop(&mut stream, muxer, &stop, &thread_out);
        // Always tear the device side down, whatever happened.
        kill_server(&serial, scid);
        remove_forward(&serial, port);
        let _ = child.kill();
        let _ = child.wait();

        // Publish the state *before* notifying: the UI may retry recording the
        // instant it sees the event, and `adb_record_start` must already see a
        // finished (evictable) session instead of a "still recording" one.
        let idle_end = !stop.load(Ordering::Relaxed);
        let snapshot = summary.clone();
        *result.lock().unwrap() = Some(summary);
        done.store(true, Ordering::Relaxed);

        // Only sessions that ended *on their own* notify the UI. A user-initiated
        // stop already carries its outcome back through `adb_record_stop`.
        if idle_end {
            match snapshot {
                // Stream ended without a stop request: tell the UI to reset.
                Ok(s) => {
                    let _ = app.emit_to(&window_label, "record:auto-stopped", s);
                }
                // Nothing usable was written (device vanished before the first
                // frame, e.g. `adb root` restarting adbd): emit explicitly so the
                // UI does not stay stuck in the "recording" state.
                Err(e) => {
                    // Let the `adb_record_start` invocation settle on the UI
                    // first, otherwise its `isRecording = true` overwrites the
                    // reset.
                    std::thread::sleep(Duration::from_millis(250));
                    let _ = app.emit_to(&window_label, "record:failed", e);
                }
            }
        }
    });

    Ok(entry)
}

fn capture_loop(
    stream: &mut TcpStream,
    mut muxer: Mp4Muxer,
    stop: &AtomicBool,
    out_path: &str,
) -> Result<RecordSummary, String> {
    let mut samples: u32 = 0;
    let mut interrupted = false;

    loop {
        if stop.load(Ordering::Relaxed) {
            break;
        }
        let header = match read_n(stream, 12, stop) {
            Ok(Some(h)) => h,
            Ok(None) => break,
            Err(e) => {
                interrupted = true;
                if samples == 0 {
                    let _ = std::fs::remove_file(out_path);
                    return Err(e);
                }
                eprintln!("[recorder] stream ended: {}", e);
                break;
            }
        };
        let flags = u64::from_be_bytes([
            header[0], header[1], header[2], header[3], header[4], header[5], header[6], header[7],
        ]);
        let size = u32::from_be_bytes([header[8], header[9], header[10], header[11]]) as usize;
        if size == 0 || size > 32 * 1024 * 1024 {
            interrupted = true;
            break;
        }
        let payload = match read_n(stream, size, stop) {
            Ok(Some(p)) => p,
            Ok(None) => break,
            Err(e) => {
                interrupted = true;
                if samples == 0 {
                    let _ = std::fs::remove_file(out_path);
                    return Err(e);
                }
                eprintln!("[recorder] payload read ended: {}", e);
                break;
            }
        };

        if flags & PACKET_FLAG_CONFIG != 0 {
            // Codec config packet: SPS/PPS for the avcC box.
            if !muxer.has_codec() {
                let (mut sps, mut pps) = (Vec::new(), Vec::new());
                for nal in split_nals(&payload) {
                    match nal[0] & 0x1f {
                        7 => sps = nal.to_vec(),
                        8 => pps = nal.to_vec(),
                        _ => {}
                    }
                }
                if !sps.is_empty() && !pps.is_empty() {
                    muxer.set_codec(sps, pps);
                }
            }
            continue;
        }

        let pts = flags & 0x3fff_ffff_ffff_ffff;
        let key = flags & PACKET_FLAG_KEY_FRAME != 0;

        // Late SPS/PPS can arrive in-band; grab them if the config packet was missed.
        if !muxer.has_codec() {
            let (mut sps, mut pps) = (Vec::new(), Vec::new());
            for nal in split_nals(&payload) {
                match nal[0] & 0x1f {
                    7 => sps = nal.to_vec(),
                    8 => pps = nal.to_vec(),
                    _ => {}
                }
            }
            if !sps.is_empty() && !pps.is_empty() {
                muxer.set_codec(sps, pps);
            }
        }

        if let Err(e) = muxer.push_sample(pts, key, &payload) {
            interrupted = true;
            eprintln!("[recorder] mux error: {}", e);
            break;
        }
        samples += 1;
    }

    let (mw, mh) = (muxer.width, muxer.height);
    let (duration_ms, frames) = muxer.finish()?;
    let size_bytes = std::fs::metadata(out_path).map(|m| m.len()).unwrap_or(0);
    Ok(RecordSummary {
        path: out_path.to_string(),
        duration_ms,
        frames,
        size_bytes,
        width: mw,
        height: mh,
        interrupted,
    })
}

/// Release the device side of a session that already finished on its own.
///
/// A recording can end without `stop()`: the device rebooted, `adb root` /
/// `adb remount` restarted adbd (which kills the hosted scrcpy-server and drops
/// the forward), or the server crashed. Such an entry is dead but still
/// registered, so it has to be evicted before a new recording can start.
/// Returns immediately — the capture thread is already done, so there is
/// nothing to wait for.
pub fn discard(entry: RecorderEntry) {
    entry.stop.store(true, Ordering::Relaxed);
    kill_server(&entry.serial, entry.scid);
    remove_forward(&entry.serial, entry.port);
}

/// Signal the capture thread to stop and wait for it to finalise the MP4.
pub fn stop(entry: RecorderEntry) -> Result<RecordSummary, String> {
    entry.stop.store(true, Ordering::Relaxed);
    let deadline = Instant::now() + Duration::from_secs(20);
    while Instant::now() < deadline {
        if entry.done.load(Ordering::Relaxed) {
            break;
        }
        std::thread::sleep(Duration::from_millis(100));
    }
    if !entry.done.load(Ordering::Relaxed) {
        // Stuck thread: at least release the device side and the port.
        kill_server(&entry.serial, entry.scid);
        remove_forward(&entry.serial, entry.port);
        return Err("停止录制超时".to_string());
    }
    let taken = entry.result.lock().unwrap().take();
    match taken {
        Some(r) => r,
        None => Err("录制结果缺失".to_string()),
    }
}
