<template>
  <Teleport to="body">
    <div v-if="modelValue" class="fixed inset-0 z-50 bg-black/30 flex items-center justify-center p-6">
      <div class="solid-panel rounded-2xl w-[940px] max-h-[88vh] flex flex-col overflow-hidden">
        <!-- 头部 -->
        <div class="panel-bar px-4 py-2.5 flex items-center gap-2 border-b border-hairline/60 shrink-0">
          <span class="material-symbols-outlined text-[16px] text-secondary">tune</span>
          <span class="text-[13px] font-semibold">{{ t('backend.ceTitle') }}</span>
          <span class="text-[10px] text-on-surface-variant">{{ t('backend.ceHint') }}</span>
          <div class="ml-auto flex items-center gap-1.5">
            <button class="glass-button rounded-md px-2 py-0.5 text-[11px] flex items-center gap-1"
              @click="startNew()">
              <span class="material-symbols-outlined text-[13px]">add</span>{{ t('backend.ceNew') }}
            </button>
            <button class="material-symbols-outlined text-[15px] text-on-surface-variant hover:text-secondary"
              :title="t('backend.refresh')" :disabled="listBusy" @click="load(1)">refresh</button>
            <button class="glass-button rounded-md px-2 py-0.5 text-[11px]" @click="close">{{ t('backend.close') }}</button>
          </div>
        </div>

        <!-- 搜索 -->
        <div class="px-4 py-2 flex items-center gap-2 border-b border-hairline/60 shrink-0">
          <input v-model="query" class="glass-input px-2.5 py-1 rounded-md text-[11px] w-[260px] select-text"
            :placeholder="t('backend.ceSearchPlaceholder')" @keyup.enter="load(1)" />
          <button class="glass-button rounded-lg px-2.5 py-1 text-[11px] flex items-center gap-1"
            :disabled="listBusy" @click="load(1)">
            <span v-if="listBusy" class="w-3 h-3 border-2 border-secondary border-t-transparent rounded-full animate-spin"></span>
            <span v-else class="material-symbols-outlined text-[13px]">search</span>
            {{ t('backend.query') }}
          </button>
          <span class="text-[10px] text-on-surface-variant">{{ t('backend.ceTotal', { n: String(total) }) }}</span>
        </div>

        <!-- 列表 -->
        <div class="flex-1 min-h-0 overflow-y-auto custom-scrollbar relative">
          <div class="grid grid-cols-[50px_104px_124px_1fr_56px_68px] gap-2 px-4 py-1.5 text-[10px] font-semibold text-on-surface-variant border-b border-hairline/60 sticky top-0 panel-bar z-[1]">
            <span>ID</span>
            <span>{{ t('backend.ceKeycode') }}</span>
            <span>{{ t('backend.ceName') }}</span>
            <span>{{ t('backend.ceValue') }}</span>
            <span class="text-center" :title="t('backend.ceRefsHint')">{{ t('backend.ceRefs') }}</span>
            <span class="text-right">{{ t('backend.operation') }}</span>
          </div>
          <div v-for="k in records" :key="k.id"
            class="grid grid-cols-[50px_104px_124px_1fr_56px_68px] gap-2 px-4 py-1.5 text-[11px] items-center border-b border-hairline/40 hover:bg-secondary/5">
            <span class="font-mono text-graphite tabular-nums">#{{ k.id }}</span>
            <span class="font-mono text-[10px] text-on-surface-variant truncate" :title="k.keycode">{{ k.keycode }}</span>
            <div class="min-w-0 flex flex-col gap-[1px]">
              <span class="truncate text-on-surface" :title="k.valuetext">{{ k.valuetext || '-' }}</span>
              <span v-if="opText(k)" class="text-[9px] text-on-surface-variant truncate">{{ opText(k) }}</span>
            </div>
            <div class="min-w-0 flex items-start gap-1.5">
              <span v-if="isMac(k)" class="text-[9px] px-1 py-[1px] rounded bg-tertiary/10 text-tertiary shrink-0 mt-[1px]">MAC</span>
              <span class="font-mono text-[10px] text-graphite leading-[1.4] break-all line-clamp-2"
                :title="valueText(k)">{{ valueText(k) || '-' }}</span>
            </div>
            <span class="text-center text-[10px] tabular-nums" :title="t('backend.ceRefsHint')"
              :class="Number(k.order_count) ? 'text-secondary font-semibold' : 'text-on-surface-variant'">
              {{ Number(k.order_count) || 0 }}
            </span>
            <span class="flex items-center justify-end gap-1">
              <button class="icon-action" :title="t('backend.edit')" @click="startEdit(k)">
                <span class="material-symbols-outlined text-[14px]">edit</span>
              </button>
              <button class="icon-action is-danger" :title="t('backend.delete')" @click="askDelete(k)">
                <span class="material-symbols-outlined text-[14px]">delete</span>
              </button>
            </span>
          </div>
          <div v-if="!records.length && !listBusy" class="py-10 text-center text-[12px] text-on-surface-variant">
            {{ t('backend.noData') }}
          </div>
          <div v-if="listBusy" class="loading-veil">
            <span class="w-3.5 h-3.5 border-2 border-secondary border-t-transparent rounded-full animate-spin"></span>
            <span class="text-[11px] text-on-surface-variant">{{ t('backend.loading') }}</span>
          </div>
        </div>

        <!-- 分页 -->
        <div class="panel-bar flex items-center justify-end gap-2 px-4 py-1.5 border-t border-hairline/60 text-[11px] shrink-0">
          <button class="glass-button rounded-md px-2 py-0.5" :disabled="page <= 1 || listBusy" @click="load(page - 1)">
            {{ t('backend.prev') }}
          </button>
          <span class="tabular-nums">{{ page }} / {{ maxPage }}</span>
          <button class="glass-button rounded-md px-2 py-0.5" :disabled="page >= maxPage || listBusy" @click="load(page + 1)">
            {{ t('backend.next') }}
          </button>
        </div>

        <!-- 编辑 / 新建 -->
        <div v-if="formOpen" class="border-t border-hairline/60 px-4 py-2.5 flex flex-col gap-2 shrink-0 panel-bar">
          <div class="flex items-center gap-2">
            <span class="material-symbols-outlined text-[14px] text-secondary">{{ form.id ? 'edit' : 'add_box' }}</span>
            <span class="text-[12px] font-semibold">{{ form.id ? t('backend.ceEdit') : t('backend.ceNew') }}</span>
            <span v-if="form.id" class="text-[10px] font-mono text-on-surface-variant">#{{ form.id }}</span>
            <span class="ml-auto text-[10px] text-on-surface-variant">{{ t('backend.ceFormHint') }}</span>
          </div>
          <div class="grid grid-cols-[92px_1fr_92px_1fr] gap-x-2 gap-y-1.5 items-center">
            <span class="text-[10px] text-on-surface-variant">{{ t('backend.ruleKeycode') }}</span>
            <input v-model="form.keycode" class="glass-input px-2 py-1 rounded-md text-[11px] font-mono select-text"
              :placeholder="t('backend.ceKeycodePlaceholder')" />
            <span class="text-[10px] text-on-surface-variant">{{ t('backend.ruleValueText') }}</span>
            <input v-model="form.valuetext" class="glass-input px-2 py-1 rounded-md text-[11px] select-text"
              :placeholder="t('backend.ruleValueTextPlaceholder')" />

            <span class="text-[10px] text-on-surface-variant">{{ t('backend.ruleKeytext') }}</span>
            <input v-model="form.keytext" class="glass-input px-2 py-1 rounded-md text-[11px] select-text"
              :placeholder="t('backend.ceKeytextPlaceholder')" />
            <span class="text-[10px] text-on-surface-variant">{{ t('backend.ruleType') }}</span>
            <select v-model="form.keywordtype" class="glass-input px-2 py-1 rounded-md text-[11px]">
              <option value="2">{{ t('backend.ruleTypeString') }}</option>
              <option value="1">{{ t('backend.ruleTypeNumber') }}</option>
            </select>

            <span class="text-[10px] text-on-surface-variant self-start pt-1">{{ t('backend.ruleValue') }}</span>
            <textarea v-model="form.valuecode" rows="2"
              class="glass-input px-2 py-1 rounded-md text-[11px] font-mono select-text resize-y"
              :placeholder="t('backend.ceValuePlaceholder')"></textarea>
            <span class="text-[10px] text-on-surface-variant self-start pt-1">{{ t('backend.ruleMatchMode') }}</span>
            <select v-model="form.keywordop" class="glass-input px-2 py-1 rounded-md text-[11px] self-start">
              <option v-for="o in opOptions" :key="o.v" :value="o.v">{{ o.t }}</option>
            </select>
          </div>
          <div class="flex items-center gap-2">
            <span v-if="formError" class="text-[10px] text-error truncate max-w-[420px]">{{ formError }}</span>
            <button class="ml-auto glass-button rounded-md px-2.5 py-0.5 text-[11px]" @click="formOpen = false">
              {{ t('backend.cancel') }}
            </button>
            <button class="glass-button rounded-md px-2.5 py-0.5 text-[11px] font-semibold flex items-center gap-1"
              :disabled="formBusy" @click="submit">
              <span v-if="formBusy" class="w-3 h-3 border-2 border-secondary border-t-transparent rounded-full animate-spin"></span>
              {{ t('backend.save') }}
            </button>
          </div>
        </div>

        <!-- 删除确认 -->
        <div v-if="deleteTarget" class="border-t border-hairline/60 px-4 py-2 flex items-center gap-2 text-[11px] shrink-0">
          <span class="material-symbols-outlined text-[14px] text-error">warning</span>
          <span class="truncate">{{ t('backend.ceDeleteConfirm', { id: String(deleteTarget.id), name: deleteTarget.valuetext || valueText(deleteTarget) }) }}</span>
          <button class="ml-auto glass-button rounded-md px-2 py-0.5 text-[11px] text-error/80 flex items-center gap-1"
            :disabled="deleteBusy" @click="doDelete">
            <span v-if="deleteBusy" class="w-3 h-3 border-2 border-error border-t-transparent rounded-full animate-spin"></span>
            {{ t('backend.delete') }}
          </button>
          <button class="glass-button rounded-md px-2 py-0.5 text-[11px]" @click="deleteTarget = null">{{ t('backend.cancel') }}</button>
        </div>

        <div v-if="toast" class="px-4 py-1 text-[10px]" :class="toastOk ? 'text-success-indicator' : 'text-error'">{{ toast }}</div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { useI18n } from '@/composables/useI18n'
import {
  deleteKeyword,
  listKeywords,
  listOrders,
  saveKeyword,
  searchEngineRules,
  type SspKeyword,
} from '@/services/sspApi'

defineOptions({ name: 'CustomEngineDialog' })

const props = withDefaults(defineProps<{
  modelValue: boolean
  /** 打开时预填的规则值（例如左侧 MAC 查询输入） */
  seedValue?: string
}>(), { seedValue: '' })

const emit = defineEmits<{
  (e: 'update:modelValue', v: boolean): void
  /** 规则被改 / 删，调用方需要重新对齐已选规则的文字 */
  (e: 'changed'): void
  /** 保存成功：带回保存后的规则（平台不回吐 id 时可能为 null），供调用方自动挂到广告上 */
  (e: 'saved', k: SspKeyword | null): void
}>()

const { t } = useI18n()

const pageSize = 50
const records = ref<SspKeyword[]>([])
const total = ref(0)
const page = ref(1)
const listBusy = ref(false)
const query = ref('')
const toast = ref('')
const toastOk = ref(true)
let toastTimer: number | null = null

const maxPage = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))

function showToast(text: string, ok = true) {
  toast.value = text
  toastOk.value = ok
  if (toastTimer) window.clearTimeout(toastTimer)
  toastTimer = window.setTimeout(() => { toast.value = '' }, 3000)
}

let reqSeq = 0
async function load(nextPage = page.value) {
  const seq = ++reqSeq
  listBusy.value = true
  try {
    const q = query.value.trim()
    if (q) {
      // 搜索态：平台单参数覆盖不全（value 只匹配规则值、name 只匹配标签说明），
      // 走 searchEngineRules 并上全量本地模糊匹配，MAC / 参数名 / 规则名称都能命中
      const hits = await searchEngineRules(q, pageSize)
      if (seq !== reqSeq) return
      records.value = hits
      total.value = hits.length
      page.value = 1
      return
    }
    const res = await listKeywords({ page: nextPage, pagesize: pageSize })
    if (seq !== reqSeq) return
    records.value = res.records
    total.value = res.total
    page.value = nextPage
  } catch (e) {
    if (seq === reqSeq) showToast(e instanceof Error ? e.message : String(e), false)
  } finally {
    if (seq === reqSeq) listBusy.value = false
  }
}

let seedCache = ''

watch(() => props.modelValue, (open) => {
  if (open) {
    query.value = ''
    formOpen.value = false
    deleteTarget.value = null
    seedCache = props.seedValue.trim()
    void load(1)
  }
})

function close() {
  emit('update:modelValue', false)
}

// ── 值展示 ──────────────────────────────────────────
function valueText(k: SspKeyword) {
  const vc = k.valuecode
  const raw = Array.isArray(vc) ? vc.join(', ') : String(vc || '')
  return raw || '-'
}

function isMac(k: SspKeyword) {
  return /mac/i.test(String(k.keycode || '')) || /^([0-9A-F]{2}[:-]){5}/i.test(valueText(k))
}

const OP_MAP: Record<string, string> = {
  '1': 'Equal', '2': 'No equal', '3': 'Less than', '4': 'Greater than',
  '5': 'Include', '6': 'Exclusive', '7': 'No parameter', '8': 'Regex match', '9': 'Regex not match',
}

function opText(k: SspKeyword) {
  const op = OP_MAP[String(k.keywordop ?? '')]
  const type = String(k.keywordtype ?? '')
  if (!op) return ''
  return type ? `${op} · ${type === '1' ? t('backend.ruleTypeNumber') : t('backend.ruleTypeString')}` : op
}

// ── 编辑表单 ────────────────────────────────────────
const formOpen = ref(false)
const formBusy = ref(false)
const formError = ref('')
const form = reactive({
  id: '',
  keycode: 'devicemac',
  keytext: 'devicemac',
  valuecode: '',
  valuetext: '',
  keywordtype: '2',
  keywordop: '1',
})

const opOptions = computed(() => {
  if (form.keywordtype === '1') {
    return [
      { v: '1', t: 'Equal' }, { v: '2', t: 'No equal' }, { v: '3', t: 'Less than' },
      { v: '4', t: 'Greater than' }, { v: '7', t: 'No parameter' },
    ]
  }
  return Object.entries(OP_MAP).map(([v, t2]) => ({ v, t: t2 }))
})

watch(() => form.keywordtype, (type, old) => {
  if (old && type !== old) {
    const opts = opOptions.value
    if (!opts.some((o) => o.v === form.keywordop)) form.keywordop = opts[0]?.v || '1'
  }
})

function startNew(seed = seedCache) {
  form.id = ''
  form.keycode = 'devicemac'
  form.keytext = 'devicemac'
  form.valuecode = seed ? normalizeMac(seed) : ''
  form.valuetext = ''
  form.keywordtype = '2'
  form.keywordop = '1'
  formError.value = ''
  formOpen.value = true
  deleteTarget.value = null
}

function startEdit(k: SspKeyword) {
  form.id = String(k.id)
  form.keycode = String(k.keycode || '')
  form.keytext = String(k.keytext || '')
  form.valuecode = Array.isArray(k.valuecode) ? k.valuecode.join(',') : String(k.valuecode || '')
  form.valuetext = String(k.valuetext || '')
  form.keywordtype = String(k.keywordtype || '2')
  form.keywordop = String(k.keywordop || '1')
  formError.value = ''
  formOpen.value = true
  deleteTarget.value = null
}

function normalizeMac(raw: string) {
  return String(raw || '')
    .replace(/[，、;；\s]+/g, ',')
    .replace(/,+/g, ',')
    .replace(/^,|,$/g, '')
}

async function submit() {
  formError.value = ''
  if (!form.keycode.trim()) { formError.value = t('backend.ruleKeycode') + ' ' + t('backend.required'); return }
  if (!form.keytext.trim()) { formError.value = t('backend.ruleKeytext') + ' ' + t('backend.required'); return }
  if (!form.valuecode.trim()) { formError.value = t('backend.ruleValue') + ' ' + t('backend.required'); return }
  if (!form.valuetext.trim()) { formError.value = t('backend.ruleValueText') + ' ' + t('backend.required'); return }
  formBusy.value = true
  try {
    const saved = await saveKeyword({
      id: form.id || 0,
      keycode: form.keycode,
      keytext: form.keytext,
      valuecode: form.valuecode,
      valuetext: form.valuetext,
      keywordtype: form.keywordtype,
      keywordop: form.keywordop,
    })
    formOpen.value = false
    showToast(t('backend.ceSaved'), true)
    // 先通知调用方刷新已选规则的文字，再把这条规则交给它（编辑器里会自动挂到当前广告）
    emit('changed')
    emit('saved', saved)
    await load(page.value)
  } catch (e) {
    formError.value = e instanceof Error ? e.message : String(e)
  } finally {
    formBusy.value = false
  }
}

// ── 删除 ────────────────────────────────────────────
const deleteTarget = ref<SspKeyword | null>(null)
const deleteBusy = ref(false)

function askDelete(k: SspKeyword) {
  deleteTarget.value = k
  formOpen.value = false
}

async function doDelete() {
  const target = deleteTarget.value
  if (!target) return
  deleteBusy.value = true
  try {
    await deleteKeyword(String(target.id))
    deleteTarget.value = null
    showToast(t('backend.ceDeleted'), true)
    emit('changed')
    await load(page.value)
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e)
    if (/being used this tags/i.test(msg)) {
      // 平台按「引用广告数」拦截删除。先查出真实引用，给用户可操作的清单；
      // 查不到时说明后台计数没回退（广告删掉了但 order_count 不减少）。
      let names: string[] = []
      try {
        const res = await listOrders({ target_keyword: String(target.id), page: 1, pagesize: 5 })
        names = (res.records || []).map((o) => `#${o.id} ${o.name}`)
      } catch { /* 忽略查询失败 */ }
      showToast(
        names.length
          ? t('backend.ceDeleteInUse', { n: String(names.length), list: names.join('、') })
          : t('backend.ceDeleteCountStale', { n: String(Number(target.order_count) || 0) }),
        false,
      )
    } else {
      showToast(msg, false)
    }
  } finally {
    deleteBusy.value = false
  }
}
</script>
