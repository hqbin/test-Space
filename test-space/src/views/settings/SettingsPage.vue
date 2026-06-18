<template>
  <div class="pt-12 max-w-5xl select-none">
    <div class="glass-panel rounded-xl p-padding-card shadow-md">
      <!-- Language -->
      <div class="flex items-center justify-between">
        <span class="font-body-md text-body-md text-on-surface font-medium">{{ t("settings.language") }}</span>
        <div class="flex gap-2">
          <button
            class="glass-button px-4 py-2 rounded-full font-label-md text-label-md select-none"
            :class="lang === 'zh' ? 'glass-active' : ''"
            @click="setLanguage('zh')"
          >{{ t("settings.langZh") }}</button>
          <button
            class="glass-button px-4 py-2 rounded-full font-label-md text-label-md select-none"
            :class="lang === 'en' ? 'glass-active' : ''"
            @click="setLanguage('en')"
          >{{ t("settings.langEn") }}</button>
        </div>
      </div>

      <div class="border-t border-glass-border-light/30 my-5"></div>

      <!-- Appearance -->
      <div class="flex items-center justify-between">
        <span class="font-body-md text-body-md text-on-surface font-medium">{{ t("settings.theme") }}</span>
        <div class="flex gap-2">
          <button
            class="glass-button px-4 py-2 rounded-full font-label-md text-label-md flex items-center gap-2 select-none"
            :class="theme === 'light' ? 'glass-active' : ''"
            @click="setTheme('light')"
          >
            <span class="material-symbols-outlined text-[18px]">light_mode</span>
            {{ t("settings.themeLight") }}
          </button>
          <button
            class="glass-button px-4 py-2 rounded-full font-label-md text-label-md flex items-center gap-2 select-none"
            :class="theme === 'dark' ? 'glass-active' : ''"
            @click="setTheme('dark')"
          >
            <span class="material-symbols-outlined text-[18px]">dark_mode</span>
            {{ t("settings.themeDark") }}
          </button>
        </div>
      </div>

      <div class="border-t border-glass-border-light/30 my-5"></div>

      <!-- Backup & Restore -->
      <div>
        <span class="font-body-md text-body-md text-on-surface font-medium">{{ t("settings.backup") }}</span>
        <!-- Device ID -->
        <div class="flex items-center gap-3 mt-3">
          <span class="font-body-md text-body-md text-on-surface-variant whitespace-nowrap">{{ t("settings.cloudDeviceId") }}</span>
          <div class="relative flex-1">
            <input
              class="w-full px-3 py-2 rounded-lg font-body-md text-body-md bg-white border border-gray-300 outline-none focus:border-gray-400"
              :placeholder="t('settings.cloudDeviceIdPlaceholder')"
              v-model="deviceId"
              @focus="showDeviceDropdown = true"
              @blur="handleDeviceIdBlur"
            />
            <div
              v-if="showDeviceDropdown && deviceIdList.length > 0"
              class="absolute top-full left-0 right-0 mt-1 bg-white rounded-lg shadow-md z-10 max-h-40 overflow-y-auto border border-gray-200"
            >
              <div
                v-for="id in deviceIdList"
                :key="id"
                class="px-3 py-2 font-body-md text-body-md text-on-surface hover:bg-gray-100 cursor-pointer truncate"
                @mousedown="selectDeviceId(id)"
              >{{ id }}</div>
            </div>
          </div>
          <button class="glass-button px-3 py-2 rounded-lg font-label-md text-label-md select-none" @click="copyDeviceId">
            {{ t("settings.cloudDeviceIdCopy") }}
          </button>
        </div>
        <!-- Buttons -->
        <div class="flex gap-3 mt-4 flex-wrap">
          <!-- Backup dropdown -->
          <div class="relative">
            <button class="glass-button px-6 py-3 rounded-full font-label-md text-label-md flex items-center gap-2 select-none" @click="showBackupMenu = !showBackupMenu; showRestoreMenu = false">
              <span class="material-symbols-outlined text-[18px]">upload</span>
              {{ t("settings.cloudUpload") }}
              <span class="material-symbols-outlined text-[16px]">arrow_drop_down</span>
            </button>
            <div v-if="showBackupMenu" class="absolute top-full left-0 mt-1 bg-white rounded-lg shadow-md z-20 min-w-[160px] border border-gray-200">
              <div class="px-4 py-2 font-body-md text-body-md text-on-surface hover:bg-gray-100 cursor-pointer flex items-center gap-2" @mousedown="handleExport(); showBackupMenu = false">
                <span class="material-symbols-outlined text-[18px]">file_upload</span>
                {{ t("settings.exportLocal") }}
              </div>
              <div class="px-4 py-2 font-body-md text-body-md text-on-surface hover:bg-gray-100 cursor-pointer flex items-center gap-2" @mousedown="handleCloudUpload(); showBackupMenu = false">
                <span class="material-symbols-outlined text-[18px]">cloud_upload</span>
                {{ t("settings.exportCloud") }}
              </div>
            </div>
          </div>
          <!-- Restore dropdown -->
          <div class="relative">
            <button class="glass-button px-6 py-3 rounded-full font-label-md text-label-md flex items-center gap-2 select-none" @click="showRestoreMenu = !showRestoreMenu; showBackupMenu = false">
              <span class="material-symbols-outlined text-[18px]">download</span>
              {{ t("settings.restore") }}
              <span class="material-symbols-outlined text-[16px]">arrow_drop_down</span>
            </button>
            <div v-if="showRestoreMenu" class="absolute top-full left-0 mt-1 bg-white rounded-lg shadow-md z-20 min-w-[160px] border border-gray-200">
              <div class="px-4 py-2 font-body-md text-body-md text-on-surface hover:bg-gray-100 cursor-pointer flex items-center gap-2" @mousedown="handleImport(); showRestoreMenu = false">
                <span class="material-symbols-outlined text-[18px]">file_download</span>
                {{ t("settings.importLocal") }}
              </div>
              <div class="px-4 py-2 font-body-md text-body-md text-on-surface hover:bg-gray-100 cursor-pointer flex items-center gap-2" @mousedown="handleCloudRestore(); showRestoreMenu = false">
                <span class="material-symbols-outlined text-[18px]">cloud_download</span>
                {{ t("settings.importCloud") }}
              </div>
              <div class="border-t border-gray-100 my-1"></div>
              <div class="px-4 py-2 font-body-md text-body-md text-on-surface hover:bg-gray-100 cursor-pointer flex items-center gap-2" @mousedown="handleExportKey(); showRestoreMenu = false">
                <span class="material-symbols-outlined text-[18px]">key</span>
                {{ t("settings.exportKey") }}
              </div>
              <div class="px-4 py-2 font-body-md text-body-md text-on-surface hover:bg-gray-100 cursor-pointer flex items-center gap-2" @mousedown="handleImportKey(); showRestoreMenu = false">
                <span class="material-symbols-outlined text-[18px]">vpn_key</span>
                {{ t("settings.importKey") }}
              </div>
            </div>
          </div>
        </div>
        <p v-if="statusMessage" class="mt-3 font-body-md text-body-md" :class="statusIsError ? 'text-error' : 'text-success-indicator'">{{ statusMessage }}</p>
      </div>

      <div class="border-t border-glass-border-light/30 my-5"></div>

      <!-- Version -->
      <div class="flex items-center justify-between">
        <span class="font-body-md text-body-md text-on-surface font-medium">{{ t("settings.version") }}</span>
        <span class="font-body-md text-body-md text-on-surface-variant">v{{ appVersion }}</span>
      </div>
    </div>
  </div>

  <!-- Key Import Modal -->
  <div v-if="showKeyImportModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/20 backdrop-blur-sm" @click.self="showKeyImportModal = false">
    <div class="glass-panel rounded-2xl p-6 w-96 bg-white/60" @click.stop>
      <h3 class="font-label-md text-label-md text-on-surface font-semibold mb-4 select-none">{{ t("settings.importKey") }}</h3>
      <input
        v-model="keyImportInput"
        type="text"
        placeholder="粘贴 44 位加密密钥"
        class="glass-input w-full px-3 py-2 rounded-lg text-[14px] outline-none select-text font-mono"
        @keydown.enter="confirmImportKey"
      />
      <div class="flex justify-end gap-2 mt-6">
        <button class="glass-button px-4 py-2 rounded-full text-[13px] select-none" @click="showKeyImportModal = false">{{ t("settings.cancel") }}</button>
        <button class="glass-button px-4 py-2 rounded-full text-[13px] select-none glass-active" @click="confirmImportKey">{{ t("settings.confirm") }}</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from "vue";
import * as db from "@/services/database";
import * as cloudApi from "@/services/cloudBackup";
import * as crypto from "@/services/crypto";
import { useI18n } from "@/composables/useI18n";
import { getVersion } from "@tauri-apps/api/app";

const { lang, t, setLanguage, initLanguage } = useI18n();

const theme = ref("light");
const statusMessage = ref("");
const statusIsError = ref(false);
const appVersion = ref("...");

function setStatus(msg: string, isError = false) {
  statusMessage.value = msg;
  statusIsError.value = isError;
}

// Cloud backup state
const deviceId = ref("");
const deviceIdList = ref<string[]>([]);
const showBackupMenu = ref(false);
const showRestoreMenu = ref(false);
const cloudBusy = ref(false);
const showDeviceDropdown = ref(false);
const showKeyImportModal = ref(false);
const keyImportInput = ref("");

async function ensureDeviceId() {
  const last = await db.getLastDeviceId();
  const list = await db.getDeviceIdList();
  deviceIdList.value = list;
  if (last) {
    deviceId.value = last;
  } else {
    const id = crypto.generateDeviceId();
    deviceId.value = id;
    deviceIdList.value = [id];
    await db.saveDeviceIdList([id]);
    await db.saveLastDeviceId(id);
  }
}

function handleDeviceIdBlur() {
  setTimeout(() => { showDeviceDropdown.value = false; }, 200);
}

function closeMenus(e: MouseEvent) {
  const target = e.target as HTMLElement;
  if (!target.closest('.relative')) {
    showBackupMenu.value = false;
    showRestoreMenu.value = false;
  }
}

onMounted(() => { document.addEventListener('click', closeMenus); });
onUnmounted(() => { document.removeEventListener('click', closeMenus); });

function selectDeviceId(id: string) {
  deviceId.value = id;
  showDeviceDropdown.value = false;
  db.saveLastDeviceId(id);
}

async function saveCurrentDeviceId() {
  const id = deviceId.value.trim();
  if (!id) return;
  await db.saveLastDeviceId(id);
  const list = await db.getDeviceIdList();
  if (!list.includes(id)) {
    list.unshift(id);
    await db.saveDeviceIdList(list);
    deviceIdList.value = list;
  }
}

async function copyDeviceId() {
  if (!deviceId.value) return;
  try {
    await navigator.clipboard.writeText(deviceId.value);
    setStatus(t("settings.cloudDeviceIdCopied"));
    setTimeout(() => { if (statusMessage.value === t("settings.cloudDeviceIdCopied")) setStatus(""); }, 2000);
  } catch {}
}

async function handleCloudUpload() {
  if (cloudBusy.value) return;
  cloudBusy.value = true;
  setStatus(t("settings.cloudBackingUp"));
  if (!deviceId.value.trim()) {
    deviceId.value = crypto.generateDeviceId();
    await saveCurrentDeviceId();
  }
  await saveCurrentDeviceId();
  try {
    const data = await db.exportAllData();
    const json = JSON.stringify(data);
    const key = await crypto.getOrCreateKey();
    const payload = await crypto.encryptBackup(json, key, {
      version: data.version,
      exportedAt: data.exportedAt,
    });
    await cloudApi.uploadBackup(deviceId.value.trim(), payload);
    setStatus(t("settings.cloudUploadSuccess"));
  } catch (e: any) {
    setStatus(t("settings.cloudUploadFail") + ": " + (e.message || e), true);
  } finally {
    cloudBusy.value = false;
  }
}

async function handleCloudRestore() {
  if (cloudBusy.value) return;
  cloudBusy.value = true;
  setStatus(t("settings.cloudRestoring"));
  if (!deviceId.value.trim()) { cloudBusy.value = false; setStatus(""); return; }
  await saveCurrentDeviceId();
  try {
    if (!await checkDbReady()) { cloudBusy.value = false; return; }
    const list = await cloudApi.listBackups(deviceId.value.trim());
    if (!list || list.length === 0) {
      setStatus(t("settings.cloudEmpty"));
      cloudBusy.value = false;
      return;
    }
    const sorted = [...list].sort((a, b) => (b.created_at || '').localeCompare(a.created_at || ''));
    const latest = sorted[0];
    const detail = await cloudApi.getBackup(deviceId.value.trim(), latest.id);
    const key = await crypto.getOrCreateKey();
    const json = await crypto.decryptBackup(detail, key);
    let backup: any;
    try { backup = JSON.parse(json); } catch { setStatus(t("settings.cloudRestoreFail") + ": 解密失败，密钥可能不匹配", true); return; }
    if (!backup.version) {
      setStatus(t("settings.cloudRestoreFail") + ": invalid backup data", true);
      return;
    }
    await db.importAllData(backup);
    setStatus(t("settings.cloudRestoreSuccess"));
  } catch (e: any) {
    setStatus(t("settings.cloudRestoreFail") + ": " + (e.message || e), true);
  } finally {
    cloudBusy.value = false;
  }
}

async function handleExportKey() {
  const key = await crypto.getOrCreateKey();
  await navigator.clipboard.writeText(key);
  setStatus(t("settings.keyExported"));
  setTimeout(() => { if (statusMessage.value === t("settings.keyExported")) setStatus(""); }, 3000);
}

async function handleImportKey() {
  keyImportInput.value = "";
  showKeyImportModal.value = true;
}

async function confirmImportKey() {
  showKeyImportModal.value = false;
  const trimmed = keyImportInput.value.trim();
  if (!trimmed) return;
  if (trimmed.length !== 44 || !/^[A-Za-z0-9+/=]+$/.test(trimmed)) {
    setStatus(t("settings.keyImportFail"), true);
    return;
  }
  await db.setSetting("cloud_encryption_key", trimmed);
  setStatus(t("settings.keyImported"));
}

async function checkDbReady(): Promise<boolean> {
  try {
    await db.checkDatabaseReady();
    return true;
  } catch {
    setStatus(t("settings.dbBusy"), true);
    return false;
  }
}

async function loadTheme() {
  const saved = await db.getSetting("theme");
  if (saved) {
    theme.value = saved;
    applyTheme(saved);
  }
}

function applyTheme(t: string) {
  const root = document.documentElement;
  if (t === "dark") {
    root.classList.add("dark");
  } else {
    root.classList.remove("dark");
  }
}

async function setTheme(t: string) {
  theme.value = t;
  applyTheme(t);
  await db.setSetting("theme", t);
}

async function handleExport() {
  if (cloudBusy.value) return;
  cloudBusy.value = true;
  setStatus(t("settings.exporting"));
  try {
    const data = await db.exportAllData();
    const json = JSON.stringify(data, null, 2);
    try {
      const { save } = await import("@tauri-apps/plugin-dialog");
      const { invoke } = await import("@tauri-apps/api/core");
      const path = await save({
        filters: [{ name: "Test Space Backup", extensions: ["tsb"] }],
        defaultPath: "test-space-backup.tsb",
      });
      if (path) {
        await invoke("write_text_file", { path, content: json });
        setStatus(t("settings.exportSuccess"));
      } else {
        setStatus("");
      }
    } catch {
      const blob = new Blob([json], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "test-space-backup.tsb";
      a.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      setStatus(t("settings.exportSuccess"));
    }
  } catch (e: any) {
    setStatus(t("settings.exportFail") + ": " + (e.message || e), true);
  } finally {
    cloudBusy.value = false;
  }
}

async function handleImport() {
  if (cloudBusy.value) return;
  cloudBusy.value = true;
  setStatus(t("settings.importing"));
  try {
    let json: string;
    try {
      const { open } = await import("@tauri-apps/plugin-dialog");
      const { invoke } = await import("@tauri-apps/api/core");
      const path = await open({
        filters: [{ name: "Test Space Backup", extensions: ["tsb", "json"] }],
        multiple: false,
      });
      if (!path) { cloudBusy.value = false; setStatus(""); return; }
      json = await invoke<string>("read_text_file", { path: path as string });
    } catch {
      const input = document.createElement("input");
      input.type = "file";
      input.accept = ".tsb,.json";
      const file = await new Promise<File | null>((resolve) => {
        input.onchange = () => resolve(input.files?.[0] || null);
        input.click();
      });
      if (!file) { cloudBusy.value = false; setStatus(""); return; }
      json = await file.text();
    }
    if (!await checkDbReady()) { cloudBusy.value = false; return; }
    let backup: any;
    try { backup = JSON.parse(json); } catch { setStatus(t("settings.importFail") + ": JSON 解析失败，文件可能损坏", true); return; }
    if (!backup.version) {
      setStatus(t("settings.importFail") + ": invalid backup file", true);
      cloudBusy.value = false;
      return;
    }
    await db.importAllData(backup);
    setStatus(t("settings.importSuccess"));
  } catch (e: any) {
    setStatus(t("settings.importFail") + ": " + (e.message || e), true);
  } finally {
    cloudBusy.value = false;
  }
}

onMounted(async () => {
  initLanguage();
  await loadTheme();
  try {
    appVersion.value = await getVersion();
  } catch {
    appVersion.value = "1.0.0";
  }
  await ensureDeviceId();
});
</script>
