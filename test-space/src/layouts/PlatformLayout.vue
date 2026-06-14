<template>
  <div class="pt-12">
    <div class="mb-8 flex justify-center">
      <div class="glass-panel rounded-full p-1 inline-flex shadow-sm">
        <router-link
          v-for="tab in tabs"
          :key="tab.path"
          :to="tab.path"
          class="glass-hover px-6 py-2 rounded-full font-label-md text-label-md flex items-center gap-2"
          :class="isActiveTab(tab.path)
            ? 'glass-active'
            : 'text-on-surface-variant'"
        >
          <span class="material-symbols-outlined text-[18px]" :style="{ fontVariationSettings: `'FILL' ${isActiveTab(tab.path) ? 1 : 0}` }">
            {{ tab.icon }}
          </span>
          {{ tab.label }}
        </router-link>
      </div>
    </div>
    <router-view />
  </div>
</template>

<script setup lang="ts">
import { useRoute } from "vue-router";

const route = useRoute();

interface TabItem {
  path: string;
  label: string;
  icon: string;
}

const tabs: TabItem[] = [
  { path: "/platform-space/analytics", label: "Data Analytics", icon: "analytics" },
  { path: "/platform-space/database", label: "Database", icon: "database" },
  { path: "/platform-space/version-release", label: "Version Release", icon: "deployed_code" },
];

function isActiveTab(path: string) {
  return route.path === path;
}
</script>
