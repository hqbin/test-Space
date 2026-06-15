<template>
  <div class="fixed top-0 left-0 right-0 z-50 h-2" @mouseenter="onTriggerEnter" @mouseleave="onTriggerLeave" />

  <Transition name="slide-down">
    <div v-if="showBar" class="fixed top-0 left-0 right-0 z-50 bg-glass-surface/15 backdrop-blur-[60px] border-b border-glass-border-light shadow-sm"
      @mouseenter="onBarEnter" @mouseleave="onBarLeave">
      <div class="flex items-center justify-between px-6 py-2.5 max-w-screen-2xl mx-auto">
        <div class="flex items-center gap-1">
          <span class="font-headline-lg text-headline-lg font-black text-on-surface tracking-tight mr-5 select-none">Test Space</span>
          <router-link v-for="item in navItems" :key="item.path" :to="item.path"
            class="glass-hover rounded-xl px-4 py-2 flex items-center gap-2 transition-colors"
            :class="isActive(item.path) ? 'glass-active font-semibold' : 'text-on-surface-variant'">
            <span class="material-symbols-outlined text-[18px]"
              :style="{ fontVariationSettings: `'FILL' ${isActive(item.path) ? 1 : 0}` }">{{ item.icon }}</span>
            <span class="font-label-md text-label-md whitespace-nowrap">{{ item.label }}</span>
          </router-link>
        </div>
        <router-link to="/settings"
          class="glass-hover rounded-xl px-4 py-2 flex items-center gap-2 transition-colors text-on-surface-variant"
          :class="isActive('/settings') ? 'glass-active font-semibold' : ''">
          <span class="material-symbols-outlined text-[18px]"
            :style="{ fontVariationSettings: `'FILL' ${isActive('/settings') ? 1 : 0}` }">settings</span>
          <span class="font-label-md text-label-md whitespace-nowrap">Settings</span>
        </router-link>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRoute } from "vue-router";

const route = useRoute();
const showBar = ref(false);
let hideTimeout: ReturnType<typeof setTimeout> | null = null;

interface NavItem {
  path: string;
  label: string;
  icon: string;
}

const navItems: NavItem[] = [
  { path: "/case-space", label: "Case", icon: "folder_shared" },
  { path: "/device-space", label: "Device", icon: "developer_board" },
  { path: "/notes-space", label: "Notes", icon: "description" },
  { path: "/script-space", label: "Scripts", icon: "code" },
];

function isActive(path: string) {
  if (path === "/case-space") return route.path.startsWith(path);
  return route.path === path;
}

function clearHide() {
  if (hideTimeout) { clearTimeout(hideTimeout); hideTimeout = null; }
}
function scheduleHide() {
  clearHide();
  hideTimeout = setTimeout(() => { showBar.value = false; }, 1500);
}
function onTriggerEnter() { clearHide(); showBar.value = true; }
function onTriggerLeave() { scheduleHide(); }
function onBarEnter() { clearHide(); }
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
