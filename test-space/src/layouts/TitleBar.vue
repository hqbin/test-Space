<template>
  <div class="fixed top-0 left-0 right-0 z-50 h-9 flex items-center bg-glass-surface/15 backdrop-blur-[60px] border-b border-glass-border-light shadow-sm title-bar px-2">
    <div class="flex items-center gap-0 h-full select-none">
      <router-link v-for="item in navItems" :key="item.path" :to="item.path"
        class="glass-hover rounded-lg px-2 py-0.5 flex items-center gap-1 transition-colors"
        :class="isActive(item.path) ? 'glass-active font-semibold' : 'text-on-surface-variant'">
        <span class="material-symbols-outlined text-[14px]"
          :style="{ fontVariationSettings: `'FILL' ${isActive(item.path) ? 1 : 0}` }">{{ item.icon }}</span>
        <span class="font-label-xs text-label-xs whitespace-nowrap">{{ t(item.labelKey) }}</span>
      </router-link>
    </div>

    <div data-tauri-drag-region class="flex-1 h-full cursor-grab active:cursor-grabbing"></div>

    <router-link to="/settings"
      class="glass-hover rounded-lg px-2 py-0.5 flex items-center gap-1 transition-colors text-on-surface-variant select-none"
      :class="isActive('/settings') ? 'glass-active font-semibold' : ''">
      <span class="material-symbols-outlined text-[14px]"
        :style="{ fontVariationSettings: `'FILL' ${isActive('/settings') ? 1 : 0}` }">settings</span>
    </router-link>

    <div class="flex items-center h-full ml-1 select-none">
      <button @click="minimize" class="window-btn h-full px-2 flex items-center justify-center hover:bg-white/20 transition-colors rounded-lg" :title="t('nav.minimize')">
        <span class="material-symbols-outlined text-[14px] text-on-surface-variant">horizontal_rule</span>
      </button>
      <button @click="toggleMaximize" class="window-btn h-full px-2 flex items-center justify-center hover:bg-white/20 transition-colors rounded-lg" :title="isMax ? t('nav.restore') : t('nav.maximize')">
        <span class="material-symbols-outlined text-[14px] text-on-surface-variant">{{ isMax ? 'fullscreen_exit' : 'crop_square' }}</span>
      </button>
      <button @click="closeWindow" class="window-btn h-full px-2 flex items-center justify-center hover:bg-red-500/20 transition-colors rounded-lg group" :title="t('nav.close')">
        <span class="material-symbols-outlined text-[14px] text-on-surface-variant group-hover:text-red-500">close</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from "vue";
import { useRoute } from "vue-router";
import { useI18n } from "@/composables/useI18n";
import { getCurrentWindow } from "@tauri-apps/api/window";

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
});
</script>
