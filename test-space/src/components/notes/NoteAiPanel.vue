<template>
  <Teleport to="body">
    <!-- Floating trigger — only on notes-space and script-space -->
    <button
      v-if="!open && showTrigger"
      ref="triggerRef"
      class="fixed right-0 bottom-24 z-50 bg-white/40 backdrop-blur-md border border-white/60 rounded-l-md px-1.5 py-4 shadow-lg hover:bg-white/60 hover:pr-2 transition-all opacity-[85%] select-none"
      :title="triggerTitle"
      @click="open = true"
    >
      <span class="material-symbols-outlined text-[20px] text-on-surface-variant">smart_toy</span>
    </button>

    <!-- Slide panel -->
    <div v-if="open && showTrigger" class="fixed right-4 bottom-4 z-[60] pointer-events-none">
      <div
        ref="panelRef"
        class="relative w-[500px] max-w-[calc(100vw-2rem)] h-[calc(100vh-8rem)] flex flex-col glass-panel rounded-[2rem] bg-white/60 border border-white/50 shadow-2xl overflow-hidden animate-ai-in pointer-events-auto"
      >
        <!-- Header -->
        <div class="p-3 border-b border-glass-border-light/30 flex items-center justify-between shrink-0 bg-white/40">
          <span class="font-label-md text-[13px] text-on-surface font-semibold flex items-center gap-2 min-w-0">
            <span class="material-symbols-outlined text-[18px] shrink-0">smart_toy</span>
            <span class="truncate">{{ panelTitle }}</span>
          </span>
          <div class="flex items-center gap-1">
            <!-- Notes mode: extract memory -->
            <button
              v-if="mode === 'notes' && messages.length >= 2"
              class="glass-button p-1 rounded select-none shrink-0 text-on-surface-variant hover:text-amber-600 transition-colors"
              :title="t('notes.aiExtractMemory')"
              :disabled="memorizing"
              @click="extractFromLastQA"
            >
              <span class="material-symbols-outlined text-[16px]" :class="memorizing ? 'animate-spin' : ''">memory</span>
            </button>
            <!-- Clear history -->
            <button
              v-if="messages.length > 0"
              class="glass-button p-1 rounded select-none shrink-0 text-on-surface-variant hover:text-red-500 transition-colors"
              :title="t('notes.aiClearHistory')"
              @click="clearHistory"
            >
              <span class="material-symbols-outlined text-[16px]">delete_sweep</span>
            </button>
            <button class="glass-button p-1 rounded select-none shrink-0" @click="open = false">
              <span class="material-symbols-outlined text-[16px]">close</span>
            </button>
          </div>
        </div>

        <!-- Not configured -->
        <div v-if="!configured" class="flex-1 flex flex-col items-center justify-center p-6 text-center">
          <span class="material-symbols-outlined text-[40px] text-on-surface-variant/40 mb-3">settings</span>
          <p class="text-[13px] text-on-surface-variant mb-4">{{ t('notes.aiNotConfigured') }}</p>
          <button class="glass-button px-4 py-2 rounded-full text-[13px] glass-active select-none" @click="$emit('goSettings')">
            {{ t('notes.aiGoSettings') }}
          </button>
        </div>

        <template v-else>
          <!-- Notes mode: context hint -->
          <div v-if="mode === 'notes'" class="px-3 py-2 border-b border-glass-border-light/20 flex items-center justify-between gap-2 shrink-0 text-[11px] text-on-surface-variant bg-white/30">
            <span>{{ t('notes.aiAllNotesHint', { total: String(notes.length), included: String(contextNoteCount) }) }}</span>
            <div class="flex items-center gap-2 shrink-0">
              <span v-if="memorizing" class="flex items-center gap-1 text-amber-600">
                <span class="material-symbols-outlined text-[13px] animate-spin">memory</span>
                {{ t('notes.aiMemorizing') }}
              </span>
              <span>~{{ estimatedTokens }} tok</span>
            </div>
          </div>
          <!-- Script mode: type indicator -->
          <div v-else class="px-3 py-2 border-b border-glass-border-light/20 flex items-center gap-2 shrink-0 text-[11px] text-on-surface-variant bg-white/30">
            <span class="material-symbols-outlined text-[13px]">code</span>
            <span>{{ t('scripts.aiModeHint', { type: scriptTypeLabelDisplay }) }}</span>
          </div>

          <!-- Messages -->
          <div ref="messagesRef" class="flex-1 overflow-y-auto custom-scrollbar p-3 space-y-3 min-h-0">
            <div v-if="messages.length === 0" class="text-[12px] text-on-surface-variant/60 text-center py-8">
              {{ mode === 'notes' ? t('notes.aiPlaceholder') : t('scripts.aiPlaceholder') }}
            </div>
            <div
              v-for="(msg, i) in messages"
              :key="i"
              class="text-[12px] leading-relaxed"
              :class="msg.role === 'user' ? 'flex justify-end' : ''"
            >
              <div
                class="max-w-[90%] px-3 py-2 rounded-md whitespace-pre-wrap break-words select-text"
                :class="msg.role === 'user'
                  ? 'bg-purple-100/80 text-on-surface'
                  : 'bg-white/90 text-on-surface border border-glass-border-light/40'"
              >
                <!-- Notes mode assistant message: parse note links -->
                <template v-if="msg.role === 'user'">{{ msg.content }}</template>
                <template v-else-if="mode === 'notes'">
                  <template v-for="(seg, si) in parseAnswerNoteLinks(msg.content)" :key="si">
                    <span v-if="seg.type === 'text'">{{ seg.content }}</span>
                    <button
                      v-else
                      type="button"
                      class="inline text-secondary underline underline-offset-2 hover:opacity-80 cursor-pointer font-medium select-none align-baseline"
                      @click="onOpenNote(seg.noteId!, seg.headingAnchor)"
                    >{{ seg.content }}</button>
                  </template>
                </template>
                <!-- Script mode assistant message: show description + saved indicator -->
                <template v-else>
                  <div class="whitespace-pre-wrap">{{ msg.content }}</div>
                  <div v-if="msg.scriptPayload" class="mt-2 pt-2 border-t border-glass-border-light/30 flex items-center gap-1.5 text-[11px] text-success-indicator">
                    <span class="material-symbols-outlined text-[14px]">check_circle</span>
                    {{ t('scripts.aiAutoSaved', { name: msg.scriptPayload.name }) }}
                  </div>
                </template>
              </div>
            </div>
            <div v-if="loading" class="flex items-center gap-2 text-[12px] text-on-surface-variant px-2">
              <span class="material-symbols-outlined text-[16px] animate-spin">sync</span>
              {{ t('notes.aiThinking') }}
            </div>
            <div v-else-if="memorizing" class="flex items-center gap-2 text-[11px] text-on-surface-variant/60 px-2">
              <span class="material-symbols-outlined text-[14px] animate-spin">memory</span>
              {{ t('notes.aiMemorizing') }}
            </div>
          </div>

          <div v-if="error" class="px-3 py-1.5 text-[11px] text-red-500 shrink-0 break-words bg-white/40">{{ error }}</div>

          <div class="p-3 border-t border-glass-border-light/30 flex gap-2 shrink-0 bg-white/40">
            <input
              v-model="input"
              type="text"
              :placeholder="mode === 'notes' ? t('notes.aiInputPlaceholder') : t('scripts.aiInputPlaceholder')"
              class="glass-input flex-1 min-w-0 px-3 py-2 rounded-lg text-[13px] outline-none select-text"
              :disabled="loading"
              @keydown.enter="send"
            />
            <button
              class="glass-button px-3 py-2 rounded-lg glass-active select-none shrink-0"
              :disabled="loading || !input.trim()"
              @click="send"
            >
              <span class="material-symbols-outlined text-[18px]">send</span>
            </button>
          </div>
        </template>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'
import type { NoteItem } from '@/types'
import type { AiConfig } from '@/services/aiSettings'
import { isAiConfigured } from '@/services/aiSettings'
import {
  chatWithNotes,
  selectContextChunks,
  buildChunkContext,
  estimateTokens,
  extractMemories,
} from '@/services/noteAi'
import { callScriptAi, type ScriptAiResult } from '@/services/scriptAi'
import { parseAnswerNoteLinks } from '@/utils/parseNoteLinks'
import { useI18n } from '@/composables/useI18n'
import { getSetting, setSetting, loadAiMemories, saveAiMemory, type AiMemory } from '@/services/database'

export type AiPanelMode = 'notes' | 'script'

const props = defineProps<{
  aiConfig: AiConfig
  notes: NoteItem[]
  mode: AiPanelMode
  /** Controls visibility of the trigger button and panel. AppLayout passes true only for notes/script pages. */
  visible: boolean
  // script mode props
  scriptType?: 'bat' | 'py'
  currentScriptContent?: string
  scriptNames?: string[] // names of other scripts in same type (for import awareness)
}>()

const emit = defineEmits<{
  goSettings: []
  openNote: [noteId: string, headingAnchor?: string]
  applyScript: [payload: ScriptAiResult]
}>()

const { t } = useI18n()

const open = ref(false)
const input = ref('')
const loading = ref(false)
const memorizing = ref(false)
const error = ref('')
const messagesRef = ref<HTMLDivElement>()
const panelRef = ref<HTMLDivElement>()
const triggerRef = ref<HTMLButtonElement>()

interface ChatMsg {
  role: 'user' | 'assistant'
  content: string
  scriptPayload?: ScriptAiResult
}

const messages = ref<ChatMsg[]>([])
const memories = ref<AiMemory[]>([])
const historyLoaded = ref(false)

// Only show trigger on notes-space and script-space — controlled by AppLayout via :visible
const showTrigger = computed(() => props.visible)

const configured = computed(() => isAiConfigured(props.aiConfig))

const panelTitle = computed(() =>
  props.mode === 'script' ? t('scripts.aiAssistant') : t('notes.aiAssistant')
)
const triggerTitle = computed(() =>
  props.mode === 'script' ? t('scripts.aiAssistant') : t('notes.aiAssistant')
)
const scriptTypeLabelDisplay = computed(() =>
  props.scriptType === 'py' ? 'Python' : 'BAT'
)

// ── Notes mode: context estimation ──────────────────────────
const contextNoteCount = ref(0)
const estimatedTokens = ref(0)

let contextDebounce: ReturnType<typeof setTimeout> | null = null
function scheduleContextUpdate() {
  if (props.mode !== 'notes') return
  if (contextDebounce) clearTimeout(contextDebounce)
  contextDebounce = setTimeout(() => {
    const q = input.value.trim() || (messages.value.filter(m => m.role === 'user').pop()?.content ?? '')
    if (!q) { contextNoteCount.value = 0; estimatedTokens.value = 0; return }
    const { chunks, noteIds } = selectContextChunks(props.notes, q, props.aiConfig.maxContextTokens)
    contextNoteCount.value = noteIds.length
    estimatedTokens.value = estimateTokens(buildChunkContext(chunks) + q)
  }, 500)
}

watch(input, scheduleContextUpdate)
watch(() => props.notes, scheduleContextUpdate, { deep: false })

// ── Mode change: clear messages & re-open state ─────────────
watch(() => props.mode, () => {
  // Close panel when switching pages so it doesn't stay open in wrong mode
  open.value = false
})

// ── Open note (notes mode) ───────────────────────────────────
function onOpenNote(noteId: string, headingAnchor?: string) {
  emit('openNote', noteId, headingAnchor)
  open.value = false
}

// ── Click outside to close ───────────────────────────────────
function onDocumentPointerDown(event: PointerEvent) {
  if (!open.value) return
  const target = event.target as Node | null
  if (!target) return
  if (panelRef.value?.contains(target) || triggerRef.value?.contains(target)) return
  open.value = false
}

onMounted(async () => {
  document.addEventListener('pointerdown', onDocumentPointerDown, true)
  try {
    memories.value = await loadAiMemories()
    const raw = await getSetting('ai_chat_history')
    if (raw) {
      const parsed = JSON.parse(raw) as ChatMsg[]
      if (Array.isArray(parsed)) messages.value = parsed
    }
  } catch {}
  historyLoaded.value = true
})

const MAX_HISTORY_MESSAGES = 50

let saveHistoryDebounce: ReturnType<typeof setTimeout> | null = null
watch(messages, () => {
  if (!historyLoaded.value) return
  if (saveHistoryDebounce) clearTimeout(saveHistoryDebounce)
  saveHistoryDebounce = setTimeout(() => {
    // strip scriptPayload before persisting (not needed across sessions)
    const toSave = messages.value.slice(-MAX_HISTORY_MESSAGES).map(m => ({
      role: m.role,
      content: m.content,
    }))
    setSetting('ai_chat_history', JSON.stringify(toSave)).catch(() => {})
  }, 300)
}, { deep: true })

onBeforeUnmount(() => {
  document.removeEventListener('pointerdown', onDocumentPointerDown, true)
})

watch(open, (v) => {
  if (v) {
    error.value = ''
    nextTick(() => messagesRef.value?.scrollTo({ top: messagesRef.value.scrollHeight }))
  }
})

// ── Send ─────────────────────────────────────────────────────
async function send() {
  const question = input.value.trim()
  if (!question || loading.value || !configured.value) return

  input.value = ''
  error.value = ''
  messages.value.push({ role: 'user', content: question })
  loading.value = true

  await nextTick()
  messagesRef.value?.scrollTo({ top: messagesRef.value.scrollHeight, behavior: 'smooth' })

  try {
    if (props.mode === 'script') {
      await sendScript(question)
    } else {
      await sendNotes(question)
    }
  } catch (e: any) {
    error.value = e.message || String(e)
  } finally {
    loading.value = false
    await nextTick()
    messagesRef.value?.scrollTo({ top: messagesRef.value.scrollHeight, behavior: 'smooth' })
  }
}

async function sendNotes(question: string) {
  const history = messages.value
    .filter(m => m.role === 'user' || m.role === 'assistant')
    .slice(0, -1)
    .map(m => ({ role: m.role, content: m.content }))

  const result = await chatWithNotes(props.aiConfig, question, props.notes, history, memories.value)
  messages.value.push({ role: 'assistant', content: result.answer })
}

async function sendScript(question: string) {
  const history = messages.value
    .filter(m => m.role === 'user' || m.role === 'assistant')
    .slice(0, -1)
    .map(m => ({ role: m.role, content: m.content }))

  const result = await callScriptAi({
    config: props.aiConfig,
    question,
    scriptType: props.scriptType ?? 'bat',
    currentContent: props.currentScriptContent ?? '',
    existingScriptNames: props.scriptNames ?? [],
    history,
  })

  // Build display message: description only (code is auto-applied)
  const displayContent = result.description || question

  messages.value.push({
    role: 'assistant',
    content: displayContent,
    scriptPayload: result,
  })

  // Auto-apply immediately — no manual button needed
  emit('applyScript', result)
}

// ── Memory extraction (notes mode) ──────────────────────────
async function extractFromLastQA() {
  if (memorizing.value || messages.value.length < 2) return
  const lastAssistant = [...messages.value].reverse().find(m => m.role === 'assistant')
  const lastUser = [...messages.value].reverse().find(m => m.role === 'user')
  if (!lastAssistant || !lastUser) return

  memorizing.value = true
  try {
    const existingTexts = memories.value.map(m => m.content)
    const facts = await extractMemories(props.aiConfig, lastUser.content, lastAssistant.content, existingTexts)
    for (const fact of facts) {
      const norm = fact.trim().toLowerCase().replace(/[，。！？；、,.!?;:]/g, '')
      const isDuplicate = memories.value.some(m => {
        const existing = m.content.trim().toLowerCase().replace(/[，。！？；、,.!?;:]/g, '')
        return existing === norm || existing.includes(norm) || norm.includes(existing)
      })
      if (!isDuplicate) {
        try {
          const saved = await saveAiMemory(fact)
          if (saved) memories.value.unshift(saved)
        } catch {
          console.warn('[NoteAiPanel] Failed to save memory:', fact)
        }
      }
    }
  } catch (e: any) {
    error.value = e?.message || String(e)
    console.warn('[NoteAiPanel] Memory extraction failed:', e?.message || e)
  } finally {
    memorizing.value = false
  }
}

async function clearHistory() {
  messages.value = []
  input.value = ''
  error.value = ''
  try { await setSetting('ai_chat_history', '') } catch {}
}

defineExpose({ open })
</script>

<style scoped>
.animate-ai-in {
  animation: aiSlideIn 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}
@keyframes aiSlideIn {
  from { transform: translateY(20px) scale(0.96); opacity: 0; }
  to { transform: translateY(0) scale(1); opacity: 1; }
}
</style>
