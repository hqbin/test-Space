<template>
  <div class="flex h-[calc(100vh-64px)] -mx-margin-page overflow-hidden">
    <!-- Left: Search + File Tree -->
    <div class="flex-shrink-0 flex flex-col bg-white/5 backdrop-blur-[30px] overflow-hidden border-r border-glass-border-light/50 w-64 glass-panel">
      <div class="p-3 border-b border-glass-border-light/50">
        <div class="glass-input flex items-center gap-2 px-3 py-2 rounded-lg">
          <span class="material-symbols-outlined text-[14px] text-on-surface-variant">search</span>
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search notes..."
            class="bg-transparent border-none outline-none text-[12px] text-on-surface w-full"
            @input="onSearch"
          />
          <button v-if="searchQuery" class="glass-button p-0.5" @click="clearSearch">
            <span class="material-symbols-outlined text-[12px]">close</span>
          </button>
        </div>
      </div>
      <div class="px-3 py-1.5 border-b border-glass-border-light/50 flex justify-between items-center">
        <span class="font-label-md text-label-md text-on-surface font-semibold text-[12px]">Directory</span>
        <div class="flex gap-1">
          <button class="glass-button p-0.5" title="New Folder" @click="createFolder">
            <span class="material-symbols-outlined text-[14px]">create_new_folder</span>
          </button>
          <button class="glass-button p-0.5" title="New Note" @click="createNote">
            <span class="material-symbols-outlined text-[14px]">note_add</span>
          </button>
        </div>
      </div>
      <!-- Space selector dropdown -->
      <div class="px-2 py-1.5 border-b border-glass-border-light/30">
        <div class="relative" ref="spaceDropdownRef">
          <button class="w-full flex items-center justify-between gap-1 px-2 py-1 rounded-md text-[11px] glass-hover cursor-pointer transition-colors text-on-surface-variant" @click="showSpaceDropdown = !showSpaceDropdown">
            <span class="truncate font-medium">{{ spaces.find(s => s.id === selectedSpaceId)?.name || 'All Notes' }}</span>
            <span class="material-symbols-outlined text-[14px]">expand_more</span>
          </button>
          <div v-if="showSpaceDropdown" class="absolute left-0 right-0 top-full mt-1 bg-white rounded-lg shadow-xl border border-gray-200/80 z-50 overflow-hidden">
            <div class="py-1 max-h-[200px] overflow-y-auto">
              <div
                v-for="space in spaces"
                :key="space.id"
                class="flex items-center justify-between px-3 py-1.5 text-[11px] cursor-pointer transition-colors group"
                :class="selectedSpaceId === space.id ? 'bg-purple-100/60 text-secondary font-medium' : 'hover:bg-gray-50 text-on-surface-variant'"
                @click="selectSpace(space.id); showSpaceDropdown = false"
              >
                <span class="truncate flex-1">{{ space.name }}</span>
                <div class="flex items-center gap-1 opacity-0 group-hover:opacity-100">
                  <button class="p-0.5 rounded hover:bg-black/5" @click.stop="startRenameSpace(space)" title="Rename">
                    <span class="material-symbols-outlined text-[12px]">edit</span>
                  </button>
                  <button class="p-0.5 rounded hover:bg-red-50 text-red-400" @click.stop="confirmDeleteSpace(space)" title="Delete">
                    <span class="material-symbols-outlined text-[12px]">delete</span>
                  </button>
                </div>
              </div>
            </div>
            <div class="border-t border-gray-100 py-1">
              <button class="w-full flex items-center gap-1 px-3 py-1.5 text-[11px] text-on-surface-variant hover:bg-gray-50 transition-colors" @click="createSpace(); showSpaceDropdown = false">
                <span class="material-symbols-outlined text-[13px]">add</span> New Space
              </button>
            </div>
          </div>
        </div>
      </div>
      <div
        class="px-3 py-1 flex items-center gap-1.5 glass-hover cursor-pointer text-[12px]"
        :class="showFavorites ? 'bg-purple-100/60 text-secondary font-medium' : 'text-on-surface-variant'"
        @click="toggleFavorites"
      >
        <span class="material-symbols-outlined text-[13px]" :class="showFavorites ? 'text-secondary' : ''">star</span>
        <span>Favorites</span>
        <span class="ml-auto text-[10px] text-on-surface-variant/60">{{ favoriteNotes.length }}</span>
      </div>
      <div class="flex-1 overflow-y-auto p-2 custom-scrollbar">
        <!-- Favorites flat list -->
        <div v-if="showFavorites" class="space-y-0.5">
          <div class="px-2 py-0.5 text-[10px] text-on-surface-variant/50 uppercase tracking-wider font-medium mb-1">Favorites</div>
          <div v-for="note in favoriteNotes" :key="note.id" class="group">
            <div
              draggable="true"
              class="glass-hover flex items-center gap-1.5 px-2 py-0.5 rounded-md cursor-pointer transition-colors"
              :class="[selectedNoteId === note.id ? 'bg-purple-100/60 text-secondary font-medium' : 'text-on-surface-variant', highlightedNoteIds.has(note.id) ? 'bg-yellow-100/60 ring-1 ring-yellow-300/50' : '']"
              @click="selectNote(note)"
              @dragstart="onDragStart(note, $event)"
              @dragend="onDragEnd"
            >
              <span class="material-symbols-outlined text-[13px] text-secondary">description</span>
              <span class="font-body-md text-body-md text-[12px] flex-1 truncate">{{ note.title || 'Untitled' }}</span>
              <span class="material-symbols-outlined text-[12px] text-secondary">star</span>
              <button class="glass-button p-0.5 opacity-0 group-hover:opacity-100 rounded" title="Delete" @click.stop="confirmDeleteNote(note)">
                <span class="material-symbols-outlined text-[11px]">delete</span>
              </button>
            </div>
          </div>
          <div v-if="favoriteNotes.length === 0" class="text-[11px] text-on-surface-variant/40 px-2 py-2">No favorite notes yet</div>
        </div>

        <!-- Folder tree -->
        <template v-if="!showFavorites">
        <ul class="space-y-0.5">
          <li v-for="{ folder, depth } in flatFolders" :key="folder.id"
            :class="dragOverFolderId === folder.id ? 'bg-purple-100/50 rounded-lg ring-2 ring-purple-300/50' : ''"
            @dragover.prevent="onDragOver(folder.id)"
            @dragleave="onDragLeave"
            @drop="onDrop(folder.id)"
          >
            <div
              class="glass-hover flex items-center gap-1.5 px-2 py-1 rounded-md cursor-pointer transition-colors group relative"
              :style="{ paddingLeft: (8 + depth * 16) + 'px' }"
              :class="selectedFolderId === folder.id && !showFavorites ? 'bg-purple-100/60 text-secondary font-medium' : 'text-on-surface-variant'"
              :data-folder-id="folder.id"
              @click="selectFolder(folder.id)"
            >
              <span class="material-symbols-outlined text-[14px]">{{ expandedFolders[folder.id] ? 'folder_open' : 'folder' }}</span>
              <span class="font-body-md text-body-md text-[12px] flex-1 truncate">{{ folder.name }}</span>
              <button class="glass-button p-0.5 rounded opacity-0 group-hover:opacity-100" title="Add" @click.stop="openFolderAddDropdown(folder.id, $event)">
                <span class="material-symbols-outlined text-[13px]">add</span>
              </button>
              <button class="glass-button p-0.5 rounded opacity-0 group-hover:opacity-100" title="Rename" @click.stop="startRenameFolder(folder)">
                <span class="material-symbols-outlined text-[12px]">edit</span>
              </button>
              <button class="glass-button p-0.5 rounded opacity-0 group-hover:opacity-100" title="Delete" @click.stop="deleteFolder(folder.id)">
                <span class="material-symbols-outlined text-[12px]">delete</span>
              </button>
            </div>
            <ul v-if="expandedFolders[folder.id]" class="pl-5 space-y-0.5 mt-0.5 border-l border-glass-border-light/50 ml-3">
              <li v-for="note in getNotesByFolder(folder.id)" :key="note.id" class="group">
                <div
                  draggable="true"
                  class="glass-hover flex items-center gap-1.5 px-2 py-0.5 rounded-md cursor-pointer transition-colors"
                  :class="[selectedNoteId === note.id ? 'bg-purple-100/60 text-secondary font-medium' : 'text-on-surface-variant', highlightedNoteIds.has(note.id) ? 'bg-yellow-100/60 ring-1 ring-yellow-300/50' : '']"
                  @click="selectNote(note)"
              @dragstart="onDragStart(note, $event)"
              @dragend="onDragEnd"
                >
                  <span class="material-symbols-outlined text-[13px] text-secondary">description</span>
                  <span class="font-body-md text-body-md text-[12px] flex-1 truncate">{{ note.title || 'Untitled' }}</span>
                  <span v-if="note.isFavorite" class="material-symbols-outlined text-[12px] text-secondary">star</span>
                  <button class="glass-button p-0.5 opacity-0 group-hover:opacity-100 rounded" title="Delete" @click.stop="confirmDeleteNote(note)">
                    <span class="material-symbols-outlined text-[11px]">delete</span>
                  </button>
                </div>
              </li>
            </ul>
          </li>
        </ul>
        <div
          class="mt-3 pt-2 border-t border-glass-border-light/30"
          :class="{ 'bg-purple-100/50 rounded-lg ring-2 ring-purple-300/50': dragOverFolderId === '__uncategorized__' }"
          @dragover.prevent="onDragOver('__uncategorized__')"
          @dragleave="onDragLeave"
          @drop="onDrop(null)"
        >
          <div class="px-2 py-0.5 text-[10px] text-on-surface-variant/50 uppercase tracking-wider font-medium">Uncategorized</div>
          <div v-for="note in uncategorizedNotes" :key="note.id" class="group">
            <div
              draggable="true"
              class="glass-hover flex items-center gap-1.5 px-2 py-0.5 rounded-md cursor-pointer transition-colors"
              :class="[selectedNoteId === note.id ? 'bg-purple-100/60 text-secondary font-medium' : 'text-on-surface-variant', highlightedNoteIds.has(note.id) ? 'bg-yellow-100/60 ring-1 ring-yellow-300/50' : '']"
              @click="selectNote(note)"
              @dragstart="onDragStart(note, $event)"
              @dragend="onDragEnd"
            >
              <span class="material-symbols-outlined text-[13px] text-secondary">description</span>
              <span class="font-body-md text-body-md text-[12px] flex-1 truncate">{{ note.title || 'Untitled' }}</span>
              <button class="glass-button p-0.5 opacity-0 group-hover:opacity-100 rounded" title="Delete" @click.stop="confirmDeleteNote(note)">
                <span class="material-symbols-outlined text-[11px]">delete</span>
              </button>
            </div>
          </div>
        </div>
        </template>
      </div>
    </div>

    <!-- Center: TipTap Editor -->
    <div class="flex-1 flex flex-col overflow-hidden bg-transparent pt-4 px-4 lg:px-8">
      <!-- Empty state when no note selected -->
      <div v-if="!selectedNoteId" class="flex-1 glass-panel rounded-xl overflow-hidden flex items-center justify-center shadow-md">
        <div class="text-center">
          <span class="material-symbols-outlined text-[48px] text-on-surface-variant/30">note_add</span>
          <p class="font-body-md text-body-md text-on-surface-variant/50 mt-3">Select a note or create a new one</p>
        </div>
      </div>
      <div v-else class="flex-1 glass-panel rounded-xl overflow-hidden flex flex-col shadow-md">
        <div class="sticky top-0 z-10 bg-white/60 backdrop-blur-md border-b border-glass-border-light/30 px-4 py-2 flex items-center gap-2">
          <input
            v-model="noteTitle"
            placeholder="Note title..."
            class="flex-1 bg-transparent border-none outline-none font-headline-sm text-headline-sm text-on-surface font-semibold"
            @input="onTitleChange"
          />
          <div class="flex items-center gap-1">
            <button class="toolbar-btn !p-1" :class="{ 'toolbar-active': currentNoteData?.isFavorite }" title="Toggle Favorite" @click="toggleFavorite">
              <span class="material-symbols-outlined text-[20px]">{{ currentNoteData?.isFavorite ? 'star' : 'star_border' }}</span>
            </button>
            <div class="relative" ref="exportMenuRef">
              <button class="toolbar-btn !p-1" title="Export" @click="showExportMenu = !showExportMenu">
                <span class="material-symbols-outlined text-[20px]">file_download</span>
              </button>
              <div v-if="showExportMenu" class="absolute right-0 top-full mt-1 bg-white rounded-xl py-1 min-w-[220px] z-50 shadow-xl border border-gray-200/80 overflow-hidden" @click.stop>
                <button class="hover:bg-gray-100 w-full text-left px-4 py-2.5 text-[13px] text-gray-700 flex items-center gap-2 transition-colors" @click="exportAs('docx')">
                  <span class="material-symbols-outlined text-[16px] text-gray-500">description</span> Word (.docx)
                </button>
                <button class="hover:bg-gray-100 w-full text-left px-4 py-2.5 text-[13px] text-gray-700 flex items-center gap-2 transition-colors" @click="exportAs('md')">
                  <span class="material-symbols-outlined text-[16px] text-gray-500">code</span> Markdown (.md)
                </button>
                <button class="hover:bg-gray-100 w-full text-left px-4 py-2.5 text-[13px] text-gray-700 flex items-center gap-2 transition-colors" @click="exportAs('pdf')">
                  <span class="material-symbols-outlined text-[16px] text-gray-500">picture_as_pdf</span> PDF (.pdf)
                </button>
              </div>
            </div>
            <span class="text-[11px] font-caption flex items-center gap-1 ml-2" :class="saved ? 'text-success-indicator' : 'text-tertiary'">
              <span class="w-1.5 h-1.5 rounded-full" :class="saved ? 'bg-success-indicator' : 'bg-tertiary animate-pulse'" />
              {{ saved ? 'Saved' : 'Saving...' }}
            </span>
          </div>
        </div>
        <div class="bg-white/40 backdrop-blur-md border-b border-glass-border-light/30 px-4 py-2 flex items-center gap-1 flex-wrap">
          <button class="toolbar-btn" :class="{ 'toolbar-active': editor?.isActive('bold') }" @click="editor?.chain().focus().toggleBold().run()" title="Bold">
            <span class="material-symbols-outlined text-[20px]">format_bold</span>
          </button>
          <button class="toolbar-btn" :class="{ 'toolbar-active': editor?.isActive('italic') }" @click="editor?.chain().focus().toggleItalic().run()" title="Italic">
            <span class="material-symbols-outlined text-[20px]">format_italic</span>
          </button>
          <button class="toolbar-btn" :class="{ 'toolbar-active': editor?.isActive('underline') }" @click="editor?.chain().focus().toggleUnderline().run()" title="Underline">
            <span class="material-symbols-outlined text-[20px]">format_underlined</span>
          </button>
          <button class="toolbar-btn" :class="{ 'toolbar-active': editor?.isActive('strike') }" @click="editor?.chain().focus().toggleStrike().run()" title="Strikethrough">
            <span class="material-symbols-outlined text-[20px]">strikethrough_s</span>
          </button>
          <div class="w-px h-4 bg-outline-variant/30 mx-1"></div>
          <button class="toolbar-btn" :class="{ 'toolbar-active': editor?.isActive('heading', { level: 1 }) }" @click="editor?.chain().focus().toggleHeading({ level: 1 }).run()" title="Heading 1">
            <span class="text-[13px] font-bold px-1">H1</span>
          </button>
          <button class="toolbar-btn" :class="{ 'toolbar-active': editor?.isActive('heading', { level: 2 }) }" @click="editor?.chain().focus().toggleHeading({ level: 2 }).run()" title="Heading 2">
            <span class="text-[13px] font-bold px-1">H2</span>
          </button>
          <button class="toolbar-btn" :class="{ 'toolbar-active': editor?.isActive('heading', { level: 3 }) }" @click="editor?.chain().focus().toggleHeading({ level: 3 }).run()" title="Heading 3">
            <span class="text-[13px] font-bold px-1">H3</span>
          </button>
          <div class="w-px h-4 bg-outline-variant/30 mx-1"></div>
          <button class="toolbar-btn" :class="{ 'toolbar-active': editor?.isActive('bulletList') }" @click="editor?.chain().focus().toggleBulletList().run()" title="Bullet List">
            <span class="material-symbols-outlined text-[20px]">format_list_bulleted</span>
          </button>
          <button class="toolbar-btn" :class="{ 'toolbar-active': editor?.isActive('orderedList') }" @click="editor?.chain().focus().toggleOrderedList().run()" title="Ordered List">
            <span class="material-symbols-outlined text-[20px]">format_list_numbered</span>
          </button>
          <button class="toolbar-btn" :class="{ 'toolbar-active': editor?.isActive('blockquote') }" @click="editor?.chain().focus().toggleBlockquote().run()" title="Blockquote">
            <span class="material-symbols-outlined text-[20px]">format_quote</span>
          </button>
          <button class="toolbar-btn" @click="showLinkDialog = true" title="Insert Link">
            <span class="material-symbols-outlined text-[20px]">link</span>
          </button>
          <button class="toolbar-btn text-on-surface-variant relative overflow-hidden" @click="triggerImageUpload" title="Insert Image">
            <span class="material-symbols-outlined text-[20px]">image</span>
          </button>
          <input type="file" accept="image/*" class="hidden" ref="imageInput" @change="addImage" />
          <div class="w-px h-4 bg-outline-variant/30 mx-1"></div>
          <div class="w-px h-4 bg-outline-variant/30 mx-1"></div>
          <button class="toolbar-btn" @click="editor?.chain().focus().undo().run()" title="Undo">
            <span class="material-symbols-outlined text-[20px]">undo</span>
          </button>
          <button class="toolbar-btn" @click="editor?.chain().focus().redo().run()" title="Redo">
            <span class="material-symbols-outlined text-[20px]">redo</span>
          </button>
        </div>
        <div class="flex-1 overflow-y-auto custom-scrollbar" ref="editorScrollRef">
          <div class="max-w-[850px] mx-auto py-8 px-6 min-h-full border border-glass-border-light/30 rounded-lg bg-white/30" ref="editorRef">
            <editor-content :editor="editor" class="prose-editor" />
          </div>
        </div>
      </div>
    </div>

    <!-- TOC Toggle Button (semi-transparent, right side) -->
    <button
      v-if="selectedNoteId && !showToc"
      class="fixed right-0 top-1/2 -translate-y-1/2 z-50 bg-white/40 backdrop-blur-md border border-white/60 rounded-l-md px-1.5 py-4 shadow-lg hover:bg-white/60 hover:pr-2 transition-all opacity-[85%]"
      title="目录"
      @click="showToc = true"
    >
      <span class="material-symbols-outlined text-[20px] text-on-surface-variant">toc</span>
    </button>

    <!-- Right: Table of Contents (slide panel) -->
    <Teleport to="body">
      <div v-if="showToc" class="fixed inset-0 z-20" @click.self="showToc = false">
        <div class="absolute right-0 top-0 bottom-0 w-72 flex flex-col bg-white/20 backdrop-blur-[30px] border-l border-white/30 overflow-hidden shadow-2xl animate-toc-in opacity-[85%]">
          <div class="p-4 border-b border-white/20 flex items-center justify-between">
            <span class="font-label-md text-label-md text-on-surface font-semibold flex items-center gap-2">
              <span class="material-symbols-outlined text-[18px]">toc</span>
              Table of Contents
            </span>
            <button class="glass-button p-1 rounded hover:bg-white/20 transition-colors" @click="showToc = false">
              <span class="material-symbols-outlined text-[16px]">close</span>
            </button>
          </div>
          <div class="flex-1 overflow-y-auto custom-scrollbar p-4">
            <div v-if="tocItems.length === 0" class="text-caption text-on-surface-variant/60 text-[12px]">
              No headings found in this note
            </div>
            <div class="space-y-0.5">
              <div
                v-for="item in visibleTocItems"
                :key="item.index"
                class="glass-hover px-2.5 py-1.5 rounded-md cursor-pointer text-[12px] flex items-center gap-1 transition-all duration-150"
                :class="activeHeadingIndex === item.index ? 'bg-purple-100/60 text-secondary font-medium' : 'text-on-surface-variant'"
                :style="{ paddingLeft: (8 + item.depth * 16) + 'px' }"
                @click="item.canExpand ? toggleTocNode(item.index) : scrollToHeading(item.index)"
              >
                <button v-if="item.canExpand && tocCollapsed.has(item.index)" class="flex-shrink-0 p-0.5 rounded hover:bg-black/5 transition-transform duration-200" @click.stop="toggleTocNode(item.index)">
                  <span class="material-symbols-outlined text-[14px]">chevron_right</span>
                </button>
                <span v-else class="w-5 flex-shrink-0"></span>
                <span class="text-[10px] text-on-surface-variant/40 font-mono flex-shrink-0">H{{ item.level }}</span>
                <span class="truncate font-bold">{{ item.text }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Link Dialog -->
    <Teleport to="body">
      <div v-if="showLinkDialog" class="fixed inset-0 z-50 flex items-center justify-center bg-black/20 backdrop-blur-sm" @click.self="showLinkDialog = false">
        <div class="glass-panel rounded-2xl p-6 w-96 bg-white/60" @click.stop>
          <h3 class="font-label-md text-label-md text-on-surface font-semibold mb-4">Insert Link</h3>
          <div class="space-y-3">
            <div>
              <label class="text-[12px] text-on-surface-variant block mb-1">URL</label>
              <input
                v-model="linkUrl"
                type="url"
                placeholder="https://example.com"
                class="glass-input w-full px-3 py-2 rounded-lg text-[14px] outline-none"
                @keydown.enter="confirmLink"
              />
            </div>
            <div>
              <label class="text-[12px] text-on-surface-variant block mb-1">Display Text (optional)</label>
              <input
                v-model="linkText"
                type="text"
                placeholder="Selected text or custom"
                class="glass-input w-full px-3 py-2 rounded-lg text-[14px] outline-none"
                @keydown.enter="confirmLink"
              />
            </div>
          </div>
          <div class="flex justify-end gap-2 mt-6">
            <button class="glass-button px-4 py-2 rounded-full text-[13px]" @click="showLinkDialog = false">Cancel</button>
            <button class="glass-button px-4 py-2 rounded-full text-[13px] glass-active" @click="confirmLink" :disabled="!linkUrl.trim()">Apply</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Rename Dialog -->
    <Teleport to="body">
      <div v-if="renameTarget" class="fixed inset-0 z-50 flex items-center justify-center bg-black/20 backdrop-blur-sm" @click.self="renameTarget = null">
        <div class="glass-panel rounded-2xl p-6 w-80 bg-white/60">
          <h3 class="font-label-md text-label-md text-on-surface font-semibold mb-4">Rename</h3>
          <input
            v-model="renameValue"
            class="glass-input w-full px-3 py-2 rounded-lg text-[14px] outline-none mb-4"
            @keydown.enter="confirmRename"
            ref="renameInputRef"
          />
          <div class="flex justify-end gap-2">
            <button class="glass-button px-4 py-2 rounded-full text-[13px]" @click="renameTarget = null">Cancel</button>
            <button class="glass-button px-4 py-2 rounded-full text-[13px] glass-active" @click="confirmRename">Rename</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Folder Add Dropdown (Teleported) -->
    <Teleport to="body">
      <div v-if="folderAddDropdownId" ref="folderAddDropdownRef" class="fixed z-50" :style="{ left: folderAddDropdownPos.x + 'px', top: folderAddDropdownPos.y + 'px' }">
        <div class="bg-white rounded-lg shadow-xl border border-gray-200/80 overflow-hidden min-w-[140px]">
          <button class="w-full flex items-center gap-2 px-3 py-2 text-[12px] hover:bg-gray-50 transition-colors text-left" @click="createSubFolder(folderAddDropdownId!)">
            <span class="material-symbols-outlined text-[14px]">create_new_folder</span> New Folder
          </button>
          <button class="w-full flex items-center gap-2 px-3 py-2 text-[12px] hover:bg-gray-50 transition-colors text-left" @click="addNoteToFolder(folderAddDropdownId!)">
            <span class="material-symbols-outlined text-[14px]">note_add</span> New Note
          </button>
        </div>
      </div>
    </Teleport>

    <!-- Delete Space Confirmation -->
    <Teleport to="body">
      <div v-if="deleteSpaceTarget" class="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm" @click.self="deleteSpaceTarget = null">
        <div class="glass-panel rounded-2xl p-6 w-80 bg-white/80">
          <h3 class="font-label-md text-label-md text-on-surface font-semibold mb-2">Delete Space</h3>
          <p class="text-[13px] text-on-surface-variant mb-6">Are you sure you want to delete "<strong>{{ deleteSpaceTarget.name }}</strong>"? All folders and notes inside will be permanently removed.</p>
          <div class="flex justify-end gap-2">
            <button class="glass-button px-4 py-2 rounded-full text-[13px]" @click="deleteSpaceTarget = null">Cancel</button>
            <button class="px-4 py-2 rounded-full text-[13px] bg-red-500 text-white hover:bg-red-600 transition-colors" @click="doDeleteSpace">Delete</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Delete Folder Confirmation -->
    <Teleport to="body">
      <div v-if="deleteFolderTarget" class="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm" @click.self="deleteFolderTarget = null">
        <div class="glass-panel rounded-2xl p-6 w-80 bg-white/80">
          <h3 class="font-label-md text-label-md text-on-surface font-semibold mb-2">Delete Folder</h3>
          <p class="text-[13px] text-on-surface-variant mb-6">Delete "<strong>{{ deleteFolderTarget.name }}</strong>"? Notes inside will be moved to Uncategorized.</p>
          <div class="flex justify-end gap-2">
            <button class="glass-button px-4 py-2 rounded-full text-[13px]" @click="deleteFolderTarget = null">Cancel</button>
            <button class="px-4 py-2 rounded-full text-[13px] bg-red-500 text-white hover:bg-red-600 transition-colors" @click="doDeleteFolder">Delete</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Delete Note Confirmation -->
    <Teleport to="body">
      <div v-if="deleteNoteTarget" class="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm" @click.self="deleteNoteTarget = null">
        <div class="glass-panel rounded-2xl p-6 w-80 bg-white/80">
          <h3 class="font-label-md text-label-md text-on-surface font-semibold mb-2">Delete Note</h3>
          <p class="text-[13px] text-on-surface-variant mb-6">Delete "<strong>{{ deleteNoteTarget.title || 'Untitled' }}</strong>"? This cannot be undone.</p>
          <div class="flex justify-end gap-2">
            <button class="glass-button px-4 py-2 rounded-full text-[13px]" @click="deleteNoteTarget = null">Cancel</button>
            <button class="px-4 py-2 rounded-full text-[13px] bg-red-500 text-white hover:bg-red-600 transition-colors" @click="doDeleteNote">Delete</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from "vue";
import { useEditor, EditorContent } from "@tiptap/vue-3";
import StarterKit from "@tiptap/starter-kit";
import Underline from "@tiptap/extension-underline";
import LinkExtension from "@tiptap/extension-link";
import Image from "@tiptap/extension-image";
import Placeholder from "@tiptap/extension-placeholder";
import Typography from "@tiptap/extension-typography";

import TurndownService from "turndown";
import { toPng } from "html-to-image";
import { jsPDF } from "jspdf";
import { Document, Packer, Paragraph, TextRun, HeadingLevel, ExternalHyperlink } from "docx";
import type { NoteSpace, NoteFolder, NoteItem, NoteVersion } from "@/types";

import * as db from "@/services/database";
const turndown = new TurndownService({ headingStyle: "atx", codeBlockStyle: "fenced" });

// ── State ────────────────────────────────────────────────────

const spaces = ref<NoteSpace[]>([])
const selectedSpaceId = ref<string | null>(null)
const folders = ref<NoteFolder[]>([])
const notes = ref<NoteItem[]>([])
const selectedFolderId = ref<string | null>(null)
const selectedNoteId = ref<string | null>(null)
const noteVersions = ref<NoteVersion[]>([])
const expandedFolders = ref<Record<string, boolean>>({})
const showFavorites = ref(false)
const searchQuery = ref("")
const searchResults = ref<NoteItem[]>([])
const saved = ref(true)
const noteTitle = ref("")
const renameTarget = ref<{ type: 'space' | 'folder' | 'note'; id: string; name: string } | null>(null)
const renameValue = ref("")
const renameInputRef = ref<HTMLInputElement>()
const editorScrollRef = ref<HTMLDivElement>()
const editorRef = ref<HTMLDivElement>()
const imageInput = ref<HTMLInputElement>()
const showLinkDialog = ref(false)
const linkUrl = ref("")
const linkText = ref("")
const showExportMenu = ref(false)
const exportMenuRef = ref<HTMLDivElement>()
const showSpaceDropdown = ref(false)
const spaceDropdownRef = ref<HTMLDivElement>()
const folderAddDropdownId = ref<string | null>(null)
const folderAddDropdownPos = ref<{ x: number; y: number }>({ x: 0, y: 0 })
const folderAddDropdownRef = ref<HTMLDivElement>()
const deleteSpaceTarget = ref<NoteSpace | null>(null)
const deleteFolderTarget = ref<NoteFolder | null>(null)
const deleteNoteTarget = ref<NoteItem | null>(null)
const activeHeadingIndex = ref(-1)
const showToc = ref(false)
const tocCollapsed = ref<Set<number>>(new Set())

let dragNoteId: string | null = null
const dragOverFolderId = ref<string | null>(null)

let saveTimer: ReturnType<typeof setTimeout> | null = null
let versionTimer: ReturnType<typeof setTimeout> | null = null


// ── Computed ─────────────────────────────────────────────────

const currentNoteData = computed(() => {
  if (!selectedNoteId.value) return null
  return notes.value.find(n => n.id === selectedNoteId.value) || null
})

const favoriteNotes = computed(() => notes.value.filter(n => n.isFavorite))

const spaceFolders = computed(() => {
  if (!selectedSpaceId.value) return folders.value.filter(f => !f.spaceId)
  return folders.value.filter(f => f.spaceId === selectedSpaceId.value)
})

const flatFolders = computed(() => {
  const result: { folder: NoteFolder; depth: number }[] = []
  function walk(parentId: string | null, depth: number) {
    const children = spaceFolders.value.filter(f => f.parentId === parentId)
    for (const folder of children) {
      result.push({ folder, depth })
      if (expandedFolders.value[folder.id]) {
        walk(folder.id, depth + 1)
      }
    }
  }
  walk(null, 0)
  return result
})

function getNotesByFolder(folderId: string): NoteItem[] {
  if (searchQuery.value && searchResults.value.length > 0) {
    return searchResults.value.filter(n => n.folderId === folderId)
  }
  if (showFavorites.value) {
    return favoriteNotes.value.filter(n => n.folderId === folderId)
  }
  return notes.value.filter(n => n.folderId === folderId)
}

const uncategorizedNotes = computed(() => {
  if (searchQuery.value) return []
  return notes.value.filter(n => !n.folderId)
})

const highlightedNoteIds = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return new Set<string>()
  return new Set(notes.value.filter(n =>
    n.title.toLowerCase().includes(q) || n.content.toLowerCase().includes(q)
  ).map(n => n.id))
})

interface TocNode { level: number; text: string; index: number; children: TocNode[] }

function buildTocTree(items: { level: number; text: string }[]): TocNode[] {
  const root: TocNode[] = []
  const path: TocNode[] = []
  for (let i = 0; i < items.length; i++) {
    const item = items[i]
    const node: TocNode = { level: item.level, text: item.text, index: i, children: [] }
    while (path.length > 0 && path[path.length - 1].level >= item.level) path.pop()
    if (path.length > 0) path[path.length - 1].children.push(node)
    else root.push(node)
    path.push(node)
  }
  return root
}

// ── Data Loading ─────────────────────────────────────────────

async function loadData() {
  try {
    spaces.value = await db.loadNoteSpaces()
    folders.value = await db.loadNoteFolders()
    notes.value = await db.loadNotes()
    if (spaces.value.length > 0 && !selectedSpaceId.value) {
      selectedSpaceId.value = spaces.value[0].id
    }
    for (const f of folders.value) {
      expandedFolders.value[f.id] = true
    }
  } catch (e) {
    console.error('Failed to load notes:', e)
  }
}

// ── Space Management ─────────────────────────────────────────

async function createSpace() {
  const id = crypto.randomUUID()
  const name = "New Space"
  await db.saveNoteSpace({ id, name })
  const space: NoteSpace = { id, name, sortOrder: spaces.value.length, createdAt: new Date().toISOString(), updatedAt: new Date().toISOString() }
  spaces.value.push(space)
  selectedSpaceId.value = id
}

function selectSpace(id: string) {
  selectedSpaceId.value = id
  selectedFolderId.value = null
  showFavorites.value = false
  searchQuery.value = ""
  searchResults.value = []
}

function startRenameSpace(space: NoteSpace) {
  renameTarget.value = { type: 'space', id: space.id, name: space.name }
  renameValue.value = space.name
  nextTick(() => renameInputRef.value?.focus())
}

function confirmDeleteSpace(space: NoteSpace) {
  deleteSpaceTarget.value = space
  showSpaceDropdown.value = false
}

async function doDeleteSpace() {
  if (!deleteSpaceTarget.value) return
  const id = deleteSpaceTarget.value.id
  deleteSpaceTarget.value = null
  await db.deleteNoteSpace(id)
  spaces.value = spaces.value.filter(s => s.id !== id)
  folders.value = await db.loadNoteFolders()
  notes.value = await db.loadNotes()
  if (selectedSpaceId.value === id) {
    selectedSpaceId.value = spaces.value.length > 0 ? spaces.value[0].id : null
  }
}

async function deleteSpace(id: string) {
  await db.deleteNoteSpace(id)
  spaces.value = spaces.value.filter(s => s.id !== id)
  folders.value = await db.loadNoteFolders()
  notes.value = await db.loadNotes()
  if (selectedSpaceId.value === id) {
    selectedSpaceId.value = spaces.value.length > 0 ? spaces.value[0].id : null
  }
}

// ── Folder Management ────────────────────────────────────────

async function createFolder() {
  const id = crypto.randomUUID()
  const parentId = selectedFolderId.value || null
  const spaceId = selectedSpaceId.value || null
  await db.saveNoteFolder({ id, name: "New Folder", parentId, spaceId })
  const folder: NoteFolder = { id, spaceId, name: "New Folder", parentId, sortOrder: folders.value.length, createdAt: new Date().toISOString(), updatedAt: new Date().toISOString() }
  folders.value.push(folder)
  expandedFolders.value[id] = true
}

async function createSubFolder(parentId: string) {
  const id = crypto.randomUUID()
  const spaceId = selectedSpaceId.value || null
  await db.saveNoteFolder({ id, name: "New Folder", parentId, spaceId })
  const folder: NoteFolder = { id, spaceId, name: "New Folder", parentId, sortOrder: folders.value.length, createdAt: new Date().toISOString(), updatedAt: new Date().toISOString() }
  folders.value.push(folder)
  expandedFolders.value[id] = true
  expandedFolders.value[parentId] = true
  folderAddDropdownId.value = null
}

function openFolderAddDropdown(folderId: string, event: MouseEvent) {
  if (folderAddDropdownId.value === folderId) {
    folderAddDropdownId.value = null
    return
  }
  const rect = (event.currentTarget as HTMLElement).getBoundingClientRect()
  folderAddDropdownPos.value = { x: rect.right - 140, y: rect.bottom + 4 }
  folderAddDropdownId.value = folderId
}

function startRenameFolder(folder: NoteFolder) {
  renameTarget.value = { type: 'folder', id: folder.id, name: folder.name }
  renameValue.value = folder.name
  nextTick(() => renameInputRef.value?.focus())
}

async function confirmRename() {
  if (!renameTarget.value || !renameValue.value.trim()) {
    renameTarget.value = null
    return
  }
  const { type, id } = renameTarget.value
  const name = renameValue.value.trim()
  if (type === 'space') {
    await db.renameNoteSpace(id, name)
    const s = spaces.value.find(s => s.id === id)
    if (s) s.name = name
  } else if (type === 'folder') {
    await db.renameNoteFolder(id, name)
    const f = folders.value.find(f => f.id === id)
    if (f) f.name = name
  }
  renameTarget.value = null
}

async function deleteFolder(id: string) {
  const folder = folders.value.find(f => f.id === id)
  if (folder) {
    deleteFolderTarget.value = folder
  }
}

async function doDeleteFolder() {
  if (!deleteFolderTarget.value) return
  const id = deleteFolderTarget.value.id
  deleteFolderTarget.value = null
  await db.deleteNoteFolder(id)
  folders.value = folders.value.filter(f => f.id !== id)
  notes.value = await db.loadNotes()
  if (selectedFolderId.value === id) selectedFolderId.value = null
}

function selectFolder(id: string) {
  showFavorites.value = false
  searchQuery.value = ""
  searchResults.value = []
  selectedFolderId.value = id
  expandedFolders.value[id] = !expandedFolders.value[id]
}

function toggleFavorites() {
  showFavorites.value = !showFavorites.value
  searchQuery.value = ""
  searchResults.value = []
  if (showFavorites.value) selectedFolderId.value = null
}

// ── Drag & Drop ──────────────────────────────────────────────

function onDragStart(note: NoteItem, event: DragEvent) {
  dragNoteId = note.id
  event.dataTransfer?.setData('text/plain', note.id)
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move'
  }
}

function onDragEnd() {
  dragNoteId = null
  dragOverFolderId.value = null
}

function onDragOver(folderId: string | null) {
  dragOverFolderId.value = folderId
}

function onDragLeave() {
  dragOverFolderId.value = null
}

async function onDrop(targetFolderId: string | null) {
  dragOverFolderId.value = null
  if (!dragNoteId) return
  const note = notes.value.find(n => n.id === dragNoteId)
  if (!note) return
  const newFolderId = targetFolderId === '__uncategorized__' ? null : targetFolderId
  if (note.folderId === newFolderId) { dragNoteId = null; return }
  note.folderId = newFolderId
  note.updatedAt = new Date().toISOString()
  await db.saveNote(note)
  dragNoteId = null
}

// ── Note Management ──────────────────────────────────────────

async function createNote() {
  const id = crypto.randomUUID()
  const now = new Date().toISOString()
  const note: NoteItem = { id, folderId: null, title: "Untitled", content: "", tags: [], isFavorite: false, createdAt: now, updatedAt: now }
  await db.saveNote(note)
  notes.value.unshift(note)
  selectNoteById(note.id, "")
}

async function addNoteToFolder(folderId: string) {
  const id = crypto.randomUUID()
  const now = new Date().toISOString()
  const note: NoteItem = { id, folderId, title: "Untitled", content: "", tags: [], isFavorite: false, createdAt: now, updatedAt: now }
  await db.saveNote(note)
  notes.value.unshift(note)
  selectNoteById(note.id, "")
}

function selectNoteById(id: string, content: string) {
  selectedNoteId.value = id
  noteTitle.value = "Untitled"
  if (editor.value) {
    editor.value.commands.setContent(content)
  }
  saved.value = true
}

async function selectNote(note: NoteItem) {
  if (saveTimer) { clearTimeout(saveTimer); saveTimer = null }
  if (versionTimer) { clearTimeout(versionTimer); versionTimer = null }

  if (selectedNoteId.value && currentNoteData.value && !saved.value) {
    await saveCurrentNote()
  }

  selectedNoteId.value = note.id
  noteTitle.value = note.title
  if (editor.value) {
    editor.value.commands.setContent(note.content || "")
  }
  saved.value = true

  try {
    noteVersions.value = await db.loadNoteVersions(note.id)
  } catch { noteVersions.value = [] }
}

async function saveCurrentNote() {
  if (!selectedNoteId.value || !currentNoteData.value) return
  const note = currentNoteData.value
  note.title = noteTitle.value || "Untitled"
  if (editor.value) {
    note.content = editor.value.getHTML()
  }
  await db.saveNote(note)
  saved.value = true
}

// ── Search ────────────────────────────────────────────────────

let searchDebounce: ReturnType<typeof setTimeout> | null = null

function onSearch() {
  if (searchDebounce) clearTimeout(searchDebounce)
  searchDebounce = setTimeout(async () => {
    const q = searchQuery.value.trim()
    if (!q) {
      searchResults.value = []
      // Restore folder expanded states (don't auto-collapse, just leave as-is)
      return
    }
    try {
      searchResults.value = await db.searchNotes(q)
    } catch {
      searchResults.value = notes.value.filter(n =>
        n.title.toLowerCase().includes(q.toLowerCase()) ||
        n.content.toLowerCase().includes(q.toLowerCase())
      )
    }
    // Auto-expand folders containing search results
    for (const f of folders.value) {
      const hasMatch = searchResults.value.some(n => n.folderId === f.id)
      if (hasMatch) expandedFolders.value[f.id] = true
    }
  }, 300)
}

function clearSearch() {
  searchQuery.value = ""
  searchResults.value = []
}

// ── Delete Note ──────────────────────────────────────────────

async function confirmDeleteNote(note: NoteItem) {
  deleteNoteTarget.value = note
}

async function doDeleteNote() {
  if (!deleteNoteTarget.value) return
  const id = deleteNoteTarget.value.id
  deleteNoteTarget.value = null
  await db.deleteNote(id)
  notes.value = notes.value.filter(n => n.id !== id)
  if (selectedNoteId.value === id) {
    selectedNoteId.value = null
    noteTitle.value = ""
    if (editor.value) editor.value.commands.setContent("")
  }
}

// ── Favorite ──────────────────────────────────────────────────

async function toggleFavorite() {
  if (!selectedNoteId.value) return
  const nowFav = await db.toggleNoteFavorite(selectedNoteId.value)
  const note = notes.value.find(n => n.id === selectedNoteId.value)
  if (note) note.isFavorite = nowFav
}

// ── Auto Save (1.5s debounce, real-time) ──────────────────────

function triggerSave() {
  saved.value = false
  if (saveTimer) clearTimeout(saveTimer)
  saveTimer = setTimeout(async () => {
    await saveCurrentNote()
    if (versionTimer) clearTimeout(versionTimer)
    versionTimer = setTimeout(async () => {
      if (selectedNoteId.value && editor.value) {
        await db.saveNoteVersion(selectedNoteId.value, editor.value.getHTML())
        noteVersions.value = await db.loadNoteVersions(selectedNoteId.value)
      }
    }, 30000)
  }, 1500)
}

function onTitleChange() {
  saved.value = false
  triggerSave()
}

// ── Link Dialog ───────────────────────────────────────────────

function confirmLink() {
  let url = linkUrl.value.trim()
  if (!url || !editor.value) return
  if (!/^https?:\/\//i.test(url)) {
    url = 'https://' + url
  }
  const text = linkText.value.trim()
  const displayText = text || url
  editor.value.chain().focus().insertContent(
    `<a href="${url}" target="_blank" rel="noopener noreferrer">${displayText}</a>`
  ).run()
  showLinkDialog.value = false
  linkUrl.value = ""
  linkText.value = ""
}

// ── Table of Contents ─────────────────────────────────────────

function toggleTocNode(idx: number) {
  const s = new Set(tocCollapsed.value)
  if (s.has(idx)) s.delete(idx)
  else s.add(idx)
  tocCollapsed.value = s
}

function scrollToHeading(idx: number) {
  if (!editor.value) return
  activeHeadingIndex.value = idx
  let pos = 0
  let count = 0
  editor.value.state.doc.forEach((node: any, offset: number) => {
    if (node.type.name === 'heading') {
      if (count === idx) {
        pos = offset
        return false
      }
      count++
    }
  })
  if (pos > 0) {
    const $pos = editor.value.state.doc.resolve(pos)
    const dom = editor.value.view.domAtPos($pos.pos)
    if (dom.node instanceof HTMLElement || (dom.node instanceof Text && dom.node.parentElement)) {
      const el = dom.node instanceof HTMLElement ? dom.node : dom.node.parentElement!
      el.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }
}

// ── Export ────────────────────────────────────────────────────

function parseInline(node: ChildNode): (TextRun | ExternalHyperlink)[] {
  const runs: (TextRun | ExternalHyperlink)[] = []
  for (const child of Array.from(node.childNodes)) {
    if (child.nodeType === Node.TEXT_NODE) {
      runs.push(new TextRun({ text: child.textContent || '', font: 'Calibri' }))
    } else if (child.nodeType === Node.ELEMENT_NODE) {
      const el = child as HTMLElement
      const tag = el.tagName.toLowerCase()
      if (tag === 'a') {
        const href = el.getAttribute('href') || ''
        runs.push(new ExternalHyperlink({ children: [new TextRun({ text: el.textContent || href, style: 'Hyperlink', font: 'Calibri' })], link: href }))
      } else if (tag === 'strong' || tag === 'b') {
        runs.push(new TextRun({ text: el.textContent || '', bold: true, font: 'Calibri' }))
      } else if (tag === 'em' || tag === 'i') {
        runs.push(new TextRun({ text: el.textContent || '', italics: true, font: 'Calibri' }))
      } else if (tag === 'code') {
        runs.push(new TextRun({ text: el.textContent || '', font: 'Consolas', size: 20, shading: { fill: 'f1f2f5' } }))
      } else if (tag === 'u') {
        runs.push(new TextRun({ text: el.textContent || '', underline: {}, font: 'Calibri' }))
      } else if (tag === 's' || tag === 'del') {
        runs.push(new TextRun({ text: el.textContent || '', strike: true, font: 'Calibri' }))
      } else {
        runs.push(...parseInline(el))
      }
    }
  }
  return runs
}

function htmlToDocxChildren(html: string): Paragraph[] {
  const parser = new DOMParser()
  const doc = parser.parseFromString(html, 'text/html')
  const result: Paragraph[] = []

  for (const node of Array.from(doc.body.childNodes)) {
    if (node.nodeType !== Node.ELEMENT_NODE) continue
    const el = node as HTMLElement
    const tag = el.tagName.toLowerCase()

    if (tag === 'h1') {
      result.push(new Paragraph({ heading: HeadingLevel.HEADING_1, children: parseInline(node), spacing: { after: 200 } }))
    } else if (tag === 'h2') {
      result.push(new Paragraph({ heading: HeadingLevel.HEADING_2, children: parseInline(node), spacing: { after: 200 } }))
    } else if (tag === 'h3') {
      result.push(new Paragraph({ heading: HeadingLevel.HEADING_3, children: parseInline(node), spacing: { after: 200 } }))
    } else if (tag === 'p') {
      result.push(new Paragraph({ children: parseInline(node), spacing: { after: 200 } }))
    } else if (tag === 'blockquote') {
      for (const child of Array.from(el.childNodes)) {
        if (child.nodeType === Node.ELEMENT_NODE) {
          result.push(new Paragraph({ children: parseInline(child), indent: { left: 720 }, spacing: { after: 200 } }))
        }
      }
    } else if (tag === 'ul') {
      for (const li of Array.from(el.querySelectorAll('li'))) {
        result.push(new Paragraph({ children: [new TextRun({ text: '• ', font: 'Calibri' }), ...parseInline(li)], indent: { left: 720 }, spacing: { after: 100 } }))
      }
    } else if (tag === 'ol') {
      let idx = 1
      for (const li of Array.from(el.querySelectorAll('li'))) {
        result.push(new Paragraph({ children: [new TextRun({ text: `${idx}. `, font: 'Calibri' }), ...parseInline(li)], indent: { left: 720 }, spacing: { after: 100 } }))
        idx++
      }
    } else if (tag === 'hr') {
      result.push(new Paragraph({ children: [], thematicBreak: true }))
    } else {
      result.push(new Paragraph({ children: parseInline(node), spacing: { after: 200 } }))
    }
  }
  return result
}

async function exportAs(format: 'docx' | 'md' | 'pdf') {
  showExportMenu.value = false
  if (!editor.value || !currentNoteData.value) return

  const title = currentNoteData.value.title || 'Untitled'
  const html = editor.value.getHTML()

  if (format === 'pdf') {
    try {
      const iframe = document.createElement('iframe')
      iframe.style.cssText = 'position:fixed;left:-9999px;top:0;width:800px;height:600px;border:none;'
      document.body.appendChild(iframe)
      const doc = iframe.contentDocument!
      doc.open()
      doc.write(`<!DOCTYPE html><html><head><meta charset="utf-8"><style>
        body{font-family:Inter,-apple-system,sans-serif;max-width:720px;margin:0 auto;padding:40px 20px;color:#1a1c1d;line-height:1.6}
        h1{font-size:2.5rem;font-weight:700;margin-bottom:1.5rem}h2{font-size:1.75rem;font-weight:600;margin-top:2rem;margin-bottom:1rem}h3{font-size:1.375rem;font-weight:600;margin-top:1.5rem;margin-bottom:0.75rem}
        p{margin-bottom:1.25rem}ul,ol{padding-left:1.5rem;margin-bottom:1.25rem}
        blockquote{border-left:3px solid #c2c1ff;padding-left:1rem;color:#6b6f82;font-style:italic}
        pre{background:#1e1f22;border-radius:8px;padding:1rem;overflow-x:auto;margin-bottom:1.25rem}
        code{font-family:Consolas,monospace;font-size:0.9em;background:#f1f2f5;border-radius:4px;padding:2px 6px}pre code{background:none;color:#e4e5e7;padding:0}
        table{width:100%;border-collapse:collapse;margin-bottom:1.25rem}th,td{padding:8px 12px;border:1px solid #e0e1e5;text-align:left}th{background:#f1f2f5;font-weight:600}
        a{color:#0050cb;text-decoration:underline}img{max-width:100%}
      </style></head><body>${html}</body></html>`)
      doc.close()

      await new Promise(r => setTimeout(r, 500))
      const dataUrl = await toPng(doc.body, { quality: 1, pixelRatio: 2, backgroundColor: '#ffffff' })
      document.body.removeChild(iframe)

      const img = new window.Image()
      img.src = dataUrl
      await new Promise((resolve, reject) => { img.onload = resolve; img.onerror = reject })

      const pdf = new jsPDF('p', 'mm', 'a4')
      const pdfW = pdf.internal.pageSize.getWidth()
      const pdfH = pdf.internal.pageSize.getHeight()
      const imgW = pdfW
      const imgH = (img.height / img.width) * imgW

      let heightLeft = imgH
      let position = 0

      pdf.addImage(dataUrl, 'PNG', 0, position, imgW, imgH)
      heightLeft -= pdfH

      while (heightLeft > 0) {
        position = -(pdfH * Math.ceil((imgH - heightLeft) / pdfH))
        pdf.addPage()
        pdf.addImage(dataUrl, 'PNG', 0, position, imgW, imgH)
        heightLeft -= pdfH
      }

      const { save } = await import('@tauri-apps/plugin-dialog')
      const path = await save({
        filters: [{ name: 'PDF Document', extensions: ['pdf'] }],
        defaultPath: `${title}.pdf`,
      })
      if (!path) return

      const pdfBuffer = pdf.output('arraybuffer')
      const uint8 = new Uint8Array(pdfBuffer)
      const { writeFile } = await import('@tauri-apps/plugin-fs')
      await writeFile(path, uint8)
    } catch (e) {
      console.error('PDF export error:', e)
      const pdf = new jsPDF('p', 'mm', 'a4')
      pdf.setFontSize(16)
      pdf.text('Error generating PDF', 20, 40)
      const blob = pdf.output('blob')
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${title}.pdf`
      a.click()
      URL.revokeObjectURL(url)
    }
    return
  }

  const ext = format

  if (format === 'docx') {
    try {
      const { save } = await import('@tauri-apps/plugin-dialog')
      const path = await save({
        filters: [{ name: 'Word Document', extensions: ['docx'] }],
        defaultPath: `${title}.docx`,
      })
      if (!path) return

      const docChildren = htmlToDocxChildren(html)
      const doc = new Document({
        sections: [{
          properties: { page: { margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } } },
          children: docChildren,
        }],
      })
      const blob = await Packer.toBlob(doc)
      const buffer = await blob.arrayBuffer()
      const uint8 = new Uint8Array(buffer)
      const { writeFile } = await import('@tauri-apps/plugin-fs')
      await writeFile(path, uint8)
    } catch (e) {
      console.error('Docx export error:', e)
    }
    return
  }

  try {
    const { save } = await import('@tauri-apps/plugin-dialog')
    const { invoke } = await import('@tauri-apps/api/core')
    const filterName = 'Markdown'
    const path = await save({
      filters: [{ name: filterName, extensions: [ext] }],
      defaultPath: `${title}.${ext}`,
    })
    if (!path) return

    if (format === 'md') {
      await invoke('write_text_file', { path, content: turndown.turndown(html) })
    }
  } catch {
    const content = turndown.turndown(html)
    const blob = new Blob([content], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${title}.${ext}`
    a.click()
    URL.revokeObjectURL(url)
  }
}

// ── Editor Actions ───────────────────────────────────────────

function triggerImageUpload() {
  imageInput.value?.click()
}

function addImage(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file || !editor.value) return
  const reader = new FileReader()
  reader.onload = () => {
    if (typeof reader.result === "string") {
      editor.value?.chain().focus().setImage({ src: reader.result }).run()
    }
  }
  reader.readAsDataURL(file)
  input.value = ""
}



// ── Editor ────────────────────────────────────────────────────

const editor = useEditor({
  content: "",
  extensions: [
    StarterKit.configure({
      heading: { levels: [1, 2, 3] },
    }),
    Underline,
    LinkExtension.configure({ openOnClick: false }),
    Image.configure({ inline: true, allowBase64: true }),
    Placeholder.configure({ placeholder: "Start writing..." }),
    Typography,
  ],
  onUpdate: () => {
    saved.value = false
    triggerSave()
  },
  editorProps: {
    attributes: {
      class: "outline-none min-h-[300px]",
    },
    handlePaste: (_view, event) => {
      const items = event.clipboardData?.items
      if (!items) return false
      for (const item of items) {
        if (item.type.startsWith('image/')) {
          const file = item.getAsFile()
          if (file) {
            const reader = new FileReader()
            reader.onload = () => {
              if (typeof reader.result === 'string') {
                editor.value?.chain().focus().setImage({ src: reader.result }).run()
              }
            }
            reader.readAsDataURL(file)
            return true
          }
        }
      }
      return false
    },
  },
})

const tocItems = computed(() => {
  if (!editor.value) return []
  const items: { level: number; text: string }[] = []
  editor.value.state.doc.forEach((node: any) => {
    if (node.type.name === 'heading') {
      const text = node.textContent
      if (text) items.push({ level: node.attrs.level, text })
    }
  })
  return items
})

const visibleTocItems = computed(() => {
  const result: { level: number; text: string; index: number; depth: number; canExpand: boolean }[] = []
  const collapsed = tocCollapsed.value
  function walk(nodes: TocNode[], depth: number) {
    for (const node of nodes) {
      result.push({ level: node.level, text: node.text, index: node.index, depth, canExpand: node.children.length > 0 })
      if (node.children.length > 0 && !collapsed.has(node.index)) walk(node.children, depth + 1)
    }
  }
  walk(buildTocTree(tocItems.value), 0)
  return result
})

watch(tocItems, (items) => {
  const tree = buildTocTree(items)
  const expandable = new Set(tocCollapsed.value)
  function collect(nodes: TocNode[]) {
    for (const node of nodes) {
      if (node.children.length > 0) expandable.add(node.index)
      collect(node.children)
    }
  }
  collect(tree)
  tocCollapsed.value = expandable
})

// ── Close export menu on outside click ──────────────────────

function onDocumentClick(e: MouseEvent) {
  const target = e.target as Node
  if (showExportMenu.value && exportMenuRef.value && !exportMenuRef.value.contains(target)) {
    showExportMenu.value = false
  }
  if (showSpaceDropdown.value && spaceDropdownRef.value && !spaceDropdownRef.value.contains(target)) {
    showSpaceDropdown.value = false
  }
  if (folderAddDropdownId.value && folderAddDropdownRef.value && !folderAddDropdownRef.value.contains(target)) {
    folderAddDropdownId.value = null
  }
}

// ── Lifecycle ─────────────────────────────────────────────────

onMounted(async () => {
  await loadData()
  document.addEventListener('click', onDocumentClick, true)

  nextTick(() => {
    const items = tocItems.value
    const tree = buildTocTree(items)
    const expandable = new Set<number>()
    function collect(nodes: TocNode[]) {
      for (const node of nodes) {
        if (node.children.length > 0) expandable.add(node.index)
        collect(node.children)
      }
    }
    collect(tree)
    tocCollapsed.value = expandable
  })
})

onBeforeUnmount(async () => {
  document.removeEventListener('click', onDocumentClick, true)
  if (!saved.value) {
    await saveCurrentNote()
  }
  if (saveTimer) clearTimeout(saveTimer)
  if (versionTimer) clearTimeout(versionTimer)
  if (searchDebounce) clearTimeout(searchDebounce)
  editor.value?.destroy()
})
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
:deep(.prose-editor h1) { font-family: 'Inter', sans-serif; font-weight: 700; color: #1a1c1d; font-size: 2rem; line-height: 1.3; margin-bottom: 1.25rem; letter-spacing: -0.02em; }
:deep(.prose-editor h2) { font-family: 'Inter', sans-serif; font-weight: 600; color: #1a1c1d; font-size: 1.75rem; line-height: 1.3; margin-top: 2rem; margin-bottom: 1rem; letter-spacing: -0.02em; }
:deep(.prose-editor h3) { font-family: 'Inter', sans-serif; font-weight: 600; color: #1a1c1d; font-size: 1.375rem; line-height: 1.4; margin-top: 1.5rem; margin-bottom: 0.75rem; letter-spacing: -0.01em; }
:deep(.prose-editor p) { font-family: 'Inter', sans-serif; font-weight: 400; color: #424656; font-size: 1.0625rem; line-height: 1.6; margin-bottom: 1.25rem; }
:deep(.prose-editor ul) { list-style-type: disc; padding-left: 1.5rem; color: #424656; margin-bottom: 1.25rem; }
:deep(.prose-editor ol) { list-style-type: decimal; padding-left: 1.5rem; color: #424656; margin-bottom: 1.25rem; }
:deep(.prose-editor li) { margin-bottom: 0.5rem; font-size: 1.0625rem; line-height: 1.6; }
:deep(.prose-editor blockquote) { border-left: 3px solid #c2c1ff; padding-left: 1rem; margin-left: 0; color: #6b6f82; font-style: italic; }
:deep(.prose-editor a) { color: #0050cb; text-decoration: underline; cursor: pointer; }

.toolbar-btn {
  background: transparent;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  padding: 6px;
  line-height: 1;
  transition: all 0.15s;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #6b6f82;
}
.toolbar-btn:hover {
  background: rgba(193, 132, 255, 0.1);
}
.toolbar-btn.toolbar-active {
  background: rgba(193, 132, 255, 0.15);
  color: #7c3aed;
}
.toolbar-btn.toolbar-active span {
  color: #7c3aed;
}

.animate-toc-in {
  animation: tocSlideIn 0.35s cubic-bezier(0.16, 1, 0.3, 1);
}
@keyframes tocSlideIn {
  from { transform: translateX(100%); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}
</style>
