<template>
  <div class="pt-12 flex flex-col gap-gutter-grid min-h-[calc(100vh-80px)]">
    <!-- Header -->
    <div class="flex justify-between items-end mb-2">
      <div>
        <h2 class="font-display-lg text-display-lg font-semibold text-on-surface tracking-tight">Device Command</h2>
        <p class="font-body-lg text-body-lg text-on-surface-variant mt-2">Manage connected hardware and monitor telemetry.</p>
      </div>
      <div class="flex gap-3">
        <button class="glass-button px-6 py-2 rounded-full flex items-center gap-2 font-label-md text-label-md" @click="scanDevices">
          <span class="material-symbols-outlined text-[18px]">refresh</span>
          Scan Devices
        </button>
        <button
          class="glass-button px-6 py-2 rounded-full flex items-center gap-2 font-label-md text-label-md"
          @click="showConnectDialog = true"
        >
          <span class="material-symbols-outlined text-[18px]">add</span>
          Connect ADB
        </button>
      </div>
    </div>

    <!-- Bento Grid -->
    <div class="grid grid-cols-12 gap-gutter-grid flex-grow">
      <!-- Left: Device List -->
      <div class="col-span-12 lg:col-span-4 flex flex-col gap-4">
        <h3 class="font-headline-md text-headline-md text-on-surface mb-2">Connected Targets</h3>
        <div
          v-for="device in devices"
          :key="device.id"
          class="rounded-xl p-6 relative overflow-hidden group cursor-pointer glass-hover"
          :class="device.status === 'online' ? 'glass-card glass-card-active' : 'glass-card'"
          @click="selectDevice(device)"
        >
          <div v-if="device.status === 'online'" class="absolute top-0 right-0 w-32 h-32 bg-secondary/10 rounded-full blur-2xl -mr-10 -mt-10"></div>
          <div class="flex justify-between items-start mb-4 relative z-10">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-lg bg-secondary/10 flex items-center justify-center text-secondary border border-secondary/20">
                <span class="material-symbols-outlined">{{ device.icon }}</span>
              </div>
              <div>
                <h4 class="font-body-lg text-body-lg font-semibold text-on-surface">{{ device.name }}</h4>
                <p class="font-caption text-caption" :class="device.status === 'online' ? 'text-secondary' : 'text-on-surface-variant'">
                  {{ device.statusText }}
                </p>
              </div>
            </div>
            <div v-if="device.status === 'online'" class="relative flex items-center justify-center w-3 h-3">
              <div class="absolute w-full h-full bg-success-indicator rounded-full opacity-50 status-pulse"></div>
              <div class="w-2 h-2 bg-success-indicator rounded-full shadow-[0_0_8px_#22C55E]"></div>
            </div>
            <div v-else class="w-2 h-2 bg-outline-variant rounded-full mt-1.5"></div>
          </div>
          <div class="space-y-2 relative z-10" :class="device.status !== 'online' ? 'opacity-60' : ''">
            <div class="flex justify-between font-label-md text-label-md">
              <span class="text-on-surface-variant">OS</span>
              <span class="font-medium">{{ device.os }}</span>
            </div>
            <div class="flex justify-between font-label-md text-label-md">
              <span class="text-on-surface-variant">{{ device.status === 'online' ? 'Serial' : 'IP' }}</span>
              <span class="font-medium font-mono text-xs">{{ device.address }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Right: Telemetry + Tools -->
      <div class="col-span-12 lg:col-span-8 flex flex-col gap-gutter-grid h-full">
        <!-- Telemetry -->
        <div class="grid grid-cols-3 gap-4">
          <div v-for="gauge in telemetry" :key="gauge.label" class="glass-card rounded-xl p-5 flex flex-col justify-between h-32 relative overflow-hidden">
            <div class="absolute bottom-0 left-0 w-full h-1/2 bg-gradient-to-t from-secondary/10 to-transparent"></div>
            <div class="flex justify-between items-center relative z-10">
              <span class="font-label-md text-label-md text-on-surface-variant flex items-center gap-1">
                <span class="material-symbols-outlined text-[16px]">{{ gauge.icon }}</span>
                {{ gauge.label }}
              </span>
              <span class="font-caption text-caption text-secondary bg-secondary/10 px-2 py-0.5 rounded-full">{{ gauge.statusText }}</span>
            </div>
            <div class="relative z-10">
              <div class="flex items-baseline gap-1">
                <span class="font-headline-lg text-headline-lg font-semibold text-on-surface">{{ gauge.value }}</span>
                <span class="font-label-md text-label-md text-on-surface-variant">{{ gauge.unit }}</span>
              </div>
              <div class="w-full h-1.5 bg-surface-variant rounded-full mt-2 overflow-hidden">
                <div
                  class="h-full rounded-full"
                  :class="gauge.colorClass"
                  :style="{ width: gauge.percent + '%' }"></div>
              </div>
            </div>
          </div>
        </div>

        <!-- ADB Tool Tabs -->
        <div class="flex gap-2 mb-2">
          <button
            v-for="tab in adbTabs"
            :key="tab.key"
            class="px-4 py-2 rounded-full font-label-md text-label-md"
            :class="activeAdbTab === tab.key
              ? 'glass-button glass-active'
              : 'glass-button'"
            @click="activeAdbTab = tab.key"
          >
            <span class="material-symbols-outlined text-[16px] align-middle mr-1">{{ tab.icon }}</span>
            {{ tab.label }}
          </button>
        </div>

        <!-- Logcat Terminal -->
        <div v-if="activeAdbTab === 'logcat'" class="glass-panel rounded-xl flex-grow flex flex-col overflow-hidden min-h-[400px]">
          <div class="h-12 border-b border-glass-border-dark flex items-center justify-between px-4 bg-white/5">
            <div class="flex items-center gap-4">
              <h4 class="font-label-md text-label-md font-semibold text-on-surface flex items-center gap-2">
                <span class="material-symbols-outlined text-[18px]">terminal</span>
                Live Logcat
              </h4>
              <div class="h-4 w-[1px] bg-glass-border-dark"></div>
              <div class="flex gap-2">
                <button
                  v-for="level in logLevels"
                  :key="level"
                  class="px-3 py-1 rounded-md font-caption text-caption"
                  :class="selectedLevel === level
                    ? 'glass-button glass-active'
                    : 'glass-button'"
                  @click="selectedLevel = level"
                >
                  {{ level }}
                </button>
              </div>
            </div>
            <div class="flex items-center gap-2">
              <div class="relative">
                <span class="material-symbols-outlined absolute left-2 top-1/2 -translate-y-1/2 text-on-surface-variant text-[14px]">filter_list</span>
                <input v-model="logFilter" class="w-48 glass-input rounded-md pl-7 pr-2 py-1 font-caption text-caption text-on-surface placeholder:text-on-surface-variant/60 focus:outline-none" placeholder="Filter logs..." type="text" @input="filterLogs" />
              </div>
              <button class="glass-button text-on-surface-variant p-1 rounded" title="Clear">
                <span class="material-symbols-outlined text-[18px]">delete</span>
              </button>
            </div>
          </div>
          <div class="flex-grow p-4 overflow-y-auto logcat-scroll bg-[#1a1c1d]/5 font-mono text-[12px] leading-relaxed text-on-surface-variant relative">
            <div class="space-y-1">
              <div v-for="(log, idx) in (filteredLogs.length ? filteredLogs : logEntries)" :key="idx" class="flex gap-3 hover:bg-white/5 px-2 py-0.5 rounded" :class="log.level === 'E' ? 'bg-error/5 border-l-2 border-error' : ''">
                <span class="text-secondary w-12 shrink-0">{{ log.time }}</span>
                <span class="w-4 shrink-0 font-bold" :class="logLevelColor(log.level)">{{ log.level }}</span>
                <span class="w-24 shrink-0 truncate text-on-surface/50">{{ log.tag }}</span>
                <span :class="log.level === 'E' ? 'text-error' : ''">{{ log.message }}</span>
              </div>
            </div>
            <div class="absolute bottom-0 left-0 w-full h-8 bg-gradient-to-t from-[#f9f9fb] to-transparent pointer-events-none"></div>
          </div>
        </div>

        <!-- ADB Shell -->
        <div v-else-if="activeAdbTab === 'shell'" class="glass-panel rounded-xl flex-grow flex flex-col overflow-hidden min-h-[400px]">
          <div class="h-12 border-b border-glass-border-dark flex items-center px-4 bg-white/5">
            <h4 class="font-label-md text-label-md font-semibold text-on-surface flex items-center gap-2">
              <span class="material-symbols-outlined text-[18px]">terminal</span>
              ADB Shell
            </h4>
          </div>
          <div class="flex-grow p-4 overflow-y-auto logcat-scroll bg-[#1a1c1d]/5 font-mono text-[12px] leading-relaxed text-on-surface-variant">
            <div class="mb-2 text-on-surface/30">$ adb shell <span v-if="selectedDevice">({{ selectedDevice.name }})</span></div>
            <div v-for="(line, idx) in shellOutput" :key="idx" class="text-on-surface font-mono">{{ line }}</div>
          </div>
          <div class="h-12 border-t border-glass-border-dark flex items-center px-4 bg-white/5 gap-2">
            <input
              v-model="shellCommand"
              class="flex-1 bg-transparent border-none outline-none font-mono text-[13px] text-on-surface placeholder:text-on-surface-variant/40"
              placeholder="Enter ADB command..."
              @keyup.enter="executeShell"
            />
            <button class="glass-button px-4 py-1.5 rounded-full font-label-md text-label-md" @click="executeShell">Run</button>
          </div>
        </div>

        <!-- APK Manager -->
        <div v-else-if="activeAdbTab === 'apk'" class="glass-panel rounded-xl flex-grow flex flex-col overflow-hidden min-h-[400px]">
          <div class="h-12 border-b border-glass-border-dark flex items-center justify-between px-4 bg-white/5">
            <h4 class="font-label-md text-label-md font-semibold text-on-surface flex items-center gap-2">
              <span class="material-symbols-outlined text-[18px]">package</span>
              APK Manager
            </h4>
            <div class="flex gap-2">
              <button class="glass-button px-4 py-1.5 rounded-full font-caption text-caption flex items-center gap-1" @click="installApkFile">
                <span class="material-symbols-outlined text-[14px]">upload</span>
                Install APK
              </button>
              <button class="glass-button px-4 py-1.5 rounded-full font-caption text-caption flex items-center gap-1">
                <span class="material-symbols-outlined text-[14px]">download</span>
                Pull APK
              </button>
            </div>
          </div>
          <div class="flex-1 p-4 overflow-y-auto custom-scrollbar">
            <div class="grid grid-cols-1 gap-2">
              <div v-for="app in installedApps" :key="app.package" class="flex items-center justify-between p-3 rounded-lg hover:bg-white/20 transition-colors">
                <div>
                  <span class="font-body-md text-body-md text-on-surface font-medium">{{ app.name }}</span>
                  <span class="font-caption text-caption text-on-surface-variant ml-2">{{ app.package }}</span>
                </div>
                <div class="flex gap-2">
                  <button class="glass-button text-on-surface-variant p-1 rounded" title="Open">
                    <span class="material-symbols-outlined text-[18px]">play_arrow</span>
                  </button>
                  <button class="glass-button text-on-surface-variant p-1 rounded" title="Uninstall" @click="uninstallApp(app.package)">
                    <span class="material-symbols-outlined text-[18px]">delete</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- File Manager -->
        <div v-else-if="activeAdbTab === 'files'" class="glass-panel rounded-xl flex-grow flex flex-col overflow-hidden min-h-[400px]">
          <div class="h-12 border-b border-glass-border-dark flex items-center justify-between px-4 bg-white/5">
            <h4 class="font-label-md text-label-md font-semibold text-on-surface flex items-center gap-2">
              <span class="material-symbols-outlined text-[18px]">folder</span>
              File Manager
            </h4>
            <div class="flex gap-2">
              <button class="glass-button px-4 py-1.5 rounded-full font-caption text-caption flex items-center gap-1" @click="pushFileAction">
                <span class="material-symbols-outlined text-[14px]">upload</span>
                Push
              </button>
              <button class="glass-button px-4 py-1.5 rounded-full font-caption text-caption flex items-center gap-1" @click="pullFileAction">
                <span class="material-symbols-outlined text-[14px]">download</span>
                Pull
              </button>
            </div>
          </div>
          <div class="flex-1 p-4 overflow-y-auto custom-scrollbar">
            <p class="font-body-md text-body-md text-on-surface-variant text-center mt-20">
              Select a device and use Push/Pull to transfer files
            </p>
          </div>
        </div>

        <!-- Screenshot -->
        <div v-else-if="activeAdbTab === 'screen'" class="glass-panel rounded-xl flex-grow flex flex-col overflow-hidden min-h-[400px]">
          <div class="h-12 border-b border-glass-border-dark flex items-center justify-between px-4 bg-white/5">
            <h4 class="font-label-md text-label-md font-semibold text-on-surface flex items-center gap-2">
              <span class="material-symbols-outlined text-[18px]">screenshot_monitor</span>
              Screenshot &amp; Recording
            </h4>
            <div class="flex gap-2">
              <button class="glass-button px-4 py-1.5 rounded-full font-caption text-caption flex items-center gap-1" @click="takeScreenshot">
                <span class="material-symbols-outlined text-[14px]">screenshot_monitor</span>
                Screenshot
              </button>
              <button
                class="px-4 py-1.5 rounded-full font-caption text-caption flex items-center gap-1"
                :class="isRecording
                  ? 'bg-error/10 text-error border border-error/20'
                  : 'glass-button'"
                @click="toggleRecording"
              >
                <span class="material-symbols-outlined text-[14px]">videocam</span>
                {{ isRecording ? "Stop" : "Record" }}
              </button>
            </div>
          </div>
          <div class="flex-1 flex items-center justify-center p-4">
            <div v-if="screenshotUrl" class="max-w-full max-h-full">
              <img :src="screenshotUrl" class="max-w-full max-h-[calc(100vh-400px)] rounded-xl shadow-sm" />
            </div>
            <p v-else class="font-body-md text-body-md text-on-surface-variant">
              Click "Screenshot" to capture the device screen
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- Connect Dialog -->
    <Teleport to="body">
      <div v-if="showConnectDialog" class="fixed inset-0 z-50 flex items-center justify-center" @click.self="showConnectDialog = false">
        <div class="absolute inset-0 bg-black/10 backdrop-blur-sm"></div>
        <div class="glass-panel rounded-[2rem] p-8 w-full max-w-md relative z-10 bg-white/60">
          <h3 class="font-headline-md text-headline-md text-on-surface font-semibold mb-6">Connect ADB Device</h3>
          <div class="flex flex-col gap-4">
            <div>
              <label class="block font-label-md text-caption text-on-surface uppercase tracking-wider mb-2">Connection Type</label>
              <div class="flex gap-2">
                <button
                  class="flex-1 px-4 py-3 rounded-xl font-label-md text-label-md"
                  :class="connType === 'usb' ? 'glass-button glass-active' : 'glass-button'"
                  @click="connType = 'usb'"
                >
                  USB
                </button>
                <button
                  class="flex-1 px-4 py-3 rounded-xl font-label-md text-label-md"
                  :class="connType === 'tcpip' ? 'glass-button glass-active' : 'glass-button'"
                  @click="connType = 'tcpip'"
                >
                  TCP/IP
                </button>
              </div>
            </div>
            <div v-if="connType === 'tcpip'">
              <label class="block font-label-md text-caption text-on-surface uppercase tracking-wider mb-2">IP Address</label>
              <input
                v-model="ipAddress"
                class="w-full bg-white border border-outline-variant rounded-lg px-4 py-3 text-body-md text-on-surface focus:ring-2 focus:ring-secondary/30 focus:border-secondary transition-all"
                placeholder="192.168.1.100:5555"
              />
            </div>
            <button
              class="w-full glass-button font-label-md text-label-md py-3 rounded-full"
              @click="connectDevice"
            >
              Connect
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useAdb } from "@/composables/useAdb";

const { listDevices, shell, installApk, uninstallApk, pushFile, pullFile, reboot, screenshot } = useAdb();

const showConnectDialog = ref(false);
const connType = ref<"usb" | "tcpip">("usb");
const ipAddress = ref("");
const activeAdbTab = ref("logcat");
const selectedLevel = ref("Verbose");
const shellCommand = ref("");
const shellOutput = ref<string[]>([]);
const screenshotUrl = ref("");
const isRecording = ref(false);
const selectedDevice = ref<DeviceItem | null>(null);
const logFilter = ref("");
const adbLoading = ref(false);

interface DeviceItem {
  id: string;
  name: string;
  icon: string;
  os: string;
  address: string;
  status: "online" | "offline";
  statusText: string;
  serial?: string;
}

const devices = ref<DeviceItem[]>([
  { id: "1", name: "Pixel 8 Pro", icon: "smartphone", os: "Android 14 (AP1A.240405.002)", address: "3A251FDH3002G", status: "online", statusText: "Active • USB Debugging" },
  { id: "2", name: "Android TV 4K", icon: "tv", os: "Android TV 12", address: "192.168.1.105:5555", status: "offline", statusText: "Standby • TCP/IP" },
]);

const logLevels = ["Verbose", "Debug", "Error"];

interface LogEntryItem {
  time: string;
  level: string;
  tag: string;
  message: string;
}

const logEntries = ref<LogEntryItem[]>([
  { time: "14:02:11", level: "I", tag: "ActivityManager", message: "Start proc com.test.app for activity" },
  { time: "14:02:11", level: "V", tag: "NetworkStack", message: "Checking connectivity state..." },
  { time: "14:02:12", level: "D", tag: "OpenGLRenderer", message: "HWUI GL Pipeline initialized" },
  { time: "14:02:12", level: "E", tag: "ConfigLoader", message: "Failed to parse JSON configuration file" },
  { time: "14:02:13", level: "D", tag: "SensorService", message: "Registering listener for PROXIMITY sensor" },
  { time: "14:02:13", level: "I", tag: "SystemUI", message: "Update status bar state: visibility=VISIBLE" },
  { time: "14:02:14", level: "V", tag: "AudioFlinger", message: "Set mode: MODE_NORMAL" },
  { time: "14:02:14", level: "D", tag: "BatteryStatsService", message: "Note start wake lock: partial_lock" },
]);

const adbTabs = [
  { key: "logcat", label: "Logcat", icon: "terminal" },
  { key: "shell", label: "Shell", icon: "code" },
  { key: "apk", label: "APK", icon: "package" },
  { key: "files", label: "Files", icon: "folder" },
  { key: "screen", label: "Screen", icon: "screenshot_monitor" },
];

interface TelemetryGauge {
  icon: string;
  label: string;
  value: number;
  unit: string;
  percent: number;
  statusText: string;
  colorClass: string;
}

const telemetry = ref<TelemetryGauge[]>([
  { icon: "memory", label: "CPU", value: 34, unit: "%", percent: 34, statusText: "Normal", colorClass: "bg-secondary shadow-[0_0_8px_rgba(76,74,202,0.5)]" },
  { icon: "sd_card", label: "RAM", value: 65, unit: "%", percent: 65, statusText: "4.2GB Free", colorClass: "bg-secondary shadow-[0_0_8px_rgba(76,74,202,0.5)]" },
  { icon: "battery_charging_full", label: "Battery", value: 88, unit: "%", percent: 88, statusText: "Charging", colorClass: "bg-secondary shadow-[0_0_8px_rgba(76,74,202,0.5)]" },
]);

interface AppItem {
  name: string;
  package: string;
}

const installedApps = ref<AppItem[]>([
  { name: "Settings", package: "com.android.settings" },
  { name: "Camera", package: "com.android.camera2" },
  { name: "Chrome", package: "com.android.chrome" },
]);

const filteredLogs = ref<LogEntryItem[]>([]);

function logLevelColor(level: string) {
  switch (level) {
    case "E": return "text-error";
    case "W": return "text-tertiary";
    case "I": return "text-success-indicator";
    default: return "text-outline";
  }
}

function selectDevice(device: DeviceItem) {
  selectedDevice.value = device;
}

async function scanDevices() {
  adbLoading.value = true;
  try {
    const adbDevices = await listDevices();
    devices.value = adbDevices.map((d, idx) => ({
      id: String(idx + 1),
      name: d.model || d.serial,
      icon: "smartphone",
      os: d.android_version || "Android",
      address: d.serial,
      status: d.status === "device" ? "online" as const : "offline" as const,
      statusText: d.status === "device" ? "Active • USB Debugging" : "Unauthorized",
      serial: d.serial,
    }));
    if (devices.value.length > 0 && !selectedDevice.value) {
      selectedDevice.value = devices.value[0];
    }
  } catch {
    // Keep mock data if ADB fails
  }
  adbLoading.value = false;
}

async function connectDevice() {
  showConnectDialog.value = false;
  scanDevices();
}

async function executeShell() {
  if (!shellCommand.value.trim() || !selectedDevice.value?.serial) return;
  const cmd = shellCommand.value.trim();
  shellOutput.value.push(`$ adb -s ${selectedDevice.value.serial} shell ${cmd}`);
  try {
    const result = await shell(selectedDevice.value.serial, cmd);
    shellOutput.value.push(result);
  } catch (e: any) {
    shellOutput.value.push(`Error: ${e?.message || e}`);
  }
  shellCommand.value = "";
}

async function installApkFile() {
  if (!selectedDevice.value?.serial) return;
  try {
    const { open } = await import("@tauri-apps/plugin-dialog");
    const selected = await open({ multiple: false, filters: [{ name: "APK", extensions: ["apk"] }] });
    if (selected) {
      adbLoading.value = true;
      await installApk(selectedDevice.value.serial, selected);
      adbLoading.value = false;
    }
  } catch {}
}

async function uninstallApp(pkg: string) {
  if (!selectedDevice.value?.serial) return;
  try {
    adbLoading.value = true;
    await uninstallApk(selectedDevice.value.serial, pkg);
    installedApps.value = installedApps.value.filter((a) => a.package !== pkg);
    adbLoading.value = false;
  } catch {}
}

async function pushFileAction() {
  if (!selectedDevice.value?.serial) return;
  try {
    const { open } = await import("@tauri-apps/plugin-dialog");
    const selected = await open({ multiple: false });
    if (selected) {
      await pushFile(selectedDevice.value.serial, selected, `/sdcard/${selected.split("/").pop() || selected.split("\\").pop()}`);
    }
  } catch {}
}

async function pullFileAction() {
  if (!selectedDevice.value?.serial) return;
  try {
    const { save } = await import("@tauri-apps/plugin-dialog");
    const dest = await save();
    if (dest) {
      await pullFile(selectedDevice.value.serial, "/sdcard/", dest);
    }
  } catch {}
}

async function takeScreenshot() {
  if (!selectedDevice.value?.serial) return;
  screenshotUrl.value = "";
  try {
    const result = await screenshot(selectedDevice.value.serial, "");
    const base64Data = result.split(",").pop() || result;
    screenshotUrl.value = `data:image/png;base64,${base64Data}`;
  } catch {
    screenshotUrl.value = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAjR9awAAAABJRU5ErkJggg==";
  }
}

function toggleRecording() {
  isRecording.value = !isRecording.value;
  if (!isRecording.value && selectedDevice.value?.serial) {
    reboot(selectedDevice.value.serial).catch(() => {});
  }
}

function filterLogs() {
  const q = logFilter.value.toLowerCase();
  if (!q) {
    filteredLogs.value = logEntries.value;
    return;
  }
  filteredLogs.value = logEntries.value.filter(
    (l) => l.message.toLowerCase().includes(q) || l.tag.toLowerCase().includes(q)
  );
}
</script>
