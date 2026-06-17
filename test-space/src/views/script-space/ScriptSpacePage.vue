<template>
  <div class="h-screen flex flex-col -mx-margin-page pb-2 box-border select-none">
    <!-- Toolbar -->
    <div class="flex items-center gap-3 mb-2 flex-shrink-0 ml-3">
      <!-- Type dropdown -->
      <div class="relative" ref="typeDropdownRef">
        <button class="glass-button px-4 py-2 rounded-full font-label-md text-label-md flex items-center gap-1.5 min-w-[100px] select-none" @click="typeDropdownOpen = !typeDropdownOpen">
          <span class="material-symbols-outlined text-[18px]">code</span>
          <span class="text-[13px] font-mono uppercase">{{ currentTypeLabel }}</span>
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
      <button class="glass-button px-4 py-2 rounded-full font-label-md text-label-md flex items-center gap-1.5 select-none" @click="newScript">
        <span class="material-symbols-outlined text-[18px]">add</span>
        {{ t("scripts.new") }}
      </button>
      <button class="glass-button px-4 py-2 rounded-full font-label-md text-label-md flex items-center gap-1.5 select-none" @click="openLocalFile">
        <span class="material-symbols-outlined text-[18px]">folder_open</span>
        {{ t("scripts.open") }}
      </button>
      <button v-if="currentScript" class="glass-button px-4 py-2 rounded-full font-label-md text-label-md flex items-center gap-1.5 select-none" @click="saveCurrentScript">
        <span class="material-symbols-outlined text-[18px]">save</span>
        {{ t("scripts.save") }}
      </button>
      <button v-if="currentScript" class="glass-button px-4 py-2 rounded-full font-label-md text-label-md flex items-center gap-1.5 select-none" @click="exportToFile">
        <span class="material-symbols-outlined text-[18px]">file_upload</span>
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
        <div v-if="totalPages > 1" class="px-3 py-1.5 border-t border-white/10 flex items-center justify-between flex-shrink-0">
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
              <div ref="lineNumbersRef" class="flex-shrink-0 text-right px-3 py-3 text-[13px] leading-relaxed font-mono text-[#4a5568] select-none overflow-hidden" style="background: #0d0d1a; min-width: 36px;">
                <div v-for="n in lineCount" :key="n">{{ n }}</div>
              </div>
              <div class="flex-1 relative min-h-0">
                <pre ref="highlightRef" class="absolute inset-0 p-3 text-[13px] leading-relaxed font-mono whitespace-pre-wrap break-all overflow-y-auto pointer-events-none text-[#e4e5e7] select-text" style="background: #0d0d1a;" aria-hidden="true"><code v-html="highlightedCode"></code></pre>
                <textarea ref="editorRef" v-model="editingContent"
                  class="absolute inset-0 w-full h-full resize-none outline-none border-none p-3 text-[13px] leading-relaxed font-mono text-transparent caret-white custom-scrollbar select-text"
                  style="background: transparent; tab-size: 2;"
                  spellcheck="false"
                  @keydown.tab.prevent="insertTab"
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
      <div v-if="activeTip !== null && tipSnippet" class="fixed z-[10000] px-3 py-2 rounded-lg text-[12px] text-white/90 max-w-[280px] pointer-events-none shadow-xl border border-white/10"
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
  addTab, clearTabOutput, killScript, setup: setupRunner, setScrollContainer,
} = useScriptRunner();

const scripts = ref<db.ScriptItem[]>([]);
const currentScript = ref<db.ScriptItem | null>(null);
const editingName = ref("");
const editingType = ref("bat");
const editingContent = ref("");
const editorRef = ref<HTMLTextAreaElement | null>(null);
const highlightRef = ref<HTMLElement | null>(null);
const lineNumbersRef = ref<HTMLElement | null>(null);
const outputContainer = ref<HTMLElement | null>(null);

// ── Dynamic pagination ────────────────────────────────
const listContainerRef = ref<HTMLElement | null>(null);
const pageSize = ref(999);
const ITEM_HEIGHT = 36;
const PAGINATOR_H = 32;

const currentPage = ref(1);

const totalPages = computed(() => {
  const n = Math.max(1, Math.ceil(filteredScripts.value.length / pageSize.value));
  if (currentPage.value > n) currentPage.value = n;
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
    resetEditor();
  }
}

function confirmTypeSwitch() {
  if (pendingTypeSwitch.value) {
    globalType.value = pendingTypeSwitch.value;
    resetEditor();
  }
  pendingTypeSwitch.value = null;
}

function resetEditor() {
  currentScript.value = null;
  editingName.value = "";
  editingContent.value = "";
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
  await db.deleteScript(id);
  if (currentScript.value?.id === id) {
    currentScript.value = null;
    editingName.value = "";
    editingContent.value = "";
  }
  deleteTarget.value = null;
  await loadScriptList();
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
    tipStyle.value = {
      left: `${rect.left}px`,
      top: `${rect.top - 8}px`,
      transform: 'translateY(-100%)',
    };
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
  let html = escHtml(code);
  html = html.replace(/(#.*)/g, '<span style="color:#6b7280">$1</span>');
  html = html.replace(/("""[\s\S]*?"""|'''[\s\S]*?'''|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')/g, '<span style="color:#34d399">$1</span>');
  html = html.replace(/(@\w[\w.]*)/g, '<span style="color:#c084fc">$1</span>');
  html = html.replace(/\b(def|class|if|elif|else|for|while|try|except|finally|import|from|return|yield|raise|with|as|pass|break|continue|and|or|not|in|is|lambda|global|nonlocal|assert|del|True|False|None|print|self|async|await)\b/g, '<span style="color:#60a5fa">$1</span>');
  html = html.replace(/\b(\d+\.?\d*)\b/g, '<span style="color:#fb923c">$1</span>');
  return html;
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
  if (ta && hl) hl.scrollTop = ta.scrollTop;
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
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
}

function insertTab() {
  const ta = editorRef.value;
  if (!ta) return;
  const start = ta.selectionStart;
  const end = ta.selectionEnd;
  editingContent.value = editingContent.value.substring(0, start) + "  " + editingContent.value.substring(end);
  nextTick(() => { ta.selectionStart = ta.selectionEnd = start + 2; });
}

function insertSnippet(code: string) {
  const ta = editorRef.value;
  if (!ta) return;
  const start = ta.selectionStart;
  editingContent.value = editingContent.value.substring(0, start) + code + editingContent.value.substring(ta.selectionEnd);
  nextTick(() => {
    ta.selectionStart = ta.selectionEnd = start + code.length;
    ta.focus();
  });
}

// ── Script operations ─────────────────────────────

async function newScript() {
  const id = genId();
  editingName.value = "untitled";
  editingType.value = globalType.value;
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

async function runCurrentScript() {
  if (!editingContent.value.trim()) return;
  const name = editingName.value.trim() || "untitled";
  const tab = addTab(name);
  const extMap: Record<string, string> = { bat: "bat", py: "py" };
  const interpreterMap: Record<string, string> = { bat: "bat", py: "python" };
  const ext = extMap[editingType.value] || "bat";
  const interpreter = interpreterMap[editingType.value] || "shell";
  try {
    const { appDataDir } = await import("@tauri-apps/api/path");
    const { mkdir } = await import("@tauri-apps/plugin-fs");
    const dir = await appDataDir();
    const tmpDir = `${dir}temp_scripts`;
    try { await mkdir(tmpDir); } catch {}
    const tempPath = `${tmpDir}${tab.id}.${ext}`;
    await invoke("write_script_file", { path: tempPath, content: editingContent.value, interpreter });
    await invoke("script_spawn", {
      id: tab.id,
      interpreter,
      scriptPath: tempPath,
      args: [],
    });
  } catch (e: any) {
    tab.output.push({ text: `Failed: ${e?.message || e}`, stream: "stderr" });
    tab.status = "error";
    tab.exitCode = -1;
  }
}

function handleDocClick(e: MouseEvent) {
  if (typeDropdownRef.value && !typeDropdownRef.value.contains(e.target as Node)) {
    typeDropdownOpen.value = false;
  }
}

let resizeObs: ResizeObserver | null = null;

onMounted(async () => {
  document.addEventListener("click", handleDocClick);
  setScrollContainer(outputContainer.value);
  await setupRunner();
  await loadScriptList();
  nextTick(() => {
    updatePageSize();
    if (listContainerRef.value) {
      resizeObs = new ResizeObserver(updatePageSize);
      resizeObs.observe(listContainerRef.value);
    }
  });
});

watch([globalType, searchQuery, sortMode, sortAsc], () => { currentPage.value = 1; });

onUnmounted(() => {
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
</style>
