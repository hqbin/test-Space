import { invoke } from "@tauri-apps/api/core";

export function useSerial() {
  const listPorts = () => invoke<string[]>("serial_list_ports");

  const connect = (portName: string, baudRate: number) =>
    invoke<void>("serial_connect", { portName, baudRate });

  const disconnect = () => invoke<void>("serial_disconnect");

  const send = (command: string) =>
    invoke<void>("serial_send", { command });

  const read = () => invoke<string>("serial_read");

  return { listPorts, connect, disconnect, send, read };
}
