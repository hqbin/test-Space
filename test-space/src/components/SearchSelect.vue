<template>
  <div class="relative min-w-0">
    <button ref="triggerEl" type="button"
      class="glass-input w-full px-2 py-1 rounded-md text-[11px] flex items-center gap-1 text-left"
      :class="disabled ? 'opacity-60 cursor-not-allowed' : 'cursor-pointer'"
      :disabled="disabled" :title="current ? current.label : placeholder" @click="toggle">
      <span class="truncate flex-1 select-none"
        :class="current ? 'text-on-surface' : 'text-on-surface-variant/70'">{{ current ? current.label : placeholder }}</span>
      <span v-if="current && clearable" class="material-symbols-outlined text-[13px] text-on-surface-variant shrink-0"
        @click.stop="clear">close</span>
      <span class="material-symbols-outlined text-[14px] text-on-surface-variant shrink-0">{{ open ? 'expand_less' : 'expand_more' }}</span>
    </button>

    <Teleport to="body">
      <div v-if="open" ref="panelEl" class="fixed glass-panel rounded-lg shadow-xl p-1.5 flex flex-col gap-1"
        :style="{ top: pos.top + 'px', left: pos.left + 'px', width: pos.width + 'px', zIndex: 90 }">
        <input ref="searchEl" v-model="query" type="text"
          class="glass-input px-2 py-1 rounded-md text-[11px] select-text shrink-0"
          :placeholder="searchPlaceholder" @keydown.enter.prevent="chooseFirst" @keydown.esc.prevent="close" />
        <div class="overflow-y-auto custom-scrollbar flex flex-col gap-0.5" style="max-height: 240px">
          <button v-for="o in filtered" :key="o.value" type="button"
            class="text-left px-2 py-1 rounded-md text-[11px] flex items-center gap-2 shrink-0"
            :class="o.value === modelValue ? 'glass-active font-semibold' : 'text-on-surface-variant glass-hover'"
            @click="choose(o)">
            <span class="truncate flex-1">{{ o.label }}</span>
            <span v-if="o.hint" class="text-[10px] opacity-60 shrink-0 font-mono">{{ o.hint }}</span>
          </button>
          <div v-if="!filtered.length" class="px-2 py-3 text-[11px] text-on-surface-variant text-center">
            {{ loading ? '…' : emptyText }}
          </div>
        </div>
        <div class="px-2 pb-0.5 text-[10px] text-on-surface-variant shrink-0">{{ filtered.length }} / {{ options.length }}</div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import type { SearchSelectOption } from '@/types/searchSelect'

defineOptions({ name: 'SearchSelect' })

const props = withDefaults(defineProps<{
  modelValue: string
  options: SearchSelectOption[]
  placeholder?: string
  searchPlaceholder?: string
  emptyText?: string
  disabled?: boolean
  loading?: boolean
  clearable?: boolean
}>(), {
  placeholder: '',
  searchPlaceholder: '搜索',
  emptyText: '暂无数据',
  disabled: false,
  loading: false,
  clearable: false,
})

const emit = defineEmits<{
  (e: 'update:modelValue', v: string): void
  (e: 'change', v: string): void
}>()

const triggerEl = ref<HTMLButtonElement | null>(null)
const panelEl = ref<HTMLElement | null>(null)
const searchEl = ref<HTMLInputElement | null>(null)
const open = ref(false)
const query = ref('')
const pos = reactive({ top: 0, left: 0, width: 220 })

const current = computed(() => props.options.find((o) => o.value === props.modelValue) || null)

const filtered = computed(() => {
  const q = query.value.trim().toLowerCase()
  if (!q) return props.options
  return props.options.filter((o) =>
    o.label.toLowerCase().includes(q)
    || o.value.toLowerCase().includes(q)
    || String(o.hint || '').toLowerCase().includes(q))
})

function updatePos() {
  const el = triggerEl.value
  if (!el) return
  const r = el.getBoundingClientRect()
  const width = Math.max(r.width, 200)
  const panelH = 300
  let top = r.bottom + 4
  if (top + panelH > window.innerHeight - 8) top = Math.max(8, r.top - 4 - panelH)
  let left = r.left
  if (left + width > window.innerWidth - 8) left = Math.max(8, window.innerWidth - 8 - width)
  pos.top = top
  pos.left = left
  pos.width = width
}

async function toggle() {
  if (props.disabled) return
  if (open.value) { close(); return }
  query.value = ''
  open.value = true
  updatePos()
  await nextTick()
  searchEl.value?.focus()
}

function close() {
  open.value = false
  query.value = ''
}

function choose(o: SearchSelectOption) {
  if (o.value !== props.modelValue) {
    emit('update:modelValue', o.value)
    emit('change', o.value)
  }
  close()
}

function clear() {
  emit('update:modelValue', '')
  emit('change', '')
}

function chooseFirst() {
  const first = filtered.value[0]
  if (first) choose(first)
}

function onDocDown(e: MouseEvent) {
  if (!open.value) return
  const target = e.target as Node | null
  if (!target) return
  if (triggerEl.value?.contains(target) || panelEl.value?.contains(target)) return
  close()
}

function onScrollOrResize() {
  if (open.value) updatePos()
}

onMounted(() => {
  document.addEventListener('mousedown', onDocDown, true)
  window.addEventListener('resize', onScrollOrResize)
  window.addEventListener('scroll', onScrollOrResize, true)
})

onBeforeUnmount(() => {
  document.removeEventListener('mousedown', onDocDown, true)
  window.removeEventListener('resize', onScrollOrResize)
  window.removeEventListener('scroll', onScrollOrResize, true)
})
</script>
