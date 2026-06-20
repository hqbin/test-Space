<template>
  <router-view />
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from "vue";
import { useRouter } from "vue-router";
import { getCurrentWindow } from "@tauri-apps/api/window";
import { useI18n } from "@/composables/useI18n";

const { initLanguage } = useI18n();

const pages = ["/device-space", "/notes-space", "/api-space", "/script-space", "/case-space", "/settings"];

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
  } else if (e.ctrlKey && e.key >= "1" && e.key <= "6") {
    e.preventDefault();
    router.push(pages[parseInt(e.key) - 1]);
  }
}

onMounted(async () => {
  initLanguage();
  window.addEventListener("keydown", onKeydown);
  try {
    const appWindow = getCurrentWindow();
    await appWindow.setIcon("icons/32x32.png");
  } catch {}
});

onUnmounted(() => {
  window.removeEventListener("keydown", onKeydown);
});
</script>
