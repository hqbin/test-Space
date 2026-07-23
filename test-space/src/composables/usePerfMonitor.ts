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
  // Extended memory distribution
  mem_cached_kb: number
  mem_buffers_kb: number
  mem_slab_kb: number
  mem_kernel_stack_kb: number
  mem_page_tables_kb: number
  // PSI pressure metrics (0 if kernel doesn't support PSI)
  pressure_mem_some_avg10: number
  pressure_mem_some_avg60: number
  pressure_mem_some_avg300: number
  pressure_mem_full_avg10: number
  pressure_mem_full_avg60: number
  pressure_mem_full_avg300: number
  pressure_io_some_avg10: number
  pressure_io_some_avg60: number
  pressure_io_some_avg300: number
  pressure_io_full_avg10: number
  pressure_io_full_avg60: number
  pressure_io_full_avg300: number
  pressure_cpu_some_avg10: number
  pressure_cpu_some_avg60: number
  pressure_cpu_some_avg300: number
  pressure_cpu_full_avg10: number
  pressure_cpu_full_avg60: number
  pressure_cpu_full_avg300: number
  // Network IO (cumulative bytes from /proc/net/dev)
  net_rx_bytes: number
  net_tx_bytes: number
  // Device info
  device_uptime_secs: number
  device_date: string
  kernel_version: string
}

export interface PerfProcess {
  pid: number
  name: string
  pss_kb: number
  cpu_percent: number
}

export interface WatermarkZone {
  name: string
  free_kb: number
  min_kb: number
  low_kb: number
  high_kb: number
  managed_kb: number
}
export interface WatermarkInfo {
  zones: WatermarkZone[]
  total_free_pages_kb: number
}

// dumpsys meminfo -S
export interface DumpsysMemInfo {
  total_ram_kb: number
  free_ram_kb: number
  used_ram_pss_kb: number
  used_ram_kernel_kb: number
  processes: PssProcess[]
}
export interface PssProcess {
  name: string
  pid: number
  pss_kb: number
}

// Incremental dmesg
export interface DmesgPollResult {
  new_lines: string[]
  total_lines: number
  last_line: string
}

// ANR / Tombstone
export interface AnrTombstoneResult {
  new_anr_files: string[]
  new_tombstone_files: string[]
}

export interface LogcatDiag {
  is_alive: boolean
  child_exit_code: number | null
  thread_alive: boolean
  exit_reason: string
}

export function usePerfMonitor() {
  async function getSnapshot(serial: string, watchApp?: string): Promise<PerfSnapshot> {
    return invoke<PerfSnapshot>("perf_get_snapshot", { serial, watchApp: watchApp ?? null })
  }

  async function getWatermark(serial: string): Promise<WatermarkInfo> {
    return invoke<WatermarkInfo>("adb_get_watermark", { serial })
  }

  async function getDumpsysMeminfo(serial: string): Promise<DumpsysMemInfo> {
    return invoke<DumpsysMemInfo>("adb_get_dumpsys_meminfo", { serial })
  }

  async function pollDmesg(serial: string, knownLines: number, knownLastLine: string): Promise<DmesgPollResult> {
    return invoke<DmesgPollResult>("adb_poll_dmesg", { serial, knownLines, knownLastLine })
  }

  async function logcatIsAlive(serial: string): Promise<boolean> {
    return invoke<boolean>("adb_logcat_is_alive", { serial })
  }

  async function logcatDiag(serial: string): Promise<LogcatDiag> {
    return invoke<LogcatDiag>("adb_logcat_diag", { serial })
  }

  async function checkAnrTombstones(serial: string, knownAnr: string[], knownTombstone: string[]): Promise<AnrTombstoneResult> {
    return invoke<AnrTombstoneResult>("adb_check_anr_tombstones", { serial, knownAnr, knownTombstone })
  }

  return { getSnapshot, getWatermark, getDumpsysMeminfo, pollDmesg, checkAnrTombstones, logcatIsAlive, logcatDiag }
}
