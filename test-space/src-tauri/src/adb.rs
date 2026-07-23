use std::process::Command;
use serde::Serialize;
use std::sync::mpsc;
use std::sync::Mutex;
use std::thread;
use std::time::Duration;

// CPU delta cache for /proc/stat + /proc/[pid]/stat approach.
// Stores the previous snapshot's cumulative jiffies so we can compute
// per-process CPU percentage across the 10s polling interval.
struct CpuSnapshot {
    total_jiffies: u64,
    idle_jiffies: u64,
    proc_ticks: std::collections::HashMap<u32, u64>, // pid -> utime + stime
}
static PREV_CPU: Mutex<Option<CpuSnapshot>> = Mutex::new(None);


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
    // Extended memory distribution
    pub mem_cached_kb: u64,
    pub mem_buffers_kb: u64,
    pub mem_slab_kb: u64,
    pub mem_kernel_stack_kb: u64,
    pub mem_page_tables_kb: u64,
    // PSI pressure metrics (0.0 if kernel doesn't support PSI)
    pub pressure_mem_some_avg10: f64,
    pub pressure_mem_some_avg60: f64,
    pub pressure_mem_some_avg300: f64,
    pub pressure_mem_full_avg10: f64,
    pub pressure_mem_full_avg60: f64,
    pub pressure_mem_full_avg300: f64,
    pub pressure_io_some_avg10: f64,
    pub pressure_io_some_avg60: f64,
    pub pressure_io_some_avg300: f64,
    pub pressure_io_full_avg10: f64,
    pub pressure_io_full_avg60: f64,
    pub pressure_io_full_avg300: f64,
    pub pressure_cpu_some_avg10: f64,
    pub pressure_cpu_some_avg60: f64,
    pub pressure_cpu_some_avg300: f64,
    pub pressure_cpu_full_avg10: f64,
    pub pressure_cpu_full_avg60: f64,
    pub pressure_cpu_full_avg300: f64,
    // Network IO (cumulative bytes, parsed from /proc/net/dev)
    pub net_rx_bytes: u64,
    pub net_tx_bytes: u64,
    // Device info
    pub device_uptime_secs: f64,
    pub device_date: String,
    pub kernel_version: String,
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
    // Collect meminfo, top, df, ps, pressure, uptime, and version in a single shell call.
    // Using a single ADB shell invocation to minimize latency on every poll cycle.
    let combined = shell_command(serial, "cat /proc/meminfo 2>/dev/null; echo '---CPU---'; cat /proc/stat; echo '---PIDS---'; cat /proc/[0-9]*/stat 2>/dev/null; echo '---DF---'; df /data 2>/dev/null; echo '---PROC---'; ps -A 2>/dev/null; echo '---PRESSURE---'; cat /proc/pressure/memory 2>/dev/null; echo '---IOPRESSURE---'; cat /proc/pressure/io 2>/dev/null; echo '---CPURESSURE---'; cat /proc/pressure/cpu 2>/dev/null; echo '---NET---'; cat /proc/net/dev 2>/dev/null; echo '---UPTIME---'; cat /proc/uptime 2>/dev/null; echo '---DATE---'; date +%s 2>/dev/null; echo '---VERSION---'; cat /proc/version 2>/dev/null")?;

    let mut mem_total_kb: u64 = 0;
    let mut mem_free_kb: u64 = 0;
    let mut mem_avail_kb: u64 = 0;
    let mut swap_total_kb: u64 = 0;
    let mut swap_free_kb: u64 = 0;

    let mut cpu_total: f64 = 0.0;
    let mut storage_total_kb: u64 = 0;
    let mut storage_used_kb: u64 = 0;
    let mut storage_avail_kb: u64 = 0;
    let mut zram_total_kb: u64 = 0;

    // Extended memory distribution fields
    let mut mem_cached_kb: u64 = 0;
    let mut mem_buffers_kb: u64 = 0;
    let mut mem_slab_kb: u64 = 0;
    let mut mem_kernel_stack_kb: u64 = 0;
    let mut mem_page_tables_kb: u64 = 0;

    // PSI pressure default to 0.0 (will stay 0 on kernels without PSI support)
    let mut pressure_mem_some_avg10: f64 = 0.0;
    let mut pressure_mem_some_avg60: f64 = 0.0;
    let mut pressure_mem_some_avg300: f64 = 0.0;
    let mut pressure_mem_full_avg10: f64 = 0.0;
    let mut pressure_mem_full_avg60: f64 = 0.0;
    let mut pressure_mem_full_avg300: f64 = 0.0;
    let mut pressure_io_some_avg10: f64 = 0.0;
    let mut pressure_io_some_avg60: f64 = 0.0;
    let mut pressure_io_some_avg300: f64 = 0.0;
    let mut pressure_io_full_avg10: f64 = 0.0;
    let mut pressure_io_full_avg60: f64 = 0.0;
    let mut pressure_io_full_avg300: f64 = 0.0;
    let mut pressure_cpu_some_avg10: f64 = 0.0;
    let mut pressure_cpu_some_avg60: f64 = 0.0;
    let mut pressure_cpu_some_avg300: f64 = 0.0;
    let mut pressure_cpu_full_avg10: f64 = 0.0;
    let mut pressure_cpu_full_avg60: f64 = 0.0;
    let mut pressure_cpu_full_avg300: f64 = 0.0;

    // Network IO
    let mut net_rx_bytes: u64 = 0;
    let mut net_tx_bytes: u64 = 0;

    // Device info
    let mut device_uptime_secs: f64 = 0.0;
    let mut device_date: String = String::new();
    let mut kernel_version: String = String::new();
    let mut current_cpu_jiffies: u64 = 0;
    let mut current_idle_jiffies: u64 = 0;
    let mut current_proc_ticks: std::collections::HashMap<u32, u64> = std::collections::HashMap::new();
    // PID -> command name (from ps -A output, used for CPU-only processes)
    let mut pid_to_name: std::collections::HashMap<u32, String> = std::collections::HashMap::new();

    // PID -> (name, pss_kb) — primary source is dumpsys meminfo (accurate PSS)
    let mut pid_to_pss: std::collections::HashMap<u32, (String, u64)> = std::collections::HashMap::new();
    // PID -> cpu_percent — from /proc/[pid]/stat delta cache
    let mut pid_to_cpu: std::collections::HashMap<u32, f64> = std::collections::HashMap::new();

    let mut section = "meminfo";

    for line in combined.lines() {
        match line.trim() {
            "---CPU---" => { section = "cpu"; continue; }
            "---PIDS---" => { section = "pids"; continue; }
            "---DF---" => { section = "df"; continue; }
            "---PROC---" => { section = "proc"; continue; }
            "---PRESSURE---" => { section = "pressure"; continue; }
            "---IOPRESSURE---" => { section = "iopressure"; continue; }
            "---CPURESSURE---" => { section = "cpupressure"; continue; }
            "---NET---" => { section = "net"; continue; }
            "---UPTIME---" => { section = "uptime"; continue; }
            "---DATE---" => { section = "date"; continue; }
            "---VERSION---" => { section = "version"; continue; }
            _ => {}
        }

        match section {
            "meminfo" => {
                if line.starts_with("MemTotal:") { mem_total_kb = parse_kb_val(line); }
                else if line.starts_with("MemFree:") { mem_free_kb = parse_kb_val(line); }
                else if line.starts_with("MemAvailable:") { mem_avail_kb = parse_kb_val(line); }
                else if line.starts_with("SwapTotal:") { swap_total_kb = parse_kb_val(line); }
                else if line.starts_with("SwapFree:") { swap_free_kb = parse_kb_val(line); }
                else if line.starts_with("Cached:") { mem_cached_kb = parse_kb_val(line); }
                else if line.starts_with("Buffers:") { mem_buffers_kb = parse_kb_val(line); }
                else if line.starts_with("Slab:") { mem_slab_kb = parse_kb_val(line); }
                else if line.starts_with("KernelStack:") { mem_kernel_stack_kb = parse_kb_val(line); }
                else if line.starts_with("PageTables:") { mem_page_tables_kb = parse_kb_val(line); }
            }
            "cpu" => {
                // /proc/stat first line: "cpu  user nice sys idle iowait irq softirq steal ..."
                let trimmed = line.trim();
                if trimmed.starts_with("cpu ") {
                    let parts: Vec<&str> = trimmed.split_whitespace().collect();
                    if parts.len() >= 5 {
                        let vals: Vec<u64> = parts[1..].iter()
                            .filter_map(|s| s.parse::<u64>().ok())
                            .collect();
                        if vals.len() >= 4 {
                            let total: u64 = vals.iter().sum();
                            let idle = vals[3]; // idle is 4th field (0-indexed 3)
                            cpu_total = ((total - idle) as f64 / total as f64 * 100.0).clamp(0.0, 100.0);
                            // Store current stats for per-process delta computation
                            current_cpu_jiffies = total;
                            current_idle_jiffies = idle;
                        }
                    }
                }
            }
            "pids" => {
                // Parse /proc/[pid]/stat for per-process CPU ticks.
                // Format: "pid (comm) state ppid ... utime stime ..."
                let trimmed = line.trim();
                if trimmed.is_empty() { continue; }
                // Find the closing paren of comm field
                if let Some(paren_close) = trimmed.rfind(')') {
                    let before_paren = trimmed[..paren_close].trim();
                    // Extract pid from start (before first space before '(')
                    if let Some(pid_str) = before_paren.split_whitespace().next() {
                        if let Ok(pid) = pid_str.parse::<u32>() {
                            if pid > 0 {
                                // Fields after ')': state ppid pgrp session tty ... utime stime
                                let after = trimmed[paren_close + 1..].trim();
                                let fields: Vec<&str> = after.split_whitespace().collect();
                                // utime = fields[11], stime = fields[12] (0-indexed after state)
                                if fields.len() >= 13 {
                                    if let Ok(utime) = fields[11].parse::<u64>() {
                                        if let Ok(stime) = fields[12].parse::<u64>() {
                                            current_proc_ticks.insert(pid, utime + stime);
                                        }
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
                                pid_to_name.entry(pid).or_insert_with(|| name.clone());
                                // Use RSS as approximate PSS if dumpsys doesn't have it
                                let rss_kb = parts[4].parse::<u64>().unwrap_or(0);
                                pid_to_pss.entry(pid).or_insert((name, rss_kb));
                            }
                        }
                    }
                }
            }
            "pressure" => {
                // /proc/pressure/memory format:
                //   some avg10=0.00 avg60=0.00 avg300=0.00 total=0
                //   full avg10=0.00 avg60=0.00 avg300=0.00 total=0
                let trimmed = line.trim();
                if trimmed.starts_with("some") {
                    for word in trimmed.split_whitespace() {
                        if let Some(val) = word.strip_prefix("avg10=") {
                            pressure_mem_some_avg10 = val.parse::<f64>().unwrap_or(0.0);
                        } else if let Some(val) = word.strip_prefix("avg60=") {
                            pressure_mem_some_avg60 = val.parse::<f64>().unwrap_or(0.0);
                        } else if let Some(val) = word.strip_prefix("avg300=") {
                            pressure_mem_some_avg300 = val.parse::<f64>().unwrap_or(0.0);
                        }
                    }
                } else if trimmed.starts_with("full") {
                    for word in trimmed.split_whitespace() {
                        if let Some(val) = word.strip_prefix("avg10=") {
                            pressure_mem_full_avg10 = val.parse::<f64>().unwrap_or(0.0);
                        } else if let Some(val) = word.strip_prefix("avg60=") {
                            pressure_mem_full_avg60 = val.parse::<f64>().unwrap_or(0.0);
                        } else if let Some(val) = word.strip_prefix("avg300=") {
                            pressure_mem_full_avg300 = val.parse::<f64>().unwrap_or(0.0);
                        }
                    }
                }
            }
            "iopressure" => {
                let trimmed = line.trim();
                if trimmed.starts_with("some") {
                    for word in trimmed.split_whitespace() {
                        if let Some(val) = word.strip_prefix("avg10=") {
                            pressure_io_some_avg10 = val.parse::<f64>().unwrap_or(0.0);
                        } else if let Some(val) = word.strip_prefix("avg60=") {
                            pressure_io_some_avg60 = val.parse::<f64>().unwrap_or(0.0);
                        } else if let Some(val) = word.strip_prefix("avg300=") {
                            pressure_io_some_avg300 = val.parse::<f64>().unwrap_or(0.0);
                        }
                    }
                } else if trimmed.starts_with("full") {
                    for word in trimmed.split_whitespace() {
                        if let Some(val) = word.strip_prefix("avg10=") {
                            pressure_io_full_avg10 = val.parse::<f64>().unwrap_or(0.0);
                        } else if let Some(val) = word.strip_prefix("avg60=") {
                            pressure_io_full_avg60 = val.parse::<f64>().unwrap_or(0.0);
                        } else if let Some(val) = word.strip_prefix("avg300=") {
                            pressure_io_full_avg300 = val.parse::<f64>().unwrap_or(0.0);
                        }
                    }
                }
            }
            "cpupressure" => {
                let trimmed = line.trim();
                if trimmed.starts_with("some") {
                    for word in trimmed.split_whitespace() {
                        if let Some(val) = word.strip_prefix("avg10=") {
                            pressure_cpu_some_avg10 = val.parse::<f64>().unwrap_or(0.0);
                        } else if let Some(val) = word.strip_prefix("avg60=") {
                            pressure_cpu_some_avg60 = val.parse::<f64>().unwrap_or(0.0);
                        } else if let Some(val) = word.strip_prefix("avg300=") {
                            pressure_cpu_some_avg300 = val.parse::<f64>().unwrap_or(0.0);
                        }
                    }
                } else if trimmed.starts_with("full") {
                    for word in trimmed.split_whitespace() {
                        if let Some(val) = word.strip_prefix("avg10=") {
                            pressure_cpu_full_avg10 = val.parse::<f64>().unwrap_or(0.0);
                        } else if let Some(val) = word.strip_prefix("avg60=") {
                            pressure_cpu_full_avg60 = val.parse::<f64>().unwrap_or(0.0);
                        } else if let Some(val) = word.strip_prefix("avg300=") {
                            pressure_cpu_full_avg300 = val.parse::<f64>().unwrap_or(0.0);
                        }
                    }
                }
            }
            "uptime" => {
                // /proc/uptime: "uptime_seconds idle_seconds"
                let trimmed = line.trim();
                if let Some(first) = trimmed.split_whitespace().next() {
                    device_uptime_secs = first.parse::<f64>().unwrap_or(0.0);
                }
            }
            "net" => {
                // /proc/net/dev: "  wlan0: 12345678 12345 ... 87654321 54321 ..."
                // Sum RX/TX bytes from all non-loopback interfaces for total device IO
                let trimmed = line.trim();
                if let Some(pos) = trimmed.find(':') {
                    let iface = trimmed[..pos].trim();
                    if iface != "lo" && !iface.is_empty() {
                        let rest = trimmed[pos+1..].trim();
                        let parts: Vec<&str> = rest.split_whitespace().collect();
                        if parts.len() >= 9 {
                            if let Ok(rx) = parts[0].parse::<u64>() { net_rx_bytes += rx; }
                            if let Ok(tx) = parts[8].parse::<u64>() { net_tx_bytes += tx; }
                        }
                    }
                }
            }
            "date" => {
                // date +%s: epoch seconds from device
                device_date = line.trim().to_string();
            }
            "version" => {
                // /proc/version: "Linux version 5.10.149-android12-9-...
                let trimmed = line.trim();
                if !trimmed.is_empty() {
                    kernel_version = trimmed.to_string();
                }
            }
            _ => {}
        }
    }

    // Compute CPU percentages from /proc/stat delta (across ~10s polling interval).
    // Using a static cache avoids the 1s sampling delay of `top -n 1 -d 1 -b`.
    if let Ok(mut prev_guard) = PREV_CPU.lock() {
        if let Some(ref prev) = *prev_guard {
            let total_delta = current_cpu_jiffies.saturating_sub(prev.total_jiffies);
            if total_delta > 0 {
                let idle_delta = current_idle_jiffies.saturating_sub(prev.idle_jiffies);
                cpu_total = ((total_delta - idle_delta) as f64 / total_delta as f64 * 100.0).clamp(0.0, 100.0);

                // Per-process CPU: (utime+stime delta) / total_jiffies_delta * 100
                for (&pid, &ticks) in &current_proc_ticks {
                    if let Some(&prev_ticks) = prev.proc_ticks.get(&pid) {
                        let delta = ticks.saturating_sub(prev_ticks);
                        let cpu = (delta as f64 / total_delta as f64 * 100.0).clamp(0.0, 100.0);
                        if cpu > 0.0 {
                            pid_to_cpu.insert(pid, cpu);
                        }
                    }
                    // PIDs with no previous entry show 0% (first appearance)
                }
            }
        }
        // Store current stats as previous for next poll
        *prev_guard = Some(CpuSnapshot {
            total_jiffies: current_cpu_jiffies,
            idle_jiffies: current_idle_jiffies,
            proc_ticks: current_proc_ticks,
        });
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
                                let pid = tokens.iter()
                                    .position(|t| t.starts_with("(pid"))
                                    .and_then(|pos| tokens.get(pos + 1))
                                    .and_then(|s| s.trim_end_matches(')').parse::<u32>().ok())
                                    .unwrap_or(0);
                                if pid > 0 {
                                    pid_to_name.entry(pid).or_insert_with(|| name.clone());
                                    pid_to_pss.insert(pid, (name, size_kb));
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    // Build final procs list: merge PSS (from dumpsys) with CPU (from proc stat delta)
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

    // Also add processes from pid_to_cpu that have CPU but no PSS (e.g., short-lived processes)
    for (pid, cpu_percent) in &pid_to_cpu {
        if !pid_to_pss.contains_key(pid) && *cpu_percent > 0.0 {
            let name = pid_to_name.get(pid).cloned().unwrap_or_default();
            if !name.is_empty() {
                procs.push(PerfProcess {
                    pid: *pid,
                    name,
                    pss_kb: 0,
                    cpu_percent: *cpu_percent,
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
        mem_cached_kb,
        mem_buffers_kb,
        mem_slab_kb,
        mem_kernel_stack_kb,
        mem_page_tables_kb,
        pressure_mem_some_avg10,
        pressure_mem_some_avg60,
        pressure_mem_some_avg300,
        pressure_mem_full_avg10,
        pressure_mem_full_avg60,
        pressure_mem_full_avg300,
        pressure_io_some_avg10,
        pressure_io_some_avg60,
        pressure_io_some_avg300,
        pressure_io_full_avg10,
        pressure_io_full_avg60,
        pressure_io_full_avg300,
        pressure_cpu_some_avg10,
        pressure_cpu_some_avg60,
        pressure_cpu_some_avg300,
        pressure_cpu_full_avg10,
        pressure_cpu_full_avg60,
        pressure_cpu_full_avg300,
        net_rx_bytes,
        net_tx_bytes,
        device_uptime_secs,
        device_date,
        kernel_version,
    })
}

// Watermark analysis: parse /proc/zoneinfo for min/low/high watermark levels per zone.
// Returns a JSON-friendly struct. This is collected separately (every 60s) because
// /proc/zoneinfo can be very large on some devices.
#[derive(Serialize)]
pub struct WatermarkInfo {
    pub zones: Vec<ZoneWatermark>,
    pub total_free_pages_kb: u64,
}

#[derive(Serialize)]
pub struct ZoneWatermark {
    pub name: String,
    pub free_kb: u64,
    pub min_kb: u64,
    pub low_kb: u64,
    pub high_kb: u64,
    pub managed_kb: u64,
}

// ── dumpsys meminfo -S: per-process PSS tracking ──

#[derive(Serialize)]
pub struct DumpsysMemInfo {
    pub total_ram_kb: u64,
    pub free_ram_kb: u64,
    pub used_ram_pss_kb: u64,
    pub used_ram_kernel_kb: u64,
    pub processes: Vec<PssProcess>,
}

#[derive(Serialize)]
pub struct PssProcess {
    pub name: String,
    pub pid: u32,
    pub pss_kb: u64,
}

pub fn get_dumpsys_meminfo(serial: &str) -> Result<DumpsysMemInfo, String> {
    let output = shell_command(serial, "dumpsys meminfo -S 2>/dev/null")?;
    let mut total_ram_kb: u64 = 0;
    let mut free_ram_kb: u64 = 0;
    let mut used_ram_pss_kb: u64 = 0;
    let mut used_ram_kernel_kb: u64 = 0;
    let mut processes: Vec<PssProcess> = Vec::new();

    let mut in_process_list = false;

    for line in output.lines() {
        let trimmed = line.trim();

        if !in_process_list {
            // Parse summary header
            if trimmed.starts_with("Total RAM:") {
                // "Total RAM: 3,456,789 KB (Free: 1,234,567 KB)"
                if let Some(rest) = trimmed.strip_prefix("Total RAM:") {
                    for part in rest.split_whitespace() {
                        let clean = part.replace(',', "");
                        if let Ok(v) = clean.parse::<u64>() {
                            if total_ram_kb == 0 { total_ram_kb = v; }
                        }
                    }
                }
                // Also parse Free from within parentheses
                if let Some(free_start) = trimmed.find("Free:") {
                    let free_str = &trimmed[free_start + 5..];
                    for part in free_str.split_whitespace() {
                        let clean = part.replace(',', "").replace("KB", "").replace("kB", "");
                        if let Ok(v) = clean.parse::<u64>() {
                            free_ram_kb = v;
                            break;
                        }
                    }
                }
            } else if trimmed.starts_with("Used RAM:") {
                // "Used RAM: 2,222,222 KB (Used RAM PSS: 1,500,000 KB Used RAM Kernel: 222,222 KB)"
                if let Some(pss_start) = trimmed.find("Used RAM PSS:") {
                    let pss_str = &trimmed[pss_start + 13..];
                    for part in pss_str.split_whitespace() {
                        let clean = part.replace(',', "");
                        if let Ok(v) = clean.parse::<u64>() {
                            used_ram_pss_kb = v;
                            break;
                        }
                    }
                }
                if let Some(kernel_start) = trimmed.find("Used RAM Kernel:") {
                    let kernel_str = &trimmed[kernel_start + 16..];
                    for part in kernel_str.split_whitespace() {
                        let clean = part.replace(',', "");
                        if let Ok(v) = clean.parse::<u64>() {
                            used_ram_kernel_kb = v;
                            break;
                        }
                    }
                }
            } else if trimmed == "Process list:" {
                in_process_list = true;
            }
        } else {
            // In process list section
            if trimmed.is_empty() || trimmed == "Process list:" {
                continue;
            }
            // Detect process header: "  com.example.app (PID 1234):"
            if trimmed.contains("(PID") && trimmed.ends_with(':') {
                let pid_start = match trimmed.rfind("(PID") {
                    Some(p) => p + 4,
                    None => continue,
                };
                let pid_end = match trimmed[pid_start..].find(')') {
                    Some(p) => pid_start + p,
                    None => continue,
                };
                let pid_str = trimmed[pid_start..pid_end].trim();
                let pid = pid_str.parse::<u32>().unwrap_or(0);
                let name = trimmed[..trimmed.rfind("(PID").unwrap_or(0)].trim().to_string();

                // Read next lines for PSS
                // We'll store the current process and fill in PSS from subsequent lines
                processes.push(PssProcess {
                    name,
                    pid,
                    pss_kb: 0,
                });
            } else if trimmed.starts_with("PSS:") && !processes.is_empty() {
                // "PSS: 12345 KB"
                let val_str = trimmed
                    .strip_prefix("PSS:")
                    .unwrap_or("")
                    .replace("KB", "")
                    .replace("kB", "")
                    .trim()
                    .replace(',', "");
                if let Ok(v) = val_str.parse::<u64>() {
                    if let Some(last) = processes.last_mut() {
                        last.pss_kb = v;
                    }
                }
            }
        }
    }

    Ok(DumpsysMemInfo {
        total_ram_kb,
        free_ram_kb,
        used_ram_pss_kb,
        used_ram_kernel_kb,
        processes,
    })
}

// ── Incremental dmesg polling ──

#[derive(Serialize)]
pub struct DmesgPollResult {
    pub new_lines: Vec<String>,
    pub total_lines: usize,
    pub last_line: String,
}

pub fn poll_dmesg(serial: &str, known_lines: usize, known_last_line: &str) -> Result<DmesgPollResult, String> {
    let output = shell_command(serial, "dmesg 2>/dev/null")?;
    let lines: Vec<&str> = output.lines().collect();
    let total = lines.len();
    let current_last = if total > 0 { lines[total - 1].to_string() } else { String::new() };

    if total == 0 {
        return Ok(DmesgPollResult { new_lines: vec![], total_lines: 0, last_line: String::new() });
    }

    // If line count grew, we can use known_lines as before
    if total > known_lines {
        let new_lines: Vec<String> = lines[known_lines..].iter().map(|s| s.to_string()).collect();
        return Ok(DmesgPollResult { new_lines, total_lines: total, last_line: current_last });
    }

    // If line count <= known_lines but content changed (buffer wrapped),
    // collect everything as new
    if current_last != known_last_line && total > 0 {
        let new_lines: Vec<String> = lines.iter().map(|s| s.to_string()).collect();
        return Ok(DmesgPollResult { new_lines, total_lines: total, last_line: current_last });
    }

    Ok(DmesgPollResult { new_lines: vec![], total_lines: total, last_line: current_last })
}

// ── ANR / Tombstone detection ──

#[derive(Serialize)]
pub struct AnrTombstoneResult {
    pub new_anr_files: Vec<String>,
    pub new_tombstone_files: Vec<String>,
}

pub fn check_anr_tombstones(serial: &str, known_anr: &[String], known_tombstone: &[String]) -> Result<AnrTombstoneResult, String> {
    let anr_list = shell_command(serial, "ls /data/anr/ 2>/dev/null").unwrap_or_default();
    let ts_list = shell_command(serial, "ls /data/tombstones/ 2>/dev/null").unwrap_or_default();

    let new_anr: Vec<String> = anr_list
        .lines()
        .map(|l| l.trim().to_string())
        .filter(|f| !f.is_empty() && f != "ls:" && !f.contains("No such file") && f != "/data/anr/:" && !known_anr.contains(f))
        .collect();
    let new_ts: Vec<String> = ts_list
        .lines()
        .map(|l| l.trim().to_string())
        .filter(|f| !f.is_empty() && f != "ls:" && !f.contains("No such file") && f != "/data/tombstones/:" && !known_tombstone.contains(f))
        .collect();

    Ok(AnrTombstoneResult { new_anr_files: new_anr, new_tombstone_files: new_ts })
}

pub fn get_watermark_info(serial: &str) -> Result<WatermarkInfo, String> {
    let output = shell_command(serial, "cat /proc/zoneinfo 2>/dev/null")?;
    let mut zones: Vec<ZoneWatermark> = Vec::new();
    let mut total_free_pages_kb: u64 = 0;
    let mut current_name = String::new();
    let mut current_free: u64 = 0;
    let mut current_min: u64 = 0;
    let mut current_low: u64 = 0;
    let mut current_high: u64 = 0;
    let mut current_managed: u64 = 0;

    for line in output.lines() {
        let trimmed = line.trim();
        // "Node 0, zone      DMA" or "Node 0, zone    DMA32" or "Node 0, zone   Normal"
        if trimmed.contains("zone") && trimmed.starts_with("Node") {
            if !current_name.is_empty() {
                zones.push(ZoneWatermark {
                    name: current_name.clone(),
                    free_kb: current_free,
                    min_kb: current_min,
                    low_kb: current_low,
                    high_kb: current_high,
                    managed_kb: current_managed,
                });
            }
            // Extract zone name after "zone"
            let parts: Vec<&str> = trimmed.split_whitespace().collect();
            if let Some(pos) = parts.iter().position(|&p| p == "zone") {
                if pos + 1 < parts.len() {
                    current_name = parts[pos + 1].to_string();
                }
            }
            current_free = 0; current_min = 0; current_low = 0; current_high = 0; current_managed = 0;
        } else if trimmed.starts_with("pages free") {
            if let Some(v) = trimmed.split_whitespace().nth(2) {
                current_free = v.parse::<u64>().unwrap_or(0);
            }
        } else if trimmed.starts_with("min") && !trimmed.starts_with("min_unmapped") {
            if let Some(v) = trimmed.split_whitespace().nth(1) {
                current_min = v.parse::<u64>().unwrap_or(0);
            }
        } else if trimmed.starts_with("low") && !trimmed.starts_with("lowmem") {
            if let Some(v) = trimmed.split_whitespace().nth(1) {
                current_low = v.parse::<u64>().unwrap_or(0);
            }
        } else if trimmed.starts_with("high") {
            if let Some(v) = trimmed.split_whitespace().nth(1) {
                current_high = v.parse::<u64>().unwrap_or(0);
            }
        } else if trimmed.starts_with("managed") {
            if let Some(v) = trimmed.split_whitespace().nth(1) {
                current_managed = v.parse::<u64>().unwrap_or(0);
            }
        }
    }
    // Push last zone
    if !current_name.is_empty() {
        zones.push(ZoneWatermark {
            name: current_name.clone(),
            free_kb: current_free,
            min_kb: current_min,
            low_kb: current_low,
            high_kb: current_high,
            managed_kb: current_managed,
        });
    }

    // Calculate total free pages (in KB: zoneinfo uses 4KB pages)
    for z in &zones {
        total_free_pages_kb += z.free_kb * 4;
    }

    Ok(WatermarkInfo { zones, total_free_pages_kb })
}
