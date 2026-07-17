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
    let stdout = String::from_utf8_lossy(&output.stdout).to_string();
    let stderr = String::from_utf8_lossy(&output.stderr).to_string();
    let mut result = stdout;
    if !stderr.is_empty() {
        if !result.is_empty() { result.push('\n'); }
        result.push_str(&stderr);
    }
    if output.status.success() || !result.is_empty() {
        Ok(result)
    } else {
        Err(stderr)
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

#[derive(Serialize)]
pub struct PerfSnapshot {
    pub cpu_total: f64,
    pub mem_total_kb: u64,
    pub mem_free_kb: u64,
    pub mem_avail_kb: u64,
    pub swap_total_kb: u64,
    pub swap_free_kb: u64,
    pub zram_total_kb: u64,
    pub storage_total_kb: u64,
    pub storage_used_kb: u64,
    pub storage_avail_kb: u64,
    pub procs: Vec<PerfProcess>,
}

#[derive(Serialize, Clone)]
pub struct PerfProcess {
    pub pid: u32,
    pub name: String,
    pub pss_kb: u64,
    pub cpu_percent: f64,
}

fn parse_kb_val(line: &str) -> u64 {
    // line format: "MemTotal:        8388608 kB"  or  "MemTotal:       1000"
    let parts: Vec<&str> = line.split_whitespace().collect();
    if parts.len() >= 2 {
        let val = parts[1].parse::<u64>().unwrap_or(0);
        if parts.len() >= 3 && parts[2] == "kB" { val } else { val }
    } else { 0 }
}

pub fn get_perf_snapshot(serial: &str, watch_app: Option<&str>) -> Result<PerfSnapshot, String> {
    // Collect meminfo, top, df, and ps in a single shell call.
    // Use `ps -A` (not `-o PID,PSS,NAME` which is unsupported on many Android devices).
    let combined = shell_command(serial, "cat /proc/meminfo 2>/dev/null; echo '---TOP---'; top -n 1 -b 2>/dev/null; echo '---DF---'; df /data 2>/dev/null; echo '---PROC---'; ps -A 2>/dev/null")?;

    let mut mem_total_kb: u64 = 0;
    let mut mem_free_kb: u64 = 0;
    let mut mem_avail_kb: u64 = 0;
    let mut swap_total_kb: u64 = 0;
    let mut swap_free_kb: u64 = 0;

    let mut cpu_total: f64 = 0.0;
    let mut core_count: f64 = 1.0; // number of CPU cores, derived from %cpu line
    let mut storage_total_kb: u64 = 0;
    let mut storage_used_kb: u64 = 0;
    let mut storage_avail_kb: u64 = 0;
    let mut zram_total_kb: u64 = 0;

    // PID -> (name, pss_kb) — primary source is dumpsys meminfo (accurate PSS)
    let mut pid_to_pss: std::collections::HashMap<u32, (String, u64)> = std::collections::HashMap::new();
    // PID -> cpu_percent — from top output
    let mut pid_to_cpu: std::collections::HashMap<u32, f64> = std::collections::HashMap::new();
    // Names seen in top output (for processes not in dumpsys meminfo)
    let mut top_names: std::collections::HashMap<u32, String> = std::collections::HashMap::new();

    let mut section = "meminfo";

    for line in combined.lines() {
        match line.trim() {
            "---TOP---" => { section = "top"; continue; }
            "---DF---" => { section = "df"; continue; }
            "---PROC---" => { section = "proc"; continue; }
            _ => {}
        }

        match section {
            "meminfo" => {
                if line.starts_with("MemTotal:") { mem_total_kb = parse_kb_val(line); }
                else if line.starts_with("MemFree:") { mem_free_kb = parse_kb_val(line); }
                else if line.starts_with("MemAvailable:") { mem_avail_kb = parse_kb_val(line); }
                else if line.starts_with("SwapTotal:") { swap_total_kb = parse_kb_val(line); }
                else if line.starts_with("SwapFree:") { swap_free_kb = parse_kb_val(line); }
            }
            "top" => {
                let trimmed = line.trim();

                // Parse total CPU from line like:
                //   "400%cpu 103%user 0%nice 19%sys 274%idle 0%iow 3%irq 0%sirq 0%host"
                // cpu_total = (total_capacity - idle) / total_capacity * 100
                if trimmed.contains("%cpu") && trimmed.contains("%idle") {
                    let mut total_capacity = 0.0f64;
                    let mut idle_val = 0.0f64;
                    for word in trimmed.split_whitespace() {
                        if word.ends_with("%cpu") {
                            let cleaned = word.trim_end_matches("cpu").trim_end_matches('%');
                            if let Ok(v) = cleaned.parse::<f64>() { total_capacity = v; }
                        } else if word.ends_with("%idle") {
                            let cleaned = word.trim_end_matches("idle").trim_end_matches('%');
                            if let Ok(v) = cleaned.parse::<f64>() { idle_val = v; }
                        }
                    }
                    if total_capacity > 0.0 {
                        cpu_total = ((total_capacity - idle_val) / total_capacity * 100.0).clamp(0.0, 100.0);
                        // Derive core count: "400%cpu" means 4 cores (400/100)
                        core_count = (total_capacity / 100.0).max(1.0);
                    }
                }

                // Skip header line: "  PID USER  PR  NI VIRT  RES  SHR S[%CPU] %MEM  TIME+ ARGS"
                if trimmed.starts_with("PID") && trimmed.contains("USER") { continue; }

                // Parse per-process: "  2033 system  20  0  1.3G  98M  63M  S  96.7  5.0  79:54.56  com.app"
                // Column positions (0-indexed): 0=PID, 1=USER, 2=PR, 3=NI, 4=VIRT, 5=RES, 6=SHR,
                //   7=S(state), 8=%CPU, 9=%MEM, 10=TIME+, 11+=ARGS
                let parts: Vec<&str> = trimmed.split_whitespace().collect();
                if parts.len() >= 11 {
                    if let Ok(pid) = parts[0].parse::<u32>() {
                        if pid > 0 {
                            if let Ok(cpu_val) = parts[8].parse::<f64>() {
                                if cpu_val >= 0.0 && cpu_val <= 800.0 {
                                    // Normalize per-process CPU to 0-100% by dividing by core count.
                                    // Android `top` reports per-process CPU relative to a single core,
                                    // so a process using 2 full cores on a 4-core device shows 200%.
                                    // Dividing by core_count gives the percentage of total device CPU.
                                    let normalized_cpu = (cpu_val / core_count).clamp(0.0, 100.0);
                                    // Command name is the last token (Android package names have no spaces)
                                    let cmd = parts[parts.len() - 1].trim();
                                    if !cmd.is_empty() && !cmd.starts_with('[') {
                                        pid_to_cpu.insert(pid, normalized_cpu);
                                        top_names.insert(pid, cmd.to_string());
                                    }
                                }
                            }
                        }
                    }
                }
            }
            "df" => {
                // df /data: "Filesystem  1K-blocks  Used  Available  Use%  Mounted on"
                //           "/dev/block/xxx  8388608  4194304  4194304  50%  /data"
                if line.starts_with('/') || line.contains("/data") {
                    let parts: Vec<&str> = line.split_whitespace().collect();
                    if parts.len() >= 4 {
                        storage_total_kb = parts[1].parse::<u64>().unwrap_or(0);
                        storage_used_kb = parts[2].parse::<u64>().unwrap_or(0);
                        storage_avail_kb = parts[3].parse::<u64>().unwrap_or(0);
                    }
                }
            }
            "proc" => {
                // ps -A format: "USER  PID  PPID  VSIZE  RSS  WCHAN  ...  STATE  NAME"
                // Example: "system  1428  555  1930600  344660  do_epoll_wait  0  S  com.whaletv.launcher"
                // We only use this as a fallback for name/PID mapping; PSS comes from dumpsys meminfo.
                let trimmed = line.trim();
                if trimmed.is_empty() || trimmed.starts_with("USER") { continue; }
                let parts: Vec<&str> = trimmed.split_whitespace().collect();
                if parts.len() >= 8 {
                    // USER=0, PID=1
                    if let Ok(pid) = parts[1].parse::<u32>() {
                        if pid > 0 {
                            let name = parts[parts.len() - 1].trim().to_string();
                            if !name.is_empty() && !name.starts_with('[') {
                                // Use RSS as approximate PSS if dumpsys doesn't have it
                                let rss_kb = parts[4].parse::<u64>().unwrap_or(0);
                                pid_to_pss.entry(pid).or_insert((name, rss_kb));
                            }
                        }
                    }
                }
            }
            _ => {}
        }
    }

    // Fallback for total CPU: use dumpsys cpuinfo if top parsing failed
    if cpu_total == 0.0 {
        if let Ok(cpuinfo_out) = shell_command(serial, "dumpsys cpuinfo 2>/dev/null") {
            for line in cpuinfo_out.lines() {
                let trimmed = line.trim();
                if trimmed.contains("% TOTAL:") || trimmed.contains("% total:") {
                    if let Some(pct) = trimmed.split('%').next() {
                        cpu_total = pct.trim().parse::<f64>().unwrap_or(0.0).clamp(0.0, 100.0);
                    }
                }
            }
        }
    }

    // Get accurate PSS from dumpsys meminfo (overrides ps RSS values)
    if let Ok(dumpsys_out) = shell_command(serial, "dumpsys meminfo 2>/dev/null") {
        for line in dumpsys_out.lines() {
            let trimmed = line.trim();
            // ZRAM line: "ZRAM: 123456K physical used for 78901K in swap (512000K total swap)"
            if trimmed.contains("ZRAM") {
                for word in trimmed.split_whitespace() {
                    let cleaned = word.replace(',', "");
                    let cleaned = cleaned.trim_end_matches('K').trim_end_matches("kB");
                    if let Ok(v) = cleaned.parse::<u64>() {
                        if v > zram_total_kb { zram_total_kb = v; }
                    }
                }
            }
            // Process PSS line: "    400,056K: com.whaletv.launcher (pid 1428 / activities)"
            // Note: PSS values may contain commas (e.g., "400,056K") which must be stripped.
            if trimmed.contains("(pid") {
                let tokens: Vec<&str> = trimmed.split_whitespace().collect();
                if !tokens.is_empty() {
                    // Strip commas: "400,056K:" -> "400056K:"
                    let first_clean = tokens[0].replace(',', "");
                    let first = first_clean
                        .trim_end_matches(|c: char| c == 'K' || c == 'k' || c == 'B' || c == 'b' || c == ':');
                    if let Ok(size_kb) = first.parse::<u64>() {
                        if size_kb > 0 {
                            // Name is between PSS value and "(pid"
                            let name_parts: Vec<&str> = tokens.iter().skip(1)
                                .take_while(|t| !t.starts_with("(pid"))
                                .copied()
                                .collect();
                            let name = name_parts.join(" ");
                            if !name.is_empty() {
                                let pid = tokens.iter().find(|t| t.starts_with("(pid"))
                                    .and_then(|t| t.strip_prefix("(pid"))
                                    .and_then(|s| s.trim_end_matches(')').trim().parse::<u32>().ok())
                                    .unwrap_or(0);
                                if pid > 0 {
                                    pid_to_pss.insert(pid, (name, size_kb));
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    // Build final procs list: merge PSS (from dumpsys) with CPU (from top)
    let mut procs: Vec<PerfProcess> = Vec::new();

    // First, add all processes that have PSS data
    for (pid, (name, pss_kb)) in &pid_to_pss {
        let cpu_percent = pid_to_cpu.get(pid).copied().unwrap_or(0.0);
        procs.push(PerfProcess {
            pid: *pid,
            name: name.clone(),
            pss_kb: *pss_kb,
            cpu_percent,
        });
    }

    // Also add processes from top that have CPU but no PSS (e.g., short-lived processes)
    for (pid, name) in &top_names {
        if !pid_to_pss.contains_key(pid) {
            let cpu_percent = pid_to_cpu.get(pid).copied().unwrap_or(0.0);
            if cpu_percent > 0.0 {
                procs.push(PerfProcess {
                    pid: *pid,
                    name: name.clone(),
                    pss_kb: 0,
                    cpu_percent,
                });
            }
        }
    }

    // Deduplicate by name (keep entry with highest PSS)
    let mut deduped: std::collections::HashMap<String, PerfProcess> = std::collections::HashMap::new();
    for p in procs.drain(..) {
        let entry = deduped.entry(p.name.clone()).or_insert(p.clone());
        if p.pss_kb > entry.pss_kb || (p.pss_kb == entry.pss_kb && p.cpu_percent > entry.cpu_percent) {
            *entry = p;
        }
    }
    procs = deduped.into_values().collect();

    // If a watch_app is specified, extract it from procs before truncation so it's
    // always retained in the result even if it's not in top 40 PSS or top 10 CPU.
    // This is critical for single-app monitoring: without this, the user-selected
    // app may be dropped during truncation and the single-app chart will be empty.
    let watch_proc: Option<PerfProcess> = if let Some(name) = watch_app {
        let name = name.trim();
        if !name.is_empty() {
            // Match by exact name, prefix (e.g. "com.app" matches "com.app:service"), or partial
            let idx = procs.iter().position(|p| {
                p.name == name
                || p.name.starts_with(&format!("{}:", name))
                || p.name.contains(name)
            });
            idx.map(|i| procs.remove(i))
        } else {
            None
        }
    } else {
        None
    };

    // Keep top 40 by PSS plus top 10 by CPU (not already included) so that both the
    // memory chart and the CPU chart on the frontend have enough data. Sorting by
    // PSS alone would drop high-CPU-but-low-PSS processes before they reach the UI,
    // which prevented new high-CPU apps from pushing the lowest one out of Top N.
    procs.sort_by(|a, b| b.pss_kb.cmp(&a.pss_kb));
    let pss_keep = 40.min(procs.len());
    let mut kept: Vec<PerfProcess> = procs.drain(..pss_keep).collect();

    // Fill remaining slots with highest-CPU processes not already kept
    let kept_names: std::collections::HashSet<String> =
        kept.iter().map(|p| p.name.clone()).collect();
    procs.sort_by(|a, b| {
        b.cpu_percent
            .partial_cmp(&a.cpu_percent)
            .unwrap_or(std::cmp::Ordering::Equal)
    });
    for p in procs.iter() {
        if kept.len() >= 50 {
            break;
        }
        if !kept_names.contains(&p.name) {
            kept.push(p.clone());
        }
    }
    // Re-add watch_app if it was extracted and is not already in kept.
    // This guarantees the single-app chart always has data when the app is running.
    if let Some(wp) = watch_proc {
        if !kept.iter().any(|p| p.name == wp.name) {
            kept.push(wp);
        }
    }
    procs = kept;

    Ok(PerfSnapshot {
        cpu_total,
        mem_total_kb,
        mem_free_kb,
        mem_avail_kb,
        swap_total_kb,
        swap_free_kb,
        zram_total_kb,
        storage_total_kb,
        storage_used_kb,
        storage_avail_kb,
        procs,
    })
}
