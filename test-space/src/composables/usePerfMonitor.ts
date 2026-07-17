import { invoke } from "@tauri-apps/api/core"

export interface PerfSnapshot {
  cpu_total: number
  mem_total_kb: number
  mem_free_kb: number
  mem_avail_kb: number
  swap_total_kb: number
  swap_free_kb: number
  zram_total_kb: number
  storage_total_kb: number
  storage_used_kb: number
  storage_avail_kb: number
  procs: PerfProcess[]
}

export interface PerfProcess {
  pid: number
  name: string
  pss_kb: number
  cpu_percent: number
}

export function usePerfMonitor() {
  async function getSnapshot(serial: string, watchApp?: string): Promise<PerfSnapshot> {
    // Tauri v2 auto-converts camelCase (JS) → snake_case (Rust), so the key MUST be
    // `watchApp` here to match Rust's `watch_app` parameter. Using `watch_app` (snake_case)
    // in JS does NOT work — Tauri won't convert it and Rust receives None.
    return invoke<PerfSnapshot>("perf_get_snapshot", { serial, watchApp: watchApp ?? null })
  }

  return { getSnapshot }
}
