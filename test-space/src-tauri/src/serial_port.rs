use std::sync::Mutex;
use tauri::State;

pub struct SerialState {
    pub port: Mutex<Option<Box<dyn serialport::SerialPort>>>,
}

pub fn list_ports() -> Vec<String> {
    serialport::available_ports()
        .unwrap_or_default()
        .into_iter()
        .map(|p| p.port_name)
        .collect()
}

pub fn connect(state: &State<SerialState>, port_name: &str, baud_rate: u32) -> Result<(), String> {
    let port = serialport::new(port_name, baud_rate)
        .timeout(std::time::Duration::from_millis(100))
        .open()
        .map_err(|e| format!("Failed to open serial port: {}", e))?;
    let mut stored = state.port.lock().map_err(|e| e.to_string())?;
    *stored = Some(port);
    Ok(())
}

pub fn disconnect(state: &State<SerialState>) -> Result<(), String> {
    let mut port = state.port.lock().map_err(|e| e.to_string())?;
    *port = None;
    Ok(())
}

pub fn send_command(state: &State<SerialState>, command: &str) -> Result<(), String> {
    let mut port = state.port.lock().map_err(|e| e.to_string())?;
    if let Some(ref mut p) = *port {
        p.write(command.as_bytes())
            .map_err(|e| format!("Write failed: {}", e))?;
        Ok(())
    } else {
        Err("No serial port connected".to_string())
    }
}

pub fn read_data(state: &State<SerialState>) -> Result<String, String> {
    let mut port = state.port.lock().map_err(|e| e.to_string())?;
    if let Some(ref mut p) = *port {
        let mut buf = vec![0u8; 1024];
        match p.read(&mut buf) {
            Ok(n) => {
                buf.truncate(n);
                Ok(String::from_utf8_lossy(&buf).to_string())
            }
            Err(e) if e.kind() == std::io::ErrorKind::TimedOut => {
                Ok(String::new())
            }
            Err(e) => Err(format!("Read failed: {}", e)),
        }
    } else {
        Err("No serial port connected".to_string())
    }
}
