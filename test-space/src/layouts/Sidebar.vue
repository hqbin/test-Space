<template>
  <aside
    class="hidden md:flex fixed left-0 top-0 h-full w-[256px] rounded-r-lg bg-glass-surface/15 backdrop-blur-[60px] border-r border-glass-border-light shadow-sm flex-col p-6 gap-y-4 z-50 font-body-md text-body-md"
  >
    <div class="mb-8 pl-4">
      <h1 class="font-headline-lg text-headline-lg font-black text-on-surface tracking-tight">Test Space</h1>
      <p class="font-caption text-caption text-on-surface-variant mt-1">Engineering Workspace</p>
    </div>
    <nav class="flex flex-col gap-2">
      <router-link
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        class="glass-hover rounded-xl px-4 py-3 flex items-center gap-3 hover:-translate-y-0.5 active:scale-95"
        :class="isActive(item.path)
          ? 'glass-active font-semibold'
          : 'text-on-surface-variant'"
      >
        <span
          class="material-symbols-outlined text-[20px]"
          :style="{ fontVariationSettings: `'FILL' ${isActive(item.path) ? 1 : 0}` }"
        >
          {{ item.icon }}
        </span>
        <span>{{ item.label }}</span>
      </router-link>
    </nav>
    <div class="mt-auto">
      <router-link
        to="/settings"
        class="glass-hover rounded-xl px-4 py-3 flex items-center gap-3 hover:-translate-y-0.5 active:scale-95"
        :class="isActive('/settings')
          ? 'glass-active font-semibold'
          : 'text-on-surface-variant'"
      >
        <span
          class="material-symbols-outlined text-[20px]"
          :style="{ fontVariationSettings: `'FILL' ${isActive('/settings') ? 1 : 0}` }"
        >
          settings
        </span>
        <span>Settings</span>
      </router-link>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { useRoute } from "vue-router";

const route = useRoute();

interface NavItem {
  path: string;
  label: string;
  icon: string;
}

const navItems: NavItem[] = [
  { path: "/workspace", label: "Workspace", icon: "dashboard" },
  { path: "/case-space", label: "Case Space", icon: "folder_shared" },
  { path: "/device-space", label: "Device Space", icon: "developer_board" },
  { path: "/notes-space", label: "Notes Space", icon: "description" },
  { path: "/script-space", label: "Script Space", icon: "code" },
];

function isActive(path: string) {
  if (path === "/case-space") {
    return route.path.startsWith(path);
  }
  return route.path === path;
}
</script>
