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

fn resolve_engine_path(app: &tauri::AppHandle) -> String {
    // Collect candidates from most likely to least
    let cwd = std::env::current_dir().ok();
    let res_dir = app.path().resource_dir().ok();
    let exe_dir = app.path().app_local_data_dir().ok();

    let mut candidates: Vec<std::path::PathBuf> = Vec::new();

    // During dev: cwd is typically test-space/src-tauri
    if let Some(ref d) = cwd {
        // relative to src-tauri: ../../tv_engine (project root sibling)
        candidates.push(d.join("..").join("..").join("tv_engine").join("main.py"));
        // relative to src-tauri parent: ../tv_engine
        candidates.push(d.join("..").join("tv_engine").join("main.py"));
        // relative to src-tauri itself
        candidates.push(d.join("tv_engine").join("main.py"));
    }

    // Bundled resource (production)
    if let Some(ref d) = res_dir {
        candidates.push(d.join("tv_engine").join("main.py"));
    }

    // Relative to Tauri app data dir
    if let Some(ref d) = exe_dir {
        candidates.push(d.join("tv_engine").join("main.py"));
    }

    // During dev: exe is in target/debug/, go up 4 levels to project root
    if let Ok(exe) = std::env::current_exe() {
        if let Some(parent) = exe.parent() {
            candidates.push(parent.join("..").join("..").join("..").join("..")
                .join("tv_engine").join("main.py"));
        }
    }

    for c in &candidates {
        if c.exists() {
            return c.to_string_lossy().to_string();
        }
    }

    // Last resort: return the first candidate for the error message
    candidates.into_iter().next()
        .map(|p| p.to_string_lossy().to_string())
        .unwrap_or_default()
}

fn spawn_python(
    main_py: &str,
    args: &[&str],
    app: &tauri::AppHandle,
) -> Result<Child, String> {
    let main_path = std::path::Path::new(main_py);
    if main_py.is_empty() || !main_path.exists() {
        return Err(format!("Engine script not found: {}", main_py));
    }

    // Set working directory to parent of tv_engine/ and use -m tv_engine.main
    // so that `from tv_engine.core.runner import ...` resolves correctly.
    // main_py = <parent>/tv_engine/main.py
    // working_dir = <parent>  (parent of tv_engine/)
    let engine_dir = main_path.parent().unwrap_or_else(|| std::path::Path::new("."));
    let working_dir = engine_dir.parent().unwrap_or_else(|| std::path::Path::new("."));

    let mut cmd = Command::new("python");
    #[cfg(target_os = "windows")]
    cmd.creation_flags(0x08000000);

    cmd.arg("-u").arg("-m").arg("tv_engine.main");
    for arg in args {
        cmd.arg(arg);
    }

    // Set TV_SCREENSHOTS_DIR so Python engine can resolve reference screenshot paths
    if let Ok(screenshots_dir) = app.path().app_local_data_dir().map(|d| d.join("auto_screenshots")) {
        cmd.env("TV_SCREENSHOTS_DIR", screenshots_dir.to_string_lossy().as_ref());
    }

    cmd.stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .current_dir(working_dir)
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
    let stderr = child.stderr.take();
    let running = Arc::new(AtomicBool::new(true));

    state.insert(run_id.clone(), running.clone(), child);

    let app_clone = app.clone();
    let run_id_clone = run_id.clone();
    std::thread::spawn(move || {
        // Read stderr in a separate thread
        let err_app = app_clone.clone();
        let err_running = running.clone();
        std::thread::spawn(move || {
            if let Some(stderr) = stderr {
                let reader = BufReader::new(stderr);
                for line in reader.lines().flatten() {
                    if !err_running.load(Ordering::Relaxed) {
                        break;
                    }
                    let _ = err_app.emit(
                        "auto:step_event",
                        &AutoStepEvent {
                            event_type: "engine_log".to_string(),
                            step_id: None,
                            desc: Some(line),
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
                }
            }
        });

        // Read stdout
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
    yaml_content: String,
    device_serial: String,
) -> Result<(), String> {
    let main_py = resolve_engine_path(&app);

    // Write YAML content to a temp file so Python can read it
    let tmp_dir = app.path().app_local_data_dir()
        .map(|d| d.join("auto_runs").join(&run_id))
        .unwrap_or_else(|_| std::env::temp_dir().join("auto_runs").join(&run_id));
    std::fs::create_dir_all(&tmp_dir).map_err(|e| format!("Failed to create temp dir: {}", e))?;
    let yaml_path = tmp_dir.join("case.yaml");
    std::fs::write(&yaml_path, &yaml_content)
        .map_err(|e| format!("Failed to write YAML file: {}", e))?;

    let yaml_str = yaml_path.to_string_lossy();
    let child = spawn_python(
        &main_py,
        &["run", &yaml_str, "--device", &device_serial, "--run-id", &run_id],
        &app,
    )?;

    start_run(&app, &state, run_id, child);
    Ok(())
}

#[tauri::command]
pub fn auto_run_suite(
    app: tauri::AppHandle,
    state: tauri::State<'_, AutoRunnerState>,
    run_id: String,
    yaml_contents: Vec<String>,
    device_serial: String,
) -> Result<(), String> {
    let main_py = resolve_engine_path(&app);

    // Write each case's YAML to a temp file
    let tmp_dir = app.path().app_local_data_dir()
        .map(|d| d.join("auto_runs").join(&run_id))
        .unwrap_or_else(|_| std::env::temp_dir().join("auto_runs").join(&run_id));
    std::fs::create_dir_all(&tmp_dir).map_err(|e| format!("Failed to create temp dir: {}", e))?;

    let mut suite_args: Vec<String> = Vec::new();
    suite_args.push("run-suite".to_string());
    for (i, content) in yaml_contents.iter().enumerate() {
        let yaml_path = tmp_dir.join(format!("case_{}.yaml", i));
        std::fs::write(&yaml_path, content)
            .map_err(|e| format!("Failed to write YAML file: {}", e))?;
        suite_args.push(yaml_path.to_string_lossy().to_string());
    }
    suite_args.push("--device".to_string());
    suite_args.push(device_serial);
    suite_args.push("--run-id".to_string());
    suite_args.push(run_id.clone());

    let child = spawn_python(&main_py, &suite_args.iter().map(|s| s.as_str()).collect::<Vec<_>>(), &app)?;

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
    for (_fp, state) in nodes {
        let _activity = state.get("activity").and_then(|v| v.as_str()).unwrap_or("");
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
