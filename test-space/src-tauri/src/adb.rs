use std::process::Command;
use serde::Serialize;

#[derive(Serialize)]
pub struct DeviceInfo {
    pub serial: String,
    pub status: String,
    pub model: String,
    pub android_version: String,
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

pub fn install_apk(serial: &str, apk_path: &str) -> Result<String, String> {
    let output = Command::new("adb")
        .args(["-s", serial, "install", "-r", apk_path])
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
        std::fs::write(save_path, &output.stdout)
            .map_err(|e| format!("Save screenshot failed: {}", e))?;
        Ok(save_path.to_string())
    } else {
        Err(String::from_utf8_lossy(&output.stderr).to_string())
    }
}
