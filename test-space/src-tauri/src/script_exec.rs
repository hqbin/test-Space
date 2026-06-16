use std::process::Command;
use serde::Serialize;

#[cfg(target_os = "windows")]
use std::os::windows::process::CommandExt;

fn silent_cmd(prog: &str) -> Command {
    let mut cmd = Command::new(prog);
    #[cfg(target_os = "windows")]
    { cmd.creation_flags(0x08000000); } // CREATE_NO_WINDOW
    cmd
}

#[derive(Serialize)]
pub struct ScriptResult {
    pub stdout: String,
    pub stderr: String,
    pub exit_code: i32,
}

pub fn execute_python(script_path: &str, args: &[String]) -> Result<ScriptResult, String> {
    let output = silent_cmd("python")
        .arg(script_path)
        .args(args)
        .output()
        .map_err(|e| format!("Python execution failed: {}", e))?;
    Ok(ScriptResult {
        stdout: String::from_utf8_lossy(&output.stdout).to_string(),
        stderr: String::from_utf8_lossy(&output.stderr).to_string(),
        exit_code: output.status.code().unwrap_or(-1),
    })
}

pub fn execute_bat(script_path: &str, args: &[String]) -> Result<ScriptResult, String> {
    let output = silent_cmd("cmd")
        .args(["/c", script_path])
        .args(args)
        .output()
        .map_err(|e| format!("BAT execution failed: {}", e))?;
    Ok(ScriptResult {
        stdout: String::from_utf8_lossy(&output.stdout).to_string(),
        stderr: String::from_utf8_lossy(&output.stderr).to_string(),
        exit_code: output.status.code().unwrap_or(-1),
    })
}

pub fn execute_powershell(script_path: &str, args: &[String]) -> Result<ScriptResult, String> {
    let output = silent_cmd("powershell")
        .args(["-ExecutionPolicy", "Bypass", "-File", script_path])
        .args(args)
        .output()
        .map_err(|e| format!("PowerShell execution failed: {}", e))?;
    Ok(ScriptResult {
        stdout: String::from_utf8_lossy(&output.stdout).to_string(),
        stderr: String::from_utf8_lossy(&output.stderr).to_string(),
        exit_code: output.status.code().unwrap_or(-1),
    })
}

pub fn execute_shell(command: &str) -> Result<ScriptResult, String> {
    let cmd = if cfg!(windows) {
        format!("chcp 65001>nul&&{}", command)
    } else {
        command.to_string()
    };
    let shell_prog = if cfg!(windows) { "cmd" } else { "sh" };
    let shell_arg = if cfg!(windows) { "/c" } else { "-c" };
    let output = silent_cmd(shell_prog)
        .args([shell_arg, &cmd])
        .output()
        .map_err(|e| format!("Shell execution failed: {}", e))?;
    Ok(ScriptResult {
        stdout: String::from_utf8_lossy(&output.stdout).to_string(),
        stderr: String::from_utf8_lossy(&output.stderr).to_string(),
        exit_code: output.status.code().unwrap_or(-1),
    })
}
