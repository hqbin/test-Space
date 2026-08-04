<template>
  <div class="w-screen h-screen select-none">
    <div class="rounded-2xl h-full flex flex-col overflow-hidden sticky-bg">
      <!-- 标题栏 -->
      <div class="group flex items-center gap-1 pl-3 pr-2 py-1.5 border-b border-black/10 shrink-0">
        <!-- 显示态：data-tauri-drag-region 必须在最内层被点击元素上，父 div 无效（Tauri v2 行为） -->
        <template v-if="!editingTitle">
          <span
            data-tauri-drag-region
            class="text-sm font-medium flex-1 min-w-0 truncate sticky-title cursor-default"
          >{{ title || t('notes.untitled') }}</span>
          <button
            class="glass-button rounded-full w-5 h-5 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity shrink-0"
            :title="t('notes.editTitle')"
            @mousedown.stop
            @click.stop="startEditTitle"
          ><span class="material-symbols-outlined text-[11px]">edit</span></button>
        </template>
        <!-- 编辑态 -->
        <template v-else>
          <input
            ref="titleInputRef"
            v-model="title"
            class="text-sm font-medium bg-transparent outline-none flex-1 min-w-0 sticky-title"
            :placeholder="t('notes.untitled')"
            @blur="finishEditTitle"
            @keydown.enter.prevent="finishEditTitle"
            @keydown.escape.prevent="finishEditTitle"
          />
          <button
            class="glass-button rounded-full w-5 h-5 flex items-center justify-center shrink-0"
            :title="t('notes.editTitle')"
            @mousedown.prevent
            @click.stop="finishEditTitle"
          ><span class="material-symbols-outlined text-[11px]">check</span></button>
        </template>
        <div class="flex items-center gap-0.5 shrink-0">
          <button
            class="glass-button rounded-full w-6 h-6 flex items-center justify-center shrink-0"
            :class="{ 'btn-keep-active': alwaysOnTop }"
            :title="alwaysOnTop ? t('notes.cancelAlwaysOnTop') : t('notes.alwaysOnTop')"
            @mousedown.stop
            @click.stop="toggleAlwaysOnTop"
          ><span class="material-symbols-outlined text-[13px]">keep</span></button>
          <button
            class="glass-button rounded-full w-6 h-6 flex items-center justify-center shrink-0"
            :title="t('notes.newStickyNote')"
            @mousedown.stop
            @click.stop="createNewSticky"
          ><span class="material-symbols-outlined text-[13px]">add</span></button>
          <button
            class="glass-button rounded-full w-6 h-6 flex items-center justify-center text-xs shrink-0"
            :title="t('notes.unpinFromDesktop')"
            @mousedown.stop
            @click.stop="handleClose"
          >✕</button>
        </div>
      </div>
      <!-- 编辑区 -->
      <div class="flex-1 min-h-0 overflow-y-auto px-3 py-2 custom-scrollbar">
        <EditorContent :editor="editor" class="sticky-editor-content" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted, onUnmounted } from "vue";
import { EditorContent } from "@tiptap/vue-3";
import { listen, emitTo, type UnlistenFn } from "@tauri-apps/api/event";
import { getCurrentWebviewWindow } from "@tauri-apps/api/webviewWindow";
import { pin, unpin } from "tauri-plugin-wallpaper";
import * as db from "@/services/database";
import { ensureStickyWindow, unpinAndClose } from "@/services/stickyWindow";
import { useNoteEditor } from "@/composables/useNoteEditor";
import { useI18n } from "@/composables/useI18n";
import { NOTE_LINK_PREFIX } from "@/extensions/wikiNoteLink";

const { t } = useI18n();

const appWindow = getCurrentWebviewWindow();
const listenTarget = { target: { kind: 'WebviewWindow' as const, label: appWindow.label } };
const noteId = new URLSearchParams(window.location.search).get("noteId") || "";

const title = ref("");
const alwaysOnTop = ref(false);
const editingTitle = ref(false);
const titleInputRef = ref<HTMLInputElement | null>(null);

let noteBase: { folderId: string | null; tags: string[]; isFavorite: boolean } | null = null
let saved = true
let lastSavedAt = ""
let saveTimer: ReturnType<typeof setTimeout> | null = null
let posTimer: ReturnType<typeof setTimeout> | null = null
let unlisteners: UnlistenFn[] = []
let closed = false
let titleMap = new Map<string, string>()

function resolveNoteIdByTitle(noteTitle: string): string | null {
  const q = noteTitle.trim().toLowerCase()
  if (!q) return null
  const id = titleMap.get(q)
  if (id) return id
  for (const [key, nid] of titleMap) {
    if (key.includes(q)) return nid
  }
  return null
}

const { editor } = useNoteEditor({
  resolveNoteId: resolveNoteIdByTitle,
  onOpenNoteLink: (href) => {
    const id = href.slice(NOTE_LINK_PREFIX.length)
    if (id) emitTo("main", "notes:open-note", { noteId: id }).catch(() => {})
  },
  onUpdate: () => { triggerSave() },
  editorClass: "outline-none min-h-[200px]",
})

function startEditTitle() {
  editingTitle.value = true
  nextTick(() => titleInputRef.value?.focus())
}

function finishEditTitle() {
  editingTitle.value = false
  triggerSave()
}


function triggerSave() {
  if (!noteId) return
  saved = false
  if (saveTimer) clearTimeout(saveTimer)
  saveTimer = setTimeout(() => { saveCurrentNote() }, 1500)
}

async function saveCurrentNote() {
  const ed = editor.value
  if (!ed || !noteId || !noteBase) return
  const html = ed.getHTML()
  const contentJson = JSON.stringify(ed.getJSON())
  const now = new Date().toISOString()
  try {
    await db.saveNote({
      id: noteId,
      folderId: noteBase.folderId,
      title: title.value,
      content: html,
      contentJson,
      tags: noteBase.tags,
      isFavorite: noteBase.isFavorite,
    })
    saved = true
    lastSavedAt = now
    try {
      await emitTo("main", "notes:note-updated", {
        noteId,
        title: title.value,
        content: html,
        contentJson,
        updatedAt: now,
        sourceLabel: appWindow.label,
      })
    } catch {}
  } catch (e) {
    console.error("[sticky] save failed:", e)
    saved = false
  }
}

async function handleClose() {
  if (closed) return
  closed = true
  if (!saved && editor.value && noteId) {
    await saveCurrentNote().catch(() => {})
  }
  emitTo("main", "sticky:closed", { noteId }).catch(() => {})
  try { await unpin() } catch {}
  await unpinAndClose(noteId)
}

// ── 置顶开关：pin() 同时处理 HWND_TOPMOST + Win+D 防护，unpin() 全部还原 ──
// 默认不调用 pin()，便签不置顶；用户点击按钮后才激活
async function toggleAlwaysOnTop() {
  const next = !alwaysOnTop.value
  alwaysOnTop.value = next
  if (next) {
    pin().catch(() => { appWindow.setAlwaysOnTop(true).catch(() => {}) })
  } else {
    unpin().catch(() => { appWindow.setAlwaysOnTop(false).catch(() => {}) })
  }
}

async function createNewSticky() {
  try {
    const newId = crypto.randomUUID()
    await db.saveNote({ id: newId, folderId: null, title: "", content: "", contentJson: null, tags: [], isFavorite: false })
    await db.pinNoteToDesktop(newId)
    emitTo("main", "notes:note-created", { noteId: newId }).catch(() => {})
    ensureStickyWindow(newId).catch(e => console.error("[sticky] create new failed:", e))
  } catch (e) {
    console.error("[sticky] createNewSticky failed:", e)
  }
}

function schedulePosSave() {
  if (posTimer) clearTimeout(posTimer)
  posTimer = setTimeout(async () => {
    try {
      const pos = await appWindow.outerPosition()
      const size = await appWindow.outerSize()
      await db.updateStickyPosition(noteId, pos.x, pos.y, size.width, size.height)
    } catch {}
  }, 300)
}

function onNoteUpdated(e: { payload: any }) {
  const p = e.payload as { noteId?: string; title?: string; content?: string; contentJson?: string; updatedAt?: string; sourceLabel?: string }
  if (!p || p.noteId !== noteId) return
  if (p.sourceLabel === appWindow.label) return
  if (!saved) return
  if (p.updatedAt && lastSavedAt && p.updatedAt <= lastSavedAt) return
  const ed = editor.value
  if (!ed) return
  try {
    if (p.contentJson) {
      const parsed = JSON.parse(p.contentJson)
      if (parsed && typeof parsed === "object") {
        ed.commands.setContent(parsed, false)
        saved = true
        lastSavedAt = p.updatedAt || ""
        if (p.title) title.value = p.title
        return
      }
    }
  } catch {}
  if (p.content !== undefined) {
    ed.commands.setContent(p.content, false)
    saved = true
    lastSavedAt = p.updatedAt || ""
  }
  if (p.title) title.value = p.title
}

function onNoteDeleted(e: { payload: any }) {
  if (e.payload?.noteId === noteId) handleClose()
}

onMounted(async () => {
  if (!noteId) {
    try { await appWindow.destroy() } catch {}
    return
  }
  try {
    const note = await db.loadNote(noteId)
    if (!note) {
      await unpinAndClose(noteId)
      return
    }
    title.value = note.title || ""
    noteBase = { folderId: note.folderId ?? null, tags: note.tags ?? [], isFavorite: !!note.isFavorite }
    const ed = editor.value
    if (ed) {
      const cj = note.contentJson
      if (cj && cj.length > 2) {
        try { ed.commands.setContent(JSON.parse(cj), false) } catch { ed.commands.setContent(note.content || "", false) }
      } else {
        ed.commands.setContent(note.content || "", false)
      }
      lastSavedAt = note.updatedAt || ""
      saved = true
    }
    // 标题 → ID 映射：用 loadNoteList（只含元数据，不拉正文，速度快）
    db.loadNoteList().then(all => {
      titleMap = new Map(all.map(n => [n.title.trim().toLowerCase(), n.id]))
    }).catch(() => {})
    // 事件监听 + 窗口事件：并行注册
    const [l1, l2] = await Promise.all([
      listen("notes:note-updated", onNoteUpdated, listenTarget),
      listen("notes:note-deleted", onNoteDeleted),
    ])
    unlisteners.push(l1, l2)
    appWindow.onMoved(schedulePosSave)
    appWindow.onResized(schedulePosSave)
    appWindow.onCloseRequested(async () => {
      if (closed) return
      closed = true
      if (!saved && editor.value && noteId) {
        await saveCurrentNote().catch(() => {})
      }
      emitTo("main", "sticky:closed", { noteId }).catch(() => {})
      db.unpinNoteFromDesktop(noteId).catch(() => {})
      unpin().catch(() => {})
    })
    // 新建便签时自动聚焦标题输入框
    if (!note.title) {
      titleInputRef.value?.focus()
    }
  } catch (e) {
    console.error("[sticky] init failed:", e)
  }
})

onUnmounted(() => {
  unlisteners.forEach(u => { try { u() } catch {} })
  unlisteners = []
  if (saveTimer) clearTimeout(saveTimer)
  if (posTimer) clearTimeout(posTimer)
  unpin().catch(() => {})
})
</script>

<style scoped>
.sticky-bg {
  /* 与软件 surface 色（#FFFDF7）一致，渐变到暖黄增加纸质感 */
  background: linear-gradient(160deg, #FFFDF7 0%, #FFF3DC 100%);
}

html.dark .sticky-bg {
  background: linear-gradient(160deg, #1E1C18 0%, #1A1812 100%);
}

.sticky-title {
  color: #1C1B1F;
}

/* 置顶按钮激活态 */
.btn-keep-active span {
  color: #E8743A;
}

.sticky-editor-content :deep(.ProseMirror) {
  color: #1C1B1F;
}

html.dark .sticky-title {
  color: #E8E2D3;
}

html.dark .btn-keep-active span {
  color: #F0B080;
}

html.dark .sticky-editor-content :deep(.ProseMirror) {
  color: #E8E2D3;
}
</style>
