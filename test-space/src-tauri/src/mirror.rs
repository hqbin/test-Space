use std::io::Read;
use std::net::TcpStream;
use std::process::{Command, Stdio};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use std::time::Duration;

#[cfg(target_os = "windows")]
use std::os::windows::process::CommandExt;

use base64::Engine;
use serde::Serialize;
use tauri::Emitter;

fn adb_cmd() -> Command {
    let mut cmd = Command::new("adb");
    #[cfg(target_os = "windows")]
    { cmd.creation_flags(0x08000000); } // CREATE_NO_WINDOW
    cmd
}

#[derive(Serialize)]
struct FramePayload {
    data: String,
    key: bool,
    pts: i64,
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

pub fn setup_forward(serial: &str) -> Result<(), String> {
    let output =     adb_cmd()
        .args(["-s", serial, "forward", "tcp:27183", "tcp:27183"])
        .output()
        .map_err(|e| format!("ADB forward failed: {}", e))?;
    if !output.status.success() {
        return Err(String::from_utf8_lossy(&output.stderr).to_string());
    }
    Ok(())
}

pub fn remove_forward(serial: &str) {
    let _ =     adb_cmd()
        .args(["-s", serial, "forward", "--remove", "tcp:27183"])
        .output();
}

pub fn start_server(serial: &str) -> Result<(), String> {
    let args = "CLASSPATH=/data/local/tmp/scrcpy-server.jar app_process / com.genymobile.scrcpy.Server 3.3.4 log_level=info max_size=1280 video_bit_rate=4000000 max_fps=30 i_frame_interval=1 raw_stream=true send_dummy_byte=true send_codec_meta=true audio=false control=false cleanup=true";

    let mut child =     adb_cmd()
        .args(["-s", serial, "shell", args])
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .spawn()
        .map_err(|e| format!("Failed to start server: {}", e))?;

    // Don't wait, let it run in background
    std::thread::spawn(move || {
        let _ = child.wait();
    });

    Ok(())
}

pub fn connect_and_stream(app_handle: tauri::AppHandle, running: Arc<AtomicBool>) -> Result<(), String> {
    // Retry loop waiting for server to be ready
    let mut stream: Option<TcpStream> = None;
    for i in 0..30 {
        if !running.load(Ordering::Relaxed) { return Ok(()); }
        match TcpStream::connect_timeout(&"127.0.0.1:27183".parse().unwrap(), Duration::from_secs(1)) {
            Ok(s) => { stream = Some(s); break; }
            Err(_) => {
                if i == 29 { return Err("Server not ready after 30s".into()); }
                std::thread::sleep(Duration::from_millis(500));
            }
        }
    }

    let mut stream = stream.unwrap();
    stream.set_read_timeout(Some(Duration::from_secs(3))).ok();

    // Read dummy byte (device info / version)
    let mut dummy = [0u8; 1];
    let _ = stream.read_exact(&mut dummy);

    let mut len_buf = [0u8; 4];
    let mut config_sent = false;
    let start_time = std::time::Instant::now();

    while running.load(Ordering::Relaxed) {
        // If config never arrived within 5s of loop start, return error to trigger fallback
        if !config_sent && start_time.elapsed() > Duration::from_secs(5) {
            return Err("Codec config not received within 5s".into());
        }

        match stream.read_exact(&mut len_buf) {
            Ok(()) => {}
            Err(_) => { break; }
        }

        let frame_len = u32::from_le_bytes(len_buf) as usize;
        if frame_len == 0 || frame_len > 10 * 1024 * 1024 { break; }

        let mut frame_data = vec![0u8; frame_len];
        if stream.read_exact(&mut frame_data).is_err() { break; }
        if frame_data.is_empty() { continue; }

        let packet_type = frame_data[0];

        match packet_type {
            0x00 => {
                if !config_sent {
                    let b64 = base64::engine::general_purpose::STANDARD.encode(&frame_data[1..]);
                    let _ = app_handle.emit("mirror:config", &b64);
                    config_sent = true;
                }
            }
            0x01 => {
                if frame_data.len() < 9 { continue; }
                let pts = i64::from_le_bytes(
                    frame_data[1..9].try_into().unwrap_or([0u8; 8])
                );
                let nal_data = &frame_data[9..];
                if nal_data.is_empty() { continue; }

                let is_key = if nal_data.len() >= 5 && nal_data[0] == 0 && nal_data[1] == 0 && nal_data[2] == 0 && nal_data[3] == 1 {
                    (nal_data[4] & 0x1f) == 5 || (nal_data[4] & 0x1f) == 7
                } else if nal_data.len() >= 5 {
                    let nal_len = u32::from_be_bytes(nal_data[0..4].try_into().unwrap_or([0; 4])) as usize;
                    if nal_len > 0 && nal_data.len() >= 8 {
                        (nal_data[4] & 0x1f) == 5 || (nal_data[4] & 0x1f) == 7
                    } else {
                        (nal_data[0] & 0x1f) == 5 || (nal_data[0] & 0x1f) == 7
                    }
                } else {
                    (nal_data[0] & 0x1f) == 5
                };

                let b64 = base64::engine::general_purpose::STANDARD.encode(nal_data);
                let payload = FramePayload { data: b64, key: is_key, pts };
                let _ = app_handle.emit("mirror:frame", &payload);
            }
            _ => {}
        }
    }

    // If we exited without config, signal fallback
    if !config_sent {
        return Err("Stream ended before codec config".into());
    }

    Ok(())
}
