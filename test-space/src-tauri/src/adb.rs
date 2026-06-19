use std::process::Command;
use serde::Serialize;
use std::sync::mpsc;
use std::thread;
use std::time::Duration;

#[cfg(target_os = "windows")]
use std::os::windows::process::CommandExt;

fn adb_cmd() -> Command {
    let mut cmd = Command::new("adb");
    #[cfg(target_os = "windows")]
    { cmd.creation_flags(0x08000000); } // CREATE_NO_WINDOW
    cmd
}

#[derive(Serialize)]
pub struct DeviceInfo {
    pub serial: String,
    pub status: String,
    pub model: String,
    pub android_version: String,
}

#[derive(Serialize)]
pub struct DeviceProperties {
    pub model: String,
    pub brand: String,
    pub device: String,
    pub android_version: String,
    pub sdk_version: String,
    pub build_id: String,
    pub build_fingerprint: String,
    pub resolution: String,
    pub density: String,
    pub product: String,
}

fn run_adb(serial: &str, args: &[&str]) -> Result<String, String> {
    let mut full_args = vec!["-s", serial];
    full_args.extend_from_slice(args);
    let (tx, rx) = mpsc::channel();
    let child = adb_cmd()
        .args(&full_args)
        .stdout(std::process::Stdio::piped())
        .stderr(std::process::Stdio::piped())
        .spawn()
        .map_err(|e| format!("Failed to spawn adb: {}", e))?;
    thread::spawn(move || {
        let output = child.wait_with_output();
        let _ = tx.send(output);
    });
    let output = rx
        .recv_timeout(Duration::from_secs(120))
        .map_err(|_| "ADB command timed out (120s)".to_string())?
        .map_err(|e| format!("ADB wait failed: {}", e))?;
    if output.status.success() {
        Ok(String::from_utf8_lossy(&output.stdout).to_string())
    } else {
        let stderr = String::from_utf8_lossy(&output.stderr).to_string();
        if stderr.is_empty() {
            Ok(String::from_utf8_lossy(&output.stdout).to_string())
        } else {
            Err(stderr)
        }
    }
}

fn get_prop(serial: &str, key: &str) -> String {
    run_adb(serial, &["shell", "getprop", key])
        .unwrap_or_default()
        .trim()
        .to_string()
}

pub fn list_devices() -> Vec<DeviceInfo> {
    let output = adb_cmd().args(["devices", "-l"]).output();
    let mut devices = Vec::new();
    if let Ok(out) = output {
        let stdout = String::from_utf8_lossy(&out.stdout);
        for line in stdout.lines().skip(1) {
            let parts: Vec<&str> = line.split_whitespace().collect();
            if parts.len() >= 2 && parts[1] != "offline" {
                let serial = parts[0].to_string();
                let model = parts.iter()
                    .find(|p| p.starts_with("model:"))
                    .map(|p| p[6..].to_string())
                    .unwrap_or_default();
                let android_version = parts.iter()
                    .find(|p| p.starts_with("android_version:"))
                    .map(|p| p[16..].to_string())
                    .unwrap_or_default();
                devices.push(DeviceInfo {
                    serial,
                    status: parts[1].to_string(),
                    model,
                    android_version,
                });
            }
        }
    }
    devices
}

pub fn shell_command(serial: &str, command: &str) -> Result<String, String> {
    let output = adb_cmd()
        .args(["-s", serial, "shell", command])
        .output()
        .map_err(|e| format!("ADB shell failed: {}", e))?;
    if output.status.success() {
        Ok(String::from_utf8_lossy(&output.stdout).to_string())
    } else {
        Err(String::from_utf8_lossy(&output.stderr).to_string())
    }
}

pub fn install_apk(serial: &str, apk_path: &str, reinstall: bool) -> Result<String, String> {
    let mut args = vec!["-s", serial, "install"];
    if reinstall { args.push("-r"); }
    args.push(apk_path);
    let output = adb_cmd()
        .args(&args)
        .output()
        .map_err(|e| format!("ADB install failed: {}", e))?;
    if output.status.success() {
        Ok(String::from_utf8_lossy(&output.stdout).to_string())
    } else {
        Err(String::from_utf8_lossy(&output.stderr).to_string())
    }
}

pub fn uninstall_apk(serial: &str, package: &str) -> Result<String, String> {
    let output = adb_cmd()
        .args(["-s", serial, "uninstall", package])
        .output()
        .map_err(|e| format!("ADB uninstall failed: {}", e))?;
    if output.status.success() {
        Ok(String::from_utf8_lossy(&output.stdout).to_string())
    } else {
        Err(String::from_utf8_lossy(&output.stderr).to_string())
    }
}

pub fn push_file(serial: &str, local: &str, remote: &str) -> Result<String, String> {
    let output = adb_cmd()
        .args(["-s", serial, "push", local, remote])
        .output()
        .map_err(|e| format!("ADB push failed: {}", e))?;
    if output.status.success() {
        Ok(String::from_utf8_lossy(&output.stdout).to_string())
    } else {
        Err(String::from_utf8_lossy(&output.stderr).to_string())
    }
}

pub fn pull_file(serial: &str, remote: &str, local: &str) -> Result<String, String> {
    let output = adb_cmd()
        .args(["-s", serial, "pull", remote, local])
        .output()
        .map_err(|e| format!("ADB pull failed: {}", e))?;
    if output.status.success() {
        Ok(String::from_utf8_lossy(&output.stdout).to_string())
    } else {
        Err(String::from_utf8_lossy(&output.stderr).to_string())
    }
}

pub fn reboot(serial: &str) -> Result<String, String> {
    adb_cmd()
        .args(["-s", serial, "reboot"])
        .spawn()
        .map_err(|e| format!("ADB reboot failed: {}", e))?;
    Ok("Reboot command sent".to_string())
}

pub fn screenshot(serial: &str, save_path: &str) -> Result<String, String> {
    let output = adb_cmd()
        .args(["-s", serial, "exec-out", "screencap", "-p"])
        .output()
        .map_err(|e| format!("ADB screenshot failed: {}", e))?;
    if output.status.success() {
        if save_path.is_empty() {
            use base64::Engine;
            Ok(format!("data:image/png;base64,{}", base64::engine::general_purpose::STANDARD.encode(&output.stdout)))
        } else {
            std::fs::write(save_path, &output.stdout)
                .map_err(|e| format!("Save screenshot failed: {}", e))?;
            Ok(save_path.to_string())
        }
    } else {
        Err(String::from_utf8_lossy(&output.stderr).to_string())
    }
}

pub fn connect_device(address: &str) -> Result<String, String> {
    let output = adb_cmd()
        .args(["connect", address])
        .output()
        .map_err(|e| format!("ADB connect failed: {}", e))?;
    Ok(String::from_utf8_lossy(&output.stdout).trim().to_string())
}

pub fn disconnect_device(serial: &str) -> Result<String, String> {
    let output = adb_cmd()
        .args(["disconnect", serial])
        .output()
        .map_err(|e| format!("ADB disconnect failed: {}", e))?;
    Ok(String::from_utf8_lossy(&output.stdout).trim().to_string())
}

pub fn reboot_recovery(serial: &str) -> Result<String, String> {
    adb_cmd()
        .args(["-s", serial, "reboot", "recovery"])
        .spawn()
        .map_err(|e| format!("ADB reboot recovery failed: {}", e))?;
    Ok("Rebooting to recovery...".to_string())
}

pub fn reboot_bootloader(serial: &str) -> Result<String, String> {
    adb_cmd()
        .args(["-s", serial, "reboot", "bootloader"])
        .spawn()
        .map_err(|e| format!("ADB reboot bootloader failed: {}", e))?;
    Ok("Rebooting to bootloader...".to_string())
}

pub fn root_device(serial: &str) -> Result<String, String> {
    run_adb(serial, &["root"])
}

pub fn remount_device(serial: &str) -> Result<String, String> {
    run_adb(serial, &["remount"])
}

pub fn get_device_properties(serial: &str) -> Result<DeviceProperties, String> {
    Ok(DeviceProperties {
        model: get_prop(serial, "ro.product.model"),
        brand: get_prop(serial, "ro.product.brand"),
        device: get_prop(serial, "ro.product.device"),
        android_version: get_prop(serial, "ro.build.version.release"),
        sdk_version: get_prop(serial, "ro.build.version.sdk"),
        build_id: get_prop(serial, "ro.build.display.id"),
        build_fingerprint: get_prop(serial, "ro.build.fingerprint"),
        resolution: run_adb(serial, &["shell", "wm", "size"]).unwrap_or_default().trim().lines().last().unwrap_or("").trim().to_string(),
        density: run_adb(serial, &["shell", "wm", "density"]).unwrap_or_default().trim().lines().last().unwrap_or("").trim().to_string(),
        product: get_prop(serial, "ro.product.name"),
    })
}

pub fn input_keyevent(serial: &str, keycode: &str) -> Result<String, String> {
    run_adb(serial, &["shell", "input", "keyevent", keycode])?;
    Ok(format!("Key event {} sent", keycode))
}

pub fn input_text(serial: &str, text: &str) -> Result<String, String> {
    let escaped = text.replace(" ", "%s");
    run_adb(serial, &["shell", "input", "text", &escaped])?;
    Ok("Text sent".to_string())
}

pub fn input_tap(serial: &str, x: i32, y: i32) -> Result<String, String> {
    run_adb(serial, &["shell", "input", "tap", &x.to_string(), &y.to_string()])?;
    Ok(format!("Tap at ({}, {})", x, y))
}

pub fn input_swipe(serial: &str, x1: i32, y1: i32, x2: i32, y2: i32, duration: i32) -> Result<String, String> {
    run_adb(serial, &["shell", "input", "swipe", &x1.to_string(), &y1.to_string(), &x2.to_string(), &y2.to_string(), &duration.to_string()])?;
    Ok("Swipe sent".to_string())
}

pub fn get_display_size(serial: &str) -> Result<(u32, u32), String> {
    let output = run_adb(serial, &["shell", "wm", "size"])?;
    // Output: "Physical size: 1080x2400"
    for line in output.lines() {
        if let Some(s) = line.strip_prefix("Physical size: ") {
            if let Some((w, h)) = s.split_once('x') {
                let w = w.trim().parse().map_err(|_| format!("Invalid width: {}", w))?;
                let h = h.trim().parse().map_err(|_| format!("Invalid height: {}", h))?;
                return Ok((w, h));
            }
        }
    }
    Err("Could not parse display size".into())
}

pub fn list_packages(serial: &str, third_party_only: bool) -> Result<Vec<String>, String> {
    let mut args = vec!["shell", "pm", "list", "packages"];
    if third_party_only {
        args.push("-3");
    }
    let output = run_adb(serial, &args)?;
    Ok(output.lines()
        .filter_map(|line| line.strip_prefix("package:").map(|s| s.trim().to_string()))
        .collect())
}

pub fn start_app(serial: &str, package: &str) -> Result<String, String> {
    run_adb(serial, &["shell", "monkey", "-p", package, "-c", "android.intent.category.LAUNCHER", "1"])?;
    Ok(format!("Started {}", package))
}

pub fn stop_app(serial: &str, package: &str) -> Result<String, String> {
    run_adb(serial, &["shell", "am", "force-stop", package])?;
    Ok(format!("Stopped {}", package))
}

pub fn clear_app_data(serial: &str, package: &str) -> Result<String, String> {
    run_adb(serial, &["shell", "pm", "clear", package])?;
    Ok(format!("Cleared data for {}", package))
}

pub fn get_current_app(serial: &str) -> Result<String, String> {
    let output = run_adb(serial, &["shell", "dumpsys", "window", "windows"])?;
    for line in output.lines() {
        if line.contains("mCurrentFocus") || line.contains("mFocusedApp") {
            return Ok(line.trim().to_string());
        }
    }
    Ok("No focused app found".to_string())
}

pub fn logcat_clear(serial: &str) -> Result<String, String> {
    run_adb(serial, &["logcat", "-c"])?;
    Ok("Logcat cleared".to_string())
}

pub fn logcat(serial: &str, buffer: &str, lines: i32) -> Result<String, String> {
    let mut args = vec!["logcat", "-d", "-v", "time"];
    if !buffer.is_empty() {
        args.push("-b");
        args.push(buffer);
    }
    let lines_str;
    if lines > 0 {
        args.push("-t");
        lines_str = lines.to_string();
        args.push(&lines_str);
    }
    run_adb(serial, &args)
}

pub fn list_directory(serial: &str, path: &str) -> Result<String, String> {
    run_adb(serial, &["shell", "ls", "-la", path])
}

pub fn get_app_info(serial: &str, package: &str) -> Result<String, String> {
    run_adb(serial, &["shell", "dumpsys", "package", package])
}

pub fn get_battery_info(serial: &str) -> Result<String, String> {
    run_adb(serial, &["shell", "dumpsys", "battery"])
}

pub fn get_cpu_info(serial: &str) -> Result<String, String> {
    run_adb(serial, &["shell", "top", "-n", "1", "-b"])
}

pub fn get_memory_info(serial: &str) -> Result<String, String> {
    run_adb(serial, &["shell", "cat", "/proc/meminfo"])
}

pub fn logcat_buffer_resize(serial: &str, size_mb: u32) -> Result<String, String> {
    run_adb(serial, &["logcat", "-G", &format!("{}M", size_mb)])
}

pub fn bugreport(serial: &str, save_path: &str) -> Result<String, String> {
    let output = adb_cmd()
        .args(["-s", serial, "bugreport", save_path])
        .output()
        .map_err(|e| format!("ADB bugreport failed: {}", e))?;
    if output.status.success() {
        Ok(save_path.to_string())
    } else {
        Err(String::from_utf8_lossy(&output.stderr).to_string())
    }
}

pub fn dmesg(serial: &str) -> Result<String, String> {
    run_adb(serial, &["shell", "dmesg"])
}

pub fn kill_server() -> Result<String, String> {
    let output = adb_cmd()
        .args(["kill-server"])
        .output()
        .map_err(|e| format!("ADB kill-server failed: {}", e))?;
    if output.status.success() {
        Ok("ADB server killed".to_string())
    } else {
        let stderr = String::from_utf8_lossy(&output.stderr).to_string();
        if stderr.is_empty() {
            Ok("ADB server killed".to_string())
        } else {
            Err(stderr)
        }
    }
}

pub fn start_server() -> Result<String, String> {
    let output = adb_cmd()
        .args(["start-server"])
        .output()
        .map_err(|e| format!("ADB start-server failed: {}", e))?;
    if output.status.success() {
        Ok("ADB server started".to_string())
    } else {
        Err(String::from_utf8_lossy(&output.stderr).to_string())
    }
}

pub fn start_screenrecord(serial: &str, file_path: &str, width: u32, height: u32) -> Result<String, String> {
    adb_cmd()
        .args(["-s", serial, "shell", &format!("nohup screenrecord --size {}x{} {} > /dev/null 2>&1 &", width, height, file_path)])
        .spawn()
        .map_err(|e| format!("Failed to start screenrecord: {}", e))?;
    Ok("Recording started".to_string())
}
