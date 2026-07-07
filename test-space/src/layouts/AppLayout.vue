<template>
  <div
    class="w-screen h-screen rounded-2xl overflow-hidden flex flex-col font-body-md text-body-md text-on-surface antialiased selection:bg-secondary-fixed selection:text-on-secondary-fixed app-content select-none"
    :style="bgStyle"
  >
    <TitleBar />
    <main class="px-margin-page pt-3 box-border flex-1 overflow-y-auto overflow-x-hidden min-h-0 flex flex-col">
      <router-view v-slot="{ Component }">
        <keep-alive :include="['NotesSpacePage', 'ScriptSpacePage', 'DeviceSpacePage', 'ApiSpacePage', 'SettingsPage', 'CaseSpacePage']">
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
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import TitleBar from './TitleBar.vue'
import NoteAiPanel from '@/components/notes/NoteAiPanel.vue'
import type { AiPanelMode } from '@/components/notes/NoteAiPanel.vue'
import { loadAiConfig, type AiConfig } from '@/services/aiSettings'
import type { NoteItem } from '@/types'
import type { ScriptAiResult } from '@/services/scriptAi'

const route = useRoute()
const router = useRouter()

// ── Background gradient ───────────────────────────────────────
const bgStyle = computed(() => {
  const path = route.path
  if (path.startsWith('/case-space')) {
    return {
      background:
        'radial-gradient(circle at top left, rgba(226,223,255,0.4) 0%, transparent 40%), radial-gradient(circle at bottom right, rgba(0,80,203,0.05) 0%, transparent 40%), #F9F9FB',
    }
  }
  if (path.startsWith('/api-space')) {
    return {
      background:
        'radial-gradient(circle at 85% 30%, rgba(0,180,200,0.06) 0%, transparent 40%), radial-gradient(circle at 15% 70%, rgba(0,100,200,0.04) 0%, transparent 40%), #F9F9FB',
    }
  }
  if (path.startsWith('/device-space')) {
    return {
      background:
        'radial-gradient(circle at 15% 50%, rgba(76,74,202,0.05), transparent 25%), radial-gradient(circle at 85% 30%, rgba(0,80,203,0.05), transparent 25%), #F9F9FB',
    }
  }
  if (path.startsWith('/notes-space')) {
    return { background: 'radial-gradient(circle at 50% 0%, #F9F9FB 0%, #F3F3F5 100%)' }
  }
  return { background: '#F9F9FB' }
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

// Watch route changes to reload AI config when returning from settings
watch(
  () => route.path,
  async (path) => {
    await ensureAiConfig()
    // Re-read AI config only when navigating TO notes/script from settings
    // (ensureAiConfig has a one-time flag, so only Settings changes need an explicit reload)
    if (path.startsWith('/notes-space') || path.startsWith('/script-space')) {
      // Only reload if config was already loaded once (i.e. user may have changed it in Settings)
      if (aiConfigLoaded) {
        try { aiConfig.value = await loadAiConfig() } catch {}
      }
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
