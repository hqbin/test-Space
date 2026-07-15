<template>
  <div class="py-0.5">
    <!-- Expandable: object / array -->
    <template v-if="isExpandable">
      <div class="flex items-center gap-1.5 group cursor-pointer hover:bg-white/[0.08] rounded px-1 -mx-1" @click.stop="expanded = !expanded">
        <span class="material-symbols-outlined text-[14px] text-on-surface-variant transition-transform" :class="expanded ? 'rotate-90' : ''">chevron_right</span>
        <span v-if="keyName !== null" class="text-primary">{{ keyName }}:</span>
        <span class="text-on-surface-variant">{{ expandLabel }}</span>
        <button class="glass-hover rounded p-0.5 text-on-surface-variant hover:text-secondary opacity-0 group-hover:opacity-100 transition-all ml-auto" title="添加断言" @click.stop="emitSelect">
          <span class="material-symbols-outlined text-[14px]">add_circle</span>
        </button>
      </div>
      <div v-if="expanded" class="pl-4 border-l border-white/10 ml-1.5">
        <template v-if="Array.isArray(data)">
          <JsonNode v-for="(item, idx) in data" :key="idx" :data="item" :key-name="idx" :parent-path="fullPath" @select="(p, v) => $emit('select', p, v)" />
        </template>
        <template v-else>
          <JsonNode v-for="(val, k) in data" :key="String(k)" :data="val" :key-name="String(k)" :parent-path="fullPath" @select="(p, v) => $emit('select', p, v)" />
        </template>
      </div>
    </template>

    <!-- Leaf: primitive -->
    <template v-else>
      <div class="flex items-center gap-1.5 group rounded px-1 -mx-1">
        <span class="w-3.5" />
        <span v-if="keyName !== null" class="text-primary">{{ keyName }}:</span>
        <span :class="valueClass" class="cursor-pointer hover:bg-white/[0.08] rounded px-0.5 -mx-0.5" @click.stop="emitSelect">{{ displayValue }}</span>
        <button class="glass-hover rounded p-0.5 text-on-surface-variant hover:text-secondary opacity-0 group-hover:opacity-100 transition-all shrink-0" title="添加断言" @click.stop="emitSelect">
          <span class="material-symbols-outlined text-[14px]">add_circle</span>
        </button>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const props = defineProps<{
  data: any
  keyName?: string | number | null
  parentPath?: string
}>()

const emit = defineEmits<{ select: [path: string, value: string] }>()

const expanded = ref(false)

const expandLabel = computed(() => {
  if (Array.isArray(props.data)) return `[${props.data.length}]`
  return `{${Object.keys(props.data).length}}`
})

const isExpandable = computed(() => {
  return props.data !== null && typeof props.data === 'object'
})

const fullPath = computed(() => {
  if (props.keyName === null || props.keyName === undefined) return props.parentPath || '$'
  if (typeof props.keyName === 'number') {
    return props.parentPath ? `${props.parentPath}[${props.keyName}]` : `$[${props.keyName}]`
  }
  return props.parentPath ? `${props.parentPath}.${props.keyName}` : `$${props.keyName}`
})

const displayValue = computed(() => {
  if (props.data === null) return 'null'
  if (props.data === undefined) return 'undefined'
  if (typeof props.data === 'string') return `"${props.data}"`
  return String(props.data)
})

const valueClass = computed(() => {
  if (props.data === null || props.data === undefined) return 'text-on-surface-variant'
  if (typeof props.data === 'string') return 'text-green-600'
  if (typeof props.data === 'number') return 'text-blue-600'
  if (typeof props.data === 'boolean') return 'text-purple-600'
  return 'text-on-surface'
})

function emitSelect() {
  const val = isExpandable.value ? JSON.stringify(props.data) : String(props.data === null ? 'null' : props.data)
  emit('select', fullPath.value, val)
}
</script>
