<template>
  <div class="relative flex flex-1 min-h-0 -mx-margin-page overflow-hidden pb-4 box-border select-none">
    <!-- Sessions Sidebar -->
    <div v-if="sessions.length > 0"
      class="flex-shrink-0 flex flex-col w-56 ml-3 overflow-hidden rounded-xl bg-white/10 backdrop-blur-[60px] border border-white/50"
    >
      <div class="p-2 border-b border-glass-border-light/50 flex items-center gap-1">
        <div class="relative flex-1" ref="modeDropdownRef">
          <button class="w-full flex items-center justify-between gap-1 px-2 py-1.5 rounded-md text-[12px] glass-hover cursor-pointer transition-colors text-on-surface-variant select-none" @click="toggleModeDropdown">
            <span class="material-symbols-outlined text-[14px]">{{ currentTabIcon }}</span>
            <span class="truncate flex-1 ml-1">{{ currentTabLabel }}</span>
            <span class="material-symbols-outlined text-[14px]">expand_more</span>
          </button>
          <div v-if="showModeDropdown" class="absolute left-0 right-0 top-full mt-1 bg-white rounded-lg border border-gray-200/80 z-50 overflow-hidden">
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
          class="ai-session-item group flex items-center gap-2 px-2.5 py-2 rounded-lg cursor-pointer"
          :class="s.id === activeSessionId ? 'is-active' : ''"
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
      <div v-if="!activeSession" class="flex-1 glass-panel rounded-xl flex flex-col items-center justify-center gap-3">
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
            v-memo="[msg.content, msg.streaming, msg.role, msg.image, msg.fileName, msg.toolCalls?.length ?? 0]"
            class="text-[13px] leading-relaxed group/msg"
            :class="msg.role === 'user' ? 'flex justify-end' : ''"
          >
            <div class="relative max-w-[80%] px-4 py-2.5 rounded-2xl whitespace-pre-wrap break-words select-text"
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
                <div v-if="msg.streaming" class="ai-markdown whitespace-normal" v-html="renderStreamingMarkdown(msg.content)"></div>
                <div v-else class="ai-markdown whitespace-normal" v-html="renderMarkdown(msg.content)"></div>
                <div v-if="msg.toolCalls?.length" class="mt-2 pt-2 border-t border-glass-border-light/30">
                  <div v-for="tc in msg.toolCalls" :key="tc.toolName" class="text-[11px] text-on-surface-variant/60 flex items-center gap-1">
                    <span class="material-symbols-outlined text-[13px]">check_circle</span>
                    <span>Called: {{ tc.toolName }} on {{ tc.serverName }}</span>
                  </div>
                </div>
                <div v-if="!msg.streaming"
                  class="flex gap-1 mt-1.5 pt-1.5 border-t border-transparent group-hover/msg:border-glass-border-light/30 opacity-0 group-hover/msg:opacity-100 transition-all"
                >
                  <button class="p-0.5 rounded hover:bg-black/5 text-on-surface-variant/40 hover:text-on-surface-variant transition-colors" @click="copyMessage(msg.content)" title="复制">
                    <span class="material-symbols-outlined text-[13px]">content_copy</span>
                  </button>
                  <button v-if="canRegenerate(i)" class="p-0.5 rounded hover:bg-black/5 text-on-surface-variant/40 hover:text-on-surface-variant transition-colors" @click="regenerate(i)" title="重新生成">
                    <span class="material-symbols-outlined text-[13px]">refresh</span>
                  </button>
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
            <div class="relative overflow-hidden glass-panel rounded-xl border border-purple-200/50 bg-white/80 ring-1 ring-purple-300/40 focus-within:ring-purple-400/70 transition-all">
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
            <button v-if="!sessionAbortControllers.has(activeSessionId)" class="glass-button px-3.5 py-2.5 rounded-xl glass-active select-none shrink-0"
              :disabled="sessionLoading.get(activeSessionId) || (!input.trim() && !uploadedImage && !attachedFile)"
              @click="send"
            >
              <span class="material-symbols-outlined text-[18px]">send</span>
            </button>
            <button v-else class="glass-button px-3.5 py-2.5 rounded-xl glass-active select-none shrink-0 !text-red-400 hover:!bg-red-50/50"
              @click="stopGeneration"
            >
              <span class="material-symbols-outlined text-[18px]">stop</span>
            </button>
          </div>
          <input ref="fileInputRef" type="file" accept="image/*,.txt" class="hidden" @change="onFileSelected" />
        </div>
      </template>
    </div>

    <!-- MCP Server Manager Modal -->
    <Teleport to="body">
      <div v-if="showMcpManager" class="fixed inset-0 z-[9999] flex items-center justify-center bg-black/20" @click.self="showMcpManager = false">
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
      <div v-if="deleteTarget" class="fixed inset-0 z-[9999] flex items-center justify-center bg-black/20" @click.self="deleteTarget = null">
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

    <!-- Not configured mask (只盖住 AI 页面区域，顶栏导航仍可点击) -->
    <div v-if="!configured" class="absolute inset-0 z-20 flex items-center justify-center bg-white/60 backdrop-blur-sm">
      <div class="rounded-2xl p-6 w-[320px] border border-outline-variant/40 shadow-lg flex flex-col items-center gap-3 bg-white">
        <span class="material-symbols-outlined text-[36px] text-on-surface-variant/40">settings</span>
        <p class="text-[13px] text-on-surface-variant text-center">{{ t('ai.noConfig') }}</p>
        <div class="flex gap-2 mt-1">
          <button class="glass-button px-4 py-1.5 rounded-full text-[13px] glass-active select-none" @click="goSettings">
            {{ t('ai.goSettings') }}
          </button>
          <button class="glass-button px-4 py-1.5 rounded-full text-[13px] flex items-center gap-1 select-none" :disabled="refreshingConfig" @click="refreshConfig" :title="t('cloudSync.syncing')">
            <span class="material-symbols-outlined text-[15px]" :class="refreshingConfig ? 'animate-spin' : ''">refresh</span>
          </button>
        </div>
      </div>
    </div>

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
import { chatWithNotes, callAiChat, callAiChatWithTools, callChatApiStream, chatWithNotesStream, resolveSystemRole, type AiChatMessage, type AiToolDefinition } from '@/services/noteAi'
import { renderMarkdown, renderStreamingMarkdown } from '@/composables/useMarkdownRenderer'
import { useTokenUsage } from '@/stores/useTokenUsage'
import { loadNoteList } from '@/services/database'
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
const { addUsage, loadUsage, flushUsage } = useTokenUsage()

const tabs = [
  { key: 'chat' as ChatMode, labelKey: 'ai.chatTab', icon: 'chat' },
  { key: 'notes' as ChatMode, labelKey: 'ai.notesTab', icon: 'description' },
  { key: 'mcp' as ChatMode, labelKey: 'ai.mcpTab', icon: 'extension' },
]

const mode = ref<ChatMode>('chat')
const input = ref('')
const messagesRef = ref<HTMLDivElement>()
const inputRef = ref<HTMLTextAreaElement>()
const draftInputs = ref<Record<string, string>>({})
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
const sessionAbortControllers = reactive(new Map<string, AbortController>())

function setLoading(sessionId: string, v: boolean) {
  sessionLoading.set(sessionId, v)
}
function setError(sessionId: string, msg: string) {
  sessionError.set(sessionId, msg)
}
function clearError(sessionId: string) {
  sessionError.delete(sessionId)
}
function stopGeneration() {
  const ac = sessionAbortControllers.get(activeSessionId.value)
  if (ac) ac.abort()
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
      if (Array.isArray(parsed)) {
        for (const s of parsed) {
          for (const m of s.messages) m.streaming = false
        }
        sessions.value = parsed
      }
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
  draftInputs.value[id] = ''
  clearError(id)
  nextTick(() => {
    resetInputHeight()
    inputRef.value?.focus()
  })
}

function resetInputHeight() {
  const el = inputRef.value
  if (!el) return
  el.style.height = 'auto'
}
function switchSession(id: string) {
  if (id === activeSessionId.value) return
  // Save draft for current session
  if (activeSessionId.value) {
    draftInputs.value[activeSessionId.value] = input.value
  }
  activeSessionId.value = id
  const s = sessions.value.find(ses => ses.id === id)
  if (s && s.mode !== mode.value) {
    mode.value = s.mode
    if (mode.value === 'mcp') refreshTools()
  }
  // Restore draft for target session
  input.value = draftInputs.value[id] || ''
  cancelRename()
  clearAttachments()
  nextTick(() => {
    resetInputHeight()
    autoResizeInput()
    inputRef.value?.focus()
  })
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
  saveSessions()
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
  const ac = sessionAbortControllers.get(id)
  if (ac) {
    ac.abort()
    sessionAbortControllers.delete(id)
  }
  sessions.value = sessions.value.filter(s => s.id !== id)
  clearError(id)
  sessionLoading.delete(id)
  if (activeSessionId.value === id) {
    const modeSessions = sessions.value.filter(s => s.mode === mode.value)
    activeSessionId.value = modeSessions.length > 0 ? modeSessions[0].id : ''
    if (!activeSessionId.value) createNewSession()
  }
  deleteTarget.value = null
}

function saveSessions() {
  // Defer serialization to avoid blocking UI on large session data
  setTimeout(() => {
    setSetting(SESSIONS_KEY, JSON.stringify(sessions.value)).catch(() => {})
  }, 0)
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

async function callChatApiWithImage(prompt: string, imageBase64: string, history: AiChatMessage[], signal?: AbortSignal): Promise<string> {
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
  const res = await f(config.endpoint.trim(), { method: 'POST', headers, body: JSON.stringify(body), signal })
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
  // Reset to measure scrollHeight; defer height calc to next frame so v-model
  // has updated the DOM (critical for paste of large text)
  el.style.height = '0px'
  requestAnimationFrame(() => {
    const maxH = getInputMaxHeight()
    const target = el.scrollHeight
    el.style.height = Math.min(target, maxH) + 'px'
    el.style.overflowY = target > maxH ? 'auto' : 'hidden'
  })
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
  draftInputs.value[sid] = ''
  clearAttachments()
  nextTick(() => resetInputHeight())

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
  const sid = session.id
  const history: AiChatMessage[] = session.messages
    .filter(m => m.role === 'user' || m.role === 'assistant')
    .slice(0, -1)
    .map(m => ({ role: m.role, content: m.content }))

  if (imageData) {
    const ac = new AbortController()
    sessionAbortControllers.set(sid, ac)
    try {
      const answer = await callChatApiWithImage(question, imageData, history, ac.signal)
      if (ac.signal.aborted) return
      session.messages.push({ role: 'assistant', content: answer || '(empty)' })
    } catch (e: any) {
      if (e.name === 'AbortError') return
      throw e
    } finally {
      sessionAbortControllers.delete(sid)
    }
    return
  }

  const messages: AiChatMessage[] = [
    { role: resolveSystemRole(aiConfig.value), content: 'You are a helpful assistant.' },
    ...history,
    { role: 'user', content: question },
  ]

  const msgIndex = session.messages.length
  session.messages.push({ role: 'assistant', content: '', streaming: true })

  const ac = new AbortController()
  sessionAbortControllers.set(sid, ac)

  try {
    let frameRequested = false
    const result = await callChatApiStream(aiConfig.value, messages, (delta) => {
      session.messages[msgIndex].content += delta
      if (!frameRequested) {
        frameRequested = true
        requestAnimationFrame(() => { frameRequested = false; scrollToBottom() })
      }
    }, ac.signal)

    addUsage(result.usage)
    if (result.aborted && !session.messages[msgIndex].content) {
      session.messages.splice(msgIndex, 1)
    }
  } finally {
    if (session.messages[msgIndex]) session.messages[msgIndex].streaming = false
    sessionAbortControllers.delete(sid)
  }
}

async function sendNotes(question: string, imageData: string, session: AiSession) {
  const sid = session.id
  const history: AiChatMessage[] = session.messages
    .filter(m => m.role === 'user' || m.role === 'assistant')
    .slice(0, -1)
    .map(m => ({ role: m.role, content: m.content }))

  if (imageData) {
    await sendChat(question, imageData, session)
    return
  }

  const msgIndex = session.messages.length
  session.messages.push({ role: 'assistant', content: '', streaming: true })

  const ac = new AbortController()
  sessionAbortControllers.set(sid, ac)

  try {
    let frameRequested = false
    const result = await chatWithNotesStream(aiConfig.value, question, notes.value, history, [], (delta) => {
      session.messages[msgIndex].content += delta
      if (!frameRequested) {
        frameRequested = true
        requestAnimationFrame(() => { frameRequested = false; scrollToBottom() })
      }
    }, ac.signal)

    contextNoteCount.value = result.contextNoteCount
    addUsage(result.usage)
    if (result.aborted && !session.messages[msgIndex].content) {
      session.messages.splice(msgIndex, 1)
    }
  } finally {
    if (session.messages[msgIndex]) session.messages[msgIndex].streaming = false
    sessionAbortControllers.delete(sid)
  }
}

async function sendMcp(question: string, session: AiSession) {
  const sid = session.id
  const history = session.messages
    .filter(m => m.role === 'user' || m.role === 'assistant')
    .slice(-4)

  // Fetch fresh tool list and convert to native OpenAI format
  const tools = await getAllToolsFlat()
  if (tools.length === 0) {
    await sendChat(question, '', session)
    return
  }

  const aiTools: AiToolDefinition[] = tools.map(t => ({
    type: 'function',
    function: {
      name: t.tool.name,
      description: t.tool.description || '',
      parameters: t.tool.inputSchema || { type: 'object', properties: {} },
    },
  }))

  const systemRole = resolveSystemRole(aiConfig.value)
  const systemPrompt = 'You are a helpful AI assistant with access to MCP tools. Use them when needed to answer the user\'s question. Always respond in the same language as the user.'

  const allToolCalls: ToolCallInfo[] = []
  let accumulatedContent = ''
  let conversation: AiChatMessage[] = [
    { role: systemRole, content: systemPrompt },
    ...history.map(m => ({ role: m.role as 'user' | 'assistant', content: m.content })),
    { role: 'user', content: question },
  ]

  const msgIndex = session.messages.length
  session.messages.push({ role: 'assistant', content: '', streaming: true })

  const ac = new AbortController()
  sessionAbortControllers.set(sid, ac)

  try {
    // Only run a final streaming pass when the loop exits with tool_calls
    // still pending synthesis. When the model returns content without tool_calls,
    // that content IS the final answer — a second stream would duplicate it.
    let needsFinalStream = false
    for (let round = 0; round < 5; round++) {
      if (ac.signal.aborted) break
      const result = await callAiChatWithTools(aiConfig.value, conversation, aiTools)
      addUsage(result.usage)

      if (result.content) {
        accumulatedContent += (accumulatedContent ? '\n\n' : '') + result.content
        session.messages[msgIndex].content = accumulatedContent
        scrollToBottom()
      }

      if (!result.toolCalls || result.toolCalls.length === 0) {
        needsFinalStream = false
        break
      }

      conversation.push({
        role: 'assistant',
        content: result.content || null,
        tool_calls: result.toolCalls,
      })

      for (const tc of result.toolCalls) {
        if (ac.signal.aborted) break
        const toolName = tc.function.name
        let args: Record<string, unknown> = {}
        try { args = JSON.parse(tc.function.arguments) } catch {}
        const desc = tools.find(t => t.tool.name === toolName)
        if (!desc) continue
        const server = servers.value.find(s => s.id === desc.serverId && s.enabled)
        if (!server) continue

        allToolCalls.push({ toolName, serverName: desc.serverName })
        let toolResult: string
        try {
          const res = await mcpCallTool(server, toolName, args)
          toolResult = JSON.stringify(res?.content || res)
        } catch (e: any) {
          toolResult = `Error: ${e.message || e}`
        }

        conversation.push({ role: 'tool', tool_call_id: tc.id, content: toolResult })
      }
      needsFinalStream = true
    }

    if (needsFinalStream && !ac.signal.aborted) {
      if (accumulatedContent) accumulatedContent += '\n\n'
      session.messages[msgIndex].content = accumulatedContent
      let frameRequested = false
      const streamResult = await callChatApiStream(aiConfig.value, conversation, (delta) => {
        accumulatedContent += delta
        session.messages[msgIndex].content = accumulatedContent
        if (!frameRequested) {
          frameRequested = true
          requestAnimationFrame(() => { frameRequested = false; scrollToBottom() })
        }
      }, ac.signal)
      addUsage(streamResult.usage)
    }

    session.messages[msgIndex].content = accumulatedContent || '(no response)'
    session.messages[msgIndex].toolCalls = allToolCalls.length > 0 ? allToolCalls : undefined
  } finally {
    if (session.messages[msgIndex]) session.messages[msgIndex].streaming = false
    sessionAbortControllers.delete(sid)
  }
}

function scrollToBottom() {
  nextTick(() => {
    messagesRef.value?.scrollTo({ top: messagesRef.value.scrollHeight, behavior: 'smooth' })
  })
}

function goSettings() { router.push('/settings') }

function onMessagesClick(e: MouseEvent) {
  const target = e.target as HTMLElement
  // Handle note links
  const link = target.closest('[data-note-link]') as HTMLElement | null
  if (link) {
    e.preventDefault()
    const noteId = link.getAttribute('data-note-link')
    const href = link.getAttribute('href') || ''
    const headingMatch = href.match(/#([^#]+)$/)
    if (noteId) {
      router.push({ path: '/notes-space', query: { noteId, heading: headingMatch?.[1] ? decodeURIComponent(headingMatch[1]) : undefined } })
    }
    return
  }
  // Handle code block copy buttons
  const copyBtn = target.closest('[data-copy-code]') as HTMLElement | null
  if (copyBtn) {
    e.preventDefault()
    const code = copyBtn.getAttribute('data-copy-code') || ''
    navigator.clipboard.writeText(code).then(() => showToast('已复制', true)).catch(() => {})
  }
}

function copyMessage(content: string) {
  navigator.clipboard.writeText(content).then(() => showToast('已复制', true)).catch(() => {})
}

function canRegenerate(index: number): boolean {
  if (!activeSession.value) return false
  const msgs = activeSession.value.messages
  if (msgs[index]?.role !== 'assistant') return false
  if (index !== msgs.length - 1) return false
  if (sessionLoading.get(activeSessionId.value)) return false
  return true
}

async function regenerate(index: number) {
  if (!activeSession.value || !canRegenerate(index)) return
  const session = activeSession.value
  // Find the user message preceding this assistant message
  let userMsgIndex = index - 1
  while (userMsgIndex >= 0 && session.messages[userMsgIndex].role !== 'user') userMsgIndex--
  if (userMsgIndex < 0) return

  const userMsg = session.messages[userMsgIndex]
  // Remove assistant message(s) after the user message
  session.messages.splice(index)

  const sid = session.id
  setLoading(sid, true)
  clearError(sid)

  try {
    const content = userMsg.fileContent
      ? `[File: ${userMsg.fileName}]\n${userMsg.fileContent}${userMsg.content ? '\n\n' + userMsg.content : ''}`
      : userMsg.content
    if (mode.value === 'chat') {
      await sendChat(content, userMsg.image || '', session)
    } else if (mode.value === 'notes') {
      await sendNotes(content, userMsg.image || '', session)
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
    // 只加载元数据 + plainText，避免拉整张笔记表的 HTML/JSON 大字段
    // （慢查询日志显示 loadNotes 在 90 条时要 1.7s，会独占 SQLite 写线程）
    notes.value = await loadNoteList()
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
  // 每次激活都重读 AI 配置 —— 用户可能刚从设置页保存了 endpoint / apiKey。
  // loadAiConfig 只读 app_settings 单行 KV，耗时可忽略。
  loadAiConfig().then(c => { aiConfig.value = c; historyLoaded.value = true }).catch(() => {})
  // 后台异步刷新笔记 / MCP。不 await：切换回 AI 页立即显示会话；数据回来后再无缝更新。
  loadAllNotes(true).catch(() => {})
  loadServers().catch(() => {})
})

// 未配置蒙版上的手动刷新（自动刷新失败时的兜底）
const refreshingConfig = ref(false)
async function refreshConfig() {
  if (refreshingConfig.value) return
  refreshingConfig.value = true
  try {
    const fresh = await loadAiConfig()
    aiConfig.value = fresh
    // 立即用 isAiConfigured 判断新配置是否完整并给出反馈，
    // 避免"点了没反应"的错觉 —— 常见是三个字段中有一个还没填。
    if (isAiConfigured(fresh)) {
      showToast(t('cloudSync.success') || 'Loaded', true)
    } else {
      const missing: string[] = []
      if (!fresh.apiKey.trim()) missing.push('API Key')
      if (!fresh.endpoint.trim()) missing.push('Endpoint')
      if (!fresh.model.trim()) missing.push('Model')
      showToast(`${t('ai.noConfig')}: ${missing.join(' / ')}`, false)
    }
  } catch (e: any) {
    showToast(e?.message || 'Load failed', false)
  } finally {
    refreshingConfig.value = false
  }
}

onUnmounted(() => {
  if (toastTimer) clearTimeout(toastTimer)
  if (saveTimer) clearTimeout(saveTimer)
  // Abort any in-flight AI requests
  for (const ac of sessionAbortControllers.values()) ac.abort()
  sessionAbortControllers.clear()
  // Flush any pending token usage before unmount
  flushUsage()
  document.removeEventListener('paste', onGlobalPaste)
  document.removeEventListener('click', onDocumentClick)
})
</script>

<style scoped>
/* AI 会话侧栏条目：默认灰字，hover 墨色叠层可见；活跃态浅蓝紫底 + 左侧朱砂条 */
.ai-session-item {
  color: rgba(28, 27, 31, 0.68);
  transition: background-color .16s ease, color .16s ease;
}
.ai-session-item:hover {
  background-color: rgba(28, 27, 31, 0.07);
  color: #1C1B1F;
}
.ai-session-item.is-active {
  background-color: rgba(30, 58, 95, 0.10);
  color: #1E3A5F;
  font-weight: 500;
  box-shadow: inset 3px 0 0 0 #C24E3A;
}
:global(html.dark) .ai-session-item {
  color: rgba(232, 227, 214, 0.72);
}
:global(html.dark) .ai-session-item:hover {
  background-color: rgba(232, 227, 214, 0.09);
  color: #FFF8EA;
}
:global(html.dark) .ai-session-item.is-active {
  background-color: rgba(232, 141, 108, 0.16);
  color: #FFF8EA;
  box-shadow: inset 3px 0 0 0 #E8734F;
}

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

/* Markdown tables rendered in chat messages */
:deep(.ai-table-wrap) {
  overflow-x: auto;
  max-width: 100%;
}
:deep(.ai-table) {
  border-collapse: collapse;
  width: 100%;
  margin: 8px 0;
  font-size: 12px;
  line-height: 1.5;
}
:deep(.ai-table th),
:deep(.ai-table td) {
  border: 1px solid rgba(139, 92, 246, 0.25);
  padding: 6px 10px;
  text-align: left;
  vertical-align: top;
}
:deep(.ai-table th) {
  background: rgba(139, 92, 246, 0.08);
  font-weight: 600;
  color: #1a1c1d;
}
:deep(.ai-table td) {
  color: #424656;
}
:deep(.ai-table tr:nth-child(even) td) {
  background: rgba(0, 0, 0, 0.02);
}

/* AI Markdown content styles */
:deep(.ai-markdown) {
  word-break: break-word;
}
:deep(.ai-markdown p) {
  margin: 0.4em 0;
}
:deep(.ai-markdown p:first-child) {
  margin-top: 0;
}
:deep(.ai-markdown p:last-child) {
  margin-bottom: 0;
}
:deep(.ai-markdown h1),
:deep(.ai-markdown h2),
:deep(.ai-markdown h3),
:deep(.ai-markdown h4) {
  margin: 0.8em 0 0.4em;
  font-weight: 600;
  line-height: 1.3;
}
:deep(.ai-markdown h1) { font-size: 1.3em; }
:deep(.ai-markdown h2) { font-size: 1.15em; }
:deep(.ai-markdown h3) { font-size: 1.05em; }
:deep(.ai-markdown h4) { font-size: 1em; }
:deep(.ai-markdown ul),
:deep(.ai-markdown ol) {
  margin: 0.4em 0;
  padding-left: 1.5em;
}
:deep(.ai-markdown li) {
  margin: 0.2em 0;
}
:deep(.ai-markdown blockquote) {
  margin: 0.5em 0;
  padding: 0.3em 0.8em;
  border-left: 3px solid rgba(139, 92, 246, 0.4);
  background: rgba(139, 92, 246, 0.04);
  border-radius: 0 6px 6px 0;
}
:deep(.ai-markdown hr) {
  border: none;
  border-top: 1px solid rgba(0, 0, 0, 0.1);
  margin: 0.8em 0;
}
:deep(.ai-markdown strong) {
  font-weight: 600;
}
:deep(.ai-markdown a) {
  color: #7c3aed;
  text-decoration: underline;
}
:deep(.ai-markdown a:hover) {
  opacity: 0.8;
}

/* Inline code */
:deep(.ai-inline-code) {
  background: rgba(139, 92, 246, 0.08);
  border: 1px solid rgba(139, 92, 246, 0.15);
  border-radius: 4px;
  padding: 0.1em 0.35em;
  font-size: 0.9em;
  font-family: 'Cascadia Code', 'Fira Code', 'JetBrains Mono', monospace;
}

/* Code blocks */
:deep(.ai-code-block) {
  margin: 0.6em 0;
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid rgba(0, 0, 0, 0.08);
  background: #1e1e2e;
}
:deep(.ai-code-header) {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 12px;
  background: rgba(0, 0, 0, 0.3);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}
:deep(.ai-code-lang) {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.5);
  font-family: inherit;
}
:deep(.ai-code-copy) {
  display: flex;
  align-items: center;
  gap: 3px;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.5);
  background: transparent;
  border: none;
  cursor: pointer;
  transition: all 0.15s;
}
:deep(.ai-code-copy:hover) {
  color: rgba(255, 255, 255, 0.9);
  background: rgba(255, 255, 255, 0.1);
}
:deep(.ai-code-block pre) {
  margin: 0;
  padding: 12px 14px;
  overflow-x: auto;
  font-size: 12px;
  line-height: 1.6;
}
:deep(.ai-code-block code) {
  font-family: 'Cascadia Code', 'Fira Code', 'JetBrains Mono', monospace;
  color: #cdd6f4;
}

/* Streaming cursor */
:deep(.ai-cursor) {
  display: inline-block;
  width: 2px;
  height: 1em;
  background: #7c3aed;
  margin-left: 1px;
  vertical-align: text-bottom;
  animation: ai-blink 0.8s infinite;
}
@keyframes ai-blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

/* highlight.js token colors (Catppuccin Mocha inspired) */
:deep(.hljs-keyword) { color: #cba6f7; }
:deep(.hljs-string) { color: #a6e3a1; }
:deep(.hljs-number) { color: #fab387; }
:deep(.hljs-comment) { color: #6c7086; font-style: italic; }
:deep(.hljs-function) { color: #89b4fa; }
:deep(.hljs-title) { color: #89b4fa; }
:deep(.hljs-params) { color: #f2cdcd; }
:deep(.hljs-built_in) { color: #f9e2af; }
:deep(.hljs-literal) { color: #fab387; }
:deep(.hljs-type) { color: #f9e2af; }
:deep(.hljs-attr) { color: #89dceb; }
:deep(.hljs-attribute) { color: #89dceb; }
:deep(.hljs-selector-tag) { color: #cba6f7; }
:deep(.hljs-selector-class) { color: #89b4fa; }
:deep(.hljs-selector-id) { color: #fab387; }
:deep(.hljs-variable) { color: #f5c2e7; }
:deep(.hljs-meta) { color: #f9e2af; }
:deep(.hljs-tag) { color: #89b4fa; }
:deep(.hljs-name) { color: #cba6f7; }
:deep(.hljs-property) { color: #89dceb; }
:deep(.hljs-punctuation) { color: #9399b2; }
:deep(.hljs-operator) { color: #89dceb; }
:deep(.hljs-regexp) { color: #f5c2e7; }
:deep(.hljs-deletion) { color: #f38ba8; }
:deep(.hljs-addition) { color: #a6e3a1; }
</style>