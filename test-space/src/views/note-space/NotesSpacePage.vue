<template>
  <div class="flex h-[calc(100vh-64px)] -mx-margin-page overflow-hidden">
    <!-- Left: File Tree -->
    <div class="w-64 glass-panel border-r flex-shrink-0 flex flex-col bg-white/5 backdrop-blur-[30px] overflow-hidden">
      <div class="p-4 border-b border-glass-border-light/50 flex justify-between items-center">
        <span class="font-label-md text-label-md text-on-surface font-semibold">Directory</span>
        <button class="glass-button" @click="createFolder">
          <span class="material-symbols-outlined text-[18px]">create_new_folder</span>
        </button>
      </div>
      <div class="flex-1 overflow-y-auto p-2">
        <ul class="space-y-1">
          <li v-for="(item, idx) in fileTree" :key="idx">
            <div
              class="glass-hover flex items-center gap-2 px-2 py-1.5 rounded-md cursor-pointer transition-colors group"
              :class="item.active && !item.children ? 'bg-white/40 text-on-surface' : 'text-on-surface-variant'"
              @click="toggleFolder(item)"
            >
              <span class="material-symbols-outlined text-[16px]">{{ item.expanded ? 'folder_open' : 'folder' }}</span>
              <span class="font-body-md text-body-md text-[13px] flex-1" :class="item.active ? 'font-medium' : ''">{{ item.name }}</span>
              <button class="glass-button p-1 opacity-0 group-hover:opacity-100" @click.stop="deleteFolder(idx)">
                <span class="material-symbols-outlined text-[14px]">delete</span>
              </button>
            </div>
            <ul v-if="item.children && item.expanded" class="pl-6 space-y-1 mt-1 border-l border-glass-border-light/50 ml-3">
              <li v-for="(child, cidx) in item.children" :key="cidx" class="group">
                <div
                  class="glass-hover flex items-center gap-2 px-2 py-1.5 rounded-md cursor-pointer transition-colors"
                  :class="child.active ? 'bg-white/40 text-on-surface' : 'text-on-surface-variant'"
                  @click="selectFile(item, child)"
                >
                  <span class="material-symbols-outlined text-[14px]" :class="child.active ? 'text-secondary' : ''">description</span>
                  <span class="font-body-md text-body-md text-[13px] flex-1" :class="child.active ? 'font-medium' : ''">{{ child.name }}</span>
                  <button class="glass-button p-1 opacity-0 group-hover:opacity-100" @click.stop="deleteFile(item, cidx)">
                    <span class="material-symbols-outlined text-[14px]">delete</span>
                  </button>
                </div>
              </li>
              <li>
                <button class="glass-button flex items-center gap-1 px-2 py-1 text-caption w-full" @click="addFile(item)">
                  <span class="material-symbols-outlined text-[12px]">add</span>
                  New file
                </button>
              </li>
            </ul>
          </li>
        </ul>
      </div>
    </div>

    <!-- Center: TipTap Editor -->
    <div class="flex-1 flex flex-col overflow-hidden bg-transparent py-4 px-4 lg:px-8">
      <div class="flex-1 glass-panel rounded-xl overflow-hidden bg-white/40 flex flex-col">
        <!-- Toolbar -->
        <div class="sticky top-0 z-10 bg-white/50 backdrop-blur-md border-b border-glass-border-light/30 px-4 py-2 flex items-center gap-1 rounded-t-xl flex-wrap">
          <button class="glass-button p-1.5 rounded" :class="{ 'glass-active': editor?.isActive('bold') }" @click="editor?.chain().focus().toggleBold().run()">
            <span class="material-symbols-outlined text-[18px] text-on-surface-variant">format_bold</span>
          </button>
          <button class="glass-button p-1.5 rounded" :class="{ 'glass-active': editor?.isActive('italic') }" @click="editor?.chain().focus().toggleItalic().run()">
            <span class="material-symbols-outlined text-[18px] text-on-surface-variant">format_italic</span>
          </button>
          <button class="glass-button p-1.5 rounded" :class="{ 'glass-active': editor?.isActive('underline') }" @click="editor?.chain().focus().toggleUnderline().run()">
            <span class="material-symbols-outlined text-[18px] text-on-surface-variant">format_underlined</span>
          </button>
          <button class="glass-button p-1.5 rounded" :class="{ 'glass-active': editor?.isActive('strike') }" @click="editor?.chain().focus().toggleStrike().run()">
            <span class="material-symbols-outlined text-[18px] text-on-surface-variant">strikethrough_s</span>
          </button>
          <div class="w-px h-4 bg-outline-variant/30 mx-1"></div>
          <button class="glass-button p-1.5 rounded" :class="{ 'glass-active': editor?.isActive('heading', { level: 1 }) }" @click="editor?.chain().focus().toggleHeading({ level: 1 }).run()">
            <span class="text-[11px] font-bold text-on-surface-variant px-1">H1</span>
          </button>
          <button class="glass-button p-1.5 rounded" :class="{ 'glass-active': editor?.isActive('heading', { level: 2 }) }" @click="editor?.chain().focus().toggleHeading({ level: 2 }).run()">
            <span class="text-[11px] font-bold text-on-surface-variant px-1">H2</span>
          </button>
          <button class="glass-button p-1.5 rounded" :class="{ 'glass-active': editor?.isActive('heading', { level: 3 }) }" @click="editor?.chain().focus().toggleHeading({ level: 3 }).run()">
            <span class="text-[11px] font-bold text-on-surface-variant px-1">H3</span>
          </button>
          <div class="w-px h-4 bg-outline-variant/30 mx-1"></div>
          <button class="glass-button p-1.5 rounded" :class="{ 'glass-active': editor?.isActive('bulletList') }" @click="editor?.chain().focus().toggleBulletList().run()">
            <span class="material-symbols-outlined text-[18px] text-on-surface-variant">format_list_bulleted</span>
          </button>
          <button class="glass-button p-1.5 rounded" :class="{ 'glass-active': editor?.isActive('orderedList') }" @click="editor?.chain().focus().toggleOrderedList().run()">
            <span class="material-symbols-outlined text-[18px] text-on-surface-variant">format_list_numbered</span>
          </button>
          <button class="glass-button p-1.5 rounded" :class="{ 'glass-active': editor?.isActive('blockquote') }" @click="editor?.chain().focus().toggleBlockquote().run()">
            <span class="material-symbols-outlined text-[18px] text-on-surface-variant">format_quote</span>
          </button>
          <button class="glass-button p-1.5 rounded" :class="{ 'glass-active': editor?.isActive('codeBlock') }" @click="editor?.chain().focus().toggleCodeBlock().run()">
            <span class="material-symbols-outlined text-[18px] text-on-surface-variant">code</span>
          </button>
          <div class="w-px h-4 bg-outline-variant/30 mx-1"></div>
          <button class="glass-button p-1.5 rounded" @click="addLink">
            <span class="material-symbols-outlined text-[18px] text-on-surface-variant">link</span>
          </button>
          <button class="glass-button p-1.5 rounded text-on-surface-variant relative overflow-hidden" @click="triggerImageUpload">
            <span class="material-symbols-outlined text-[18px]">image</span>
          </button>
          <input type="file" accept="image/*" class="hidden" ref="imageInput" @change="addImage" />
          <div class="w-px h-4 bg-outline-variant/30 mx-1"></div>
          <button class="glass-button p-1.5 rounded" @click="editor?.chain().focus().undo().run()">
            <span class="material-symbols-outlined text-[18px] text-on-surface-variant">undo</span>
          </button>
          <button class="glass-button p-1.5 rounded" @click="editor?.chain().focus().redo().run()">
            <span class="material-symbols-outlined text-[18px] text-on-surface-variant">redo</span>
          </button>
          <div class="ml-auto flex items-center gap-2 text-caption font-caption" :class="saved ? 'text-success-indicator' : 'text-on-surface-variant'">
            <span class="flex items-center gap-1">
              <span class="w-1.5 h-1.5 rounded-full" :class="saved ? 'bg-success-indicator' : 'bg-tertiary' + (saved ? '' : ' animate-pulse')" />
              {{ saved ? 'Saved' : 'Unsaved' }}
            </span>
          </div>
        </div>
        <!-- Editor Content -->
        <div class="flex-1 overflow-y-auto custom-scrollbar">
          <div class="max-w-3xl mx-auto py-12 px-8 min-h-full" ref="editorRef">
            <editor-content :editor="editor" class="prose-editor" />
          </div>
        </div>
      </div>
    </div>

    <!-- Right: Context & Links -->
    <div class="w-72 glass-panel border-l flex-shrink-0 hidden xl:flex flex-col bg-white/10 backdrop-blur-[40px] overflow-hidden">
      <div class="p-4 border-b border-glass-border-light/50">
        <span class="font-label-md text-label-md text-on-surface font-semibold flex items-center gap-2">
          <span class="material-symbols-outlined text-[18px]">info</span>
          Context &amp; Links
        </span>
      </div>
      <div class="p-4 flex-1 overflow-y-auto space-y-6">
        <div>
          <h3 class="font-caption text-caption text-on-surface-variant uppercase tracking-wider mb-3">Entities Mentioned</h3>
          <div class="flex flex-wrap gap-2">
            <span v-for="entity in currentNote.entities" :key="entity" class="glass-hover px-2.5 py-1 rounded-md bg-secondary-fixed/50 border border-secondary-fixed-dim/30 text-on-secondary-fixed-variant font-label-md text-label-md flex items-center gap-1 cursor-pointer">
              <span class="material-symbols-outlined text-[14px]">api</span>
              {{ entity }}
            </span>
          </div>
        </div>
        <div>
          <h3 class="font-caption text-caption text-on-surface-variant uppercase tracking-wider mb-3">Linked Issues</h3>
          <div class="space-y-2">
            <div v-for="issue in currentNote.linkedIssues" :key="issue.id" class="glass-hover p-3 rounded-lg bg-white/30 border border-glass-border-light/40 cursor-pointer">
              <div class="flex items-center gap-2 text-on-surface font-label-md text-label-md font-medium">
                <span class="material-symbols-outlined text-[16px]" :class="issue.type === 'bug' ? 'text-tertiary' : 'text-primary'">{{ issue.type === 'bug' ? 'bug_report' : 'task_alt' }}</span>
                {{ issue.id }}
              </div>
              <p class="text-caption font-caption text-on-surface-variant mt-1">{{ issue.description }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch } from "vue";
import { useEditor, EditorContent, BubbleMenu } from "@tiptap/vue-3";
import StarterKit from "@tiptap/starter-kit";
import Underline from "@tiptap/extension-underline";
import Link from "@tiptap/extension-link";
import Image from "@tiptap/extension-image";
import Placeholder from "@tiptap/extension-placeholder";
import Typography from "@tiptap/extension-typography";

interface NoteFile {
  name: string;
  active: boolean;
  content: string;
  entities: string[];
  linkedIssues: { id: string; type: string; description: string }[];
}

interface NoteFolder {
  name: string;
  expanded: boolean;
  active: boolean;
  children: NoteFile[];
}

const fileTree = ref<NoteFolder[]>([
  {
    name: "Sprint 42 Notes",
    expanded: true,
    active: true,
    children: [
      { name: "Authentication Flow Redesign", active: true, content: "", entities: ["AuthService", "Redis Cache"], linkedIssues: [{ id: "ENG-1402", type: "bug", description: "Token expiration causes silent failures." }, { id: "ENG-1510", type: "task", description: "Implement Redis caching layer for sessions." }] },
      { name: "API Rate Limiting", active: false, content: "", entities: ["RateLimiter", "NGINX"], linkedIssues: [{ id: "ENG-1511", type: "bug", description: "Rate limit exceeded on burst requests." }] },
    ],
  },
  { name: "Architecture Specs", expanded: false, active: false, children: [] },
  { name: "Meeting Minutes", expanded: false, active: false, children: [] },
]);

const defaultContent = `<h1>Authentication Flow Redesign</h1><p>The current implementation relies heavily on legacy token structures. We need to transition to a more robust OAuth 2.0 flow with strict PKCE requirements for all mobile and desktop clients.</p><h2>Key Objectives</h2><ul><li><p>Deprecate v1 authentication endpoints by Q3.</p></li><li><p>Implement strict JWT validation with short-lived access tokens (15m).</p></li><li><p>Establish robust refresh token rotation to mitigate token theft.</p></li></ul>`;

const saved = ref(true);
const editorRef = ref<HTMLDivElement>();
const imageInput = ref<HTMLInputElement>();

function getActiveFile(): NoteFile | null {
  for (const folder of fileTree.value) {
    for (const file of folder.children) {
      if (file.active) return file;
    }
  }
  return null;
}

const currentNote = computed(() => {
  return getActiveFile() || { name: "", content: "", entities: [], linkedIssues: [] };
});

const editor = useEditor({
  content: defaultContent,
  extensions: [
    StarterKit.configure({
      heading: { levels: [1, 2, 3] },
    }),
    Underline,
    Link.configure({ openOnClick: false }),
    Image.configure({ inline: true }),
    Placeholder.configure({ placeholder: "Start writing..." }),
    Typography,
  ],
  onUpdate: () => {
    saved.value = false;
    const file = getActiveFile();
    if (file && editor.value) {
      file.content = editor.value.getHTML();
    }
  },
  editorProps: {
    attributes: {
      class: "outline-none min-h-[300px]",
    },
  },
});

function selectFile(folder: NoteFolder, file: NoteFile) {
  for (const f of fileTree.value) {
    f.active = false;
    for (const c of f.children) c.active = false;
  }
  folder.active = true;
  file.active = true;
  if (editor.value) {
    editor.value.commands.setContent(file.content || defaultContent);
  }
}

function toggleFolder(item: NoteFolder) {
  item.expanded = !item.expanded;
}

function addFile(folder: NoteFolder) {
  const name = `note-${folder.children.length + 1}.md`;
  folder.children.push({ name, active: false, content: "", entities: [], linkedIssues: [] });
}

function createFolder() {
  fileTree.value.push({ name: "New Folder", expanded: true, active: false, children: [] });
}

function deleteFolder(idx: number) {
  fileTree.value.splice(idx, 1);
}

function deleteFile(folder: NoteFolder, idx: number) {
  folder.children.splice(idx, 1);
}

function addLink() {
  const url = window.prompt("Enter URL:");
  if (url && editor.value) {
    editor.value.chain().focus().setLink({ href: url }).run();
  }
}

function triggerImageUpload() {
  imageInput.value?.click();
}

function addImage(e: Event) {
  const input = e.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file || !editor.value) return;
  const reader = new FileReader();
  reader.onload = () => {
    if (typeof reader.result === "string") {
      editor.value?.chain().focus().setImage({ src: reader.result }).run();
    }
  };
  reader.readAsDataURL(file);
  input.value = "";
}

watch(saved, (v) => {
  if (!v) {
    const timer = setTimeout(() => { saved.value = true; }, 2000);
    return () => clearTimeout(timer);
  }
});

onBeforeUnmount(() => {
  editor.value?.destroy();
});
</script>

<style scoped>
:deep(.ProseMirror) {
  outline: none;
  min-height: 300px;
}
:deep(.ProseMirror p.is-editor-empty:first-child::before) {
  content: attr(data-placeholder);
  float: left;
  color: #adb5bd;
  pointer-events: none;
  height: 0;
}
:deep(.prose-editor h1) { font-family: 'Inter', sans-serif; font-weight: 700; color: #1a1c1d; font-size: 2.5rem; line-height: 1.2; margin-bottom: 1.5rem; letter-spacing: -0.04em; }
:deep(.prose-editor h2) { font-family: 'Inter', sans-serif; font-weight: 600; color: #1a1c1d; font-size: 1.75rem; line-height: 1.3; margin-top: 2rem; margin-bottom: 1rem; letter-spacing: -0.02em; }
:deep(.prose-editor h3) { font-family: 'Inter', sans-serif; font-weight: 600; color: #1a1c1d; font-size: 1.375rem; line-height: 1.4; margin-top: 1.5rem; margin-bottom: 0.75rem; letter-spacing: -0.01em; }
:deep(.prose-editor p) { font-family: 'Inter', sans-serif; font-weight: 400; color: #424656; font-size: 1.0625rem; line-height: 1.6; margin-bottom: 1.25rem; }
:deep(.prose-editor ul) { list-style-type: disc; padding-left: 1.5rem; color: #424656; margin-bottom: 1.25rem; }
:deep(.prose-editor ol) { list-style-type: decimal; padding-left: 1.5rem; color: #424656; margin-bottom: 1.25rem; }
:deep(.prose-editor li) { margin-bottom: 0.5rem; font-size: 1.0625rem; line-height: 1.6; }
:deep(.prose-editor blockquote) { border-left: 3px solid #c2c1ff; padding-left: 1rem; margin-left: 0; color: #6b6f82; font-style: italic; }
:deep(.prose-editor code) { background: #f1f2f5; border-radius: 4px; padding: 2px 6px; font-size: 0.9em; color: #d63384; }
:deep(.prose-editor pre) { background: #1a1c1d; border-radius: 8px; padding: 1rem; overflow-x: auto; margin-bottom: 1.25rem; }
:deep(.prose-editor pre code) { background: none; color: #e4e5e7; padding: 0; }
:deep(.prose-editor a) { color: #0050cb; text-decoration: underline; cursor: pointer; }
</style>
