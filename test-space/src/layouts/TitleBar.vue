<template>
  <div class="h-12 shrink-0 flex items-center bg-glass-surface/60 backdrop-blur-[30px] border-b border-glass-border-light title-bar px-4">
    <!-- 杂志刊头 -->
    <div class="flex items-center gap-3 h-full select-none shrink-0 pr-2">
      <div class="flex items-baseline gap-1.5">
        <span class="font-editorial italic text-[18px] leading-none text-ink tracking-tight">Test</span>
        <span class="font-editorial italic text-[18px] leading-none text-rust tracking-tight">Space</span>
      </div>
      <span class="folio hidden md:inline">— vol.1 · iss.15</span>
    </div>

    <span class="h-4 w-px bg-hairline-strong mx-2 shrink-0"></span>

    <div class="flex items-center gap-0.5 h-full select-none">
      <router-link v-for="(item, i) in navItems" :key="item.path" :to="item.path"
        class="glass-hover rounded-md px-2.5 py-1.5 flex items-center gap-1.5 relative"
        :class="isActive(item.path) ? 'glass-active' : 'text-graphite'">
        <span class="folio opacity-70 mr-0.5" v-if="isActive(item.path)">§{{ String(i + 1).padStart(2, '0') }}</span>
        <span class="material-symbols-outlined text-[15px]"
          :style="{ fontVariationSettings: `'FILL' ${isActive(item.path) ? 1 : 0}` }">{{ item.icon }}</span>
        <span class="text-[12px] font-semibold tracking-wide whitespace-nowrap">{{ t(item.labelKey) }}</span>
      </router-link>
    </div>

    <div data-tauri-drag-region class="flex-1 h-full cursor-grab active:cursor-grabbing"></div>

    <router-link to="/settings"
      class="glass-hover rounded-md px-2.5 py-1.5 flex items-center gap-1.5 text-graphite select-none"
      :class="isActive('/settings') ? 'glass-active' : ''">
      <span class="material-symbols-outlined text-[15px]"
        :style="{ fontVariationSettings: `'FILL' ${isActive('/settings') ? 1 : 0}` }">settings</span>
    </router-link>

    <button
      class="glass-hover rounded-md px-2.5 py-1.5 flex items-center gap-1.5 text-graphite select-none"
      :class="syncBusy ? 'opacity-50 cursor-not-allowed' : ''"
      @click="runSync"
    >
      <span class="material-symbols-outlined text-[15px]" :class="syncBusy ? 'animate-spin' : ''">sync</span>
    </button>

    <Teleport to="body">
      <div v-if="syncToast.show" class="fixed left-1/2 -translate-x-1/2 top-4 z-[99999] pointer-events-none">
        <div class="glass-panel rounded-full px-5 py-2.5 flex items-center gap-2 bg-white/90 backdrop-blur-sm border">
          <span v-if="syncToast.type === 'loading'" class="material-symbols-outlined text-[18px] animate-spin text-on-surface-variant">sync</span>
          <span v-else-if="syncToast.type === 'success'" class="material-symbols-outlined text-[18px] text-success-indicator">check_circle</span>
          <span v-else class="material-symbols-outlined text-[18px] text-error">error</span>
          <span class="text-[13px] font-semibold" :class="syncToast.type === 'error' ? 'text-error' : 'text-on-surface'">{{ syncToast.message }}</span>
        </div>
      </div>
    </Teleport>

    <div class="flex items-center h-full ml-2 select-none shrink-0">
      <button @click="minimize" class="window-btn h-full w-11 flex items-center justify-center rounded-lg group" :title="t('nav.minimize')">
        <span class="material-symbols-outlined text-[15px] text-on-surface-variant window-btn-icon">horizontal_rule</span>
      </button>
      <button @click="toggleMaximize" class="window-btn h-full w-11 flex items-center justify-center rounded-lg group" :title="isMax ? t('nav.restore') : t('nav.maximize')">
        <span class="material-symbols-outlined text-[15px] text-on-surface-variant window-btn-icon">{{ isMax ? 'fullscreen_exit' : 'crop_square' }}</span>
      </button>
      <button @click="closeWindow" class="window-btn h-full w-11 flex items-center justify-center rounded-lg group" :title="t('nav.close')">
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
  { path: "/ai-space", labelKey: "nav.ai", icon: "smart_toy" },
];

function isActive(path: string) {
  if (path === "/api-space" || path === "/ai-space") return route.path.startsWith(path);
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
    }, 5000);
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
  transition: color 0.16s ease, background-color 0.16s ease;
}
.window-btn:hover {
  background-color: rgba(28, 27, 31, 0.05);
}
.window-btn:hover .window-btn-icon {
  color: #C24E3A;
}
html.dark .window-btn:hover {
  background-color: rgba(232, 227, 214, 0.06);
}
html.dark .window-btn:hover .window-btn-icon {
  color: #E8734F;
}
</style>
