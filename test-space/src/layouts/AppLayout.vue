<template>
  <div
    class="w-screen h-screen overflow-hidden flex flex-col font-body-md text-body-md text-on-surface antialiased selection:bg-secondary-fixed selection:text-on-secondary-fixed app-content select-none"
    :class="[isMaximized ? 'rounded-none maximized-padding' : 'rounded-2xl']"
    :style="bgStyle"
  >
    <TitleBar />
    <main class="px-margin-page pt-3 box-border flex-1 overflow-y-auto overflow-x-hidden min-h-0 flex flex-col">
      <router-view v-slot="{ Component }">
        <keep-alive :include="['NotesSpacePage', 'ScriptSpacePage', 'DeviceSpacePage', 'ApiSpacePage', 'SettingsPage', 'PerfMonitorPage']">
          <component :is="Component" :ref="onPageRef" />
        </keep-alive>
      </router-view>
    </main>

    <!-- Global AI Assistant Panel (notes + script pages only) -->
    <NoteAiPanel
      :ai-config="aiConfig"
      :notes="notesForAi"
      :mode="aiMode"
      :visible="aiPanelVisible"
      :script-type="scriptType"
      :current-script-content="currentScriptContent"
      :script-names="scriptNames"
      @go-settings="router.push('/settings')"
      @open-note="onAiOpenNote"
      @apply-script="onAiApplyScript"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getCurrentWindow } from '@tauri-apps/api/window'
import TitleBar from './TitleBar.vue'
import NoteAiPanel from '@/components/notes/NoteAiPanel.vue'
import type { AiPanelMode } from '@/components/notes/NoteAiPanel.vue'
import { loadAiConfig, type AiConfig } from '@/services/aiSettings'
import type { NoteItem } from '@/types'
import type { ScriptAiResult } from '@/services/scriptAi'

const route = useRoute()
const router = useRouter()

// 最大化时去除圆角，避免视觉冲突和 resize 时的圆角闪烁
const isMaximized = ref(false)
let unlistenResize: (() => void) | null = null
async function refreshMaximized() {
  try { isMaximized.value = await getCurrentWindow().isMaximized() } catch {}
}
onMounted(async () => {
  await refreshMaximized()
  try { unlistenResize = await getCurrentWindow().onResized(refreshMaximized) } catch {}
})
onUnmounted(() => { if (unlistenResize) unlistenResize() })

// 每个 space 用一枚极淡的色相点缀纸底，主体保持 paper (#F1EDE4)
const bgStyle = computed(() => {
  const path = route.path
  const paper = '#F1EDE4'
  if (path.startsWith('/api-space')) {
    return {
      background:
        `radial-gradient(circle at 85% 30%, rgba(20,160,133,0.05) 0%, transparent 42%), ` +
        `radial-gradient(circle at 15% 70%, rgba(30,58,95,0.045) 0%, transparent 42%), ${paper}`,
    }
  }
  if (path.startsWith('/device-space/perf-monitor')) {
    return {
      background:
        `radial-gradient(circle at 20% 40%, rgba(20,160,133,0.06), transparent 32%), ` +
        `radial-gradient(circle at 80% 60%, rgba(30,58,95,0.05), transparent 32%), ${paper}`,
    }
  }
  if (path.startsWith('/device-space')) {
    return {
      background:
        `radial-gradient(circle at 15% 50%, rgba(30,58,95,0.055), transparent 28%), ` +
        `radial-gradient(circle at 85% 30%, rgba(194,78,58,0.045), transparent 28%), ${paper}`,
    }
  }
  if (path.startsWith('/notes-space')) {
    return {
      background:
        `radial-gradient(circle at 50% 0%, #F5F1E9 0%, ${paper} 55%, #EEE9DE 100%)`,
    }
  }
  if (path.startsWith('/script-space')) {
    return {
      background:
        `radial-gradient(circle at 25% 25%, rgba(30,58,95,0.05) 0%, transparent 40%), ` +
        `radial-gradient(circle at 75% 75%, rgba(194,78,58,0.04) 0%, transparent 40%), ${paper}`,
    }
  }
  return { background: paper }
})

// ── AI panel global state ─────────────────────────────────────
const aiConfig = ref<AiConfig>({
  provider: 'azure',
  apiKey: '',
  endpoint: '',
  model: '',
  maxContextTokens: 8000,
  authMode: 'api-key',
})

// Lazy-load AI config once
let aiConfigLoaded = false
async function ensureAiConfig() {
  if (aiConfigLoaded) return
  aiConfigLoaded = true
  try { aiConfig.value = await loadAiConfig() } catch {}
}

// ── Page component ref ───────────────────────────────────────
// The router-view child component exposes its state via defineExpose
const pageRef = ref<any>(null)
function onPageRef(el: any) {
  pageRef.value = el
}

// ── Mode detection based on current route ────────────────────
const aiMode = computed<AiPanelMode>(() => {
  if (route.path.startsWith('/script-space')) return 'script'
  return 'notes'
})

/** Only show AI panel trigger on notes and script pages */
const aiPanelVisible = computed(() =>
  route.path.startsWith('/notes-space') || route.path.startsWith('/script-space')
)

// 只在离开 /settings 后返回笔记/脚本页时刷新 AI 配置。
// 原来每次切页都同步 await loadAiConfig() 会命中一次 SQLite 读，
// 是页面之间切换卡顿的主要来源。
let lastPath = ''
watch(
  () => route.path,
  async (path) => {
    await ensureAiConfig()
    const cameFromSettings = lastPath.startsWith('/settings')
    lastPath = path
    if (cameFromSettings && aiConfigLoaded && (path.startsWith('/notes-space') || path.startsWith('/script-space'))) {
      try { aiConfig.value = await loadAiConfig() } catch {}
    }
  },
  { immediate: true }
)

// ── Notes data for AI ─────────────────────────────────────────
// NotesSpacePage keeps its own notes ref; we read it via the exposed ref.
// If the page is not mounted yet we serve an empty array.
const notesForAi = computed<NoteItem[]>(() => {
  if (aiMode.value !== 'notes') return []
  return pageRef.value?.notes ?? []
})

// ── Script data for AI ────────────────────────────────────────
const scriptType = computed<'bat' | 'py'>(() => {
  if (aiMode.value !== 'script') return 'bat'
  return pageRef.value?.globalType ?? 'bat'
})

const currentScriptContent = computed<string>(() => {
  if (aiMode.value !== 'script') return ''
  return pageRef.value?.editingContent ?? ''
})

const scriptNames = computed<string[]>(() => {
  if (aiMode.value !== 'script') return []
  // scriptNames exposed from ScriptSpacePage: names of other scripts of same type
  return pageRef.value?.siblingScriptNames ?? []
})

// ── Event handlers ────────────────────────────────────────────
function onAiOpenNote(noteId: string, headingAnchor?: string) {
  // Delegate to the notes page component if it's mounted
  pageRef.value?.openNoteById?.(noteId, headingAnchor)
}

function onAiApplyScript(payload: ScriptAiResult) {
  // Delegate to the script page component
  pageRef.value?.applyAiScript?.(payload)
}
</script>

<style scoped>
/**
 * Tauri Windows 无边框最大化补偿
 * ─────────────────────────────────────────────────────
 * decorations:false + resizable:true 时，Windows 会把
 * 客户区扩展到屏幕外约 7px（隐藏 resize 边框区）。
 * 最大化后视觉上"超框"、右侧窗口按钮被推到屏幕外。
 * 加同等 padding 补偿。
 */
.maximized-padding {
  padding: 7px;
}
</style>
