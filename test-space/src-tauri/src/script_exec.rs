use std::collections::HashMap;
use std::io::{BufRead, BufReader};
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;
use serde::Serialize;
use tauri::{Emitter, Manager};

#[cfg(target_os = "windows")]
use std::os::windows::process::CommandExt;

fn decode(bytes: &[u8]) -> String {
    if let Ok(s) = std::str::from_utf8(bytes) {
        return s.to_string();
    }
    let (cow, _, _) = encoding_rs::GBK.decode(bytes);
    cow.to_string()
}

fn strip_backspaces(s: &str) -> String {
    let mut r = String::with_capacity(s.len());
    for c in s.chars() {
        if c == '\u{0008}' {
            r.pop();
        } else {
            r.push(c);
        }
    }
    r
}

fn silent_cmd(prog: &str) -> Command {
    let mut cmd = Command::new(prog);
    #[cfg(target_os = "windows")]
    { cmd.creation_flags(0x08000000); }
    cmd
}

/// 单个参数按 cmd 规则加引号（仅处理空白与内嵌引号，够脚本场景用）。
#[cfg(target_os = "windows")]
fn cmd_quote_arg(a: &str) -> String {
    if a.is_empty() {
        return "\"\"".to_string();
    }
    if a.chars().any(|c| c == ' ' || c == '\t' || c == '"') {
        format!("\"{}\"", a.replace('"', ""))
    } else {
        a.to_string()
    }
}

/// 构造 `cmd /S /C "<整段命令>"`。
///
/// 为什么不能直接 `c.args(["/C", path])`：Rust 只在参数含空白时才自动加引号，
/// 而 `(` `)` `&` `^` 这些 cmd 元字符不含空白，于是 `...\随机20分钟(1).bat`
/// 会被 cmd 在 `(` 处截断，报 “'...随机按上下左右ok返回20分钟' 不是内部或外部命令”。
/// `/S` 下 cmd 会剥掉最外层一对引号，剩下的内容原样执行，因此这里再包一层。
#[cfg(target_os = "windows")]
fn cmd_with_line(raw: &str) -> Command {
    let mut c = silent_cmd("cmd");
    c.arg("/S");
    c.arg("/C");
    c.raw_arg(format!("\"{}\"", raw));
    c
}

#[cfg(target_os = "windows")]
fn cmd_line(base: &str, args: &[String]) -> String {
    let mut s = base.to_string();
    for a in args {
        s.push(' ');
        s.push_str(&cmd_quote_arg(a));
    }
    s
}

#[derive(Serialize)]
pub struct ScriptResult {
    pub stdout: String,
    pub stderr: String,
    pub exit_code: i32,
}

#[derive(Serialize, Clone)]
pub struct ScriptLinePayload {
    pub id: String,
    pub line: String,
    pub stream: String,
}

#[derive(Serialize, Clone)]
pub struct ScriptExitPayload {
    pub id: String,
    pub exit_code: i32,
}

pub struct ScriptManager {
    pub processes: Mutex<HashMap<String, std::sync::Arc<Mutex<Child>>>>,
    pub pids: Mutex<HashMap<String, u32>>,
}

impl ScriptManager {
    pub fn new() -> Self {
        Self {
            processes: Mutex::new(HashMap::new()),
            pids: Mutex::new(HashMap::new()),
        }
    }
}

fn spawn_command(interpreter: &str, script_path: &str, args: &[String]) -> Result<Command, String> {
    let cmd = match interpreter {
        "python" => {
            let mut c = silent_cmd("python");
            c.arg("-u").arg(script_path);
            c.args(args);
            c
        }
        "bat" => {
            // 与双击 .bat 等价：代码页、换行、编码都已在打包阶段写进文件本身，
            // 这里不再追加 chcp 前缀，避免「应用内能跑、导出后报错」的隐性差异。
            #[cfg(target_os = "windows")]
            {
                cmd_with_line(&cmd_line(&format!("\"{}\"", script_path), args))
            }
            #[cfg(not(target_os = "windows"))]
            {
                let mut c = silent_cmd("cmd");
                c.args(["/C", script_path]);
                c.args(args);
                c
            }
        }
        "ps1" => {
            let mut c = silent_cmd("powershell");
            c.args(["-ExecutionPolicy", "Bypass", "-NoProfile", "-File", script_path]);
            c.args(args);
            c
        }
        "shell" => {
            // 注意：这里的 script_path 实际是一条命令字符串（execute_shell），
            // 不是文件路径，所以不能加引号，保持原样交给 cmd。
            let cmd_str = if cfg!(windows) {
                format!("chcp 65001>nul&&{}", script_path)
            } else {
                script_path.to_string()
            };
            let (shell, arg) = if cfg!(windows) { ("cmd", "/c") } else { ("sh", "-c") };
            let mut c = silent_cmd(shell);
            c.arg(arg).arg(&cmd_str);
            c.args(args);
            c
        }
        _ => return Err(format!("Unknown interpreter: {}", interpreter)),
    };
    Ok(cmd)
}

pub fn execute_python(script_path: &str, args: &[String]) -> Result<ScriptResult, String> {
    let output = spawn_command("python", script_path, args)?
        .output()
        .map_err(|e| format!("Python execution failed: {}", e))?;
    Ok(ScriptResult {
        stdout: decode(&output.stdout),
        stderr: decode(&output.stderr),
        exit_code: output.status.code().unwrap_or(-1),
    })
}

pub fn execute_powershell(script_path: &str, args: &[String]) -> Result<ScriptResult, String> {
    let output = spawn_command("ps1", script_path, args)?
        .output()
        .map_err(|e| format!("PowerShell execution failed: {}", e))?;
    Ok(ScriptResult {
        stdout: decode(&output.stdout),
        stderr: decode(&output.stderr),
        exit_code: output.status.code().unwrap_or(-1),
    })
}

pub fn execute_shell(command: &str) -> Result<ScriptResult, String> {
    let output = spawn_command("shell", command, &[])?
        .output()
        .map_err(|e| format!("Shell execution failed: {}", e))?;
    Ok(ScriptResult {
        stdout: decode(&output.stdout),
        stderr: decode(&output.stderr),
        exit_code: output.status.code().unwrap_or(-1),
    })
}

pub fn execute_bat(script_path: &str, args: &[String]) -> Result<ScriptResult, String> {
    let output = spawn_command("bat", script_path, args)?
        .output()
        .map_err(|e| format!("BAT execution failed: {}", e))?;
    Ok(ScriptResult {
        stdout: decode(&output.stdout),
        stderr: decode(&output.stderr),
        exit_code: output.status.code().unwrap_or(-1),
    })
}



#[tauri::command]
pub fn script_spawn(
    app: tauri::AppHandle,
    state: tauri::State<'_, ScriptManager>,
    id: String,
    interpreter: String,
    script_path: String,
    args: Vec<String>,
    work_dir: Option<String>,
) -> Result<(), String> {
    let mut cmd = spawn_command(&interpreter, &script_path, &args)?;
    if let Some(dir) = &work_dir {
        cmd.current_dir(dir);
    }
    let mut child = cmd
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(|e| format!("Failed to spawn: {}", e))?;

    let pid = child.id();
    let stdout = child.stdout.take()
        .ok_or_else(|| "Failed to capture stdout".to_string())?;
    let stderr = child.stderr.take()
        .ok_or_else(|| "Failed to capture stderr".to_string())?;

    let child_arc = std::sync::Arc::new(Mutex::new(child));
    state.processes.lock().unwrap().insert(id.clone(), child_arc.clone());
    state.pids.lock().unwrap().insert(id.clone(), pid);

    log::info!("Script spawned: id={}, interpreter={}, path={}, pid={}", id, interpreter, script_path, pid);

    let r_id = id.clone();
    let r_app = app.clone();
    std::thread::spawn(move || {
        let mut reader = BufReader::new(stdout);
        let mut buf = Vec::new();
        loop {
            buf.clear();
            let n = reader.read_until(b'\n', &mut buf).unwrap_or(0);
            if n == 0 { break; }
            let end = if buf.ends_with(b"\n") { buf.len() - 1 } else { buf.len() };
            let raw = decode(&buf[..end]);
            let line = strip_backspaces(raw.trim_end_matches('\r'));
            drop(r_app.emit("script-line", ScriptLinePayload {
                id: r_id.clone(),
                line,
                stream: "stdout".to_string(),
            }));
        }
    });

    let e_id = id.clone();
    let e_app = app.clone();
    std::thread::spawn(move || {
        let mut reader = BufReader::new(stderr);
        let mut buf = Vec::new();
        loop {
            buf.clear();
            let n = reader.read_until(b'\n', &mut buf).unwrap_or(0);
            if n == 0 { break; }
            let end = if buf.ends_with(b"\n") { buf.len() - 1 } else { buf.len() };
            let raw = decode(&buf[..end]);
            let line = strip_backspaces(raw.trim_end_matches('\r'));
            drop(e_app.emit("script-line", ScriptLinePayload {
                id: e_id.clone(),
                line,
                stream: "stderr".to_string(),
            }));
        }
    });

    let w_id = id.clone();
    let w_app = app.clone();
    let w_child = child_arc.clone();
    std::thread::spawn(move || {
        let status = {
            let mut guard = w_child.lock().unwrap();
            guard.wait()
        };
        let exit_code = status.map(|s| s.code().unwrap_or(-1)).unwrap_or(-1);
        drop(w_app.emit("script-exit", ScriptExitPayload {
            id: w_id.clone(),
            exit_code,
        }));
        let mgr = w_app.state::<ScriptManager>();
        mgr.processes.lock().unwrap().remove(&w_id);
        mgr.pids.lock().unwrap().remove(&w_id);
        log::info!("Script exited: id={}, code={}", w_id, exit_code);
    });

    Ok(())
}

#[tauri::command]
pub fn script_kill(
    state: tauri::State<'_, ScriptManager>,
    id: String,
) -> Result<(), String> {
    let pids = state.pids.lock().unwrap();
    let pid = pids.get(&id).copied();
    drop(pids);

    if let Some(pid) = pid {
        state.processes.lock().unwrap().remove(&id);
        state.pids.lock().unwrap().remove(&id);

        let _ = silent_cmd("taskkill")
            .args(["/F", "/T", "/PID", &pid.to_string()])
            .output();

        log::info!("Script killed: id={}, pid={}", id, pid);
        Ok(())
    } else {
        Err(format!("No running process with id: {}", id))
    }
}
