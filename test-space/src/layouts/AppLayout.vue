<template>
  <div
    class="min-h-screen font-body-md text-body-md text-on-surface antialiased selection:bg-secondary-fixed selection:text-on-secondary-fixed"
    :style="bgStyle"
  >
    <Sidebar />
    <main class="md:ml-[256px] px-margin-page pb-20 md:pb-12 box-border w-full md:w-[calc(100%-256px)] min-h-screen">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";
import Sidebar from "./Sidebar.vue";

const route = useRoute();

const bgStyle = computed(() => {
  const path = route.path;
  if (path.startsWith("/workspace")) {
    return { background: "radial-gradient(circle at 50% 0%, #DAE1FF 0%, #F9F9FB 50%)" };
  }
  if (path.startsWith("/case-space")) {
    return {
      background:
        "radial-gradient(circle at top left, rgba(226,223,255,0.4) 0%, transparent 40%), radial-gradient(circle at bottom right, rgba(0,80,203,0.05) 0%, transparent 40%), #F9F9FB",
    };
  }
  if (path.startsWith("/device-space")) {
    return {
      background:
        "radial-gradient(circle at 15% 50%, rgba(76,74,202,0.05), transparent 25%), radial-gradient(circle at 85% 30%, rgba(0,80,203,0.05), transparent 25%), #F9F9FB",
    };
  }
  if (path.startsWith("/notes-space")) {
    return {
      background: "radial-gradient(circle at 50% 0%, #F9F9FB 0%, #F3F3F5 100%)",
    };
  }
  return { background: "#F9F9FB" };
});
</script>
