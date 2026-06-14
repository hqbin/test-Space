import { invoke } from "@tauri-apps/api/core";

interface AdbDeviceInfo {
  serial: string;
  status: string;
  model: string;
  android_version: string;
}

export function useAdb() {
  const listDevices = () => invoke<AdbDeviceInfo[]>("adb_list_devices");

  const shell = (serial: string, command: string) =>
    invoke<string>("adb_shell", { serial, command });

  const installApk = (serial: string, apkPath: string) =>
    invoke<string>("adb_install", { serial, apkPath });

  const uninstallApk = (serial: string, packageName: string) =>
    invoke<string>("adb_uninstall", { serial, package: packageName });

  const pushFile = (serial: string, local: string, remote: string) =>
    invoke<string>("adb_push", { serial, local, remote });

  const pullFile = (serial: string, remote: string, local: string) =>
    invoke<string>("adb_pull", { serial, remote, local });

  const reboot = (serial: string) =>
    invoke<string>("adb_reboot", { serial });

  const screenshot = (serial: string, savePath: string) =>
    invoke<string>("adb_screenshot", { serial, savePath });

  return {
    listDevices,
    shell,
    installApk,
    uninstallApk,
    pushFile,
    pullFile,
    reboot,
    screenshot,
  };
}
