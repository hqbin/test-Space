<template>
  <div class="adb-tool-standalone">
    <iframe
      ref="iframeRef"
      src="/adb-tool/index.html"
      class="adb-tool-iframe"
      frameborder="0"
      allow="clipboard-read; clipboard-write"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue'

const iframeRef = ref(null)
</script>

<style scoped>
.adb-tool-standalone {
  width: 100%;
  height: 100%;
  overflow: hidden;
}

.adb-tool-iframe {
  width: 100%;
  height: 100%;
  border: none;
}
</style>
