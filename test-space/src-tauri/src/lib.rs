mod adb;
mod script_exec;
mod serial_port;

use serial_port::SerialState;
use std::sync::Mutex;

#[tauri::command]
fn adb_list_devices() -> Vec<adb::DeviceInfo> {
    adb::list_devices()
}

#[tauri::command]
fn adb_shell(serial: String, command: String) -> Result<String, String> {
    adb::shell_command(&serial, &command)
}

#[tauri::command]
fn adb_install(serial: String, apk_path: String) -> Result<String, String> {
    adb::install_apk(&serial, &apk_path)
}

#[tauri::command]
fn adb_uninstall(serial: String, package: String) -> Result<String, String> {
    adb::uninstall_apk(&serial, &package)
}

#[tauri::command]
fn adb_push(serial: String, local: String, remote: String) -> Result<String, String> {
    adb::push_file(&serial, &local, &remote)
}

#[tauri::command]
fn adb_pull(serial: String, remote: String, local: String) -> Result<String, String> {
    adb::pull_file(&serial, &remote, &local)
}

#[tauri::command]
fn adb_reboot(serial: String) -> Result<String, String> {
    adb::reboot(&serial)
}

#[tauri::command]
fn adb_screenshot(serial: String, save_path: String) -> Result<String, String> {
    adb::screenshot(&serial, &save_path)
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
fn read_text_file(path: String) -> Result<String, String> {
    std::fs::read_to_string(&path).map_err(|e| e.to_string())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_sql::Builder::default().build())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .manage(SerialState {
            port: Mutex::new(None),
        })
        .setup(|app| {
            if cfg!(debug_assertions) {
                app.handle().plugin(
                    tauri_plugin_log::Builder::default()
                        .level(log::LevelFilter::Info)
                        .build(),
                )?;
            }
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            adb_list_devices,
            adb_shell,
            adb_install,
            adb_uninstall,
            adb_push,
            adb_pull,
            adb_reboot,
            adb_screenshot,
            serial_list_ports,
            serial_connect,
            serial_disconnect,
            serial_send,
            serial_read,
            script_execute_python,
            script_execute_bat,
            script_execute_powershell,
            script_execute_shell,
            write_text_file,
            read_text_file,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
