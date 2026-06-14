<template>
  <div class="flex flex-col h-[calc(100vh-64px)] -mx-margin-page -mt-14">
    <!-- Toolbar -->
    <div class="flex items-center gap-1 px-4 py-2 bg-white/20 backdrop-blur-sm border-b border-white/20 shrink-0 overflow-x-auto custom-scrollbar">
      <button class="glass-button px-3 py-1.5 rounded-lg font-caption text-caption flex items-center gap-1 shrink-0" title="Back to Home" @click="goHome">
        <span class="material-symbols-outlined text-[16px]">arrow_back</span>
        <span class="hidden sm:inline">Back</span>
      </button>
      <span class="w-px h-5 bg-white/30 mx-1 shrink-0"></span>
      <button class="glass-button px-3 py-1.5 rounded-lg font-caption text-caption flex items-center gap-1 shrink-0" title="Save" @click="saveFile">
        <span class="material-symbols-outlined text-[16px]">save</span>
        <span class="hidden sm:inline">Save</span>
      </button>
      <button class="glass-button px-3 py-1.5 rounded-lg font-caption text-caption flex items-center gap-1 shrink-0" title="Save As" @click="showSaveAsDialog = true">
        <span class="material-symbols-outlined text-[16px]">save_as</span>
        <span class="hidden sm:inline">Save As</span>
      </button>
      <span class="w-px h-5 bg-white/30 mx-1 shrink-0"></span>
      <button class="glass-button px-3 py-1.5 rounded-lg font-caption text-caption flex items-center gap-1 shrink-0 opacity-50 cursor-not-allowed" title="Cloud Sync (Coming Soon)">
        <span class="material-symbols-outlined text-[16px]">cloud_sync</span>
        <span class="hidden sm:inline">Cloud</span>
      </button>
      <button class="glass-button px-3 py-1.5 rounded-lg font-caption text-caption flex items-center gap-1 shrink-0 opacity-50 cursor-not-allowed" title="Platform Sync (Coming Soon)">
        <span class="material-symbols-outlined text-[16px]">sync</span>
        <span class="hidden sm:inline">Platform</span>
      </button>

      <div class="ml-auto flex items-center gap-1">
        <div class="glass-panel rounded-full p-0.5 inline-flex shadow-sm shrink-0">
          <button class="px-3 py-1.5 rounded-full font-caption text-caption flex items-center gap-1.5 transition-all" :class="viewMode === 'excel' ? 'glass-active' : 'glass-button'" @click="viewMode = 'excel'">
            <span class="material-symbols-outlined text-[16px]">table_view</span>
            <span class="hidden sm:inline">Excel</span>
          </button>
          <button class="px-3 py-1.5 rounded-full font-caption text-caption flex items-center gap-1.5 transition-all" :class="viewMode === 'mindmap' ? 'glass-active' : 'glass-button'" @click="viewMode = 'mindmap'">
            <span class="material-symbols-outlined text-[16px]">account_tree</span>
            <span class="hidden sm:inline">Mind Map</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Excel View -->
    <div v-if="viewMode === 'excel' && activeFile" class="flex-1 overflow-hidden">
      <div class="h-full glass-panel rounded-none border-0 flex flex-col">
        <!-- Header bar -->
        <div class="flex items-center justify-between px-3 py-1.5 border-b border-white/30 bg-white/10 shrink-0">
          <div class="flex items-center gap-2">
            <span class="font-label-md text-label-md text-on-surface-variant">{{ activeFile.name }}</span>
            <span class="font-caption text-caption text-on-surface-variant/60">{{ contentRows().length }} cases</span>
          </div>
          <div class="flex items-center gap-1">
            <button class="glass-button px-2 py-1 rounded-lg text-caption flex items-center gap-1" @click="addRow">
              <span class="material-symbols-outlined text-[14px]">add</span>
              Row
            </button>
          </div>
        </div>

        <!-- Spreadsheet (Virtual Scroll / CSS Grid) -->
        <div class="flex-1 overflow-hidden" @contextmenu.prevent="showContextMenu($event)">
          <div ref="scrollBody" class="h-full overflow-auto custom-scrollbar relative" @scroll="onBodyScroll">
            <div class="relative" :style="{ minWidth: totalWidth + 'px', width: '100%' }">
              <!-- Sticky header -->
              <div class="sticky top-0 z-20 grid items-center bg-[#eaeaf0] border-b border-gray-300/60 text-[13px]"
                :style="{ gridTemplateColumns: gridTemplateCols }">
                <div class="text-center font-caption text-caption text-on-surface-variant/60 px-1.5 py-2 border-r border-gray-300/60">#</div>
                <div v-for="col in visibleCols" :key="col.key"
                  data-col-key
                  class="bg-[#eaeaf0] border-r border-gray-300/60 px-2 py-2 font-caption text-caption text-on-surface-variant/70 relative select-none overflow-hidden min-w-0"
                  @contextmenu.prevent="showColumnContextMenu($event, col)">
                  <div class="flex items-center gap-1">
                    <span class="truncate">{{ col.label }}</span>
                    <span v-if="sortState?.key === col.key" class="text-[11px] text-secondary font-bold shrink-0">{{ sortState.dir === 'asc' ? '▲' : '▼' }}</span>
                    <button class="p-0.5 rounded hover:bg-black/10 ml-auto shrink-0" :class="{ 'text-secondary': isFilterActive(col.key) }" @click.stop="openFilterPopup($event, col.key)">
                      <span class="material-symbols-outlined text-[14px]">filter_list</span>
                    </button>
                  </div>
                  <span class="absolute top-0 right-0 w-1.5 h-full cursor-col-resize hover:bg-secondary/30 active:bg-secondary/50 z-10" @mousedown.stop="startResize($event, col.key)"></span>
                </div>
                <div class="bg-[#eaeaf0] border-gray-300/60"></div>
              </div>
              <!-- Virtual rows -->
              <div class="relative" :style="{ height: rowsHeight + 'px' }">
                <div v-for="entry in virtualRows" :key="(entry.item as any).id"
                  class="absolute left-0 right-0 grid transition-colors will-change-transform"
                  :class="{ 'bg-secondary-fixed/15': selectedIds.includes((entry.item as any).id), 'hover:bg-white/40': !selectedIds.includes((entry.item as any).id) }"
                  :style="{ transform: 'translateY(' + entry.top + 'px)', minHeight: ROW_ESTIMATE + 'px', gridTemplateColumns: gridTemplateCols }"
                  :data-case-id="(entry.item as any).id"
                  @click="selectCase((entry.item as any).id, $event)"
                  @contextmenu.prevent="showRowContextMenu($event, entry.item, entry.index)">
                  <div class="text-center font-caption text-caption text-on-surface-variant/40 px-1.5 py-1 border-r border-b border-gray-300/40 bg-white">
                    {{ entry.index + 1 }}
                  </div>
                  <template v-if="(entry.item as any)._virtual">
                    <div class="border-r border-b border-gray-300/40 cursor-text hover:bg-white/30" @click.stop="activateRow((entry.item as any).id, entry.index)">
                      <div class="px-3 py-[7px] text-[13px] text-on-surface-variant/20 select-none">&nbsp;</div>
                    </div>
                  </template>
                  <template v-else>
                    <div v-for="col in visibleCols" :key="col.key"
                      class="border-r border-b border-gray-300/40 cursor-text overflow-hidden min-w-0"
                      @click.stop="focusCell((entry.item as CaseItem).id, col.key, $event)">
                      <template v-if="col.key === 'module'">
                        <div class="flex items-start gap-1 px-2">
                          <span class="material-symbols-outlined text-[14px] text-on-surface-variant/30 shrink-0 mt-[9px]">folder</span>
                          <textarea :ref="initTextarea" :value="getCaseValue(entry.item as CaseItem, col.key) || ''" class="cell-editor"
                            @input="onTextareaInput((entry.item as CaseItem).id, col.key, $event)" @click.stop></textarea>
                        </div>
                      </template>
                      <template v-else-if="col.key === 'priority'">
                        <select :value="getCaseValue(entry.item as CaseItem, col.key)" class="cell-editor cursor-pointer"
                          @change="updateField((entry.item as CaseItem).id, col.key, ($event.target as HTMLSelectElement).value)" @click.stop>
                          <option value="">--</option>
                          <option v-for="opt in (col.options || ['P0','P1','P2','P3'])" :key="opt" :value="opt">{{ opt }}</option>
                        </select>
                      </template>
                      <template v-else-if="col.key === 'tags'">
                        <div class="flex flex-wrap gap-0.5 px-1 py-0.5">
                          <span v-for="(tag, tIdx) in getCaseTags(entry.item as CaseItem)" :key="tIdx"
                            class="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded-md bg-white/60 text-on-surface-variant/70 text-[11px]">
                            {{ tag }}
                            <button class="p-0 rounded-full ml-0.5 text-on-surface-variant/40 hover:text-error/60" @click.stop="removeTag((entry.item as CaseItem).id, tIdx)">
                              <span class="material-symbols-outlined text-[12px]">close</span>
                            </button>
                          </span>
                          <input :value="tagInputs[(entry.item as CaseItem).id] || ''" class="cell-editor min-w-[50px] max-w-[100px]"
                            @click.stop
                            @input="onTagInput((entry.item as CaseItem).id, ($event.target as HTMLInputElement).value)"
                            @keydown.enter.prevent="commitTag((entry.item as CaseItem).id)"
                            @keydown.backspace.prevent="backspaceTag((entry.item as CaseItem).id)"
                            @blur="commitTag((entry.item as CaseItem).id)" />
                        </div>
                      </template>
                      <template v-else-if="col.type === 'select'">
                        <select :value="getCaseValue(entry.item as CaseItem, col.key)" class="cell-editor cursor-pointer"
                          @change="updateField((entry.item as CaseItem).id, col.key, ($event.target as HTMLSelectElement).value)" @click.stop>
                          <option v-for="opt in (col.options || [])" :key="opt" :value="opt">{{ opt }}</option>
                        </select>
                      </template>
                      <template v-else-if="col.type === 'text'">
                        <textarea :ref="initTextarea" :value="getCaseValue(entry.item as CaseItem, col.key) || ''" class="cell-editor"
                          @input="onTextareaInput((entry.item as CaseItem).id, col.key, $event)" @click.stop></textarea>
                      </template>
                      <template v-else>
                         <textarea :ref="initTextarea" :value="getCaseValue(entry.item as CaseItem, col.key)" class="cell-editor"
                          @input="onTextareaInput((entry.item as CaseItem).id, col.key, $event)" @click.stop></textarea>
                      </template>
                    </div>
                    <div class="border-b border-gray-300/40 flex items-center justify-center gap-0 opacity-30 hover:opacity-80 transition-opacity">
                      <button class="p-0.5 rounded hover:bg-white/40" @click.stop="duplicateSingle((entry.item as CaseItem).id)" title="Duplicate">
                        <span class="material-symbols-outlined text-[14px] text-on-surface-variant/50">content_copy</span>
                      </button>
                      <button class="p-0.5 rounded hover:bg-white/40" @click.stop="store.deleteCase((entry.item as CaseItem).id)" title="Delete">
                        <span class="material-symbols-outlined text-[14px] text-on-surface-variant/50">delete</span>
                      </button>
                    </div>
                  </template>
                </div>
              </div>
            </div>
            <div v-if="contentRows().length === 0" class="flex items-center justify-center py-20">
              <div class="text-center">
                <span class="material-symbols-outlined text-4xl text-on-surface-variant/15">table_rows</span>
                <p class="font-body-md text-body-md text-on-surface-variant/50 mt-3">No test cases yet</p>
                <button class="mt-4 px-5 py-2 rounded-full glass-button inline-flex items-center gap-1.5" @click="addRow">
                  <span class="material-symbols-outlined text-[16px]">add</span>
                  Add First Case
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Status bar -->
        <div class="flex items-center justify-between px-3 py-1 border-t border-gray-300/50 bg-white/10 shrink-0">
          <span class="font-caption text-caption text-on-surface-variant/50">{{ contentRows().length }} rows</span>
          <div class="flex items-center gap-3">
            <span v-if="selectedIds.length > 0" class="font-caption text-caption text-secondary/70">{{ selectedIds.length }} selected</span>
            <button v-if="selectedIds.length > 1" class="glass-button px-2 py-0.5 rounded text-caption text-error/70 flex items-center gap-1" @click="deleteSelected">
              <span class="material-symbols-outlined text-[14px]">delete</span>
              Delete {{ selectedIds.length }}
            </button>
          </div>
        </div>

        <!-- Context menu -->
        <Teleport to="body">
          <div
            v-if="contextMenu.show"
            data-menu="context"
            class="fixed z-50 glass-panel rounded-xl py-1 shadow-lg border border-white/50 min-w-[200px]"
            :style="{ left: contextMenu.x + 'px', top: contextMenu.y + 'px' }"
            @mousedown.stop
          >
            <div class="px-3 py-1.5 font-caption text-caption text-on-surface-variant/60 border-b border-white/20">
              {{ contextMenu.targetType === 'row' ? 'Row Actions' : contextMenu.targetType === 'header' ? 'Column Actions' : 'Table Actions' }}
            </div>

            <!-- Row context menu -->
            <template v-if="contextMenu.targetType === 'row'">
              <button class="w-full flex items-center gap-2 px-3 py-1.5 text-[13px] text-on-surface glass-hover text-left" @click="cmInsertAbove">
                <span class="material-symbols-outlined text-[16px]">expand_less</span> Insert Above
              </button>
              <button class="w-full flex items-center gap-2 px-3 py-1.5 text-[13px] text-on-surface glass-hover text-left" @click="cmInsertBelow">
                <span class="material-symbols-outlined text-[16px]">expand_more</span> Insert Below
              </button>
              <button class="w-full flex items-center gap-2 px-3 py-1.5 text-[13px] text-on-surface glass-hover text-left" @click="cmDuplicate">
                <span class="material-symbols-outlined text-[16px]">content_copy</span> Duplicate
              </button>
              <div class="border-t border-white/10"></div>
              <button class="w-full flex items-center gap-2 px-3 py-1.5 text-[13px] text-error glass-hover text-left" @click="cmDelete">
                <span class="material-symbols-outlined text-[16px]">delete</span> Delete
              </button>
            </template>

            <!-- Header column context menu -->
            <template v-else-if="contextMenu.targetType === 'header'">
              <button class="w-full flex items-center gap-2 px-3 py-1.5 text-[13px] text-on-surface glass-hover text-left" @click="cmAddColumn">
                <span class="material-symbols-outlined text-[16px]">add</span> Add Column
              </button>
              <div class="border-t border-white/10"></div>
              <div class="px-3 py-1 font-caption text-caption text-on-surface-variant/50">Toggle Columns</div>
              <div
                v-for="col in columns"
                :key="col.key"
                class="flex items-center gap-2 px-3 py-1.5 text-[13px] text-on-surface glass-hover text-left cursor-pointer"
                @click="toggleColumnVisibility(col.key)"
              >
                <span
                  class="w-4 h-4 rounded border border-gray-300/50 flex items-center justify-center text-[10px]"
                  :class="visibleColumns.includes(col.key) ? 'bg-secondary/20 border-secondary/40 text-secondary' : ''"
                >
                  <span v-if="visibleColumns.includes(col.key)" class="material-symbols-outlined text-[12px]">check</span>
                </span>
                <span>{{ col.label }}</span>
                <span v-if="isCustomField(col.key)" class="ml-auto text-[11px] text-on-surface-variant/40">
                  <button class="glass-button px-1 py-0.5 rounded text-[11px]" @click.stop="cmEditField(col.key)">Edit</button>
                  <button class="glass-button px-1 py-0.5 rounded text-[11px] text-error/60 ml-1" @click.stop="cmRemoveField(col.key)">Del</button>
                </span>
              </div>
            </template>

            <!-- Table context menu -->
            <template v-else>
              <button class="w-full flex items-center gap-2 px-3 py-1.5 text-[13px] text-on-surface glass-hover text-left" @click="addRow">
                <span class="material-symbols-outlined text-[16px]">add</span> Insert Row
              </button>
              <button class="w-full flex items-center gap-2 px-3 py-1.5 text-[13px] text-on-surface glass-hover text-left" @click="cmAddColumn">
                <span class="material-symbols-outlined text-[16px]">view_column</span> Add Column
              </button>
              <div v-if="selectedIds.length > 0" class="border-t border-white/10"></div>
              <button v-if="selectedIds.length > 0" class="w-full flex items-center gap-2 px-3 py-1.5 text-[13px] text-on-surface glass-hover text-left" @click="duplicateSelected">
                <span class="material-symbols-outlined text-[16px]">content_copy</span> Duplicate Selected
              </button>
              <button v-if="selectedIds.length > 0" class="w-full flex items-center gap-2 px-3 py-1.5 text-[13px] text-on-surface glass-hover text-left" @click="copySelected">
                <span class="material-symbols-outlined text-[16px]">file_copy</span> Copy Selected
              </button>
              <div v-if="selectedIds.length > 0" class="border-t border-white/10"></div>
              <button v-if="selectedIds.length > 0" class="w-full flex items-center gap-2 px-3 py-1.5 text-[13px] text-error glass-hover text-left" @click="deleteSelected">
                <span class="material-symbols-outlined text-[16px]">delete</span> Delete Selected
              </button>
            </template>
          </div>
        </Teleport>

        <!-- Add/Edit column dialog -->
        <Teleport to="body">
          <div v-if="showColumnDialog" class="fixed inset-0 z-50 flex items-center justify-center">
            <div class="absolute inset-0 bg-black/10 backdrop-blur-sm" @click="showColumnDialog = false"></div>
            <div class="glass-panel rounded-2xl p-6 w-[420px] relative z-10">
              <h3 class="font-headline-md text-headline-md text-on-surface font-semibold mb-4">{{ editingColumnKey ? 'Edit Column' : 'Add Column' }}</h3>
              <div class="flex flex-col gap-3">
                <div>
                  <label class="font-caption text-caption text-on-surface-variant/60 block mb-1">Key</label>
                  <input
                    v-model="columnForm.key"
                    class="w-full bg-white/60 border border-gray-300/50 rounded-lg px-3 py-2 text-[13px] text-on-surface font-mono focus:outline-none focus:border-secondary/40"
                    placeholder="field_key"
                    :disabled="!!editingColumnKey"
                  />
                </div>
                <div>
                  <label class="font-caption text-caption text-on-surface-variant/60 block mb-1">Label</label>
                  <input
                    v-model="columnForm.label"
                    class="w-full bg-white/60 border border-gray-300/50 rounded-lg px-3 py-2 text-[13px] text-on-surface focus:outline-none focus:border-secondary/40"
                    placeholder="Display Name"
                  />
                </div>
                <div>
                  <label class="font-caption text-caption text-on-surface-variant/60 block mb-1">Type</label>
                  <select
                    v-model="columnForm.type"
                    class="w-full bg-white/60 border border-gray-300/50 rounded-lg px-3 py-2 text-[13px] text-on-surface focus:outline-none focus:border-secondary/40 appearance-none cursor-pointer"
                  >
                    <option value="text">Text</option>
                    <option value="select">Select</option>
                    <option value="textarea">Textarea</option>
                  </select>
                </div>
                <div v-if="columnForm.type === 'select'">
                  <label class="font-caption text-caption text-on-surface-variant/60 block mb-1">Options (comma separated)</label>
                  <input
                    v-model="columnForm.optionsStr"
                    class="w-full bg-white/60 border border-gray-300/50 rounded-lg px-3 py-2 text-[13px] text-on-surface font-mono focus:outline-none focus:border-secondary/40"
                    placeholder="opt1, opt2, opt3"
                  />
                </div>
              </div>
              <div class="flex justify-end gap-2 mt-5">
                <button class="glass-button px-4 py-2 rounded-full text-caption" @click="showColumnDialog = false">Cancel</button>
                <button class="glass-button px-4 py-2 rounded-full text-caption flex items-center gap-1" @click="confirmColumn">
                  <span class="material-symbols-outlined text-[14px]">check</span>
                  {{ editingColumnKey ? 'Update' : 'Add' }}
                </button>
              </div>
            </div>
          </div>
        </Teleport>
      </div>
    </div>

    <!-- Save As Dialog -->
    <Teleport to="body">
      <div v-if="showSaveAsDialog" class="fixed inset-0 z-50 flex items-center justify-center" @click.self="showSaveAsDialog = false">
        <div class="absolute inset-0 bg-black/10 backdrop-blur-sm"></div>
        <div class="glass-panel rounded-2xl p-6 w-full max-w-xs relative z-10 bg-white/80 shadow-xl">
          <h3 class="font-headline-md text-headline-md text-on-surface font-semibold mb-4">Export As</h3>
          <div class="flex flex-col gap-2">
            <button class="glass-button w-full px-4 py-3 rounded-xl font-label-md text-label-md flex items-center gap-3 text-left" @click="saveAsExcel">
              <span class="material-symbols-outlined text-[20px]">table_chart</span>
              <div>
                <div>Excel (.xlsx)</div>
                <div class="font-caption text-caption text-on-surface-variant/60">Export to spreadsheet</div>
              </div>
            </button>
            <button class="glass-button w-full px-4 py-3 rounded-xl font-label-md text-label-md flex items-center gap-3 text-left" @click="saveAsPng">
              <span class="material-symbols-outlined text-[20px]">account_tree</span>
              <div>
                <div>Mind Map (.png)</div>
                <div class="font-caption text-caption text-on-surface-variant/60">Export mind map as image</div>
              </div>
            </button>
          </div>
          <button class="glass-button w-full mt-3 px-4 py-2 rounded-xl font-caption text-caption text-on-surface-variant" @click="showSaveAsDialog = false">Cancel</button>
        </div>
      </div>
    </Teleport>

    <!-- Status message -->
    <div v-if="importStatus" class="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 glass-panel rounded-full px-6 py-3 font-label-md text-label-md text-on-surface shadow-lg bg-white/90 backdrop-blur-sm">
      {{ importStatus }}
    </div>

    <!-- Mind Map View -->
    <div v-else-if="viewMode === 'mindmap' && activeFile" class="flex-1 relative overflow-hidden bg-white/10">
      <div ref="mindmapContainer" class="w-full h-full cursor-grab" @wheel.prevent="onMindMapWheel">
        <div class="absolute inset-0" :style="mindMapTransform" @mousedown="onMindMapPanStart" @mousemove="onMindMapPan" @mouseup="onMindMapPanEnd" @mouseleave="onMindMapPanEnd">
          <svg class="absolute inset-0 pointer-events-none" style="width: 100%; height: 100%">
            <path v-for="(line, idx) in mindMapLines" :key="'l' + idx" :d="line.path" stroke="rgba(100,120,255,0.2)" stroke-width="1.5" fill="none" />
          </svg>

          <div
            v-for="(mod, mIdx) in mindMapModules"
            :key="'mod' + mIdx"
            class="absolute glass-panel rounded-xl px-4 py-2.5 min-w-[140px] cursor-pointer select-none z-10 border-l-[3px] border-secondary/40 glass-hover"
            :style="{ left: mod.x + 'px', top: mod.y + 'px' }"
            @dblclick="startRenameModule(mod)"
          >
            <div class="flex items-center gap-2">
              <span class="material-symbols-outlined text-[16px] text-secondary/60" style="font-variation-settings: 'FILL' 1">folder</span>
              <span v-if="mod.renaming" class="bg-transparent border-b border-secondary/40 text-body-md text-[13px] text-on-surface font-medium outline-none" contenteditable @blur="finishRenameModule(mod, $event)" @keydown.enter.prevent="finishRenameModule(mod, $event)" ref="renameInput"></span>
              <span v-else class="font-body-md text-[13px] text-on-surface font-medium">{{ mod.name || '(No Module)' }}</span>
              <span class="font-caption text-[10px] text-on-surface-variant/50 ml-1">{{ mod.count }}</span>
            </div>
            <div v-for="c in mod.cases" :key="c.id" class="mt-2 ml-2 pl-2 border-l-2 border-white/20">
              <div class="mm-case-node glass-hover rounded-lg" @click="navigateToCase(c.id)">
                <div class="flex items-start gap-1.5">
                  <span class="w-4 h-4 rounded-full bg-secondary-fixed/40 text-[9px] font-bold flex items-center justify-center text-secondary shrink-0 mt-0.5">{{ activeFile.cases.indexOf(c) + 1 }}</span>
                  <div class="min-w-0">
                    <div class="font-body-md text-[12px] text-on-surface font-medium leading-snug">{{ c.title || '(No Title)' }}</div>
                    <div v-if="c.steps" class="text-[11px] text-on-surface-variant/60 mt-0.5 line-clamp-2">{{ c.steps }}</div>
                  </div>
                </div>
              </div>
            </div>
            <button v-if="mod.cases.length > 3" class="text-[11px] text-secondary/60 mt-1 ml-2 glass-button px-2 py-0.5 rounded-full" @click.stop="mod.collapsed = !mod.collapsed">
              {{ mod.collapsed ? 'Expand' : 'Collapse' }}
            </button>
          </div>
        </div>
      </div>

      <div class="absolute bottom-4 left-4 glass-panel rounded-lg p-1 flex items-center gap-1 z-20 shadow-sm">
        <button class="glass-button w-7 h-7 rounded flex items-center justify-center" @click="mmZoomIn"><span class="material-symbols-outlined text-[16px]">add</span></button>
        <div class="w-px h-4 bg-white/20"></div>
        <button class="glass-button w-7 h-7 rounded flex items-center justify-center" @click="mmZoomOut"><span class="material-symbols-outlined text-[16px]">remove</span></button>
        <div class="w-px h-4 bg-white/20"></div>
        <button class="glass-button w-7 h-7 rounded flex items-center justify-center" @click="mmFit"><span class="material-symbols-outlined text-[16px]">fit_screen</span></button>
        <div class="w-px h-4 bg-white/20"></div>
        <span class="w-10 h-7 flex items-center justify-center font-caption text-caption text-on-surface-variant">{{ Math.round(mmZoom * 100) }}%</span>
      </div>
    </div>
  </div>

  <Teleport to="body">
    <div v-if="activeFilterCol" class="fixed inset-0 z-50" @click="closeFilterPopup">
      <div class="absolute bg-white rounded-lg shadow-xl border border-gray-200 py-1 text-[13px] min-w-[180px] max-h-[320px] overflow-y-auto" :style="{ top: filterPopupPos.top + 'px', left: filterPopupPos.left + 'px' }" @click.stop>
        <div class="px-3 py-1 text-[12px] font-medium text-gray-500">Sort</div>
        <button class="w-full flex items-center gap-2 px-3 py-1.5 hover:bg-gray-100 text-left" :class="{ 'font-bold text-secondary': sortState?.key === activeFilterCol && sortState?.dir === 'asc' }" @click="setSort(activeFilterCol!, 'asc')">
          <span class="material-symbols-outlined text-[14px]">arrow_upward</span> Sort A→Z
        </button>
        <button class="w-full flex items-center gap-2 px-3 py-1.5 hover:bg-gray-100 text-left" :class="{ 'font-bold text-secondary': sortState?.key === activeFilterCol && sortState?.dir === 'desc' }" @click="setSort(activeFilterCol!, 'desc')">
          <span class="material-symbols-outlined text-[14px]">arrow_downward</span> Sort Z→A
        </button>
        <div v-if="sortState" class="border-t border-gray-200 my-1">
          <button class="w-full flex items-center gap-2 px-3 py-1.5 hover:bg-gray-100 text-left text-gray-500" @click="clearSort">
            <span class="material-symbols-outlined text-[14px]">close</span> Clear Sort
          </button>
        </div>
        <div class="border-t border-gray-200 my-1"></div>
        <div class="px-3 py-1 flex items-center justify-between">
          <span class="text-[12px] font-medium text-gray-500">Filter by value</span>
          <button v-if="isFilterActive(activeFilterCol!)" class="text-[11px] text-secondary hover:underline" @click="clearColumnFilter(activeFilterCol!)">Clear</button>
        </div>
        <label v-for="val in getUniqueValues(activeFilterCol!)" :key="val" class="flex items-center gap-2 px-3 py-1 hover:bg-gray-100 cursor-pointer">
          <input type="checkbox" :checked="columnFilters[activeFilterCol!]?.has(val)" @change="toggleFilterValue(activeFilterCol!, val)" class="accent-secondary" />
          <span class="truncate">{{ val || '(Empty)' }}</span>
        </label>
        <div v-if="getUniqueValues(activeFilterCol!).length === 0" class="px-3 py-2 text-gray-400 text-[12px] text-center">No values</div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick, shallowRef } from 'vue'
import { useRouter } from 'vue-router'
import { useCaseFileStore } from '@/stores/caseFileStore'
import type { CaseFile, CaseItem, CustomFieldDef } from '@/types'
import * as XLSX from 'xlsx'

const router = useRouter()
const store = useCaseFileStore()

const viewMode = ref<'excel' | 'mindmap'>('excel')
const selectedIds = ref<string[]>([])
const contextMenu = ref<{ show: boolean; x: number; y: number; targetType: 'table' | 'row' | 'header'; targetId?: string; targetCol?: string }>({ show: false, x: 0, y: 0, targetType: 'table' })
const renameInput = ref<HTMLElement>()
const showColumnDialog = ref(false)
const editingColumnKey = ref('')
const tagInputs = ref<Record<string, string>>({})
const colWidths = ref<Record<string, number>>({})
const resizing = ref<{ key: string; startX: number; startW: number } | null>(null)

// Filter / Sort state
const sortState = ref<{ key: string; dir: 'asc' | 'desc' } | null>(null)
const columnFilters = ref<Record<string, Set<string>>>({})
const activeFilterCol = ref<string | null>(null)
const filterPopupPos = ref({ top: 0, left: 0 })

function isFilterActive(colKey: string): boolean {
  return colKey in columnFilters.value
}

function getUniqueValues(colKey: string): string[] {
  const vals = new Set<string>()
  displayRows.value.forEach((c: any) => {
    const v = String(c[colKey] ?? '')
    vals.add(v)
  })
  return Array.from(vals).sort()
}

function toggleFilterValue(colKey: string, value: string) {
  if (!columnFilters.value[colKey]) columnFilters.value[colKey] = new Set()
  const s = columnFilters.value[colKey]
  if (s.has(value)) s.delete(value)
  else s.add(value)
  if (s.size === 0) delete columnFilters.value[colKey]
}

function clearColumnFilter(colKey: string) {
  delete columnFilters.value[colKey]
}

function setSort(key: string, dir: 'asc' | 'desc') {
  sortState.value = { key, dir }
  activeFilterCol.value = null
}

function clearSort() {
  sortState.value = null
}

function openFilterPopup(e: MouseEvent, colKey: string) {
  const cell = (e.target as HTMLElement).closest('[data-col-key]') as HTMLElement
  if (!cell) return
  const rect = cell.getBoundingClientRect()
  filterPopupPos.value = { top: rect.bottom + 4, left: rect.left }
  activeFilterCol.value = colKey
}

function closeFilterPopup() {
  activeFilterCol.value = null
}

const filteredSortedRows = computed(() => {
  const rows = displayRows.value
  let filtered = rows.filter(c => {
    if ((c as any)._virtual) {
      return Object.keys(columnFilters.value).length === 0
    }
    for (const [colKey, selected] of Object.entries(columnFilters.value)) {
      const val = String((c as any)[colKey] ?? '')
      if (!selected.has(val)) return false
    }
    return true
  })
  if (sortState.value) {
    const { key, dir } = sortState.value
    filtered = [...filtered].sort((a, b) => {
      const va = (a as any)[key] ?? ''
      const vb = (b as any)[key] ?? ''
      const cmp = String(va).localeCompare(String(vb))
      return dir === 'asc' ? cmp : -cmp
    })
  }
  return filtered
})

function startResize(event: MouseEvent, key: string) {
  const cell = (event.target as HTMLElement).closest('[data-col-key]') as HTMLElement
  if (!cell) return
  resizing.value = { key, startX: event.clientX, startW: cell.offsetWidth }
  document.addEventListener('mousemove', onResizeMove)
  document.addEventListener('mouseup', onResizeEnd)
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
}

function onResizeMove(event: MouseEvent) {
  if (!resizing.value) return
  const dx = event.clientX - resizing.value.startX
  const w = Math.max(80, resizing.value.startW + dx)
  colWidths.value[resizing.value.key] = w
}

function onResizeEnd() {
  resizing.value = null
  document.removeEventListener('mousemove', onResizeMove)
  document.removeEventListener('mouseup', onResizeEnd)
  document.body.style.cursor = ''
  document.body.style.userSelect = ''
}

const columnForm = ref({ key: '', label: '', type: 'text', optionsStr: '' })
const visibleColumns = ref<string[]>(['module', 'title', 'precondition', 'steps', 'expected', 'priority', 'tags', 'assignee', 'remarks'])

const activeFile = computed(() => store.activeFile)

const defaultColumns = [
  { key: 'module', label: 'Module', type: 'text' },
  { key: 'title', label: 'Title', type: 'text' },
  { key: 'precondition', label: 'Precondition', type: 'textarea' },
  { key: 'steps', label: 'Steps', type: 'textarea' },
  { key: 'expected', label: 'Expected', type: 'textarea' },
  { key: 'priority', label: 'Priority', type: 'select', options: ['P0', 'P1', 'P2', 'P3'] },
  { key: 'tags', label: 'Tags', type: 'tags' },
  { key: 'assignee', label: 'Assignee', type: 'text' },
  { key: 'remarks', label: 'Remarks', type: 'textarea' },
]

const customCols = computed(() => {
  const f = activeFile.value
  if (!f?.customFields) return []
  return f.customFields.map(cf => ({ key: cf.key, label: cf.label, type: cf.type, options: cf.options }))
})

const columns = computed(() => {
  const custom = customCols.value
  if (custom.length > 0) return custom
  const customKeys = custom.map(c => c.key)
  return [...defaultColumns.filter(c => !customKeys.includes(c.key)), ...custom]
})

const visibleCols = computed(() => {
  const custom = customCols.value
  if (custom.length > 0) return custom as { key: string; label: string; type: string; options?: string[] }[]
  return defaultColumns.filter(c => visibleColumns.value.includes(c.key)) as { key: string; label: string; type: string; options?: string[] }[]
})

function isCustomField(key: string): boolean {
  return !defaultColumns.some(dc => dc.key === key)
}

function toggleColumnVisibility(key: string) {
  const idx = visibleColumns.value.indexOf(key)
  if (idx >= 0) visibleColumns.value.splice(idx, 1)
  else visibleColumns.value.push(key)
}

function getCaseValue(c: CaseItem, key: string): any {
  return (c as any)[key] ?? ''
}

function getCaseTags(c: CaseItem): string[] {
  return Array.isArray(c.tags) ? c.tags : []
}

function updateField(caseId: string, field: string, value: any) {
  store.updateCaseField(caseId, field, value)
}

function addRow() {
  store.addCase()
  const f = activeFile.value
  if (f) (f.cases[f.cases.length - 1] as any)._activated = true
  selectedIds.value = []
}

function insertAbove(caseId: string) {
  const f = activeFile.value
  if (!f) return
  const idx = f.cases.findIndex(c => c.id === caseId)
  if (idx >= 0) {
    store.addCaseAt(idx)
    const f2 = activeFile.value
    if (f2) (f2.cases[idx] as any)._activated = true
  }
}

function insertBelow(caseId: string) {
  const f = activeFile.value
  if (!f) return
  const idx = f.cases.findIndex(c => c.id === caseId)
  if (idx >= 0) {
    store.addCaseAt(idx + 1)
    const f2 = activeFile.value
    if (f2) (f2.cases[idx + 1] as any)._activated = true
  }
}

function duplicateSingle(caseId: string) {
  store.duplicateCase(caseId)
}

function deleteSingle(caseId: string) {
  store.deleteCase(caseId)
  selectedIds.value = selectedIds.value.filter(id => id !== caseId)
}

function selectCase(id: string, event: MouseEvent) {
  if (isVirtualId(id)) { activateRow(id, 0); return }
  if (event.shiftKey && selectedIds.value.length > 0) {
    const f = activeFile.value
    if (!f) return
    const lastIdx = f.cases.findIndex(c => c.id === selectedIds.value[selectedIds.value.length - 1])
    const curIdx = f.cases.findIndex(c => c.id === id)
    if (lastIdx >= 0 && curIdx >= 0) {
      const start = Math.min(lastIdx, curIdx)
      const end = Math.max(lastIdx, curIdx)
      selectedIds.value = f.cases.slice(start, end + 1).map(c => c.id)
      return
    }
  }
  if (event.ctrlKey || event.metaKey) {
    const idx = selectedIds.value.indexOf(id)
    if (idx >= 0) selectedIds.value.splice(idx, 1)
    else selectedIds.value.push(id)
  } else {
    selectedIds.value = [id]
  }
}

function focusCell(caseId: string, key: string, event: MouseEvent) {
  const target = event.currentTarget as HTMLElement
  const textarea = target.querySelector('textarea, input:not([type="hidden"])') as HTMLElement
  if (textarea && !(textarea as HTMLInputElement).readOnly) {
    textarea.focus()
  }
}

function onTagInput(caseId: string, value: string) {
  if (value.endsWith(',') || value.endsWith('，')) {
    const tag = value.slice(0, -1).trim()
    if (tag) {
      commitSingleTag(caseId, tag)
    }
    tagInputs.value[caseId] = ''
  } else {
    tagInputs.value[caseId] = value
  }
}

function commitSingleTag(caseId: string, tag: string) {
  const f = activeFile.value
  if (!f) return
  const c = f.cases.find(c => c.id === caseId)
  if (!c) return
  if (!Array.isArray(c.tags)) c.tags = []
  if (!c.tags.includes(tag)) {
    c.tags.push(tag)
  }
}

function commitTag(caseId: string) {
  const val = tagInputs.value[caseId]?.trim()
  if (val) {
    commitSingleTag(caseId, val)
  }
  tagInputs.value[caseId] = ''
}

function backspaceTag(caseId: string) {
  const val = tagInputs.value[caseId]
  if (!val || val.length === 0) {
    const f = activeFile.value
    if (!f) return
    const c = f.cases.find(c => c.id === caseId)
    if (c && Array.isArray(c.tags) && c.tags.length > 0) {
      c.tags.pop()
    }
  }
}

function removeTag(caseId: string, tagIdx: number) {
  const f = activeFile.value
  if (!f) return
  const c = f.cases.find(c => c.id === caseId)
  if (c && Array.isArray(c.tags)) {
    c.tags.splice(tagIdx, 1)
  }
}

function priorityClass(p: string): string {
  const map: Record<string, string> = {
    P0: 'bg-error/15 text-error',
    P1: 'bg-orange-500/15 text-orange-600',
    P2: 'bg-secondary-fixed/20 text-secondary',
    P3: 'bg-white/30 text-on-surface-variant/60',
  }
  return map[p] || map.P2
}

// --- Context menu handlers ---

function cmClose() { contextMenu.value.show = false }

function cmInsertAbove() { if (contextMenu.value.targetId) insertAbove(contextMenu.value.targetId); cmClose() }
function cmInsertBelow() { if (contextMenu.value.targetId) insertBelow(contextMenu.value.targetId); cmClose() }
function cmDuplicate() { if (contextMenu.value.targetId) store.duplicateCase(contextMenu.value.targetId); cmClose() }
function cmDelete() { if (contextMenu.value.targetId) { store.deleteCase(contextMenu.value.targetId); selectedIds.value = selectedIds.value.filter(id => id !== contextMenu.value.targetId) }; cmClose() }

function cmAddColumn() {
  cmClose()
  editingColumnKey.value = ''
  columnForm.value = { key: '', label: '', type: 'text', optionsStr: '' }
  showColumnDialog.value = true
}

function cmEditField(key: string) {
  cmClose()
  const f = activeFile.value
  if (!f?.customFields) return
  const cf = f.customFields.find(c => c.key === key)
  if (!cf) return
  editingColumnKey.value = key
  columnForm.value = {
    key: cf.key,
    label: cf.label,
    type: cf.type,
    optionsStr: cf.options?.join(', ') || '',
  }
  showColumnDialog.value = true
}

function cmRemoveField(key: string) {
  cmClose()
  store.removeCustomField(key)
  const idx = visibleColumns.value.indexOf(key)
  if (idx >= 0) visibleColumns.value.splice(idx, 1)
}

let _menuCloseHandler: ((e: MouseEvent) => void) | null = null

function bindMenuClose() {
  if (_menuCloseHandler) document.removeEventListener('mousedown', _menuCloseHandler)
  _menuCloseHandler = (e: MouseEvent) => {
    const el = document.querySelector('[data-menu="context"]')
    if (el && !el.contains(e.target as Node)) {
      contextMenu.value.show = false
      document.removeEventListener('mousedown', _menuCloseHandler!)
      _menuCloseHandler = null
    }
  }
  // Delay to avoid the right-click event itself triggering close
  setTimeout(() => {
    document.addEventListener('mousedown', _menuCloseHandler!)
  }, 0)
}

function showContextMenu(event: MouseEvent) {
  contextMenu.value = { show: true, x: event.clientX, y: event.clientY, targetType: 'table' }
  bindMenuClose()
}

function showRowContextMenu(event: MouseEvent, c: CaseItem | { id: string; _virtual: true }, rowIdx: number) {
  if ((c as any)._virtual) {
    activateRow(c.id, rowIdx)
    return
  }
  if (!selectedIds.value.includes(c.id)) {
    selectedIds.value = [c.id]
  }
  contextMenu.value = { show: true, x: event.clientX, y: event.clientY, targetType: 'row', targetId: c.id }
  bindMenuClose()
}

function showColumnContextMenu(event: MouseEvent, col: { key: string; label: string }) {
  contextMenu.value = { show: true, x: event.clientX, y: event.clientY, targetType: 'header', targetCol: col.key }
  bindMenuClose()
}

function confirmColumn() {
  if (!columnForm.value.key.trim() || !columnForm.value.label.trim()) return
  const def: CustomFieldDef = {
    key: columnForm.value.key.trim(),
    label: columnForm.value.label.trim(),
    type: columnForm.value.type as 'text' | 'select' | 'textarea',
  }
  if (columnForm.value.type === 'select' && columnForm.value.optionsStr.trim()) {
    def.options = columnForm.value.optionsStr.split(',').map(s => s.trim()).filter(Boolean)
  }
  if (editingColumnKey.value) {
    store.updateCustomField(editingColumnKey.value, def)
  } else {
    store.addCustomField(def)
    if (!visibleColumns.value.includes(def.key)) {
      visibleColumns.value.push(def.key)
    }
  }
  showColumnDialog.value = false
}

function duplicateSelected() {
  selectedIds.value.forEach(id => store.duplicateCase(id))
}

function copySelected() {
  const f = activeFile.value
  if (!f) return
  const items = f.cases.filter(c => selectedIds.value.includes(c.id))
  if (items.length > 0) {
    navigator.clipboard.writeText(JSON.stringify(items, null, 2))
  }
}

function deleteSelected() {
  selectedIds.value.forEach(id => store.deleteCase(id))
  selectedIds.value = []
}


function resizeTextarea(ta: HTMLTextAreaElement) {
  ta.style.height = 'auto'
  const h = ta.scrollHeight
  if (h > 0) ta.style.height = h + 'px'
}

function initTextarea(el: any) {
  if (!el || !(el instanceof HTMLTextAreaElement)) return
  requestAnimationFrame(() => resizeTextarea(el as HTMLTextAreaElement))
}

function onTextareaInput(caseId: string, field: string, event: Event) {
  const ta = event.target as HTMLTextAreaElement
  updateField(caseId, field, ta.value)
  resizeTextarea(ta)
}

function goHome() {
  router.push('/case-space')
}

async function saveFile() {
  if (!store.activeFile) return
  const f = store.activeFile
  const content = f.cases.filter(c => hasContent(c))
  const backup = f.cases
  f.cases = content
  await store.saveFileToDb(f.id)
  f.cases = backup
  store.markSaved(f.id)
  await store.addToRecent(f.id, f.name, content.length, 'db://' + f.id)
  importStatus.value = "Saved to database"
  setTimeout(() => importStatus.value = "", 2000)
}

const showSaveAsDialog = ref(false)


async function saveAsExcel() {
  showSaveAsDialog.value = false
  if (!store.activeFile) return
  const f = store.activeFile
  const ws = XLSX.utils.json_to_sheet(
    f.cases.filter(c => hasContent(c)).map((c: any) => {
      const row: Record<string, any> = {}
      visibleCols.value.forEach(col => { row[col.label] = c[col.key] ?? '' })
      return row
    })
  )
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, 'Cases')
  const wbOut = XLSX.write(wb, { bookType: 'xlsx', type: 'array' })
  const blob = new Blob([wbOut], { type: 'application/octet-stream' })
  try {
    const { save } = await import('@tauri-apps/plugin-dialog')
    const { invoke } = await import('@tauri-apps/api/core')
    const path = await save({
      filters: [{ name: 'Excel Workbook', extensions: ['xlsx'] }],
      defaultPath: (f.name || 'cases') + '.xlsx',
    })
    if (path) {
      await invoke('write_text_file', { path, content: '' })
      // For binary data, use the fs plugin
      const { writeFile: fsWrite } = await import('@tauri-apps/plugin-fs')
      await fsWrite(path, new Uint8Array(wbOut))
      importStatus.value = "Excel exported"
      setTimeout(() => importStatus.value = "", 2000)
    }
  } catch {
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = (f.name || 'cases') + '.xlsx'
    a.click()
    URL.revokeObjectURL(url)
  }
}

async function saveAsPng() {
  showSaveAsDialog.value = false
  if (!store.activeFile) return
  const el = mindmapContainer.value
  if (!el) return
  try {
    const { toPng } = await import('html-to-image')
    const dataUrl = await toPng(el, { backgroundColor: '#F9F9FB' })
    const blob = await (await fetch(dataUrl)).blob()
    try {
      const { save } = await import('@tauri-apps/plugin-dialog')
      const { writeFile: fsWrite } = await import('@tauri-apps/plugin-fs')
      const path = await save({
        filters: [{ name: 'PNG Image', extensions: ['png'] }],
        defaultPath: (store.activeFile.name || 'mindmap') + '.png',
      })
      if (path) {
        const buf = await blob.arrayBuffer()
        await fsWrite(path, new Uint8Array(buf))
        importStatus.value = "Mind Map exported"
        setTimeout(() => importStatus.value = "", 2000)
      }
    } catch {
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = (store.activeFile.name || 'mindmap') + '.png'
      a.click()
      URL.revokeObjectURL(url)
    }
  } catch (e: any) {
    importStatus.value = "Export failed: " + (e.message || e)
    setTimeout(() => importStatus.value = "", 3000)
  }
}

const importStatus = ref("")

const EMPTY_ROW_COUNT = 200

function genId(): string {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 8)
}

function activateRow(virtualId: string, _rowIdx: number) {
  const f = activeFile.value
  if (!f || !isVirtualId(virtualId)) return
  const c: CaseItem = {
    id: genId(),
    module: '',
    title: '',
    precondition: '',
    steps: '',
    expected: '',
    priority: '',
    tags: [],
    assignee: '',
    remarks: '',
  }
  ;(c as any)._activated = true
  f.cases.push(c)
  f.updatedAt = new Date().toISOString()
}

function isEmptyCase(c: CaseItem): boolean {
  if ((c as any)._activated) return false
  if (c.title || c.steps || c.expected || c.precondition || c.module || c.remarks || c.assignee) return false
  if (c.tags && c.tags.length > 0) return false
  return true
}

function hasContent(c: CaseItem): boolean {
  if (c.title || c.steps || c.expected || c.precondition || c.module || c.remarks || c.assignee) return true
  if (c.tags && c.tags.length > 0) return true
  return false
}

function contentRows(): CaseItem[] {
  const f = activeFile.value
  if (!f) return []
  return f.cases.filter(c => !isEmptyCase(c))
}

const VIRTUAL_PREFIX = '__virtual__'

function isVirtualId(id: string): boolean {
  return id.startsWith(VIRTUAL_PREFIX)
}

const displayRows = computed<(CaseItem | { id: string; _virtual: true })[]>(() => {
  const f = activeFile.value
  if (!f) return []
  const content = contentRows()
  if (content.length >= EMPTY_ROW_COUNT) return content
  const pads: { id: string; _virtual: true }[] = []
  for (let i = 0; i < EMPTY_ROW_COUNT - content.length; i++) {
    pads.push({ id: VIRTUAL_PREFIX + content.length + i, _virtual: true })
  }
  return [...content, ...pads]
})

// Mind Map
const mindmapContainer = ref<HTMLElement>()
const mmZoom = ref(0.65)
const mmPan = ref({ x: 40, y: 40 })
const mmPanning = ref(false)
const mmPanStart = ref({ x: 0, y: 0 })
const mmPanOrigin = ref({ x: 0, y: 0 })

const mindMapTransform = computed(() => ({
  transform: `translate(${mmPan.value.x}px, ${mmPan.value.y}px) scale(${mmZoom.value})`,
  transformOrigin: '0 0',
}))

const spacing = 320

const mindMapModules = computed(() => {
  const f = activeFile.value
  if (!f) return []
  const groups: Record<string, CaseItem[]> = {}
  contentRows().forEach(c => {
    const key = c.module || '(No Module)'
    if (!groups[key]) groups[key] = []
    groups[key].push(c)
  })
  return Object.entries(groups).map(([name, cases], idx) => ({
    name, cases, count: cases.length, x: 0, y: idx * spacing, collapsed: false, renaming: false,
  }))
})

const mindMapLines = computed(() => {
  const paths: { path: string }[] = []
  mindMapModules.value.forEach((mod, idx) => {
    const my = idx * spacing + 30
    paths.push({ path: `M0,${my} Q80,${my} 160,${my}` })
    mod.cases.forEach((_c, cIdx) => {
      const cy = idx * spacing + 30 + (cIdx + 1) * 50
      paths.push({ path: `M160,${cy} Q240,${cy} 320,${cy}` })
    })
  })
  return paths
})

function navigateToCase(caseId: string) {
  viewMode.value = 'excel'
  selectedIds.value = [caseId]
}

function startRenameModule(mod: any) {
  mod.renaming = true
  nextTick(() => {
    if (renameInput.value) {
      renameInput.value.focus()
      renameInput.value.textContent = mod.name
    }
  })
}

function finishRenameModule(mod: any, event: Event) {
  const newName = (event.target as HTMLElement).textContent?.trim() || mod.name
  const f = activeFile.value
  if (f && newName !== mod.name) {
    f.cases.forEach(c => {
      if ((c.module || '(No Module)') === mod.name) c.module = newName
    })
  }
  mod.renaming = false
}

function onMindMapWheel(event: WheelEvent) {
  const delta = event.deltaY > 0 ? -0.05 : 0.05
  mmZoom.value = Math.max(0.2, Math.min(2, mmZoom.value + delta))
}

function onMindMapPanStart(event: MouseEvent) {
  if (event.button === 0) {
    mmPanning.value = true
    mmPanStart.value = { x: event.clientX, y: event.clientY }
    mmPanOrigin.value = { ...mmPan.value }
    const el = mindmapContainer.value
    if (el) el.style.cursor = 'grabbing'
  }
}

function onMindMapPan(event: MouseEvent) {
  if (!mmPanning.value) return
  mmPan.value = {
    x: mmPanOrigin.value.x + event.clientX - mmPanStart.value.x,
    y: mmPanOrigin.value.y + event.clientY - mmPanStart.value.y,
  }
}

function onMindMapPanEnd() {
  mmPanning.value = false
  const el = mindmapContainer.value
  if (el) el.style.cursor = 'grab'
}

function mmZoomIn() { mmZoom.value = Math.min(2, mmZoom.value + 0.15) }
function mmZoomOut() { mmZoom.value = Math.max(0.2, mmZoom.value - 0.15) }
function mmFit() { mmZoom.value = 0.65; mmPan.value = { x: 40, y: 40 } }

let handlingKey = false

function onKeydown(e: KeyboardEvent) {
  if ((e.ctrlKey || e.metaKey) && e.key === 's') {
    e.preventDefault()
    saveFile()
    return
  }
  if ((e.ctrlKey || e.metaKey) && e.key === 'd') {
    e.preventDefault()
    if (handlingKey) return
    handlingKey = true
    try {
      let id: string | undefined = selectedIds.value[selectedIds.value.length - 1]
      if (!id) {
        const tr = (e.target as HTMLElement)?.closest?.('[data-case-id]') as HTMLElement
        id = tr?.dataset?.caseId
      }
      if (id) duplicateSingle(id)
    } finally { setTimeout(() => { handlingKey = false }, 100) }
  }
}

// --- Virtual Scroll ---
const ROW_ESTIMATE = 48
const SCROLL_BUFFER = 10
const scrollBody = ref<HTMLDivElement>()
const measuredHeights = new Map<string, number>()
const virtualRows = shallowRef<{ item: any; index: number; top: number }[]>([])
const rowsHeight = ref(0)

const totalWidth = computed(() => {
  let w = 40
  visibleCols.value.forEach(col => {
    w += colWidths.value[col.key] || 140
  })
  w += 36
  return w
})

const gridTemplateCols = computed(() => {
  const parts: string[] = ['40px']
  visibleCols.value.forEach(col => {
    const cw = colWidths.value[col.key]
    parts.push(cw ? cw + 'px' : '1fr')
  })
  parts.push('36px')
  return parts.join(' ')
})

function updateVirtualRows() {
  const items = filteredSortedRows.value
  if (items.length === 0) {
    rowsHeight.value = 0
    virtualRows.value = []
    return
  }
  const el = scrollBody.value
  if (!el) return
  const st = el.scrollTop
  const ch = el.clientHeight
  const offsets: number[] = []
  let total = 0
  for (let i = 0; i < items.length; i++) {
    offsets[i] = total
    total += measuredHeights.get((items[i] as any).id) || ROW_ESTIMATE
  }
  rowsHeight.value = total
  let start = 0
  while (start < items.length && offsets[start] + (measuredHeights.get((items[start] as any).id) || ROW_ESTIMATE) <= st) start++
  let end = start
  while (end < items.length && offsets[end] < st + ch) end++
  start = Math.max(0, start - SCROLL_BUFFER)
  end = Math.min(items.length, end + SCROLL_BUFFER)
  const result: { item: any; index: number; top: number }[] = []
  for (let i = start; i < end; i++) {
    result.push({ item: items[i], index: i, top: offsets[i] })
  }
  virtualRows.value = result
}

let _scrollRaf = 0
function onBodyScroll() {
  if (_scrollRaf) return
  _scrollRaf = requestAnimationFrame(() => {
    updateVirtualRows()
    // Only observe when new unmeasured rows appear (avoids DOM queries on every scroll)
    const needsObserve = virtualRows.value.some(v => !measuredHeights.has((v.item as any).id))
    if (needsObserve) observeRenderedRows()
    _scrollRaf = 0
  })
}

let _resizeObserver: ResizeObserver | null = null
function ensureRowObserver() {
  if (_resizeObserver) return _resizeObserver
  _resizeObserver = new ResizeObserver(entries => {
    let changed = false
    for (const entry of entries) {
      const el = entry.target as HTMLElement
      const id = el.dataset.caseId
      if (id) {
        const h = entry.contentRect.height
        if (h > 0 && measuredHeights.get(id) !== h) {
          measuredHeights.set(id, h)
          changed = true
        }
      }
    }
    if (changed) updateVirtualRows()
  })
  return _resizeObserver
}

function observeRenderedRows() {
  // Use rAF to coalesce with initTextarea rAF and wait for layout to settle
  requestAnimationFrame(() => {
    let changed = false
    document.querySelectorAll('[data-case-id]').forEach(el => {
      const id = (el as HTMLElement).dataset.caseId
      if (id) {
        const h = (el as HTMLElement).offsetHeight
        if (h > 0 && measuredHeights.get(id) !== h) {
          measuredHeights.set(id, h)
          changed = true
        }
        ensureRowObserver().observe(el)
      }
    })
    if (changed) updateVirtualRows()
  })
}

watch(filteredSortedRows, () => {
  updateVirtualRows()
  observeRenderedRows()
})

onMounted(() => {
  document.addEventListener('keydown', onKeydown)
  updateVirtualRows()
  requestAnimationFrame(() => {
    // Wait for initTextarea rAF callbacks to resize textareas and layout to settle
    requestAnimationFrame(() => {
      document.querySelectorAll('[data-case-id]').forEach(el => {
        const id = (el as HTMLElement).dataset.caseId
        if (id) {
          const h = (el as HTMLElement).offsetHeight
          if (h > 0) measuredHeights.set(id, h)
          ensureRowObserver().observe(el)
        }
      })
      updateVirtualRows()
    })
  })
})

onUnmounted(() => {
  document.removeEventListener('keydown', onKeydown)
})

watch(viewMode, (v) => {
  if (v === 'mindmap') {
    nextTick(() => {
      const el = mindmapContainer.value
      if (el) el.style.cursor = 'grab'
    })
  }
})
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 6px; height: 6px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(0,0,0,0.08); border-radius: 3px; }
.mm-case-node { padding: 4px 8px; transition: background 0.15s; }
.line-clamp-2 { display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }

.cell-editor {
  width: 100%;
  background: transparent;
  border: none;
  outline: none;
  padding: 6px 8px;
  color: var(--on-surface, #1c1b1f);
  font-family: inherit;
  font-size: 13px;
  line-height: 1.5;
  resize: none;
  min-height: 32px;
  display: block;
  box-sizing: border-box;
  field-sizing: content;
  overflow-wrap: break-word;
  word-break: break-word;
  white-space: pre-wrap;
}
.cell-editor:hover {
  background: rgba(255,255,255,0.3);
}
.cell-editor:focus {
  background: rgba(255,255,255,0.55);
}
/* select element inside cell */
select.cell-editor {
  appearance: none;
  cursor: pointer;
  padding-right: 20px;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='rgba(0,0,0,0.3)' stroke-width='2'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 4px center;
}
</style>
