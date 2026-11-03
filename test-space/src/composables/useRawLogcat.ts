import { ref, onUnmounted, type Ref } from 'vue'
import { invoke } from '@tauri-apps/api/core'

const MAX_LINES = 8000
const HISTORY_KEY = 'rawlogcat_search_history'
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
  try {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(history.slice(0, MAX_HISTORY)))
  } catch {}
}

export function removeSearchHistory(query: string) {
  const history = getSearchHistory().filter(h => h !== query)
  try { localStorage.setItem(HISTORY_KEY, JSON.stringify(history)) } catch {}
}

export function clearSearchHistory() {
  try { localStorage.removeItem(HISTORY_KEY) } catch {}
}

// ── Composable ──

export function useRawLogcat(serial: Ref<string | null | undefined>) {
  const status = ref<LogcatStatus>('idle')
  const lines = ref<RawLogLine[]>([])
  const bookmarkedIds = ref<Set<number>>(new Set())

  let pollTimer: number | null = null
  let lineIdCounter = 0
  let lastTimestamp = ''
  let isPolling = false
  let clearGen = 0  // 每次 clear 递增，让飞行中的旧 poll 结果失效

  function parseAndAppend(output: string, gen: number) {
    // 如果 clear 在飞行中被调用过，这批结果作废
    if (gen !== clearGen) return

    const rawLines = output.split('\n')
    const parsed: RawLogLine[] = []

    for (const raw of rawLines) {
      const trimmed = raw.trim()
      if (!trimmed || trimmed.startsWith('-----')) continue
      const line = parseLine(trimmed, ++lineIdCounter)
      if (line) parsed.push(line)
    }

    if (parsed.length === 0) return

    const last = parsed[parsed.length - 1]
    if (last) lastTimestamp = `${last.date} ${last.time}`

    lines.value.push(...parsed)
    if (lines.value.length > MAX_LINES) {
      const evicted = lines.value.splice(0, lines.value.length - MAX_LINES)
      // 淘汰的行同步清掉书签，避免书签定位到不存在的行
      if (bookmarkedIds.value.size > 0) {
        const evictedIds = new Set(evicted.map(l => l.id))
        const cleaned = new Set([...bookmarkedIds.value].filter(id => !evictedIds.has(id)))
        if (cleaned.size !== bookmarkedIds.value.size) bookmarkedIds.value = cleaned
      }
    }
  }

  async function doPoll(isFirst: boolean) {
    if (!serial.value || status.value !== 'running') return
    if (isPolling && !isFirst) {
      if (status.value === 'running') pollTimer = window.setTimeout(() => doPoll(false), 300)
      return
    }
    isPolling = true
    const gen = clearGen
    try {
      let cmd: string
      if (isFirst) {
        // 首次只取最近 800 行，避免首屏卡顿
        cmd = 'logcat -d -v threadtime -b main,system,crash -t 800'
      } else if (lastTimestamp) {
        // 不加 -t 限制，取 lastTimestamp 之后的所有行，确保无遗漏
        cmd = `logcat -d -v threadtime -b main,system,crash -T "${lastTimestamp}"`
      } else {
        cmd = 'logcat -d -v threadtime -b main,system,crash -t 800'
      }
      const output = await invoke<string>('adb_shell', { serial: serial.value, command: cmd })
      parseAndAppend(output, gen)
    } catch { /* silent */ } finally {
      isPolling = false
    }
    // 只有当前 gen 仍有效时才继续调度，避免 clear 后旧 poll 链续活
    if (gen === clearGen && status.value === 'running') pollTimer = window.setTimeout(() => doPoll(false), 800)
  }

  function start() {
    if (!serial.value) return
    clearGen++
    lines.value = []
    bookmarkedIds.value = new Set()
    lineIdCounter = 0
    lastTimestamp = ''
    isPolling = false
    if (pollTimer !== null) { clearTimeout(pollTimer); pollTimer = null }
    status.value = 'running'
    doPoll(true)
  }

  function pause() {
    if (status.value !== 'running') return
    status.value = 'paused'
    if (pollTimer !== null) { clearTimeout(pollTimer); pollTimer = null }
  }

  function resume() {
    if (status.value !== 'paused') return
    status.value = 'running'
    doPoll(false)
  }

  function stop() {
    status.value = 'idle'
    if (pollTimer !== null) { clearTimeout(pollTimer); pollTimer = null }
  }

  function clear() {
    clearGen++
    isPolling = false
    lines.value = []
    bookmarkedIds.value = new Set()
    lineIdCounter = 0
    lastTimestamp = ''
  }

  // 清空后立即触发一次拉取，不等 800ms timer
  function refresh() {
    if (status.value !== 'running') return
    if (pollTimer !== null) { clearTimeout(pollTimer); pollTimer = null }
    doPoll(false)
  }

  function toggleBookmark(id: number) {
    const s = new Set(bookmarkedIds.value)
    if (s.has(id)) s.delete(id)
    else s.add(id)
    bookmarkedIds.value = s
  }

  onUnmounted(stop)

  return { status, lines, bookmarkedIds, start, pause, resume, stop, clear, refresh, toggleBookmark }
}
