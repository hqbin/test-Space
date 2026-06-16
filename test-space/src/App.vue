<template>
  <router-view />
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from "vue";
import { useRouter } from "vue-router";

const pages = ["/device-space", "/notes-space", "/case-space", "/script-space", "/settings"];

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

onMounted(() => {
  window.addEventListener("keydown", onKeydown);
});

onUnmounted(() => {
  window.removeEventListener("keydown", onKeydown);
});
</script>
