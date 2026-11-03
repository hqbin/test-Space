import { ref, computed, onUnmounted, type Ref } from 'vue'
import { invoke } from '@tauri-apps/api/core'
import { listen, type UnlistenFn } from '@tauri-apps/api/event'

const MAX_LINES = 10000
const HISTORY_KEY = 'rawlogcat_search_history'
const TAG_HISTORY_KEY = 'rawlogcat_tag_history'
const MAX_HISTORY = 20

export type LogLevel = 'V' | 'D' | 'I' | 'W' | 'E' | 'F' | '?'
export type LogcatStatus = 'idle' | 'running' | 'paused'

export interface RawLogLine {
  id: number
  date: string
  time: string
  pid: string
  tid: string
  level: LogLevel
  tag: string
  message: string
  raw: string
}

// threadtime format: "MM-DD HH:MM:SS.mmm  PID  TID LEVEL TAG: message"
const LINE_RE = /^(\d{2}-\d{2}) (\d{2}:\d{2}:\d{2}\.\d+)\s+(\d+)\s+(\d+)\s+([VDIWEF?])\s+(.+?):\s*(.*)$/

function parseLine(raw: string, id: number): RawLogLine | null {
  const m = raw.match(LINE_RE)
  if (!m) return null
  return {
    id,
    date: m[1], time: m[2],
    pid: m[3], tid: m[4],
    level: m[5] as LogLevel,
    tag: m[6].trim(),
    message: m[7],
    raw,
  }
}

export const ALL_LEVELS: LogLevel[] = ['V', 'D', 'I', 'W', 'E', 'F']

export function getSearchHistory(): string[] {
  try {
    const raw = localStorage.getItem(HISTORY_KEY)
    return raw ? JSON.parse(raw) : []
  } catch { return [] }
}

export function addSearchHistory(query: string) {
  if (!query.trim()) return
  const history = getSearchHistory().filter(h => h !== query)
  history.unshift(query)
  try { localStorage.setItem(HISTORY_KEY, JSON.stringify(history.slice(0, MAX_HISTORY))) } catch {}
}

export function removeSearchHistory(query: string) {
  const history = getSearchHistory().filter(h => h !== query)
  try { localStorage.setItem(HISTORY_KEY, JSON.stringify(history)) } catch {}
}

export function clearSearchHistory() {
  try { localStorage.removeItem(HISTORY_KEY) } catch {}
}

export function getTagHistory(): string[] {
  try {
    const raw = localStorage.getItem(TAG_HISTORY_KEY)
    return raw ? JSON.parse(raw) : []
  } catch { return [] }
}

export function addTagHistory(query: string) {
  if (!query.trim()) return
  const history = getTagHistory().filter(h => h !== query)
  history.unshift(query)
  try { localStorage.setItem(TAG_HISTORY_KEY, JSON.stringify(history.slice(0, MAX_HISTORY))) } catch {}
}

export function removeTagHistory(query: string) {
  const history = getTagHistory().filter(h => h !== query)
  try { localStorage.setItem(TAG_HISTORY_KEY, JSON.stringify(history)) } catch {}
}

export function clearTagHistory() {
  try { localStorage.removeItem(TAG_HISTORY_KEY) } catch {}
}

// ── Composable ──

export function useRawLogcat(serial: Ref<string | null | undefined>) {
  const status = ref<LogcatStatus>('idle')
  // 内部裸数组，不进 Vue 响应式，直接 push/splice
  const _linesRaw: RawLogLine[] = []
  // 整数信号：每次有新数据就 +1，驱动 computed 重跑
  const _tick = ref(0)
  // 对外暴露：computed 依赖 _tick，每次返回浅拷贝（只复制指针）
  const lines = computed<RawLogLine[]>(() => { _tick.value; return _linesRaw.slice() })
  const bookmarkedIds = ref<Set<number>>(new Set())

  let lineIdCounter = 0
  let clearGen = 0
  let unlisten: UnlistenFn | null = null
  let pauseBuffer: string[] = []  // 暂停时缓存行，resume 后补入

  function appendLines(rawLines: string[], gen: number) {
    if (gen !== clearGen) return
    let hasNew = false
    for (const raw of rawLines) {
      const trimmed = raw.trim()
      if (!trimmed || trimmed.startsWith('-----')) continue
      const line = parseLine(trimmed, ++lineIdCounter)
      if (!line) continue
      _linesRaw.push(line)
      hasNew = true
    }
    if (!hasNew) return
    if (_linesRaw.length > MAX_LINES) {
      const evicted = _linesRaw.splice(0, _linesRaw.length - MAX_LINES)
      if (bookmarkedIds.value.size > 0) {
        const evictedIds = new Set(evicted.map(l => l.id))
        const cleaned = new Set([...bookmarkedIds.value].filter(id => !evictedIds.has(id)))
        if (cleaned.size !== bookmarkedIds.value.size) bookmarkedIds.value = cleaned
      }
    }
    _tick.value++
  }

  async function start() {
    if (!serial.value) return
    await stop()
    clearGen++
    const gen = clearGen
    _linesRaw.length = 0
    _tick.value++
    bookmarkedIds.value = new Set()
    lineIdCounter = 0
    pauseBuffer = []

    const eventName = `logcat://lines:${serial.value}`
    unlisten = await listen<{ serial: string; lines: string[] }>(eventName, (e) => {
      if (status.value === 'paused') {
        pauseBuffer.push(...e.payload.lines)
        return
      }
      appendLines(e.payload.lines, gen)
    })

    await invoke('logcat_stream_start', { serial: serial.value })
    status.value = 'running'
  }

  async function stop() {
    const s = serial.value
    status.value = 'idle'
    if (unlisten) { unlisten(); unlisten = null }
    pauseBuffer = []
    if (s) {
      try { await invoke('logcat_stream_stop', { serial: s }) } catch {}
    }
  }

  function pause() {
    if (status.value !== 'running') return
    status.value = 'paused'
  }

  function resume() {
    if (status.value !== 'paused') return
    status.value = 'running'
    if (pauseBuffer.length > 0) {
      appendLines(pauseBuffer, clearGen)
      pauseBuffer = []
    }
  }

  function clear() {
    clearGen++
    _linesRaw.length = 0
    pauseBuffer = []
    _tick.value++
    bookmarkedIds.value = new Set()
    lineIdCounter = 0
  }

  // 清空设备日志后重启流
  async function refresh() {
    if (!serial.value || status.value === 'idle') return
    const s = serial.value
    clear()
    if (unlisten) { unlisten(); unlisten = null }
    try { await invoke('logcat_stream_stop', { serial: s }) } catch {}
    const gen = clearGen
    const eventName = `logcat://lines:${s}`
    unlisten = await listen<{ serial: string; lines: string[] }>(eventName, (e) => {
      if (status.value === 'paused') { pauseBuffer.push(...e.payload.lines); return }
      appendLines(e.payload.lines, gen)
    })
    await invoke('logcat_stream_start', { serial: s })
  }

  function toggleBookmark(id: number) {
    const s = new Set(bookmarkedIds.value)
    if (s.has(id)) s.delete(id)
    else s.add(id)
    bookmarkedIds.value = s
  }

  onUnmounted(() => { stop() })

  return { status, lines, bookmarkedIds, start, pause, resume, stop, clear, refresh, toggleBookmark }
}
