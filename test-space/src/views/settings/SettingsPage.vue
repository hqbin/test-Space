<template>
  <div class="pt-12 max-w-5xl">
    <h2 class="font-display-lg text-display-lg font-semibold text-on-surface tracking-tight mb-8">Settings</h2>

    <div class="flex flex-col gap-6">
      <!-- Profile -->
      <div class="glass-card rounded-xl p-padding-card">
        <h3 class="font-headline-md text-headline-md text-on-surface mb-6">Profile</h3>
        <div class="flex items-center gap-4 mb-6">
          <div class="w-16 h-16 rounded-full bg-primary-fixed flex items-center justify-center text-2xl text-on-primary-fixed font-bold">
            {{ initials }}
          </div>
          <div>
            <p class="font-body-lg text-body-lg text-on-surface font-medium">{{ userStore.displayName }}</p>
            <p class="font-caption text-caption text-on-surface-variant">{{ userStore.userInfo?.email || "No email" }}</p>
          </div>
        </div>
        <div class="flex flex-col gap-4">
          <div class="flex items-center justify-between py-3 border-b border-glass-border-dark">
            <span class="font-body-md text-body-md text-on-surface-variant">Username</span>
            <span class="font-body-md text-body-md text-on-surface font-medium">{{ userStore.userInfo?.username }}</span>
          </div>
          <div class="flex items-center justify-between py-3 border-b border-glass-border-dark">
            <span class="font-body-md text-body-md text-on-surface-variant">Role</span>
            <span class="font-body-md text-body-md text-on-surface font-medium">{{ userStore.userInfo?.role || "Tester" }}</span>
          </div>
        </div>
      </div>

      <!-- Theme -->
      <div class="glass-card rounded-xl p-padding-card">
        <h3 class="font-headline-md text-headline-md text-on-surface mb-6">Appearance</h3>
        <div class="flex items-center justify-between">
          <span class="font-body-md text-body-md text-on-surface-variant">Theme</span>
          <div class="flex gap-2">
            <button
              class="glass-button px-4 py-2 rounded-full font-label-md text-label-md"
              :class="theme === 'light' ? 'glass-active' : ''"
              @click="theme = 'light'"
            >
              Light
            </button>
            <button
              class="glass-button px-4 py-2 rounded-full font-label-md text-label-md"
              :class="theme === 'dark' ? 'glass-active' : ''"
              @click="theme = 'dark'"
            >
              Dark
            </button>
          </div>
        </div>
      </div>

      <!-- Platform Connection -->
      <div class="glass-card rounded-xl p-padding-card">
        <h3 class="font-headline-md text-headline-md text-on-surface mb-6">Platform Connection</h3>
        <div class="flex flex-col gap-4">
          <div class="flex items-center justify-between py-3 border-b border-glass-border-dark">
            <span class="font-body-md text-body-md text-on-surface-variant">Server URL</span>
            <span class="font-body-md text-body-md text-on-surface font-medium font-mono">http://localhost:8000</span>
          </div>
          <div class="flex items-center justify-between py-3">
            <span class="font-body-md text-body-md text-on-surface-variant">Status</span>
            <span class="flex items-center gap-2 font-body-md text-body-md">
              <span class="w-2 h-2 rounded-full bg-success-indicator shadow-[0_0_8px_#22C55E]" />
              Connected
            </span>
          </div>
        </div>
      </div>

      <!-- Data Management -->
      <div class="glass-card rounded-xl p-padding-card">
        <h3 class="font-headline-md text-headline-md text-on-surface mb-6">Data Management</h3>
        <p class="font-body-md text-body-md text-on-surface-variant mb-6">
          Export all data (field templates, case files, history, settings) to a backup file,
          or import from a previous backup.
        </p>
        <div class="flex gap-4">
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

      <!-- Logout -->
      <button
        class="w-full glass-button rounded-xl p-padding-card text-error font-label-md text-label-md text-center"
        @click="handleLogout"
      >
        Sign Out
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import { useRouter } from "vue-router";
import { useUserStore } from "@/stores/user";
import * as db from "@/services/database";

const router = useRouter();
const userStore = useUserStore();
const theme = ref("light");
const importStatus = ref("");

const initials = computed(() => {
  const name = userStore.displayName;
  return name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
});

function handleLogout() {
  userStore.logout();
  router.push("/login");
}

async function handleExport() {
  importStatus.value = ""
  try {
    const data = await db.exportAllData()
    const json = JSON.stringify(data, null, 2)
    try {
      const { save } = await import('@tauri-apps/plugin-dialog')
      const { invoke } = await import('@tauri-apps/api/core')
      const path = await save({
        filters: [{ name: 'Test Space Backup', extensions: ['tsb'] }],
        defaultPath: 'test-space-backup.tsb',
      })
      if (path) {
        await invoke('write_text_file', { path, content: json })
        importStatus.value = "Exported successfully"
      }
    } catch {
      const blob = new Blob([json], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'test-space-backup.tsb'
      a.click()
      URL.revokeObjectURL(url)
      importStatus.value = "Exported successfully (browser download)"
    }
  } catch (e: any) {
    importStatus.value = "Export failed: " + (e.message || e)
  }
}

async function handleImport() {
  importStatus.value = ""
  try {
    let json: string
    try {
      const { open } = await import('@tauri-apps/plugin-dialog')
      const { invoke } = await import('@tauri-apps/api/core')
      const path = await open({
        filters: [{ name: 'Test Space Backup', extensions: ['tsb', 'json'] }],
        multiple: false,
      })
      if (!path) return
      json = await invoke<string>('read_text_file', { path: path as string })
    } catch {
      // Tauri unavailable, browser fallback
      const input = document.createElement('input')
      input.type = 'file'
      input.accept = '.tsb,.json'
      const file = await new Promise<File | null>((resolve) => {
        input.onchange = () => resolve(input.files?.[0] || null)
        input.click()
      })
      if (!file) return
      json = await file.text()
    }
    const backup = JSON.parse(json)
    if (!backup.version) {
      importStatus.value = "Error: invalid backup file"
      return
    }
    await db.importAllData(backup)
    importStatus.value = "Import successful. Restart the app to reload data."
  } catch (e: any) {
    importStatus.value = "Import failed: " + (e.message || e)
  }
}
</script>
