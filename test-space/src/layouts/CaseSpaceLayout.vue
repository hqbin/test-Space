<template>
  <div :class="isEditor ? '' : 'pt-12'">
    <router-view />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
const route = useRoute()
const isEditor = computed(() => route.path === '/case-space/editor')
</script>
