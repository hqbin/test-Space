<template>
  <router-view />
</template>

<script setup lang="ts">
import { onMounted } from "vue";
import { getCurrentWindow, LogicalSize } from "@tauri-apps/api/window";

onMounted(async () => {
  const win = getCurrentWindow();
  try {
    const saved = localStorage.getItem("appWindowSize");
    if (saved) {
      const { width, height } = JSON.parse(saved);
      await win.setSize(new LogicalSize(width, height));
    }
  } catch {}
  await win.onResized(async ({ payload }) => {
    try {
      localStorage.setItem("appWindowSize", JSON.stringify({ width: payload.width, height: payload.height }));
    } catch {}
  });
});
</script>
