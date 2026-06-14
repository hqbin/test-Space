use std::process::Command;
use serde::Serialize;

#[derive(Serialize)]
pub struct ScriptResult {
    pub stdout: String,
    pub stderr: String,
    pub exit_code: i32,
}

pub fn execute_python(script_path: &str, args: &[String]) -> Result<ScriptResult, String> {
    let output = Command::new("python")
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
    let output = Command::new("cmd")
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
    let output = Command::new("powershell")
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
    let output = Command::new("cmd")
        .args(["/c", command])
        .output()
        .map_err(|e| format!("Shell execution failed: {}", e))?;
    Ok(ScriptResult {
        stdout: String::from_utf8_lossy(&output.stdout).to_string(),
        stderr: String::from_utf8_lossy(&output.stderr).to_string(),
        exit_code: output.status.code().unwrap_or(-1),
    })
}
