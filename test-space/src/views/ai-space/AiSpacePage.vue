<template>
  <div class="flex flex-1 min-h-0 -mx-margin-page overflow-hidden pb-4 box-border select-none">
    <!-- Sessions Sidebar -->
    <div v-if="sessions.length > 0"
      class="flex-shrink-0 flex flex-col w-56 ml-3 overflow-hidden rounded-xl bg-white/10 backdrop-blur-[60px] border border-white/50 shadow-lg"
    >
      <div class="p-2 border-b border-glass-border-light/50 flex items-center gap-1">
        <div class="relative flex-1" ref="modeDropdownRef">
          <button class="w-full flex items-center justify-between gap-1 px-2 py-1.5 rounded-md text-[12px] glass-hover cursor-pointer transition-colors text-on-surface-variant select-none" @click="toggleModeDropdown">
            <span class="material-symbols-outlined text-[14px]">{{ currentTabIcon }}</span>
            <span class="truncate flex-1 ml-1">{{ currentTabLabel }}</span>
            <span class="material-symbols-outlined text-[14px]">expand_more</span>
          </button>
          <div v-if="showModeDropdown" class="absolute left-0 right-0 top-full mt-1 bg-white rounded-lg shadow-xl border border-gray-200/80 z-50 overflow-hidden">
            <div class="py-1">
              <div v-for="tab in tabs" :key="tab.key"
                class="flex items-center gap-2 px-3 py-1.5 text-[12px] cursor-pointer transition-colors"
                :class="mode === tab.key ? 'bg-purple-100/60 text-secondary font-medium' : 'hover:bg-gray-50 text-on-surface-variant'"
                @click="switchMode(tab.key); showModeDropdown = false"
              >
                <span class="material-symbols-outlined text-[14px]">{{ tab.icon }}</span>
                <span>{{ t(tab.labelKey) }}</span>
              </div>
            </div>
          </div>
        </div>
        <button class="glass-button !border-0 px-1.5 py-1.5 select-none" :title="t('ai.newSession')" @click="createNewSession">
          <span class="material-symbols-outlined text-[14px]">add</span>
        </button>
      </div>
      <div class="flex-1 overflow-y-auto custom-scrollbar p-1.5 space-y-0.5">
        <div v-for="s in sessions" :key="s.id"
          class="group flex items-center gap-2 px-2.5 py-2 rounded-lg cursor-pointer transition-colors"
          :class="s.id === activeSessionId
            ? 'bg-purple-100/60 text-secondary font-medium shadow-sm'
            : 'text-on-surface-variant hover:bg-white/15 hover:text-on-surface'"
          @click="switchSession(s.id)"
        >
          <span class="material-symbols-outlined text-[14px] shrink-0" :class="s.id === activeSessionId ? 'text-secondary' : 'text-on-surface-variant/40'">{{ modeIcon(s.mode) }}</span>
          <div class="flex-1 min-w-0">
            <template v-if="renamingId === s.id">
              <input ref="renameInputRef" v-model="renameValue"
                class="w-full bg-transparent border-b border-secondary/60 outline-none text-[12px] font-medium select-text"
                @blur="commitRename"
                @keydown.enter="commitRename"
                @keydown.escape="cancelRename"
                @click.stop
              />
            </template>
            <div v-else class="flex items-center gap-1.5">
              <span class="block truncate text-[12px]" @dblclick.stop="startRename(s)">{{ s.title || 'New Chat' }}</span>
              <span class="text-[9px] px-1 py-0.5 rounded-full bg-white/30 border border-glass-border-light/30 text-on-surface-variant/50 shrink-0">{{ modeLabel(s.mode) }}</span>
            </div>
          </div>
          <button class="opacity-0 group-hover:opacity-100 p-0.5 rounded hover:bg-white/10 text-on-surface-variant/40 hover:text-red-400 transition-all shrink-0"
            @click.stop="confirmDeleteSession(s)"
          >
            <span class="material-symbols-outlined text-[13px]">delete</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Chat Area -->
    <div class="flex-1 min-w-0 flex flex-col bg-transparent pl-3 pr-3" :class="sessions.length > 0 ? 'pt-4' : 'pt-4 pl-3 pr-3'">
      <!-- Empty state when no sessions -->
      <div v-if="!activeSession" class="flex-1 glass-panel rounded-xl flex flex-col items-center justify-center shadow-md gap-3">
        <span class="material-symbols-outlined text-5xl text-on-surface-variant/20">smart_toy</span>
        <p class="text-[13px] text-on-surface-variant/60">{{ t('ai.noSession') }}</p>
        <button class="glass-button px-5 py-2 rounded-full text-[13px] glass-active select-none" @click="createNewSession">
          <span class="material-symbols-outlined text-[16px] mr-1">add</span>
          {{ t('ai.newSession') }}
        </button>
      </div>

      <template v-if="activeSession">
        <!-- Messages -->
        <div ref="messagesRef" @click="onMessagesClick"
          class="flex-1 overflow-y-auto custom-scrollbar space-y-3 py-2 pr-1 min-h-0"
        >
          <div v-for="(msg, i) in activeSession.messages" :key="i"
            class="text-[13px] leading-relaxed"
            :class="msg.role === 'user' ? 'flex justify-end' : ''"
          >
            <div class="max-w-[80%] px-4 py-2.5 rounded-2xl whitespace-pre-wrap break-words select-text"
              :class="msg.role === 'user'
                ? 'bg-purple-100/80 text-on-surface rounded-br-md'
                : 'bg-white/90 text-on-surface border border-glass-border-light/40 rounded-bl-md'"
            >
              <template v-if="msg.role === 'user'">
                <div v-if="msg.image" class="mb-2">
                  <img :src="msg.image" class="max-w-[240px] max-h-[240px] rounded-lg border border-glass-border-light/30" />
                </div>
                <div v-if="msg.fileContent" class="mb-1 text-[11px] text-on-surface-variant/70 bg-white/40 rounded px-2 py-1 border border-glass-border-light/30">
                  <span class="material-symbols-outlined text-[12px] mr-1">description</span>{{ msg.fileName }}
                </div>
                {{ msg.content }}
              </template>
              <template v-else>
                <div class="whitespace-pre-wrap" v-html="renderNoteLinks(msg.content)"></div>
                <div v-if="msg.toolCalls?.length" class="mt-2 pt-2 border-t border-glass-border-light/30">
                  <div v-for="tc in msg.toolCalls" :key="tc.toolName" class="text-[11px] text-on-surface-variant/60 flex items-center gap-1">
                    <span class="material-symbols-outlined text-[13px]">check_circle</span>
                    <span>Called: {{ tc.toolName }} on {{ tc.serverName }}</span>
                  </div>
                </div>
              </template>
            </div>
          </div>
          <div v-if="sessionLoading.get(activeSessionId)" class="flex items-center gap-2 text-[12px] text-on-surface-variant px-2">
            <span class="material-symbols-outlined text-[16px] animate-spin">sync</span>
            {{ loadingLabel }}
          </div>
        </div>

        <div v-if="sessionError.get(activeSessionId)" class="mx-1 mb-1 px-3 py-1.5 text-[11px] text-red-500 shrink-0 break-words bg-white/60 rounded-lg border border-red-200/50">{{ sessionError.get(activeSessionId) }}</div>

        <!-- Input -->
        <div class="flex gap-2 shrink-0 pb-2 pt-2 items-end">
          <div class="flex-1 flex flex-col gap-1.5">
            <div v-if="uploadedImage || attachedFile" class="flex items-center gap-2 px-1">
              <template v-if="uploadedImage">
                <img :src="uploadedImage" class="h-10 w-10 rounded-lg object-cover border border-glass-border-light/30" />
                <span class="text-[11px] text-on-surface-variant/60">{{ t('ai.imageAttached') }}</span>
              </template>
              <template v-if="attachedFile">
                <div class="flex items-center gap-1.5 px-2 py-1 bg-white/60 rounded-lg border border-glass-border-light/40">
                  <span class="material-symbols-outlined text-[14px] text-on-surface-variant/60">description</span>
                  <span class="text-[11px] text-on-surface-variant/80">{{ attachedFile.name }}</span>
                </div>
              </template>
              <button class="ml-auto p-0.5 rounded hover:bg-white/10 text-on-surface-variant/40 hover:text-red-400 transition-colors" @click="clearAttachments">
                <span class="material-symbols-outlined text-[14px]">close</span>
              </button>
            </div>
            <div class="relative glass-panel rounded-xl border border-purple-200/50 shadow-sm bg-white/80 ring-1 ring-purple-300/40 focus-within:ring-purple-400/70 transition-all">
              <textarea ref="inputRef" v-model="input"
                :placeholder="inputPlaceholder"
                class="ai-input-textarea w-full bg-transparent px-4 py-2.5 text-[13px] outline-none select-text resize-none rounded-xl"
                :disabled="sessionLoading.get(activeSessionId)"
                rows="1"
                @keydown="onInputKeydown"
                @paste="onInputPaste"
                @input="autoResizeInput"
              ></textarea>
            </div>
          </div>
          <div class="flex gap-1">
            <button v-if="mode !== 'notes'" class="glass-button px-2.5 py-2.5 rounded-xl text-on-surface-variant/60 hover:text-on-surface select-none shrink-0" :title="t('ai.attach')" @click="triggerFileUpload">
              <span class="material-symbols-outlined text-[18px]">attach_file</span>
            </button>
            <button v-if="mode === 'mcp'" class="glass-button px-2.5 py-2.5 rounded-xl text-on-surface-variant/60 hover:text-on-surface select-none shrink-0" :title="t('ai.mcpSettings')" @click="showMcpManager = true">
              <span class="material-symbols-outlined text-[18px]">extension</span>
            </button>
            <button class="glass-button px-3.5 py-2.5 rounded-xl glass-active select-none shrink-0"
              :disabled="sessionLoading.get(activeSessionId) || (!input.trim() && !uploadedImage && !attachedFile)"
              @click="send"
            >
              <span class="material-symbols-outlined text-[18px]">send</span>
            </button>
          </div>
          <input ref="fileInputRef" type="file" accept="image/*,.txt" class="hidden" @change="onFileSelected" />
        </div>
      </template>
    </div>

    <!-- MCP Server Manager Modal -->
    <Teleport to="body">
      <div v-if="showMcpManager" class="fixed inset-0 z-[9999] flex items-center justify-center bg-black/20 backdrop-blur-sm" @click.self="showMcpManager = false">
        <div class="glass-panel rounded-2xl p-5 w-[480px] border border-glass-border-light shadow-2xl flex flex-col gap-4 bg-white/90">
          <div class="flex items-center justify-between">
            <span class="text-[15px] font-semibold text-on-surface">{{ t('ai.mcpSettings') }}</span>
            <button class="p-0.5 rounded hover:bg-white/10 text-on-surface-variant/40 hover:text-on-surface transition-colors" @click="showMcpManager = false">
              <span class="material-symbols-outlined text-[18px]">close</span>
            </button>
          </div>
          <div class="max-h-[300px] overflow-y-auto custom-scrollbar space-y-2">
            <div v-for="server in servers" :key="server.id">
              <div class="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/40 border border-glass-border-light/40">
                <button class="p-0.5 rounded hover:bg-white/10 transition-colors shrink-0" :title="server.enabled ? t('ai.mcpDisable') : t('ai.mcpEnable')" @click="toggleServer(server.id)">
                  <span class="material-symbols-outlined text-[16px]" :class="server.enabled ? 'text-green-500' : 'text-on-surface-variant/30'">{{ server.enabled ? 'check_circle' : 'radio_button_unchecked' }}</span>
                </button>
                <div class="flex-1 min-w-0 cursor-pointer" @click="editServer(server)">
                  <div class="text-[12px] font-medium truncate flex items-center gap-1.5">
                    {{ server.name }}
                    <span class="text-[9px] px-1.5 py-0.5 rounded-full bg-white/40 border border-glass-border-light/30 text-on-surface-variant/60">{{ authTypeLabel(server.authType) }}</span>
                  </div>
                  <div class="text-[10px] text-on-surface-variant/50 truncate">{{ server.endpoint }}</div>
                </div>
                <button class="p-0.5 rounded hover:bg-white/10 text-on-surface-variant/40 hover:text-yellow-600 transition-colors shrink-0" :title="t('notes.rename')" @click="editServer(server)">
                  <span class="material-symbols-outlined text-[14px]">edit</span>
                </button>
                <button class="p-0.5 rounded hover:bg-white/10 text-on-surface-variant/40 hover:text-blue-500 transition-colors shrink-0" :title="t('ai.mcpTest')" :disabled="testingServers.has(server.id)" @click="testServer(server)">
                  <span v-if="!testingServers.has(server.id)" class="material-symbols-outlined text-[14px]">wifi_tethering</span>
                  <svg v-else class="w-[14px] h-[14px] animate-spin" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
                </button>
                <button class="p-0.5 rounded hover:bg-white/10 text-on-surface-variant/40 hover:text-red-400 transition-colors shrink-0" :title="t('notes.delete')" @click="deleteServer(server.id)">
                  <span class="material-symbols-outlined text-[14px]">delete</span>
                </button>
              </div>
              <div v-if="server.enabled && serverTools[server.id]?.length" class="ml-6 mt-1 mb-2 flex flex-wrap gap-1.5">
                <button v-for="tool in serverTools[server.id]" :key="tool.name"
                  class="text-[10px] px-2 py-0.5 rounded-full border transition-all select-none flex items-center gap-1"
                  :class="isToolDisabled(server.id, tool.name)
                    ? 'bg-gray-100 text-on-surface-variant/50 border-gray-200 line-through'
                    : 'bg-white/60 text-secondary border-secondary/30 hover:bg-secondary/10'"
                  @click="toggleTool(server.id, tool.name)"
                >
                  {{ tool.name }}
                </button>
              </div>
            </div>
            <div v-if="servers.length === 0" class="text-[12px] text-on-surface-variant/40 text-center py-4">{{ t('ai.mcpNoServers') }}</div>
          </div>
          <div class="border-t border-glass-border-light/30 pt-3 flex flex-col gap-2">
            <div class="flex items-center justify-between">
              <span class="text-[12px] font-medium text-on-surface">{{ isEditing ? t('notes.rename') : t('ai.mcpNewServer') }}</span>
              <button v-if="isEditing" class="text-[11px] text-on-surface-variant/60 hover:text-on-surface transition-colors select-none" @click="cancelEdit">{{ t('settings.cancel') }}</button>
            </div>
            <input v-model="newServerName" class="glass-input w-full px-3 py-2 rounded-lg text-[12px] outline-none select-text" :placeholder="t('ai.mcpServerNamePlaceholder')" />
            <input v-model="newServerEndpoint" class="glass-input w-full px-3 py-2 rounded-lg text-[12px] outline-none select-text" :placeholder="t('ai.mcpEndpointPlaceholder')" />
            <div class="flex items-center gap-2 flex-wrap">
              <select v-model="newServerAuthType" class="glass-input px-2 py-2 rounded-lg text-[12px] outline-none select-text bg-white/80 flex-shrink-0 w-[130px]">
                <option value="none">{{ t('ai.mcpAuthNone') }}</option>
                <option value="bearer">{{ t('ai.mcpAuthBearer') }}</option>
                <option value="api-key">{{ t('ai.mcpAuthApiKey') }}</option>
                <option value="custom">{{ t('ai.mcpAuthCustom') }}</option>
              </select>
              <input v-if="newServerAuthType !== 'none'" v-model="newServerAuthValue" class="glass-input w-full px-3 py-2 rounded-lg text-[12px] outline-none select-text flex-1 min-w-[120px]" :placeholder="t('ai.mcpAuthValuePlaceholder')" />
              <input v-if="newServerAuthType === 'custom'" v-model="newServerCustomHeader" class="glass-input w-full px-3 py-2 rounded-lg text-[12px] outline-none select-text flex-1 min-w-[120px]" :placeholder="t('ai.mcpAuthHeaderPlaceholder')" />
            </div>
            <button class="glass-button self-end px-4 py-1.5 rounded-full text-[12px] glass-active select-none" :disabled="!newServerName.trim() || !newServerEndpoint.trim()" @click="addOrUpdateServer">
              {{ t('settings.confirm') }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Delete Session Confirm -->
    <Teleport to="body">
      <div v-if="deleteTarget" class="fixed inset-0 z-[9999] flex items-center justify-center bg-black/20 backdrop-blur-sm" @click.self="deleteTarget = null">
        <div class="glass-panel rounded-2xl p-5 w-[340px] border border-glass-border-light shadow-2xl flex flex-col gap-4 bg-white/90">
          <div class="text-[15px] font-semibold text-on-surface">{{ t('notes.deleteNote') }}</div>
          <div class="text-[12px] text-on-surface-variant">{{ t('notes.deleteNoteDesc', { name: deleteTarget.title || 'New Chat' }) }}</div>
          <div class="flex justify-end gap-2">
            <button class="px-4 py-1.5 rounded-full text-[12px] text-on-surface-variant border border-glass-border-light hover:bg-white/10 transition-colors select-none" @click="deleteTarget = null">{{ t('settings.cancel') }}</button>
            <button class="px-4 py-1.5 rounded-full text-[12px] bg-red-500/20 text-red-400 hover:bg-red-500/30 transition-colors select-none" @click="doDeleteSession">{{ t('notes.delete') }}</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Not configured overlay -->
    <Teleport to="body">
      <div v-if="!configured" class="fixed inset-0 z-[999] flex items-center justify-center bg-white/60 backdrop-blur-sm" @click.self="goSettings">
        <div class="glass-panel rounded-2xl p-8 w-[360px] border border-glass-border-light shadow-2xl flex flex-col items-center gap-4 bg-white/95">
          <span class="material-symbols-outlined text-[48px] text-on-surface-variant/30">settings</span>
          <p class="text-[13px] text-on-surface-variant text-center">{{ t('ai.noConfig') }}</p>
          <button class="glass-button px-5 py-2 rounded-full text-[13px] glass-active select-none" @click="goSettings">
            {{ t('ai.goSettings') }}
          </button>
        </div>
      </div>
    </Teleport>

    <!-- Toast -->
    <div v-if="toast" class="fixed bottom-6 left-1/2 -translate-x-1/2 z-[99999] px-5 py-2.5 rounded-full text-[13px] font-semibold shadow-2xl border pointer-events-none transition-all"
      :class="toast.ok ? 'bg-green-700 text-white border-green-500' : 'bg-red-700 text-white border-red-500'">
      {{ toast.msg }}
    </div>
  </div>
</template>

<script setup lang="ts">
defineOptions({ name: 'AiSpacePage' })
import { ref, reactive, computed, watch, nextTick, onMounted, onActivated, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from '@/composables/useI18n'
import { isAiConfigured, loadAiConfig, type AiConfig } from '@/services/aiSettings'
import { chatWithNotes, callAiChat, resolveSystemRole, type AiChatMessage } from '@/services/noteAi'
import { useTokenUsage } from '@/stores/useTokenUsage'
import { loadNotes } from '@/services/database'
import type { AiSession, ChatMsg, ChatMode, NoteItem, McpServerConfig, McpAuthType, McpTool } from '@/types'
import {
  loadMcpServers,
  saveMcpServers,
  addMcpServer,
  deleteMcpServer,
  updateMcpServer,
  listTools,
  callTool as mcpCallTool,
  getAllToolsFlat,
  type McpToolDescriptor,
} from '@/services/mcpService'
import { getSetting, setSetting } from '@/services/database'

const { t } = useI18n()
const router = useRouter()
const { addUsage, loadUsage } = useTokenUsage()

const tabs = [
  { key: 'chat' as ChatMode, labelKey: 'ai.chatTab', icon: 'chat' },
  { key: 'notes' as ChatMode, labelKey: 'ai.notesTab', icon: 'description' },
  { key: 'mcp' as ChatMode, labelKey: 'ai.mcpTab', icon: 'extension' },
]

const mode = ref<ChatMode>('chat')
const input = ref('')
const messagesRef = ref<HTMLDivElement>()
const inputRef = ref<HTMLTextAreaElement>()
const historyLoaded = ref(false)
const showModeDropdown = ref(false)
const modeDropdownRef = ref<HTMLDivElement>()

function modeIcon(m: ChatMode): string {
  return tabs.find(t => t.key === m)?.icon || 'chat'
}
function modeLabel(m: ChatMode): string {
  return t(tabs.find(t => t.key === m)?.labelKey || 'ai.chatTab')
}
const currentTabIcon = computed(() => modeIcon(mode.value))
const currentTabLabel = computed(() => modeLabel(mode.value))
const inputPlaceholder = computed(() => {
  if (mode.value === 'chat') return t('ai.inputPlaceholder')
  if (mode.value === 'notes') return t('ai.inputNotesPlaceholder')
  return t('ai.inputMcpPlaceholder')
})

// ── Per-session loading/error state (using reactive Map to avoid spread overhead) ──
const sessionLoading = reactive(new Map<string, boolean>())
const sessionError = reactive(new Map<string, string>())

function setLoading(sessionId: string, v: boolean) {
  sessionLoading.set(sessionId, v)
}
function setError(sessionId: string, msg: string) {
  sessionError.set(sessionId, msg)
}
function clearError(sessionId: string) {
  sessionError.delete(sessionId)
}

// ── Sessions ──
const sessions = ref<AiSession[]>([])
const activeSessionId = ref<string>('')

const activeSession = computed(() => sessions.value.find(s => s.id === activeSessionId.value))

interface ToolCallInfo {
  toolName: string
  serverName: string
}

// ── Image / File upload ──
const fileInputRef = ref<HTMLInputElement>()
const uploadedImage = ref('')
const attachedFile = ref<{ name: string; content: string } | null>(null)

function triggerFileUpload() {
  fileInputRef.value?.click()
}

function clearAttachments() {
  uploadedImage.value = ''
  attachedFile.value = null
}

function onFileSelected(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  if (file.type.startsWith('image/')) {
    const reader = new FileReader()
    reader.onload = () => { uploadedImage.value = reader.result as string }
    reader.readAsDataURL(file)
  } else if (file.name.endsWith('.txt')) {
    const reader = new FileReader()
    reader.onload = () => {
      attachedFile.value = { name: file.name, content: reader.result as string }
    }
    reader.readAsText(file)
  }
  ;(e.target as HTMLInputElement).value = ''
}

// ── Clipboard paste ──
function onInputPaste(e: ClipboardEvent) {
  handlePaste(e)
}

function handlePaste(e: ClipboardEvent) {
  const items = e.clipboardData?.items
  if (!items) return
  for (let i = 0; i < items.length; i++) {
    const item = items[i]
    if (item.type.startsWith('image/')) {
      e.preventDefault()
      const blob = item.getAsFile()
      if (!blob) continue
      const reader = new FileReader()
      reader.onload = () => { uploadedImage.value = reader.result as string }
      reader.readAsDataURL(blob)
      break
    }
  }
}

// ── AI Config ──
const aiConfig = ref<AiConfig>({
  provider: 'azure', apiKey: '', endpoint: '', model: '', maxContextTokens: 8000, authMode: 'api-key',
})
const configured = computed(() => isAiConfigured(aiConfig.value))

// Notes (with cache to avoid re-fetching on keep-alive reactivation)
const notes = ref<NoteItem[]>([])
const contextNoteCount = ref(0)
let _notesCache: NoteItem[] | null = null

// MCP
const servers = ref<McpServerConfig[]>([])
const allTools = ref<McpToolDescriptor[]>([])
const showMcpManager = ref(false)
const newServerName = ref('')
const newServerEndpoint = ref('')
const newServerAuthType = ref<McpAuthType>('none')
const newServerAuthValue = ref('')
const newServerCustomHeader = ref('Authorization')
const editingServerId = ref<string | null>(null)
const isEditing = computed(() => editingServerId.value !== null)
const testingServers = ref<Set<string>>(new Set())

const loadingLabel = computed(() => mode.value === 'mcp' ? t('ai.mcpThinking') : t('ai.thinking'))

// ── Session persistence ──
const SESSIONS_KEY = 'ai_chat_sessions'

async function loadSessions() {
  try {
    const raw = await getSetting(SESSIONS_KEY)
    if (raw) {
      const parsed = JSON.parse(raw) as AiSession[]
      if (Array.isArray(parsed)) sessions.value = parsed
    }
  } catch {}
  ensureSessionExists()
}

function ensureSessionExists() {
  const modeSessions = sessions.value.filter(s => s.mode === mode.value)
  if (modeSessions.length > 0) {
    if (!activeSessionId.value || !modeSessions.some(s => s.id === activeSessionId.value)) {
      activeSessionId.value = modeSessions[0].id
    }
  } else {
    createNewSession()
  }
}

function createNewSession() {
  const id = crypto.randomUUID()
  const s: AiSession = {
    id,
    title: 'New Chat',
    mode: mode.value,
    messages: [],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  }
  sessions.value.push(s)
  activeSessionId.value = id
  input.value = ''
  clearError(id)
  nextTick(() => inputRef.value?.focus())
}

function switchSession(id: string) {
  if (id === activeSessionId.value) return
  activeSessionId.value = id
  const s = sessions.value.find(ses => ses.id === id)
  if (s && s.mode !== mode.value) {
    mode.value = s.mode
    if (mode.value === 'mcp') refreshTools()
  }
  input.value = ''
  cancelRename()
  clearAttachments()
  nextTick(() => inputRef.value?.focus())
}

// ── Rename ──
const renamingId = ref<string | null>(null)
const renameValue = ref('')
const renameInputRef = ref<HTMLInputElement>()

function startRename(s: AiSession) {
  renamingId.value = s.id
  renameValue.value = s.title || 'New Chat'
  nextTick(() => {
    renameInputRef.value?.focus()
    renameInputRef.value?.select()
  })
}

function commitRename() {
  if (!renamingId.value) return
  const s = sessions.value.find(ses => ses.id === renamingId.value)
  if (s) {
    s.title = renameValue.value.trim() || 'New Chat'
    s.updatedAt = new Date().toISOString()
  }
  renamingId.value = null
}

function cancelRename() {
  renamingId.value = null
}

// ── Delete ──
const deleteTarget = ref<AiSession | null>(null)
function confirmDeleteSession(s: AiSession) {
  deleteTarget.value = s
}
function doDeleteSession() {
  if (!deleteTarget.value) return
  const id = deleteTarget.value.id
  sessions.value = sessions.value.filter(s => s.id !== id)
  clearError(id)
  if (activeSessionId.value === id) {
    const modeSessions = sessions.value.filter(s => s.mode === mode.value)
    activeSessionId.value = modeSessions.length > 0 ? modeSessions[0].id : ''
    if (!activeSessionId.value) createNewSession()
  }
  deleteTarget.value = null
}

function saveSessions() {
  setSetting(SESSIONS_KEY, JSON.stringify(sessions.value)).catch(() => {})
}

let saveTimer: ReturnType<typeof setTimeout> | null = null
// Watch length + active session messages length to detect changes without deep watching full objects
watch(
  [() => sessions.value.length, () => activeSession.value?.messages.length],
  () => {
    if (!historyLoaded.value) return
    if (saveTimer) clearTimeout(saveTimer)
    saveTimer = setTimeout(saveSessions, 800)
  },
)

// ── Mode dropdown ──
function toggleModeDropdown() {
  showModeDropdown.value = !showModeDropdown.value
}

function onDocumentClick(e: MouseEvent) {
  const el = modeDropdownRef.value
  if (!el || showModeDropdown.value) {
    const target = e.target as HTMLElement
    if (el && !el.contains(target)) {
      showModeDropdown.value = false
    }
  }
}

// ── Mode switching ──
function switchMode(newMode: ChatMode) {
  if (newMode === mode.value) return
  mode.value = newMode
  showModeDropdown.value = false
  ensureSessionExists()
  clearAttachments()
  if (newMode === 'mcp') refreshTools().catch(() => {})
}

// ── API helpers ──
let tauriFetch: typeof fetch | null = null
async function getFetch(): Promise<typeof fetch> {
  if (tauriFetch) return tauriFetch
  try {
    const mod = await import('@tauri-apps/plugin-http')
    tauriFetch = mod.fetch
  } catch { tauriFetch = fetch }
  return tauriFetch
}

async function callChatApiWithImage(prompt: string, imageBase64: string, history: AiChatMessage[]): Promise<string> {
  const f = await getFetch()
  const config = aiConfig.value
  const body: Record<string, unknown> = {
    model: config.model.trim(),
    messages: [
      ...history,
      {
        role: 'user',
        content: [
          { type: 'text', text: prompt },
          { type: 'image_url', image_url: { url: imageBase64 } },
        ],
      },
    ],
  }
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (config.authMode === 'api-key') headers['api-key'] = config.apiKey.trim()
  else headers['Authorization'] = `Bearer ${config.apiKey.trim()}`
  const res = await f(config.endpoint.trim(), { method: 'POST', headers, body: JSON.stringify(body) })
  const text = await res.text()
  let json: any
  try { json = JSON.parse(text) } catch { throw new Error(`API ${res.status}: ${text.slice(0, 300)}`) }
  if (!res.ok) {
    const errMsg = json.error?.message || json.error?.code || `HTTP ${res.status}`
    throw new Error(typeof errMsg === 'string' ? errMsg : JSON.stringify(errMsg))
  }
  return json.choices?.[0]?.message?.content?.trim() || ''
}

function autoTitle(msg: string): string {
  return msg.length > 30 ? msg.slice(0, 30) + '...' : msg
}

// ── Input auto-resize ──
const INPUT_MAX_HEIGHT_RATIO = 0.50
function getInputMaxHeight(): number {
  return Math.floor(window.innerHeight * INPUT_MAX_HEIGHT_RATIO)
}
function autoResizeInput() {
  const el = inputRef.value
  if (!el) return
  const maxH = getInputMaxHeight()
  el.style.height = '0px'
  const target = el.scrollHeight
  el.style.height = Math.min(target, maxH) + 'px'
  el.style.overflowY = target > maxH ? 'auto' : 'hidden'
}

function onInputKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    send()
  }
}

// ── Send ──
async function send() {
  const sid = activeSessionId.value
  if (!sid) return
  const question = input.value.trim()
  const hasImage = !!uploadedImage.value
  const hasFile = !!attachedFile.value
  if ((!question && !hasImage && !hasFile) || sessionLoading.get(sid) || !configured.value) return

  if (!activeSession.value) ensureSessionExists()

  const imageData = uploadedImage.value
  const fileData = attachedFile.value
  input.value = ''
  clearAttachments()

  let content = question
  if (fileData) {
    content = `[File: ${fileData.name}]\n${fileData.content}${question ? '\n\n' + question : ''}`
  }

  const session = sessions.value.find(s => s.id === sid)
  if (!session) return

  if (session.messages.length === 0 && question) {
    session.title = autoTitle(question)
  }

  const userMsg: ChatMsg = { role: 'user', content: content }
  if (imageData) userMsg.image = imageData
  if (fileData) {
    userMsg.fileName = fileData.name
    userMsg.fileContent = fileData.content
  }

  session.messages.push(userMsg)
  session.updatedAt = new Date().toISOString()
  setLoading(sid, true)
  clearError(sid)

  await nextTick()
  scrollToBottom()

  try {
    if (mode.value === 'chat') {
      await sendChat(content, imageData, session)
    } else if (mode.value === 'notes') {
      await sendNotes(content, imageData, session)
    } else {
      await sendMcp(content, session)
    }
  } catch (e: any) {
    setError(sid, e.message || String(e))
  } finally {
    setLoading(sid, false)
    session.updatedAt = new Date().toISOString()
    await nextTick()
    scrollToBottom()
  }
}

async function sendChat(question: string, imageData: string, session: AiSession) {
  const history: AiChatMessage[] = session.messages
    .filter(m => m.role === 'user' || m.role === 'assistant')
    .slice(0, -1)
    .map(m => ({ role: m.role, content: m.content }))

  let answer: string
  let usage: any
  if (imageData) {
    answer = await callChatApiWithImage(question, imageData, history)
  } else {
    const result = await callAiChat(aiConfig.value, [
      { role: resolveSystemRole(aiConfig.value), content: 'You are a helpful assistant.' },
      ...history,
      { role: 'user', content: question },
    ])
    answer = result.answer
    usage = result.usage
  }
  addUsage(usage)
  session.messages.push({ role: 'assistant', content: answer || '(empty)' })
}

async function sendNotes(question: string, imageData: string, session: AiSession) {
  const history: AiChatMessage[] = session.messages
    .filter(m => m.role === 'user' || m.role === 'assistant')
    .slice(0, -1)
    .map(m => ({ role: m.role, content: m.content }))

  if (imageData) {
    await sendChat(question, imageData, session)
    return
  }

  const result = await chatWithNotes(aiConfig.value, question, notes.value, history)
  contextNoteCount.value = result.contextNoteCount
  addUsage(result.usage)
  session.messages.push({ role: 'assistant', content: result.answer })
}

async function sendMcp(question: string, session: AiSession) {
  const history = session.messages
    .filter(m => m.role === 'user' || m.role === 'assistant')
    .slice(-4)

  // Always fetch fresh tool list — caching causes stale data after server toggles
  const tools = await getAllToolsFlat()
  if (tools.length === 0) {
    await sendChat(question, '', session)
    return
  }

  const toolsDesc = tools.map(t =>
    `- ${t.tool.name}${t.tool.description ? ': ' + t.tool.description : ''}`
  ).join('\n')

  const systemRole = resolveSystemRole(aiConfig.value)
  const systemPrompt = `You are a helpful AI assistant with access to these MCP tools:\n${toolsDesc}\n\n## Tool Calling Protocol\nWhen a tool can help, output EXACTLY on its own line:\nTOOL_CALL: tool_name | {"arg1": "value1"}\n\n## Multi-Step Workflow\n- You can call tools multiple times across several rounds. After seeing tool results, you may call more tools or provide your final answer.\n- Think step by step: explain your plan, call a tool, review the result, then decide the next action.\n- You may interleave natural language explanations with TOOL_CALL lines.\n\n## Guidelines\n- Use tools only when they genuinely help answer the question.\n- If the first tool's result isn't sufficient, call another tool to get more information.\n- Handle errors: if a tool fails, explain what happened and try an alternative approach if possible.\n- When you have enough information, stop calling tools and provide your final answer.\n- If no tool is relevant, just answer directly using your own knowledge.`

  // Multi-round tool-calling loop
  // Round 1 sends full context (system prompt + tools + history + question).
  // Subsequent rounds send only the latest response + tool results — no need to repeat
  // tool lists or conversation history, which dramatically reduces token consumption.
  const MAX_ROUNDS = 5
  const toolCallRegex = /TOOL_CALL:\s*(\w[\w.-]*)\s*(?:\([^)]*\))?\s*\|\s*(\{.*?\})/g
  const allToolCalls: ToolCallInfo[] = []
  let accumulatedAnswer = ''
  let conversation: AiChatMessage[] = [
    { role: systemRole, content: systemPrompt },
    ...history.map(m => ({ role: m.role as 'user' | 'assistant', content: m.content })),
    { role: 'user', content: question },
  ]

  for (let round = 0; round < MAX_ROUNDS; round++) {
    const result = await callAiChat(aiConfig.value, conversation)
    const response = result.answer
    addUsage(result.usage)
    if (!response) break

    // Parse TOOL_CALL instructions
    const roundToolCalls: ToolCallInfo[] = []
    let cleanResponse = response
    let toolResults = ''
    let match: RegExpExecArray | null
    let hasValidCall = false

    toolCallRegex.lastIndex = 0
    while ((match = toolCallRegex.exec(response)) !== null) {
      const toolName = match[1]
      let args: Record<string, unknown> = {}
      try { args = JSON.parse(match[2]) } catch {}
      const tool = tools.find(t => t.tool.name === toolName)
      if (tool) {
        const server = servers.value.find(s => s.id === tool.serverId && s.enabled)
        if (server) {
          hasValidCall = true
          try {
            const toolResult = await mcpCallTool(server, toolName, args)
            const resultText = JSON.stringify(toolResult?.content || toolResult)
            toolResults += `\n[${toolName}] result: ${resultText}`
            roundToolCalls.push({ toolName, serverName: tool.serverName })
          } catch (e: any) {
            toolResults += `\n[${toolName}] error: ${e.message || e}`
          }
        }
      }
      cleanResponse = cleanResponse.replace(match[0], '')
    }

    // Accumulate AI's intermediate text (everything except TOOL_CALL lines)
    const intermediateText = cleanResponse.trim()
    if (intermediateText) {
      accumulatedAnswer += (accumulatedAnswer ? '\n\n' : '') + intermediateText
    }

    if (!hasValidCall) {
      // No more tool calls — this round's response is the final answer
      if (!accumulatedAnswer) accumulatedAnswer = response
      break
    }

    allToolCalls.push(...roundToolCalls)

    // Subsequent rounds: send ONLY the latest exchange + results, not the full context.
    // The AI already knows the tools and what the original goal was.
    conversation = [
      { role: systemRole, content: 'You are an AI assistant with MCP tools. Continue your work based on the context below.' },
      { role: 'user', content: `Your previous response:\n${response}\n\nTool results:${toolResults}\n\nReview these results and decide: call more tools or provide a final answer.` },
    ]
  }

  session.messages.push({
    role: 'assistant',
    content: accumulatedAnswer || '(no response)',
    toolCalls: allToolCalls.length > 0 ? allToolCalls : undefined,
  })
}

function scrollToBottom() {
  nextTick(() => {
    messagesRef.value?.scrollTo({ top: messagesRef.value.scrollHeight, behavior: 'smooth' })
  })
}

function goSettings() { router.push('/settings') }

function onMessagesClick(e: MouseEvent) {
  const target = e.target as HTMLElement
  const link = target.closest('[data-note-link]') as HTMLElement | null
  if (link) {
    e.preventDefault()
    const noteId = link.getAttribute('data-note-link')
    const href = link.getAttribute('href') || ''
    const headingMatch = href.match(/#([^#]+)$/)
    if (noteId) {
      router.push({ path: '/notes-space', query: { noteId, heading: headingMatch?.[1] ? decodeURIComponent(headingMatch[1]) : undefined } })
    }
  }
}

// ── Note link rendering ──
const NOTE_LINK_RE = /\[([^\]]+)\]\(note:([a-f0-9-]+)(?:#([^)]*))?\)/g
function renderNoteLinks(text: string): string {
  return text.replace(NOTE_LINK_RE, (match, displayText, noteId, heading) => {
    const href = heading
      ? `/notes-space?noteId=${noteId}&heading=${encodeURIComponent(heading)}`
      : `/notes-space?noteId=${noteId}`
    return `<a href="${href}" class="text-secondary underline hover:text-secondary/80 cursor-pointer" data-note-link="${noteId}">${displayText}</a>`
  })
}

// ── MCP ──
const authTypeLabels: Record<McpAuthType, string> = {
  none: t('ai.mcpAuthNone'),
  bearer: t('ai.mcpAuthBearer'),
  'api-key': t('ai.mcpAuthApiKey'),
  custom: t('ai.mcpAuthCustom'),
}
function authTypeLabel(type: McpAuthType): string { return authTypeLabels[type] || type }
async function loadAllNotes(force = false) {
  if (!force && _notesCache) { notes.value = _notesCache; return }
  try {
    notes.value = await loadNotes()
    _notesCache = notes.value
  } catch { notes.value = [] }
}
async function loadServers() {
  servers.value = await loadMcpServers()
  await loadServerTools()
}
const serverTools = ref<Record<string, McpTool[]>>({})
async function loadServerTools() {
  const enabledServers = servers.value.filter(s => s.enabled)
  // Concurrently list tools for all servers — don't let one slow server block the rest
  const results = await Promise.allSettled(
    enabledServers.map(async s => {
      const tools = await listTools(s)
      return { serverId: s.id, tools }
    })
  )
  const result: Record<string, McpTool[]> = {}
  for (const r of results) {
    if (r.status === 'fulfilled') {
      result[r.value.serverId] = r.value.tools
    }
  }
  serverTools.value = result
}
function isToolDisabled(serverId: string, toolName: string): boolean {
  const s = servers.value.find(x => x.id === serverId)
  return s ? (s.disabledTools || []).includes(toolName) : false
}
async function toggleTool(serverId: string, toolName: string) {
  const s = servers.value.find(x => x.id === serverId)
  if (!s) return
  const disabled = s.disabledTools || []
  s.disabledTools = disabled.includes(toolName)
    ? disabled.filter(n => n !== toolName)
    : [...disabled, toolName]
  await updateMcpServer(serverId, { disabledTools: s.disabledTools })
  // Refresh cached tools so MCP chat immediately reflects the change
  refreshTools().catch(() => {})
}
async function refreshTools() {
  if (mode.value === 'mcp') { try { allTools.value = await getAllToolsFlat() } catch { allTools.value = [] } }
}
async function toggleServer(id: string) {
  const server = servers.value.find(s => s.id === id)
  if (!server) return
  server.enabled = !server.enabled
  // Persist directly without closing SSE (updateMcpServer always closes it)
  const all = await loadMcpServers()
  const idx = all.findIndex(s => s.id === id)
  if (idx >= 0) { all[idx].enabled = server.enabled; await saveMcpServers(all) }
  // Refresh tools in background — don't block the UI toggle feedback
  loadServerTools().catch(() => {})
  refreshTools().catch(() => {})
}
async function testServer(server: McpServerConfig) {
  testingServers.value = new Set(testingServers.value).add(server.id)
  console.log(`[MCP Test] Testing ${server.name} (${server.endpoint}) authType=${server.authType}`)
  try {
    const tools = await listTools(server)
    console.log(`[MCP Test] SUCCESS: ${tools.length} tools found`, tools)
    showToast(t('ai.mcpTestSuccess') + ` (${tools.length} tools)`, true)
  } catch (e: any) {
    console.error(`[MCP Test] FAILED: ${e.message || e}`, e)
    showToast(t('ai.mcpTestFail', { msg: e.message || String(e) }), false)
  } finally {
    testingServers.value = new Set([...testingServers.value].filter(id => id !== server.id))
  }
}
async function deleteServer(id: string) {
  await deleteMcpServer(id)
  await loadServers()
  showToast(t('ai.mcpServerDeleted'), true)
}
function editServer(server: McpServerConfig) {
  editingServerId.value = server.id
  newServerName.value = server.name
  newServerEndpoint.value = server.endpoint
  newServerAuthType.value = server.authType
  newServerAuthValue.value = server.authValue || ''
  newServerCustomHeader.value = server.authHeader || 'Authorization'
}

function cancelEdit() {
  editingServerId.value = null
  newServerName.value = ''
  newServerEndpoint.value = ''
  newServerAuthType.value = 'none'
  newServerAuthValue.value = ''
  newServerCustomHeader.value = 'Authorization'
}

async function addOrUpdateServer() {
  const name = newServerName.value.trim()
  const endpoint = newServerEndpoint.value.trim()
  if (!name || !endpoint) return
  const authType = newServerAuthType.value
  try {
    if (editingServerId.value) {
      await updateMcpServer(editingServerId.value, {
        name, endpoint,
        authType,
        authValue: authType !== 'none' ? newServerAuthValue.value.trim() || undefined : undefined,
        authHeader: authType === 'custom' ? newServerCustomHeader.value.trim() || 'Authorization' : undefined,
      })
      showToast(t('ai.mcpServerAdded'), true)
    } else {
      await addMcpServer({
        name, endpoint,
        authType,
        authValue: authType !== 'none' ? newServerAuthValue.value.trim() || undefined : undefined,
        authHeader: authType === 'custom' ? newServerCustomHeader.value.trim() || 'Authorization' : undefined,
        enabled: true,
      })
      showToast(t('ai.mcpServerAdded'), true)
    }
    cancelEdit()
    await loadServers()
  } catch (e: any) { showToast(e?.message || 'Failed', false) }
}

// Toast
const toast = ref<{ msg: string; ok: boolean } | null>(null)
let toastTimer: ReturnType<typeof setTimeout> | null = null
function showToast(msg: string, ok: boolean) {
  if (toastTimer) clearTimeout(toastTimer)
  toast.value = { msg, ok }
  toastTimer = setTimeout(() => { toast.value = null }, 2000)
}

// Global paste listener (catches paste outside input)
function onGlobalPaste(e: ClipboardEvent) {
  const target = e.target as HTMLElement
  if (target.closest('.glass-panel') || target.tagName === 'INPUT' || target.tagName === 'TEXTAREA') return
  handlePaste(e)
}

onMounted(async () => {
  try {
    aiConfig.value = await loadAiConfig()
    historyLoaded.value = true
    await loadSessions()
  } catch {}
  await loadAllNotes()
  // Load servers + tools in the background — don't block UI on slow/unreachable MCP servers
  loadServers().catch(() => {})
  await loadUsage()
  if (mode.value === 'mcp') {
    try { allTools.value = await getAllToolsFlat() } catch { allTools.value = [] }
  }
  document.addEventListener('paste', onGlobalPaste)
  document.addEventListener('click', onDocumentClick)
})

onActivated(() => {
  if (!historyLoaded.value) {
    loadAiConfig().then(c => { aiConfig.value = c; historyLoaded.value = true }).catch(() => {})
  }
  loadAllNotes(false)
  loadServers().catch(() => {})
})

onUnmounted(() => {
  if (toastTimer) clearTimeout(toastTimer)
  if (saveTimer) clearTimeout(saveTimer)
  document.removeEventListener('paste', onGlobalPaste)
  document.removeEventListener('click', onDocumentClick)
})
</script>

<style scoped>
.ai-input-textarea::-webkit-scrollbar {
  width: 5px;
}
.ai-input-textarea::-webkit-scrollbar-track {
  background: transparent;
}
.ai-input-textarea::-webkit-scrollbar-thumb {
  background: rgba(139, 92, 246, 0.25);
  border-radius: 10px;
}
.ai-input-textarea::-webkit-scrollbar-thumb:hover {
  background: rgba(139, 92, 246, 0.4);
}
</style>