mod adb;
mod script_exec;
mod serial_port;
mod zip_util;

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
fn adb_install(serial: String, apk_path: String, reinstall: bool) -> Result<String, String> {
    adb::install_apk(&serial, &apk_path, reinstall)
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
fn adb_connect(address: String) -> Result<String, String> {
    adb::connect_device(&address)
}

#[tauri::command]
fn adb_disconnect(serial: String) -> Result<String, String> {
    adb::disconnect_device(&serial)
}

#[tauri::command]
fn adb_reboot_recovery(serial: String) -> Result<String, String> {
    adb::reboot_recovery(&serial)
}

#[tauri::command]
fn adb_reboot_bootloader(serial: String) -> Result<String, String> {
    adb::reboot_bootloader(&serial)
}

#[tauri::command]
fn adb_root(serial: String) -> Result<String, String> {
    adb::root_device(&serial)
}

#[tauri::command]
fn adb_remount(serial: String) -> Result<String, String> {
    adb::remount_device(&serial)
}

#[tauri::command]
fn adb_get_properties(serial: String) -> Result<adb::DeviceProperties, String> {
    adb::get_device_properties(&serial)
}

#[tauri::command]
fn adb_input_keyevent(serial: String, keycode: String) -> Result<String, String> {
    adb::input_keyevent(&serial, &keycode)
}

#[tauri::command]
fn adb_input_text(serial: String, text: String) -> Result<String, String> {
    adb::input_text(&serial, &text)
}

#[tauri::command]
fn adb_input_tap(serial: String, x: i32, y: i32) -> Result<String, String> {
    adb::input_tap(&serial, x, y)
}

#[tauri::command]
fn adb_input_swipe(serial: String, x1: i32, y1: i32, x2: i32, y2: i32, duration: i32) -> Result<String, String> {
    adb::input_swipe(&serial, x1, y1, x2, y2, duration)
}

#[tauri::command]
fn adb_list_packages(serial: String, third_party_only: bool) -> Result<Vec<String>, String> {
    adb::list_packages(&serial, third_party_only)
}

#[tauri::command]
fn adb_start_app(serial: String, package: String) -> Result<String, String> {
    adb::start_app(&serial, &package)
}

#[tauri::command]
fn adb_stop_app(serial: String, package: String) -> Result<String, String> {
    adb::stop_app(&serial, &package)
}

#[tauri::command]
fn adb_clear_app_data(serial: String, package: String) -> Result<String, String> {
    adb::clear_app_data(&serial, &package)
}

#[tauri::command]
fn adb_get_current_app(serial: String) -> Result<String, String> {
    adb::get_current_app(&serial)
}

#[tauri::command]
fn adb_logcat_clear(serial: String) -> Result<String, String> {
    adb::logcat_clear(&serial)
}

#[tauri::command]
fn adb_logcat(serial: String, buffer: String, lines: i32) -> Result<String, String> {
    adb::logcat(&serial, &buffer, lines)
}

#[tauri::command]
fn adb_get_battery(serial: String) -> Result<String, String> {
    adb::get_battery_info(&serial)
}

#[tauri::command]
fn adb_list_directory(serial: String, path: String) -> Result<String, String> {
    adb::list_directory(&serial, &path)
}

#[tauri::command]
fn adb_get_app_info(serial: String, package: String) -> Result<String, String> {
    adb::get_app_info(&serial, &package)
}

#[tauri::command]
fn adb_get_cpu(serial: String) -> Result<String, String> {
    adb::get_cpu_info(&serial)
}

#[tauri::command]
fn adb_get_memory(serial: String) -> Result<String, String> {
    adb::get_memory_info(&serial)
}

#[tauri::command]
fn adb_logcat_buffer_resize(serial: String, size_mb: u32) -> Result<String, String> {
    adb::logcat_buffer_resize(&serial, size_mb)
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
fn adb_dmesg(serial: String) -> Result<String, String> {
    adb::dmesg(&serial)
}

#[tauri::command]
fn adb_kill_server() -> Result<String, String> {
    adb::kill_server()
}

#[tauri::command]
fn adb_start_server() -> Result<String, String> {
    adb::start_server()
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
            write_text_file,
            read_text_file,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
