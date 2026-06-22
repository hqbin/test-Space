mod adb;
mod mirror;
mod proxy;
mod script_exec;
mod serial_port;
mod zip_util;

use script_exec::{ScriptManager, script_spawn, script_kill};
use serial_port::SerialState;
use std::collections::HashMap;
use base64::Engine;
use std::sync::atomic::{AtomicBool, AtomicU16, Ordering};
use std::sync::Arc;
use tauri::menu::{Menu, MenuItem};
use tauri::tray::TrayIconBuilder;
use std::sync::Mutex;
use std::time::Duration;
#[cfg(target_os = "windows")]
use std::os::windows::process::CommandExt;
use tauri::Emitter;
use tauri::Manager;
use tauri_plugin_single_instance::init as single_instance_init;

type MirrorKey = (String, String); // (serial, window_label)
struct MirrorState(Mutex<HashMap<MirrorKey, (Arc<AtomicBool>, u16)>>);

static NEXT_MIRROR_PORT: AtomicU16 = AtomicU16::new(27183);

#[tauri::command]
fn adb_list_devices() -> Vec<adb::DeviceInfo> {
    adb::list_devices()
}

#[tauri::command]
async fn adb_shell(serial: String, command: String) -> Result<String, String> {
    tokio::task::spawn_blocking(move || {
        adb::shell_command(&serial, &command)
    }).await.map_err(|e| e.to_string())?
}

#[tauri::command]
async fn adb_install(serial: String, apk_path: String, reinstall: bool) -> Result<String, String> {
    let output = tokio::time::timeout(Duration::from_secs(120), async {
        let mut cmd = std::process::Command::new("adb");
        #[cfg(target_os = "windows")]
        cmd.creation_flags(0x08000000);
        cmd.args(["-s", &serial, "install"]);
        if reinstall { cmd.arg("-r"); }
        cmd.arg(&apk_path);
        tokio::process::Command::from(cmd).output().await
            .map_err(|e| format!("ADB install failed: {}", e))
    }).await
        .map_err(|_| "ADB install timed out (120s)".to_string())?
        .map_err(|e| e.to_string())?;

    if output.status.success() {
        Ok(String::from_utf8_lossy(&output.stdout).to_string())
    } else {
        let stderr = String::from_utf8_lossy(&output.stderr).to_string();
        Err(if stderr.is_empty() { "Unknown error".to_string() } else { stderr })
    }
}

#[tauri::command]
async fn adb_uninstall(serial: String, package: String) -> Result<String, String> {
    tokio::task::spawn_blocking(move || {
        adb::uninstall_apk(&serial, &package)
    }).await.map_err(|e| e.to_string())?
}

#[tauri::command]
async fn adb_push(serial: String, local: String, remote: String) -> Result<String, String> {
    tokio::task::spawn_blocking(move || {
        adb::push_file(&serial, &local, &remote)
    }).await.map_err(|e| e.to_string())?
}

#[tauri::command]
async fn adb_push_bytes(serial: String, remote: String, filename: String, data: Vec<u8>) -> Result<String, String> {
    let tmp_dir = std::env::temp_dir();
    let tmp_path = tmp_dir.join(&filename);
    std::fs::write(&tmp_path, &data).map_err(|e| format!("Failed to write temp file: {}", e))?;
    let result = tokio::task::spawn_blocking(move || {
        let r = adb::push_file(&serial, &tmp_path.to_string_lossy(), &remote);
        let _ = std::fs::remove_file(&tmp_path);
        r
    }).await.map_err(|e| e.to_string())?;
    result
}

#[tauri::command]
async fn adb_pull(serial: String, remote: String, local: String) -> Result<String, String> {
    tokio::task::spawn_blocking(move || {
        adb::pull_file(&serial, &remote, &local)
    }).await.map_err(|e| e.to_string())?
}

#[tauri::command]
async fn adb_reboot(serial: String) -> Result<String, String> {
    tokio::task::spawn_blocking(move || {
        adb::reboot(&serial)
    }).await.map_err(|e| e.to_string())?
}

#[tauri::command]
async fn adb_screenshot(serial: String, save_path: String) -> Result<String, String> {
    tokio::task::spawn_blocking(move || {
        adb::screenshot(&serial, &save_path)
    }).await.map_err(|e| e.to_string())?
}

#[tauri::command]
async fn adb_mirror_start(
    serial: String,
    window: tauri::Window,
    app: tauri::AppHandle,
    state: tauri::State<'_, MirrorState>,
    on_frame: tauri::ipc::Channel<Vec<u8>>,
    max_size: Option<u16>,
    video_bit_rate: Option<u32>,
    max_fps: Option<u8>,
) -> Result<(), String> {
    let max_size = max_size.unwrap_or(960);
    let video_bit_rate = video_bit_rate.unwrap_or(3_000_000);
    let max_fps = max_fps.unwrap_or(15);
    let port = NEXT_MIRROR_PORT.fetch_add(1, Ordering::Relaxed);
    let running = Arc::new(AtomicBool::new(true));
    let win_label = window.label().to_string();
    state.0.lock().unwrap().insert((serial.clone(), win_label.clone()), (running.clone(), port));

    // Resolve scrcpy-server path before spawning
    let jar_str = app.path().resource_dir()
        .map(|d| d.join("bin/scrcpy-server").to_string_lossy().to_string())
        .unwrap_or_default();

    let serial_c = serial.clone();
    let running_c = running.clone();
    let app_c = app.clone();

    tokio::task::spawn_blocking(move || {
        // Try scrcpy-server; if any step fails or config not received, fall back to legacy
        let scrcpy_ok = if jar_str.is_empty() {
            let _ = app_c.emit_to(&win_label, "mirror:diagnostic", "scrcpy-server jar not found in app resources");
            false
        } else if let Err(e) = mirror::push_server(&serial_c, &jar_str) {
            let _ = app_c.emit_to(&win_label, "mirror:diagnostic", &format!("scrcpy-server push failed: {}", e));
            false
        } else {
            mirror::remove_forward(&serial_c, port);
            if let Err(e) = mirror::setup_forward(&serial_c, port) {
                let _ = app_c.emit_to(&win_label, "mirror:diagnostic", &format!("ADB forward failed: {}", e));
                false
            } else if let Err(e) = mirror::start_server(&serial_c, max_size, video_bit_rate, max_fps) {
                let _ = app_c.emit_to(&win_label, "mirror:diagnostic", &format!("scrcpy-server start failed: {}", e));
                false
            } else {
                true
            }
        };

        if scrcpy_ok {
            let _ = app_c.emit_to(&win_label, "mirror:mode", "scrcpy");
            let _ = app_c.emit_to(&win_label, "mirror:ready", "");
            let mut stream_result = Err("not started".into());
            for attempt in 0..3 {
                if !running_c.load(Ordering::Relaxed) { break; }
                if attempt > 0 {
                    std::thread::sleep(Duration::from_secs(2));
                }
                stream_result = mirror::connect_and_stream(app_c.clone(), running_c.clone(), port, &win_label, on_frame.clone());
                if stream_result.is_ok() { break; }
            }
            mirror::remove_forward(&serial_c, port);
            if let Ok(()) = stream_result {
                running_c.store(false, Ordering::Relaxed);
                return;
            }
            if let Err(ref msg) = stream_result {
                let _ = app_c.emit_to(&win_label, "mirror:diagnostic", &format!("scrcpy: {}", msg));
            }
        }
        let _ = app_c.emit_to(&win_label, "mirror:mode", "legacy");

        while running_c.load(Ordering::Relaxed) {
            match adb::screenshot(&serial_c, "") {
                Ok(data_url) => {
                    let png_base64 = data_url.strip_prefix("data:image/png;base64,").unwrap_or(&data_url);
                    if let Ok(raw) = base64::engine::general_purpose::STANDARD.decode(png_base64) {
                        let mut payload = vec![1u8]; // key flag = true
                        payload.extend_from_slice(&raw);
                        let _ = on_frame.send(payload);
                    }
                }
                Err(e) => {
                    let _ = app_c.emit_to(&win_label, "mirror:error", &format!("截图失败: {}", e));
                    break;
                }
            }
            std::thread::sleep(Duration::from_millis(200));
        }

        running_c.store(false, Ordering::Relaxed);
    });

    Ok(())
}

#[tauri::command]
fn adb_mirror_stop(serial: String, window: tauri::Window, state: tauri::State<'_, MirrorState>) -> Result<(), String> {
    let win_label = window.label().to_string();
    if let Some((flag, port)) = state.0.lock().unwrap().remove(&(serial.clone(), win_label)) {
        flag.store(false, Ordering::Relaxed);
        mirror::remove_forward(&serial, port);
    }
    Ok(())
}

#[tauri::command]
async fn adb_connect(address: String) -> Result<String, String> {
    tokio::task::spawn_blocking(move || {
        adb::connect_device(&address)
    }).await.map_err(|e| e.to_string())?
}

#[tauri::command]
async fn adb_disconnect(serial: String) -> Result<String, String> {
    tokio::task::spawn_blocking(move || {
        adb::disconnect_device(&serial)
    }).await.map_err(|e| e.to_string())?
}

#[tauri::command]
async fn adb_reboot_recovery(serial: String) -> Result<String, String> {
    tokio::task::spawn_blocking(move || {
        adb::reboot_recovery(&serial)
    }).await.map_err(|e| e.to_string())?
}

#[tauri::command]
async fn adb_reboot_bootloader(serial: String) -> Result<String, String> {
    tokio::task::spawn_blocking(move || {
        adb::reboot_bootloader(&serial)
    }).await.map_err(|e| e.to_string())?
}

#[tauri::command]
async fn adb_root(serial: String) -> Result<String, String> {
    tokio::task::spawn_blocking(move || {
        adb::root_device(&serial)
    }).await.map_err(|e| e.to_string())?
}

#[tauri::command]
async fn adb_remount(serial: String) -> Result<String, String> {
    tokio::task::spawn_blocking(move || {
        adb::remount_device(&serial)
    }).await.map_err(|e| e.to_string())?
}

#[tauri::command]
async fn adb_get_properties(serial: String) -> Result<adb::DeviceProperties, String> {
    tokio::task::spawn_blocking(move || {
        adb::get_device_properties(&serial)
    }).await.map_err(|e| e.to_string())?
}

#[tauri::command]
async fn adb_input_keyevent(serial: String, keycode: String) -> Result<String, String> {
    tokio::task::spawn_blocking(move || {
        adb::input_keyevent(&serial, &keycode)
    }).await.map_err(|e| e.to_string())?
}

#[tauri::command]
async fn adb_input_text(serial: String, text: String) -> Result<String, String> {
    tokio::task::spawn_blocking(move || {
        adb::input_text(&serial, &text)
    }).await.map_err(|e| e.to_string())?
}

#[tauri::command]
async fn adb_input_tap(serial: String, x: i32, y: i32) -> Result<String, String> {
    tokio::task::spawn_blocking(move || {
        adb::input_tap(&serial, x, y)
    }).await.map_err(|e| e.to_string())?
}

#[tauri::command]
async fn adb_input_swipe(serial: String, x1: i32, y1: i32, x2: i32, y2: i32, duration: i32) -> Result<String, String> {
    tokio::task::spawn_blocking(move || {
        adb::input_swipe(&serial, x1, y1, x2, y2, duration)
    }).await.map_err(|e| e.to_string())?
}

#[tauri::command]
async fn adb_list_packages(serial: String, third_party_only: bool) -> Result<Vec<String>, String> {
    tokio::task::spawn_blocking(move || {
        adb::list_packages(&serial, third_party_only)
    }).await.map_err(|e| e.to_string())?
}

#[tauri::command]
async fn adb_start_app(serial: String, package: String) -> Result<String, String> {
    tokio::task::spawn_blocking(move || {
        adb::start_app(&serial, &package)
    }).await.map_err(|e| e.to_string())?
}

#[tauri::command]
async fn adb_stop_app(serial: String, package: String) -> Result<String, String> {
    tokio::task::spawn_blocking(move || {
        adb::stop_app(&serial, &package)
    }).await.map_err(|e| e.to_string())?
}

#[tauri::command]
async fn adb_get_display_size(serial: String) -> Result<(u32, u32), String> {
    tokio::task::spawn_blocking(move || {
        adb::get_display_size(&serial)
    }).await.map_err(|e| e.to_string())?
}

#[tauri::command]
async fn adb_clear_app_data(serial: String, package: String) -> Result<String, String> {
    tokio::task::spawn_blocking(move || {
        adb::clear_app_data(&serial, &package)
    }).await.map_err(|e| e.to_string())?
}

#[tauri::command]
async fn adb_get_current_app(serial: String) -> Result<String, String> {
    tokio::task::spawn_blocking(move || {
        adb::get_current_app(&serial)
    }).await.map_err(|e| e.to_string())?
}

#[tauri::command]
async fn adb_logcat_clear(serial: String) -> Result<String, String> {
    tokio::task::spawn_blocking(move || {
        adb::logcat_clear(&serial)
    }).await.map_err(|e| e.to_string())?
}

#[tauri::command]
async fn adb_logcat(serial: String, buffer: String, lines: i32) -> Result<String, String> {
    tokio::task::spawn_blocking(move || {
        adb::logcat(&serial, &buffer, lines)
    }).await.map_err(|e| e.to_string())?
}

#[tauri::command]
async fn adb_get_battery(serial: String) -> Result<String, String> {
    tokio::task::spawn_blocking(move || {
        adb::get_battery_info(&serial)
    }).await.map_err(|e| e.to_string())?
}

#[tauri::command]
async fn adb_list_directory(serial: String, path: String) -> Result<String, String> {
    tokio::task::spawn_blocking(move || {
        adb::list_directory(&serial, &path)
    }).await.map_err(|e| e.to_string())?
}

#[tauri::command]
async fn adb_get_app_info(serial: String, package: String) -> Result<String, String> {
    tokio::task::spawn_blocking(move || {
        adb::get_app_info(&serial, &package)
    }).await.map_err(|e| e.to_string())?
}

#[tauri::command]
async fn adb_get_cpu(serial: String) -> Result<String, String> {
    tokio::task::spawn_blocking(move || {
        adb::get_cpu_info(&serial)
    }).await.map_err(|e| e.to_string())?
}

#[tauri::command]
async fn adb_get_memory(serial: String) -> Result<String, String> {
    tokio::task::spawn_blocking(move || {
        adb::get_memory_info(&serial)
    }).await.map_err(|e| e.to_string())?
}

#[tauri::command]
async fn adb_logcat_buffer_resize(serial: String, size_mb: u32) -> Result<String, String> {
    tokio::task::spawn_blocking(move || {
        adb::logcat_buffer_resize(&serial, size_mb)
    }).await.map_err(|e| e.to_string())?
}

#[tauri::command]
async fn adb_dmesg(serial: String) -> Result<String, String> {
    tokio::task::spawn_blocking(move || {
        adb::dmesg(&serial)
    }).await.map_err(|e| e.to_string())?
}

#[tauri::command]
async fn adb_bugreport(serial: String, save_path: String) -> Result<String, String> {
    tokio::task::spawn_blocking(move || {
        adb::bugreport(&serial, &save_path)
    }).await.map_err(|e| e.to_string())?
}

#[tauri::command]
async fn adb_start_screenrecord(serial: String, file_path: String, width: u32, height: u32) -> Result<String, String> {
    tokio::task::spawn_blocking(move || {
        adb::start_screenrecord(&serial, &file_path, width, height)
    }).await.map_err(|e| e.to_string())?
}

#[derive(serde::Deserialize)]
struct ZipFileEntry {
    filename: String,
    content: String,
}

#[tauri::command]
fn create_zip(files: Vec<ZipFileEntry>, dest_path: String) -> Result<String, String> {
    zip_util::create_zip_from_memory(&files, &dest_path)
}

#[tauri::command]
async fn adb_kill_server() -> Result<String, String> {
    tokio::task::spawn_blocking(move || {
        adb::kill_server()
    }).await.map_err(|e| e.to_string())?
}

#[tauri::command]
async fn adb_start_server() -> Result<String, String> {
    tokio::task::spawn_blocking(move || {
        adb::start_server()
    }).await.map_err(|e| e.to_string())?
}

#[tauri::command]
fn serial_list_ports() -> Vec<String> {
    serial_port::list_ports()
}

#[tauri::command]
fn serial_connect(state: tauri::State<SerialState>, port_name: String, baud_rate: u32) -> Result<(), String> {
    serial_port::connect(&state, &port_name, baud_rate)
}

#[tauri::command]
fn serial_disconnect(state: tauri::State<SerialState>) -> Result<(), String> {
    serial_port::disconnect(&state)
}

#[tauri::command]
fn serial_send(state: tauri::State<SerialState>, command: String) -> Result<(), String> {
    serial_port::send_command(&state, &command)
}

#[tauri::command]
fn serial_read(state: tauri::State<SerialState>) -> Result<String, String> {
    serial_port::read_data(&state)
}

#[tauri::command]
fn script_execute_python(script_path: String, args: Vec<String>) -> Result<script_exec::ScriptResult, String> {
    script_exec::execute_python(&script_path, &args)
}

#[tauri::command]
fn script_execute_bat(script_path: String, args: Vec<String>) -> Result<script_exec::ScriptResult, String> {
    script_exec::execute_bat(&script_path, &args)
}

#[tauri::command]
fn script_execute_powershell(script_path: String, args: Vec<String>) -> Result<script_exec::ScriptResult, String> {
    script_exec::execute_powershell(&script_path, &args)
}

#[tauri::command]
fn script_execute_shell(command: String) -> Result<script_exec::ScriptResult, String> {
    script_exec::execute_shell(&command)
}

#[tauri::command]
fn write_text_file(path: String, content: String) -> Result<(), String> {
    std::fs::write(&path, &content).map_err(|e| e.to_string())
}

#[tauri::command]
fn write_script_file(path: String, content: String, interpreter: String) -> Result<(), String> {
    if interpreter == "bat" {
        // Normalize to CRLF for cmd.exe compatibility
        let crlf = content.replace("\r\n", "\n").replace('\n', "\r\n");
        std::fs::write(&path, &crlf).map_err(|e| e.to_string())
    } else {
        std::fs::write(&path, &content).map_err(|e| e.to_string())
    }
}

#[tauri::command]
fn read_text_file(path: String) -> Result<String, String> {
    let bytes = std::fs::read(&path).map_err(|e| e.to_string())?;
    Ok(String::from_utf8_lossy(&bytes).to_string())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(single_instance_init(|app, _args, _cwd| {
            // 当用户再次双击打开应用时，聚焦已有窗口
            if let Some(window) = app.get_webview_window("main") {
                let _ = window.show();
                let _ = window.set_focus();
            }
        }))
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_sql::Builder::default().build())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_http::init())
        .manage(SerialState {
            port: Mutex::new(None),
        })
        .manage(MirrorState(Mutex::new(HashMap::new())))
        .manage(ScriptManager::new())
        .manage(proxy::ProxyState::new())
        .setup(|app| {
            if cfg!(debug_assertions) {
                app.handle().plugin(
                    tauri_plugin_log::Builder::default()
                        .level(log::LevelFilter::Info)
                        .build(),
                )?;
            }

            if let Some(window) = app.get_webview_window("main") {
                let w = window.clone();
                window.on_window_event(move |event| {
                    if let tauri::WindowEvent::CloseRequested { api, .. } = event {
                        api.prevent_close();
                        let _ = w.hide();
                    }
                });
            }

            let show_item = MenuItem::with_id(app, "show", "显示窗口", true, None::<&str>)?;
            let quit_item = MenuItem::with_id(app, "quit", "退出", true, None::<&str>)?;
            let menu = Menu::with_items(app, &[&show_item, &quit_item])?;

            let _tray = TrayIconBuilder::new()
                .icon(app.default_window_icon().unwrap().clone())
                .tooltip("TestSpace")
                .menu(&menu)
                .show_menu_on_left_click(false)
                .on_menu_event(move |app, event| {
                    match event.id().as_ref() {
                        "show" => {
                            if let Some(win) = app.get_webview_window("main") {
                                let _ = win.show();
                                let _ = win.set_focus();
                            }
                        }
                        "quit" => {
                            app.exit(0);
                        }
                        _ => {}
                    }
                })
                .on_tray_icon_event(move |tray, event| {
                    if let tauri::tray::TrayIconEvent::Click { button: tauri::tray::MouseButton::Left, .. } = event {
                        if let Some(win) = tray.app_handle().get_webview_window("main") {
                            let _ = win.show();
                            let _ = win.set_focus();
                        }
                    }
                })
                .build(app)?;

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            adb_list_devices,
            adb_shell,
            adb_install,
            adb_uninstall,
            adb_push,
            adb_push_bytes,
            adb_pull,
            adb_reboot,
            adb_screenshot,
            adb_mirror_start,
            adb_mirror_stop,
            adb_connect,
            adb_disconnect,
            adb_reboot_recovery,
            adb_reboot_bootloader,
            adb_root,
            adb_remount,
            adb_get_properties,
            adb_input_keyevent,
            adb_input_text,
            adb_input_tap,
            adb_input_swipe,
            adb_get_display_size,
            adb_list_packages,
            adb_start_app,
            adb_stop_app,
            adb_clear_app_data,
            adb_get_current_app,
            adb_logcat_clear,
            adb_logcat,
            adb_get_battery,
            adb_get_cpu,
            adb_get_memory,
            adb_logcat_buffer_resize,
            adb_bugreport,
            adb_dmesg,
            adb_kill_server,
            adb_start_server,
            adb_start_screenrecord,
            create_zip,
            adb_list_directory,
            adb_get_app_info,
            serial_list_ports,
            serial_connect,
            serial_disconnect,
            serial_send,
            serial_read,
            script_execute_python,
            script_execute_bat,
            script_execute_powershell,
            script_execute_shell,
            script_spawn,
            script_kill,
            write_text_file,
            write_script_file,
            read_text_file,
            proxy::proxy_start,
            proxy::proxy_stop,
            proxy::proxy_set_breakpoint,
            proxy::proxy_continue,
            proxy::proxy_add_rewrite_rule,
            proxy::proxy_remove_rewrite_rule,
            proxy::proxy_update_rewrite_rule,
            proxy::proxy_clear_rewrite_rules,
            proxy::proxy_get_rewrite_rules,
            proxy::proxy_get_captured,
            proxy::proxy_get_status,
            proxy::proxy_get_ca_cert,
            proxy::proxy_set_device_proxy,
            proxy::proxy_clear_device_proxy,
            proxy::proxy_install_cert,
            proxy::proxy_replay,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
