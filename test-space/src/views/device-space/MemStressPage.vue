<template>
  <div class="flex flex-col gap-3 flex-1 min-h-0 overflow-hidden select-none">
    <!-- Header -->
    <div class="glass-panel rounded-xl px-4 py-2.5 flex items-center gap-3 flex-wrap shrink-0">
      <button class="glass-button px-3 py-1.5 rounded-lg font-label-md text-label-md" @click="goBack">{{ t('device.back') }}</button>
      <div class="h-5 w-[1px] bg-glass-border-dark"></div>
      <span class="material-symbols-outlined text-[18px] text-secondary">memory</span>
      <span class="font-label-lg text-label-lg text-on-surface">{{ t('memStress.title') }}</span>
      <span class="h-4 w-[1px] bg-glass-border-dark"></span>
      <span class="font-body-sm text-body-sm text-on-surface-variant flex items-center gap-1">
        <span class="material-symbols-outlined text-[14px]">smartphone</span>
        {{ deviceSerial || t('memStress.noDevice') }}
      </span>
      <span v-if="deviceAbi" class="px-2 py-0.5 rounded-full bg-secondary/10 text-secondary border border-secondary/20 font-mono text-[11px]">{{ deviceAbi }}</span>
      <span class="flex items-center gap-1.5 px-2 py-0.5 rounded-full border" :class="deployChipClass">
        <span class="w-1.5 h-1.5 rounded-full" :class="deployDotClass"></span>
        <span class="font-caption text-caption">{{ deployLabel }}</span>
      </span>
      <div class="flex-1"></div>
      <button class="glass-button p-1.5 rounded-lg" :title="t('memStress.redeploy')" :disabled="deploying" @click="deploy(true)">
        <span class="material-symbols-outlined text-[16px]" :class="deploying ? 'animate-spin' : ''">refresh</span>
      </button>
      <button class="glass-button p-1.5 rounded-lg" :title="t('memStress.exportLog')" :disabled="isRunning || exportingLog || !deployed" @click="exportLog">
        <span class="material-symbols-outlined text-[16px]">file_download</span>
      </button>
    </div>

    <!-- Deployment progress strip -->
    <Transition name="fade">
      <div v-if="deploying || deployError" class="glass-panel rounded-xl px-4 py-2 flex items-center gap-3 shrink-0">
        <div class="flex items-center gap-3 flex-wrap">
          <template v-for="s in deploySteps" :key="s.key">
            <span class="flex items-center gap-1">
              <span class="material-symbols-outlined text-[14px]" :class="stepIconClass(s.key)">{{ stepIcon(s.key) }}</span>
              <span class="font-caption text-caption text-on-surface-variant">{{ t(s.label) }}</span>
            </span>
          </template>
        </div>
        <div class="flex-1"></div>
        <span class="font-caption text-caption max-w-[60%] truncate" :class="deployError ? 'text-error' : 'text-on-surface-variant'"
          :title="deployError || deployMessage">{{ deployError || deployMessage }}</span>
      </div>
    </Transition>

    <!-- Row 1: stress parameters + start button -->
    <div class="glass-panel rounded-xl px-4 py-2 flex items-center gap-3 flex-wrap shrink-0">
      <h3 class="font-label-md text-label-md text-on-surface flex items-center gap-2">
        <span class="material-symbols-outlined text-[16px] text-secondary">tune</span>{{ t('memStress.params') }}
      </h3>
      <span class="h-4 w-[1px] bg-glass-border-dark"></span>
      <label class="flex items-center gap-1.5">
        <span class="font-body-sm text-body-sm text-on-surface-variant">{{ t('memStress.totalMem') }}</span>
        <input v-model.number="totalMemMb" type="number" min="32" max="16384" step="32"
          class="w-20 bg-white/60 border border-outline-variant/50 rounded-lg px-2 py-1 text-right font-mono text-[12px] outline-none focus:ring-2 focus:ring-secondary/40 select-text" />
        <span class="font-caption text-caption text-on-surface-variant">MB</span>
      </label>
      <label class="flex items-center gap-1.5">
        <span class="font-body-sm text-body-sm text-on-surface-variant">{{ t('memStress.workers') }}</span>
        <input v-model.number="workers" type="number" min="1" max="8" step="1"
          class="w-14 bg-white/60 border border-outline-variant/50 rounded-lg px-2 py-1 text-right font-mono text-[12px] outline-none focus:ring-2 focus:ring-secondary/40 select-text" />
      </label>
      <label class="flex items-center gap-1.5">
        <span class="font-body-sm text-body-sm text-on-surface-variant">{{ t('memStress.duration') }}</span>
        <input v-model.number="durationMin" type="number" min="1" max="60" step="1" :disabled="isRunning"
          class="w-14 bg-white/60 border border-outline-variant/50 rounded-lg px-2 py-1 text-right font-mono text-[12px] outline-none focus:ring-2 focus:ring-secondary/40 select-text disabled:opacity-50" />
        <span class="font-caption text-caption text-on-surface-variant">{{ t('memStress.minutes') }}</span>
      </label>
      <span v-if="overcommit" class="font-caption text-caption text-error">{{ t('memStress.overcommit') }}</span>
      <div class="flex-1"></div>
      <template v-if="isRunning">
        <span class="flex items-center gap-1.5 font-caption text-caption text-on-surface">
          <span class="w-1.5 h-1.5 rounded-full bg-success-indicator animate-pulse"></span>{{ t('memStress.running') }}
        </span>
        <span class="font-mono text-[11px] text-on-surface-variant">{{ mmss(elapsed) }} / {{ mmss(totalSec) }}</span>
        <div class="w-28 h-1.5 rounded-full bg-outline-variant/30 overflow-hidden">
          <div class="h-full bg-secondary transition-all duration-500" :style="{ width: progressPct + '%' }"></div>
        </div>
        <button class="glass-button px-3 py-1.5 rounded-lg font-label-md text-label-md flex items-center gap-1 text-error"
          :disabled="stopping" @click="stopStress">
          <span class="material-symbols-outlined text-[16px]">stop_circle</span>{{ stopping ? t('memStress.stopping') : t('memStress.stop') }}
        </button>
      </template>
      <button v-else class="glass-button px-3 py-1.5 rounded-lg font-label-md text-label-md flex items-center gap-1"
        :disabled="!canStart" @click="startStress">
        <span class="material-symbols-outlined text-[16px]">play_arrow</span>{{ starting ? t('memStress.starting') : t('memStress.start') }}
      </button>
    </div>

    <!-- Row 2: live memory -->
    <div class="glass-panel rounded-xl px-4 py-2 flex items-center gap-4 flex-wrap shrink-0">
      <h3 class="font-label-md text-label-md text-on-surface flex items-center gap-2">
        <span class="material-symbols-outlined text-[16px] text-secondary">monitor_heart</span>{{ t('memStress.memory') }}
      </h3>
      <span class="flex items-center gap-1.5 font-caption text-caption text-on-surface-variant">
        <span class="w-1.5 h-1.5 rounded-full" :class="memSampling ? 'bg-success-indicator animate-pulse' : 'bg-outline-variant'"></span>
        {{ memSampling ? t('memStress.sampling') : t('memStress.paused') }}
      </span>
      <span class="h-4 w-[1px] bg-glass-border-dark"></span>
      <div class="flex items-center gap-4 flex-wrap">
        <span class="font-body-sm text-body-sm text-on-surface-variant">{{ t('memStress.total') }}
          <strong class="font-mono text-[12px] text-on-surface ml-1">{{ mem.totalMb }} MB</strong></span>
        <span class="font-body-sm text-body-sm text-on-surface-variant">{{ t('memStress.available') }}
          <strong class="font-mono text-[12px] text-success-indicator ml-1">{{ mem.availMb }} MB</strong></span>
        <span class="font-body-sm text-body-sm text-on-surface-variant">{{ t('memStress.used') }}
          <strong class="font-mono text-[12px] text-error ml-1">{{ mem.usedMb }} MB</strong></span>
        <span class="font-body-sm text-body-sm text-on-surface-variant">{{ t('memStress.usage') }}
          <strong class="font-mono text-[12px] text-on-surface ml-1">{{ mem.usage.toFixed(1) }}%</strong></span>
      </div>
      <div class="flex-1"></div>
      <span class="font-caption text-caption text-on-surface-variant truncate" :title="stressVersion || deployHint">
        {{ stressVersion || deployHint }}
      </span>
    </div>

    <!-- Row 3: app process query + LMK events -->
    <div class="grid grid-cols-2 gap-3 flex-1 min-h-0">
      <!-- App processes -->
      <div class="glass-panel rounded-xl p-4 flex flex-col gap-2 min-h-0">
        <div class="flex items-center gap-2 shrink-0">
          <h3 class="font-label-md text-label-md text-on-surface flex items-center gap-2">
            <span class="material-symbols-outlined text-[16px] text-secondary">apps</span>{{ t('memStress.apps') }}
          </h3>
          <span class="font-caption text-caption text-on-surface-variant">{{ t('memStress.appSummary', { running: String(appStats.running), killed: String(appStats.killed) }) }}</span>
          <div class="flex-1"></div>
          <button class="glass-hover rounded-lg p-1" :title="t('device.refresh')" :disabled="appLoading" @click="loadApps(true)">
            <span class="material-symbols-outlined text-[14px] text-on-surface-variant" :class="appLoading ? 'animate-spin' : ''">refresh</span>
          </button>
        </div>
        <div class="flex items-center gap-2 shrink-0">
          <div class="relative flex-1">
            <span class="material-symbols-outlined text-[14px] text-on-surface-variant absolute left-2 top-1/2 -translate-y-1/2">search</span>
            <input v-model="appQuery" type="text" :placeholder="t('memStress.appQueryHint')"
              class="w-full bg-white/60 border border-outline-variant/50 rounded-lg pl-7 pr-2 py-1 font-mono text-[12px] outline-none focus:ring-2 focus:ring-secondary/40 select-text"
              @input="clearSingleInfo" @keyup.enter="querySingle" />
          </div>
          <button class="glass-button px-3 py-1 rounded-lg font-caption text-caption" @click="querySingle">{{ t('memStress.query') }}</button>
        </div>

        <!-- Single query result (package not in installed list) -->
        <div v-if="singleInfo" class="shrink-0 px-3 py-1.5 rounded-lg bg-white/40 border border-outline-variant/40 flex items-center gap-2">
          <span class="font-mono text-[12px] text-on-surface truncate flex-1" :title="singleInfo.pkg">{{ singleInfo.pkg }}</span>
          <span v-if="singleInfo.killed" class="px-1.5 py-0.5 rounded bg-error/10 text-error text-[10px] shrink-0">{{ t('memStress.appKilled') }}</span>
          <span v-else-if="singleInfo.pid" class="px-1.5 py-0.5 rounded bg-success-indicator/10 text-success-indicator text-[10px] shrink-0">{{ t('memStress.appRunning') }}</span>
          <span v-else class="px-1.5 py-0.5 rounded bg-outline-variant/20 text-on-surface-variant text-[10px] shrink-0">{{ t('memStress.appStopped') }}</span>
          <span v-if="singleInfo.pid" class="font-mono text-[10px] text-on-surface-variant shrink-0">PID {{ singleInfo.pid }}</span>
          <button class="glass-hover rounded-lg p-0.5 shrink-0" @click="clearSingleInfo">
            <span class="material-symbols-outlined text-[14px] text-on-surface-variant">close</span>
          </button>
        </div>

        <div v-if="appLoading && apps.length === 0" class="flex-1 flex items-center justify-center gap-2 text-on-surface-variant/60">
          <span class="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin"></span>
          <span class="font-caption text-caption">{{ t('memStress.appsLoading') }}</span>
        </div>
        <div v-else-if="appRows.length === 0" class="flex-1 flex flex-col items-center justify-center gap-2 text-on-surface-variant/60">
          <span class="material-symbols-outlined text-[28px]">apps</span>
          <span class="font-caption text-caption">{{ apps.length === 0 ? t('memStress.appsEmpty') : t('memStress.appsNoMatch') }}</span>
        </div>
        <div v-else class="flex-1 min-h-0 overflow-y-auto custom-scrollbar">
          <div v-for="row in appRows" :key="row.pkg" class="flex items-center gap-2 px-2 py-[3px] rounded-lg list-hover">
            <span class="w-1.5 h-1.5 rounded-full shrink-0"
              :class="row.killed ? 'bg-error' : row.pid ? 'bg-success-indicator' : 'bg-outline-variant'"></span>
            <span class="font-mono text-[12px] truncate flex-1" :class="row.killed ? 'text-error' : 'text-on-surface'" :title="row.pkg">{{ row.pkg }}</span>
            <span v-if="row.killed" class="px-1.5 py-0.5 rounded bg-error/10 text-error text-[10px] shrink-0">{{ t('memStress.appKilled') }}</span>
            <span v-else-if="row.pid" class="px-1.5 py-0.5 rounded bg-success-indicator/10 text-success-indicator text-[10px] shrink-0">{{ t('memStress.appRunning') }}</span>
            <span v-else class="px-1.5 py-0.5 rounded bg-outline-variant/20 text-on-surface-variant text-[10px] shrink-0">{{ t('memStress.appStopped') }}</span>
            <span class="font-mono text-[10px] text-on-surface-variant/70 w-14 text-right shrink-0">{{ row.pid ?? '-' }}</span>
          </div>
        </div>
      </div>

      <!-- LMK events -->
      <div class="glass-panel rounded-xl p-4 flex flex-col gap-2 min-h-0 relative">
        <div class="flex items-center gap-2 shrink-0">
          <h3 class="font-label-md text-label-md text-on-surface flex items-center gap-2">
            <span class="material-symbols-outlined text-[16px] text-error">crisis_alert</span>{{ t('memStress.lmk') }}
          </h3>
          <span v-if="killCount > 0" class="px-2 py-0.5 rounded-full bg-error/10 text-error border border-error/20 font-caption text-caption">
            {{ killCount }} {{ t('memStress.kills') }}
          </span>
          <div class="flex-1"></div>
          <button class="glass-hover rounded-lg p-1" :title="t('memStress.clear')" @click="clearLmk">
            <span class="material-symbols-outlined text-[14px] text-on-surface-variant">delete_sweep</span>
          </button>
        </div>
        <div v-if="lmkLines.length === 0" class="flex-1 flex flex-col items-center justify-center gap-2 text-on-surface-variant/60">
          <span class="material-symbols-outlined text-[28px]">shield</span>
          <span class="font-caption text-caption">{{ t('memStress.lmkEmpty') }}</span>
        </div>
        <div v-else ref="lmkListRef" class="flex-1 min-h-0 overflow-y-auto custom-scrollbar font-mono text-[11px] leading-[18px]" @scroll="onLmkScroll">
          <div v-for="(line, idx) in lmkLines" :key="idx" class="whitespace-pre-wrap break-all"
            :class="isKillLine(line) ? 'text-on-surface' : 'text-on-surface-variant'">
            <template v-for="(seg, si) in lineSegments(line)" :key="si">
              <span v-if="seg.pkg" :class="isKillLine(line) ? 'text-error font-semibold' : 'text-on-surface font-medium'">{{ seg.text }}</span>
              <span v-else>{{ seg.text }}</span>
            </template>
          </div>
        </div>
        <button v-if="lmkLines.length > 0 && !lmkPinnedBottom"
          class="absolute bottom-3 right-3 px-2.5 py-1 rounded-full bg-secondary text-white font-caption text-caption shadow-md flex items-center gap-1"
          @click="scrollLmkToBottom(true)">
          <span class="material-symbols-outlined text-[13px]">arrow_downward</span>{{ t('memStress.latest') }}
        </button>
      </div>
    </div>

    <!-- Toast -->
    <Teleport to="body">
      <Transition name="fade">
        <div v-if="toastMsg" class="fixed top-4 left-1/2 -translate-x-1/2 z-[9999] glass-panel rounded-xl px-5 py-3 bg-white/80 flex items-center gap-2"
          :class="toastError ? 'text-error border border-error/20' : 'text-on-surface'">
          <span class="material-symbols-outlined text-[18px]">{{ toastError ? 'error' : 'check_circle' }}</span>
          <span class="font-body-sm text-body-sm">{{ toastMsg }}</span>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, onActivated, onDeactivated, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from '@/composables/useI18n'
import { useAdb } from '@/composables/useAdb'
import { invoke } from '@tauri-apps/api/core'
import { mkdir } from '@tauri-apps/plugin-fs'

defineOptions({ name: 'MemStressPage' })

const router = useRouter()
const { t } = useI18n()
const { shell, pushFile, pullFile } = useAdb()

const deviceSerial = ref(localStorage.getItem('last_device_serial') || '')

// ── Deployment ───────────────────────────────────────────────
type StepKey = 'abi' | 'push' | 'chmod' | 'verify'
type StepState = 'pending' | 'running' | 'done' | 'error'
const deploySteps: { key: StepKey; label: string }[] = [
  { key: 'abi', label: 'memStress.stepAbi' },
  { key: 'push', label: 'memStress.stepPush' },
  { key: 'chmod', label: 'memStress.stepChmod' },
  { key: 'verify', label: 'memStress.stepVerify' },
]
const stepState = ref<Record<StepKey, StepState>>({ abi: 'pending', push: 'pending', chmod: 'pending', verify: 'pending' })
const deploying = ref(false)
const deployed = ref(false)
const deployError = ref('')
const deployMessage = ref('')
const deviceAbi = ref('')
const stressVersion = ref('')

const deployLabel = computed(() => {
  if (deploying.value) return t('memStress.deploying')
  if (deployError.value) return t('memStress.notDeployed')
  return deployed.value ? t('memStress.deployed') : t('memStress.notDeployed')
})
const deployChipClass = computed(() => {
  if (deploying.value) return 'bg-secondary/10 text-secondary border-secondary/20'
  if (deployError.value || !deployed.value) return 'bg-error/10 text-error border-error/20'
  return 'bg-success-indicator/10 text-success-indicator border-success-indicator/20'
})
const deployDotClass = computed(() => {
  if (deploying.value) return 'bg-secondary animate-pulse'
  if (deployError.value || !deployed.value) return 'bg-error'
  return 'bg-success-indicator'
})
const deployHint = computed(() => deployed.value ? '' : t('memStress.deployHint'))

function resetSteps() {
  stepState.value = { abi: 'pending', push: 'pending', chmod: 'pending', verify: 'pending' }
}
function stepIcon(key: StepKey): string {
  const s = stepState.value[key]
  if (s === 'done') return 'check_circle'
  if (s === 'running') return 'progress_activity'
  if (s === 'error') return 'error'
  return 'circle'
}
function stepIconClass(key: StepKey): string {
  const s = stepState.value[key]
  if (s === 'done') return 'text-success-indicator'
  if (s === 'running') return 'text-secondary animate-spin'
  if (s === 'error') return 'text-error'
  return 'text-outline-variant'
}

/** ABI → 随包分发的二进制名（Rust 侧同样会校验一次） */
function resolveBinSuffix(abi: string): string {
  if (abi === 'armeabi-v7a' || abi === 'armeabi') return 'armv7a'
  if (abi === 'arm64-v8a' || abi === 'aarch64') return 'arm64'
  if (abi === 'x86_64') return 'x86_64'
  throw new Error(`${t('memStress.unsupportedAbi')}: ${abi || 'unknown'}`)
}

async function deploy(force = false) {
  if (!deviceSerial.value) { deployError.value = t('memStress.noDevice'); return }
  if (deploying.value) return
  const serial = deviceSerial.value
  deploying.value = true
  deployError.value = ''
  deployMessage.value = ''
  resetSteps()

  if (!force && deployed.value) {
    deploying.value = false
    return
  }

  try {
    stepState.value.abi = 'running'
    let abi = (await shell(serial, 'getprop ro.product.cpu.abi')).trim().split(/\r?\n/)[0]?.trim() || ''
    if (!abi) {
      const list = (await shell(serial, 'getprop ro.product.cpu.abilist')).trim()
      abi = list.split(',')[0]?.trim() || ''
    }
    deviceAbi.value = abi
    resolveBinSuffix(abi)
    stepState.value.abi = 'done'

    // 设备上已有可执行文件则跳过推送
    if (!force) {
      deployMessage.value = t('memStress.checking')
      const existing = await shell(serial, '[ -x /data/local/tmp/stress-ng ] && /data/local/tmp/stress-ng --version 2>&1 | head -n 1 || true')
      if (/stress-ng,\s*version/i.test(existing)) {
        stressVersion.value = existing.trim()
        stepState.value.push = 'done'
        stepState.value.chmod = 'done'
        stepState.value.verify = 'done'
        deployed.value = true
        deployMessage.value = ''
        return
      }
    }

    stepState.value.push = 'running'
    deployMessage.value = t('memStress.pushing')
    const localPath = await invoke<string>('stress_ng_binary_path', { abi })
    await pushFile(serial, localPath, '/data/local/tmp/stress-ng')
    stepState.value.push = 'done'

    stepState.value.chmod = 'running'
    deployMessage.value = t('memStress.chmod')
    await shell(serial, 'chmod 755 /data/local/tmp/stress-ng')
    stepState.value.chmod = 'done'

    stepState.value.verify = 'running'
    deployMessage.value = t('memStress.verifying')
    const ver = await shell(serial, '/data/local/tmp/stress-ng --version 2>&1 | head -n 1')
    if (!/stress-ng,\s*version/i.test(ver)) {
      throw new Error(ver.trim() || t('memStress.verifyFailed'))
    }
    stressVersion.value = ver.trim()
    stepState.value.verify = 'done'
    deployed.value = true
    deployMessage.value = ''
  } catch (e: any) {
    const key = (Object.keys(stepState.value) as StepKey[]).find(k => stepState.value[k] === 'running')
    if (key) stepState.value[key] = 'error'
    deployError.value = e?.message ?? String(e)
    deployed.value = false
  } finally {
    deploying.value = false
  }
}

// ── Memory sampling ──────────────────────────────────────────
const mem = ref({ totalMb: 0, availMb: 0, usedMb: 0, usage: 0 })
const memSampling = ref(false)

function parseKb(out: string, key: string): number {
  const m = out.match(new RegExp(`^${key}:\\s+(\\d+)`, 'm'))
  return m ? Number(m[1]) : 0
}

async function pollMemory() {
  if (!deviceSerial.value) return
  try {
    const out = await shell(deviceSerial.value,
      "grep -E '^(MemTotal|MemAvailable|MemFree):' /proc/meminfo")
    const totalKb = parseKb(out, 'MemTotal')
    const availKb = parseKb(out, 'MemAvailable') || parseKb(out, 'MemFree')
    if (!totalKb) throw new Error('empty meminfo')
    const totalMb = Math.round(totalKb / 1024)
    const availMb = Math.round(availKb / 1024)
    const usedMb = Math.max(0, totalMb - availMb)
    mem.value = { totalMb, availMb, usedMb, usage: totalMb ? (usedMb / totalMb) * 100 : 0 }
    memSampling.value = true
  } catch {
    memSampling.value = false
  }
}

// ── Low-memory-killer events ─────────────────────────────────
const lmkLines = ref<string[]>([])
const lmkListRef = ref<HTMLDivElement | null>(null)
const lmkPinnedBottom = ref(true)
let lmkSeen = new Set<string>()
const killCount = computed(() => lmkLines.value.filter(isKillLine).length)

/** 只匹配真正的查杀动作（Kill 动词后紧跟包名），如 "Kill 'com.x' (1234)" / "Killing com.x" */
const KILL_PKG_RE = /\bKill(?:ing|ed)?\s+['"]?([A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z0-9_]+)+)/i
/** 白名单 / 跳过等非查杀语句，不能算作被查杀 */
const KILL_EXCLUDE_RE = /whitelist|not\s+kill|not\s+killing|skip|suppress|avoid|ignore/i

/** 从 LMK 日志行中提取被查杀包名（只取 Kill 动词后的包名，自动去掉 :process 后缀） */
function extractKilledPkg(line: string): string | null {
  if (KILL_EXCLUDE_RE.test(line)) return null
  const m = line.match(KILL_PKG_RE)
  return m ? m[1] : null
}

function isKillLine(line: string): boolean {
  return extractKilledPkg(line) !== null
}

const killedPkgs = ref<Set<string>>(new Set())

/** 把日志行拆成片段，包名片段单独高亮 */
const PKG_RE = /[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z0-9_]+)+/g
function lineSegments(line: string): { text: string; pkg: boolean }[] {
  const out: { text: string; pkg: boolean }[] = []
  let last = 0
  PKG_RE.lastIndex = 0
  let m: RegExpExecArray | null
  while ((m = PKG_RE.exec(line)) !== null) {
    if (m.index > last) out.push({ text: line.slice(last, m.index), pkg: false })
    out.push({ text: m[0], pkg: true })
    last = m.index + m[0].length
  }
  if (last < line.length) out.push({ text: line.slice(last), pkg: false })
  return out
}

function onLmkScroll() {
  const el = lmkListRef.value
  if (!el) return
  lmkPinnedBottom.value = el.scrollHeight - el.scrollTop - el.clientHeight < 40
}

async function scrollLmkToBottom(force = false) {
  await nextTick()
  const el = lmkListRef.value
  if (!el) return
  if (force || lmkPinnedBottom.value) {
    el.scrollTop = el.scrollHeight
    lmkPinnedBottom.value = true
  }
}

async function pollLmk() {
  if (!deviceSerial.value) return
  try {
    const out = await shell(deviceSerial.value,
      'logcat -d -v time -t 300 -s lowmemorykiller lmkd 2>/dev/null | tail -n 200')
    const fresh: string[] = []
    for (const raw of out.split(/\r?\n/)) {
      const line = raw.trimEnd()
      if (!line || line.startsWith('---------')) continue
      if (lmkSeen.has(line)) continue
      lmkSeen.add(line)
      fresh.push(line)
    }
    if (fresh.length) {
      // 旧 → 新，新消息追加在底部
      lmkLines.value = [...lmkLines.value, ...fresh].slice(-300)
      const newKilled: string[] = []
      for (const line of fresh) {
        const pkg = extractKilledPkg(line)
        if (pkg) newKilled.push(pkg)
      }
      if (newKilled.length) {
        const next = new Set(killedPkgs.value)
        for (const pkg of newKilled) next.add(pkg)
        killedPkgs.value = next
        for (const pkg of newKilled) {
          if (!apps.value.some(a => a.pkg === pkg)) apps.value.push({ pkg })
        }
      }
      await scrollLmkToBottom()
    }
    if (lmkSeen.size > 3000) lmkSeen = new Set(lmkLines.value)
  } catch {
    /* logcat 不可用时静默 */
  }
}

async function clearLmk() {
  lmkLines.value = []
  // 查杀状态由日志推导，清空日志时一并重置，避免误判残留
  killedPkgs.value = new Set()
  lmkPinnedBottom.value = true
  // 把设备当前缓冲区里的历史行标记为已读，避免下一次轮询又把旧事件灌回来
  try {
    const out = await shell(deviceSerial.value,
      'logcat -d -v time -t 300 -s lowmemorykiller lmkd 2>/dev/null | tail -n 200')
    lmkSeen = new Set()
    for (const raw of out.split(/\r?\n/)) {
      const line = raw.trimEnd()
      if (line && !line.startsWith('---------')) lmkSeen.add(line)
    }
  } catch {
    lmkSeen = new Set()
  }
}

// ── App process query ────────────────────────────────────────
interface AppEntry { pkg: string }
interface ProcEntry { pid: number; name: string }
interface SingleInfo { pkg: string; pid: number | null; killed: boolean }

const apps = ref<AppEntry[]>([])
const procs = ref<ProcEntry[]>([])
const appLoading = ref(false)
const appQuery = ref('')
const singleInfo = ref<SingleInfo | null>(null)

function parsePkgList(out: string): string[] {
  const list: string[] = []
  const re = /package:(\S+)/g
  let m: RegExpExecArray | null
  while ((m = re.exec(out)) !== null) list.push(m[1])
  return list
}

function parsePs(out: string): ProcEntry[] {
  const list: ProcEntry[] = []
  for (const raw of out.split(/\r?\n/)) {
    const line = raw.trim()
    if (!line) continue
    // ps -A -o PID,NAME
    const brief = line.match(/^(\d+)\s+(\S+)$/)
    if (brief) { list.push({ pid: Number(brief[1]), name: brief[2] }); continue }
    // 兜底：USER PID PPID VSZ RSS WCHAN ADDR S NAME
    const f = line.split(/\s+/)
    if (f.length >= 9 && /^\d+$/.test(f[1])) list.push({ pid: Number(f[1]), name: f[f.length - 1] })
  }
  return list
}

function findPid(pkg: string): number | null {
  for (const p of procs.value) {
    if (p.name === pkg || p.name.startsWith(`${pkg}:`)) return p.pid
  }
  return null
}

async function loadApps(force = false) {
  if (!deviceSerial.value || appLoading.value) return
  if (!force && apps.value.length > 0) return
  const previous = apps.value
  appLoading.value = true
  if (force) {
    // 手动刷新：先清空列表和单包查询结果，避免看起来"点了没反应"
    apps.value = []
    appQuery.value = ''
    singleInfo.value = null
  }
  try {
    let out = await shell(deviceSerial.value, 'pm list packages -3')
    let pkgs = parsePkgList(out)
    if (pkgs.length === 0) {
      out = await shell(deviceSerial.value, 'pm list packages')
      pkgs = parsePkgList(out)
    }
    // 预装的 zeasn / whaletv 应用通常不在第三方包列表中，额外纳入
    try {
      const brandOut = await shell(deviceSerial.value, "pm list packages | grep -Ei 'zeasn|whaletv' || true")
      pkgs = [...pkgs, ...parsePkgList(brandOut)]
    } catch { /* 忽略品牌包查询失败 */ }
    // 保留已从 LMK 日志中发现的包名
    const merged = new Set<string>([
      ...pkgs,
      ...killedPkgs.value,
      ...(force ? [] : previous.map(a => a.pkg)),
    ])
    apps.value = [...merged].sort((a, b) => a.localeCompare(b)).map(pkg => ({ pkg }))
    await pollProcesses()
    if (force) showToast(t('memStress.appsRefreshed'))
  } catch {
    /* 失败时恢复旧列表 */
    apps.value = previous
  } finally {
    appLoading.value = false
  }
}

async function pollProcesses() {
  if (!deviceSerial.value) return
  try {
    let out = await shell(deviceSerial.value, 'ps -A -o PID,NAME 2>/dev/null')
    let list = parsePs(out)
    if (!list.length) {
      out = await shell(deviceSerial.value, 'ps -A 2>/dev/null')
      list = parsePs(out)
    }
    procs.value = list
  } catch {
    /* 瞬时失败保留上一次结果 */
  }
}

const appRows = computed(() => {
  const q = appQuery.value.trim().toLowerCase()
  const rows = apps.value
    .map(a => ({ pkg: a.pkg, pid: findPid(a.pkg), killed: killedPkgs.value.has(a.pkg) }))
    .filter(r => !q || r.pkg.toLowerCase().includes(q))
  const rank = (r: { pid: number | null; killed: boolean }) => (r.killed ? 0 : r.pid ? 1 : 2)
  return rows.sort((a, b) => rank(a) - rank(b) || a.pkg.localeCompare(b.pkg))
})

const appStats = computed(() => {
  let running = 0, killed = 0
  for (const a of apps.value) {
    if (killedPkgs.value.has(a.pkg)) killed++
    else if (findPid(a.pkg)) running++
  }
  return { running, killed }
})

/** 查询单个包名：已安装的直接在列表中过滤展示，未安装的单独查询进程 */
function clearSingleInfo() { singleInfo.value = null }

async function querySingle() {
  const q = appQuery.value.trim()
  singleInfo.value = null
  if (!q || !deviceSerial.value) return
  if (!/^[A-Za-z][A-Za-z0-9._]*$/.test(q)) {
    showToast(t('memStress.invalidPkg'), true)
    return
  }
  const installed = apps.value.find(a => a.pkg.toLowerCase() === q.toLowerCase())
  if (installed) return

  try {
    const out = await shell(deviceSerial.value, `ps -A -o PID,NAME 2>/dev/null | grep -F '${q}' || true`)
    const m = out.match(/^\s*(\d+)\s+(\S+)/m)
    singleInfo.value = { pkg: q, pid: m ? Number(m[1]) : null, killed: killedPkgs.value.has(q) }
  } catch {
    singleInfo.value = { pkg: q, pid: null, killed: killedPkgs.value.has(q) }
  }
}

// ── Sampling loops ───────────────────────────────────────────
let memLoopActive = false
let lmkLoopActive = false
let memTimer: ReturnType<typeof setTimeout> | null = null
let lmkTimer: ReturnType<typeof setTimeout> | null = null

async function memLoop() {
  if (!memLoopActive) return
  await pollMemory()
  if (!memLoopActive) return
  memTimer = setTimeout(memLoop, 2000)
}
async function lmkLoop() {
  if (!lmkLoopActive) return
  await pollLmk()
  await pollProcesses()
  if (!lmkLoopActive) return
  lmkTimer = setTimeout(lmkLoop, 3000)
}
function startSampling() {
  if (!deviceSerial.value) return
  if (!memLoopActive) { memLoopActive = true; memLoop() }
  if (!lmkLoopActive) { lmkLoopActive = true; lmkLoop() }
  if (apps.value.length === 0) loadApps()
}
function stopSampling() {
  memLoopActive = false
  lmkLoopActive = false
  if (memTimer) { clearTimeout(memTimer); memTimer = null }
  if (lmkTimer) { clearTimeout(lmkTimer); lmkTimer = null }
}

// ── Stress control ───────────────────────────────────────────
const totalMemMb = ref(1024)
const workers = ref(2)
const durationMin = ref(3)
const isRunning = ref(false)
const starting = ref(false)
const stopping = ref(false)
const startAt = ref(0)
const elapsed = ref(0)
let tickTimer: ReturnType<typeof setInterval> | null = null
let aliveTimer: ReturnType<typeof setInterval> | null = null
let missedPid = 0

/** 界面填写的是总内存；stress-ng 0.19 的 --vm-bytes 是全部 worker 的合计分配量 */
const overcommit = computed(() => mem.value.totalMb > 0 && totalMemMb.value > mem.value.totalMb)
const totalSec = computed(() => Math.max(1, Math.round((Number(durationMin.value) || 1) * 60)))
const progressPct = computed(() => Math.min(100, (elapsed.value / totalSec.value) * 100))
const canStart = computed(() => !!deviceSerial.value && deployed.value && !starting.value && !isRunning.value)

function mmss(sec: number): string {
  const s = Math.max(0, Math.round(sec))
  return `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`
}
const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms))

function startTimers() {
  stopTimers()
  tickTimer = setInterval(() => {
    if (!isRunning.value) return
    elapsed.value = Math.floor((Date.now() - startAt.value) / 1000)
    if (elapsed.value >= totalSec.value) finishStress(false)
  }, 1000)
  aliveTimer = setInterval(async () => {
    if (!isRunning.value) return
    try {
      const pid = (await shell(deviceSerial.value, 'pidof stress-ng 2>/dev/null || true')).trim()
      if (pid) { missedPid = 0; return }
      missedPid++
      if (missedPid >= 2) finishStress(true)
    } catch { /* 瞬时 adb 失败忽略 */ }
  }, 2000)
}
function stopTimers() {
  if (tickTimer) { clearInterval(tickTimer); tickTimer = null }
  if (aliveTimer) { clearInterval(aliveTimer); aliveTimer = null }
}

function finishStress(earlyExit: boolean) {
  if (!isRunning.value) return
  isRunning.value = false
  missedPid = 0
  stopTimers()
  showToast(earlyExit ? t('memStress.exited') : t('memStress.finished'), earlyExit)
}

async function startStress() {
  if (!deviceSerial.value) { showToast(t('memStress.noDevice'), true); return }
  if (!deployed.value) { showToast(t('memStress.deployRequired'), true); return }
  if (isRunning.value || starting.value) return

  const total = Math.min(16384, Math.max(32, Math.round(Number(totalMemMb.value) || 0)))
  const wk = Math.min(8, Math.max(1, Math.round(Number(workers.value) || 0)))
  const dur = Math.min(60, Math.max(1, Math.round(Number(durationMin.value) || 0)))
  totalMemMb.value = total; workers.value = wk; durationMin.value = dur

  starting.value = true
  try {
    const cmd =
      'cd /data/local/tmp; rm -f memtest.log memtest.yaml memtest.out stress-ng.pid; ' +
      `setsid ./stress-ng --vm ${wk} --vm-bytes ${total}M --vm-keep --timeout ${dur}m --metrics --stressor-time --oomable ` +
      '--log-file /data/local/tmp/memtest.log -Y /data/local/tmp/memtest.yaml ' +
      '>/data/local/tmp/memtest.out 2>&1 </dev/null & ' +
      'echo $! > /data/local/tmp/stress-ng.pid'
    await shell(deviceSerial.value, cmd)

    let pid = ''
    for (let i = 0; i < 4; i++) {
      await sleep(600)
      pid = (await shell(deviceSerial.value, 'pidof stress-ng 2>/dev/null || true')).trim()
      if (pid) break
    }
    if (!pid) {
      const out = await shell(deviceSerial.value, 'cat /data/local/tmp/memtest.out 2>/dev/null | tail -n 6')
      throw new Error(out.trim() || 'stress-ng failed to start')
    }
    isRunning.value = true
    startAt.value = Date.now()
    elapsed.value = 0
    missedPid = 0
    startTimers()
    startSampling()
    showToast(t('memStress.started'))
  } catch (e: any) {
    showToast(`${t('memStress.startFailed')}: ${e?.message ?? String(e)}`, true)
  } finally {
    starting.value = false
  }
}

async function stopStress() {
  if (!deviceSerial.value || !isRunning.value || stopping.value) return
  stopping.value = true
  try {
    const serial = deviceSerial.value
    await shell(serial,
      'cd /data/local/tmp; if [ -f stress-ng.pid ]; then kill -TERM $(cat stress-ng.pid) 2>/dev/null; fi; rm -f stress-ng.pid; echo ok')
    await sleep(1200)
    const pid = (await shell(serial, 'pidof stress-ng 2>/dev/null || true')).trim()
    if (pid) {
      await shell(serial, 'pkill -KILL -f "stress-ng --vm" 2>/dev/null || kill -KILL ' + pid + ' 2>/dev/null || true')
      await sleep(400)
    }
    isRunning.value = false
    missedPid = 0
    stopTimers()
    showToast(t('memStress.stopped'))
  } catch (e: any) {
    showToast(`${t('memStress.stopFailed')}: ${e?.message ?? String(e)}`, true)
  } finally {
    stopping.value = false
  }
}

// ── Export stress-ng log ─────────────────────────────────────
const exportingLog = ref(false)
async function exportLog() {
  if (!deviceSerial.value || exportingLog.value) return
  exportingLog.value = true
  try {
    const { documentDir, join } = await import('@tauri-apps/api/path')
    const docDir = await documentDir()
    const dir = (await join(docDir, 'TestSpace')).replace(/\\/g, '/')
    try { await mkdir(dir, { recursive: true }) } catch {}
    const d = new Date()
    const p = (n: number) => String(n).padStart(2, '0')
    const stamp = `${d.getFullYear()}${p(d.getMonth() + 1)}${p(d.getDate())}_${p(d.getHours())}${p(d.getMinutes())}${p(d.getSeconds())}`
    const local = `${dir}/memtest_${stamp}.log`
    await pullFile(deviceSerial.value, '/data/local/tmp/memtest.log', local)
    showToast(t('memStress.logSaved'))
    try { await invoke('open_path', { path: dir }) } catch {}
  } catch (e: any) {
    showToast(`${t('memStress.exportFailed')}: ${e?.message ?? String(e)}`, true)
  } finally {
    exportingLog.value = false
  }
}

// ── Toast ────────────────────────────────────────────────────
const toastMsg = ref('')
const toastError = ref(false)
let toastTimer: ReturnType<typeof setTimeout> | null = null
function showToast(msg: string, error = false) {
  toastMsg.value = msg
  toastError.value = error
  if (toastTimer) clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toastMsg.value = '' }, 3000)
}

// ── Navigation / lifecycle ───────────────────────────────────
function goBack() { router.push('/device-space') }

onMounted(() => {
  if (deviceSerial.value) {
    startSampling()
    deploy(false)
  }
})

onActivated(() => {
  // 设备页可能切换了设备，重新读取
  const latest = localStorage.getItem('last_device_serial') || ''
  if (latest !== deviceSerial.value) {
    deviceSerial.value = latest
    deployed.value = false
    deployError.value = ''
    stressVersion.value = ''
    deviceAbi.value = ''
    apps.value = []
    procs.value = []
    killedPkgs.value = new Set()
    appQuery.value = ''
    singleInfo.value = null
    clearLmk()
  }
  if (deviceSerial.value) {
    startSampling()
    if (!deployed.value && !deploying.value && !deployError.value) deploy(false)
  }
})

onDeactivated(() => {
  // 空闲时暂停轮询；压测中继续采集，避免漏掉 LMK 查杀记录
  if (!isRunning.value) stopSampling()
})

onUnmounted(() => {
  stopSampling()
  stopTimers()
  if (toastTimer) clearTimeout(toastTimer)
})
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.18s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
