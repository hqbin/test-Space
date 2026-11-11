<template>
  <div class="flex flex-col gap-1 min-w-0 flex-1">
    <div class="flex flex-wrap items-center gap-1.5">
      <select :value="type" class="glass-input px-1.5 py-1 rounded-md text-[11px] shrink-0 w-[112px]"
        @change="onTypeChange(($event.target as HTMLSelectElement).value as LandingUiType)">
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
    <span v-if="type === 'custom'" class="text-[10px] text-amber-700">{{ t('backend.clickRawNotice') }}</span>
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
  LANDING_CUSTOM_OPTION,
  LANDING_OPTIONS,
  LANDING_SAMPLES,
  parseLanding,
  type LandingOption,
  type LandingUiType,
} from '@/constants/adPresets'

defineOptions({ name: 'LandingInput' })

const props = withDefaults(defineProps<{ modelValue: string }>(), { modelValue: '' })
const emit = defineEmits<{ (e: 'update:modelValue', v: string): void }>()

const { t, lang } = useI18n()

const type = ref<LandingUiType>('none')
const url = ref('')
const pkg = ref('')
const raw = ref(false)
const draft = ref(props.modelValue || '')

/** 「原文」档只在真遇到时出现在下拉里，不干扰新建广告的预设选择 */
const options = computed(() =>
  type.value === 'custom' ? [LANDING_CUSTOM_OPTION, ...LANDING_OPTIONS] : LANDING_OPTIONS)

const needPkg = computed(() => landingOption(type.value).needPkg)
const needUrl = computed(() => landingOption(type.value).needUrl)

/** 内部生成的值，避免 watch 回灌造成死循环 */
let lastEmitted = props.modelValue || ''

function resetToNone() {
  type.value = 'none'
  url.value = ''
  pkg.value = ''
  raw.value = false
}

watch(() => props.modelValue, (v) => {
  const next = v || ''
  if (next === lastEmitted) { draft.value = next; return }
  lastEmitted = next
  draft.value = next
  if (!next.trim()) { resetToNone(); return }
  const parsed = parseLanding(next)
  if (parsed && parsed.type !== 'custom') {
    type.value = parsed.type
    url.value = parsed.url
    pkg.value = parsed.pkg
    raw.value = false
    return
  }
  // 后台有值但不是预设结构（纯链接 / 其它 JSON）：保留原文，绝不能显示成「无跳转」
  type.value = 'custom'
  url.value = ''
  pkg.value = ''
  raw.value = true
}, { immediate: true })

function commit(v: string) {
  lastEmitted = v
  draft.value = v
  emit('update:modelValue', v)
}

function rebuild() {
  if (type.value === 'custom') return
  commit(buildLanding(type.value, url.value, pkg.value))
}

/** 所有预设示例值：用来判断输入框里还是不是「没改过的示例」 */
const PRESET_URLS = new Set(
  [...LANDING_OPTIONS.map((o) => o.sampleUrl || ''), ...Object.values(LANDING_SAMPLES).map((s) => s.url || '')]
    .map((v) => v.trim())
    .filter(Boolean),
)
const PRESET_PKGS = new Set(
  [...LANDING_OPTIONS.map((o) => o.samplePkg || ''), ...Object.values(LANDING_SAMPLES).map((s) => s.pkg || '')]
    .map((v) => v.trim())
    .filter(Boolean),
)

/** 空值或仍是某个预设示例 → 可以安全地换成新类型的示例 */
function untouched(value: string, presets: Set<string>) {
  const v = value.trim()
  return !v || presets.has(v)
}

/**
 * 取某个类型的示例值。
 * 三级兜底（选项自带 → 示例表 → 旧版单字段 sample），保证任何情况下「选了类型」都有值，
 * 不会出现五个预设全是空框。
 */
function sampleOf(opt: LandingOption) {
  const base = LANDING_SAMPLES[opt.key as string] || {}
  const legacy = String((opt as any).sample || '').trim()
  const urlOnly = opt.needPkg && !opt.needUrl // 「应用」这一档的旧版 sample 是包名
  return {
    url: (opt.sampleUrl || base.url || (urlOnly ? '' : legacy)).trim(),
    pkg: (opt.samplePkg || base.pkg || (urlOnly ? legacy : '')).trim(),
  }
}

function onTypeChange(v: LandingUiType) {
  type.value = v
  if (v === 'custom') {
    raw.value = true
    return
  }
  const opt = landingOption(v)
  const sample = sampleOf(opt)
  // 每种类型带自己的示例：切换时整体换掉，避免「换成网址了还是 mp4 那条」；
  // 用户手动改过的值（不是预设示例）保持不动，编辑老广告不会被示例覆盖。
  if (opt.needUrl && untouched(url.value, PRESET_URLS) && sample.url) url.value = sample.url
  if (opt.needPkg && untouched(pkg.value, PRESET_PKGS) && sample.pkg) pkg.value = sample.pkg
  raw.value = false
  rebuild()
}
function onUrl(v: string) { url.value = v; rebuild() }
function onPkg(v: string) { pkg.value = v; rebuild() }
function onRaw(v: string) { commit(v) }
function toggleRaw() {
  if (raw.value) {
    const parsed = parseLanding(draft.value)
    if (parsed && parsed.type !== 'custom') {
      raw.value = false
      type.value = parsed.type
      url.value = parsed.url
      pkg.value = parsed.pkg
      return
    }
    if (!draft.value.trim()) { resetToNone(); return }
    // 认不出来就继续留在原文模式，避免把已有配置覆盖成空
    type.value = 'custom'
    return
  }
  raw.value = true
}
</script>
