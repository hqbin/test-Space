<template>
  <div ref="reportRoot" class="flex flex-col flex-1 min-h-0 box-border select-none overflow-x-hidden overflow-y-auto">
    <!-- Loading -->
    <div v-if="loading" class="flex-1 flex items-center justify-center">
      <span class="material-symbols-outlined text-3xl text-on-surface-variant/40 animate-spin">refresh</span>
    </div>

    <template v-else-if="record">
      <div class="min-w-0 w-full">
      <!-- Header row 1: back + info + status -->
      <div class="flex items-center gap-2 mb-2 flex-shrink-0 px-3">
        <button class="glass-button px-2 py-1.5 rounded text-[11px] flex items-center gap-1 select-none" @click="emit('back')">
          <span class="material-symbols-outlined text-[13px]">arrow_back</span>
          <span>{{ t('report.back') }}</span>
        </button>
        <div class="text-[11px] text-on-surface-variant/60 flex items-center gap-1.5">
          <span>{{ record.startedAt ? new Date(record.startedAt).toLocaleString() : '-' }}</span>
          <span class="w-1 h-1 rounded-full bg-on-surface-variant/20"></span>
          <span>{{ record.deviceSerial || t('report.noDevice') }}</span>
        </div>
        <span class="glass-panel px-2 py-0.5 rounded text-[11px] font-medium"
          :class="record.status === 'done' ? 'text-green-400 bg-green-500/10' : record.status === 'failed' || record.status === 'aborted' ? 'text-red-400 bg-red-500/10' : 'text-blue-400 bg-blue-500/10'">
          {{ record.status }}
        </span>
        <div class="flex-1"></div>
        <button class="glass-button px-2 py-1 rounded text-[10px] flex items-center gap-1 select-none" @click="exportHtml">
          <span class="material-symbols-outlined text-[12px]">file_download</span>
          <span>HTML</span>
        </button>
        <button class="glass-button px-2 py-1 rounded text-[10px] flex items-center gap-1 select-none" @click="exportPdf">
          <span class="material-symbols-outlined text-[12px]">picture_as_pdf</span>
          <span>PDF</span>
        </button>
        <button class="glass-button px-2 py-1 rounded text-[10px] flex items-center gap-1 select-none" @click="exportJson">
          <span class="material-symbols-outlined text-[12px]">data_object</span>
          <span>JSON</span>
        </button>
      </div>

      <!-- Summary bar -->
      <div class="flex items-center gap-3 mb-3 flex-shrink-0 px-3">
        <div class="flex-1 flex items-center gap-3 px-3 py-1.5 glass-panel rounded-lg text-[11px] text-on-surface-variant/70 min-w-0 overflow-x-auto">
          <span>{{ t('report.total') }}: <strong class="text-on-surface">{{ record.total }}</strong></span>
          <span class="w-1 h-1 rounded-full bg-on-surface-variant/20 flex-shrink-0"></span>
          <span class="text-green-400 flex-shrink-0">{{ t('report.passed') }}: <strong>{{ record.passed }}</strong></span>
          <span class="w-1 h-1 rounded-full bg-on-surface-variant/20 flex-shrink-0"></span>
          <span class="text-red-400 flex-shrink-0">{{ t('report.failed') }}: <strong>{{ record.failed }}</strong></span>
          <span class="w-1 h-1 rounded-full bg-on-surface-variant/20 flex-shrink-0"></span>
          <span class="text-orange-400 flex-shrink-0">{{ t('report.healed') }}: <strong>{{ record.healed }}</strong></span>
          <span class="w-1 h-1 rounded-full bg-on-surface-variant/20 flex-shrink-0"></span>
          <span class="text-gray-400 flex-shrink-0">{{ t('report.skipped') }}: <strong>{{ record.skipped }}</strong></span>
          <span class="flex-shrink-0">{{ t('report.duration') }}: {{ record.durationMs }}ms</span>
        </div>
      </div>

      <!-- Metric Cards Row -->
      <div class="grid grid-cols-4 gap-2 mb-3 flex-shrink-0 px-3">
        <div class="glass-panel rounded-lg p-3 text-center min-w-0">
          <div class="text-2xl font-bold text-on-surface">{{ record.total }}</div>
          <div class="text-[11px] text-on-surface-variant/60 mt-1">{{ t('report.total') }}</div>
        </div>
        <div class="glass-panel rounded-lg p-3 text-center min-w-0" style="background: linear-gradient(135deg, rgba(34,197,94,0.15), rgba(34,197,94,0.05));">
          <div class="text-2xl font-bold text-green-400">{{ record.passed }}</div>
          <div class="text-[11px] text-green-400/60 mt-1">{{ t('report.passed') }}</div>
        </div>
        <div class="glass-panel rounded-lg p-3 text-center min-w-0" style="background: linear-gradient(135deg, rgba(239,68,68,0.15), rgba(239,68,68,0.05));">
          <div class="text-2xl font-bold text-red-400">{{ record.failed }}</div>
          <div class="text-[11px] text-red-400/60 mt-1">{{ t('report.failed') }}</div>
        </div>
        <div class="glass-panel rounded-lg p-3 text-center min-w-0" style="background: linear-gradient(135deg, rgba(249,115,22,0.15), rgba(249,115,22,0.05));">
          <div class="text-2xl font-bold text-orange-400">{{ record.healed }}</div>
          <div class="text-[11px] text-orange-400/60 mt-1">{{ t('report.healed') }}</div>
        </div>
      </div>

      <!-- Status Distribution Bar -->
      <div v-if="record.total > 0" class="flex-shrink-0 px-3 mb-3 glass-panel rounded-lg overflow-hidden h-6 flex">
        <div v-if="record.passed > 0" class="flex items-center justify-center text-[11px] font-medium text-white/90 transition-all" :style="{ width: (record.passed / record.total * 100) + '%', background: '#22c55e' }">{{ record.passed }}</div>
        <div v-if="record.failed > 0" class="flex items-center justify-center text-[11px] font-medium text-white/90 transition-all" :style="{ width: (record.failed / record.total * 100) + '%', background: '#ef4444' }">{{ record.failed }}</div>
        <div v-if="record.healed > 0" class="flex items-center justify-center text-[11px] font-medium text-white/90 transition-all" :style="{ width: (record.healed / record.total * 100) + '%', background: '#f97316' }">{{ record.healed }}</div>
        <div v-if="record.skipped > 0" class="flex items-center justify-center text-[11px] font-medium text-white/90 transition-all" :style="{ width: (record.skipped / record.total * 100) + '%', background: '#94a3b8' }">{{ record.skipped }}</div>
      </div>

      <!-- Trend Comparison -->
      <div v-if="prevRecord" class="flex-shrink-0 px-3 mb-3">
        <div class="glass-panel rounded-lg px-4 py-2.5">
        <div class="text-[11px] font-medium text-on-surface-variant/80 mb-2 flex items-center gap-1.5">
          <span class="material-symbols-outlined text-[14px]">trending_up</span>
          {{ t('report.trendTitle') }}
        </div>
        <div class="flex items-center gap-4 text-[11px]">
          <span class="flex items-center gap-1">
            <span class="text-red-400 material-symbols-outlined text-[14px]">arrow_upward</span>
            {{ t('report.newFails') }}: <strong class="text-red-400">{{ Math.max(0, (record?.failed || 0) - (prevRecord.failed || 0)) }}</strong>
          </span>
          <span class="flex items-center gap-1">
            <span class="text-green-400 material-symbols-outlined text-[14px]">arrow_downward</span>
            {{ t('report.fixedIssues') }}: <strong class="text-green-400">{{ Math.max(0, (prevRecord.failed || 0) - (record?.failed || 0)) }}</strong>
          </span>
          <span class="flex items-center gap-1">
            <span class="text-blue-400 material-symbols-outlined text-[14px]">add</span>
            {{ t('report.newCases') }}: <strong class="text-blue-400">{{ Math.abs((record?.total || 0) - (prevRecord.total || 0)) }}</strong>
          </span>
        </div>
        </div>
      </div>

      <!-- Tag Filter Row -->
      <div v-if="uniqueTags.length > 0" class="flex-shrink-0 px-3 mb-3 flex items-center gap-1.5 flex-wrap">
        <span class="text-[10px] text-on-surface-variant/40 mr-1">{{ t('report.tags') }}:</span>
        <button v-for="tag in uniqueTags" :key="tag"
          class="px-2.5 py-0.5 rounded-full text-[10px] transition-all select-none"
          :class="activeTags.has(tag) ? 'bg-purple-500/30 text-purple-300 border border-purple-500/40' : 'bg-white/5 text-on-surface-variant/60 border border-white/10 hover:border-white/20'"
          @click="toggleTag(tag)">
          {{ tag }}
        </button>
        <button v-if="activeTags.size > 0" class="text-[10px] text-on-surface-variant/40 hover:text-on-surface-variant/80 ml-1 select-none" @click="activeTags.clear()">
          {{ t('report.clearFilter') }}
        </button>
      </div>

      <!-- Step Timeline -->
      <div class="flex-1 overflow-y-auto custom-scrollbar px-3">
        <div v-if="filteredSteps.length === 0" class="flex items-center justify-center h-full text-on-surface-variant/40 text-[12px]">
          {{ t('report.noSteps') }}
        </div>
        <div v-for="(step, idx) in filteredSteps" :key="step.id" class="relative pl-8 pb-3">
          <!-- Timeline line -->
          <div v-if="idx < filteredSteps.length - 1" class="absolute left-[11px] top-4 bottom-0 w-0.5" :class="step.status === 'passed' ? 'bg-green-500/20' : step.status === 'failed' ? 'bg-red-500/20' : step.status === 'healed' ? 'bg-orange-500/20' : 'bg-gray-500/20'"></div>
          <!-- Status dot -->
          <div class="absolute left-0 top-1 w-6 h-6 rounded-full flex items-center justify-center"
            :class="step.status === 'passed' ? 'bg-green-500/20' : step.status === 'failed' ? 'bg-red-500/20' : step.status === 'healed' ? 'bg-orange-500/20' : 'bg-gray-500/20'">
            <span class="material-symbols-outlined text-[14px]"
              :class="step.status === 'passed' ? 'text-green-400' : step.status === 'failed' ? 'text-red-400' : step.status === 'healed' ? 'text-orange-400' : 'text-gray-400'">
              {{ step.status === 'passed' ? 'check' : step.status === 'failed' ? 'close' : step.status === 'healed' ? 'settings' : 'radio_button_unchecked' }}
            </span>
          </div>

          <!-- Step card -->
          <div class="glass-panel rounded-2xl overflow-hidden transition-all" :class="expandedSteps.has(step.id) ? 'bg-white/50' : 'bg-white/30 hover:bg-white/40'">
            <div class="px-4 py-2.5 flex items-center gap-3 cursor-pointer select-none" @click="toggleStep(step.id)">
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2">
                  <span class="text-[12px] font-semibold text-on-surface">{{ step.stepId }}</span>
                  <span v-if="step.stepDesc" class="text-[11px] text-on-surface-variant/60 truncate">{{ step.stepDesc }}</span>
                </div>
                <div class="flex items-center gap-3 mt-1">
                  <span class="text-[10px] text-on-surface-variant/40 flex items-center gap-1">
                    <span class="material-symbols-outlined text-[11px]">touch_app</span>
                    {{ step.locatorUsed || '-' }}
                  </span>
                  <span class="text-[10px] text-on-surface-variant/40 flex items-center gap-1">
                    <span class="material-symbols-outlined text-[11px]">timer</span>
                    {{ step.durationMs }}ms
                  </span>
                </div>
              </div>
              <span class="text-[10px] px-2 py-0.5 rounded-full font-medium flex-shrink-0" :class="statusBadgeClass(step.status)">{{ step.status }}</span>
              <span class="material-symbols-outlined text-[14px] text-on-surface-variant/30 transition-transform" :class="expandedSteps.has(step.id) ? '' : '-rotate-90'">expand_more</span>
            </div>

            <!-- Expanded content -->
            <div v-if="expandedSteps.has(step.id)" class="px-4 pb-3 space-y-2 border-t border-white/10 pt-2">
              <!-- Screenshots -->
              <div v-if="step.screenshotBefore || step.screenshotAfter" class="grid grid-cols-2 gap-2 max-w-full">
                <div v-if="step.screenshotBefore" class="glass-panel rounded-xl p-2 bg-white/20">
                  <div class="text-[10px] text-on-surface-variant/40 mb-1">{{ t('report.beforeScreenshot') }}</div>
                  <img :src="convertFileSrc(step.screenshotBefore)" class="w-full rounded-lg cursor-pointer hover:opacity-80 transition-opacity" @click="viewScreenshot(step.screenshotBefore!)" />
                </div>
                <div v-if="step.screenshotAfter" class="glass-panel rounded-xl p-2 bg-white/20">
                  <div class="text-[10px] text-on-surface-variant/40 mb-1">{{ t('report.afterScreenshot') }}</div>
                  <img :src="convertFileSrc(step.screenshotAfter)" class="w-full rounded-lg cursor-pointer hover:opacity-80 transition-opacity" @click="viewScreenshot(step.screenshotAfter!)" />
                </div>
              </div>
              <div v-if="!step.screenshotBefore && !step.screenshotAfter" class="text-[10px] text-on-surface-variant/30 italic">
                {{ t('report.noScreenshots') }}
              </div>

              <!-- Screenshot diff overlay (when both before and ref exist) -->
              <div v-if="step.screenshotBefore && step.screenshotRef" class="glass-panel rounded-xl p-2 bg-white/20">
                <div class="text-[10px] text-on-surface-variant/40 mb-1">{{ t('report.screenshotDiff') }}</div>
                <div class="relative inline-block max-w-full">
                  <img :src="convertFileSrc(step.screenshotBefore)" class="w-full rounded-lg opacity-60" />
                  <img :src="convertFileSrc(step.screenshotRef)" class="absolute inset-0 w-full h-full rounded-lg mix-blend-difference opacity-40" />
                </div>
                <div class="flex gap-2 mt-1">
                  <span class="text-[9px] px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-400">{{ t('report.actual') }}</span>
                  <span class="text-[9px] px-1.5 py-0.5 rounded bg-orange-500/10 text-orange-400">{{ t('report.expected') }}</span>
                </div>
              </div>
              <!-- Reference screenshot (standalone) -->
              <div v-if="step.screenshotRef && !step.screenshotBefore" class="glass-panel rounded-xl p-2 bg-white/20">
                <div class="text-[10px] text-on-surface-variant/40 mb-1">{{ t('report.refScreenshot') }}</div>
                <img :src="convertFileSrc(step.screenshotRef)" class="w-full rounded-lg cursor-pointer hover:opacity-80 transition-opacity max-w-sm" @click="viewScreenshot(step.screenshotRef!)" />
              </div>

              <!-- Error message -->
              <div v-if="step.errorMessage" class="text-[11px] text-red-400/90 bg-red-500/10 rounded-xl px-3 py-2 leading-relaxed">
                <span class="material-symbols-outlined text-[13px] align-text-bottom mr-1">error</span>
                {{ step.errorMessage }}
              </div>

              <!-- AI heal log -->
              <div v-if="step.healLog" class="text-[11px] text-orange-400/90 bg-orange-500/10 rounded-xl px-3 py-2 leading-relaxed">
                <span class="material-symbols-outlined text-[13px] align-text-bottom mr-1">healing</span>
                <template v-if="step.healLog.startsWith('{') || step.healLog.startsWith('[')">
                  <div class="space-y-1">
                    <div v-if="parseHealLog(step.healLog)?.description">{{ parseHealLog(step.healLog)?.description }}</div>
                    <div v-if="parseHealLog(step.healLog)?.phase || parseHealLog(step.healLog)?.method" class="flex gap-2 text-[10px]">
                      <span v-if="parseHealLog(step.healLog)?.phase" class="px-1.5 py-0.5 rounded bg-orange-500/20">{{ t('report.healPhase') }} {{ parseHealLog(step.healLog)?.phase }}</span>
                      <span v-if="parseHealLog(step.healLog)?.method" class="px-1.5 py-0.5 rounded bg-orange-500/20">{{ parseHealLog(step.healLog)?.method }}</span>
                      <span v-if="parseHealLog(step.healLog)?.confidence" class="px-1.5 py-0.5 rounded bg-orange-500/20">{{ t('report.confidence') }} {{ ((parseHealLog(step.healLog)?.confidence ?? 0) * 100).toFixed(0) }}%</span>
                    </div>
                  </div>
                </template>
                <span v-else>{{ step.healLog }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div></template>

    <!-- Empty state -->
    <div v-else class="flex-1 flex items-center justify-center text-on-surface-variant/40">
      <div class="text-center">
        <span class="material-symbols-outlined text-5xl mb-3 block">assignment</span>
        <p class="text-[14px]">{{ t('report.notFound') }}</p>
      </div>
    </div>

    <!-- Screenshot zoom overlay -->
    <Teleport to="body">
      <div v-if="zoomScreenshot" class="fixed inset-0 z-50 flex items-center justify-center" @click.self="closeZoom">
        <div class="absolute inset-0 bg-black/60 backdrop-blur-sm"></div>
        <img :src="zoomScreenshot" class="max-w-[90vw] max-h-[90vh] object-contain relative z-10 rounded-2xl shadow-2xl cursor-pointer" @click="closeZoom" />
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
defineOptions({ name: 'ReportViewer' })
import { ref, computed, onMounted } from "vue"
import * as db from "@/services/database"
import type { AutoRunRecord, AutoRunStep } from "@/types"
import { useI18n } from "@/composables/useI18n"
import { convertFileSrc } from "@tauri-apps/api/core"

const props = defineProps<{
  runId: string
}>()
const emit = defineEmits<{
  back: []
}>()

const { t } = useI18n()

const reportRoot = ref<HTMLElement | null>(null)
const record = ref<AutoRunRecord | null>(null)
const prevRecord = ref<AutoRunRecord | null>(null)
const steps = ref<AutoRunStep[]>([])
const caseNameMap = ref<Record<string, string>>({})
const loading = ref(true)
const expandedSteps = ref<Set<string>>(new Set())
const activeTags = ref<Set<string>>(new Set())
const zoomScreenshot = ref<string | null>(null)

const uniqueTags = computed(() => {
  const tags = new Set<string>()
  for (const s of steps.value) {
    const name = caseNameMap.value[s.caseId]
    if (name) {
      const parts = name.split(/[/\s]/)
      for (const p of parts) {
        const trimmed = p.trim()
        if (trimmed.startsWith('@')) tags.add(trimmed)
      }
    }
  }
  return Array.from(tags).sort()
})

const filteredSteps = computed(() => {
  if (activeTags.value.size === 0) return steps.value
  return steps.value.filter(s => {
    const name = caseNameMap.value[s.caseId] || ''
    return Array.from(activeTags.value).some(tag => name.includes(tag))
  })
})

function toggleStep(id: string) {
  if (expandedSteps.value.has(id)) expandedSteps.value.delete(id)
  else expandedSteps.value.add(id)
}

function toggleTag(tag: string) {
  if (activeTags.value.has(tag)) activeTags.value.delete(tag)
  else activeTags.value.add(tag)
}

function viewScreenshot(path: string) {
  zoomScreenshot.value = convertFileSrc(path)
}

function parseHealLog(log: string | null): { description?: string; phase?: number; method?: string; confidence?: number } | null {
  if (!log) return null
  try { return JSON.parse(log) } catch { return { description: log } }
}

function closeZoom() {
  zoomScreenshot.value = null
}

function statusBadgeClass(status: string) {
  switch (status) {
    case 'passed': return 'bg-green-500/20 text-green-400'
    case 'failed': return 'bg-red-500/20 text-red-400'
    case 'healed': return 'bg-orange-500/20 text-orange-400'
    default: return 'bg-gray-500/20 text-gray-400'
  }
}

async function exportPdf() {
  try {
    const { save } = await import("@tauri-apps/plugin-dialog")
    const { writeFile } = await import("@tauri-apps/plugin-fs")
    const path = await save({ defaultPath: `report-${record.value?.id}.pdf`, filters: [{ name: "PDF", extensions: ["pdf"] }] })
    if (!path) return
    const { default: htmlToImage } = await import("html-to-image")
    const { jsPDF } = await import("jspdf")
    const el = reportRoot.value
    if (!el) return
    const imgData = await htmlToImage.toPng(el, { backgroundColor: '#f0f2f5' })
    const pdf = new jsPDF('p', 'mm', 'a4')
    const imgWidth = 210
    const imgHeight = (imgWidth * el.offsetHeight) / el.offsetWidth
    pdf.addImage(imgData, 'PNG', 0, 0, imgWidth, imgHeight)
    const pdfBytes = pdf.output('arraybuffer')
    await writeFile(path, new Uint8Array(pdfBytes))
  } catch (e: any) {
    console.error('[Report] PDF export failed:', e)
  }
}

async function exportHtml() {
  const { save } = await import("@tauri-apps/plugin-dialog")
  const { writeTextFile } = await import("@tauri-apps/plugin-fs")
  const path = await save({ defaultPath: `report-${record.value?.id}.html`, filters: [{ name: "HTML", extensions: ["html"] }] })
  if (!path) return
  const rows = steps.value.map(s => `
    <tr class="${s.status}">
      <td>${s.stepId}</td>
      <td>${s.stepDesc || ''}</td>
      <td>${s.status}</td>
      <td>${s.durationMs}ms</td>
      <td>${s.errorMessage ? `<div class="error">${s.errorMessage}</div>` : ''}${s.healLog ? `<div class="heal">${s.healLog}</div>` : ''}</td>
    </tr>`).join('')
  const html = `<!DOCTYPE html><html><head><meta charset="utf-8"><title>Test Report</title>
<style>body{font-family:sans-serif;max-width:1200px;margin:auto;padding:20px;background:#f5f5f5}
h1{color:#333}.summary{display:flex;gap:16px;margin:16px 0;flex-wrap:wrap}
.card{padding:16px;border-radius:12px;background:white;box-shadow:0 1px 4px rgba(0,0,0,.1);min-width:100px;text-align:center}
.card .num{font-size:28px;font-weight:bold}.card .lbl{font-size:11px;color:#666;margin-top:4px}
table{width:100%;border-collapse:collapse;background:white;border-radius:12px;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,.1)}
th{background:#f8f8f8;padding:10px 12px;text-align:left;font-size:12px;color:#666;border-bottom:1px solid #eee}
td{padding:10px 12px;font-size:13px;border-bottom:1px solid #f0f0f0}
.passed td:first-child{border-left:3px solid #22c55e}
.failed td:first-child{border-left:3px solid #ef4444}
.healed td:first-child{border-left:3px solid #f97316}
.skipped td:first-child{border-left:3px solid #94a3b8}
.error{background:#fef2f2;padding:6px 8px;border-radius:4px;margin:4px 0;color:#dc2626;font-size:12px}
.heal{background:#fff7ed;padding:6px 8px;border-radius:4px;margin:4px 0;color:#ea580c;font-size:12px}</style></head><body>
<h1>Test Report</h1>
<p>Run ID: ${record.value?.id} | Status: ${record.value?.status} | Device: ${record.value?.deviceSerial || '-'}</p>
<p>${record.value?.startedAt ? new Date(record.value?.startedAt).toLocaleString() : ''}</p>
<div class="summary">
  <div class="card"><div class="num">${record.value?.total || 0}</div><div class="lbl">Total</div></div>
  <div class="card" style="color:#22c55e"><div class="num" style="color:#22c55e">${record.value?.passed || 0}</div><div class="lbl">Passed</div></div>
  <div class="card" style="color:#ef4444"><div class="num" style="color:#ef4444">${record.value?.failed || 0}</div><div class="lbl">Failed</div></div>
  <div class="card" style="color:#f97316"><div class="num" style="color:#f97316">${record.value?.healed || 0}</div><div class="lbl">Healed</div></div>
  <div class="card" style="color:#94a3b8"><div class="num" style="color:#94a3b8">${record.value?.skipped || 0}</div><div class="lbl">Skipped</div></div>
  <div class="card"><div class="num">${record.value?.durationMs || 0}ms</div><div class="lbl">Duration</div></div>
</div>
<table><thead><tr><th>Step</th><th>Description</th><th>Status</th><th>Duration</th><th>Details</th></tr></thead><tbody>${rows}</tbody></table></body></html>`
  await writeTextFile(path, html)
}

async function exportJson() {
  const { save } = await import("@tauri-apps/plugin-dialog")
  const { writeTextFile } = await import("@tauri-apps/plugin-fs")
  const path = await save({ defaultPath: `summary-${record.value?.id}.json`, filters: [{ name: "JSON", extensions: ["json"] }] })
  if (!path) return
  const summary = {
    runId: record.value?.id,
    status: record.value?.status,
    deviceSerial: record.value?.deviceSerial,
    startedAt: record.value?.startedAt,
    endedAt: record.value?.endedAt,
    total: record.value?.total,
    passed: record.value?.passed,
    failed: record.value?.failed,
    healed: record.value?.healed,
    skipped: record.value?.skipped,
    durationMs: record.value?.durationMs,
    steps: steps.value.map(s => ({
      id: s.id,
      stepId: s.stepId,
      stepDesc: s.stepDesc,
      caseId: s.caseId,
      status: s.status,
      durationMs: s.durationMs,
      errorMessage: s.errorMessage,
      healLog: s.healLog,
      locatorUsed: s.locatorUsed,
    })),
  }
  await writeTextFile(path, JSON.stringify(summary, null, 2))
}

async function loadPrevRecord() {
  try {
    const allRecords = await db.listAutoRunRecords(2)
    const others = allRecords.filter(r => r.id !== props.runId)
    if (others.length > 0) prevRecord.value = others[0]
  } catch {}
}

onMounted(async () => {
  try {
    loading.value = true
    record.value = await db.loadAutoRunRecord(props.runId)
    steps.value = await db.listAutoRunSteps(props.runId)
    const caseIds = new Set(steps.value.map(s => s.caseId))
    for (const id of caseIds) {
      const c = await db.loadAutoCase(id)
      if (c) caseNameMap.value[id] = c.name
    }
    await loadPrevRecord()
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.15s ease;
}
.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}
</style>
