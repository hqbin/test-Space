<template>
  <div class="flex flex-col gap-1.5">
    <div class="flex flex-wrap items-center gap-2">
      <input v-model="query" class="glass-input px-2 py-0.5 rounded-md text-[10px] w-[168px] select-text"
        :placeholder="searchPlaceholder" />
      <button class="glass-button rounded-md px-2 py-0.5 text-[10px] disabled:opacity-40"
        :disabled="loading || !items.length" @click="toggleAll">
        {{ modelValue.length >= items.length && items.length ? clearLabel : allLabel }}
      </button>
      <button class="glass-button rounded-md px-2 py-0.5 text-[10px] disabled:opacity-40"
        :disabled="loading || !filtered.length" @click="selectFiltered">{{ selectFilteredLabel }}</button>
      <span v-if="hint" class="text-[10px] text-on-surface-variant truncate max-w-[220px]" :title="hint">{{ hint }}</span>
      <span class="ml-auto text-[10px] text-on-surface-variant tabular-nums">{{ modelValue.length }} / {{ items.length }}</span>
    </div>

    <div class="relative glass-panel rounded-lg overflow-hidden">
      <div class="p-2 grid gap-x-2 gap-y-1 max-h-[132px] overflow-y-auto custom-scrollbar"
        :class="columns === 2 ? 'grid-cols-2' : 'grid-cols-3'">
        <label v-for="it in filtered" :key="it.id"
          class="relative flex items-center gap-1.5 text-[10px] cursor-pointer select-none min-w-0 py-[1px]">
          <input type="checkbox" class="check-input" :checked="isChecked(it.id)" :disabled="loading"
            @change="toggleOne(it.id)" />
          <span class="check-box" :class="{ 'is-on': isChecked(it.id) }" aria-hidden="true">
            <svg v-if="isChecked(it.id)" viewBox="0 0 12 12" class="check-mark">
              <path d="M2.2 6.3 4.7 8.7 9.8 3.4" fill="none" stroke="currentColor" stroke-width="1.8"
                stroke-linecap="round" stroke-linejoin="round" />
            </svg>
          </span>
          <span class="truncate" :title="it.name">{{ it.name }}</span>
        </label>
        <div v-if="!filtered.length" class="col-span-3 text-[10px] text-on-surface-variant text-center py-3">
          {{ loading ? t('backend.loading') : (items.length ? t('backend.noMatch') : emptyText) }}
        </div>
      </div>
      <div v-if="loading" class="loading-veil">
        <span class="w-3 h-3 border-2 border-secondary border-t-transparent rounded-full animate-spin"></span>
        <span class="text-[10px] text-on-surface-variant">{{ t('backend.loading') }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from '@/composables/useI18n'
import type { CheckGridItem } from '@/types/backend'

defineOptions({ name: 'CheckGrid' })

const props = withDefaults(defineProps<{
  modelValue: string[]
  items: CheckGridItem[]
  loading?: boolean
  emptyText?: string
  searchPlaceholder?: string
  allLabel?: string
  clearLabel?: string
  selectFilteredLabel?: string
  hint?: string
  columns?: 2 | 3
}>(), {
  loading: false,
  emptyText: '',
  searchPlaceholder: '筛选',
  allLabel: '全选',
  clearLabel: '清空',
  selectFilteredLabel: '选中筛选结果',
  hint: '',
  columns: 3,
})

const emit = defineEmits<{ (e: 'update:modelValue', v: string[]): void }>()
const { t } = useI18n()

const query = ref('')

const filtered = computed(() => {
  const q = query.value.trim().toLowerCase()
  if (!q) return props.items
  return props.items.filter((it) => `${it.name} ${it.id}`.toLowerCase().includes(q))
})

function isChecked(id: string) {
  return props.modelValue.includes(id)
}

function toggleOne(id: string) {
  if (props.loading) return
  const set = new Set(props.modelValue)
  if (set.has(id)) set.delete(id)
  else set.add(id)
  emit('update:modelValue', Array.from(set))
}

function toggleAll() {
  if (props.modelValue.length >= props.items.length) emit('update:modelValue', [])
  else emit('update:modelValue', props.items.map((it) => it.id))
}

function selectFiltered() {
  const set = new Set(props.modelValue)
  filtered.value.forEach((it) => set.add(it.id))
  emit('update:modelValue', Array.from(set))
}
</script>
