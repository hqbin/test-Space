use std::process::Command;
use serde::Serialize;

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
    let output = Command::new("adb")
        .args(&full_args)
        .output()
        .map_err(|e| format!("ADB command failed: {}", e))?;
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
    let output = Command::new("adb").args(["devices", "-l"]).output();
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
    let output = Command::new("adb")
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
    if reinstall {
        args.push("-r");
    }
    args.push(apk_path);
    let output = Command::new("adb")
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
    let output = Command::new("adb")
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
    let output = Command::new("adb")
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
    let output = Command::new("adb")
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
    let output = Command::new("adb")
        .args(["-s", serial, "reboot"])
        .output()
        .map_err(|e| format!("ADB reboot failed: {}", e))?;
    if output.status.success() {
        Ok("Reboot command sent".to_string())
    } else {
        Err(String::from_utf8_lossy(&output.stderr).to_string())
    }
}

pub fn screenshot(serial: &str, save_path: &str) -> Result<String, String> {
    let output = Command::new("adb")
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
    let output = Command::new("adb")
        .args(["connect", address])
        .output()
        .map_err(|e| format!("ADB connect failed: {}", e))?;
    Ok(String::from_utf8_lossy(&output.stdout).trim().to_string())
}

pub fn disconnect_device(serial: &str) -> Result<String, String> {
    let output = Command::new("adb")
        .args(["disconnect", serial])
        .output()
        .map_err(|e| format!("ADB disconnect failed: {}", e))?;
    Ok(String::from_utf8_lossy(&output.stdout).trim().to_string())
}

pub fn reboot_recovery(serial: &str) -> Result<String, String> {
    run_adb(serial, &["reboot", "recovery"])?;
    Ok("Rebooting to recovery...".to_string())
}

pub fn reboot_bootloader(serial: &str) -> Result<String, String> {
    run_adb(serial, &["reboot", "bootloader"])?;
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
