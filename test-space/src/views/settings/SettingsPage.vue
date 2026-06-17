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
        <p class="font-caption text-caption text-on-surface-variant mt-0.5">{{ t("settings.backupDesc") }}</p>
        <div class="flex gap-4 mt-4">
          <button class="glass-button px-6 py-3 rounded-full font-label-md text-label-md flex items-center gap-2 select-none" @click="handleExport">
            <span class="material-symbols-outlined text-[18px]">file_upload</span>
            {{ t("settings.exportAll") }}
          </button>
          <button class="glass-button px-6 py-3 rounded-full font-label-md text-label-md flex items-center gap-2 select-none" @click="handleImport">
            <span class="material-symbols-outlined text-[18px]">file_download</span>
            {{ t("settings.importAll") }}
          </button>
        </div>
        <p v-if="importStatus" class="mt-3 font-body-md text-body-md" :class="importStatus.startsWith('Error') ? 'text-error' : 'text-success-indicator'">{{ importStatus }}</p>
      </div>

      <div class="border-t border-glass-border-light/30 my-5"></div>

      <!-- Version -->
      <div class="flex items-center justify-between">
        <span class="font-body-md text-body-md text-on-surface font-medium">{{ t("settings.version") }}</span>
        <span class="font-body-md text-body-md text-on-surface-variant">v{{ appVersion }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import * as db from "@/services/database";
import { useI18n } from "@/composables/useI18n";
import { getVersion } from "@tauri-apps/api/app";

const { lang, t, setLanguage, initLanguage } = useI18n();

const theme = ref("light");
const importStatus = ref("");
const appVersion = ref("...");

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
  importStatus.value = "";
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
        importStatus.value = t("settings.exportSuccess");
      }
    } catch {
      const blob = new Blob([json], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "test-space-backup.tsb";
      a.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      importStatus.value = t("settings.exportSuccess");
    }
  } catch (e: any) {
    importStatus.value = t("settings.exportFail") + ": " + (e.message || e);
  }
}

async function handleImport() {
  importStatus.value = "";
  try {
    let json: string;
    try {
      const { open } = await import("@tauri-apps/plugin-dialog");
      const { invoke } = await import("@tauri-apps/api/core");
      const path = await open({
        filters: [{ name: "Test Space Backup", extensions: ["tsb", "json"] }],
        multiple: false,
      });
      if (!path) return;
      json = await invoke<string>("read_text_file", { path: path as string });
    } catch {
      const input = document.createElement("input");
      input.type = "file";
      input.accept = ".tsb,.json";
      const file = await new Promise<File | null>((resolve) => {
        input.onchange = () => resolve(input.files?.[0] || null);
        input.click();
      });
      if (!file) return;
      json = await file.text();
    }
    const backup = JSON.parse(json);
    if (!backup.version) {
      importStatus.value = t("settings.importFail") + ": invalid backup file";
      return;
    }
    await db.importAllData(backup);
    importStatus.value = t("settings.importSuccess");
  } catch (e: any) {
    importStatus.value = t("settings.importFail") + ": " + (e.message || e);
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
});
</script>
