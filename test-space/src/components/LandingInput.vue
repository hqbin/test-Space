<template>
  <div class="flex flex-col gap-1 min-w-0 flex-1">
    <div class="flex flex-wrap items-center gap-1.5">
      <select :value="type" class="glass-input px-1.5 py-1 rounded-md text-[11px] shrink-0 w-[112px]"
        @change="onTypeChange(($event.target as HTMLSelectElement).value as LandingType)">
        <option v-for="o in options" :key="o.key" :value="o.key">{{ lang === 'en' ? o.en : o.zh }}</option>
      </select>
      <input v-if="needPkg" :value="pkg" class="glass-input px-2 py-1 rounded-md text-[10px] font-mono w-[150px] shrink-0 select-text"
        :placeholder="t('backend.clickPkg')" @input="onPkg(($event.target as HTMLInputElement).value)" />
      <input v-if="needUrl" :value="url" class="glass-input px-2 py-1 rounded-md text-[10px] font-mono flex-1 min-w-0 select-text"
        :placeholder="t('backend.clickUrlPlaceholder')" @input="onUrl(($event.target as HTMLInputElement).value)" />
      <button type="button" class="text-[10px] shrink-0 px-1.5 py-0.5 rounded-md border border-hairline/70 text-on-surface-variant hover:text-secondary"
        :title="t('backend.clickRaw')" @click="toggleRaw">
        {{ raw ? 'JSON ✎' : 'JSON' }}
      </button>
    </div>
    <textarea v-if="raw" :value="draft" rows="2"
      class="glass-input px-2 py-1 rounded-md text-[10px] font-mono select-text resize-y"
      :placeholder="t('backend.clickUrlPlaceholder')" @input="onRaw(($event.target as HTMLTextAreaElement).value)"></textarea>
    <div v-else-if="draft" class="text-[10px] font-mono text-graphite truncate" :title="draft">{{ draft }}</div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from '@/composables/useI18n'
import {
  buildLanding,
  landingOption,
  LANDING_OPTIONS,
  parseLanding,
  type LandingType,
} from '@/constants/adPresets'

defineOptions({ name: 'LandingInput' })

const props = withDefaults(defineProps<{ modelValue: string }>(), { modelValue: '' })
const emit = defineEmits<{ (e: 'update:modelValue', v: string): void }>()

const { t, lang } = useI18n()
const options = LANDING_OPTIONS

const type = ref<LandingType>('none')
const url = ref('')
const pkg = ref('')
const raw = ref(false)
const draft = ref(props.modelValue || '')

const needPkg = computed(() => landingOption(type.value).needPkg)
const needUrl = computed(() => landingOption(type.value).needUrl)

/** 内部生成的值，避免 watch 回灌造成死循环 */
let lastEmitted = props.modelValue || ''

watch(() => props.modelValue, (v) => {
  const next = v || ''
  if (next === lastEmitted) { draft.value = next; return }
  lastEmitted = next
  draft.value = next
  if (!next) {
    type.value = 'none'
    url.value = ''
    pkg.value = ''
    raw.value = false
    return
  }
  const parsed = parseLanding(next)
  if (parsed) {
    type.value = parsed.type
    url.value = parsed.url
    pkg.value = parsed.pkg
    raw.value = false
  } else if (next) {
    // 无法识别成预设结构，直接按 JSON 原文编辑
    raw.value = true
  }
}, { immediate: true })

function commit(v: string) {
  lastEmitted = v
  draft.value = v
  emit('update:modelValue', v)
}

function rebuild() {
  commit(buildLanding(type.value, url.value, pkg.value))
}

function onTypeChange(v: LandingType) {
  type.value = v
  const opt = landingOption(v)
  if (opt.sample) {
    if (opt.needUrl && !url.value) url.value = opt.sample
    if (opt.needPkg && !pkg.value) pkg.value = opt.sample
  }
  rebuild()
}
function onUrl(v: string) { url.value = v; rebuild() }
function onPkg(v: string) { pkg.value = v; rebuild() }
function onRaw(v: string) { commit(v) }
function toggleRaw() {
  raw.value = !raw.value
  if (!raw.value) {
    const parsed = parseLanding(draft.value)
    if (parsed) { type.value = parsed.type; url.value = parsed.url; pkg.value = parsed.pkg }
  }
}
</script>
