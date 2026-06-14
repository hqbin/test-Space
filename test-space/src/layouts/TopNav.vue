<template>
  <nav
    v-if="showNav"
    class="hidden md:flex fixed top-0 right-0 w-[calc(100%-256px)] h-16 bg-glass-surface/15 backdrop-blur-[60px] border-b border-glass-border-light shadow-sm items-center justify-end px-margin-page z-40 font-label-md text-label-md"
  >
    <div class="flex items-center gap-4">
      <button class="glass-button px-4 py-2 rounded-full font-caption text-caption flex items-center gap-1.5">
        <span class="material-symbols-outlined text-[18px]">add</span>
        Quick Action
      </button>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";

const route = useRoute();

const showNav = computed(() => {
  return !route.path.startsWith("/case-space/editor");
});
</script>
