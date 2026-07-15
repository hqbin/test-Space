<template>
  <div class="font-mono text-caption select-text">
    <JsonNode :data="data" path="$" @select="onSelect" />
  </div>
</template>

<script setup lang="ts">
import JsonNode from './JsonNode.vue'

defineProps<{ data: any }>()
const emit = defineEmits<{ select: [path: string, value: string] }>()

function onSelect(path: string, value: string) {
  emit('select', path, value)
}
</script>
