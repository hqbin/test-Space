use std::io::{Read, Write};
use std::net::TcpStream;
use std::process::{Command, Stdio};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use std::time::Duration;

#[cfg(target_os = "windows")]
use std::os::windows::process::CommandExt;

use tauri::Emitter;

fn adb_cmd() -> Command {
    let mut cmd = Command::new("adb");
    #[cfg(target_os = "windows")]
    { cmd.creation_flags(0x08000000); }
    cmd
}

pub fn push_server(serial: &str, jar_path: &str) -> Result<(), String> {
    let output =     adb_cmd()
        .args(["-s", serial, "push", jar_path, "/data/local/tmp/scrcpy-server.jar"])
        .output()
        .map_err(|e| format!("ADB push failed: {}", e))?;
    if !output.status.success() {
        let err = String::from_utf8_lossy(&output.stderr);
        let msg = if err.is_empty() {
            String::from_utf8_lossy(&output.stdout).to_string()
        } else {
            err.to_string()
        };
        return Err(msg);
    }
    Ok(())
}

pub fn setup_forward(serial: &str, port: u16) -> Result<(), String> {
    let addr = format!("tcp:{}", port);
    let output =     adb_cmd()
        .args(["-s", serial, "forward", &addr, "localabstract:scrcpy"])
        .output()
        .map_err(|e| format!("ADB forward failed: {}", e))?;
    if !output.status.success() {
        return Err(String::from_utf8_lossy(&output.stderr).to_string());
    }
    Ok(())
}

pub fn remove_forward(serial: &str, port: u16) {
    let addr = format!("tcp:{}", port);
    let _ =     adb_cmd()
        .args(["-s", serial, "forward", "--remove", &addr])
        .output();
}

pub fn start_server(serial: &str, max_size: u16, video_bit_rate: u32, max_fps: u8) -> Result<(), String> {
    let args = format!(
        "CLASSPATH=/data/local/tmp/scrcpy-server.jar app_process / \
         com.genymobile.scrcpy.Server 3.3.4 log_level=info \
         max_size={max_size} video_bit_rate={video_bit_rate} max_fps={max_fps} \
         tunnel_forward=true raw_stream=true \
         send_device_meta=false send_codec_meta=false \
         audio=false control=false cleanup=true"
    );

    let mut child =     adb_cmd()
        .args(["-s", serial, "shell", &args])
        .stderr(Stdio::piped())
        .stdout(Stdio::piped())
        .spawn()
        .map_err(|e| format!("Failed to start server: {}", e))?;

    let stderr = child.stderr.take();
    let stdout = child.stdout.take();

    std::thread::spawn(move || {
        if let Some(mut err) = stderr {
            let mut buf = String::new();
            use std::io::Read;
            let _ = err.read_to_string(&mut buf);
            if !buf.is_empty() {
                eprintln!("[scrcpy-server stderr] {}", buf.trim());
            }
        }
        if let Some(mut out) = stdout {
            let mut buf = String::new();
            use std::io::Read;
            let _ = out.read_to_string(&mut buf);
            if !buf.is_empty() {
                eprintln!("[scrcpy-server stdout] {}", buf.trim());
            }
        }
        let _ = child.wait();
    });

    Ok(())
}

/// Build avcC decoder config from SPS/PPS NAL units (Annex B format).
fn build_avcc(sps: &[u8], pps: &[u8]) -> Vec<u8> {
    let profile = sps.get(1).copied().unwrap_or(0x42);
    let compatibility = sps.get(2).copied().unwrap_or(0);
    let level = sps.get(3).copied().unwrap_or(0x1e);
    let mut avcc = Vec::with_capacity(7 + sps.len() + pps.len());
    avcc.push(1); // version
    avcc.push(profile);
    avcc.push(compatibility);
    avcc.push(level);
    avcc.push(0xfc | 3); // 6 bits reserved + 2 bits nal size length - 1 (=3 means 4 bytes)
    avcc.push(0xe0 | 1); // 3 bits reserved + num_sps
    avcc.extend_from_slice(&(sps.len() as u16).to_be_bytes());
    avcc.extend_from_slice(sps);
    avcc.push(1); // num_pps
    avcc.extend_from_slice(&(pps.len() as u16).to_be_bytes());
    avcc.extend_from_slice(pps);
    avcc
}

pub fn connect_and_stream(
    app_handle: tauri::AppHandle,
    running: Arc<AtomicBool>,
    port: u16,
    win_label: &str,
    on_frame: tauri::ipc::Channel<Vec<u8>>,
) -> Result<(), String> {
    let addr = format!("127.0.0.1:{}", port);
    let mut stream: Option<TcpStream> = None;
    for i in 0..30 {
        if !running.load(Ordering::Relaxed) { return Ok(()); }
        match TcpStream::connect_timeout(&addr.parse().unwrap(), Duration::from_secs(1)) {
            Ok(s) => { stream = Some(s); break; }
            Err(_) => {
                if i == 29 { return Err("Server not ready after 30s".into()); }
                std::thread::sleep(Duration::from_millis(500));
            }
        }
    }

    let mut stream = stream.unwrap();

    // Read dummy byte, send handshake (0x00 = no flags)
    let mut dummy = [0u8; 1];
    let _ = stream.read_exact(&mut dummy);
    let _ = stream.write_all(&[0x00]);
    let _ = stream.flush();

    // Read raw H264 byte stream in chunks and parse NAL units
    let mut sps = Vec::new();
    let mut pps = Vec::new();
    let mut config_sent = false;
    let mut raw_buf = vec![0u8; 0];
    let mut temp_buf = vec![0u8; 256 * 1024]; // 256KB read buffer
    let mut pending: Vec<u8> = Vec::new();

    let _ = app_handle.emit_to(win_label, "mirror:ready", "h264");

    loop {
        if !running.load(Ordering::Relaxed) { break; }

        let n = match stream.read(&mut temp_buf) {
            Ok(0) => break,
            Ok(n) => n,
            Err(_) => break,
        };

        raw_buf.extend_from_slice(&temp_buf[..n]);

        // Parse NAL units from the buffer using Annex B start codes
        let mut consumed = 0;
        let mut pos = 0;
        while pos + 4 <= raw_buf.len() {
            let start = find_nal_start(&raw_buf, pos);
            if start + 4 > raw_buf.len() { break; }

            let sc_len = if start + 3 < raw_buf.len() && raw_buf[start] == 0 && raw_buf[start+1] == 0 && raw_buf[start+2] == 0 && raw_buf[start+3] == 1 {
                4
            } else {
                3
            };

            let nal_data_start = start + sc_len;
            if nal_data_start >= raw_buf.len() { break; }
            let nal_type = raw_buf[nal_data_start] & 0x1f;

            let next = find_nal_start(&raw_buf, nal_data_start + 1);
            if next >= raw_buf.len() { break; }

            let is_vcl = nal_type == 1 || nal_type == 5; // slice or IDR

            if !config_sent {
                if nal_type == 7 {
                    sps = raw_buf[nal_data_start..next].to_vec();
                } else if nal_type == 8 {
                    pps = raw_buf[nal_data_start..next].to_vec();
                }
                if !sps.is_empty() && !pps.is_empty() {
                    let avcc = build_avcc(&sps, &pps);
                    let mut config_payload = vec![0xFF]; // marker for decoder config
                    config_payload.extend_from_slice(&avcc);
                    let _ = on_frame.send(config_payload);
                    config_sent = true;
                }
            }

            // Convert NAL to AVCC format (4-byte BE length prefix + data)
            let nal_len = next - nal_data_start;
            let mut avcc_nal = Vec::with_capacity(4 + nal_len);
            avcc_nal.extend_from_slice(&(nal_len as u32).to_be_bytes());
            avcc_nal.extend_from_slice(&raw_buf[nal_data_start..next]);

            if nal_type == 7 || nal_type == 8 {
                // Buffer SPS/PPS to combine with the next VCL NAL
                pending.extend_from_slice(&avcc_nal);
            } else if is_vcl {
                // Flush pending SPS/PPS + this VCL NAL as one access unit
                let mut combined = std::mem::take(&mut pending);
                combined.extend_from_slice(&avcc_nal);
                let is_key = nal_type == 5;
                // Prepend 1-byte key flag, then send raw bytes directly via Channel
                let mut payload = vec![if is_key { 1 } else { 0 }];
                payload.extend_from_slice(&combined);
                let _ = on_frame.send(payload);
            } else if !config_sent {
                // Before config, buffer everything
                pending.extend_from_slice(&avcc_nal);
            }
            consumed = next;
            pos = next;
        }

        if consumed < raw_buf.len() {
            raw_buf = raw_buf[consumed..].to_vec();
        } else {
            raw_buf.clear();
        }
    }

    if !config_sent {
        return Err("Stream ended before codec config".into());
    }
    Ok(())
}

fn find_nal_start(buf: &[u8], from: usize) -> usize {
    if from + 2 >= buf.len() { return buf.len(); }
    let mut i = from;
    while i + 2 < buf.len() {
        if buf[i] == 0 && buf[i+1] == 0 {
            if buf[i+2] == 1 {
                return i;
            }
            if i + 3 < buf.len() && buf[i+2] == 0 && buf[i+3] == 1 {
                return i;
            }
        }
        i += 1;
    }
    buf.len()
}
