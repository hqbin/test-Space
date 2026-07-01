<template>
  <div class="flex flex-col flex-1 min-h-0 -mx-margin-page pb-2 box-border select-none">
    <!-- Toolbar -->
    <div class="flex items-center gap-3 mb-2 flex-shrink-0 ml-3">
      <!-- Type dropdown -->
      <div class="relative" ref="typeDropdownRef">
        <button class="glass-button px-3 py-1.5 rounded-full font-caption text-caption font-normal flex items-center gap-1.5 min-w-[80px] select-none" @click="typeDropdownOpen = !typeDropdownOpen">
          <span class="material-symbols-outlined text-[16px]">code</span>
          <span class="text-[12px] font-mono uppercase">{{ currentTypeLabel }}</span>
          <span class="material-symbols-outlined text-[16px] transition-transform" :class="typeDropdownOpen ? 'rotate-180' : ''">expand_more</span>
        </button>
        <Transition name="dropdown">
          <div v-if="typeDropdownOpen" class="absolute top-full left-0 mt-1.5 w-[140px] rounded-xl border border-white/10 shadow-2xl overflow-hidden z-50 glass-panel">
            <button v-for="t in typeOptions" :key="t.value"
              class="w-full flex items-center gap-2 px-3 py-2 text-[13px] font-mono uppercase transition-colors select-none"
              :class="globalType === t.value ? 'bg-white/15 text-on-surface' : 'text-on-surface-variant hover:bg-white/8 hover:text-on-surface'"
              @click="switchType(t.value)">
              <span class="material-symbols-outlined text-[16px]" :class="globalType === t.value ? 'text-green-400' : 'text-on-surface-variant/40'">check</span>
              {{ t.label }}
            </button>
          </div>
        </Transition>
      </div>
      <button class="glass-button px-3 py-1.5 rounded-full font-caption text-caption font-normal flex items-center gap-1.5 select-none" @click="newScript">
        <span class="material-symbols-outlined text-[16px]">add</span>
        {{ t("scripts.new") }}
      </button>
      <button class="glass-button px-3 py-1.5 rounded-full font-caption text-caption font-normal flex items-center gap-1.5 select-none" @click="openLocalFile">
        <span class="material-symbols-outlined text-[16px]">folder_open</span>
        {{ t("scripts.open") }}
      </button>
      <button v-if="currentScript" class="glass-button px-3 py-1.5 rounded-full font-caption text-caption font-normal flex items-center gap-1.5 select-none" @click="saveCurrentScript">
        <span class="material-symbols-outlined text-[16px]">save</span>
        {{ t("scripts.save") }}
      </button>
      <button v-if="currentScript" class="glass-button px-3 py-1.5 rounded-full font-caption text-caption font-normal flex items-center gap-1.5 select-none" @click="exportToFile">
        <span class="material-symbols-outlined text-[16px]">file_upload</span>
        {{ t("scripts.export") }}
      </button>
    </div>

    <div class="flex-1 flex gap-4 min-h-0">
      <!-- Script library sidebar -->
      <div class="w-56 flex-shrink-0 ml-3 rounded-xl bg-white/10 backdrop-blur-[60px] border border-white/50 shadow-lg flex flex-col overflow-hidden">
        <div class="px-3 py-2 border-b border-white/10 flex items-center gap-2">
          <span class="text-[13px] text-on-surface font-medium flex-shrink-0">{{ t("nav.scripts") }}</span>
          <div class="flex-1 relative">
            <input v-model="searchQuery" class="w-full bg-white/5 border border-white/10 rounded-lg px-2.5 py-1 text-[12px] text-on-surface placeholder-on-surface-variant/40 focus:outline-none focus:border-white/20 select-text" :placeholder="t('scripts.search')" />
            <span v-if="searchQuery" class="absolute right-1.5 top-1/2 -translate-y-1/2 text-on-surface-variant/40 cursor-pointer hover:text-on-surface-variant/70" @click="searchQuery = ''">
              <span class="material-symbols-outlined text-[14px]">close</span>
            </span>
          </div>
          <span class="text-[11px] text-on-surface-variant/40 flex-shrink-0">{{ filteredScripts.length }}</span>
        </div>
        <div class="px-3 py-1.5 border-b border-white/10 flex items-center gap-2">
          <button class="flex items-center gap-0.5 text-[11px] text-on-surface-variant/50 hover:text-on-surface transition-colors select-none" @click="toggleSort">
            <span class="material-symbols-outlined text-[13px]">{{ sortAsc ? 'arrow_upward' : 'arrow_downward' }}</span>
            {{ sortLabel }}
          </button>
        </div>
        <div ref="listContainerRef" class="flex-1 overflow-hidden">
          <div v-if="filteredScripts.length === 0" class="p-4 text-[12px] text-on-surface-variant/40 text-center">
            {{ t("scripts.noScripts") }}
          </div>
          <div v-for="s in pagedScripts" :key="s.id"
            class="flex items-center gap-2 px-3 py-2 cursor-pointer transition-colors text-[13px] border-b border-white/[2%]"
            :class="currentScript?.id === s.id ? 'bg-white/15 text-on-surface font-medium' : 'text-on-surface-variant hover:bg-white/5 hover:text-on-surface'"
            @click="loadScript(s.id)">
            <span class="material-symbols-outlined text-[16px] text-on-surface-variant/50 flex-shrink-0">code</span>
            <span class="truncate flex-1">{{ s.name }}</span>
            <button class="p-0.5 rounded hover:bg-red-500/20 text-on-surface-variant/20 hover:text-red-400 transition-colors flex-shrink-0 select-none" @click.stop="confirmDelete(s)">
              <span class="material-symbols-outlined text-[14px]">close</span>
            </button>
          </div>
        </div>
        <div v-if="totalPages > 1" class="px-3 py-1.5 border-t border-white/10 flex items-center justify-center gap-2 flex-shrink-0">
          <button class="text-[11px] text-on-surface-variant/50 hover:text-on-surface disabled:opacity-30 disabled:cursor-default select-none" :disabled="currentPage <= 1" @click="currentPage--">
            <span class="material-symbols-outlined text-[14px]">chevron_left</span>
          </button>
          <span class="text-[11px] text-on-surface-variant/50">{{ currentPage }} / {{ totalPages }}</span>
          <button class="text-[11px] text-on-surface-variant/50 hover:text-on-surface disabled:opacity-30 disabled:cursor-default select-none" :disabled="currentPage >= totalPages" @click="currentPage++">
            <span class="material-symbols-outlined text-[14px]">chevron_right</span>
          </button>
        </div>
      </div>

      <!-- Main content area -->
      <div class="flex-1 flex flex-col min-h-0 pr-3">
        <!-- Editor area -->
        <div class="flex-[3] min-h-0 flex flex-col">
          <!-- Script header bar -->
          <div v-if="currentScript" class="flex items-center gap-3 px-4 py-2 flex-shrink-0 flex-wrap">
            <input v-model="editingName" class="bg-transparent border-b border-transparent focus:border-secondary/40 focus:outline-none text-[20px] font-bold text-on-surface px-1 -ml-1 min-w-0 max-w-[60%] truncate select-text" :placeholder="t('scripts.namePlaceholder')" />
            <div class="flex-1"></div>
            <div class="flex items-center gap-1 flex-wrap justify-end min-w-0">
              <div v-for="(snp, idx) in snippets" :key="snp.label" class="relative"
                @mouseenter="(e: MouseEvent) => showSnippetTip(idx, e)" @mouseleave="hideSnippetTip">
                <button class="px-2 py-0.5 rounded text-[11px] bg-white/10 hover:bg-white/20 text-on-surface-variant/70 hover:text-on-surface transition-colors whitespace-nowrap select-none" @click="insertSnippet(snp.code)">
                  {{ snp.label }}
                </button>
              </div>
            </div>
          </div>
          <!-- Editor -->
          <div v-if="currentScript" class="flex-1 min-h-0 rounded-2xl overflow-hidden border border-white/10 flex flex-col">
            <div class="flex items-center gap-3 px-4 py-2 bg-[#1a1c1d] border-b border-white/5 flex-shrink-0">
              <div class="flex gap-1.5">
                <span class="w-3 h-3 rounded-full bg-[#ff5f56]"></span>
                <span class="w-3 h-3 rounded-full bg-[#ffbd2e]"></span>
                <span class="w-3 h-3 rounded-full bg-[#27c93f]"></span>
              </div>
              <div class="flex-1"></div>
              <button class="flex items-center gap-1 px-3 py-1 rounded-full text-[12px] bg-green-500/20 hover:bg-green-500/30 text-green-400 transition-colors select-none" @click="runCurrentScript">
                <span class="material-symbols-outlined text-[15px]">play_arrow</span>
                {{ t("scripts.run") }}
              </button>
            </div>
            <div class="flex-1 flex min-h-0" style="background: #0d0d1a;">
              <div ref="lineNumbersRef" class="flex-shrink-0 text-right px-3 font-mono text-[#4a5568] select-none overflow-hidden" style="background: #0d0d1a; min-width: 36px; font-size: 13px; line-height: 21px; padding-top: 12px; padding-bottom: 48px;">
                <div v-for="n in lineCount" :key="n" style="height: 21px; line-height: 21px;">{{ n }}</div>
              </div>
              <div class="flex-1 relative min-h-0">
                <pre ref="highlightRef" class="editor-highlight absolute inset-0 pointer-events-none select-none" style="background: #0d0d1a; overflow: auto; tab-size: 2; white-space: pre; scrollbar-width: none; -ms-overflow-style: none; font-family: 'Consolas', 'Monaco', 'Courier New', monospace; font-size: 13px; line-height: 21px; padding: 12px 12px 48px 12px; margin: 0; color: #e4e5e7;" aria-hidden="true" v-html="highlightedCode"></pre>
                <textarea ref="editorRef" v-model="editingContent"
                  class="editor-textarea absolute inset-0 w-full h-full resize-none outline-none border-none select-text"
                  style="background: transparent; tab-size: 2; -webkit-text-fill-color: transparent; color: transparent; caret-color: white; overflow: auto; scrollbar-width: none; -ms-overflow-style: none; white-space: pre; font-family: 'Consolas', 'Monaco', 'Courier New', monospace; font-size: 13px; line-height: 21px; padding: 12px 12px 48px 12px;"
                  spellcheck="false"
                  @keydown="onEditorKeydown"
                  @scroll="syncScroll">
                </textarea>
              </div>
            </div>
          </div>
          <!-- Empty state -->
          <div v-else class="flex-1 min-h-0 flex items-center justify-center rounded-2xl border border-white/10" style="background: #0d0d1a;">
            <div class="text-center text-[#4a5568]">
              <span class="material-symbols-outlined text-5xl mb-3 block">code</span>
              <p class="text-[14px]">{{ t("scripts.placeholder") }}</p>
            </div>
          </div>
        </div>

        <!-- Console area -->
        <div class="flex-[2] min-h-0 mt-2 rounded-2xl overflow-hidden border border-white/10 flex flex-col">
          <div class="flex items-center justify-between px-4 py-2 bg-[#1a1c1d] border-b border-white/5 flex-shrink-0">
            <div class="flex items-center gap-3">
              <span class="material-symbols-outlined text-[14px] text-[#6b7280]">terminal</span>
              <span class="text-[12px] font-medium text-[#9ca3af]">{{ t("scripts.console") }}</span>
              <span v-if="activeTab?.status === 'running'" class="flex items-center gap-1.5 text-[11px] text-green-400">
                <span class="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse"></span>
                {{ t("scripts.running") }} {{ activeTab.elapsed }}
              </span>
              <span v-else-if="activeTab?.status === 'success'" class="text-[11px] text-green-500">Exit {{ activeTab.exitCode }}</span>
              <span v-else-if="activeTab?.status === 'error'" class="text-[11px] text-red-400">Exit {{ activeTab.exitCode }}</span>
              <span v-else-if="activeTab?.status === 'killed'" class="text-[11px] text-orange-400">{{ t("scripts.terminated") }}</span>
            </div>
            <div class="flex items-center gap-2">
              <button v-if="activeTab?.status === 'running'" class="glass-button px-2.5 py-1 rounded-full text-[11px] flex items-center gap-1 text-red-400 select-none" @click="killScript(activeTab.id)">
                <span class="material-symbols-outlined text-[13px]">stop</span>
                {{ t("scripts.stop") }}
              </button>
              <button class="glass-button px-2.5 py-1 rounded-full text-[11px] flex items-center gap-1 select-none" @click="activeTabId && clearTabOutput(activeTabId)">
                <span class="material-symbols-outlined text-[13px]">delete</span>
                {{ t("scripts.clear") }}
              </button>
            </div>
          </div>
          <div ref="outputContainer" class="flex-1 overflow-y-auto font-mono text-[13px] leading-relaxed px-4 py-3 custom-scrollbar rounded-b-2xl" style="background: #0d0d1a;">
            <div v-if="!activeTab || activeTabOutput.length === 0" class="text-[#6b7280]">
              <span class="text-green-400/60">$</span> {{ t("scripts.outputHint") }}
            </div>
            <div v-for="(line, idx) in activeTabOutput" :key="idx" class="whitespace-pre-wrap">
              <span v-if="line.stream === 'stderr'" class="text-red-400">{{ line.text }}</span>
              <span v-else class="text-[#e4e5e7]">{{ line.text }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Toast -->
    <div v-if="toast" class="fixed bottom-6 left-1/2 -translate-x-1/2 z-[99999] px-5 py-2.5 rounded-full text-[13px] font-semibold shadow-2xl border pointer-events-none transition-all"
      :class="toast.ok ? 'bg-green-700 text-white border-green-500' : 'bg-red-700 text-white border-red-500'">
      {{ toast.msg }}
    </div>

    <!-- Snippet tooltip -->
    <Teleport to="body">
      <div v-if="activeTip !== null && tipSnippet" class="fixed z-[10000] px-3 py-2 rounded-lg text-[12px] text-white/90 max-w-[280px] max-h-[40vh] overflow-y-auto pointer-events-none shadow-xl border border-white/10"
        :style="tipStyle" style="background: rgba(20,22,28,0.95); backdrop-filter: blur(12px);">
        <div class="font-medium text-green-400 mb-1 font-mono text-[11px]">{{ tipSnippet.label }}</div>
        <div class="text-white/50 leading-relaxed">{{ tipSnippet.desc }}</div>
      </div>
    </Teleport>

    <!-- Delete confirmation modal -->
    <Teleport to="body">
      <div v-if="deleteTarget" class="fixed inset-0 z-[9999] flex items-center justify-center bg-black/40" @click.self="deleteTarget = null">
        <div class="rounded-2xl p-6 w-[340px] border border-white/10 shadow-2xl" style="background: rgba(30,32,40,0.95); backdrop-filter: blur(20px);">
          <div class="text-[15px] font-medium text-white mb-2">{{ t("scripts.deleteTitle") }}</div>
          <div class="text-[13px] text-white/50 mb-5">{{ t("scripts.deleteDesc", { name: deleteTarget.name }) }}</div>
          <div class="flex justify-end gap-2">
            <button class="px-4 py-1.5 rounded-full text-[13px] text-white/60 border border-white/10 hover:bg-white/10 transition-colors select-none" @click="deleteTarget = null">{{ t("scripts.deleteCancel") }}</button>
            <button class="px-4 py-1.5 rounded-full text-[13px] bg-red-500/20 text-red-400 hover:bg-red-500/30 transition-colors select-none" @click="doDelete">{{ t("scripts.deleteConfirm") }}</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Type switch confirm modal -->
    <Teleport to="body">
      <div v-if="pendingTypeSwitch" class="fixed inset-0 z-[9999] flex items-center justify-center bg-black/40" @click.self="pendingTypeSwitch = null">
        <div class="rounded-2xl p-6 w-[360px] border border-white/10 shadow-2xl" style="background: rgba(30,32,40,0.95); backdrop-filter: blur(20px);">
          <div class="text-[15px] font-medium text-white mb-2">{{ t("scripts.typeTitle") }}</div>
          <div class="text-[13px] text-white/50 mb-5">{{ t("scripts.typeDesc", { name: editingName || 'untitled' }) }}</div>
          <div class="flex justify-end gap-2">
            <button class="px-4 py-1.5 rounded-full text-[13px] text-white/60 border border-white/10 hover:bg-white/10 transition-colors select-none" @click="pendingTypeSwitch = null">{{ t("scripts.typeCancel") }}</button>
            <button class="px-4 py-1.5 rounded-full text-[13px] bg-white/15 text-white hover:bg-white/25 transition-colors select-none" @click="confirmTypeSwitch">{{ t("scripts.typeConfirm") }}</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted, onUnmounted, watch } from "vue";
import { invoke } from "@tauri-apps/api/core";
import * as db from "@/services/database";
import { useScriptRunner } from "@/composables/useScriptRunner";
import { useI18n } from "@/composables/useI18n";
import { save } from "@tauri-apps/plugin-dialog";

const { t } = useI18n();

const {
  tabs, activeTabId, activeTab, activeTabOutput,
  addTab, clearTabOutput, killScript, setup: setupRunner, setScrollContainer, destroy,
} = useScriptRunner();

const scripts = ref<db.ScriptItem[]>([]);
const currentScript = ref<db.ScriptItem | null>(null);
const editingName = ref("");
const editingType = ref("bat");
const editingContent = ref("");
const localFilePath = ref<string | null>(null); // 本地打开文件的原始路径，用于设置工作目录
const workingDir = ref<string>(""); // 用户手动指定的工作目录
const editorRef = ref<HTMLTextAreaElement | null>(null);
const highlightRef = ref<HTMLElement | null>(null);
const lineNumbersRef = ref<HTMLElement | null>(null);
const outputContainer = ref<HTMLElement | null>(null);

// ── Dynamic pagination ────────────────────────────────
const listContainerRef = ref<HTMLElement | null>(null);
const pageSize = ref(10);
const ITEM_HEIGHT = 36;
const PAGINATOR_H = 32;

const currentPage = ref(1);

const totalPages = computed(() => {
  const n = Math.ceil(filteredScripts.value.length / pageSize.value) || 1;
  return n;
});

function updatePageSize() {
  const el = listContainerRef.value;
  if (!el) return;
  const h = el.clientHeight - PAGINATOR_H;
  pageSize.value = Math.max(1, Math.floor(h / ITEM_HEIGHT));
}

const pagedScripts = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value;
  return filteredScripts.value.slice(start, start + pageSize.value);
});

// ── Type dropdown ─────────────────────────────────
const globalType = ref("bat");
const typeDropdownOpen = ref(false);
const typeDropdownRef = ref<HTMLElement | null>(null);

const typeOptions = [
  { value: "bat", label: "BAT" },
  { value: "py", label: "Python" },
];

const currentTypeLabel = computed(() => typeOptions.find(t => t.value === globalType.value)?.label || "BAT");

const pendingTypeSwitch = ref<string | null>(null);

function switchType(newType: string) {
  typeDropdownOpen.value = false;
  if (newType === globalType.value) return;
  if (currentScript.value && editingContent.value.trim()) {
    pendingTypeSwitch.value = newType;
  } else {
    globalType.value = newType;
    localStorage.setItem('script-space:type', newType);
    resetEditor();
  }
}

function confirmTypeSwitch() {
  if (pendingTypeSwitch.value) {
    globalType.value = pendingTypeSwitch.value;
    localStorage.setItem('script-space:type', pendingTypeSwitch.value);
    resetEditor();
  }
  pendingTypeSwitch.value = null;
}

function resetEditor() {
  currentScript.value = null;
  editingName.value = "";
  editingContent.value = "";
  localFilePath.value = null;
}

// ── Search / Sort / Pagination ─────────────────────────
const searchQuery = ref("");
const sortMode = ref<"name" | "created">("name");
const sortAsc = ref(true);

const sortLabel = computed(() => sortMode.value === "name" ? t("scripts.sortName") : t("scripts.sortTime"));

const filteredScripts = computed(() => {
  let list = scripts.value.filter(s => s.type === globalType.value);
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.trim().toLowerCase();
    list = list.filter(s => s.name.toLowerCase().includes(q));
  }
  list.sort((a, b) => {
    const cmp = sortMode.value === "name"
      ? a.name.localeCompare(b.name)
      : (a.createdAt || "").localeCompare(b.createdAt || "");
    return sortAsc.value ? cmp : -cmp;
  });
  return list;
});
watch(totalPages, (n) => {
  if (currentPage.value > n) currentPage.value = n;
});

function toggleSort() {
  if (sortMode.value === "name") {
    sortMode.value = "created";
  } else if (sortAsc.value) {
    sortAsc.value = false;
  } else {
    sortMode.value = "name";
    sortAsc.value = true;
  }
}

// ── Delete ─────────────────────────
const deleteTarget = ref<db.ScriptItem | null>(null);

function confirmDelete(s: db.ScriptItem) {
  deleteTarget.value = s;
}

async function doDelete() {
  if (!deleteTarget.value) return;
  const id = deleteTarget.value.id;
  try {
    await db.deleteScript(id);
    if (currentScript.value?.id === id) {
      currentScript.value = null;
      editingName.value = "";
      editingContent.value = "";
    }
    deleteTarget.value = null;
    await loadScriptList();
  } catch (e: any) {
    console.error("[ScriptSpace] delete failed:", e);
    showToast(t("scripts.saveFail") + ": " + (e?.message || e), false);
    deleteTarget.value = null;
  }
}

// ── Toast feedback ─────────────────────────────────
const toast = ref<{ msg: string; ok: boolean } | null>(null);
let toastTimer: ReturnType<typeof setTimeout> | null = null;

function showToast(msg: string, ok: boolean) {
  if (toastTimer) clearTimeout(toastTimer);
  toast.value = { msg, ok };
  toastTimer = setTimeout(() => { toast.value = null; }, 2000);
}

// ── Snippet tooltip ─────────────────────────────────
const activeTip = ref<number | null>(null);
const tipStyle = ref<Record<string, string>>({});
const tipSnippet = ref<{ label: string; desc: string } | null>(null);
let tipTimer: ReturnType<typeof setTimeout> | null = null;

function showSnippetTip(idx: number, e: MouseEvent) {
  const snippetsArr = snippets.value;
  const el = e.currentTarget as HTMLElement;
  tipTimer = setTimeout(() => {
    activeTip.value = idx;
    tipSnippet.value = snippetsArr[idx] || null;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const tipH = 80;
    const above = rect.top >= tipH + 8;
    tipStyle.value = above
      ? { left: `${rect.left}px`, top: `${rect.top - 8}px`, transform: 'translateY(-100%)' }
      : { left: `${rect.left}px`, top: `${rect.bottom + 8}px` };
  }, 500);
}

function hideSnippetTip() {
  if (tipTimer) { clearTimeout(tipTimer); tipTimer = null; }
  activeTip.value = null;
  tipSnippet.value = null;
}

const lineCount = computed(() => editingContent.value.split("\n").length);

const snippets = computed(() => {
  const t = editingType.value;
  if (t === "bat") return BAT_SNIPPETS.value;
  if (t === "py") return PY_SNIPPETS.value;
  return [];
});

// ── Syntax highlighting ──────────────────────────────────────

function highlightBat(code: string): string {
  let html = escHtml(code);
  html = html.replace(/(\s*::.*|^\s*rem\b.*)/gim, '<span style="color:#6b7280">$1</span>');
  html = html.replace(/(%[~]?[a-zA-Z0-9_-]+%)/g, '<span style="color:#f59e0b">$1</span>');
  html = html.replace(/^(:\w+)/gm, '<span style="color:#a78bfa;font-weight:bold">$1</span>');
  html = html.replace(/\b(echo|goto|call|set|if|else|for|do|in|exist|not|defined|errorlevel|exit|pause|timeout|ping|mkdir|rmdir|del|copy|move|ren|type|findstr|chcp|pushd|popd|choice|start|taskkill|reg|sc|net|cmd|powershell)\b/gi, '<span style="color:#60a5fa">$1</span>');
  return html;
}

function highlightPy(code: string): string {
  const html = escHtml(code);
  const combined = /(#.*)|("""[\s\S]*?"""|'''[\s\S]*?'''|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')|(@\w[\w.]*)|\b(def|class|if|elif|else|for|while|try|except|finally|import|from|return|yield|raise|with|as|pass|break|continue|and|or|not|in|is|lambda|global|nonlocal|assert|del|True|False|None|print|self|async|await)\b|\b(\d+\.?\d*)\b/g;
  return html.replace(combined, (match, comment, string, decorator, keyword, number) => {
    if (comment) return `<span style="color:#6b7280">${comment}</span>`;
    if (string) return `<span style="color:#34d399">${string}</span>`;
    if (decorator) return `<span style="color:#c084fc">${decorator}</span>`;
    if (keyword) return `<span style="color:#60a5fa">${keyword}</span>`;
    if (number) return `<span style="color:#fb923c">${number}</span>`;
    return match;
  });
}

function escHtml(s: string): string {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

const highlightedCode = computed(() => {
  const code = editingContent.value;
  if (!code) return "";
  switch (editingType.value) {
    case "bat": return highlightBat(code);
    case "py": return highlightPy(code);
    default: return escHtml(code);
  }
});

function syncScroll() {
  const ta = editorRef.value;
  const hl = highlightRef.value;
  const ln = lineNumbersRef.value;
  if (ta && hl) {
    hl.scrollTop = ta.scrollTop;
    hl.scrollLeft = ta.scrollLeft;
  }
  if (ta && ln) ln.scrollTop = ta.scrollTop;
}

// ── Snippets ─────────────────────────────────────

const BAT_SNIPPETS = computed(() => [
  { label: "@echo off", code: "@echo off\n", desc: t("snippets.bat_echo_desc") },
  { label: "Goto", code: ":label\necho loop\ngoto label\n", desc: t("snippets.bat_goto_desc") },
  { label: "Wait", code: "timeout /t 5 /nobreak >nul\n", desc: t("snippets.bat_wait_desc") },
  { label: "Comment", code: "rem This is a comment\n", desc: t("snippets.bat_comment_desc") },
  { label: "Loop Num", code: "for /l %%i in (1,1,10) do (\n  echo %%i\n)\n", desc: t("snippets.bat_loop_desc") },
  { label: "Set Var", code: "set \"var=value\"\n", desc: t("snippets.bat_set_desc") },
]);

const PY_SNIPPETS = computed(() => [
  { label: "def", code: "def main():\n    pass\n\nif __name__ == \"__main__\":\n    main()\n", desc: t("snippets.py_def_desc") },
  { label: "for", code: "for i in range(10):\n    print(i)\n", desc: t("snippets.py_for_desc") },
  { label: "for each", code: "for item in items:\n    print(item)\n", desc: t("snippets.py_foreach_desc") },
  { label: "while", code: "while True:\n    time.sleep(1)\n", desc: t("snippets.py_while_desc") },
  { label: "if/else", code: "if condition:\n    pass\nelse:\n    pass\n", desc: t("snippets.py_if_desc") },
  { label: "sleep", code: "time.sleep(5)\n", desc: t("snippets.py_sleep_desc") },
  { label: "try/except", code: "try:\n    pass\nexcept Exception as e:\n    print(f\"Error: {e}\")\n", desc: t("snippets.py_try_desc") },
]);

// ── Helpers ─────────────────────────────────────

function genId(): string {
  return crypto.randomUUID().replace(/-/g, '').slice(0, 12);
}

/**
 * 统一的编辑器 keydown 处理，避免 Vue 事件修饰符在组合键时的冲突。
 */
function onEditorKeydown(e: KeyboardEvent) {
  // Tab / Shift+Tab
  if (e.key === 'Tab') {
    e.preventDefault();
    if (e.shiftKey) {
      unindentTab();
    } else {
      insertTab();
    }
    return;
  }
  // Ctrl+/ 注释
  if (e.key === '/' && (e.ctrlKey || e.metaKey) && !e.shiftKey && !e.altKey) {
    e.preventDefault();
    toggleComment();
    return;
  }
}

/**
 * 编辑器核心：直接操作 textarea，用 setRangeText 替换指定区间。
 * 执行后游标位于 replaceStart + text.length（'end' 模式）。
 * 调用方负责在此函数返回后用 setSelectionRange 设置最终光标/选区。
 *
 * 关于 undo：
 *   execCommand('insertText') 能保留原生 undo，但在 Tauri WebView (WebKit2GTK/WKWebView)
 *   上行为不一致——有时光标被错误放置，有时返回 false。
 *   因此改用 setRangeText，并通过 dispatchEvent('input') 让 Vue v-model 同步。
 *   这样失去了浏览器原生 undo，但光标行为稳定可预测。
 *   未来可考虑自实现 undo 栈（保存快照），此处先以正确性优先。
 */
function applyRangeText(ta: HTMLTextAreaElement, text: string, replaceStart: number, replaceEnd: number): void {
  ta.setRangeText(text, replaceStart, replaceEnd, 'end');
  // 同步 Vue v-model（setRangeText 不触发 input 事件）
  editingContent.value = ta.value;
}

function insertTab() {
  const ta = editorRef.value;
  if (!ta) return;
  const { selectionStart: start, selectionEnd: end, value } = ta;

  if (start === end) {
    // 无选区：光标处插入两个空格
    applyRangeText(ta, '  ', start, end);
    ta.setSelectionRange(start + 2, start + 2);
  } else {
    // 有选区（含多行）：扩展到行首，每行行首加两个空格
    const lineStart = value.lastIndexOf('\n', start - 1) + 1;
    const lineEnd = value[end - 1] === '\n' ? end - 1 : end;
    const block = value.substring(lineStart, lineEnd);
    const lines = block.split('\n');
    const indented = lines.map(l => '  ' + l).join('\n');
    applyRangeText(ta, indented, lineStart, lineEnd);
    // start 偏移2（首行多了两格），end 偏移总增量
    ta.setSelectionRange(start + 2, end + lines.length * 2);
  }
}

function unindentTab() {
  const ta = editorRef.value;
  if (!ta) return;
  const { selectionStart: start, selectionEnd: end, value } = ta;

  const lineStart = value.lastIndexOf('\n', start - 1) + 1;
  const lineEnd = value[end - 1] === '\n' ? end - 1 : end;
  const block = value.substring(lineStart, lineEnd);
  const lines = block.split('\n');

  let firstLineDelta = 0;
  const dedented = lines.map((l, i) => {
    const trimmed = l.replace(/^  ?/, '');
    if (i === 0) firstLineDelta = l.length - trimmed.length;
    return trimmed;
  });
  const dedentedStr = dedented.join('\n');
  const totalDelta = block.length - dedentedStr.length;
  if (totalDelta === 0) return;
  applyRangeText(ta, dedentedStr, lineStart, lineEnd);
  ta.setSelectionRange(
    Math.max(lineStart, start - firstLineDelta),
    end - totalDelta
  );
}

function toggleComment() {
  const ta = editorRef.value;
  if (!ta) return;
  const { selectionStart: start, selectionEnd: end, value } = ta;

  const commentChar = editingType.value === 'py' ? '# ' : ':: ';

  const lineStart = value.lastIndexOf('\n', start - 1) + 1;
  const lineEnd = value[end - 1] === '\n' ? end - 1 : end;
  const block = value.substring(lineStart, lineEnd);
  const lines = block.split('\n');

  const nonEmpty = lines.filter(l => l.trim().length > 0);
  const allCommented = nonEmpty.length > 0 &&
    nonEmpty.every(l => l.trimStart().startsWith(commentChar.trimEnd()));

  let toggled: string;
  if (allCommented) {
    toggled = lines.map(l => {
      const idx = l.indexOf(commentChar.trimEnd());
      if (idx < 0) return l;
      const afterComment = l.charAt(idx + commentChar.trimEnd().length) === ' '
        ? idx + commentChar.length
        : idx + commentChar.trimEnd().length;
      return l.substring(0, idx) + l.substring(afterComment);
    }).join('\n');
  } else {
    toggled = lines.map(l => commentChar + l).join('\n');
  }

  const delta = toggled.length - block.length;
  applyRangeText(ta, toggled, lineStart, lineEnd);
  const newStart = Math.max(lineStart, start + (allCommented ? -commentChar.length : commentChar.length));
  ta.setSelectionRange(newStart, end + delta);
}

function insertSnippet(code: string) {
  const ta = editorRef.value;
  if (!ta) return;
  const { selectionStart: start, selectionEnd: end } = ta;
  applyRangeText(ta, code, start, end);
  ta.setSelectionRange(start + code.length, start + code.length);
  ta.focus();
}

// ── Script operations ─────────────────────────────

async function newScript() {
  const id = genId();
  editingName.value = "untitled";
  editingType.value = globalType.value;
  localFilePath.value = null;
  const templates: Record<string, string> = {
    bat: "@echo off\n\n",
    py: "#!/usr/bin/env python3\n\n",
  };
  editingContent.value = templates[globalType.value] || "";
  currentScript.value = { id, name: "untitled", type: globalType.value, content: editingContent.value, createdAt: "", updatedAt: "" };
  nextTick(() => editorRef.value?.focus());
}

async function openLocalFile() {
  try {
    const result = await invoke<string | null>("plugin:dialog|open", {
      options: {
        multiple: false,
        filters: [
          { name: "Scripts", extensions: ["bat", "cmd", "py"] },
          { name: "All Files", extensions: ["*"] },
        ],
      },
    });
    if (!result) return;
    const path = result;
    const content = await invoke<string>("read_text_file", { path });
    if (content === undefined || content === null) return;
    const parts = path.replace(/\\/g, "/").split("/");
    const fullName = parts.pop() || "untitled";
    const nameParts = fullName.split(".");
    const ext = nameParts.length > 1 ? nameParts.pop()!.toLowerCase() : "";
    const name = nameParts.join(".");
    const typeMap: Record<string, string> = { bat: "bat", cmd: "bat", py: "py" };
    editingName.value = name || fullName;
    editingType.value = typeMap[ext] || "bat";
    editingContent.value = content;
    localFilePath.value = path; // 记住原始文件路径
    // 自动把文件所在目录设为工作目录
    const normalized = path.replace(/\\/g, '/');
    const lastSlash = normalized.lastIndexOf('/');
    workingDir.value = lastSlash >= 0 ? path.substring(0, lastSlash) : "";
    currentScript.value = { id: genId(), name: editingName.value, type: editingType.value, content, createdAt: "", updatedAt: "" };
    nextTick(() => editorRef.value?.focus());
  } catch (e: any) {
    console.error("Open failed:", e);
  }
}

async function saveCurrentScript() {
  if (!editingName.value.trim()) { showToast(t("scripts.nameEmpty"), false); return; }
  try {
    const name = editingName.value.trim();
    const id = currentScript.value?.id || genId();
    await db.saveScript({ id, name, type: editingType.value, content: editingContent.value });
    currentScript.value = { id, name, type: editingType.value, content: editingContent.value, createdAt: "", updatedAt: "" };
    await loadScriptList();
    showToast(t("scripts.saveSuccess"), true);
  } catch (e: any) {
    showToast(t("scripts.saveFail") + ": " + (e?.message || e), false);
  }
}

async function loadScript(id: string) {
  const s = await db.loadScript(id);
  if (s) {
    currentScript.value = s;
    editingName.value = s.name;
    editingType.value = s.type;
    editingContent.value = s.content;
    localFilePath.value = null; // 数据库脚本无本地文件路径
    // 恢复该脚本的工作目录（按脚本 id 存入 localStorage）
    workingDir.value = localStorage.getItem(`script-work-dir:${id}`) || "";
  }
}

async function loadScriptList() {
  scripts.value = await db.listScripts();
}

async function exportToFile() {
  try {
    const extMap: Record<string, string> = { bat: "bat", py: "py" };
    const ext = extMap[editingType.value] || "bat";
    const defaultName = editingName.value.includes(".") ? editingName.value : `${editingName.value}.${ext}`;
    const path = await save({ defaultPath: defaultName, filters: [{ name: "Script", extensions: [ext] }] });
    if (!path) return;
    const { writeTextFile } = await import("@tauri-apps/plugin-fs");
    await writeTextFile(path, editingContent.value);
    showToast(t("scripts.exportSuccess"), true);
  } catch (e: any) {
    showToast(t("scripts.exportFail") + ": " + (e?.message || e), false);
  }
}

let isRunning = false;
async function runCurrentScript() {
  if (isRunning) return;
  if (!editingContent.value.trim()) return;
  isRunning = true;
  const name = editingName.value.trim() || "untitled";
  const tab = addTab(name);
  const extMap: Record<string, string> = { bat: "bat", py: "py" };
  const interpreterMap: Record<string, string> = { bat: "bat", py: "python" };
  const ext = extMap[editingType.value] || "bat";
  const interpreter = interpreterMap[editingType.value] || "shell";
  try {
    let scriptPath: string;
    // 优先级：用户手动指定的工作目录 > localFilePath 派生的目录
    let workDir: string | null = workingDir.value.trim() || null;

    // 对 Python 脚本（localFilePath 路径），如果有工作目录则注入 sys.path
    // temp 路径分支会在后面单独处理注入逻辑
    let finalContent = editingContent.value;
    if (interpreter === 'python' && workDir && localFilePath.value) {
      const sysPathInject = `import sys as _sys; _sys.path.insert(0, r"${workDir}"); del _sys\n`;
      finalContent = sysPathInject + finalContent;
    }

    if (localFilePath.value) {
      // 有原始文件路径：直接写回原始文件后在原始目录执行
      const { writeTextFile } = await import("@tauri-apps/plugin-fs");
      await writeTextFile(localFilePath.value, finalContent);
      scriptPath = localFilePath.value;
      if (!workDir) {
        const normalized = localFilePath.value.replace(/\\/g, '/');
        const lastSlash = normalized.lastIndexOf('/');
        workDir = lastSlash >= 0 ? localFilePath.value.substring(0, lastSlash) : null;
      }
    } else {
      // 没有原始路径：写入 temp_scripts 目录
      const { appDataDir } = await import("@tauri-apps/api/path");
      const { mkdir, writeTextFile } = await import("@tauri-apps/plugin-fs");
      const dir = await appDataDir();
      const s = dir.includes('\\') ? '\\' : '/';
      const tmpDir = (dir.endsWith(s) ? `${dir}temp_scripts` : `${dir}${s}temp_scripts`).trimEnd();
      try { await mkdir(tmpDir, { recursive: true }); } catch (e) { console.warn('[ScriptSpace] mkdir failed:', e); }

      // 把同类型的其他脚本也写到 temp 目录，文件名用脚本名，
      // 这样 import exporter 能找到同目录的 exporter.py
      const sameTypeScripts = scripts.value.filter(
        s => s.type === editingType.value && s.id !== currentScript.value?.id
      );
      for (const sibling of sameTypeScripts) {
        try {
          const full = await db.loadScript(sibling.id);
          if (!full) continue;
          const safeName = sibling.name.replace(/[<>:"/\\|?*\s]/g, '_');
          const siblingPath = `${tmpDir}${dir.includes('\\') ? '\\' : '/'}${safeName}.${ext}`;
          await writeTextFile(siblingPath, full.content);
        } catch { /* 单个失败不阻断运行 */ }
      }

      // 在注入代码里把 tmpDir 加入 sys.path（覆盖前面的 workDir 注入逻辑）
      if (interpreter === 'python') {
        const sysPathInject = `import sys as _sys; _sys.path.insert(0, r"${tmpDir}"); del _sys\n`;
        finalContent = sysPathInject + editingContent.value; // 重新构建，以 tmpDir 为准
      }

      const tempPath = `${tmpDir}${dir.includes('\\') ? '\\' : '/'}__ts_run_${tab.id}.${ext}`;
      await invoke("write_script_file", { path: tempPath, content: finalContent, interpreter });
      scriptPath = tempPath;
      workDir = workDir || tmpDir; // 工作目录也设为 tmpDir
    }

    await invoke("script_spawn", {
      id: tab.id,
      interpreter,
      scriptPath,
      args: [],
      workDir,
    });
  } catch (e: any) {
    tab.output.push({ text: `Failed: ${e?.message || e}`, stream: "stderr" });
    tab.status = "error";
    tab.exitCode = -1;
  } finally {
    isRunning = false;
  }
}

async function browseWorkDir() {
  try {
    const { open } = await import("@tauri-apps/plugin-dialog");
    const dir = await open({ directory: true, title: t("scripts.workDirBrowse") });
    if (dir) {
      workingDir.value = dir as string;
      // 立即持久化
      if (currentScript.value?.id) {
        localStorage.setItem(`script-work-dir:${currentScript.value.id}`, dir as string);
      }
    }
  } catch {}
}

function handleDocClick(e: MouseEvent) {
  if (typeDropdownRef.value && !typeDropdownRef.value.contains(e.target as Node)) {
    typeDropdownOpen.value = false;
  }
}

let resizeObs: ResizeObserver | null = null;

onMounted(async () => {
  // 恢复上次选择的脚本类型
  const savedType = localStorage.getItem('script-space:type');
  if (savedType && typeOptions.some(o => o.value === savedType)) {
    globalType.value = savedType;
  }
  document.addEventListener("click", handleDocClick);
  setScrollContainer(outputContainer.value);
  await setupRunner();
  await loadScriptList();
  updatePageSize();
  if (listContainerRef.value) {
    resizeObs = new ResizeObserver(updatePageSize);
    resizeObs.observe(listContainerRef.value);
  }
});

watch([globalType, searchQuery, sortMode, sortAsc], () => { currentPage.value = 1; });

// 工作目录变更时持久化（按脚本 id 存储）
watch(workingDir, (val) => {
  if (currentScript.value?.id) {
    if (val.trim()) {
      localStorage.setItem(`script-work-dir:${currentScript.value.id}`, val.trim());
    } else {
      localStorage.removeItem(`script-work-dir:${currentScript.value.id}`);
    }
  }
});

// 内容变化时（包括删除导致的自动滚动）同步 pre 和行号的滚动位置
// 用 rAF 确保在浏览器完成自动滚动并绘制后再同步，避免 pre 停留在旧位置
watch(editingContent, () => {
  nextTick(() => requestAnimationFrame(syncScroll));
});

onUnmounted(() => {
  destroy();
  document.removeEventListener("click", handleDocClick);
  if (tipTimer) clearTimeout(tipTimer);
  if (toastTimer) clearTimeout(toastTimer);
  if (resizeObs) resizeObs.disconnect();
});
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

.editor-textarea::selection {
  background: rgba(100, 140, 255, 0.25);
  color: transparent;
  -webkit-text-fill-color: transparent;
}
.editor-textarea::-moz-selection {
  background: rgba(100, 140, 255, 0.25);
  color: transparent;
}
.editor-textarea {
  color: transparent !important;
  caret-color: white !important;
  user-select: text !important;
  -webkit-user-select: text !important;
}
.editor-textarea::-webkit-scrollbar {
  display: none;
}
.editor-highlight::-webkit-scrollbar {
  display: none;
}
</style>
