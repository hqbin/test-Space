<template>
  <div class="flex flex-col gap-4 flex-1 min-h-0 overflow-hidden select-none">
    <!-- Header -->
    <div class="glass-panel rounded-xl p-3 px-5 flex items-center gap-3 flex-wrap shrink-0">
      <button class="glass-button px-3 py-1.5 rounded-lg font-label-md text-label-md" @click="goBack">
        返回
      </button>
      <div class="h-5 w-[1px] bg-glass-border-dark"></div>
      <button class="glass-button px-3 py-1.5 rounded-lg font-label-md text-label-md flex items-center gap-1" @click="toggleCollect" :disabled="!deviceSerial">
        <span class="material-symbols-outlined text-[16px]">{{ store.isCollecting ? 'pause' : 'play_arrow' }}</span>
        {{ store.isCollecting ? '暂停' : '开始' }}
      </button>
      <div class="flex items-center gap-2">
        <div class="w-2 h-2 rounded-full" :class="store.isCollecting ? 'bg-success-indicator animate-pulse' : 'bg-outline-variant'"></div>
        <span class="font-caption text-caption text-on-surface-variant">{{ store.isCollecting ? t('perf.collecting') : t('perf.idle') }}</span>
      </div>
      <div class="flex items-center gap-2">
        <span class="font-caption text-caption text-on-surface-variant">{{ t('perf.interval') }}:</span>
        <div class="relative" ref="intervalDropdownRef">
          <button class="glass-hover rounded-xl px-3 py-1.5 text-body-md flex items-center gap-2 select-none min-w-[72px]"
            @click="toggleIntervalDropdown">
            <span class="flex-1 text-left">{{ intervalOptions.find(o => String(o.value) === intervalMs)?.label || intervalMs + 'ms' }}</span>
            <span class="material-symbols-outlined text-[16px] transition-transform" :class="intervalDropdownOpen ? 'rotate-180' : ''">expand_more</span>
          </button>
        </div>
      </div>
      <Teleport to="body">
        <Transition name="fade-scale">
          <div v-if="intervalDropdownOpen" class="fixed z-[9999]" :style="intervalDropdownStyle" @click.stop>
            <div class="glass-panel rounded-2xl py-1 shadow-xl" style="min-width:120px">
              <div v-for="opt in intervalOptions" :key="opt.value"
                class="flex items-center gap-2 rounded-xl px-3 py-1.5 cursor-pointer select-none mx-1"
                :class="intervalMs === String(opt.value) ? 'bg-white/20 font-medium' : 'hover:bg-white/10'"
                @click.stop="selectInterval(opt.value)">
                <span class="material-symbols-outlined text-[14px] text-on-surface-variant shrink-0" :class="intervalMs === String(opt.value) ? 'visible' : 'invisible'">check</span>
                <span class="text-body-md">{{ opt.label }}</span>
              </div>
            </div>
          </div>
        </Transition>
      </Teleport>
      <Teleport to="body">
        <Transition name="fade-scale">
          <div v-if="topNDropdownOpen" class="fixed z-[9999]" :style="topNDropdownStyle" @click.stop>
            <div class="glass-panel rounded-2xl py-1 shadow-xl" style="min-width:100px">
              <div v-for="n in topNOptions" :key="n"
                class="flex items-center gap-2 rounded-xl px-3 py-1.5 cursor-pointer select-none mx-1"
                :class="store.topAppCount === n ? 'bg-white/20 font-medium' : 'hover:bg-white/10'"
                @click.stop="selectTopN(n)">
                <span class="material-symbols-outlined text-[14px] text-on-surface-variant shrink-0" :class="store.topAppCount === n ? 'visible' : 'invisible'">check</span>
                <span class="text-body-md">{{ n }}</span>
              </div>
            </div>
          </div>
        </Transition>
        <Transition name="fade-scale">
          <div v-if="cpuDropdownOpen" class="fixed z-[9999]" :style="cpuDropdownStyle" @click.stop>
            <div class="glass-panel rounded-2xl py-1 shadow-xl" style="min-width:100px">
              <div v-for="n in topNOptions" :key="n"
                class="flex items-center gap-2 rounded-xl px-3 py-1.5 cursor-pointer select-none mx-1"
                :class="store.cpuTopNCount === n ? 'bg-white/20 font-medium' : 'hover:bg-white/10'"
                @click.stop="selectCpuTopN(n)">
                <span class="material-symbols-outlined text-[14px] text-on-surface-variant shrink-0" :class="store.cpuTopNCount === n ? 'visible' : 'invisible'">check</span>
                <span class="text-body-md">{{ n }}</span>
              </div>
            </div>
          </div>
        </Transition>
      </Teleport>
      <!-- CPU app filter dropdown -->
      <Teleport to="body">
        <Transition name="fade-scale">
          <div v-if="cpuFilterOpen" class="fixed z-[9999]" :style="cpuFilterStyle" @click.stop>
            <div class="glass-panel rounded-2xl py-1 shadow-xl" style="min-width:240px; max-height:60vh; overflow-y:auto" ref="cpuFilterPanelRef">
              <div class="flex items-center justify-between px-3 py-1.5 border-b border-outline-variant/30 mx-1 sticky top-0 bg-white/80 backdrop-blur-sm rounded-xl">
                <span class="font-label-sm text-label-sm">应用筛选 ({{ cpuAppNames.length }})</span>
                <div class="flex items-center gap-2">
                  <button class="text-caption text-secondary hover:underline" @click.stop="cpuSelectAll">全选</button>
                  <button class="text-caption text-on-surface-variant hover:underline" @click.stop="cpuSelectNone">全不选</button>
                </div>
              </div>
              <div v-if="cpuAppNames.length === 0" class="px-3 py-3 text-center text-caption text-on-surface-variant">暂无数据</div>
              <div v-for="name in cpuAppNames" :key="name"
                class="flex items-center gap-2 rounded-xl px-3 py-1.5 cursor-pointer select-none mx-1 hover:bg-white/10"
                @click.stop="toggleCpuApp(name)">
                <span class="material-symbols-outlined text-[14px] shrink-0" :class="cpuHiddenApps.has(name) ? 'text-on-surface-variant/30' : 'text-secondary'">{{ cpuHiddenApps.has(name) ? 'check_box_outline_blank' : 'check_box' }}</span>
                <span class="text-body-sm break-all" :class="cpuHiddenApps.has(name) ? 'line-through text-on-surface-variant/50' : ''">{{ name }}</span>
              </div>
            </div>
          </div>
        </Transition>
      </Teleport>
      <!-- Top app filter dropdown -->
      <Teleport to="body">
        <Transition name="fade-scale">
          <div v-if="topAppFilterOpen" class="fixed z-[9999]" :style="topAppFilterStyle" @click.stop>
            <div class="glass-panel rounded-2xl py-1 shadow-xl" style="min-width:240px; max-height:60vh; overflow-y:auto" ref="topAppFilterPanelRef">
              <div class="flex items-center justify-between px-3 py-1.5 border-b border-outline-variant/30 mx-1 sticky top-0 bg-white/80 backdrop-blur-sm rounded-xl">
                <span class="font-label-sm text-label-sm">应用筛选 ({{ topAppNames.length }})</span>
                <div class="flex items-center gap-2">
                  <button class="text-caption text-secondary hover:underline" @click.stop="topAppSelectAll">全选</button>
                  <button class="text-caption text-on-surface-variant hover:underline" @click.stop="topAppSelectNone">全不选</button>
                </div>
              </div>
              <div v-if="topAppNames.length === 0" class="px-3 py-3 text-center text-caption text-on-surface-variant">暂无数据</div>
              <div v-for="name in topAppNames" :key="name"
                class="flex items-center gap-2 rounded-xl px-3 py-1.5 cursor-pointer select-none mx-1 hover:bg-white/10"
                @click.stop="toggleTopApp(name)">
                <span class="material-symbols-outlined text-[14px] shrink-0" :class="topAppHiddenApps.has(name) ? 'text-on-surface-variant/30' : 'text-secondary'">{{ topAppHiddenApps.has(name) ? 'check_box_outline_blank' : 'check_box' }}</span>
                <span class="text-body-sm break-all" :class="topAppHiddenApps.has(name) ? 'line-through text-on-surface-variant/50' : ''">{{ name }}</span>
              </div>
            </div>
          </div>
        </Transition>
      </Teleport>
      <div class="flex-1"></div>
      <button class="glass-button px-2 py-1.5 rounded-lg font-caption text-caption flex items-center gap-1" @click="showSaveDialog = true">
        <span class="material-symbols-outlined text-[14px]">save</span>{{ t('perf.saveSession') }}
      </button>
      <button class="glass-button px-2 py-1.5 rounded-lg font-caption text-caption flex items-center gap-1" @click="openLoadDialog">
        <span class="material-symbols-outlined text-[14px]">history</span>{{ t('perf.loadSession') }}
      </button>
      <button class="glass-button px-2 py-1.5 rounded-lg font-caption text-caption flex items-center gap-1" @click="exportReport">
        <span class="material-symbols-outlined text-[14px]">file_download</span>{{ t('perf.exportReport') }}
      </button>
      <button class="glass-button px-2 py-1.5 rounded-lg font-caption text-caption flex items-center gap-1" @click="clearHistory">
        <span class="material-symbols-outlined text-[14px]">delete_sweep</span>{{ t('perf.clearHistory') }}
      </button>
    </div>

    <!-- 2x2 Grid: Memory/CPU (top) + Top N / Single app (bottom) -->
    <div class="grid grid-cols-2 grid-rows-2 gap-4 flex-1 min-h-0">
      <!-- Memory trend -->
      <div class="glass-panel rounded-xl p-4 shadow-md flex flex-col min-h-0">
        <h3 class="font-label-md text-label-md text-on-surface mb-2 shrink-0 flex items-center gap-3 flex-wrap">
          <span class="material-symbols-outlined text-[16px] text-secondary">memory_alt</span>{{ t('perf.memTrend') }}
          <span class="flex items-center gap-3 ml-auto flex-wrap">
            <span class="flex items-center gap-1 font-caption text-caption cursor-pointer"
              :class="showMemUsed ? 'text-on-surface' : 'text-on-surface-variant/30'"
              @click="toggleMemSeries('used')">
              <span class="w-2.5 h-2.5 rounded-full" :class="showMemUsed ? '' : 'opacity-30'" style="background:#7c5cfc"></span>{{ t('perf.used') }}
            </span>
            <span class="flex items-center gap-1 font-caption text-caption cursor-pointer"
              :class="showMemFree ? 'text-on-surface' : 'text-on-surface-variant/30'"
              @click="toggleMemSeries('free')">
              <span class="w-2.5 h-2.5 rounded-full" :class="showMemFree ? '' : 'opacity-30'" style="background:#22c55e"></span>{{ t('perf.free') }}
            </span>
          </span>
        </h3>
        <div ref="memChartRef" class="flex-1 min-h-0"></div>
      </div>

      <!-- CPU trend -->
      <div class="glass-panel rounded-xl p-4 shadow-md flex flex-col min-h-0">
        <h3 class="font-label-md text-label-md text-on-surface mb-2 shrink-0 flex items-center gap-2 flex-wrap">
          <span class="material-symbols-outlined text-[16px] text-secondary">memory</span>Top{{ store.cpuTopNCount }} 应用CPU使用率
          <span class="flex items-center gap-1 ml-auto">
            <span class="font-caption text-caption text-on-surface-variant text-nowrap">Top</span>
            <div class="relative" ref="cpuDropdownRef">
              <button class="glass-hover rounded-xl px-3 py-1.5 text-body-md flex items-center gap-2 select-none min-w-[56px]"
                @click="toggleCpuDropdown">
                <span class="flex-1 text-left">{{ store.cpuTopNCount }}</span>
                <span class="material-symbols-outlined text-[16px] transition-transform" :class="cpuDropdownOpen ? 'rotate-180' : ''">expand_more</span>
              </button>
            </div>
            <div class="relative" ref="cpuFilterRef">
              <button class="glass-hover rounded-xl px-2 py-1.5 flex items-center gap-1 select-none"
                @click="toggleCpuFilterDropdown" :title="'应用筛选'">
                <span class="material-symbols-outlined text-[16px]">filter_list</span>
                <span v-if="cpuHiddenApps.size > 0" class="text-[10px] font-bold text-secondary">{{ store.cpuTopNCount - cpuHiddenApps.size }}/{{ store.cpuTopNCount }}</span>
              </button>
            </div>
          </span>
        </h3>
        <div ref="cpuChartRef" class="flex-1 min-h-0"></div>
      </div>

      <!-- Top N app memory trend -->
      <div class="glass-panel rounded-xl p-4 shadow-md flex flex-col min-h-0">
        <h3 class="font-label-md text-label-md text-on-surface mb-2 shrink-0 flex items-center gap-2 flex-wrap">
          <span class="material-symbols-outlined text-[16px] text-secondary">lan</span>Top{{ store.topAppCount }} 应用内存
            <span class="flex items-center gap-1 ml-auto">
              <span class="font-caption text-caption text-on-surface-variant text-nowrap">显示</span>
              <div class="relative" ref="topNDropdownRef">
                <button class="glass-hover rounded-xl px-3 py-1.5 text-body-md flex items-center gap-2 select-none min-w-[56px]"
                  @click="toggleTopNDropdown">
                  <span class="flex-1 text-left">{{ store.topAppCount }}</span>
                  <span class="material-symbols-outlined text-[16px] transition-transform" :class="topNDropdownOpen ? 'rotate-180' : ''">expand_more</span>
                </button>
              </div>
              <div class="relative" ref="topAppFilterRef">
                <button class="glass-hover rounded-xl px-2 py-1.5 flex items-center gap-1 select-none"
                  @click="toggleTopAppFilterDropdown" :title="'应用筛选'">
                  <span class="material-symbols-outlined text-[16px]">filter_list</span>
                  <span v-if="topAppHiddenApps.size > 0" class="text-[10px] font-bold text-secondary">{{ store.topAppCount - topAppHiddenApps.size }}/{{ store.topAppCount }}</span>
                </button>
              </div>
            </span>
        </h3>
        <div ref="topAppChartRef" class="flex-1 min-h-0"></div>
      </div>

      <!-- Single app memory trend -->
      <div class="glass-panel rounded-xl p-4 shadow-md flex flex-col min-h-0">
        <h3 class="font-label-md text-label-md text-on-surface mb-2 shrink-0 flex items-center gap-2 flex-wrap">
          <span class="material-symbols-outlined text-[16px] text-secondary">app_badging</span>单个应用内存
          <span class="flex items-center gap-1 ml-auto">
            <input v-model="appSearch" placeholder="输入应用包名..."
              class="w-48 bg-white/60 backdrop-blur-sm border border-outline-variant/50 rounded-xl px-3 py-1.5 font-caption text-caption text-on-surface outline-none focus:ring-2 focus:ring-secondary/40 shadow-sm"
              @change="updateSingleAppName" />
            <button v-if="store.singleAppName" class="glass-hover rounded-xl px-2 py-1.5" @click="clearSingleApp">
              <span class="material-symbols-outlined text-[16px]">clear</span>
            </button>
          </span>
        </h3>
        <div ref="singleAppChartRef" class="flex-1 min-h-0"></div>
      </div>
    </div>

    <!-- Save Session Dialog -->
    <Teleport to="body">
      <Transition name="fade">
        <div v-if="showSaveDialog" class="fixed inset-0 z-50 flex items-center justify-center" @click.self="showSaveDialog = false">
          <div class="absolute inset-0 bg-black/30 backdrop-blur-sm"></div>
          <div class="glass-panel rounded-[2rem] p-6 w-full max-w-md relative z-10 bg-white/60">
            <div class="flex justify-between items-center mb-4">
              <h3 class="font-label-md text-label-md text-on-surface font-semibold flex items-center gap-1.5">
                <span class="material-symbols-outlined text-[16px]">save</span>{{ t('perf.saveSession') }}
              </h3>
              <button class="glass-button p-1 rounded" @click="showSaveDialog = false">
                <span class="material-symbols-outlined text-[18px]">close</span>
              </button>
            </div>
            <input v-model="sessionName" class="w-full bg-white/60 backdrop-blur-sm border border-outline-variant/50 rounded-xl px-4 py-2 font-body-sm text-body-sm mb-4 outline-none focus:ring-2 focus:ring-secondary/40 shadow-sm select-text"
              :placeholder="t('perf.sessionName')" @keyup.enter="doSaveSession" />
            <div class="flex gap-2 justify-end">
              <button class="glass-button px-4 py-1.5 rounded-lg font-label-md text-label-md" @click="showSaveDialog = false">{{ t('device.cancel') }}</button>
              <button class="glass-button px-4 py-1.5 rounded-lg font-label-md text-label-md" :disabled="!sessionName.trim() || store.history.length === 0" @click="doSaveSession">{{ t('device.confirm') }}</button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- Load Session Dialog -->
    <Teleport to="body">
      <Transition name="fade">
        <div v-if="showLoadDialog" class="fixed inset-0 z-50 flex items-center justify-center" @click.self="showLoadDialog = false">
          <div class="absolute inset-0 bg-black/30 backdrop-blur-sm"></div>
          <div class="glass-panel rounded-[2rem] p-6 w-full max-w-lg relative z-10 bg-white/60 max-h-[80vh] flex flex-col">
            <div class="flex justify-between items-center mb-4 shrink-0">
              <h3 class="font-label-md text-label-md text-on-surface font-semibold flex items-center gap-1.5">
                <span class="material-symbols-outlined text-[16px]">history</span>{{ t('perf.loadSession') }}
              </h3>
              <button class="glass-button p-1 rounded" @click="showLoadDialog = false">
                <span class="material-symbols-outlined text-[18px]">close</span>
              </button>
            </div>
            <div v-if="sessions.length === 0" class="flex-1 flex items-center justify-center text-on-surface-variant/50 font-caption text-caption py-8">
              {{ t('settings.cloudEmpty') }}
            </div>
            <div v-else class="flex-1 min-h-0 overflow-y-auto custom-scrollbar space-y-1">
              <div v-for="s in sessions" :key="s.id"
                class="w-full flex items-center justify-between px-3 py-2 rounded-xl hover:bg-white/30 transition-all text-left group cursor-pointer"
                @click="doLoadSession(s)">
                <div>
                  <div class="font-label-sm text-label-sm text-on-surface">{{ s.name }}</div>
                  <div class="font-caption text-caption text-on-surface-variant/60">{{ s.device_serial }} · {{ new Date(s.created_at).toLocaleString() }} · {{ s.data.length }} pts</div>
                </div>
                <div class="flex items-center gap-1">
                  <span class="material-symbols-outlined text-[16px] text-error opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer" @click.stop="doDeleteSession(s)">delete</span>
                  <span class="material-symbols-outlined text-[16px] text-secondary">folder_open</span>
                </div>
              </div>
            </div>
            <div class="flex gap-2 justify-end pt-4 border-t border-outline-variant/30 mt-4 shrink-0">
              <button class="glass-button px-4 py-1.5 rounded-lg font-label-md text-label-md" @click="showLoadDialog = false">{{ t('device.close') }}</button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- Toast -->
    <Teleport to="body">
      <Transition name="fade">
        <div v-if="toastMsg" class="fixed top-4 left-1/2 -translate-x-1/2 z-[9999] glass-panel rounded-xl px-5 py-3 bg-white/80 shadow-lg flex items-center gap-2"
          :class="toastError ? 'text-error border border-error/20' : 'text-on-surface'">
          <span class="material-symbols-outlined text-[18px]">{{ toastError ? 'error' : 'check_circle' }}</span>
          <span class="font-body-sm text-body-sm">{{ toastMsg }}</span>
        </div>
      </Transition>
    </Teleport>

    <!-- Export Loading Overlay -->
    <Teleport to="body">
      <Transition name="fade">
        <div v-if="isExporting" class="fixed inset-0 z-[9998] flex items-center justify-center bg-black/30 backdrop-blur-sm">
          <div class="glass-panel rounded-2xl p-8 flex flex-col items-center gap-4 bg-white/90 shadow-2xl">
            <div class="w-12 h-12 rounded-full border-4 border-secondary/20 border-t-secondary animate-spin"></div>
            <span class="font-label-md text-label-md text-on-surface">正在停止并保存数据...</span>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, onActivated, onDeactivated, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from '@/composables/useI18n'
import { usePerfMonitor, type PerfSnapshot } from '@/composables/usePerfMonitor'
import { useAdb } from '@/composables/useAdb'
import { usePerfMonitorStore } from '@/stores/usePerfMonitorStore'
import { savePerfSession, listPerfSessions, deletePerfSession, type PerfSessionRow } from '@/services/database'
import { mkdir, writeTextFile, readTextFile, readDir } from '@tauri-apps/plugin-fs'
import { appDataDir } from '@tauri-apps/api/path'
import { open } from '@tauri-apps/plugin-dialog'
import { invoke } from '@tauri-apps/api/core'
import * as echarts from 'echarts'

defineOptions({ name: 'PerfMonitorPage' })

const router = useRouter()
const { t } = useI18n()
const { getSnapshot } = usePerfMonitor()
const { shell, dmesg, rootDevice, pullFile } = useAdb()
const store = usePerfMonitorStore()

const deviceSerial = ref(localStorage.getItem('last_device_serial') || '')
const intervalMs = ref(String(store.intervalMs))
// Track whether the page is currently active (visible). When deactivated by
// keep-alive (user switched to another page), we skip ECharts rendering to
// avoid blocking the main thread, but data collection continues uninterrupted.
const isPageActive = ref(true)

// Interval dropdown
const intervalDropdownOpen = ref(false)
const intervalDropdownRef = ref<HTMLElement | null>(null)
const intervalDropdownStyle = ref({ top: '0px', left: '0px' })
const intervalOptions = [
  { value: 1000, label: '1s' },
  { value: 2000, label: '2s' },
  { value: 5000, label: '5s' },
  { value: 10000, label: '10s' },
]
function toggleIntervalDropdown() {
  if (intervalDropdownOpen.value) { intervalDropdownOpen.value = false; return }
  if (intervalDropdownRef.value) {
    const r = intervalDropdownRef.value.getBoundingClientRect()
    intervalDropdownStyle.value = { top: `${r.bottom + 4}px`, left: `${r.left}px` }
  }
  intervalDropdownOpen.value = true
}
function selectInterval(v: number) {
  store.setInterval(v)
  intervalMs.value = String(v)
  intervalDropdownOpen.value = false
  // Restart polling timer with new interval if currently collecting
  if (store.isCollecting && pollTimer) {
    clearInterval(pollTimer)
    pollTimer = setInterval(pollOnce, v)
  }
}

// Top N dropdown
const topNDropdownOpen = ref(false)
const topNDropdownRef = ref<HTMLElement | null>(null)
const topNDropdownStyle = ref({ top: '0px', left: '0px' })
const topNOptions = [5, 10, 20, 25, 30]
function toggleTopNDropdown() {
  if (topNDropdownOpen.value) { topNDropdownOpen.value = false; return }
  if (topNDropdownRef.value) {
    const r = topNDropdownRef.value.getBoundingClientRect()
    topNDropdownStyle.value = { top: `${r.bottom + 4}px`, left: `${r.left}px` }
  }
  topNDropdownOpen.value = true
}
function selectTopN(n: number) {
  store.topAppCount = n
  topNDropdownOpen.value = false
}

// CPU Top N dropdown — independent from TopApp dropdown (uses cpuTopNCount)
const cpuDropdownOpen = ref(false)
const cpuDropdownRef = ref<HTMLElement | null>(null)
const cpuDropdownStyle = ref({ top: '0px', left: '0px' })
function toggleCpuDropdown() {
  if (cpuDropdownOpen.value) { cpuDropdownOpen.value = false; return }
  if (cpuDropdownRef.value) {
    const r = cpuDropdownRef.value.getBoundingClientRect()
    cpuDropdownStyle.value = { top: `${r.bottom + 4}px`, left: `${r.left}px` }
  }
  cpuDropdownOpen.value = true
}
function selectCpuTopN(n: number) {
  store.cpuTopNCount = n
  cpuDropdownOpen.value = false
}

// App filter dropdowns (CPU + TopApp) — replace echarts default legend to
// prevent tooltip/legend overflow at bottom of chart.
const cpuFilterOpen = ref(false)
const cpuFilterRef = ref<HTMLElement | null>(null)
const cpuFilterPanelRef = ref<HTMLElement | null>(null)
const cpuFilterStyle = ref({ top: '0px', left: '0px' })
const cpuHiddenApps = ref<Set<string>>(new Set())

const topAppFilterOpen = ref(false)
const topAppFilterRef = ref<HTMLElement | null>(null)
const topAppFilterPanelRef = ref<HTMLElement | null>(null)
const topAppFilterStyle = ref({ top: '0px', left: '0px' })
const topAppHiddenApps = ref<Set<string>>(new Set())

// Computed list of current top N app names (sorted by latest value desc)
const cpuAppNames = computed(() => {
  const hist = store.processCpuHistory
  if (hist.size === 0) return []
  return Array.from(hist.entries())
    .map(([name, data]) => ({ name, lastCpu: data[data.length - 1]?.cpuPercent ?? 0 }))
    .sort((a, b) => b.lastCpu - a.lastCpu)
    .slice(0, store.cpuTopNCount)
    .map(p => p.name)
})
const topAppNames = computed(() => {
  const hist = store.processPssHistory
  if (hist.size === 0) return []
  return Array.from(hist.entries())
    .map(([name, data]) => ({ name, lastPss: data[data.length - 1]?.pssKb ?? 0 }))
    .sort((a, b) => b.lastPss - a.lastPss)
    .slice(0, store.topAppCount)
    .map(p => p.name)
})

function toggleCpuFilterDropdown() {
  if (cpuFilterOpen.value) { cpuFilterOpen.value = false; return }
  if (cpuFilterRef.value) {
    const r = cpuFilterRef.value.getBoundingClientRect()
    // Open upward if not enough space below
    const panelH = Math.min(400, cpuAppNames.value.length * 32 + 60)
    const winH = window.innerHeight
    const top = (r.bottom + panelH > winH) ? r.top - panelH - 4 : r.bottom + 4
    cpuFilterStyle.value = { top: `${Math.max(8, top)}px`, left: `${Math.min(r.left, window.innerWidth - 260)}px` }
  }
  cpuFilterOpen.value = true
}
function toggleTopAppFilterDropdown() {
  if (topAppFilterOpen.value) { topAppFilterOpen.value = false; return }
  if (topAppFilterRef.value) {
    const r = topAppFilterRef.value.getBoundingClientRect()
    const panelH = Math.min(400, topAppNames.value.length * 32 + 60)
    const winH = window.innerHeight
    const top = (r.bottom + panelH > winH) ? r.top - panelH - 4 : r.bottom + 4
    topAppFilterStyle.value = { top: `${Math.max(8, top)}px`, left: `${Math.min(r.left, window.innerWidth - 260)}px` }
  }
  topAppFilterOpen.value = true
}

function toggleCpuApp(name: string) {
  const s = new Set(cpuHiddenApps.value)
  if (s.has(name)) s.delete(name)
  else s.add(name)
  cpuHiddenApps.value = s
  updateCpuChart()
}
function toggleTopApp(name: string) {
  const s = new Set(topAppHiddenApps.value)
  if (s.has(name)) s.delete(name)
  else s.add(name)
  topAppHiddenApps.value = s
  updateTopAppChart()
}
function cpuSelectAll() { cpuHiddenApps.value = new Set(); updateCpuChart() }
function cpuSelectNone() {
  cpuHiddenApps.value = new Set(cpuAppNames.value)
  updateCpuChart()
}
function topAppSelectAll() { topAppHiddenApps.value = new Set(); updateTopAppChart() }
function topAppSelectNone() {
  topAppHiddenApps.value = new Set(topAppNames.value)
  updateTopAppChart()
}

// Click outside to close dropdowns
function handleDropdownClick(e: MouseEvent) {
  const t = e.target as Node
  if (intervalDropdownOpen.value && intervalDropdownRef.value && !intervalDropdownRef.value.contains(t)) {
    intervalDropdownOpen.value = false
  }
  if (topNDropdownOpen.value && topNDropdownRef.value && !topNDropdownRef.value.contains(t)) {
    topNDropdownOpen.value = false
  }
  if (cpuDropdownOpen.value && cpuDropdownRef.value && !cpuDropdownRef.value.contains(t)) {
    cpuDropdownOpen.value = false
  }
  if (cpuFilterOpen.value && cpuFilterRef.value && !cpuFilterRef.value.contains(t) &&
      cpuFilterPanelRef.value && !cpuFilterPanelRef.value.contains(t)) {
    cpuFilterOpen.value = false
  }
  if (topAppFilterOpen.value && topAppFilterRef.value && !topAppFilterRef.value.contains(t) &&
      topAppFilterPanelRef.value && !topAppFilterPanelRef.value.contains(t)) {
    topAppFilterOpen.value = false
  }
}

let pollTimer: ReturnType<typeof setInterval> | null = null
let logTimer: ReturnType<typeof setInterval> | null = null
const sessionLogDir = ref('')
const sessionLogPaths = ref<string[]>([])
let cpuChart: echarts.ECharts | null = null
let memChart: echarts.ECharts | null = null
let topAppChart: echarts.ECharts | null = null
let singleAppChart: echarts.ECharts | null = null
let chartResizeObserver: ResizeObserver | null = null
const cpuChartRef = ref<HTMLElement | null>(null)
const memChartRef = ref<HTMLElement | null>(null)
const topAppChartRef = ref<HTMLElement | null>(null)
const singleAppChartRef = ref<HTMLElement | null>(null)

// Series visibility
const showCpu = ref(true)
const showMemUsed = ref(true)
const showMemFree = ref(true)

function toggleCpu() {
  showCpu.value = !showCpu.value
  cpuChart?.dispatchAction({ type: 'legendToggleSelect', name: 'CPU' })
}
function toggleMemSeries(name: string) {
  if (name === 'used') {
    showMemUsed.value = !showMemUsed.value
    memChart?.dispatchAction({ type: 'legendToggleSelect', name: t('perf.used') })
  } else {
    showMemFree.value = !showMemFree.value
    memChart?.dispatchAction({ type: 'legendToggleSelect', name: t('perf.free') })
  }
}

const appSearch = ref('')

function updateSingleAppName() {
  const name = appSearch.value.trim()
  store.singleAppName = name
  updateSingleAppChart()
}

function clearSingleApp() {
  store.singleAppName = ''
  appSearch.value = ''
  updateSingleAppChart()
}

// Toast
const toastMsg = ref('')
const toastError = ref(false)
const isExporting = ref(false)
let toastTimer: ReturnType<typeof setTimeout> | null = null
function showToast(msg: string, err = false) {
  toastMsg.value = msg
  toastError.value = err
  if (toastTimer) clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toastMsg.value = '' }, 4000)
}

// Save/Load dialogs
const showSaveDialog = ref(false)
const showLoadDialog = ref(false)
const sessionName = ref('')
const sessions = ref<PerfSessionRow[]>([])

async function doSaveSession() {
  if (!sessionName.value.trim() || store.history.length === 0) return
  const id = Date.now().toString(36) + Math.random().toString(36).slice(2, 6)
  // Save full session: history points + per-process history maps + single app name + topN counts
  const sessionData = JSON.stringify({
    history: store.history,
    processPssHistory: Array.from(store.processPssHistory.entries()),
    processCpuHistory: Array.from(store.processCpuHistory.entries()),
    singleAppName: store.singleAppName,
    topAppCount: store.topAppCount,
    cpuTopNCount: store.cpuTopNCount,
  })
  await savePerfSession({
    id,
    name: sessionName.value.trim(),
    device_serial: deviceSerial.value,
    started_at: new Date(store.history[0]?.time ?? Date.now()).toISOString(),
    ended_at: new Date().toISOString(),
    interval_ms: store.intervalMs,
    data: sessionData,
    created_at: new Date().toISOString(),
  })
  showSaveDialog.value = false
  sessionName.value = ''
  showToast(t('perf.sessionSaved'))
}

async function openLoadDialog() {
  sessions.value = await listPerfSessions()
  showLoadDialog.value = true
}

async function doLoadSession(s: PerfSessionRow) {
  try {
    const parsed = JSON.parse(s.data)
    // Handle both old format (array of points) and new format (object with history + process maps)
    if (Array.isArray(parsed)) {
      store.restoreHistory(parsed)
    } else {
      store.restoreFullSession(parsed)
    }
    store.setInterval(s.interval_ms)
    intervalMs.value = String(s.interval_ms)
    showLoadDialog.value = false
    // Must call all 4 update functions so every chart reloads from restored data
    updateCharts()
    updateTopAppChart()
    updateCpuChart()
    updateSingleAppChart()
    showToast(t('perf.sessionLoaded'))
  } catch { showToast('Failed to load session', true) }
}

async function doDeleteSession(s: PerfSessionRow) {
  await deletePerfSession(s.id)
  sessions.value = sessions.value.filter(x => x.id !== s.id)
  showToast(t('perf.sessionDeleted'))
}

function formatKb(v: number): string {
  if (v >= 1048576) return (v / 1048576).toFixed(1)
  if (v >= 1024) return (v / 1024).toFixed(1)
  return v.toFixed(0)
}
function formatKbUnit(v: number): string {
  if (v >= 1048576) return 'GB'
  if (v >= 1024) return 'MB'
  return 'KB'
}
function formatMem(v: number): string {
  const gb = (v / 1048576).toFixed(2)
  const mb = Math.round(v / 1024)
  return `${gb}GB(${mb}MB)`
}

// Safe max/min for large arrays — Math.max(...arr) stack-overflows on >~65K elements
function safeMax(arr: number[]): number {
  let m = -Infinity
  for (const v of arr) if (v > m) m = v
  return m
}

function safeMin(arr: number[]): number {
  let m = Infinity
  for (const v of arr) if (v < m) m = v
  return m
}

function safeAvg(arr: number[]): number {
  if (arr.length === 0) return 0
  let s = 0
  for (const v of arr) s += v
  return s / arr.length
}

// Downsample an array of points to at most maxLen entries by taking every Nth point.
// Keeps first and last to preserve time range. Used for HTML interactive charts
// to prevent huge JSON payloads when monitoring runs for hours/days.
function downsample<T>(arr: T[], maxLen: number): T[] {
  if (arr.length <= maxLen) return arr
  const step = Math.ceil(arr.length / maxLen)
  const result: T[] = []
  for (let i = 0; i < arr.length; i += step) result.push(arr[i])
  // Always keep the last point
  if (result[result.length - 1] !== arr[arr.length - 1]) result.push(arr[arr.length - 1])
  return result
}

// Build an overall assessment section based on collected data.
// Heuristics: high CPU peaks, low available memory, PSS surges,
// memory-leak-like continuous growth, sustained rising trends.
// NOTE: For reference only — not a definitive diagnosis.
function buildOverallAssessment(
  pts: { time: number; cpu: number; memUsedKb: number; memTotalKb: number; memAvailKb: number }[],
  topMem: { name: string; data: { time: number; pssKb: number }[] }[],
  topCpu: { name: string; data: { time: number; cpuPercent: number }[] }[],
  singleName: string,
  singleData: { time: number; pssKb: number }[],
): string {
  const issues: string[] = []
  const leaks: string[] = []
  const rising: string[] = []

  if (pts.length >= 4) {
    // 1. Abnormal CPU peak
    const cpus = pts.map(p => p.cpu)
    const maxCpu = safeMax(cpus)
    if (maxCpu > 90) {
      issues.push(`CPU 峰值达到 ${maxCpu.toFixed(1)}%，接近满载，可能影响系统流畅度`)
    } else if (maxCpu > 80) {
      issues.push(`CPU 峰值达到 ${maxCpu.toFixed(1)}%，处于较高水平`)
    }

    // 2. Low available memory
    const minAvail = safeMin(pts.map(p => p.memAvailKb))
    const totalMem = pts[0].memTotalKb
    if (totalMem > 0 && minAvail / totalMem < 0.1) {
      issues.push(`设备可用内存最低仅 ${formatKb(minAvail)} ${formatKbUnit(minAvail)}，低于总内存 10%，存在 OOM 风险`)
    } else if (totalMem > 0 && minAvail / totalMem < 0.2) {
      issues.push(`设备可用内存最低 ${formatKb(minAvail)} ${formatKbUnit(minAvail)}，低于总内存 20%，内存紧张`)
    }

    // 3. Per-app CPU anomalies
    for (const p of topCpu) {
      if (p.data.length < 4) continue
      const vals = p.data.map(d => d.cpuPercent)
      const mx = safeMax(vals)
      const avg = safeAvg(vals)
      if (mx > 50 && mx > avg * 3) {
        issues.push(`应用 ${p.name} CPU 峰值 ${mx.toFixed(1)}% 远超均值 ${avg.toFixed(1)}%，存在 CPU 突发占用`)
      }
    }

    // 4. Memory leak detection: PSS grows continuously and final > initial * 1.3
    const minPointsForTrend = Math.min(10, Math.floor(pts.length / 2))
    for (const p of topMem) {
      if (p.data.length < minPointsForTrend * 2) continue
      const firstAvg = safeAvg(p.data.slice(0, minPointsForTrend).map(d => d.pssKb))
      const lastAvg = safeAvg(p.data.slice(-minPointsForTrend).map(d => d.pssKb))
      if (firstAvg > 0 && lastAvg > firstAvg * 1.3) {
        const growth = ((lastAvg - firstAvg) / firstAvg * 100).toFixed(1)
        if (lastAvg > firstAvg * 1.5) {
          leaks.push(`应用 ${p.name} PSS 从 ${formatKb(firstAvg)} ${formatKbUnit(firstAvg)} 增长到 ${formatKb(lastAvg)} ${formatKbUnit(lastAvg)}（+${growth}%），疑似内存泄露`)
        } else {
          rising.push(`应用 ${p.name} PSS 持续上涨 ${growth}%（${formatKb(firstAvg)} → ${formatKb(lastAvg)} ${formatKbUnit(lastAvg)}）`)
        }
      }
    }

    // 5. Single app memory leak
    if (singleData.length >= minPointsForTrend * 2) {
      const firstAvg = safeAvg(singleData.slice(0, minPointsForTrend).map(d => d.pssKb))
      const lastAvg = safeAvg(singleData.slice(-minPointsForTrend).map(d => d.pssKb))
      if (firstAvg > 0 && lastAvg > firstAvg * 1.3) {
        const growth = ((lastAvg - firstAvg) / firstAvg * 100).toFixed(1)
        if (lastAvg > firstAvg * 1.5) {
          leaks.push(`单应用 ${singleName} PSS 从 ${formatKb(firstAvg)} ${formatKbUnit(firstAvg)} 增长到 ${formatKb(lastAvg)} ${formatKbUnit(lastAvg)}（+${growth}%），疑似内存泄露`)
        } else {
          rising.push(`单应用 ${singleName} PSS 持续上涨 ${growth}%`)
        }
      }
    }

    // 6. CPU sustained high
    for (const p of topCpu) {
      if (p.data.length < minPointsForTrend * 2) continue
      const lastAvg = safeAvg(p.data.slice(-minPointsForTrend).map(d => d.cpuPercent))
      if (lastAvg > 30) {
        rising.push(`应用 ${p.name} 近期 CPU 均值 ${lastAvg.toFixed(1)}%，持续高占用`)
      }
    }
  }

  const issueHtml = issues.length
    ? issues.map(i => `<li>${i}</li>`).join('')
    : '<li style="color:#22c55e">未检测到明显异常</li>'
  const leakHtml = leaks.length
    ? leaks.map(i => `<li>${i}</li>`).join('')
    : '<li style="color:#22c55e">未检测到明显内存泄露特征</li>'
  const risingHtml = rising.length
    ? rising.map(i => `<li>${i}</li>`).join('')
    : '<li style="color:#22c55e">未检测到持续上涨趋势</li>'

  return `<div class="card">
  <h2>整体评估</h2>
  <div style="background:#fef9e7;border:1px solid #f0e0a0;border-radius:8px;padding:.6rem .8rem;margin-bottom:1rem;font-size:.85rem;color:#8a6d3b">
    <strong>⚠️ 仅供参考：</strong>以下评估基于采集期间的统计数据和简单趋势检测，不构成确定性诊断。实际表现可能受设备状态、系统调度、测试场景等多种因素影响，请结合具体场景综合判断。
  </div>
  <h3 style="color:#e74c3c;font-size:.95rem;margin:1rem 0 .4rem 0">异常情况</h3>
  <ul>${issueHtml}</ul>
  <h3 style="color:#9b59b6;font-size:.95rem;margin:1rem 0 .4rem 0">内存泄露情况</h3>
  <ul>${leakHtml}</ul>
  <h3 style="color:#f39c12;font-size:.95rem;margin:1rem 0 .4rem 0">持续上涨情况</h3>
  <ul>${risingHtml}</ul>
</div>`
}

async function exportReport() {
  const pts = store.history
  if (pts.length === 0) { showToast('暂无数据可导出', true); return }
  isExporting.value = true
  try {
    const dir = await open({ directory: true, multiple: false, title: '选择导出目录' })
    if (!dir) return

    const cpus = pts.map(p => p.cpu)
    const memUsed = pts.map(p => p.memUsedKb)
    const memAvail = pts.map(p => p.memAvailKb)
    const avgCpu = cpus.reduce((a, b) => a + b, 0) / cpus.length
    const maxCpu = safeMax(cpus)
    const avgMemUsed = memUsed.reduce((a, b) => a + b, 0) / memUsed.length
    const maxMemUsed = safeMax(memUsed)
    const avgMemAvail = memAvail.reduce((a, b) => a + b, 0) / memAvail.length

    const hist = store.processPssHistory
    const cpuHist = store.processCpuHistory
    const topN = Array.from(hist.entries())
      .map(([name, data]) => ({ name, lastPss: data[data.length - 1]?.pssKb ?? 0, data }))
      .sort((a, b) => b.lastPss - a.lastPss)
      .slice(0, store.topAppCount)
    const topCpu = Array.from(cpuHist.entries())
      .map(([name, data]) => ({ name, lastCpu: data[data.length - 1]?.cpuPercent ?? 0, data }))
      .sort((a, b) => b.lastCpu - a.lastCpu)
      .slice(0, store.cpuTopNCount)
    const topNames = topN.map(p => p.name)
    const singleName = store.singleAppName
    const singleData = singleName ? (hist.get(singleName) || []) : []

    // Save perf_data.csv
    const csvHeader = 'Time,CPU(%),MemUsed(KB),MemTotal(KB),MemAvail(KB),ZRAM(KB),StorageUsed(KB),StorageTotal(KB)'
    const csvRows = pts.map(p =>
      `${new Date(p.time).toISOString()},${p.cpu.toFixed(1)},${p.memUsedKb},${p.memTotalKb},${p.memAvailKb},${p.zramKb},${p.storageUsedKb},${p.storageTotalKb}`
    )
    await writeTextFile(dir + '/perf_data.csv', csvHeader + '\n' + csvRows.join('\n'))

    // Save perf_top_apps.csv
    if (topN.length > 0) {
      const topHeader = 'Time,' + topNames.map(n => `"${n}(KB)"`).join(',')
      const maxLen = safeMax(topN.map(p => p.data.length))
      const topRows: string[] = []
      for (let i = 0; i < maxLen; i++) {
        const t = i < topN[0].data.length ? new Date(topN[0].data[i].time).toISOString() : ''
        const vals = topN.map(p => i < p.data.length ? p.data[i].pssKb.toString() : '')
        topRows.push(t + ',' + vals.join(','))
      }
      await writeTextFile(dir + '/perf_top_apps.csv', topHeader + '\n' + topRows.join('\n'))
    }

    // Save perf_top_cpu.csv
    if (topCpu.length > 0) {
      const maxLen = safeMax(topCpu.map(p => p.data.length))
      const rows: string[] = []
      for (let i = 0; i < maxLen; i++) {
        const t = i < topCpu[0].data.length ? new Date(topCpu[0].data[i].time).toISOString() : ''
        const vals = topCpu.map(p => i < p.data.length ? p.data[i].cpuPercent.toFixed(1) : '')
        rows.push(t + ',' + vals.join(','))
      }
      await writeTextFile(dir + '/perf_top_cpu.csv', 'Time,' + topCpu.map(p => `"${p.name}(%)"`).join(',') + '\n' + rows.join('\n'))
    }

    // Save perf_single_app.csv
    if (singleData.length > 0) {
      const singleCsv = 'Time,PSS(KB)\n' + singleData.map(d => `${new Date(d.time).toISOString()},${d.pssKb}`).join('\n')
      await writeTextFile(dir + '/perf_single_app.csv', singleCsv)
    }

    // Save perf_report.html — downsample data for interactive charts to keep
    // the HTML file manageable (max 2000 points per series) even for multi-day runs
    const DOWNSAMPLE_MAX = 2000
    const dsPts = downsample(pts, DOWNSAMPLE_MAX)
    const dsTopN = topN.map(p => ({ ...p, data: downsample(p.data, DOWNSAMPLE_MAX) }))
    const dsTopCpu = topCpu.map(p => ({ ...p, data: downsample(p.data, DOWNSAMPLE_MAX) }))
    const dsSingleData = downsample(singleData, DOWNSAMPLE_MAX)
    const interactiveHtml = buildInteractiveChartsHtml(dsPts, dsTopN, dsTopCpu, singleName || '', dsSingleData)
    const html = `<!DOCTYPE html>
<html lang="zh">
<head><meta charset="utf-8"><title>性能报告</title>
<style>
body{font-family:system-ui,-apple-system,sans-serif;max-width:1100px;margin:auto;padding:2rem;background:#f5f5f5;color:#222}
h1{color:#333;border-bottom:2px solid #7c5cfc;padding-bottom:.5rem}
h2{color:#444;margin-top:1.5rem}
table{border-collapse:collapse;width:100%;margin:1rem 0;font-size:.85rem}
th,td{padding:.35rem .5rem;text-align:left;border-bottom:1px solid #ddd}
th{background:#7c5cfc;color:#fff;font-weight:600;position:sticky;top:0}
td{font-variant-numeric:tabular-nums}
.card{background:#fff;border-radius:12px;padding:1.2rem;margin:1rem 0;box-shadow:0 2px 8px rgba(0,0,0,.08)}
.card-title{font-size:1.1rem;font-weight:600;color:#444;margin-bottom:.8rem;padding-bottom:.4rem;border-bottom:1px solid #eee}
.stat-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:.8rem}
.stat{background:#f0eeff;border-radius:8px;padding:.8rem}
.stat-label{font-size:.7rem;color:#888}
.stat-value{font-size:1.1rem;font-weight:700;color:#222;margin-top:.2rem}
code{background:#eee;padding:.1em .3em;border-radius:3px;font-size:.85em}
img.chart{max-width:100%;border:1px solid #ddd;border-radius:8px;margin:.5rem 0}
.interactive-chart{background:#fafafa;border:1px solid #e5e5e5;border-radius:8px;padding:1rem;margin:1rem 0}
.interactive-chart h3{color:#444;font-size:1rem;margin:0 0 .5rem 0}
</style></head>
<body>
<h1>📊 性能监控报告</h1>
<div class="card">
  <h2>采集信息</h2>
  <p><strong>设备:</strong> ${deviceSerial.value || 'N/A'}</p>
  <p><strong>采样数:</strong> ${pts.length}</p>
  <p><strong>时间范围:</strong> ${new Date(pts[0].time).toISOString()} ~ ${new Date(pts[pts.length-1].time).toISOString()}</p>
  <p><strong>采集间隔:</strong> ${store.intervalMs}ms</p>
  <p><strong>导出目录:</strong> ${dir}</p>
</div>
${buildOverallAssessment(pts, topN, topCpu, singleName || '', singleData)}
<div class="card">
  <h2>汇总统计</h2>
  <div class="stat-grid">
    <div class="stat"><div class="stat-label">CPU 平均</div><div class="stat-value">${avgCpu.toFixed(1)}%</div></div>
    <div class="stat"><div class="stat-label">CPU 峰值</div><div class="stat-value">${maxCpu.toFixed(1)}%</div></div>
    <div class="stat"><div class="stat-label">内存已用平均</div><div class="stat-value">${formatKb(avgMemUsed)} ${formatKbUnit(avgMemUsed)}</div></div>
    <div class="stat"><div class="stat-label">内存已用峰值</div><div class="stat-value">${formatKb(maxMemUsed)} ${formatKbUnit(maxMemUsed)}</div></div>
    <div class="stat"><div class="stat-label">内存平均剩余</div><div class="stat-value">${formatKb(avgMemAvail)} ${formatKbUnit(avgMemAvail)}</div></div>
  </div>
</div>
<div class="card">
  <h2>Top${store.topAppCount} 应用内存使用情况</h2>
  <table><thead><tr><th>#</th><th>应用包名</th><th>最小 PSS</th><th>最大 PSS</th><th>平均 PSS</th></tr></thead>
  <tbody>${topN.map((p, i) => {
    const vals = p.data.map(d => d.pssKb)
    const mn = vals.length ? safeMin(vals) : 0
    const mx = vals.length ? safeMax(vals) : 0
    const av = vals.length ? safeAvg(vals) : 0
    return `<tr><td>${i+1}</td><td>${p.name}</td><td>${formatKb(mn)} ${formatKbUnit(mn)}</td><td>${formatKb(mx)} ${formatKbUnit(mx)}</td><td>${formatKb(av)} ${formatKbUnit(av)}</td></tr>`
  }).join('')}</tbody></table>
</div>
<div class="card">
  <h2>Top${store.cpuTopNCount} 应用 CPU 使用情况</h2>
  <table><thead><tr><th>#</th><th>应用包名</th><th>最小 CPU%</th><th>最大 CPU%</th><th>平均 CPU%</th></tr></thead>
  <tbody>${topCpu.map((p, i) => {
    const vals = p.data.map(d => d.cpuPercent)
    const mn = vals.length ? safeMin(vals) : 0
    const mx = vals.length ? safeMax(vals) : 0
    const av = vals.length ? safeAvg(vals) : 0
    return `<tr><td>${i+1}</td><td>${p.name}</td><td>${mn.toFixed(1)}%</td><td>${mx.toFixed(1)}%</td><td>${av.toFixed(1)}%</td></tr>`
  }).join('')}</tbody></table>
</div>
<div class="card">
  <h2>单个应用内存使用情况: ${singleName || '(未选择)'}</h2>
  ${singleData.length ? (() => {
    const vals = singleData.map(d => d.pssKb)
    const mn = safeMin(vals); const mx = safeMax(vals); const av = safeAvg(vals)
    return `<table><thead><tr><th>最小 PSS</th><th>最大 PSS</th><th>平均 PSS</th><th>采样数</th></tr></thead>
      <tbody><tr><td>${formatKb(mn)} ${formatKbUnit(mn)}</td><td>${formatKb(mx)} ${formatKbUnit(mx)}</td><td>${formatKb(av)} ${formatKbUnit(av)}</td><td>${singleData.length}</td></tr></tbody></table>`
  })() : '<p>暂无数据</p>'}
</div>
${interactiveHtml}
<div class="card">
  <h2>导出文件清单</h2>
  <ul>
    <li><code>perf_data.csv</code> — CPU/内存/存储 时序数据</li>
    <li><code>perf_top_apps.csv</code> — Top N 应用 PSS 时序数据</li>
    <li><code>perf_top_cpu.csv</code> — Top N 应用 CPU 时序数据</li>
    <li><code>perf_single_app.csv</code> — 单个应用 PSS 时序数据</li>
    <li><code>perf_report.html</code> — 本报告（含交互式图表，需联网加载图表库）</li>
  </ul>
</div>
</body></html>`
    await writeTextFile(dir + '/perf_report.html', html)

    showToast('报告已导出到:\n' + dir)
  } catch (e: any) {
    showToast('导出失败: ' + (e?.message ?? String(e)), true)
  } finally {
    isExporting.value = false
  }
}

// Build interactive chart HTML section that embeds chart data as JSON and
// renders 4 ECharts charts (loaded from CDN) with clickable legend to
// toggle individual series on/off. Falls back gracefully if offline.
function buildInteractiveChartsHtml(
  pts: any[],
  topMem: { name: string; data: { time: number; pssKb: number }[] }[],
  topCpu: { name: string; data: { time: number; cpuPercent: number }[] }[],
  singleName: string,
  singleData: { time: number; pssKb: number }[],
): string {
  // Compact JSON for embedding
  const memSeries = [
    { name: '已用', data: pts.map(p => [p.time, p.memUsedKb] as [number, number]) },
    { name: '可用', data: pts.map(p => [p.time, p.memAvailKb] as [number, number]) },
  ]
  const cpuSeries = topCpu.map(p => ({
    name: p.name,
    data: p.data.map(d => [d.time, d.cpuPercent] as [number, number]),
  }))
  const topSeries = topMem.map(p => ({
    name: p.name,
    data: p.data.map(d => [d.time, d.pssKb] as [number, number]),
  }))
  const singleSeries = singleData.length > 0 ? [{
    name: singleName,
    data: singleData.map(d => [d.time, d.pssKb] as [number, number]),
  }] : []

  const colors = ['#7c5cfc', '#22c55e', '#f59e0b', '#ef4444', '#3b82f6', '#ec4899', '#14b8a6', '#f97316', '#8b5cf6', '#06b6d4']
  const jsonStr = (v: any) => JSON.stringify(v).replace(/</g, '\\u003c')

  return `
<div class="card">
  <h2>交互式图表</h2>
  <p style="font-size:.85rem;color:#666;margin-bottom:.5rem">点击图例可显示/隐藏单个应用。需要联网加载图表库。</p>
  <div id="chart-loading" style="padding:2rem;text-align:center;color:#888;font-size:.9rem">正在加载图表库...</div>
  <div id="charts-container" style="display:none">
    <div class="interactive-chart"><h3>设备内存趋势</h3><div id="ic-mem" style="width:100%;height:360px"></div></div>
    <div class="interactive-chart"><h3>Top ${topCpu.length} 应用 CPU 使用率</h3><div id="ic-cpu" style="width:100%;height:360px"></div></div>
    <div class="interactive-chart"><h3>Top ${topMem.length} 应用内存</h3><div id="ic-top" style="width:100%;height:360px"></div></div>
    <div class="interactive-chart"><h3>单个应用内存: ${singleName || '(未选择)'}</h3><div id="ic-single" style="width:100%;height:360px"></div></div>
  </div>
  <script type="application/json" id="ic-data">${jsonStr({
    mem: memSeries, cpu: cpuSeries, top: topSeries, single: singleSeries,
    colors,
  })}<\/script>
  <script>
  (function() {
    function loadScript(src, onLoad, onError) {
      var s = document.createElement('script');
      s.src = src; s.async = true;
      s.onload = onLoad; s.onerror = onError;
      document.head.appendChild(s);
    }
    function render() {
      var el = document.getElementById('ic-data');
      if (!el) return;
      var data;
      try { data = JSON.parse(el.textContent); } catch(e) { return; }
      var opts = {
        tooltip: { trigger: 'axis', confine: true },
        legend: {
          type: 'scroll', orient: 'vertical', right: 0, top: 'middle',
          icon: 'circle', itemWidth: 14, itemHeight: 14,
          textStyle: { fontSize: 13, width: 200, overflow: 'truncate' },
          pageTextStyle: { fontSize: 13 }, pageIconSize: 14,
        },
        grid: { left: 60, right: 220, top: 15, bottom: 40 },
        xAxis: {
          type: 'time',
          axisLabel: {
            fontSize: 11,
            hideOverlap: true,
            formatter: function(value) {
              var d = new Date(value);
              if (isNaN(d.getTime())) return '';
              var pad = function(n) { return n < 10 ? '0' + n : '' + n; };
              // Determine if data spans multiple days by checking all series
              var allT = [];
              ['mem','cpu','top','single'].forEach(function(k) {
                (data[k] || []).forEach(function(s) {
                  (s.data || []).forEach(function(p) { allT.push(p[0]); });
                });
              });
              if (allT.length >= 2) {
                var minT = Math.min.apply(null, allT);
                var maxT = Math.max.apply(null, allT);
                if (new Date(minT).toDateString() !== new Date(maxT).toDateString()) {
                  return pad(d.getMonth()+1) + '-' + pad(d.getDate()) + ' ' + pad(d.getHours()) + ':' + pad(d.getMinutes());
                }
              }
              return pad(d.getHours()) + ':' + pad(d.getMinutes()) + ':' + pad(d.getSeconds());
            }
          }
        },
        yAxis: { type: 'value', axisLabel: { fontSize: 11 } },
        dataZoom: [{ type: 'inside', start: 0, end: 100 }],
        color: data.colors,
        animationDuration: 300,
      };
      function mk(series, yFmt, valFmt) {
        return Object.assign({}, opts, {
          yAxis: Object.assign({}, opts.yAxis, { axisLabel: Object.assign({}, opts.yAxis.axisLabel, { formatter: yFmt }) }),
          tooltip: Object.assign({}, opts.tooltip, { valueFormatter: valFmt }),
          series: series.map(function(s) {
            return { type: 'line', name: s.name, data: s.data, smooth: true, symbol: 'none', lineStyle: { width: 1.5 } };
          }),
        });
      }
      var KB = 1048576;
      function fmtKb(v) { return v >= KB ? (v / KB).toFixed(2) + ' GB' : (v / 1024).toFixed(0) + ' MB'; }
      echarts.init(document.getElementById('ic-mem')).setOption(mk(data.mem,
        function(v) { return v >= KB ? (v / KB).toFixed(0) + 'G' : (v / 1024).toFixed(0) + 'M'; },
        function(v) { return fmtKb(v); }));
      echarts.init(document.getElementById('ic-cpu')).setOption(mk(data.cpu,
        function(v) { return v + '%'; },
        function(v) { return v.toFixed(1) + '%'; }));
      echarts.init(document.getElementById('ic-top')).setOption(mk(data.top,
        function(v) { return v >= 1024 ? (v / 1024).toFixed(0) + 'M' : v + 'K'; },
        function(v) { return fmtKb(v); }));
      echarts.init(document.getElementById('ic-single')).setOption(mk(data.single,
        function(v) { return v >= 1024 ? (v / 1024).toFixed(0) + 'M' : v + 'K'; },
        function(v) { return fmtKb(v); }));
      window.addEventListener('resize', function() {
        ['ic-mem','ic-cpu','ic-top','ic-single'].forEach(function(id) {
          var inst = echarts.getInstanceByDom(document.getElementById(id));
          if (inst) inst.resize();
        });
      });
    }
    // Try CDN, then fallback
    loadScript('https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js', function() {
      document.getElementById('chart-loading').style.display = 'none';
      document.getElementById('charts-container').style.display = 'block';
      render();
    }, function() {
      // Fallback: try another CDN
      loadScript('https://cdn.bootcdn.net/ajax/libs/echarts/5.4.3/echarts.min.js', function() {
        document.getElementById('chart-loading').style.display = 'none';
        document.getElementById('charts-container').style.display = 'block';
        render();
      }, function() {
        document.getElementById('chart-loading').innerHTML = '<div style="color:#c00">⚠️ 图表库加载失败，请联网后重新打开本报告查看交互式图表。静态 PNG 图片在上方折线图区块。</div>';
      });
    });
  })();
  <\/script>
</div>
`
}

// Capture one-time logs at start / stop. Always merges into the same anr/tombstone
// directory (no _final suffix) so logs accumulate instead of being split.
async function captureOneTimeLogs(serial: string) {
  if (!sessionLogDir.value) return

  // versionInfo (only captured once — skip on subsequent calls)
  try {
    const versionInfo = await shell(serial, 'getprop 2>/dev/null') + '\n---\n' + await shell(serial, 'cat /proc/version 2>/dev/null')
    await writeTextFile(sessionLogDir.value + 'versionInfo.txt', versionInfo)
  } catch {}

  // anr — single merged directory
  try {
    const anrDir = sessionLogDir.value + 'anr/'
    await mkdir(anrDir, { recursive: true })
    const listing = await shell(serial, 'ls -1 /data/anr/ 2>/dev/null')
    const files = listing.split('\n').map(f => f.trim()).filter(f => f && !f.includes(' '))
    for (const file of files) {
      try { await pullFile(serial, '/data/anr/' + file, anrDir + file) } catch {}
    }
  } catch {}

  // tombstone — single merged directory
  try {
    const tombDir = sessionLogDir.value + 'tombstone/'
    await mkdir(tombDir, { recursive: true })
    const listing = await shell(serial, 'ls -1 /data/tombstones/ 2>/dev/null')
    const files = listing.split('\n').map(f => f.trim()).filter(f => f && !f.includes(' '))
    for (const file of files) {
      try { await pullFile(serial, '/data/tombstones/' + file, tombDir + file) } catch {}
    }
  } catch {}

  // Extra one-time logs
  try { await writeTextFile(sessionLogDir.value + 'dmesg.txt', await dmesg(serial)) } catch {}
  try { await writeTextFile(sessionLogDir.value + 'ps.txt', await shell(serial, 'ps -A 2>/dev/null')) } catch {}
  try { await writeTextFile(sessionLogDir.value + 'df.txt', await shell(serial, 'df 2>/dev/null')) } catch {}
  try { await writeTextFile(sessionLogDir.value + 'battery.txt', await shell(serial, 'dumpsys battery 2>/dev/null')) } catch {}
  try { await writeTextFile(sessionLogDir.value + 'proc_stat.txt', await shell(serial, 'cat /proc/stat 2>/dev/null')) } catch {}
}

// Periodic meminfo collection
async function collectLogs(serial: string) {
  if (!serial || !sessionLogDir.value) return
  try {
    const ts = new Date().toISOString().replace(/[:.]/g, '-')
    const memDir = sessionLogDir.value + 'meminfo/'
    try { await mkdir(memDir, { recursive: true }) } catch {}
    const meminfo = await shell(serial, 'cat /proc/meminfo 2>/dev/null')
    await writeTextFile(memDir + 'meminfo_' + ts + '.txt', meminfo)
  } catch {}
}

function goBack() { router.push('/device-space') }

let pollErrorCount = 0
async function pollOnce() {
  if (!deviceSerial.value) return
  try {
    const snap = await getSnapshot(deviceSerial.value, store.singleAppName || undefined)
    pollErrorCount = 0
    store.addPoint(snap)
    bufferCsvPoint(snap)
    flushCsvBuffer()
    // Skip chart rendering when page is deactivated (user on another page).
    // Data still collects in the store; charts update when user returns.
    if (isPageActive.value) {
      updateCharts()
      updateTopAppChart()
      updateSingleAppChart()
    }
  } catch (e: any) {
    pollErrorCount++
    if (pollErrorCount >= 3) {
      showToast('ADB 连接异常，已连续失败 ' + pollErrorCount + ' 次，请检查设备连接', true)
    }
    if (pollErrorCount >= 10) {
      showToast('ADB 连接持续失败，自动停止监控', true)
      stopPolling()
    }
  }
}

function toggleCollect() {
  store.isCollecting ? stopPolling() : startPolling()
}

// --- Streaming CSV buffer ---
// During long-running monitoring (hours/days), we stream data to CSV files on
// disk incrementally instead of building the entire CSV in memory at export time.
// This prevents memory bloat and ensures data survives even if the app crashes.
let csvBuffer: string[] = []
const CSV_FLUSH_THRESHOLD = 30 // flush after every 30 data points
let csvBaseDir = ''
let csvHasProcs = false

function initCsvFiles(dir: string, hasProcs: boolean) {
  csvBaseDir = dir
  csvHasProcs = hasProcs
  csvBuffer = []
  // Write headers immediately (overwrite any existing file)
  try {
    invoke('write_text_file', { path: dir + '/perf_data.csv', content: 'Time,CPU(%),MemUsed(KB),MemTotal(KB),MemAvail(KB),ZRAM(KB),StorageUsed(KB),StorageTotal(KB)\n' })
  } catch {}
}

function bufferCsvPoint(snap: PerfSnapshot) {
  const now = new Date()
  const row = `${now.toISOString()},${snap.cpu_total.toFixed(1)},${snap.mem_total_kb - snap.mem_free_kb},${snap.mem_total_kb},${snap.mem_avail_kb},${snap.zram_total_kb},${snap.storage_used_kb},${snap.storage_total_kb}`
  csvBuffer.push(row)
  if (csvBuffer.length >= CSV_FLUSH_THRESHOLD) {
    flushCsvBuffer()
  }
}

async function flushCsvBuffer() {
  if (csvBuffer.length === 0 || !csvBaseDir) return
  const data = csvBuffer.join('\n') + '\n'
  csvBuffer = []
  try {
    await invoke('append_text_file', { path: csvBaseDir + '/perf_data.csv', content: data })
  } catch {}
}

async function startPolling() {
  const serial = deviceSerial.value
  if (!serial) return

  // 0. Clear existing history and error count
  clearHistory()
  pollErrorCount = 0

  // 1. Let user choose save directory
  const chosenDir = await open({ directory: true, multiple: false, title: '选择日志保存目录' })
  if (!chosenDir) return

  // 2. adb root first to get full data access
  try {
    const result = await rootDevice(serial)
    if (result) showToast('adb root: ' + result)
  } catch {}

  // 3. Create session log dir
  const ts = new Date().toISOString().replace(/[:.]/g, '-')
  sessionLogDir.value = chosenDir + '/TestSpace_Perf_' + ts + '/'
  try { await mkdir(sessionLogDir.value, { recursive: true }) } catch {}

  // 3.5. Initialize streaming CSV files with headers
  initCsvFiles(sessionLogDir.value, true)

  // 4. Clear logcat buffer and start streaming logcat to file
  try { await shell(serial, 'logcat -c 2>/dev/null') } catch {}
  try {
    await invoke('adb_logcat_start', { serial, filePath: sessionLogDir.value + 'logcat.txt' })
  } catch (e) {
    showToast('启动 logcat 流式抓取失败: ' + String(e), true)
  }

  // 5. Capture one-time logs
  await captureOneTimeLogs(serial)

  // 6. Start polling immediately
  store.setCollecting(true)
  pollOnce()
  pollTimer = setInterval(pollOnce, store.intervalMs)

  // 7. Start periodic meminfo collection (first after 5s, then every 30s)
  setTimeout(() => collectLogs(serial), 5000)
  logTimer = setInterval(() => collectLogs(serial), 30000)
}
async function stopPolling() {
  // Show loading overlay immediately on pause — before any async work
  store.setCollecting(false)
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
  if (logTimer) { clearInterval(logTimer); logTimer = null }

  // Skip everything if no data collected
  if (store.history.length === 0) {
    showToast('未采集到数据，跳过自动导出')
    return
  }

  isExporting.value = true
  // Timeout safeguard: if export hangs for >60s, force-hide loading
  const exportTimeout = setTimeout(() => {
    if (isExporting.value) {
      isExporting.value = false
      showToast('导出超时，请重试手动导出', true)
    }
  }, 60000)

  try {
    // Flush any remaining CSV buffer to disk
    await flushCsvBuffer()

    // Stop logcat stream
    if (deviceSerial.value) {
      try { await invoke('adb_logcat_stop', { serial: deviceSerial.value }) } catch {}
    }

    // Final logs
    if (deviceSerial.value && sessionLogDir.value) {
      try {
        await collectLogs(deviceSerial.value)
        await captureOneTimeLogs(deviceSerial.value)
      } catch {}
    }

    // Auto export report to session dir
    if (sessionLogDir.value) {
      await autoExportReport(sessionLogDir.value)
    }
  } catch (e: any) {
    showToast('导出失败: ' + (e?.message ?? String(e)), true)
  } finally {
    clearTimeout(exportTimeout)
    isExporting.value = false
  }
}

async function autoExportReport(dir: string) {
  const pts = store.history
  if (pts.length === 0) return
  try {
    const cpus = pts.map(p => p.cpu)
    const memUsed = pts.map(p => p.memUsedKb)
    const memAvail = pts.map(p => p.memAvailKb)
    const avgCpu = cpus.reduce((a, b) => a + b, 0) / cpus.length
    const maxCpu = safeMax(cpus)
    const avgMemUsed = memUsed.reduce((a, b) => a + b, 0) / memUsed.length
    const maxMemUsed = safeMax(memUsed)
    const avgMemAvail = memAvail.reduce((a, b) => a + b, 0) / memAvail.length

    const pssHist = store.processPssHistory
    const cpuHist = store.processCpuHistory

    const topMem = Array.from(pssHist.entries())
      .map(([name, data]) => ({ name, lastPss: data[data.length - 1]?.pssKb ?? 0, data }))
      .sort((a, b) => b.lastPss - a.lastPss)
      .slice(0, store.topAppCount)
    const topCpu = Array.from(cpuHist.entries())
      .map(([name, data]) => ({ name, lastCpu: data[data.length - 1]?.cpuPercent ?? 0, data }))
      .sort((a, b) => b.lastCpu - a.lastCpu)
      .slice(0, store.cpuTopNCount)

    const topNames = topMem.map(p => p.name)
    const singleName = store.singleAppName
    const singleData = singleName ? (pssHist.get(singleName) || []) : []

    // perf_data.csv already streamed to disk during collection — flush remaining buffer first
    await flushCsvBuffer()

    if (topMem.length > 0) {
      const maxLen = safeMax(topMem.map(p => p.data.length))
      const rows = []
      for (let i = 0; i < maxLen; i++) {
        const t = i < topMem[0].data.length ? new Date(topMem[0].data[i].time).toISOString() : ''
        const vals = topMem.map(p => i < p.data.length ? p.data[i].pssKb.toString() : '')
        rows.push(t + ',' + vals.join(','))
      }
      await writeTextFile(dir + 'perf_top_apps.csv', 'Time,' + topNames.map(n => `"${n}(KB)"`).join(',') + '\n' + rows.join('\n'))
    }

    if (topCpu.length > 0) {
      const maxLen = safeMax(topCpu.map(p => p.data.length))
      const rows = []
      for (let i = 0; i < maxLen; i++) {
        const t = i < topCpu[0].data.length ? new Date(topCpu[0].data[i].time).toISOString() : ''
        const vals = topCpu.map(p => i < p.data.length ? p.data[i].cpuPercent.toFixed(1) : '')
        rows.push(t + ',' + vals.join(','))
      }
      await writeTextFile(dir + 'perf_top_cpu.csv', 'Time,' + topCpu.map(p => `"${p.name}(%)"`).join(',') + '\n' + rows.join('\n'))
    }

    if (singleData.length > 0) {
      await writeTextFile(dir + 'perf_single_app.csv', 'Time,PSS(KB)\n' + singleData.map(d => `${new Date(d.time).toISOString()},${d.pssKb}`).join('\n'))
    }

    // Downsample for interactive HTML charts to keep file size manageable
    const DOWNSAMPLE_MAX = 2000
    const dsPts = downsample(pts, DOWNSAMPLE_MAX)
    const dsTopMem = topMem.map(p => ({ ...p, data: downsample(p.data, DOWNSAMPLE_MAX) }))
    const dsTopCpu = topCpu.map(p => ({ ...p, data: downsample(p.data, DOWNSAMPLE_MAX) }))
    const dsSingleData = downsample(singleData, DOWNSAMPLE_MAX)
    const interactiveHtml = buildInteractiveChartsHtml(dsPts, dsTopMem, dsTopCpu, singleName || '', dsSingleData)
    await writeTextFile(dir + 'perf_report.html', `<!DOCTYPE html>
<html lang="zh">
<head><meta charset="utf-8"><title>性能报告</title>
<style>
body{font-family:system-ui,-apple-system,sans-serif;max-width:1100px;margin:auto;padding:2rem;background:#f5f5f5;color:#222}
h1{color:#333;border-bottom:2px solid #7c5cfc;padding-bottom:.5rem}
h2{color:#444;margin-top:1.5rem}
table{border-collapse:collapse;width:100%;margin:1rem 0;font-size:.85rem}
th,td{padding:.35rem .5rem;text-align:left;border-bottom:1px solid #ddd}
th{background:#7c5cfc;color:#fff;font-weight:600;position:sticky;top:0}
td{font-variant-numeric:tabular-nums}
.card{background:#fff;border-radius:12px;padding:1.2rem;margin:1rem 0;box-shadow:0 2px 8px rgba(0,0,0,.08)}
.card-title{font-size:1.1rem;font-weight:600;color:#444;margin-bottom:.8rem;padding-bottom:.4rem;border-bottom:1px solid #eee}
.stat-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:.8rem}
.stat{background:#f0eeff;border-radius:8px;padding:.8rem}
.stat-label{font-size:.7rem;color:#888}
.stat-value{font-size:1.1rem;font-weight:700;color:#222;margin-top:.2rem}
code{background:#eee;padding:.1em .3em;border-radius:3px;font-size:.85em}
img.chart{max-width:100%;border:1px solid #ddd;border-radius:8px;margin:.5rem 0}
.interactive-chart{background:#fafafa;border:1px solid #e5e5e5;border-radius:8px;padding:1rem;margin:1rem 0}
.interactive-chart h3{color:#444;font-size:1rem;margin:0 0 .5rem 0}
</style></head>
<body>
<h1>📊 性能监控报告</h1>
<div class="card">
  <h2>采集信息</h2>
  <p><strong>设备:</strong> ${deviceSerial.value || 'N/A'}</p>
  <p><strong>采样数:</strong> ${pts.length}</p>
  <p><strong>时间范围:</strong> ${new Date(pts[0].time).toISOString()} ~ ${new Date(pts[pts.length-1].time).toISOString()}</p>
  <p><strong>采集间隔:</strong> ${store.intervalMs}ms</p>
  <p><strong>报告目录:</strong> ${dir}</p>
</div>
${buildOverallAssessment(pts, topMem, topCpu, singleName || '', singleData)}
<div class="card">
  <h2>汇总统计</h2>
  <div class="stat-grid">
    <div class="stat"><div class="stat-label">CPU 平均</div><div class="stat-value">${avgCpu.toFixed(1)}%</div></div>
    <div class="stat"><div class="stat-label">CPU 峰值</div><div class="stat-value">${maxCpu.toFixed(1)}%</div></div>
    <div class="stat"><div class="stat-label">内存已用平均</div><div class="stat-value">${formatKb(avgMemUsed)} ${formatKbUnit(avgMemUsed)}</div></div>
    <div class="stat"><div class="stat-label">内存已用峰值</div><div class="stat-value">${formatKb(maxMemUsed)} ${formatKbUnit(maxMemUsed)}</div></div>
    <div class="stat"><div class="stat-label">内存平均剩余</div><div class="stat-value">${formatKb(avgMemAvail)} ${formatKbUnit(avgMemAvail)}</div></div>
  </div>
</div>
<div class="card">
  <h2>Top${store.topAppCount} 应用内存使用情况</h2>
  <table><thead><tr><th>#</th><th>应用包名</th><th>最小 PSS</th><th>最大 PSS</th><th>平均 PSS</th></tr></thead>
  <tbody>${topMem.map((p, i) => {
    const vals = p.data.map(d => d.pssKb)
    const mn = vals.length ? safeMin(vals) : 0
    const mx = vals.length ? safeMax(vals) : 0
    const av = vals.length ? safeAvg(vals) : 0
    return `<tr><td>${i+1}</td><td>${p.name}</td><td>${formatKb(mn)} ${formatKbUnit(mn)}</td><td>${formatKb(mx)} ${formatKbUnit(mx)}</td><td>${formatKb(av)} ${formatKbUnit(av)}</td></tr>`
  }).join('')}</tbody></table>
</div>
<div class="card">
  <h2>Top${store.cpuTopNCount} 应用 CPU 使用情况</h2>
  <table><thead><tr><th>#</th><th>应用包名</th><th>最小 CPU%</th><th>最大 CPU%</th><th>平均 CPU%</th></tr></thead>
  <tbody>${topCpu.map((p, i) => {
    const vals = p.data.map(d => d.cpuPercent)
    const mn = vals.length ? safeMin(vals) : 0
    const mx = vals.length ? safeMax(vals) : 0
    const av = vals.length ? safeAvg(vals) : 0
    return `<tr><td>${i+1}</td><td>${p.name}</td><td>${mn.toFixed(1)}%</td><td>${mx.toFixed(1)}%</td><td>${av.toFixed(1)}%</td></tr>`
  }).join('')}</tbody></table>
</div>
<div class="card">
  <h2>单个应用内存使用情况: ${singleName || '(未选择)'}</h2>
  ${singleData.length ? (() => {
    const vals = singleData.map(d => d.pssKb)
    const mn = safeMin(vals); const mx = safeMax(vals); const av = safeAvg(vals)
    return `<table><thead><tr><th>最小 PSS</th><th>最大 PSS</th><th>平均 PSS</th><th>采样数</th></tr></thead>
      <tbody><tr><td>${formatKb(mn)} ${formatKbUnit(mn)}</td><td>${formatKb(mx)} ${formatKbUnit(mx)}</td><td>${formatKb(av)} ${formatKbUnit(av)}</td><td>${singleData.length}</td></tr></tbody></table>`
  })() : '<p>暂无数据</p>'}
</div>
${interactiveHtml}
<div class="card">
  <h2>导出文件清单</h2>
  <ul>
    <li><code>perf_data.csv</code> — CPU/内存/存储 时序数据</li>
    <li><code>perf_top_apps.csv</code> — Top N 应用 PSS 时序数据</li>
    <li><code>perf_top_cpu.csv</code> — Top N 应用 CPU 时序数据</li>
    <li><code>perf_single_app.csv</code> — 单个应用 PSS 时序数据</li>
    <li><code>perf_report.html</code> — 本报告（含交互式图表，需联网加载图表库）</li>
  </ul>
</div>
</body></html>`,)

    showToast('报告已自动导出到:\n' + dir)
  } catch (e: any) {
    showToast('自动导出失败: ' + (e?.message ?? String(e)), true)
  }
}

function clearHistory() {
  store.clearHistory()
  cpuHiddenApps.value = new Set()
  topAppHiddenApps.value = new Set()
  cpuChart?.setOption({ series: [] }, { replaceMerge: ['series'] })
  memChart?.setOption({ series: [{ data: [] }, { data: [] }] })
  topAppChart?.setOption({ series: [] }, { replaceMerge: ['series'] })
  singleAppChart?.setOption({ series: [{ data: [] }] })
}

// Watch topAppCount changes to re-render chart
watch(() => store.topAppCount, () => { updateTopAppChart() })
watch(() => store.cpuTopNCount, () => { updateCpuChart() })
watch(() => store.singleAppName, () => { updateSingleAppChart(); if (store.singleAppName) appSearch.value = store.singleAppName })

function initCharts() {
  const chartColors = ['#7c5cfc', '#22c55e', '#f59e0b', '#ef4444', '#3b82f6', '#ec4899', '#14b8a6', '#f97316', '#8b5cf6', '#06b6d4']

  // xAxis time formatter: shows date when data spans multiple days, otherwise just HH:MM:SS.
  // ECharts axisLabel.formatter receives (value, index) — value is the timestamp (number) for time axis.
  // hideOverlap prevents labels from crowding/overlapping when there are many ticks.
  const timeAxisLabel = {
    fontSize: 10,
    hideOverlap: true,
    formatter: (value: any) => {
      const d = new Date(value)
      if (isNaN(d.getTime())) return ''
      const pts = store.history
      if (pts.length >= 2) {
        const minT = pts[0].time
        const maxT = pts[pts.length - 1].time
        const minDay = new Date(minT).toDateString()
        const maxDay = new Date(maxT).toDateString()
        if (minDay !== maxDay) {
          // Spans multiple days — show MM-DD HH:MM
          return `${(d.getMonth()+1).toString().padStart(2,'0')}-${d.getDate().toString().padStart(2,'0')} ${d.getHours().toString().padStart(2,'0')}:${d.getMinutes().toString().padStart(2,'0')}`
        }
      }
      // Same day — show HH:MM:SS
      return `${d.getHours().toString().padStart(2,'0')}:${d.getMinutes().toString().padStart(2,'0')}:${d.getSeconds().toString().padStart(2,'0')}`
    },
  }

  // Tooltip position factory: returns a position function that accounts for the
  // chart container's actual position in the viewport. ECharts position functions
  // return coordinates relative to the chart container, and when appendTo: 'body'
  // is used, ECharts adds the container's offset on top. For charts located in
  // the lower half of the window (like TopApp in the 2x2 grid bottom-left), a
  // y=8 return value can still place the tooltip beyond the window bottom because
  // container_top + 8 + tooltip_height > window_height.
  //
  // This factory uses getBoundingClientRect() to compute the container's real
  // viewport position and clamps the tooltip within the visible window area.
  const makeTooltipPosition = (containerRef: any) => {
    return (point: number[], _params: any, _dom: any, _rect: any, size: any) => {
      const tipHeight = (size?.contentSize?.[1] ?? 0) as number
      const mouseX = point[0]
      const mouseY = point[1]
      const winHeight = window.innerHeight

      const containerEl = containerRef?.value
      const containerRect = containerEl?.getBoundingClientRect?.()
      if (!containerRect) {
        // Fallback: show above cursor
        return [mouseX, Math.max(8, mouseY - tipHeight - 12)]
      }

      // Mouse Y in viewport coordinates
      const mouseClientY = containerRect.top + mouseY

      // Prefer above the cursor
      let topClient = mouseClientY - tipHeight - 12
      if (topClient < 8) {
        // Not enough room above — pin to window top
        topClient = 8
      }
      // If still exceeds window bottom, clamp to window bottom
      if (topClient + tipHeight > winHeight - 8) {
        topClient = winHeight - 8 - tipHeight
        if (topClient < 8) topClient = 8
      }

      // Convert back to container-relative Y
      const topRel = topClient - containerRect.top
      return [mouseX, topRel]
    }
  }

  if (cpuChartRef.value && !cpuChart) {
    cpuChart = echarts.init(cpuChartRef.value)
    cpuChart.setOption({
      grid: { left: 45, right: 12, top: 15, bottom: 25 },
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'cross', label: { show: false } },
        confine: true,
        appendTo: 'body' as any,
        position: makeTooltipPosition(cpuChartRef),
        formatter: (params: any) => {
          if (!Array.isArray(params) || params.length === 0) return ''
          const time = new Date(params[0].axisValue).toLocaleTimeString('zh-CN', { hour12: false })
          const getVal = (p: any): number | null => {
            if (p.value == null) return null
            return Array.isArray(p.value) ? p.value[1] : p.value
          }
          const sorted = params
            .map((p: any) => ({ p, v: getVal(p) }))
            .filter((x: any) => x.v != null && x.v >= 0)
            .sort((a: any, b: any) => (b.v ?? 0) - (a.v ?? 0))
          const lines = sorted.map((x: any) => {
            const v = (x.v as number).toFixed(1)
            return `${x.p.marker} ${x.p.seriesName}: <b>${v}%</b>`
          })
          return `<div style="max-height:60vh;overflow-y:auto"><div style="font-weight:600;margin-bottom:4px">${time}</div>${lines.join('<br>')}</div>`
        },
      },
      legend: { show: false },
      xAxis: { type: 'time', axisLabel: timeAxisLabel },
      yAxis: { type: 'value', min: 0, max: 100, axisLabel: { fontSize: 10, formatter: '{value}%' } },
      dataZoom: [{ type: 'inside', start: 0, end: 100 }],
      series: [],
      color: chartColors,
    })
  }
  if (memChartRef.value && !memChart) {
    memChart = echarts.init(memChartRef.value)
    memChart.setOption({
      grid: { left: 45, right: 12, top: 5, bottom: 25 },
      tooltip: { trigger: 'axis',
        axisPointer: { type: 'cross', label: { show: false } },
        valueFormatter: (v: any) => formatMem(v as number) },
      legend: { show: false },
      xAxis: { type: 'time', axisLabel: timeAxisLabel },
      yAxis: { type: 'value', axisLabel: { fontSize: 10, formatter: (v: number) => v >= 1048576 ? (v / 1048576).toFixed(1) + 'G' : v >= 1024 ? (v / 1024).toFixed(0) + 'M' : v + 'K' } },
      dataZoom: [{ type: 'inside', start: 0, end: 100 }],
      series: [
        { type: 'line', name: t('perf.used'), data: [], smooth: true, symbol: 'none', lineStyle: { width: 2, color: '#7c5cfc' }, areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(124,92,252,0.25)' }, { offset: 1, color: 'rgba(124,92,252,0.02)' }]) }, animationDuration: 300 },
        { type: 'line', name: t('perf.free'), data: [], smooth: true, symbol: 'none', lineStyle: { width: 2, color: '#22c55e' }, areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(34,197,94,0.2)' }, { offset: 1, color: 'rgba(34,197,94,0.02)' }]) }, animationDuration: 300 },
      ],
    })
  }
  if (topAppChartRef.value && !topAppChart) {
    topAppChart = echarts.init(topAppChartRef.value)
    topAppChart.setOption({
      grid: { left: 5, right: 5, top: 15, bottom: 25 },
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'cross', label: { show: false } },
        confine: true,
        appendTo: 'body' as any,
        position: makeTooltipPosition(topAppChartRef),
        formatter: (params: any) => {
          if (!Array.isArray(params) || params.length === 0) return ''
          const time = new Date(params[0].axisValue).toLocaleTimeString('zh-CN', { hour12: false })
          const getVal = (p: any): number | null => {
            if (p.value == null) return null
            return Array.isArray(p.value) ? p.value[1] : p.value
          }
          const sorted = params
            .map((p: any) => ({ p, v: getVal(p) }))
            .filter((x: any) => x.v != null && x.v >= 0)
            .sort((a: any, b: any) => (b.v ?? 0) - (a.v ?? 0))
          const lines = sorted.map((x: any) => {
            const v = x.v as number
            const vstr = v >= 1024 ? (v / 1024).toFixed(1) + 'MB' : v + 'KB'
            return `${x.p.marker} ${x.p.seriesName}: <b>${vstr}</b>`
          })
          return `<div style="max-height:60vh;overflow-y:auto"><div style="font-weight:600;margin-bottom:4px">${time}</div>${lines.join('<br>')}</div>`
        },
      },
      legend: { show: false },
      xAxis: { type: 'time', axisLabel: { ...timeAxisLabel, fontSize: 8 } },
      yAxis: { type: 'value', axisLabel: { fontSize: 8, formatter: (v: number) => v >= 1024 ? (v / 1024).toFixed(0) + 'M' : v + 'K' } },
      dataZoom: [{ type: 'inside', start: 0, end: 100 }],
      series: [],
      color: chartColors,
      animationDuration: 300,
    })
  }
  if (singleAppChartRef.value && !singleAppChart) {
    singleAppChart = echarts.init(singleAppChartRef.value)
    singleAppChart.setOption({
      grid: { left: 45, right: 12, top: 5, bottom: 25 },
      tooltip: { trigger: 'axis',
        axisPointer: { type: 'cross', label: { show: false } },
        valueFormatter: (v: any) => (v as number) >= 1024 ? ((v as number) / 1024).toFixed(1) + 'MB' : (v as number) + 'KB' },
      xAxis: { type: 'time', axisLabel: timeAxisLabel },
      yAxis: { type: 'value', axisLabel: { fontSize: 10, formatter: (v: number) => v >= 1024 ? (v / 1024).toFixed(0) + 'M' : v + 'K' } },
      dataZoom: [{ type: 'inside', start: 0, end: 100 }],
      series: [{ type: 'line', name: '', data: [], smooth: true, symbol: 'none', lineStyle: { width: 2, color: '#7c5cfc' }, areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(124,92,252,0.25)' }, { offset: 1, color: 'rgba(124,92,252,0.02)' }]) }, animationDuration: 300 }],
    })
  }
}

function updateCharts() {
  if (!memChart) return
  const pts = store.history
  if (pts.length === 0) return
  memChart.setOption({ series: [
    { data: pts.map(p => [p.time, p.memUsedKb] as [number, number]) },
    { data: pts.map(p => [p.time, p.memAvailKb] as [number, number]) },
  ]})
  updateCpuChart()
}

function updateCpuChart() {
  if (!cpuChart) return
  const hist = store.processCpuHistory
  if (hist.size === 0) {
    cpuChart.setOption({ series: [] }, { replaceMerge: ['series'] })
    return
  }

  // Sort by last CPU value descending, filter out hidden apps first, then take top N.
  // Filtering BEFORE slice ensures hidden apps don't waste Top N slots, so the
  // Top N highest visible apps always show and a new higher-usage app pushes out
  // the lowest visible one.
  const topN = Array.from(hist.entries())
    .map(([name, data]) => ({
      name,
      lastCpu: data[data.length - 1]?.cpuPercent ?? 0,
      data,
    }))
    .sort((a, b) => b.lastCpu - a.lastCpu)
    .filter(p => !cpuHiddenApps.value.has(p.name))
    .slice(0, store.cpuTopNCount)

  if (topN.length === 0) {
    cpuChart.setOption({ series: [] }, { replaceMerge: ['series'] })
    return
  }

  // Rebuild series completely each time — replaceMerge removes dropped apps automatically
  const series = topN.map(p => ({
    type: 'line',
    name: p.name,
    data: p.data.map(h => [h.time, h.cpuPercent] as [number, number]),
    smooth: true,
    symbol: 'none',
    lineStyle: { width: 1.5 },
    animation: false,
  }))

  cpuChart.setOption({ series }, { replaceMerge: ['series'] })
}

function updateTopAppChart() {
  if (!topAppChart) return
  const hist = store.processPssHistory
  if (hist.size === 0) {
    topAppChart.setOption({ series: [] }, { replaceMerge: ['series'] })
    return
  }

  // Sort by last PSS value descending, filter out hidden apps first, then take top N.
  // Filtering BEFORE slice ensures hidden apps don't waste Top N slots, so the
  // Top N highest visible apps always show and a new higher-usage app pushes out
  // the lowest visible one.
  const topN = Array.from(hist.entries())
    .map(([name, data]) => ({
      name,
      lastPss: data[data.length - 1]?.pssKb ?? 0,
      data,
    }))
    .sort((a, b) => b.lastPss - a.lastPss)
    .filter(p => !topAppHiddenApps.value.has(p.name))
    .slice(0, store.topAppCount)

  if (topN.length === 0) {
    topAppChart.setOption({ series: [] }, { replaceMerge: ['series'] })
    return
  }

  // Rebuild series completely each time — replaceMerge removes dropped apps automatically
  const series = topN.map(p => ({
    type: 'line',
    name: p.name,
    data: p.data.map(h => [h.time, h.pssKb] as [number, number]),
    smooth: true,
    symbol: 'none',
    lineStyle: { width: 1.5 },
    animation: false,
  }))

  topAppChart.setOption({ series }, { replaceMerge: ['series'] })
}

function updateSingleAppChart() {
  if (!singleAppChart) return
  const name = store.singleAppName
  if (!name) { singleAppChart.setOption({ series: [{ data: [] }] }); return }

  const hist = store.processPssHistory.get(name)
  if (!hist || hist.length === 0) { singleAppChart.setOption({ series: [{ data: [] }] }); return }

  singleAppChart.setOption({
    series: [{
      name: name,
      data: hist.map(h => [h.time, h.pssKb] as [number, number]),
    }],
  })
}

function resizeCharts() {
  cpuChart?.resize(); memChart?.resize(); topAppChart?.resize(); singleAppChart?.resize()
}

function setupResizeObserver() {
  if (chartResizeObserver) return
  const containers = [cpuChartRef.value, memChartRef.value, topAppChartRef.value, singleAppChartRef.value].filter(Boolean)
  if (containers.length === 0) return
  chartResizeObserver = new ResizeObserver(() => resizeCharts())
  containers.forEach(el => chartResizeObserver!.observe(el!))
}

onMounted(() => {
  document.addEventListener('click', handleDropdownClick)
  nextTick(() => {
    initCharts()
    setupResizeObserver()
    if (store.isCollecting) startPolling()
  })
})
onActivated(() => {
  isPageActive.value = true
  nextTick(() => {
    initCharts(); setupResizeObserver(); resizeCharts()
    if (store.isCollecting) {
      if (!pollTimer) startPolling()
      else {
        // Redraw all charts with data collected while page was inactive
        updateCharts(); updateTopAppChart(); updateCpuChart(); updateSingleAppChart()
      }
    }
  })
})
onDeactivated(() => {
  isPageActive.value = false
})
onUnmounted(() => {
  document.removeEventListener('click', handleDropdownClick)
  stopPolling()
  if (chartResizeObserver) { chartResizeObserver.disconnect(); chartResizeObserver = null }
  cpuChart?.dispose(); cpuChart = null
  memChart?.dispose(); memChart = null
  topAppChart?.dispose(); topAppChart = null
  singleAppChart?.dispose(); singleAppChart = null
})
</script>

<style scoped>
.fade-scale-enter-active,
.fade-scale-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}
.fade-scale-enter-from,
.fade-scale-leave-to {
  opacity: 0;
  transform: scale(0.95) translateY(-4px);
}
</style>
