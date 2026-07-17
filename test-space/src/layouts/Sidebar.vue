<template>
  <div class="fixed top-0 left-0 right-0 z-50 h-2" @mouseenter="onTriggerEnter" @mouseleave="onTriggerLeave" />

  <Transition name="slide-down">
      <div v-if="showBar" class="fixed top-0 left-0 right-0 z-50 bg-glass-surface/15 backdrop-blur-[60px] border-b border-glass-border-light shadow-sm top-bar"
      @mouseenter="onBarEnter" @mouseleave="onBarLeave">
      <div class="flex items-center justify-between px-6 py-2.5 max-w-screen-2xl mx-auto">
        <div class="flex items-center gap-1">
          <span class="font-headline-lg text-headline-lg font-black text-on-surface tracking-tight mr-5 select-none">Test Space</span>
          <router-link v-for="item in navItems" :key="item.path" :to="item.path"
            class="glass-hover rounded-xl px-4 py-2 flex items-center gap-2 transition-colors"
            :class="isActive(item.path) ? 'glass-active font-semibold' : 'text-on-surface-variant'">
            <span class="material-symbols-outlined text-[18px]"
              :style="{ fontVariationSettings: `'FILL' ${isActive(item.path) ? 1 : 0}` }">{{ item.icon }}</span>
            <span class="font-label-md text-label-md whitespace-nowrap">{{ t(item.labelKey) }}</span>
          </router-link>
        </div>
        <div class="flex items-center gap-1">
          <router-link to="/settings"
            class="glass-hover rounded-xl px-4 py-2 flex items-center gap-2 transition-colors text-on-surface-variant"
            :class="isActive('/settings') ? 'glass-active font-semibold' : ''">
            <span class="material-symbols-outlined text-[18px]"
              :style="{ fontVariationSettings: `'FILL' ${isActive('/settings') ? 1 : 0}` }">settings</span>
            <span class="font-label-md text-label-md whitespace-nowrap">{{ t("nav.settings") }}</span>
          </router-link>

          <button
            class="glass-hover rounded-xl px-3 py-2 flex items-center gap-2 transition-colors text-on-surface-variant select-none"
            :class="syncBusy ? 'opacity-60 cursor-not-allowed' : ''"
            @click="runSync"
          >
            <span class="material-symbols-outlined text-[18px]" :class="syncBusy ? 'animate-spin' : ''">sync</span>
          </button>
        </div>
      </div>
    </div>
  </Transition>

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
</template>

<script setup lang="ts">
import { onUnmounted, ref } from "vue";
import { useRoute } from "vue-router";
import { useI18n } from "@/composables/useI18n";
import { syncBackupToCloud } from "@/services/cloudSync";

const { t } = useI18n();
const route = useRoute();
const showBar = ref(false);
let showTimeout: ReturnType<typeof setTimeout> | null = null;
let hideTimeout: ReturnType<typeof setTimeout> | null = null;

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
];

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

function clearTimer() {
  if (syncToastTimer) clearTimeout(syncToastTimer);
}

onUnmounted(() => clearTimer());

function isActive(path: string) {
  if (path === "/api-space") return route.path.startsWith(path);
  return route.path === path;
}

function clearAll() {
  if (showTimeout) { clearTimeout(showTimeout); showTimeout = null; }
  if (hideTimeout) { clearTimeout(hideTimeout); hideTimeout = null; }
}
function scheduleShow() {
  clearAll();
  showTimeout = setTimeout(() => { showBar.value = true; }, 300);
}
function scheduleHide() {
  clearAll();
  hideTimeout = setTimeout(() => { showBar.value = false; }, 1500);
}
function onTriggerEnter() { scheduleShow(); }
function onTriggerLeave() { clearAll(); if (showBar.value) scheduleHide(); }
function onBarEnter() { clearAll(); }
function onBarLeave() { scheduleHide(); }
</script>

<style scoped>
.slide-down-enter-active {
  transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.25s ease-out;
}
.slide-down-leave-active {
  transition: transform 0.2s cubic-bezier(0.4, 0, 1, 1), opacity 0.15s ease-in;
}
.slide-down-enter-from {
  transform: translateY(-100%);
  opacity: 0;
}
.slide-down-leave-to {
  transform: translateY(-100%);
  opacity: 0;
}
</style>
