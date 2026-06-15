<template>
  <router-view />
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from "vue";
import { useRouter } from "vue-router";
import { getCurrentWindow, LogicalSize } from "@tauri-apps/api/window";

const pages = ["/case-space", "/device-space", "/notes-space", "/script-space", "/settings"];

const router = useRouter();

function onKeydown(e: KeyboardEvent) {
  if (e.ctrlKey && e.key === "Tab") {
    e.preventDefault();
    const current = router.currentRoute.value.path;
    const idx = pages.indexOf(current);
    if (e.shiftKey) {
      router.push(pages[(idx - 1 + pages.length) % pages.length]);
    } else {
      router.push(pages[(idx + 1) % pages.length]);
    }
  } else if (e.ctrlKey && e.key >= "1" && e.key <= "5") {
    e.preventDefault();
    router.push(pages[parseInt(e.key) - 1]);
  }
}

onMounted(async () => {
  window.addEventListener("keydown", onKeydown);
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

onUnmounted(() => window.removeEventListener("keydown", onKeydown));
</script>
