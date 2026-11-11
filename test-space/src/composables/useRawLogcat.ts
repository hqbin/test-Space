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
  /** 设备本地时间 MM-DD */
  deviceDate: string
  /** 设备本地时间 HH:MM:SS.mmm */
  deviceTime: string
  /** 设备时间对应的 epoch 毫秒（用于换算本机时间） */
  deviceTs: number
  /** 显示用的本机时间（epoch 毫秒）：写入时按当时的时钟偏移定标，之后不再变动 */
  hostTs: number
  pid: string
  tid: string
  level: LogLevel
  tag: string
  message: string
  raw: string
}

// threadtime format: "MM-DD HH:MM:SS.mmm  PID  TID LEVEL TAG: message"
const LINE_RE = /^(\d{2}-\d{2}) (\d{2}:\d{2}:\d{2}\.\d+)\s+(\d+)\s+(\d+)\s+([VDIWEF?])\s+(.+?):\s*(.*)$/

// threadtime 不带年份，按本机当前年补齐；年份误差会被 clockOffset 完全吸收，不影响本机时间换算
const LINE_YEAR = new Date().getFullYear()

function parseDeviceTs(date: string, time: string): number {
  const [mon, day] = date.split('-').map(Number)
  const [hms, frac = '0'] = time.split('.')
  const [h, mi, s] = hms.split(':').map(Number)
  const ms = Number(frac.padEnd(3, '0').slice(0, 3))
  return new Date(LINE_YEAR, mon - 1, day, h, mi, s, ms).getTime()
}

function parseLine(raw: string, id: number, clockOffset: number): RawLogLine | null {
  const m = raw.match(LINE_RE)
  if (!m) return null
  const deviceTs = parseDeviceTs(m[1], m[2])
  return {
    id,
    deviceDate: m[1], deviceTime: m[2],
    deviceTs,
    hostTs: deviceTs + clockOffset,
    pid: m[3], tid: m[4],
    level: m[5] as LogLevel,
    tag: m[6].trim(),
    message: m[7],
    raw,
  }
}

const pad2 = (n: number) => String(n).padStart(2, '0')

/** epoch 毫秒 → MM-DD / HH:MM:SS.mmm */
export function formatStamp(ts: number): { date: string; time: string } {
  const d = new Date(ts)
  return {
    date: `${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}`,
    time: `${pad2(d.getHours())}:${pad2(d.getMinutes())}:${pad2(d.getSeconds())}.${String(d.getMilliseconds()).padStart(3, '0')}`,
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

  // ── 时钟校准 ──
  // 本机时间 = 设备时间 + clockOffset。设备时钟快慢 / 时区差异全被这个偏移吸收。
  // 行一旦写入就冻结自己的 hostTs：改设备时钟、暂停补发、批次延迟都不会让已显示的
  // 时间回跳——只有「尚未追平实时」期间才会回填一次（见 settle）。
  let clockOffset = 0
  let clockSynced = false   // 是否已拿到第一次校准样本
  let settled = false       // 是否已追上实时（追平前允许回填已有行）
  let pendingOffset: number | null = null  // 设备时钟被调慢时的待确认偏移
  let pendingFromIdx = 0    // 待确认窗口内起始行下标，确认后回填这几行
  let prevNewestDeviceTs = 0
  let prevNow = 0

  /** 用当前偏移重算第 idx 行起的 hostTs（只用于「刚写入、还没被人看」的窗口） */
  function rebaseFrom(idx: number) {
    const from = Math.max(0, idx)
    for (let i = from; i < _linesRaw.length; i++) {
      const l = _linesRaw[i]
      l.hostTs = l.deviceTs + clockOffset
    }
    _tick.value++
  }

  function syncClock(newestDeviceTs: number, batchStartIdx: number) {
    const now = Date.now()
    const candidate = now - newestDeviceTs          // 该批最新一行对应的偏移候选
    const lag = candidate - clockOffset             // >0：这行是「过去」的（投递延迟 / 积压补发）
    const deltaDevice = prevNewestDeviceTs ? newestDeviceTs - prevNewestDeviceTs : Infinity
    const deltaHost = prevNow ? now - prevNow : Infinity
    prevNewestDeviceTs = newestDeviceTs
    prevNow = now

    if (!clockSynced) {
      // 首批数据可能来自开机积压，先取样本，追平后再定标
      clockOffset = candidate
      clockSynced = true
      return
    }

    if (!settled) {
      // 追平阶段：积压日志的设备时间较旧，candidate 偏大，取最小值逼近真实差值
      if (candidate < clockOffset - 50) clockOffset = candidate
      // 设备时间不再比本机跑得更快 → 积压已追平实时，定标并回填此前用旧偏移算过的行
      if (deltaDevice <= deltaHost * 2 + 200) {
        settled = true
        rebaseFrom(0)
      }
      return
    }

    // ── 定标后：正常情况 lag 只会略大于 0（投递延迟） ──
    // 设备时钟被调快 → 新行时间戳跑到未来，lag 变负，立即跟随
    if (lag < -2000) {
      clockOffset = candidate
      pendingOffset = null
      rebaseFrom(batchStartIdx)
      return
    }
    // 设备时钟被调慢 → lag 大幅变正；连续两批一致才认，排除暂停补发这类一次性旧数据
    if (lag > 30000) {
      if (pendingOffset !== null && Math.abs(candidate - pendingOffset) < 2000) {
        clockOffset = candidate
        pendingOffset = null
        rebaseFrom(pendingFromIdx)
      } else {
        pendingOffset = candidate
        pendingFromIdx = batchStartIdx
      }
      return
    }
    pendingOffset = null
  }

  /** 新会话重新校准（清空后设备日志从头来，偏移要重新取） */
  function resetClock() {
    clockOffset = 0
    clockSynced = false
    settled = false
    pendingOffset = null
    pendingFromIdx = 0
    prevNewestDeviceTs = 0
    prevNow = 0
  }

  function appendLines(rawLines: string[], gen: number) {
    if (gen !== clearGen) return
    let hasNew = false
    let newestDeviceTs = 0
    const batchStartIdx = _linesRaw.length
    for (const raw of rawLines) {
      const trimmed = raw.trim()
      if (!trimmed || trimmed.startsWith('-----')) continue
      const line = parseLine(trimmed, ++lineIdCounter, clockOffset)
      if (!line) continue
      if (line.deviceTs > newestDeviceTs) newestDeviceTs = line.deviceTs
      _linesRaw.push(line)
      hasNew = true
    }
    if (!hasNew) return
    syncClock(newestDeviceTs, batchStartIdx)
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
    resetClock()
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
    resetClock()
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
