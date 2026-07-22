import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { PerfSnapshot } from '@/composables/usePerfMonitor'

export interface SnapshotPoint {
  time: number
  cpu: number
  memUsedKb: number
  memTotalKb: number
  memAvailKb: number
  zramKb: number
  swapFreeKb: number
  storageUsedKb: number
  storageTotalKb: number
  // Extended memory distribution
  memCachedKb: number
  memBuffersKb: number
  memSlabKb: number
  memKernelStackKb: number
  memPageTablesKb: number
  // Network IO (cumulative bytes)
  netRxBytes: number
  netTxBytes: number
  // PSI pressure (avg10 only, sufficient for trend analysis)
  pressureMemSomeAvg10: number
  pressureMemFullAvg10: number
  pressureIoSomeAvg10: number
  pressureIoFullAvg10: number
  pressureCpuSomeAvg10: number
  pressureCpuFullAvg10: number
  // Device info
  deviceUptimeSecs: number
}

export interface DumpsysPssPoint {
  time: number
  usedRamPssKb: number
  usedRamKernelKb: number
  processes: { name: string; pssKb: number }[]
}

export interface WatermarkPoint {
  time: number
  nrFreePagesKb: number
  minKb: number
  lowKb: number
  highKb: number
}

export interface DmesgSegment {
  time: number
  text: string
}

export const usePerfMonitorStore = defineStore('perfMonitor', () => {
  const isCollecting = ref(false)
  const intervalMs = ref(2000)
  const history = ref<SnapshotPoint[]>([])
  // 86400 points = 24h at 1s, 48h at 2s, 5 days at 5s, 10 days at 10s.
  // In-memory buffer is only for real-time chart display.
  // ALL data is streamed to CSV files for long-term persistence (supports months of runtime).
  const maxPoints = 86400
  const trimThreshold = Math.floor(maxPoints * 1.1)
  const latestSnapshot = ref<PerfSnapshot | null>(null)
  const processPssHistory = ref<Map<string, { time: number; pssKb: number }[]>>(new Map())
  const processCpuHistory = ref<Map<string, { time: number; cpuPercent: number }[]>>(new Map())
  const maxTrackedProcs = 30
  const topAppCount = ref(20)
  const cpuTopNCount = ref(20)
  const singleAppName = ref('')

  // dumpsys meminfo PSS tracking (separate from ps-based PSS)
  const dumpsysPssHistory = ref<DumpsysPssPoint[]>([])
  // Watermark history for chart
  const watermarkHistory = ref<WatermarkPoint[]>([])
  // Dmesg streaming buffer (last ~200 lines)
  const dmesgBuffer = ref<DmesgSegment[]>([])
  const dmesgTotalLines = ref(0)
  // ANR / Tombstone tracking
  const knownAnrFiles = ref<string[]>([])
  const knownTombstoneFiles = ref<string[]>([])
  const newAnrFiles = ref<string[]>([])
  const newTombstoneFiles = ref<string[]>([])

  const currentCpu = computed(() => latestSnapshot.value?.cpu_total ?? 0)
  const currentMemUsedKb = computed(() => latestSnapshot.value ? (latestSnapshot.value.mem_total_kb - latestSnapshot.value.mem_free_kb) : 0)
  const currentMemTotalKb = computed(() => latestSnapshot.value?.mem_total_kb ?? 0)
  const currentZramKb = computed(() => latestSnapshot.value?.zram_total_kb ?? 0)
  const currentStorageUsedKb = computed(() => latestSnapshot.value?.storage_used_kb ?? 0)
  const currentStorageTotalKb = computed(() => latestSnapshot.value?.storage_total_kb ?? 0)

  function addPoint(snapshot: PerfSnapshot) {
    const point: SnapshotPoint = {
      time: Date.now(),
      cpu: snapshot.cpu_total,
      memUsedKb: snapshot.mem_total_kb - snapshot.mem_free_kb,
      memTotalKb: snapshot.mem_total_kb,
      memAvailKb: snapshot.mem_avail_kb,
      zramKb: snapshot.zram_total_kb,
      swapFreeKb: snapshot.swap_free_kb,
      storageUsedKb: snapshot.storage_used_kb,
      storageTotalKb: snapshot.storage_total_kb,
      memCachedKb: snapshot.mem_cached_kb,
      memBuffersKb: snapshot.mem_buffers_kb,
      memSlabKb: snapshot.mem_slab_kb,
      memKernelStackKb: snapshot.mem_kernel_stack_kb,
      memPageTablesKb: snapshot.mem_page_tables_kb,
      pressureMemSomeAvg10: snapshot.pressure_mem_some_avg10,
      pressureMemFullAvg10: snapshot.pressure_mem_full_avg10,
      pressureIoSomeAvg10: snapshot.pressure_io_some_avg10,
      pressureIoFullAvg10: snapshot.pressure_io_full_avg10,
      netRxBytes: snapshot.net_rx_bytes,
      netTxBytes: snapshot.net_tx_bytes,
      pressureCpuSomeAvg10: snapshot.pressure_cpu_some_avg10,
      pressureCpuFullAvg10: snapshot.pressure_cpu_full_avg10,
      deviceUptimeSecs: snapshot.device_uptime_secs,
    }
    history.value.push(point)
    if (history.value.length > trimThreshold) {
      history.value = history.value.slice(-maxPoints)
    }
    latestSnapshot.value = snapshot

    for (const p of snapshot.procs) {
      if (!processPssHistory.value.has(p.name)) {
        processPssHistory.value.set(p.name, [])
      }
      const pssArr = processPssHistory.value.get(p.name)!
      pssArr.push({ time: Date.now(), pssKb: p.pss_kb })
      if (pssArr.length > trimThreshold) {
        pssArr.splice(0, pssArr.length - maxPoints)
      }

      if (!processCpuHistory.value.has(p.name)) {
        processCpuHistory.value.set(p.name, [])
      }
      const cpuArr = processCpuHistory.value.get(p.name)!
      cpuArr.push({ time: Date.now(), cpuPercent: p.cpu_percent })
      if (cpuArr.length > trimThreshold) {
        cpuArr.splice(0, cpuArr.length - maxPoints)
      }
    }

    // Ensure singleAppName is tracked: try exact match, then prefix match
    if (singleAppName.value) {
      // Find exact match
      let singleProc = snapshot.procs.find(p => p.name === singleAppName.value)
      // Try prefix match (e.g. user enters "com.app", actual proc is "com.app:service")
      if (!singleProc) {
        singleProc = snapshot.procs.find(p => p.name.startsWith(singleAppName.value + ':') || p.name === singleAppName.value)
      }
      // Try partial match (user enters partial name)
      if (!singleProc) {
        singleProc = snapshot.procs.find(p => p.name.includes(singleAppName.value))
      }
      if (singleProc) {
        // Update singleAppName to actual process name
        if (singleAppName.value !== singleProc.name) {
          singleAppName.value = singleProc.name
        }
        if (!processPssHistory.value.has(singleProc.name)) {
          processPssHistory.value.set(singleProc.name, [{ time: Date.now(), pssKb: singleProc.pss_kb }])
        }
        if (!processCpuHistory.value.has(singleProc.name)) {
          processCpuHistory.value.set(singleProc.name, [{ time: Date.now(), cpuPercent: singleProc.cpu_percent }])
        }
      }
    }

    // Prune processes no longer in snapshot to prevent unbounded Map growth
    const currentNames = new Set(snapshot.procs.map(p => p.name))
    if (singleAppName.value) currentNames.add(singleAppName.value)
    for (const key of processPssHistory.value.keys()) {
      if (!currentNames.has(key)) {
        processPssHistory.value.delete(key)
      }
    }
    for (const key of processCpuHistory.value.keys()) {
      if (!currentNames.has(key)) {
        processCpuHistory.value.delete(key)
      }
    }

    return null
  }

  function clearHistory() {
    history.value = []
    latestSnapshot.value = null
    processPssHistory.value.clear()
    processCpuHistory.value.clear()
    dumpsysPssHistory.value = []
    watermarkHistory.value = []
    dmesgBuffer.value = []
    dmesgTotalLines.value = 0
    knownAnrFiles.value = []
    knownTombstoneFiles.value = []
    newAnrFiles.value = []
    newTombstoneFiles.value = []
  }

  function setCollecting(v: boolean) {
    isCollecting.value = v
  }

  function setInterval(ms: number) {
    intervalMs.value = ms
  }

  function restoreHistory(pts: SnapshotPoint[]) {
    history.value = pts
  }

  // Restore full session: history points + per-process history + single app name
  function addDumpsysPssPoint(data: { usedRamPssKb: number; usedRamKernelKb: number; processes: { name: string; pssKb: number }[] }) {
    const top20 = [...data.processes].sort((a, b) => b.pssKb - a.pssKb).slice(0, 20)
    dumpsysPssHistory.value.push({
      time: Date.now(),
      usedRamPssKb: data.usedRamPssKb,
      usedRamKernelKb: data.usedRamKernelKb,
      processes: top20,
    })
    if (dumpsysPssHistory.value.length > maxPoints) {
      dumpsysPssHistory.value = dumpsysPssHistory.value.slice(-maxPoints)
    }
  }

  function addWatermarkPoint(data: { nrFreePagesKb: number; minKb: number; lowKb: number; highKb: number }) {
    watermarkHistory.value.push({
      time: Date.now(),
      nrFreePagesKb: data.nrFreePagesKb,
      minKb: data.minKb,
      lowKb: data.lowKb,
      highKb: data.highKb,
    })
    if (watermarkHistory.value.length > maxPoints / 30) {
      watermarkHistory.value = watermarkHistory.value.slice(-maxPoints / 30)
    }
  }

  function addDmesgLines(lines: string[]) {
    const now = Date.now()
    for (const text of lines) {
      dmesgBuffer.value.push({ time: now, text })
    }
    // Keep only last 500 lines for display
    if (dmesgBuffer.value.length > 500) {
      dmesgBuffer.value = dmesgBuffer.value.slice(-500)
    }
  }

  function setAnrTombstoneFound(anr: string[], ts: string[]) {
    if (anr.length > 0) {
      newAnrFiles.value = [...newAnrFiles.value, ...anr.filter(f => !newAnrFiles.value.includes(f))]
      knownAnrFiles.value = [...knownAnrFiles.value, ...anr]
    }
    if (ts.length > 0) {
      newTombstoneFiles.value = [...newTombstoneFiles.value, ...ts.filter(f => !newTombstoneFiles.value.includes(f))]
      knownTombstoneFiles.value = [...knownTombstoneFiles.value, ...ts]
    }
  }

  function restoreFullSession(data: {
    history: SnapshotPoint[]
    processPssHistory?: [string, { time: number; pssKb: number }[]][]
    processCpuHistory?: [string, { time: number; cpuPercent: number }[]][]
    singleAppName?: string
    topAppCount?: number
    cpuTopNCount?: number
  }) {
    history.value = data.history
    processPssHistory.value = new Map(data.processPssHistory ?? [])
    processCpuHistory.value = new Map(data.processCpuHistory ?? [])
    if (data.singleAppName !== undefined) singleAppName.value = data.singleAppName
    if (data.topAppCount !== undefined) topAppCount.value = data.topAppCount
    if (data.cpuTopNCount !== undefined) cpuTopNCount.value = data.cpuTopNCount
  }

  return {
    isCollecting, intervalMs, history, maxPoints, latestSnapshot,
    processPssHistory, processCpuHistory, topAppCount, cpuTopNCount, singleAppName,
    currentCpu, currentMemUsedKb, currentMemTotalKb,
    currentZramKb, currentStorageUsedKb, currentStorageTotalKb,
    dumpsysPssHistory, watermarkHistory, dmesgBuffer, dmesgTotalLines,
    knownAnrFiles, knownTombstoneFiles, newAnrFiles, newTombstoneFiles,
    addPoint, addDumpsysPssPoint, addWatermarkPoint, addDmesgLines, setAnrTombstoneFound,
    clearHistory, setCollecting, setInterval,
    restoreHistory, restoreFullSession,
  }
})
