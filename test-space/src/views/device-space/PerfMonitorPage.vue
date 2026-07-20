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
        <div class="w-2 h-2 rounded-full" :class="store.isCollecting ? 'bg-success-indicator animate-pulse' : 'bg-outline-variant'" :title="store.isCollecting ? t('perf.collecting') : t('perf.idle')"></div>
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
      <!-- Hidden chart toggle buttons -->
      <div v-if="Object.values(chartVisibility).some(v => !v)" class="flex items-center gap-1 ml-2 pl-2 border-l border-glass-border-dark">
        <button v-if="!chartVisibility.topApp" class="glass-button p-1.5 rounded-lg" title="显示TopN应用内存" @click="toggleChartVisibility('topApp')">
          <span class="material-symbols-outlined text-[14px]">lan</span>
        </button>
        <button v-if="!chartVisibility.cpu" class="glass-button p-1.5 rounded-lg" title="显示CPU使用率" @click="toggleChartVisibility('cpu')">
          <span class="material-symbols-outlined text-[14px]">memory</span>
        </button>
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
      <!-- Top N charts use ECharts native scroll legend for show/hide lines -->
      <div class="flex-1"></div>
      <button class="glass-button p-1.5 rounded-lg" @click="showSaveDialog = true" :disabled="store.isCollecting" :title="store.isCollecting ? '监控运行中不可用' : t('perf.saveSession')">
        <span class="material-symbols-outlined text-[16px]">save</span>
      </button>
      <button class="glass-button p-1.5 rounded-lg" @click="openLoadDialog" :disabled="store.isCollecting" :title="store.isCollecting ? '监控运行中不可用' : t('perf.loadSession')">
        <span class="material-symbols-outlined text-[16px]">history</span>
      </button>
      <button class="glass-button p-1.5 rounded-lg" @click="exportReport" :disabled="store.isCollecting" :title="store.isCollecting ? '监控运行中不可用' : t('perf.exportReport')">
        <span class="material-symbols-outlined text-[16px]">file_download</span>
      </button>
      <button class="glass-button p-1.5 rounded-lg" @click="clearHistory" :disabled="store.isCollecting" :title="store.isCollecting ? '监控运行中不可用' : t('perf.clearHistory')">
        <span class="material-symbols-outlined text-[16px]">delete_sweep</span>
      </button>
    </div>

    <!-- Top N app memory (top) + CPU (bottom) -->
    <div class="flex flex-col gap-4 flex-1 min-h-0">
      <div v-show="chartVisibility.topApp" class="glass-panel rounded-xl p-4 shadow-md flex flex-col min-h-0 flex-1">
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
              <button class="glass-hover rounded-lg p-1 ml-1" title="隐藏图表" @click="toggleChartVisibility('topApp')">
                <span class="material-symbols-outlined text-[14px]">visibility_off</span>
              </button>
            </span>
        </h3>
        <div ref="topAppChartRef" class="flex-1 min-h-0"></div>
      </div>

      <div v-show="chartVisibility.cpu" class="glass-panel rounded-xl p-4 shadow-md flex flex-col min-h-0 flex-1">
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
            <button class="glass-hover rounded-lg p-1 ml-1" title="隐藏图表" @click="toggleChartVisibility('cpu')">
              <span class="material-symbols-outlined text-[14px]">visibility_off</span>
            </button>
          </span>
        </h3>
        <div ref="cpuChartRef" class="flex-1 min-h-0"></div>
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

    <!-- Load Session Loading Overlay -->
    <Teleport to="body">
      <Transition name="fade">
        <div v-if="loadingSession" class="fixed inset-0 z-[9998] flex items-center justify-center bg-black/40 backdrop-blur-sm">
          <div class="glass-panel rounded-2xl p-8 flex flex-col items-center gap-4 bg-white/95 shadow-2xl min-w-[320px]">
            <div class="w-12 h-12 rounded-full border-4 border-secondary/20 border-t-secondary animate-spin"></div>
            <span class="font-label-md text-label-md text-on-surface">加载历史会话中</span>
            <span class="font-caption text-caption text-on-surface-variant text-center max-w-[280px]">{{ loadingSessionText }}</span>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, onActivated, onDeactivated, nextTick, type Ref } from 'vue'
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
const { shell, rootDevice, pullFile } = useAdb()
const store = usePerfMonitorStore()

const deviceSerial = ref(localStorage.getItem('last_device_serial') || '')
const intervalMs = ref(String(store.intervalMs))
// Track whether the page is currently active (visible). When deactivated by
// keep-alive (user switched to another page), we skip ECharts rendering to
// avoid blocking the main thread, but data collection continues uninterrupted.
const isPageActive = ref(true)

// Chart visibility state with localStorage persistence
const chartVisibility = ref(JSON.parse(localStorage.getItem('perfChartVisibility') || '{"cpu": true, "topApp": true}'))
watch(chartVisibility, (val, oldVal) => {
  localStorage.setItem('perfChartVisibility', JSON.stringify(val))
  // Resize charts when they become visible
  nextTick(() => {
    if (val.cpu && !oldVal.cpu) cpuChart?.resize()
    if (val.topApp && !oldVal.topApp) topAppChart?.resize()
  })
}, { deep: true })

function toggleChartVisibility(chart: 'cpu' | 'topApp') {
  chartVisibility.value[chart] = !chartVisibility.value[chart]
}

// Track highlighted series for tooltip filtering
const highlightedSeries = ref<string | null>(null)

// Track selected series (click to show single line)
const cpuSelectedSeries = ref<string | null>(null)
const topAppSelectedSeries = ref<string | null>(null)

function selectSeries(
  chart: echarts.ECharts | null,
  seriesName: string,
  selectedRef: Ref<string | null>,
  allSeriesNames: string[],
) {
  if (!chart) return
  if (selectedRef.value === seriesName) {
    // Click same series again, show all
    selectedRef.value = null
    allSeriesNames.forEach(name => chart.dispatchAction({ type: 'legendSelect', name }))
  } else {
    // Click different series, show only this one
    selectedRef.value = seriesName
    allSeriesNames.forEach(name => {
      if (name === seriesName) {
        chart.dispatchAction({ type: 'legendSelect', name })
      } else {
        chart.dispatchAction({ type: 'legendUnSelect', name })
      }
    })
  }
}

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
  updateCpuChartDebounced()
}
function toggleTopApp(name: string) {
  const s = new Set(topAppHiddenApps.value)
  if (s.has(name)) s.delete(name)
  else s.add(name)
  topAppHiddenApps.value = s
  updateTopAppChartDebounced()
}
function cpuSelectAll() { cpuHiddenApps.value = new Set(); updateCpuChartDebounced() }
function cpuSelectNone() {
  cpuHiddenApps.value = new Set(cpuAppNames.value)
  updateCpuChartDebounced()
}
function topAppSelectAll() { topAppHiddenApps.value = new Set(); updateTopAppChartDebounced() }
function topAppSelectNone() {
  topAppHiddenApps.value = new Set(topAppNames.value)
  updateTopAppChartDebounced()
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
let topAppChart: echarts.ECharts | null = null
let chartResizeObserver: ResizeObserver | null = null
const cpuChartRef = ref<HTMLElement | null>(null)
const topAppChartRef = ref<HTMLElement | null>(null)

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
// 加载历史会话的loading遮罩状态
const loadingSession = ref(false)
const loadingSessionText = ref('')
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
    started_at: formatLocalTime(new Date(store.history[0]?.time ?? Date.now())),
    ended_at: formatLocalTime(new Date()),
    interval_ms: store.intervalMs,
    data: sessionData,
    created_at: formatLocalTime(new Date()),
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
  loadingSession.value = true
  loadingSessionText.value = '正在准备加载会话...'
  // 让UI先渲染遮罩，再执行后续操作（避免长任务阻塞导致看不到遮罩）
  await new Promise(resolve => requestAnimationFrame(resolve))
  try {
    loadingSessionText.value = '正在解析数据...'
    await new Promise(resolve => requestAnimationFrame(resolve))
    const parsed = JSON.parse(s.data)
    // Handle both old format (array of points) and new format (object with history + process maps)
    if (Array.isArray(parsed)) {
      store.restoreHistory(parsed)
    } else {
      loadingSessionText.value = '正在恢复历史数据...'
      await new Promise(resolve => requestAnimationFrame(resolve))
      store.restoreFullSession(parsed)
    }
    store.setInterval(s.interval_ms)
    intervalMs.value = String(s.interval_ms)
    showLoadDialog.value = false
    // 大数据量加载时，分批异步渲染避免阻塞UI线程
    const dataSize = store.history.length
    if (dataSize > 5000) {
      loadingSessionText.value = `正在渲染 ${dataSize} 个数据点（约${(dataSize/3600).toFixed(1)}小时）...`
    } else {
      loadingSessionText.value = '正在渲染图表...'
    }
    // 让UI刷新遮罩文字
    await new Promise(resolve => requestAnimationFrame(resolve))
    // 使用setTimeout拆分任务，给UI响应机会
    // 第一个图表先立即渲染（响应快），其余图表延后到下一个事件循环
    updateCpuChartDebounced()
    setTimeout(() => updateTopAppChartDebounced(), 0)
    // 等待所有图表完成渲染后关闭遮罩
    setTimeout(() => {
      loadingSession.value = false
      showToast(t('perf.sessionLoaded'))
    }, 500)
  } catch (e: any) {
    loadingSession.value = false
    showToast('Failed to load session: ' + (e?.message || e), true)
  }
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

// Bucketing-based downsampling: for each time bucket, keep min/max/first/last points
// to preserve spikes and trends that simple stride-based downsampling would miss.
// 优化：避免在循环内创建Set/filter，使用数组push+排序去重，大幅提升大数据量渲染速度
function bucketingDownsample<T extends { time: number }>(arr: T[], valueFn: (x: T) => number, maxLen: number): T[] {
  if (arr.length <= maxLen) return arr
  const bucketSize = arr.length / maxLen
  const n = arr.length
  const result: T[] = new Array(maxLen * 4) // 预分配，避免push扩容
  let outLen = 0
  for (let b = 0; b < maxLen; b++) {
    const start = Math.floor(b * bucketSize)
    const end = b === maxLen - 1 ? n : Math.floor((b + 1) * bucketSize)
    if (start >= end) continue
    let minV = valueFn(arr[start]), minIdx = start
    let maxV = minV, maxIdx = start
    for (let i = start + 1; i < end; i++) {
      const v = valueFn(arr[i])
      if (v < minV) { minV = v; minIdx = i }
      else if (v > maxV) { maxV = v; maxIdx = i }
    }
    // 顺序: start, minIdx, maxIdx, end-1，去重并按索引升序
    const idx = [start, minIdx, maxIdx, end - 1]
    // 内联去重（4个元素，O(1) 排序）
    const uniq: number[] = []
    if (idx[0] !== idx[1] && idx[0] !== idx[2] && idx[0] !== idx[3]) uniq.push(idx[0])
    else if (idx[0] !== idx[1] && idx[0] !== idx[2]) uniq.push(idx[0])
    else if (idx[0] !== idx[1]) uniq.push(idx[0])
    if (idx[1] !== idx[0] && idx[1] !== idx[2] && idx[1] !== idx[3]) uniq.push(idx[1])
    else if (idx[1] !== idx[0] && idx[1] !== idx[2]) uniq.push(idx[1])
    if (idx[2] !== idx[0] && idx[2] !== idx[1] && idx[2] !== idx[3]) uniq.push(idx[2])
    else if (idx[2] !== idx[0] && idx[2] !== idx[1]) uniq.push(idx[2])
    if (idx[3] !== idx[0] && idx[3] !== idx[1] && idx[3] !== idx[2]) uniq.push(idx[3])
    uniq.sort((a, c) => a - c)
    for (let k = 0; k < uniq.length; k++) result[outLen++] = arr[uniq[k]]
  }
  result.length = outLen
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
  return buildBuiltinAssessment(pts, topMem, topCpu, singleName, singleData)
}

function buildBuiltinAssessment(
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
    // 1. Abnormal CPU peak — list top CPU-consuming apps
    const cpus = pts.map(p => p.cpu)
    const maxCpu = safeMax(cpus)
    if (maxCpu > 80) {
      const peakApps = topCpu
        .map(p => ({ name: p.name, max: safeMax(p.data.map(d => d.cpuPercent)) }))
        .filter(p => p.max > 5)
        .sort((a, b) => b.max - a.max)
        .slice(0, 5)
      const appList = peakApps.map(p => `${p.name} ${p.max.toFixed(1)}%`).join('、')
      if (maxCpu > 90) {
        issues.push(`CPU 峰值达到 ${maxCpu.toFixed(1)}%，接近满载，可能影响系统流畅度。主要占用应用：${appList}`)
      } else {
        issues.push(`CPU 峰值达到 ${maxCpu.toFixed(1)}%，处于较高水平。主要占用应用：${appList}`)
      }
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

    // 4. Device memory trend analysis
    const deviceMemData = pts.map(p => ({ time: p.time, pssKb: p.memUsedKb }))
    const deviceMemAnalysis = analyzeMemoryTrend(deviceMemData)
    if (deviceMemAnalysis.isLeak) {
      leaks.push(deviceMemAnalysis.description.replace('内存', '设备内存使用量'))
    } else if (deviceMemAnalysis.isRising) {
      rising.push(deviceMemAnalysis.description.replace('内存', '设备内存使用量'))
    }

    // 5. CPU overall trend analysis
    const cpuData = pts.map(p => ({ time: p.time, pssKb: p.cpu }))
    const cpuAnalysis = analyzeMemoryTrend(cpuData)
    if (cpuAnalysis.isLeak) {
      issues.push(cpuAnalysis.description.replace('内存', 'CPU 使用率').replace('MB', '%'))
    } else if (cpuAnalysis.isRising) {
      rising.push(cpuAnalysis.description.replace('内存', 'CPU 使用率').replace('MB', '%'))
    }

    // 6. Memory leak detection using linear regression + segmented trend analysis
    for (const p of topMem) {
      const analysis = analyzeMemoryTrend(p.data)
      if (analysis.isLeak) {
        leaks.push(analysis.description.replace('内存', `应用 ${p.name} PSS`))
      } else if (analysis.isRising) {
        rising.push(analysis.description.replace('内存', `应用 ${p.name} PSS`))
      }
    }

    // 7. Single app memory leak
    if (singleData.length >= 10) {
      const analysis = analyzeMemoryTrend(singleData)
      if (analysis.isLeak) {
        leaks.push(analysis.description.replace('内存', `单应用 ${singleName} PSS`))
      } else if (analysis.isRising) {
        rising.push(analysis.description.replace('内存', `单应用 ${singleName} PSS`))
      }
    }

    // 8. CPU sustained high
    for (const p of topCpu) {
      if (p.data.length < 10) continue
      const lastAvg = safeAvg(p.data.slice(-10).map(d => d.cpuPercent))
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
    <strong>⚠️ 仅供参考：</strong>以下评估基于采集期间的统计数据和趋势分析（线性回归 + 分段趋势检测），不构成确定性诊断。实际表现可能受设备状态、系统调度、测试场景等多种因素影响，请结合具体场景综合判断。
  </div>
  <h3 style="color:#e74c3c;font-size:.95rem;margin:1rem 0 .4rem 0">异常情况</h3>
  <ul>${issueHtml}</ul>
  <h3 style="color:#9b59b6;font-size:.95rem;margin:1rem 0 .4rem 0">内存泄露情况</h3>
  <ul>${leakHtml}</ul>
  <h3 style="color:#f39c12;font-size:.95rem;margin:1rem 0 .4rem 0">持续上涨情况</h3>
  <ul>${risingHtml}</ul>
</div>`
}

function analyzeMemoryTrend(data: { time: number; pssKb: number }[]): {
  isLeak: boolean;
  isRising: boolean;
  description: string;
} {
  if (data.length < 10) {
    return { isLeak: false, isRising: false, description: '' }
  }

  const values = data.map(d => d.pssKb)
  const times = data.map(d => d.time)
  
  const firstAvg = safeAvg(values.slice(0, Math.min(10, Math.floor(values.length / 4))))
  const lastAvg = safeAvg(values.slice(-Math.min(10, Math.floor(values.length / 4))))
  
  if (firstAvg <= 0) {
    return { isLeak: false, isRising: false, description: '' }
  }

  const growthPercent = ((lastAvg - firstAvg) / firstAvg * 100).toFixed(1)
  
  const slopeResult = linearRegression(times, values)
  const slopeKbPerSec = slopeResult.slope
  const r2 = slopeResult.r2
  
  const stdDev = calculateStdDev(values)
  const cv = stdDev / safeAvg(values)
  
  const segments = splitIntoSegments(data, 3)
  const segmentSlopes = segments.map(s => linearRegression(s.times, s.values).slope)
  
  const durationSec = (times[times.length - 1] - times[0]) / 1000
  const totalGrowthKb = lastAvg - firstAvg
  const avgGrowthRateKbPerSec = totalGrowthKb / durationSec
  
  const lastSegmentSlope = segmentSlopes[segmentSlopes.length - 1]
  const firstSegmentSlope = segmentSlopes[0]
  
  const isLastSlopePositive = lastSegmentSlope > 0.01
  const isLastSlopeHigher = lastSegmentSlope >= firstSegmentSlope * 0.5
  
  const growthThreshold = 1.2
  
  if (lastAvg <= firstAvg * growthThreshold) {
    return { isLeak: false, isRising: false, description: '' }
  }

  if (r2 > 0.6 && isLastSlopePositive && isLastSlopeHigher && avgGrowthRateKbPerSec > 0.1) {
    const rateStr = formatGrowthRate(avgGrowthRateKbPerSec)
    const durStr = formatDuration(durationSec)
    return {
      isLeak: true,
      isRising: false,
      description: `内存从 ${formatKb(firstAvg)} ${formatKbUnit(firstAvg)} 持续增长至 ${formatKb(lastAvg)} ${formatKbUnit(lastAvg)}（+${growthPercent}%），${durStr} 内平均增速 ${rateStr}，且后期增长趋势未减缓（R²=${r2.toFixed(2)}），疑似内存泄露`
    }
  }

  if (lastSegmentSlope <= 0.01 || (!isLastSlopeHigher && firstSegmentSlope > 0.1)) {
    return {
      isLeak: false,
      isRising: true,
      description: `内存初始阶段增长 ${growthPercent}%（${formatKb(firstAvg)} → ${formatKb(lastAvg)} ${formatKbUnit(lastAvg)}），但后期趋于稳定，属于正常启动加载特征`
    }
  }

  if (cv > 0.2) {
    return {
      isLeak: false,
      isRising: true,
      description: `内存波动较大（变异系数 ${(cv * 100).toFixed(0)}%），整体呈上升趋势 ${growthPercent}%，建议结合更长时间观察确认是否存在泄露`
    }
  }

  return {
    isLeak: false,
    isRising: true,
    description: `内存呈上升趋势 ${growthPercent}%（${formatKb(firstAvg)} → ${formatKb(lastAvg)} ${formatKbUnit(lastAvg)}），建议持续观察`
  }
}

function linearRegression(x: number[], y: number[]): { slope: number; intercept: number; r2: number } {
  const n = x.length
  if (n < 2) return { slope: 0, intercept: 0, r2: 0 }
  
  let sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0
  for (let i = 0; i < n; i++) {
    sumX += x[i]
    sumY += y[i]
    sumXY += x[i] * y[i]
    sumX2 += x[i] * x[i]
  }
  
  const denominator = n * sumX2 - sumX * sumX
  if (denominator === 0) return { slope: 0, intercept: 0, r2: 0 }
  
  const slope = (n * sumXY - sumX * sumY) / denominator
  const intercept = (sumY - slope * sumX) / n
  
  let ssTot = 0, ssRes = 0
  const meanY = sumY / n
  for (let i = 0; i < n; i++) {
    ssTot += Math.pow(y[i] - meanY, 2)
    ssRes += Math.pow(y[i] - (slope * x[i] + intercept), 2)
  }
  
  const r2 = ssTot === 0 ? 0 : 1 - ssRes / ssTot
  
  return { slope, intercept, r2 }
}

function calculateStdDev(values: number[]): number {
  if (values.length === 0) return 0
  const mean = safeAvg(values)
  const variance = values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / values.length
  return Math.sqrt(variance)
}

function splitIntoSegments(data: { time: number; pssKb: number }[], count: number): Array<{ times: number[]; values: number[] }> {
  const segmentSize = Math.floor(data.length / count)
  const segments: Array<{ times: number[]; values: number[] }> = []
  
  for (let i = 0; i < count; i++) {
    const start = i * segmentSize
    const end = i === count - 1 ? data.length : (i + 1) * segmentSize
    segments.push({
      times: data.slice(start, end).map(d => d.time),
      values: data.slice(start, end).map(d => d.pssKb)
    })
  }
  
  return segments
}

function formatGrowthRate(kbPerSec: number): string {
  if (kbPerSec >= 1024) {
    return `${(kbPerSec / 1024).toFixed(2)} MB/s`
  }
  return `${kbPerSec.toFixed(2)} KB/s`
}

function formatDuration(seconds: number): string {
  if (seconds < 60) return `${Math.round(seconds)}秒`
  if (seconds < 3600) return `${Math.round(seconds / 60)}分钟`
  return `${(seconds / 3600).toFixed(1)}小时`
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

    // Save perf_top_apps.csv
    if (topN.length > 0) {
      const topHeader = 'Time,Free_RAM(KB),Swap_Free(KB),' + topNames.map(n => `"${n}(KB)"`).join(',')
      const maxLen = pts.length
      const topRows: string[] = []
      for (let i = 0; i < maxLen; i++) {
        const t = formatLocalTime(new Date(pts[i].time))
        const freeRam = pts[i].memAvailKb.toString()
        const swapFree = pts[i].swapFreeKb.toString()
        const vals = topN.map(p => i < p.data.length ? p.data[i].pssKb.toString() : '')
        topRows.push(t + ',' + freeRam + ',' + swapFree + ',' + vals.join(','))
      }
      await writeTextFile(dir + '/perf_top_apps.csv', topHeader + '\n' + topRows.join('\n'))
    }

    // Save perf_top_cpu.csv
    if (topCpu.length > 0) {
      const maxLen = safeMax(topCpu.map(p => p.data.length))
      const rows: string[] = []
      for (let i = 0; i < maxLen; i++) {
        const t = i < topCpu[0].data.length ? formatLocalTime(new Date(topCpu[0].data[i].time)) : ''
        const vals = topCpu.map(p => i < p.data.length ? p.data[i].cpuPercent.toFixed(1) : '')
        rows.push(t + ',' + vals.join(','))
      }
      await writeTextFile(dir + '/perf_top_cpu.csv', 'Time,' + topCpu.map(p => `"${p.name}(%)"`).join(',') + '\n' + rows.join('\n'))
    }

    // Save perf_report.html — downsample data for interactive charts to keep
    // the HTML file manageable (max 4000 points per series) even for multi-day runs.
    // 使用bucketing下采样保留极值，支持一周数据的有效分析
    const DOWNSAMPLE_MAX = 4000
    const dsPts = bucketingDownsample(pts, p => p.cpu, DOWNSAMPLE_MAX)
    const dsTopN = topN.map(p => ({ ...p, data: bucketingDownsample(p.data, d => d.pssKb, DOWNSAMPLE_MAX) }))
    const dsTopCpu = topCpu.map(p => ({ ...p, data: bucketingDownsample(p.data, d => d.cpuPercent, DOWNSAMPLE_MAX) }))
    const interactiveHtml = buildInteractiveChartsHtml(dsPts, dsTopN, dsTopCpu)
    const freeRamVals = pts.map(p => p.memAvailKb)
    const swapFreeVals = pts.map(p => p.swapFreeKb)
    const memFreeRows = `<tr><td></td><td><strong>Free RAM</strong></td><td>${formatKb(safeMin(freeRamVals))} ${formatKbUnit(safeMin(freeRamVals))}</td><td>${formatKb(safeMax(freeRamVals))} ${formatKbUnit(safeMax(freeRamVals))}</td><td>${formatKb(safeAvg(freeRamVals))} ${formatKbUnit(safeAvg(freeRamVals))}</td></tr>
<tr><td></td><td><strong>Swap Free</strong></td><td>${formatKb(safeMin(swapFreeVals))} ${formatKbUnit(safeMin(swapFreeVals))}</td><td>${formatKb(safeMax(swapFreeVals))} ${formatKbUnit(safeMax(swapFreeVals))}</td><td>${formatKb(safeAvg(swapFreeVals))} ${formatKbUnit(safeAvg(swapFreeVals))}</td></tr>
`
    const html = `<!DOCTYPE html>
<html lang="zh">
<head><meta charset="utf-8"><title>性能报告</title>
<style>
body{font-family:system-ui,-apple-system,sans-serif;max-width:1400px;margin:auto;padding:2rem;background:#f5f5f5;color:#222}
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
  <p><strong>时间范围:</strong> ${formatLocalTime(new Date(pts[0].time))} ~ ${formatLocalTime(new Date(pts[pts.length-1].time))}</p>
  <p><strong>采集间隔:</strong> ${(store.intervalMs / 1000).toFixed(0)}s</p>
</div>
${buildOverallAssessment(pts, topN, topCpu, '', [])}
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
  <tbody>${memFreeRows}${topN.map((p, i) => {
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
${interactiveHtml}
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
): string {
  // Stable color assignment: same package name always gets same color
  const allColors = ['#7c5cfc', '#22c55e', '#f59e0b', '#ef4444', '#3b82f6', '#ec4899', '#14b8a6', '#f97316', '#8b5cf6', '#06b6d4', '#84cc16', '#a855f7', '#f43f5e', '#0ea5e9', '#10b981', '#eab308', '#d946ef', '#6366f1', '#fb923c', '#14b8a6']
  const colorMap: Record<string, string> = {}
  function getColor(name: string): string {
    if (!colorMap[name]) {
      const keys = Object.keys(colorMap)
      colorMap[name] = allColors[keys.length % allColors.length]
    }
    return colorMap[name]
  }

  const cpuSeries = topCpu.map(p => ({
    name: p.name,
    data: p.data.map(d => [d.time, d.cpuPercent] as [number, number]),
    color: getColor(p.name),
  }))
  const topSeries: { name: string; data: [number, number][]; color: string }[] = []
  if (pts.length > 0) {
    topSeries.push({
      name: 'Free RAM',
      data: pts.map(p => [p.time, p.memAvailKb] as [number, number]),
      color: '#22c55e',
    })
    topSeries.push({
      name: 'Swap Free',
      data: pts.map(p => [p.time, p.swapFreeKb] as [number, number]),
      color: '#3b82f6',
    })
  }
  topSeries.push(...topMem.map(p => ({
    name: p.name,
    data: p.data.map(d => [d.time, d.pssKb] as [number, number]),
    color: getColor(p.name),
  })))

  const jsonStr = (v: any) => JSON.stringify(v).replace(/</g, '\\u003c')

  return `
<div class="card">
  <h2>交互式图表</h2>
  <p style="font-size:.85rem;color:#666;margin-bottom:.5rem">点击折线或包名选中单个应用，再次点击显示全部。需要联网加载图表库。</p>
  <div id="chart-loading" style="padding:2rem;text-align:center;color:#888;font-size:.9rem">正在加载图表库...</div>
  <div id="charts-container" style="display:none">
    <div class="interactive-chart"><h3>Top ${topMem.length} 应用内存</h3><div id="ic-top" style="width:100%;height:360px"></div></div>
    <div class="interactive-chart"><h3>Top ${topCpu.length} 应用 CPU 使用率</h3><div id="ic-cpu" style="width:100%;height:360px"></div></div>
  </div>
  <script type="application/json" id="ic-data">${jsonStr({
    cpu: cpuSeries, top: topSeries,
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
      var latestCpuValues = {};
      (data.cpu || []).forEach(function(s) {
        if (s.data && s.data.length > 0) {
          var last = s.data[s.data.length - 1];
          latestCpuValues[s.name] = last[1];
        }
      });
      var latestTopValues = {};
      (data.top || []).forEach(function(s) {
        if (s.data && s.data.length > 0) {
          var last = s.data[s.data.length - 1];
          latestTopValues[s.name] = last[1];
        }
      });
      var cpuSelected = null;
      var topSelected = null;
      function getAllNames(chart) {
        return (chart.getOption().series || []).map(function(s) { return s.name; });
      }
      function selectSeries(chart, seriesName, selectedRef) {
        var allNames = getAllNames(chart);
        if (selectedRef === 'cpu') {
          if (cpuSelected === seriesName) {
            cpuSelected = null;
            allNames.forEach(function(n) { chart.dispatchAction({ type: 'legendSelect', name: n }); });
          } else {
            cpuSelected = seriesName;
            allNames.forEach(function(n) {
              if (n === seriesName) chart.dispatchAction({ type: 'legendSelect', name: n });
              else chart.dispatchAction({ type: 'legendUnSelect', name: n });
            });
          }
        } else {
          if (topSelected === seriesName) {
            topSelected = null;
            allNames.forEach(function(n) { chart.dispatchAction({ type: 'legendSelect', name: n }); });
          } else {
            topSelected = seriesName;
            allNames.forEach(function(n) {
              if (n === seriesName) chart.dispatchAction({ type: 'legendSelect', name: n });
              else chart.dispatchAction({ type: 'legendUnSelect', name: n });
            });
          }
        }
      }
      var opts = {
        tooltip: {
          trigger: 'axis',
          confine: true,
          axisPointer: {
            type: 'cross',
            label: {
              show: true,
              backgroundColor: 'rgba(50,50,50,0.85)',
              borderColor: 'rgba(50,50,50,0.85)',
              borderWidth: 0,
              color: '#fff',
              fontSize: 10,
              padding: [4, 6],
            }
          },
        },
        legend: {
          type: 'scroll', orient: 'vertical', right: 10, top: 'middle',
          icon: 'circle', itemWidth: 12, itemHeight: 10,
          textStyle: { fontSize: 11, width: 340, overflow: 'breakAll' },
          pageTextStyle: { fontSize: 11 }, pageIconSize: 12,
          selectedMode: 'multiple',
        },
        grid: { left: 60, right: 380, top: 15, bottom: 40 },
        xAxis: {
          type: 'time',
          axisLabel: {
            fontSize: 11,
            hideOverlap: true,
            formatter: function(value) {
              var d = new Date(value);
              if (isNaN(d.getTime())) return '';
              var pad = function(n) { return n < 10 ? '0' + n : '' + n; };
              var allT = [];
              ['cpu','top'].forEach(function(k) {
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
        animationDuration: 300,
      };
      function mk(series, yFmt, valFmt, isCpu, isTop) {
        var tooltipOpt = Object.assign({}, opts.tooltip);
        if (isCpu || isTop) {
          tooltipOpt.formatter = function(params) {
            var selected = isCpu ? cpuSelected : topSelected;
            if (!selected) return '';
            if (!params || !params.length) return '';
            var time = new Date(params[0].axisValue).toLocaleTimeString('zh-CN', { hour12: false });
            var item = params.find(function(p) { return p.seriesName === selected; });
            if (!item) return '';
            return '<div><div style="font-weight:600;margin-bottom:4px">' + time + '</div>' + item.marker + ' ' + item.seriesName + ': <b>' + valFmt(item.value[1]) + '</b></div>';
          };
        }
        return Object.assign({}, opts, {
          yAxis: Object.assign({}, opts.yAxis, { axisLabel: Object.assign({}, opts.yAxis.axisLabel, { formatter: yFmt }) }),
          tooltip: tooltipOpt,
          legend: Object.assign({}, opts.legend, {
            formatter: function(name) {
              var map = isCpu ? latestCpuValues : latestTopValues;
              var v = map[name];
              if (v !== undefined) {
                if (isCpu) {
                  return name + ' (' + v.toFixed(1) + '%)';
                } else {
                  return name + ' (' + (v >= 1024 ? (v / 1024).toFixed(0) + 'M' : v + 'K') + ')';
                }
              }
              return name;
            }
          }),
          series: series.map(function(s) {
            return { type: 'line', name: s.name, data: s.data, smooth: true, symbol: 'none', lineStyle: { width: 2, color: s.color }, itemStyle: { color: s.color } };
          }),
        });
      }
      var cpuChart = echarts.init(document.getElementById('ic-cpu'));
      cpuChart.setOption(mk(data.cpu,
        function(v) { return v + '%'; },
        function(v) { return v.toFixed(1) + '%'; }, true));
      cpuChart.on('click', function(params) {
        if (params.componentType !== 'series') return;
        selectSeries(cpuChart, params.seriesName, 'cpu');
      });
      cpuChart.on('legendselectchanged', function(params) {
        selectSeries(cpuChart, params.name, 'cpu');
      });
      var topChart = echarts.init(document.getElementById('ic-top'));
      topChart.setOption(mk(data.top,
        function(v) { return v >= 1024 ? (v / 1024).toFixed(0) + 'M' : v + 'K'; },
        function(v) { return v >= 1024 ? (v / 1024).toFixed(0) + 'M' : v + 'K'; }, false, true));
      topChart.on('click', function(params) {
        if (params.componentType !== 'series') return;
        selectSeries(topChart, params.seriesName, 'top');
      });
      topChart.on('legendselectchanged', function(params) {
        selectSeries(topChart, params.name, 'top');
      });
      window.addEventListener('resize', function() {
        ['ic-cpu','ic-top'].forEach(function(id) {
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
  try { await writeTextFile(sessionLogDir.value + 'ps.txt', await shell(serial, 'ps -A 2>/dev/null')) } catch {}
  try { await writeTextFile(sessionLogDir.value + 'df.txt', await shell(serial, 'df 2>/dev/null')) } catch {}
  try { await writeTextFile(sessionLogDir.value + 'proc_stat.txt', await shell(serial, 'cat /proc/stat 2>/dev/null')) } catch {}
}

// Periodic meminfo collection
async function collectLogs(serial: string) {
  if (!serial || !sessionLogDir.value) return
  try {
    const ts = formatLocalTime(new Date()).replace(/[:.]/g, '-')
    const memDir = sessionLogDir.value + 'meminfo/'
    try { await mkdir(memDir, { recursive: true }) } catch {}
    const meminfo = await shell(serial, 'cat /proc/meminfo 2>/dev/null')
    await writeTextFile(memDir + 'meminfo_' + ts + '.txt', meminfo)
  } catch {}
}

function goBack() { router.push('/device-space') }

function formatLocalTime(date: Date): string {
  const pad = (n: number) => n.toString().padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
}

let pollErrorCount = 0
let renderTimer: ReturnType<typeof setTimeout> | null = null
let renderPending = false
// 实时图表最大点数：提升到600以支持更长时间运行时的精度
// 同时使用bucketing下采样保留极值（峰值、谷值），避免简单步进下采样丢失关键信息
const MAX_CHART_POINTS = 600
const latestTopAppValues = ref<Record<string, number>>({})
const latestCpuValues = ref<Record<string, number>>({})

function scheduleRender() {
  renderPending = true
  if (renderTimer) return
  renderTimer = setTimeout(() => {
    renderTimer = null
    if (renderPending && isPageActive.value) {
      renderPending = false
      updateCpuChartDebounced()
      if (chartVisibility.value.topApp) updateTopAppChartDebounced()
    }
  }, 300)
}

function updateCpuChartDebounced() {
  if (!cpuChart) return
  const hist = store.processCpuHistory
  if (hist.size === 0) {
    cpuChart.setOption({ series: [] }, { replaceMerge: ['series'] })
    return
  }

  // 性能优化：先按最后值排序筛出Top N候选，再只对前N个进程做下采样
  // 避免对50+进程全部做bucketing下采样（大数据量时性能瓶颈）
  const candidates = Array.from(hist.entries())
    .map(([name, data]) => ({
      name,
      lastCpu: data[data.length - 1]?.cpuPercent ?? 0,
      data,
    }))
  candidates.sort((a, b) => b.lastCpu - a.lastCpu)
  // 只对需要的Top N做下采样
  const topN = candidates.slice(0, store.cpuTopNCount).map(p => ({
    ...p,
    data: bucketingDownsample(p.data, d => d.cpuPercent, MAX_CHART_POINTS),
  }))

  if (topN.length === 0) {
    cpuChart.setOption({ series: [] }, { replaceMerge: ['series'] })
    return
  }

  const newLatest: Record<string, number> = {}
  const series = topN.map(p => {
    const last = p.data[p.data.length - 1]
    if (last) newLatest[p.name] = last.cpuPercent
    return {
      type: 'line',
      name: p.name,
      data: p.data.map(h => [h.time, h.cpuPercent] as [number, number]),
      smooth: true,
      symbol: 'none',
      symbolSize: 4,
      lineStyle: { width: 2, color: getColor(p.name) },
      itemStyle: { color: getColor(p.name) },
      animation: false,
      triggerLineEvent: true,
      emphasis: {
        focus: 'series',
        blurScope: 'coordinateSystem',
        lineStyle: { width: 3 },
        itemStyle: { borderWidth: 2 },
        showSymbol: true,
      },
    }
  })
  latestCpuValues.value = newLatest

  cpuChart.setOption({
    series,
    legend: {
      formatter: (name: string) => {
        const v = latestCpuValues.value[name]
        if (v !== undefined) return name + ' (' + v.toFixed(1) + '%)'
        return name
      },
    },
  }, { replaceMerge: ['series'] })

  // Apply series visibility based on selection
  series.forEach(s => {
    if (cpuSelectedSeries.value) {
      // Show only selected series
      if (s.name === cpuSelectedSeries.value) {
        cpuChart?.dispatchAction({ type: 'legendSelect', name: s.name })
      } else {
        cpuChart?.dispatchAction({ type: 'legendUnSelect', name: s.name })
      }
    } else {
      // Show all series
      cpuChart?.dispatchAction({ type: 'legendSelect', name: s.name })
    }
  })
}

function updateTopAppChartDebounced() {
  if (!topAppChart) return
  const pts = store.history
  const hist = store.processPssHistory
  const series: any[] = []
  const newLatest: Record<string, number> = {}

  // Series 1: Free RAM (always first, green)
  if (pts.length > 0) {
    const freeRamData = bucketingDownsample(
      pts.map(p => ({ time: p.time, pssKb: p.memAvailKb })),
      d => d.pssKb,
      MAX_CHART_POINTS,
    )
    series.push({
      type: 'line',
      name: 'Free RAM',
      data: freeRamData.map(h => [h.time, h.pssKb] as [number, number]),
      smooth: true,
      symbol: 'none',
      symbolSize: 4,
      lineStyle: { width: 2, color: '#22c55e' },
      itemStyle: { color: '#22c55e' },
      areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(34,197,94,0.2)' }, { offset: 1, color: 'rgba(34,197,94,0.02)' }]) },
      animation: false,
      triggerLineEvent: true,
      emphasis: {
        focus: 'series',
        blurScope: 'coordinateSystem',
        lineStyle: { width: 3 },
        itemStyle: { borderWidth: 2 },
        showSymbol: true,
      },
    })
    const last = freeRamData[freeRamData.length - 1]
    if (last) newLatest['Free RAM'] = last.pssKb
  }

  // Series 2: Swap Free (always second, blue)
  if (pts.length > 0) {
    const swapFreeData = bucketingDownsample(
      pts.map(p => ({ time: p.time, pssKb: p.swapFreeKb })),
      d => d.pssKb,
      MAX_CHART_POINTS,
    )
    series.push({
      type: 'line',
      name: 'Swap Free',
      data: swapFreeData.map(h => [h.time, h.pssKb] as [number, number]),
      smooth: true,
      symbol: 'none',
      symbolSize: 4,
      lineStyle: { width: 2, color: '#3b82f6' },
      itemStyle: { color: '#3b82f6' },
      areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(59,130,246,0.2)' }, { offset: 1, color: 'rgba(59,130,246,0.02)' }]) },
      animation: false,
      triggerLineEvent: true,
      emphasis: {
        focus: 'series',
        blurScope: 'coordinateSystem',
        lineStyle: { width: 3 },
        itemStyle: { borderWidth: 2 },
        showSymbol: true,
      },
    })
    const last = swapFreeData[swapFreeData.length - 1]
    if (last) newLatest['Swap Free'] = last.pssKb
  }

  // Top N app memory series
  if (hist.size > 0) {
    const candidates = Array.from(hist.entries())
      .map(([name, data]) => ({
        name,
        lastPss: data[data.length - 1]?.pssKb ?? 0,
        data,
      }))
    candidates.sort((a, b) => b.lastPss - a.lastPss)
    const topN = candidates.slice(0, store.topAppCount).map(p => ({
      ...p,
      data: bucketingDownsample(p.data, d => d.pssKb, MAX_CHART_POINTS),
    }))

    for (const p of topN) {
      series.push({
        type: 'line',
        name: p.name,
        data: p.data.map(h => [h.time, h.pssKb] as [number, number]),
        smooth: true,
        symbol: 'none',
        symbolSize: 4,
        lineStyle: { width: 2, color: getColor(p.name) },
        itemStyle: { color: getColor(p.name) },
        animation: false,
        triggerLineEvent: true,
        emphasis: {
          focus: 'series',
          blurScope: 'coordinateSystem',
          lineStyle: { width: 3 },
          itemStyle: { borderWidth: 2 },
          showSymbol: true,
        },
      })
      const last = p.data[p.data.length - 1]
      if (last) newLatest[p.name] = last.pssKb
    }
  }

  if (series.length === 0) {
    topAppChart.setOption({ series: [] }, { replaceMerge: ['series'] })
    return
  }
  latestTopAppValues.value = newLatest

  topAppChart.setOption({
    series,
    legend: {
      formatter: (name: string) => {
        const v = latestTopAppValues.value[name]
        if (v !== undefined) {
          const val = v >= 1048576 ? (v / 1048576).toFixed(1) + 'G' : v >= 1024 ? (v / 1024).toFixed(0) + 'M' : v + 'K'
          return name + ' (' + val + ')'
        }
        return name
      },
    },
  }, { replaceMerge: ['series'] })

  // Apply series visibility based on selection
  series.forEach(s => {
    if (topAppSelectedSeries.value) {
      if (s.name === topAppSelectedSeries.value) {
        topAppChart?.dispatchAction({ type: 'legendSelect', name: s.name })
      } else {
        topAppChart?.dispatchAction({ type: 'legendUnSelect', name: s.name })
      }
    } else {
      topAppChart?.dispatchAction({ type: 'legendSelect', name: s.name })
    }
  })
}

async function pollOnce() {
  if (!deviceSerial.value) return
  try {
    const snap = await getSnapshot(deviceSerial.value)
    pollErrorCount = 0
    store.addPoint(snap)
    // Schedule chart rendering with debounce to avoid jank with large datasets.
    // Charts are updated at most once every 300ms, and only when the page is active.
    // Data still collects in the store; charts update when user returns.
    scheduleRender()
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
}

function bufferCsvPoint(snap: PerfSnapshot) {
  const now = new Date()
  const row = `${formatLocalTime(now)},${snap.cpu_total.toFixed(1)},${snap.mem_total_kb - snap.mem_free_kb},${snap.mem_total_kb},${snap.mem_avail_kb},${snap.zram_total_kb},${snap.storage_used_kb},${snap.storage_total_kb}`
  csvBuffer.push(row)
  if (csvBuffer.length >= CSV_FLUSH_THRESHOLD) {
    flushCsvBuffer()
  }
}

async function flushCsvBuffer() {
  csvBuffer = []
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
  const ts = formatLocalTime(new Date()).replace(/[:.]/g, '-')
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

  // 5. Start polling immediately (before one-time logs to show data ASAP)
  store.setCollecting(true)
  pollOnce()
  pollTimer = setInterval(pollOnce, store.intervalMs)

  // 6. Capture one-time logs in background (fire-and-forget, don't block first poll)
  captureOneTimeLogs(serial)

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

    if (topMem.length > 0) {
      const maxLen = pts.length
      const rows = []
      for (let i = 0; i < maxLen; i++) {
        const t = formatLocalTime(new Date(pts[i].time))
        const freeRam = pts[i].memAvailKb.toString()
        const swapFree = pts[i].swapFreeKb.toString()
        const vals = topMem.map(p => i < p.data.length ? p.data[i].pssKb.toString() : '')
        rows.push(t + ',' + freeRam + ',' + swapFree + ',' + vals.join(','))
      }
      await writeTextFile(dir + 'perf_top_apps.csv', 'Time,Free_RAM(KB),Swap_Free(KB),' + topNames.map(n => `"${n}(KB)"`).join(',') + '\n' + rows.join('\n'))
    }

    if (topCpu.length > 0) {
      const maxLen = safeMax(topCpu.map(p => p.data.length))
      const rows = []
      for (let i = 0; i < maxLen; i++) {
        const t = i < topCpu[0].data.length ? formatLocalTime(new Date(topCpu[0].data[i].time)) : ''
        const vals = topCpu.map(p => i < p.data.length ? p.data[i].cpuPercent.toFixed(1) : '')
        rows.push(t + ',' + vals.join(','))
      }
      await writeTextFile(dir + 'perf_top_cpu.csv', 'Time,' + topCpu.map(p => `"${p.name}(%)"`).join(',') + '\n' + rows.join('\n'))
    }

    // Downsample for interactive HTML charts to keep file size manageable
    // 使用bucketing下采样保留极值，确保一周数据也能有效分析
    const DOWNSAMPLE_MAX = 4000
    const dsPts = bucketingDownsample(pts, p => p.cpu, DOWNSAMPLE_MAX)
    const dsTopMem = topMem.map(p => ({ ...p, data: bucketingDownsample(p.data, d => d.pssKb, DOWNSAMPLE_MAX) }))
    const dsTopCpu = topCpu.map(p => ({ ...p, data: bucketingDownsample(p.data, d => d.cpuPercent, DOWNSAMPLE_MAX) }))
    const interactiveHtml = buildInteractiveChartsHtml(dsPts, dsTopMem, dsTopCpu)
    const freeRamVals2 = pts.map(p => p.memAvailKb)
    const swapFreeVals2 = pts.map(p => p.swapFreeKb)
    const memFreeRows2 = `<tr><td></td><td><strong>Free RAM</strong></td><td>${formatKb(safeMin(freeRamVals2))} ${formatKbUnit(safeMin(freeRamVals2))}</td><td>${formatKb(safeMax(freeRamVals2))} ${formatKbUnit(safeMax(freeRamVals2))}</td><td>${formatKb(safeAvg(freeRamVals2))} ${formatKbUnit(safeAvg(freeRamVals2))}</td></tr>
<tr><td></td><td><strong>Swap Free</strong></td><td>${formatKb(safeMin(swapFreeVals2))} ${formatKbUnit(safeMin(swapFreeVals2))}</td><td>${formatKb(safeMax(swapFreeVals2))} ${formatKbUnit(safeMax(swapFreeVals2))}</td><td>${formatKb(safeAvg(swapFreeVals2))} ${formatKbUnit(safeAvg(swapFreeVals2))}</td></tr>
`
    await writeTextFile(dir + 'perf_report.html', `<!DOCTYPE html>
<html lang="zh">
<head><meta charset="utf-8"><title>性能报告</title>
<style>
body{font-family:system-ui,-apple-system,sans-serif;max-width:1400px;margin:auto;padding:2rem;background:#f5f5f5;color:#222}
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
  <p><strong>时间范围:</strong> ${formatLocalTime(new Date(pts[0].time))} ~ ${formatLocalTime(new Date(pts[pts.length-1].time))}</p>
  <p><strong>采集间隔:</strong> ${(store.intervalMs / 1000).toFixed(0)}s</p>
</div>
${buildOverallAssessment(pts, topMem, topCpu, '', [])}
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
  <tbody>${memFreeRows2}${topMem.map((p, i) => {
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
${interactiveHtml}
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
  colorMap.clear()
  cpuSelectedSeries.value = null
  topAppSelectedSeries.value = null
  cpuChart?.setOption({ series: [] }, { replaceMerge: ['series'] })
  topAppChart?.setOption({ series: [] }, { replaceMerge: ['series'] })
}

// Watch topAppCount changes to re-render chart
watch(() => store.topAppCount, () => { updateTopAppChartDebounced() })
watch(() => store.cpuTopNCount, () => { updateCpuChartDebounced() })

// Stable color assignment per process name: same package always gets same color
// across the whole session, regardless of its current rank in Top N.
const chartColors = ['#7c5cfc', '#22c55e', '#f59e0b', '#ef4444', '#3b82f6', '#ec4899', '#14b8a6', '#f97316', '#8b5cf6', '#06b6d4', '#84cc16', '#a855f7', '#f43f5e', '#0ea5e9', '#10b981', '#eab308', '#d946ef', '#6366f1', '#fb923c', '#14b8a6']
const colorMap = new Map<string, string>()
function getColor(name: string): string {
  if (!colorMap.has(name)) {
    colorMap.set(name, chartColors[colorMap.size % chartColors.length])
  }
  return colorMap.get(name)!
}

function initCharts() {
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
    // Click on line to select single series
    cpuChart.on('click', (params: any) => {
      if (params.componentType !== 'series') return
      const allNames = (cpuChart?.getOption().series as any[])?.map((s: any) => s.name) || []
      selectSeries(cpuChart, params.seriesName, cpuSelectedSeries, allNames)
    })
    // Click on legend to select single series
    cpuChart.on('legendselectchanged', (params: any) => {
      const clickedName = params.name
      const allNames = (cpuChart?.getOption().series as any[])?.map((s: any) => s.name) || []
      if (cpuSelectedSeries.value === clickedName) {
        // Click same series again, show all
        cpuSelectedSeries.value = null
        allNames.forEach(name => cpuChart?.dispatchAction({ type: 'legendSelect', name }))
      } else {
        // Click different series, show only this one
        cpuSelectedSeries.value = clickedName
        allNames.forEach(name => {
          if (name === clickedName) {
            cpuChart?.dispatchAction({ type: 'legendSelect', name })
          } else {
            cpuChart?.dispatchAction({ type: 'legendUnSelect', name })
          }
        })
      }
    })
    cpuChart.setOption({
      grid: { left: 45, right: 260, top: 15, bottom: 25 },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross',
          label: {
            show: true,
            backgroundColor: 'rgba(50,50,50,0.85)',
            borderColor: 'rgba(50,50,50,0.85)',
            borderWidth: 0,
            color: '#fff',
            fontSize: 10,
            padding: [4, 6],
            formatter: (params: any) => {
              if (params.axisDimension === 'x') {
                return new Date(params.value).toLocaleTimeString('zh-CN', { hour12: false })
              } else {
                return params.value.toFixed(1) + '%'
              }
            },
          },
        },
        confine: true,
        appendTo: 'body' as any,
        position: makeTooltipPosition(cpuChartRef),
        formatter: (params: any) => {
          // No tooltip when showing all lines
          if (!cpuSelectedSeries.value) return ''
          if (!params || !Array.isArray(params) || params.length === 0) return ''
          const time = new Date(params[0].axisValue).toLocaleTimeString('zh-CN', { hour12: false })
          const getVal = (p: any): number | null => {
            if (p.value == null) return null
            return Array.isArray(p.value) ? p.value[1] : p.value
          }
          const item = params.find((p: any) => p.seriesName === cpuSelectedSeries.value)
          if (!item) return ''
          const v = getVal(item)
          if (v == null || v < 0) return ''
          const vstr = (v as number).toFixed(1) + '%'
          return `<div><div style="font-weight:600;margin-bottom:4px">${time}</div>${item.marker} ${item.seriesName}: <b>${vstr}</b></div>`
        },
      },
      legend: {
        type: 'scroll',
        show: true,
        orient: 'vertical',
        right: 10,
        top: 'middle',
        itemWidth: 12,
        itemHeight: 10,
        textStyle: { fontSize: 11, width: 220, overflow: 'breakAll' },
        pageTextStyle: { fontSize: 11 },
        pageIconSize: [12, 12],
        animation: false,
        selectedMode: 'multiple',
      },
      xAxis: { type: 'time', axisLabel: timeAxisLabel },
      yAxis: { type: 'value', min: 0, max: 100, axisLabel: { fontSize: 10, formatter: '{value}%' } },
      dataZoom: [{ type: 'inside', start: 0, end: 100 }],
      progressive: 1000,
      progressiveThreshold: 1000,
      series: [],
    })
  }
  if (topAppChartRef.value && !topAppChart) {
    topAppChart = echarts.init(topAppChartRef.value)
    // Click on line to select single series
    topAppChart.on('click', (params: any) => {
      if (params.componentType !== 'series') return
      const allNames = (topAppChart?.getOption().series as any[])?.map((s: any) => s.name) || []
      selectSeries(topAppChart, params.seriesName, topAppSelectedSeries, allNames)
    })
    // Click on legend to select single series
    topAppChart.on('legendselectchanged', (params: any) => {
      const clickedName = params.name
      const allNames = (topAppChart?.getOption().series as any[])?.map((s: any) => s.name) || []
      if (topAppSelectedSeries.value === clickedName) {
        // Click same series again, show all
        topAppSelectedSeries.value = null
        allNames.forEach(name => topAppChart?.dispatchAction({ type: 'legendSelect', name }))
      } else {
        // Click different series, show only this one
        topAppSelectedSeries.value = clickedName
        allNames.forEach(name => {
          if (name === clickedName) {
            topAppChart?.dispatchAction({ type: 'legendSelect', name })
          } else {
            topAppChart?.dispatchAction({ type: 'legendUnSelect', name })
          }
        })
      }
    })
    topAppChart.setOption({
      grid: { left: 45, right: 260, top: 15, bottom: 25 },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross',
          label: {
            show: true,
            backgroundColor: 'rgba(50,50,50,0.85)',
            borderColor: 'rgba(50,50,50,0.85)',
            borderWidth: 0,
            color: '#fff',
            fontSize: 10,
            padding: [4, 6],
            formatter: (params: any) => {
              if (params.axisDimension === 'x') {
                return new Date(params.value).toLocaleTimeString('zh-CN', { hour12: false })
              } else {
                const v = params.value
                return v >= 1024 ? (v / 1024).toFixed(1) + 'MB' : v + 'KB'
              }
            },
          },
        },
        confine: true,
        appendTo: 'body' as any,
        position: makeTooltipPosition(topAppChartRef),
        formatter: (params: any) => {
          // No tooltip when showing all lines
          if (!topAppSelectedSeries.value) return ''
          if (!params || !Array.isArray(params) || params.length === 0) return ''
          const time = new Date(params[0].axisValue).toLocaleTimeString('zh-CN', { hour12: false })
          const getVal = (p: any): number | null => {
            if (p.value == null) return null
            return Array.isArray(p.value) ? p.value[1] : p.value
          }
          const item = params.find((p: any) => p.seriesName === topAppSelectedSeries.value)
          if (!item) return ''
          const v = getVal(item)
          if (v == null || v < 0) return ''
          const vstr = (v as number) >= 1024 ? ((v as number) / 1024).toFixed(1) + 'MB' : (v as number) + 'KB'
          return `<div><div style="font-weight:600;margin-bottom:4px">${time}</div>${item.marker} ${item.seriesName}: <b>${vstr}</b></div>`
        },
      },
      legend: {
        type: 'scroll',
        show: true,
        orient: 'vertical',
        right: 10,
        top: 'middle',
        itemWidth: 12,
        itemHeight: 10,
        textStyle: { fontSize: 11, width: 220, overflow: 'breakAll' },
        pageTextStyle: { fontSize: 11 },
        pageIconSize: [12, 12],
        animation: false,
        selectedMode: 'multiple',
      },
      xAxis: { type: 'time', axisLabel: { ...timeAxisLabel, fontSize: 10 } },
      yAxis: { type: 'value', axisLabel: { fontSize: 10, formatter: (v: number) => v >= 1024 ? (v / 1024).toFixed(0) + 'M' : v + 'K' } },
      dataZoom: [{ type: 'inside', start: 0, end: 100 }],
      progressive: 1000,
      progressiveThreshold: 1000,
      series: [],
      animationDuration: 300,
    })

  }
}

function resizeCharts() {
  if (chartVisibility.value.cpu) cpuChart?.resize()
  if (chartVisibility.value.topApp) topAppChart?.resize()
}

function setupResizeObserver() {
  if (chartResizeObserver) return
  const containers = [cpuChartRef.value, topAppChartRef.value].filter(Boolean)
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
        updateCpuChartDebounced(); updateTopAppChartDebounced()
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
  topAppChart?.dispose(); topAppChart = null
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
