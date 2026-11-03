<template>
  <div class="w-screen h-screen flex flex-col overflow-hidden p-3 gap-3"
    style="background: radial-gradient(circle at 15% 50%, rgba(30,58,95,0.055), transparent 28%), radial-gradient(circle at 85% 30%, rgba(194,78,58,0.045), transparent 28%), #F1EDE4">
    <LogAnalysisPanel :serial="serial" />
  </div>
</template>

<script setup lang="ts">
import LogAnalysisPanel from './LogAnalysisPanel.vue'

const serial = new URLSearchParams(window.location.search).get('serial') || ''
</script>
