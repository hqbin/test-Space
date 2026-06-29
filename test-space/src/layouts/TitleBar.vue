<template>
  <div class="h-12 shrink-0 flex items-center bg-glass-surface/15 backdrop-blur-[60px] border-b border-glass-border-light shadow-sm title-bar px-3">
    <div class="flex items-center gap-1 h-full select-none">
      <router-link v-for="item in navItems" :key="item.path" :to="item.path"
        class="glass-hover rounded-lg px-3 py-1.5 flex items-center gap-1.5 transition-colors"
        :class="isActive(item.path) ? 'glass-active font-semibold' : 'text-on-surface-variant'">
        <span class="material-symbols-outlined text-[15px]"
          :style="{ fontVariationSettings: `'FILL' ${isActive(item.path) ? 1 : 0}` }">{{ item.icon }}</span>
        <span class="font-label-xs text-label-xs whitespace-nowrap">{{ t(item.labelKey) }}</span>
      </router-link>
    </div>

    <div data-tauri-drag-region class="flex-1 h-full cursor-grab active:cursor-grabbing"></div>

    <router-link to="/settings"
      class="glass-hover rounded-lg px-3 py-1.5 flex items-center gap-1.5 transition-colors text-on-surface-variant select-none"
      :class="isActive('/settings') ? 'glass-active font-semibold' : ''">
      <span class="material-symbols-outlined text-[15px]"
        :style="{ fontVariationSettings: `'FILL' ${isActive('/settings') ? 1 : 0}` }">settings</span>
    </router-link>

    <button
      class="glass-hover rounded-lg px-3 py-1.5 flex items-center gap-1.5 transition-colors text-on-surface-variant select-none"
      :class="syncBusy ? 'opacity-60 cursor-not-allowed' : ''"
      @click="runSync"
    >
      <span class="material-symbols-outlined text-[15px]" :class="syncBusy ? 'animate-spin' : ''">sync</span>
    </button>

    <Teleport to="body">
      <div v-if="syncToast.show" class="fixed left-1/2 -translate-x-1/2 top-4 z-[99999] pointer-events-none">
        <div class="glass-panel rounded-full px-5 py-2.5 flex items-center gap-2 shadow-lg bg-white/90 backdrop-blur-sm border">
          <span v-if="syncToast.type === 'loading'" class="material-symbols-outlined text-[18px] animate-spin text-on-surface-variant">sync</span>
          <span v-else-if="syncToast.type === 'success'" class="material-symbols-outlined text-[18px] text-success-indicator">check_circle</span>
          <span v-else class="material-symbols-outlined text-[18px] text-error">error</span>
          <span class="text-[13px] font-semibold" :class="syncToast.type === 'error' ? 'text-error' : 'text-on-surface'">{{ syncToast.message }}</span>
        </div>
      </div>
    </Teleport>

    <div class="flex items-center h-full ml-2 select-none">
      <button @click="minimize" class="window-btn h-full px-2.5 flex items-center justify-center transition-all rounded-lg group hover:scale-110" :title="t('nav.minimize')">
        <span class="material-symbols-outlined text-[15px] text-on-surface-variant window-btn-icon">horizontal_rule</span>
      </button>
      <button @click="toggleMaximize" class="window-btn h-full px-2.5 flex items-center justify-center transition-all rounded-lg group hover:scale-110" :title="isMax ? t('nav.restore') : t('nav.maximize')">
        <span class="material-symbols-outlined text-[15px] text-on-surface-variant window-btn-icon">{{ isMax ? 'fullscreen_exit' : 'crop_square' }}</span>
      </button>
      <button @click="closeWindow" class="window-btn h-full px-2.5 flex items-center justify-center transition-all rounded-lg group hover:scale-110" :title="t('nav.close')">
        <span class="material-symbols-outlined text-[15px] text-on-surface-variant group-hover:text-red-500">close</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from "vue";
import { useRoute } from "vue-router";
import { useI18n } from "@/composables/useI18n";
import { getCurrentWindow } from "@tauri-apps/api/window";
import { syncBackupToCloud } from "@/services/cloudSync";

const { t } = useI18n();
const route = useRoute();
const isMax = ref(false);

const appWindow = getCurrentWindow();

interface NavItem {
  path: string;
  labelKey: string;
  icon: string;
}

const navItems: NavItem[] = [
  { path: "/device-space", labelKey: "nav.device", icon: "developer_board" },
  { path: "/notes-space", labelKey: "nav.notes", icon: "description" },
  { path: "/api-space", labelKey: "nav.api", icon: "api" },
  { path: "/script-space", labelKey: "nav.scripts", icon: "code" },
  { path: "/case-space", labelKey: "nav.case", icon: "folder_shared" },
];

function isActive(path: string) {
  if (path === "/case-space" || path === "/api-space") return route.path.startsWith(path);
  return route.path === path;
}

async function minimize() {
  await appWindow.minimize();
}

async function toggleMaximize() {
  await appWindow.toggleMaximize();
  isMax.value = await appWindow.isMaximized();
}

async function closeWindow() {
  await appWindow.close();
}

async function checkMaximized() {
  try {
    isMax.value = await appWindow.isMaximized();
  } catch {}
}

let unlistenResize: (() => void) | null = null;

const syncBusy = ref(false);
const syncToast = ref<{ show: boolean; message: string; type: "loading" | "success" | "error" }>({ show: false, message: "", type: "loading" });
let syncToastTimer: ReturnType<typeof setTimeout> | null = null;

function showSyncToast(message: string, type: "loading" | "success" | "error") {
  syncToast.value = { show: true, message, type };
  if (syncToastTimer) clearTimeout(syncToastTimer);
  if (type !== "loading") {
    syncToastTimer = setTimeout(() => {
      syncToast.value.show = false;
    }, 3000);
  }
}

async function runSync() {
  if (syncBusy.value) return;
  syncBusy.value = true;
  showSyncToast(t("cloudSync.syncing"), "loading");
  try {
    await syncBackupToCloud();
    showSyncToast(t("cloudSync.success"), "success");
  } catch (e: any) {
    showSyncToast(`${t("cloudSync.fail")}: ${e?.message || String(e)}`, "error");
  } finally {
    syncBusy.value = false;
    if (syncToast.value.type === "loading") syncToast.value.show = false;
  }
}

onMounted(async () => {
  await checkMaximized();
  try {
    unlistenResize = await appWindow.onResized(() => {
      checkMaximized();
    });
  } catch {}
});

onUnmounted(() => {
  if (unlistenResize) unlistenResize();
  if (syncToastTimer) clearTimeout(syncToastTimer);
});
</script>

<style scoped>
.window-btn {
  transition: all 0.2s ease;
}
.window-btn:hover .window-btn-icon {
  color: #f97316;
}
html.dark .window-btn:hover .window-btn-icon {
  color: #fb923c;
}
</style>
