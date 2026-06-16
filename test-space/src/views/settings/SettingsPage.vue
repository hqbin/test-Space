<template>
  <div class="pt-12 max-w-5xl">

    <div class="flex flex-col gap-6">
      <!-- Appearance -->
      <div class="glass-card rounded-xl p-padding-card">
        <h3 class="font-headline-md text-headline-md text-on-surface mb-6">Appearance</h3>

        <!-- Theme -->
        <div class="flex items-center justify-between mb-6">
          <div>
            <span class="font-body-md text-body-md text-on-surface font-medium">Theme</span>
            <p class="font-caption text-caption text-on-surface-variant mt-0.5">Choose your preferred color scheme</p>
          </div>
          <div class="flex gap-2">
            <button
              class="glass-button px-4 py-2 rounded-full font-label-md text-label-md flex items-center gap-2"
              :class="theme === 'light' ? 'glass-active' : ''"
              @click="setTheme('light')"
            >
              <span class="material-symbols-outlined text-[18px]">light_mode</span>
              Light
            </button>
            <button
              class="glass-button px-4 py-2 rounded-full font-label-md text-label-md flex items-center gap-2"
              :class="theme === 'dark' ? 'glass-active' : ''"
              @click="setTheme('dark')"
            >
              <span class="material-symbols-outlined text-[18px]">dark_mode</span>
              Dark
            </button>
          </div>
        </div>

        <div class="border-t border-glass-border-light/30 pt-6">
          <div>
            <span class="font-body-md text-body-md text-on-surface font-medium">Data Backup</span>
            <p class="font-caption text-caption text-on-surface-variant mt-0.5">
              Export all data (field templates, case files, notes, history, settings) to a backup file,
              or restore from a previous backup.
            </p>
          </div>
          <div class="flex gap-4 mt-4">
            <button class="glass-button px-6 py-3 rounded-full font-label-md text-label-md flex items-center gap-2" @click="handleExport">
              <span class="material-symbols-outlined text-[18px]">file_download</span>
              Export All Data
            </button>
            <button class="glass-button px-6 py-3 rounded-full font-label-md text-label-md flex items-center gap-2" @click="handleImport">
              <span class="material-symbols-outlined text-[18px]">file_upload</span>
              Import Data
            </button>
          </div>
          <p v-if="importStatus" class="mt-4 font-body-md text-body-md" :class="importStatus.startsWith('Error') ? 'text-error' : 'text-success-indicator'">{{ importStatus }}</p>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import * as db from "@/services/database";

const theme = ref("light");
const importStatus = ref("");

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
        importStatus.value = "Exported successfully";
      }
    } catch {
      const blob = new Blob([json], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "test-space-backup.tsb";
      a.click();
      URL.revokeObjectURL(url);
      importStatus.value = "Exported successfully (browser download)";
    }
  } catch (e: any) {
    importStatus.value = "Export failed: " + (e.message || e);
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
      importStatus.value = "Error: invalid backup file";
      return;
    }
    await db.importAllData(backup);
    importStatus.value = "Import successful. Restart the app to reload data.";
  } catch (e: any) {
    importStatus.value = "Import failed: " + (e.message || e);
  }
}

onMounted(() => loadTheme());
</script>
