use std::collections::HashMap;
use std::io::{BufRead, BufReader};
use std::process::{Child, Command, Stdio};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{Arc, Mutex};
use serde::{Deserialize, Serialize};
use tauri::{Emitter, Manager};

#[cfg(target_os = "windows")]
use std::os::windows::process::CommandExt;

#[derive(Serialize, Deserialize, Clone)]
pub struct AutoStepEvent {
    #[serde(rename = "type")]
    pub event_type: String,
    pub step_id: Option<String>,
    pub desc: Option<String>,
    pub status: Option<String>,
    pub ms: Option<u64>,
    pub phase: Option<u8>,
    pub method: Option<String>,
    pub error: Option<String>,
    pub path: Option<String>,
    pub passed: Option<u32>,
    pub failed: Option<u32>,
    pub healed: Option<u32>,
    pub step_total: Option<u32>,
    pub heal_log: Option<String>,
}

pub struct AutoRunnerState {
    pub runs: Mutex<HashMap<String, (Arc<AtomicBool>, Mutex<Child>)>>,
}

impl AutoRunnerState {
    pub fn new() -> Self {
        Self {
            runs: Mutex::new(HashMap::new()),
        }
    }

    pub fn insert(&self, run_id: String, running: Arc<AtomicBool>, child: Child) {
        self.runs
            .lock()
            .unwrap()
            .insert(run_id, (running, Mutex::new(child)));
    }

    pub fn remove(&self, run_id: &str) -> Option<(Arc<AtomicBool>, Child)> {
        self.runs
            .lock()
            .unwrap()
            .remove(run_id)
            .map(|(flag, mutex)| (flag, mutex.into_inner().unwrap()))
    }
}

fn spawn_python(
    main_py: &str,
    args: &[&str],
) -> Result<Child, String> {
    let mut cmd = Command::new("python");
    #[cfg(target_os = "windows")]
    cmd.creation_flags(0x08000000);

    cmd.arg("-u").arg(main_py);
    for arg in args {
        cmd.arg(arg);
    }

    cmd.stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(|e| format!("Failed to spawn Python engine: {}", e))
}

fn start_run(
    app: &tauri::AppHandle,
    state: &AutoRunnerState,
    run_id: String,
    child: Child,
) {
    let mut child = child;
    let stdout = child.stdout.take();
    let running = Arc::new(AtomicBool::new(true));

    state.insert(run_id.clone(), running.clone(), child);

    let app_clone = app.clone();
    let run_id_clone = run_id.clone();
    std::thread::spawn(move || {
        if let Some(stdout) = stdout {
            let reader = BufReader::new(stdout);
            for line in reader.lines().flatten() {
                if !running.load(Ordering::Relaxed) {
                    break;
                }
                if let Ok(event) = serde_json::from_str::<AutoStepEvent>(&line) {
                    let _ = app_clone.emit("auto:step_event", &event);
                }
            }
        }

        // Process exited, clean up
        let state = app_clone.state::<AutoRunnerState>();
        if let Some((_, mut child)) = state.remove(&run_id_clone) {
            let _ = child.wait();
        }
        let _ = app_clone.emit(
            "auto:step_event",
            &AutoStepEvent {
                event_type: "suite_done".to_string(),
                step_id: None,
                desc: None,
                status: None,
                ms: None,
                phase: None,
                method: None,
                error: None,
                path: None,
                passed: None,
                failed: None,
                healed: None,
                step_total: None,
                heal_log: None,
            },
        );
    });
}

#[tauri::command]
pub fn auto_run_case(
    app: tauri::AppHandle,
    state: tauri::State<'_, AutoRunnerState>,
    run_id: String,
    case_id: String,
    device_serial: String,
) -> Result<(), String> {
    let engine_dir = app
        .path()
        .resource_dir()
        .map(|d| d.join("tv_engine").to_string_lossy().to_string())
        .unwrap_or_default();

    let main_py = format!("{}/main.py", engine_dir);
    let child = spawn_python(
        &main_py,
        &["run", "--case-id", &case_id, "--device", &device_serial, "--run-id", &run_id],
    )?;

    start_run(&app, &state, run_id, child);
    Ok(())
}

#[tauri::command]
pub fn auto_run_suite(
    app: tauri::AppHandle,
    state: tauri::State<'_, AutoRunnerState>,
    run_id: String,
    case_ids: Vec<String>,
    device_serial: String,
) -> Result<(), String> {
    let engine_dir = app
        .path()
        .resource_dir()
        .map(|d| d.join("tv_engine").to_string_lossy().to_string())
        .unwrap_or_default();

    let main_py = format!("{}/main.py", engine_dir);
    let child = spawn_python(
        &main_py,
        &["run", "--suite", &case_ids.join(","), "--device", &device_serial, "--run-id", &run_id],
    )?;

    start_run(&app, &state, run_id, child);
    Ok(())
}

#[tauri::command]
pub fn auto_stop_run(
    state: tauri::State<'_, AutoRunnerState>,
    run_id: String,
) -> Result<(), String> {
    if let Some((running, mut child)) = state.remove(&run_id) {
        running.store(false, Ordering::Relaxed);
        let _ = child.kill();
        let _ = child.wait();
    }
    Ok(())
}

#[tauri::command]
pub fn auto_gen_skeleton(
    graph_json: String,
    package: String,
) -> Result<String, String> {
    let data: serde_json::Value =
        serde_json::from_str(&graph_json).map_err(|e| format!("Invalid graph JSON: {}", e))?;
    let nodes = data.get("nodes").and_then(|v| v.as_object()).ok_or("No nodes in graph")?;
    let mut step_count = 0u32;
    let mut steps_yaml = String::new();
    for (fp, state) in nodes {
        let activity = state.get("activity").and_then(|v| v.as_str()).unwrap_or("");
        let focused_id = state.get("focused_id").and_then(|v| v.as_str()).unwrap_or("");
        let focused_desc = state.get("focused_desc").and_then(|v| v.as_str()).unwrap_or("");
        if focused_id.is_empty() && focused_desc.is_empty() {
            continue;
        }
        step_count += 1;
        steps_yaml.push_str(&format!(
            r#"  - id: "step_{:02}"
    desc: "navigate to {}"
    action: navigate_to
    target:
      primary:
        by: resource_id
        value: "{}"
    on_failure: "ai_heal"
"#,
            step_count,
            if focused_desc.is_empty() { focused_id } else { focused_desc },
            focused_id
        ));
    }
    let skeleton = format!(
        r#"# Auto-generated from StateGraph - {}
meta:
  id: "TC-{}-001"
  name: "Auto-generated case from {}"
  author: ""
  version: "1.0"
  tags:
    - "auto_gen"
  priority: "P2"
  description: "Auto-generated test case from StateGraph exploration"

setup:
  - action: launch_app
    package: "{}"
    wait_activity: ""
    timeout: 8000

steps:
{}

teardown:
  - action: press_key
    key: HOME
"#,
        package, package, package, package, steps_yaml
    );
    Ok(skeleton)
}

#[tauri::command]
pub fn auto_check_engine() -> Result<String, String> {
    let output = Command::new("python")
        .arg("--version")
        .output()
        .map_err(|e| format!("Python not found: {}", e))?;

    if output.status.success() {
        Ok("ok".to_string())
    } else {
        Err("Python engine not available".to_string())
    }
}
