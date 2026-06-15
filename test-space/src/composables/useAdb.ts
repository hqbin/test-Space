import { invoke } from "@tauri-apps/api/core";

interface AdbDeviceInfo {
  serial: string;
  status: string;
  model: string;
  android_version: string;
}

interface DeviceProperties {
  model: string;
  brand: string;
  device: string;
  android_version: string;
  sdk_version: string;
  build_id: string;
  build_fingerprint: string;
  resolution: string;
  density: string;
  product: string;
}

export function useAdb() {
  const listDevices = () => invoke<AdbDeviceInfo[]>("adb_list_devices");

  const shell = (serial: string, command: string) =>
    invoke<string>("adb_shell", { serial, command });

  const installApk = (serial: string, apkPath: string, reinstall = true) =>
    invoke<string>("adb_install", { serial, apkPath, reinstall });

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

  const connectDevice = (address: string) =>
    invoke<string>("adb_connect", { address });

  const disconnectDevice = (serial: string) =>
    invoke<string>("adb_disconnect", { serial });

  const rebootRecovery = (serial: string) =>
    invoke<string>("adb_reboot_recovery", { serial });

  const rebootBootloader = (serial: string) =>
    invoke<string>("adb_reboot_bootloader", { serial });

  const rootDevice = (serial: string) =>
    invoke<string>("adb_root", { serial });

  const remountDevice = (serial: string) =>
    invoke<string>("adb_remount", { serial });

  const getProperties = (serial: string) =>
    invoke<DeviceProperties>("adb_get_properties", { serial });

  const inputKeyevent = (serial: string, keycode: string) =>
    invoke<string>("adb_input_keyevent", { serial, keycode });

  const inputText = (serial: string, text: string) =>
    invoke<string>("adb_input_text", { serial, text });

  const inputTap = (serial: string, x: number, y: number) =>
    invoke<string>("adb_input_tap", { serial, x, y });

  const inputSwipe = (serial: string, x1: number, y1: number, x2: number, y2: number, duration: number) =>
    invoke<string>("adb_input_swipe", { serial, x1, y1, x2, y2, duration });

  const listPackages = (serial: string, thirdPartyOnly = true) =>
    invoke<string[]>("adb_list_packages", { serial, thirdPartyOnly });

  const startApp = (serial: string, packageName: string) =>
    invoke<string>("adb_start_app", { serial, package: packageName });

  const stopApp = (serial: string, packageName: string) =>
    invoke<string>("adb_stop_app", { serial, package: packageName });

  const clearAppData = (serial: string, packageName: string) =>
    invoke<string>("adb_clear_app_data", { serial, package: packageName });

  const getCurrentApp = (serial: string) =>
    invoke<string>("adb_get_current_app", { serial });

  const logcatClear = (serial: string) =>
    invoke<string>("adb_logcat_clear", { serial });

  const logcat = (serial: string, buffer = "", lines = 500) =>
    invoke<string>("adb_logcat", { serial, buffer, lines });

  const getBattery = (serial: string) =>
    invoke<string>("adb_get_battery", { serial });

  const getCpu = (serial: string) =>
    invoke<string>("adb_get_cpu", { serial });

  const getMemory = (serial: string) =>
    invoke<string>("adb_get_memory", { serial });

  const listDirectory = (serial: string, path: string) =>
    invoke<string>("adb_list_directory", { serial, path });

  const getAppInfo = (serial: string, packageName: string) =>
    invoke<string>("adb_get_app_info", { serial, package: packageName });

  const logcatBufferResize = (serial: string, sizeMb: number) =>
    invoke<string>("adb_logcat_buffer_resize", { serial, sizeMb });

  const bugreport = (serial: string, savePath: string) =>
    invoke<string>("adb_bugreport", { serial, savePath });

  const dmesg = (serial: string) =>
    invoke<string>("adb_dmesg", { serial });

  const killServer = () => invoke<string>("adb_kill_server");
  const startServer = () => invoke<string>("adb_start_server");

  const startScreenrecord = (serial: string, filePath: string, width: number, height: number) =>
    invoke<string>("adb_start_screenrecord", { serial, filePath, width, height });

  const createZip = (files: { filename: string; content: string }[], destPath: string) =>
    invoke<string>("create_zip", { files, destPath });

  return {
    listDevices,
    shell,
    installApk,
    uninstallApk,
    pushFile,
    pullFile,
    reboot,
    screenshot,
    connectDevice,
    disconnectDevice,
    rebootRecovery,
    rebootBootloader,
    rootDevice,
    remountDevice,
    getProperties,
    inputKeyevent,
    inputText,
    inputTap,
    inputSwipe,
    listPackages,
    startApp,
    stopApp,
    clearAppData,
    getCurrentApp,
    logcatClear,
    logcat,
    getBattery,
    getCpu,
    getMemory,
    listDirectory,
    getAppInfo,
    logcatBufferResize,
    bugreport,
    dmesg,
    startScreenrecord,
    killServer,
    startServer,
    createZip,
  };
}

export type { AdbDeviceInfo, DeviceProperties };
