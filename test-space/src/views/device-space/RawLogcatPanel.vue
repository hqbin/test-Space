<template>
  <div class="flex flex-col h-full min-h-0 overflow-hidden">

    <!-- 日志区 -->
    <div class="glass-panel rounded-xl flex flex-col flex-1 min-h-0 overflow-hidden">

      <!-- 列表头 -->
      <div class="grid select-none shrink-0 border-b border-outline-variant/15 px-2 py-1"
        style="grid-template-columns: 28px 90px 52px 52px 20px 130px 1fr">
        <div></div>
        <span class="font-caption text-[9px] text-on-surface-variant/40 font-semibold" title="本机当前时间，悬停行可查看设备时间">时间</span>
        <span class="font-caption text-[9px] text-on-surface-variant/40 font-semibold">PID</span>
        <span class="font-caption text-[9px] text-on-surface-variant/40 font-semibold">TID</span>
        <span class="font-caption text-[9px] text-on-surface-variant/40 font-semibold">L</span>
        <span class="font-caption text-[9px] text-on-surface-variant/40 font-semibold">Tag</span>
        <span class="font-caption text-[9px] text-on-surface-variant/40 font-semibold">Message</span>
      </div>

      <!-- 空态 -->
      <div v-if="filteredLines.length === 0"
        class="flex-1 flex flex-col items-center justify-center text-on-surface-variant/30 gap-2 select-none">
        <span class="material-symbols-outlined text-[36px] opacity-30">
          {{ status === 'running' ? 'hourglass_empty' : 'terminal' }}
        </span>
        <span class="font-caption text-[11px]">
          {{ !serial ? '请先连接设备' : status === 'idle' ? '点击「开始分析」捕获日志' : '等待日志…' }}
        </span>
      </div>

      <!-- 虚拟滚动外层：relative 基准锁定可视区，悬浮按钮不随内容滚动 -->
      <div v-else class="flex-1 min-h-0 relative">
        <div
          ref="scrollContainerRef"
          class="h-full overflow-y-auto custom-scrollbar"
          @scroll="onScroll">

          <div :style="{ height: filteredLines.length * ROW_H + 'px', position: 'relative' }">
            <div :style="{ position: 'absolute', top: visibleStart * ROW_H + 'px', left: 0, right: 0 }">
            <div v-for="item in visibleItems" :key="item.id"
              class="group flex items-center gap-1 px-2 border-b border-outline-variant/5 hover:bg-white/10 transition-colors cursor-pointer"
              :class="[
                levelRowBg(item.level),
                bookmarkedIds.has(item.id) ? 'bg-secondary/8' : '',
                currentMatchId === item.id ? '!bg-yellow-200/70 ring-1 ring-yellow-400/60 ring-inset' : '',
              ]"
              :style="{ height: ROW_H + 'px' }"
              @click="openLineModal(item)">

              <!-- 书签 -->
              <div class="w-5 flex items-center justify-center shrink-0">
                <button
                  class="opacity-0 group-hover:opacity-100 transition-opacity"
                  :class="bookmarkedIds.has(item.id) ? '!opacity-100' : ''"
                  @click.stop="toggleBookmark(item.id)">
                  <span class="material-symbols-outlined text-[12px]"
                    :class="bookmarkedIds.has(item.id) ? 'text-secondary' : 'text-on-surface-variant/40'"
                    :style="{ fontVariationSettings: `'FILL' ${bookmarkedIds.has(item.id) ? 1 : 0}` }">bookmark</span>
                </button>
              </div>

              <span class="font-mono text-[10px] text-on-surface-variant/50 w-[90px] shrink-0 select-text whitespace-nowrap overflow-hidden"
                :title="`设备时间 ${item.deviceDate} ${item.deviceTime}`">
                {{ hostStamp(item) }}
              </span>
              <span class="font-mono text-[10px] text-on-surface-variant/40 w-[52px] shrink-0 select-text text-right pr-2 whitespace-nowrap overflow-hidden">{{ item.pid }}</span>
              <span class="font-mono text-[10px] text-on-surface-variant/40 w-[52px] shrink-0 select-text text-right pr-2 whitespace-nowrap overflow-hidden">{{ item.tid }}</span>
              <span class="font-mono text-[10px] font-bold w-5 shrink-0 text-center select-none" :class="levelTextClass(item.level)">{{ item.level }}</span>
              <span class="font-mono text-[10px] w-[130px] shrink-0 truncate select-text" :class="levelTextClass(item.level)" :title="item.tag">{{ item.tag }}</span>

              <span class="font-mono text-[11px] flex-1 min-w-0 truncate select-text flex items-center gap-1"
                :class="isHttpLine(item) ? 'text-secondary' : 'text-on-surface'"
                :title="item.message">
                <span v-if="isHttpLine(item)" class="text-[8px] font-semibold px-1 py-px rounded shrink-0 bg-secondary/15 text-secondary">HTTP</span>
                <template v-if="searchQuery && !regexError">
                  <template v-for="(seg, si) in highlight(item.message)" :key="si">
                    <mark v-if="seg.match" class="bg-yellow-300/60 text-on-surface rounded-sm px-px">{{ seg.text }}</mark>
                    <span v-else>{{ seg.text }}</span>
                  </template>
                </template>
                <template v-else>{{ item.message }}</template>
              </span>

              <button class="opacity-0 group-hover:opacity-100 transition-opacity shrink-0 glass-hover rounded p-0.5 ml-1"
                title="复制整行" @click.stop="copyLine(item.raw)">
                <span class="material-symbols-outlined text-[12px] text-on-surface-variant/50">content_copy</span>
              </button>
            </div>
          </div>
          </div>
        </div>

        <!-- 自动滚动浮动按钮：fixed 在外层 relative 容器右下角，不随内容滚动 -->
        <button v-if="!autoScroll"
          class="absolute bottom-3 right-4 glass-button rounded-full p-1.5 shadow-md select-none z-10"
          title="滚动到底部"
          @click="scrollToBottom">
          <span class="material-symbols-outlined text-[16px]">vertical_align_bottom</span>
        </button>
      </div>
    </div>

    <!-- 行详情弹窗 -->
    <Teleport to="body">
      <Transition name="fade">
        <div v-if="toastVisible"
          class="fixed bottom-8 left-1/2 -translate-x-1/2 z-[9999] glass-panel rounded-full px-5 py-2.5 flex items-center gap-2 select-none pointer-events-none">
          <span class="material-symbols-outlined text-[18px]"
            :class="toastOk ? 'text-success-indicator' : 'text-error'"
            :style="{ fontVariationSettings: `'FILL' 1` }">
            {{ toastOk ? 'check_circle' : 'error' }}
          </span>
          <span class="font-body-md text-body-md text-on-surface">{{ toastMsg }}</span>
        </div>
      </Transition>
    </Teleport>

    <!-- 行详情弹窗 -->
    <Teleport to="body">
      <Transition name="fade">
        <div v-if="lineModal" class="fixed inset-0 z-50 flex items-center justify-center" @click.self="lineModal = null">
          <div class="absolute inset-0 bg-black/30 backdrop-blur-sm"></div>
          <div class="glass-panel rounded-[2rem] p-5 w-full max-w-3xl relative z-10 bg-white/60 max-h-[80vh] flex flex-col">
            <div class="flex items-center gap-3 mb-3 shrink-0">
              <span class="font-mono text-[11px] px-2 py-0.5 rounded font-semibold shrink-0" :class="levelActiveClass(lineModal.level)">{{ lineModal.level }}</span>
              <span class="font-mono text-[12px] text-secondary font-semibold truncate flex-1 select-text">{{ lineModal.tag }}</span>
              <button class="glass-button p-1 rounded shrink-0 ml-1" @click="lineModal = null">
                <span class="material-symbols-outlined text-[18px]">close</span>
              </button>
            </div>
            <div class="flex-1 min-h-0 overflow-y-auto custom-scrollbar space-y-3">
              <!-- 时间：本机当前时间 + 设备时间 并列展示 -->
              <div class="flex items-center gap-x-5 gap-y-2 flex-wrap px-1">
                <span class="font-caption text-[10px] text-on-surface-variant/60 select-none">
                  当前时间
                  <span class="font-mono text-[11px] text-on-surface font-semibold select-text ml-1">{{ hostStamp(lineModal, true) }}</span>
                </span>
                <span class="font-caption text-[10px] text-on-surface-variant/60 select-none">
                  设备时间
                  <span class="font-mono text-[11px] text-on-surface-variant/80 select-text ml-1">{{ lineModal.deviceDate }} {{ lineModal.deviceTime }}</span>
                  <span v-if="clockOffsetLabel(lineModal)" class="text-[9px] text-on-surface-variant/40 ml-1">（{{ clockOffsetLabel(lineModal) }}）</span>
                </span>
                <span class="font-caption text-[10px] text-on-surface-variant/60 select-none">PID <span class="font-mono text-on-surface select-text">{{ lineModal.pid }}</span></span>
                <span class="font-caption text-[10px] text-on-surface-variant/60 select-none">TID <span class="font-mono text-on-surface select-text">{{ lineModal.tid }}</span></span>
              </div>
              <div class="bg-black/5 rounded-xl p-3">
                <div class="text-[10px] font-semibold text-on-surface-variant/60 mb-2 select-none">Message</div>
                <pre class="font-mono text-[11px] text-on-surface whitespace-pre-wrap break-all select-text leading-relaxed">{{ lineModal.message }}</pre>
              </div>
              <div class="bg-black/5 rounded-xl p-3">
                <div class="flex items-center justify-between mb-2">
                  <div class="text-[10px] font-semibold text-on-surface-variant/60 select-none">原始日志行</div>
                  <button class="glass-hover rounded px-2 py-0.5 flex items-center gap-1 select-none" @click="copyLine(lineModal.raw)">
                    <span class="material-symbols-outlined text-[12px]">content_copy</span>
                    <span class="text-[10px]">复制</span>
                  </button>
                </div>
                <pre class="font-mono text-[10px] text-on-surface-variant/80 whitespace-pre-wrap break-all select-text leading-relaxed">{{ lineModal.raw }}</pre>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { formatStamp, type LogLevel, type LogcatStatus, type RawLogLine } from '@/composables/useRawLogcat'

const props = defineProps<{
  serial: string | null | undefined
  fullscreen: boolean
  status: LogcatStatus
  filteredLines: RawLogLine[]
  bookmarkedIds: Set<number>
  searchQuery: string
  useRegex: boolean
  regexError: boolean
  active: boolean
}>()

const emit = defineEmits<{
  'update:fullscreen': [value: boolean]
  'toggleBookmark': [id: number]
}>()

const toggleBookmark = (id: number) => emit('toggleBookmark', id)

// ── 当前匹配行索引 ──
const currentMatchId = ref<number | null>(null)
const currentMatchCount = ref(-1)

// 仅搜索词变化时才重置，filteredLines 新增内容不重置（避免打断连续跳转）
watch(() => props.searchQuery, () => { currentMatchId.value = null; currentMatchCount.value = -1 })

// ── 虚拟滚动 ──
const ROW_H = 28
const OVERSCAN = 20
const scrollTop = ref(0)
const containerHeight = ref(600)
const scrollContainerRef = ref<HTMLElement | null>(null)
const autoScroll = ref(true)
let _scrollingToBottom = false  // 程序性滚动期间屏蔽 onScroll 的 autoScroll 判断

function onScroll(e: Event) {
  const el = e.target as HTMLElement
  scrollTop.value = el.scrollTop
  containerHeight.value = el.clientHeight
  // 程序性滚动期间只跳过 autoScroll 判断，scrollTop 仍需同步给虚拟滚动
  if (_scrollingToBottom) return
  const distFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight
  autoScroll.value = distFromBottom <= ROW_H * 3
}

let resizeObs: ResizeObserver | null = null
onMounted(() => {
  if (scrollContainerRef.value) {
    containerHeight.value = scrollContainerRef.value.clientHeight
    resizeObs = new ResizeObserver(() => {
      if (scrollContainerRef.value) containerHeight.value = scrollContainerRef.value.clientHeight
    })
    resizeObs.observe(scrollContainerRef.value)
  }
})
onUnmounted(() => { resizeObs?.disconnect() })

// 切换回来时同步重读 scrollTop + containerHeight，再按需滚到底部
// 避免 v-show 隐藏期间 clientHeight=0 导致虚拟滚动渲染区间为空
watch(() => props.active, (val) => {
  if (val) {
    nextTick(() => {
      const el = scrollContainerRef.value
      if (!el) return
      containerHeight.value = el.clientHeight
      scrollTop.value = el.scrollTop
      if (autoScroll.value) scrollToBottom()
    })
  }
})

const visibleStart = computed(() => Math.max(0, Math.floor(scrollTop.value / ROW_H) - OVERSCAN))
const visibleEnd = computed(() => Math.min(
  props.filteredLines.length,
  Math.ceil((scrollTop.value + containerHeight.value) / ROW_H) + OVERSCAN
))
const visibleItems = computed(() => props.filteredLines.slice(visibleStart.value, visibleEnd.value))

function scrollToBottom() {
  const el = scrollContainerRef.value
  if (!el) return
  _scrollingToBottom = true
  el.scrollTop = el.scrollHeight
  autoScroll.value = true
  // 等滚动事件结束后再解锁，requestAnimationFrame 确保在下一帧之后
  requestAnimationFrame(() => { _scrollingToBottom = false })
}

watch(() => props.filteredLines, async () => {
  if (!autoScroll.value) return
  await nextTick()
  scrollToBottom()
})

// ── 书签跳转（供父组件通过 expose 调用） ──
function jumpBookmark(dir: 1 | -1) {
  const el = scrollContainerRef.value
  if (!el) return
  const ids = Array.from(props.bookmarkedIds)
  const currentRowIdx = Math.floor(scrollTop.value / ROW_H)
  const allIdxs = props.filteredLines.map((l, i) => ids.includes(l.id) ? i : -1).filter(i => i >= 0)
  if (!allIdxs.length) return
  let target: number
  if (dir === 1) target = allIdxs.find(i => i > currentRowIdx) ?? allIdxs[0]
  else target = [...allIdxs].reverse().find(i => i < currentRowIdx) ?? allIdxs[allIdxs.length - 1]
  el.scrollTop = target * ROW_H - containerHeight.value / 2
}

// ── 搜索跳转（Enter 循环跳匹配行） ──
function jumpToMatch(dir: 1 | -1) {
  const el = scrollContainerRef.value
  if (!el || !props.searchQuery.trim()) return
  const q = props.searchQuery.trim()
  const re = props.useRegex
    ? (() => { try { return new RegExp(q, 'i') } catch { return null } })()
    : null
  const matchTest = (l: typeof props.filteredLines[0]) => {
    if (re) return re.test(l.message) || re.test(l.tag)
    const ql = q.toLowerCase()
    return l.message.toLowerCase().includes(ql) || l.tag.toLowerCase().includes(ql)
  }
  const matchIdxs = props.filteredLines.map((l, i) => matchTest(l) ? i : -1).filter(i => i >= 0)
  if (!matchIdxs.length) return

  // 先用 currentMatchId 重新定位计数器，防止新行进来后位置漂移
  if (currentMatchId.value !== null) {
    const syncIdx = props.filteredLines.findIndex(l => l.id === currentMatchId.value)
    const syncCount = matchIdxs.indexOf(syncIdx)
    if (syncCount >= 0) currentMatchCount.value = syncCount
  }

  let nextCount: number
  if (currentMatchCount.value < 0 || currentMatchCount.value >= matchIdxs.length) {
    nextCount = dir === 1 ? 0 : matchIdxs.length - 1
  } else {
    nextCount = (currentMatchCount.value + dir + matchIdxs.length) % matchIdxs.length
  }
  currentMatchCount.value = nextCount
  const target = matchIdxs[nextCount]
  el.scrollTop = target * ROW_H - containerHeight.value / 2
  currentMatchId.value = props.filteredLines[target]?.id ?? null
  autoScroll.value = false
}

// ── 导出（供父组件通过 expose 调用） ──
async function exportLog() {
  if (props.filteredLines.length === 0) {
    _toast('没有日志可导出', false)
    return
  }
  try {
    const { documentDir, join } = await import('@tauri-apps/api/path')
    const { mkdir, writeTextFile } = await import('@tauri-apps/plugin-fs')
    const { invoke } = await import('@tauri-apps/api/core')
    const docDir = await documentDir()
    const dir = await join(docDir, 'TestSpace', 'Logs')
    await mkdir(dir, { recursive: true })
    const now = new Date()
    const pad = (n: number) => String(n).padStart(2, '0')
    const ts = `${now.getFullYear()}${pad(now.getMonth()+1)}${pad(now.getDate())}_${pad(now.getHours())}${pad(now.getMinutes())}${pad(now.getSeconds())}`
    const filename = `logcat_${ts}.txt`
    const dest = await join(dir, filename)
    const content = props.filteredLines.map(l => l.raw).join('\n')
    await writeTextFile(dest, content)
    _toast(`已保存 ${filename}`, true)
    try { await invoke('open_path', { path: dir }) } catch {}
  } catch (e) {
    _toast(`导出失败: ${String(e)}`, false)
  }
}

// 简单 toast（不依赖父组件）
const toastMsg = ref('')
const toastOk = ref(true)
const toastVisible = ref(false)
let _toastTimer: number | null = null
function _toast(msg: string, ok: boolean) {
  toastMsg.value = msg; toastOk.value = ok; toastVisible.value = true
  if (_toastTimer) clearTimeout(_toastTimer)
  _toastTimer = window.setTimeout(() => { toastVisible.value = false }, 3000)
}

defineExpose({ jumpBookmark, jumpToMatch, exportLog })

// ── 时间显示：行内冻结的本机时间（设备时间 + 收到时的时钟偏移） ──
function hostStamp(line: RawLogLine, withMs = false): string {
  const h = formatStamp(line.hostTs)
  return `${h.date} ${withMs ? h.time : h.time.substring(0, 8)}`
}

// 该行设备时钟与本机的时差提示（≥1s 才显示，避免正常毫秒抖动打扰）
function clockOffsetLabel(line: RawLogLine): string {
  const offset = line.hostTs - line.deviceTs
  if (Math.abs(offset) < 1000) return ''
  const total = Math.round(Math.abs(offset) / 1000)
  const h = Math.floor(total / 3600)
  const m = Math.floor((total % 3600) / 60)
  const s = total % 60
  const parts: string[] = []
  if (h) parts.push(`${h}h`)
  if (m) parts.push(`${m}m`)
  if (!h && s) parts.push(`${s}s`)
  return `设备${offset > 0 ? '慢' : '快'} ${parts.join('')}`
}

// ── 行详情弹窗 ──
const lineModal = ref<RawLogLine | null>(null)
function openLineModal(item: RawLogLine) {
  lineModal.value = item
}

// ── 搜索高亮 ──
function highlight(text: string): Array<{ text: string; match: boolean }> {
  const q = props.searchQuery.trim()
  if (!q || props.regexError) return [{ text, match: false }]
  try {
    const re = props.useRegex ? new RegExp(q, 'gi') : new RegExp(q.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi')
    const result: Array<{ text: string; match: boolean }> = []
    let last = 0; let m: RegExpExecArray | null
    while ((m = re.exec(text)) !== null) {
      if (m.index > last) result.push({ text: text.slice(last, m.index), match: false })
      result.push({ text: m[0], match: true })
      last = re.lastIndex
      if (m[0].length === 0) break
    }
    if (last < text.length) result.push({ text: text.slice(last), match: false })
    return result.length ? result : [{ text, match: false }]
  } catch { return [{ text, match: false }] }
}

// ── 样式函数 ──
const HTTP_LINE_RE = /-->\s*(GET|POST|PUT|DELETE|PATCH)|<--\s*\d{3}|https?:\/\/\S+zeasn|WhaleTvHttpLogg|NetLogInterceptor|NetLog[12]/i
function isHttpLine(item: RawLogLine): boolean { return HTTP_LINE_RE.test(item.message) || HTTP_LINE_RE.test(item.tag) }

function levelTextClass(lv: LogLevel): string {
  const map: Record<LogLevel, string> = { V: 'text-on-surface-variant/40', D: 'text-secondary/70', I: 'text-green-700/80', W: 'text-yellow-600', E: 'text-error', F: 'text-purple-600', '?': 'text-on-surface-variant/40' }
  return map[lv] ?? 'text-on-surface-variant'
}
function levelRowBg(lv: LogLevel): string {
  if (lv === 'E') return 'border-l-2 border-error/30'
  if (lv === 'F') return 'border-l-2 border-purple-500/40'
  if (lv === 'W') return 'border-l-2 border-yellow-400/30'
  return ''
}
function levelActiveClass(lv: LogLevel): string {
  const map: Record<LogLevel, string> = { V: 'bg-on-surface-variant/20 text-on-surface-variant', D: 'bg-secondary/20 text-secondary', I: 'bg-success-indicator/20 text-green-700', W: 'bg-yellow-400/30 text-yellow-700', E: 'bg-error/20 text-error', F: 'bg-purple-500/20 text-purple-700', '?': 'bg-outline-variant/20 text-on-surface-variant' }
  return map[lv] ?? 'bg-outline-variant/20 text-on-surface-variant'
}

function copyLine(raw: string) { navigator.clipboard.writeText(raw).catch(() => {}) }
</script>
