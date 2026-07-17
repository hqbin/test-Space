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
  storageUsedKb: number
  storageTotalKb: number
}

export const usePerfMonitorStore = defineStore('perfMonitor', () => {
  const isCollecting = ref(false)
  const intervalMs = ref(2000)
  const history = ref<SnapshotPoint[]>([])
  // 86400 points = 24h at 1s, 48h at 2s, 5 days at 5s, 10 days at 10s, 30 days at 30s.
  // Process maps use the same cap to bound memory (~50 procs × 86400 × 32 bytes ≈ 138MB worst case).
  const maxPoints = 86400
  const latestSnapshot = ref<PerfSnapshot | null>(null)
  const processPssHistory = ref<Map<string, { time: number; pssKb: number }[]>>(new Map())
  const processCpuHistory = ref<Map<string, { time: number; cpuPercent: number }[]>>(new Map())
  const maxTrackedProcs = 30
  const topAppCount = ref(20)
  const cpuTopNCount = ref(20)
  const singleAppName = ref('')

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
      storageUsedKb: snapshot.storage_used_kb,
      storageTotalKb: snapshot.storage_total_kb,
    }
    history.value.push(point)
    if (history.value.length > maxPoints) {
      history.value.shift()
    }
    latestSnapshot.value = snapshot

    // Track ALL processes from snapshot (Rust already returns top 20-30)
    for (const p of snapshot.procs) {
      if (!processPssHistory.value.has(p.name)) {
        processPssHistory.value.set(p.name, [])
      }
      const pssArr = processPssHistory.value.get(p.name)!
      pssArr.push({ time: Date.now(), pssKb: p.pss_kb })
      if (pssArr.length > maxPoints) pssArr.shift()

      if (!processCpuHistory.value.has(p.name)) {
        processCpuHistory.value.set(p.name, [])
      }
      const cpuArr = processCpuHistory.value.get(p.name)!
      cpuArr.push({ time: Date.now(), cpuPercent: p.cpu_percent })
      if (cpuArr.length > maxPoints) cpuArr.shift()
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
    addPoint, clearHistory, setCollecting, setInterval,
    restoreHistory, restoreFullSession,
  }
})
