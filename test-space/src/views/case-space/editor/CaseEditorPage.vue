<template>
  <div class="flex flex-col h-screen -mx-margin-page select-none">
    <!-- Toolbar -->
    <div class="flex items-center gap-1 px-4 py-2 bg-white/20 backdrop-blur-sm border-b border-white/20 shrink-0 overflow-x-auto custom-scrollbar">
      <button class="glass-button px-3 py-1.5 rounded-lg font-caption text-caption flex items-center gap-1 shrink-0 select-none" title="Back to Home" @click="goHome">
        <span class="material-symbols-outlined text-[16px]">arrow_back</span>
        <span class="hidden sm:inline">Back</span>
      </button>
      <span class="w-px h-5 bg-white/30 mx-1 shrink-0"></span>
      <button class="glass-button px-3 py-1.5 rounded-lg font-caption text-caption flex items-center gap-1 shrink-0 select-none" title="Save" @click="saveFile">
        <span class="material-symbols-outlined text-[16px]">save</span>
        <span class="hidden sm:inline">Save</span>
      </button>
      <button class="glass-button px-3 py-1.5 rounded-lg font-caption text-caption flex items-center gap-1 shrink-0 select-none" title="Save As" @click="showSaveAsDialog = true">
        <span class="material-symbols-outlined text-[16px]">save_as</span>
        <span class="hidden sm:inline">Save As</span>
      </button>
      <span class="w-px h-5 bg-white/30 mx-1 shrink-0"></span>
      <button class="glass-button px-3 py-1.5 rounded-lg font-caption text-caption flex items-center gap-1 shrink-0 opacity-50 cursor-not-allowed select-none" title="Cloud Sync (Coming Soon)">
        <span class="material-symbols-outlined text-[16px]">cloud_sync</span>
        <span class="hidden sm:inline">Cloud</span>
      </button>
      <button class="glass-button px-3 py-1.5 rounded-lg font-caption text-caption flex items-center gap-1 shrink-0 opacity-50 cursor-not-allowed select-none" title="Platform Sync (Coming Soon)">
        <span class="material-symbols-outlined text-[16px]">sync</span>
        <span class="hidden sm:inline">Platform</span>
      </button>

      <div class="ml-auto flex items-center gap-1">
        <div class="glass-panel rounded-full p-0.5 inline-flex shadow-sm shrink-0">
          <button class="px-3 py-1.5 rounded-full font-caption text-caption flex items-center gap-1.5 transition-all select-none" :class="viewMode === 'excel' ? 'glass-active' : 'glass-button'" @click="viewMode = 'excel'">
            <span class="material-symbols-outlined text-[16px]">table_view</span>
            <span class="hidden sm:inline">Excel</span>
          </button>
          <button class="px-3 py-1.5 rounded-full font-caption text-caption flex items-center gap-1.5 transition-all select-none" :class="viewMode === 'mindmap' ? 'glass-active' : 'glass-button'" @click="viewMode = 'mindmap'">
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
            <span class="font-caption text-caption text-on-surface-variant/60">{{ contentRows.length }} cases</span>
          </div>
          <div class="flex items-center gap-1">
            <button class="glass-button px-2 py-1 rounded-lg text-caption flex items-center gap-1 select-none" @click="addRow">
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
                    <button class="p-0.5 rounded hover:bg-black/10 ml-auto shrink-0 select-none" :class="{ 'text-secondary': isFilterActive(col.key) }" @click.stop="openFilterPopup($event, col.key)">
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
                          <textarea :ref="initTextarea" :value="getCaseValue(entry.item as CaseItem, col.key) || ''" class="cell-editor select-text"
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
                            <button class="p-0 rounded-full ml-0.5 text-on-surface-variant/40 hover:text-error/60 select-none" @click.stop="removeTag((entry.item as CaseItem).id, tIdx)">
                              <span class="material-symbols-outlined text-[12px]">close</span>
                            </button>
                          </span>
                          <input :value="tagInputs[(entry.item as CaseItem).id] || ''" class="cell-editor min-w-[50px] max-w-[100px] select-text"
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
                        <textarea :ref="initTextarea" :value="getCaseValue(entry.item as CaseItem, col.key) || ''" class="cell-editor select-text"
                          @input="onTextareaInput((entry.item as CaseItem).id, col.key, $event)" @click.stop></textarea>
                      </template>
                      <template v-else>
                         <textarea :ref="initTextarea" :value="getCaseValue(entry.item as CaseItem, col.key)" class="cell-editor select-text"
                          @input="onTextareaInput((entry.item as CaseItem).id, col.key, $event)" @click.stop></textarea>
                      </template>
                    </div>
                    <div class="border-b border-gray-300/40 flex items-center justify-center gap-0 opacity-30 hover:opacity-80 transition-opacity">
                      <button class="p-0.5 rounded hover:bg-white/40 select-none" @click.stop="duplicateSingle((entry.item as CaseItem).id)" title="Duplicate">
                        <span class="material-symbols-outlined text-[14px] text-on-surface-variant/50">content_copy</span>
                      </button>
                      <button class="p-0.5 rounded hover:bg-white/40 select-none" @click.stop="store.deleteCase((entry.item as CaseItem).id)" title="Delete">
                        <span class="material-symbols-outlined text-[14px] text-on-surface-variant/50">delete</span>
                      </button>
                    </div>
                  </template>
                </div>
              </div>
            </div>
            <div v-if="contentRows.length === 0" class="flex items-center justify-center py-20">
              <div class="text-center">
                <span class="material-symbols-outlined text-4xl text-on-surface-variant/15">table_rows</span>
                <p class="font-body-md text-body-md text-on-surface-variant/50 mt-3">No test cases yet</p>
                <button class="mt-4 px-5 py-2 rounded-full glass-button inline-flex items-center gap-1.5 select-none" @click="addRow">
                  <span class="material-symbols-outlined text-[16px]">add</span>
                  Add First Case
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Status bar -->
        <div class="flex items-center justify-between px-3 py-1 border-t border-gray-300/50 bg-white/10 shrink-0">
          <span class="font-caption text-caption text-on-surface-variant/50">{{ contentRows.length }} rows</span>
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
              <button class="w-full flex items-center gap-2 px-3 py-1.5 text-[13px] text-on-surface glass-hover text-left select-none" @click="cmInsertAbove">
                <span class="material-symbols-outlined text-[16px]">expand_less</span> Insert Above
              </button>
              <button class="w-full flex items-center gap-2 px-3 py-1.5 text-[13px] text-on-surface glass-hover text-left select-none" @click="cmInsertBelow">
                <span class="material-symbols-outlined text-[16px]">expand_more</span> Insert Below
              </button>
              <button class="w-full flex items-center gap-2 px-3 py-1.5 text-[13px] text-on-surface glass-hover text-left select-none" @click="cmDuplicate">
                <span class="material-symbols-outlined text-[16px]">content_copy</span> Duplicate
              </button>
              <div class="border-t border-white/10"></div>
              <button class="w-full flex items-center gap-2 px-3 py-1.5 text-[13px] text-error glass-hover text-left select-none" @click="cmDelete">
                <span class="material-symbols-outlined text-[16px]">delete</span> Delete
              </button>
            </template>

            <!-- Header column context menu -->
            <template v-else-if="contextMenu.targetType === 'header'">
              <button class="w-full flex items-center gap-2 px-3 py-1.5 text-[13px] text-on-surface glass-hover text-left select-none" @click="cmAddColumn">
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
                  <button class="glass-button px-1 py-0.5 rounded text-[11px] select-none" @click.stop="cmEditField(col.key)">Edit</button>
                  <button class="glass-button px-1 py-0.5 rounded text-[11px] text-error/60 ml-1 select-none" @click.stop="cmRemoveField(col.key)">Del</button>
                </span>
              </div>
            </template>

            <!-- Table context menu -->
            <template v-else>
              <button class="w-full flex items-center gap-2 px-3 py-1.5 text-[13px] text-on-surface glass-hover text-left select-none" @click="addRow">
                <span class="material-symbols-outlined text-[16px]">add</span> Insert Row
              </button>
              <button class="w-full flex items-center gap-2 px-3 py-1.5 text-[13px] text-on-surface glass-hover text-left select-none" @click="cmAddColumn">
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
              <h3 class="font-headline-md text-headline-md text-on-surface font-semibold mb-4 select-none">{{ editingColumnKey ? 'Edit Column' : 'Add Column' }}</h3>
              <div class="flex flex-col gap-3">
                <div>
                  <label class="font-caption text-caption text-on-surface-variant/60 block mb-1">Key</label>
                  <input                     v-model="columnForm.key"
                    class="w-full bg-white/60 border border-gray-300/50 rounded-lg px-3 py-2 text-[13px] text-on-surface font-mono focus:outline-none focus:border-secondary/40 select-text"
                    placeholder="field_key"
                    :disabled="!!editingColumnKey"
                  />
                </div>
                <div>
                  <label class="font-caption text-caption text-on-surface-variant/60 block mb-1">Label</label>
                  <input                     v-model="columnForm.label"
                    class="w-full bg-white/60 border border-gray-300/50 rounded-lg px-3 py-2 text-[13px] text-on-surface focus:outline-none focus:border-secondary/40 select-text"
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
                  <input                     v-model="columnForm.optionsStr"
                    class="w-full bg-white/60 border border-gray-300/50 rounded-lg px-3 py-2 text-[13px] text-on-surface font-mono focus:outline-none focus:border-secondary/40 select-text"
                    placeholder="opt1, opt2, opt3"
                  />
                </div>
              </div>
              <div class="flex justify-end gap-2 mt-5">
                <button class="glass-button px-4 py-2 rounded-full text-caption select-none" @click="showColumnDialog = false">Cancel</button>
                <button class="glass-button px-4 py-2 rounded-full text-caption flex items-center gap-1 select-none" @click="confirmColumn">
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
          <h3 class="font-headline-md text-headline-md text-on-surface font-semibold mb-4 select-none">Export As</h3>
          <div class="flex flex-col gap-2">
            <button class="glass-button w-full px-4 py-3 rounded-xl font-label-md text-label-md flex items-center gap-3 text-left select-none" @click="saveAsExcel">
              <span class="material-symbols-outlined text-[20px]">table_chart</span>
              <div>
                <div>Excel (.xlsx)</div>
                <div class="font-caption text-caption text-on-surface-variant/60">Export to spreadsheet</div>
              </div>
            </button>
            <button class="glass-button w-full px-4 py-3 rounded-xl font-label-md text-label-md flex items-center gap-3 text-left select-none" @click="saveAsPng">
              <span class="material-symbols-outlined text-[20px]">account_tree</span>
              <div>
                <div>Mind Map (.png)</div>
                <div class="font-caption text-caption text-on-surface-variant/60">Export mind map as image</div>
              </div>
            </button>
          </div>
          <button class="glass-button w-full mt-3 px-4 py-2 rounded-xl font-caption text-caption text-on-surface-variant select-none" @click="showSaveAsDialog = false">Cancel</button>
        </div>
      </div>
    </Teleport>

    <!-- Status message -->
    <div v-if="importStatus" class="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 glass-panel rounded-full px-6 py-3 font-label-md text-label-md text-on-surface shadow-lg bg-white/90 backdrop-blur-sm">
      {{ importStatus }}
    </div>

    <!-- Mind Map View (Tree Layout) -->
    <div v-else-if="viewMode === 'mindmap' && activeFile" class="flex-1 relative overflow-hidden bg-white/10 m-3 rounded-xl border border-white/40 shadow-sm">
      <div class="absolute top-0 left-0 right-0 z-20 flex items-center justify-between px-3 py-1.5 bg-white/20 backdrop-blur-sm border-b border-white/20 rounded-t-xl">
        <div class="flex items-center gap-2">
          <span class="material-symbols-outlined text-[14px] text-on-surface-variant/50">account_tree</span>
          <span class="font-caption text-caption text-on-surface-variant/70">{{ activeFile.name }}</span>
          <span class="font-caption text-caption text-on-surface-variant/40">{{ contentRows.length }} cases</span>
        </div>
      </div>
      <div ref="mindmapContainer" class="w-full h-full cursor-grab pt-8" @wheel.prevent="onMindMapWheel">
        <div class="absolute inset-0" :style="mindMapTransform" @mousedown="onMindMapPanStart" @mousemove="onMindMapPan" @mouseup="onMindMapPanEnd" @mouseleave="onMindMapPanEnd">
          <!-- SVG Layer: Bézier connection curves -->
          <svg class="absolute inset-0 pointer-events-none" style="width: 100%; height: 100%; overflow: visible">
            <path v-for="(line, idx) in mmLines" :key="'l' + idx" :d="line.path" stroke="rgba(120,130,250,0.25)" stroke-width="2" fill="none" />
          </svg>

          <!-- Root node -->
          <div v-if="mmRoot"
            class="absolute glass-panel rounded-xl px-5 py-3 min-w-[160px] select-none z-10 border-l-[4px] border-primary/50 shadow-sm"
            :style="{ left: mmRoot.root.x + 'px', top: mmRoot.root.y + 'px', width: mmRoot.root.w + 'px' }"
          >
            <div class="flex items-center gap-2.5">
              <span class="material-symbols-outlined text-[22px] text-primary/50" style="font-variation-settings:'FILL'1">account_tree</span>
              <span class="font-label-md text-label-md text-on-surface font-semibold truncate">{{ mmRoot.root.label }}</span>
            </div>
          </div>

          <!-- Module nodes -->
          <div v-for="mod in mmModules" :key="mod.id"
            class="absolute glass-panel rounded-lg px-3 py-2 select-none z-10 glass-hover cursor-pointer"
            :class="[mod.moduleDepth === 0 ? 'border-l-[4px]' : 'border-l-[3px] border-secondary/30', { 'ring-2 ring-secondary/50': selectedMmNodeId === mod.id, 'opacity-50': mmDrag?.isDragging && mmDrag.node.id === mod.id }]"
            :style="{ left: mod.x + 'px', top: mod.y + 'px', width: mod.w + 'px', minHeight: mod.h + 'px', borderLeftColor: mod.data?.colorIdx != null ? MODULE_PALETTE[mod.data.colorIdx % MODULE_PALETTE.length] : undefined }"
            @mousedown.stop="onMmMouseDown($event, mod)"
            @dblclick.stop="startEditing(mod)"
            @contextmenu.prevent="openMmCtx($event, mod)"
          >
            <div class="flex items-start gap-1.5">
              <span class="text-[9px] font-medium px-1.5 py-0.5 rounded-full shrink-0 mt-0.5" :style="{ background: mod.data?.colorIdx != null ? MODULE_PALETTE[mod.data.colorIdx % MODULE_PALETTE.length] + '22' : '#88822', color: mod.data?.colorIdx != null ? MODULE_PALETTE[mod.data.colorIdx % MODULE_PALETTE.length] : '#888' }">{{ mod.fieldLabel }}</span>
              <textarea v-if="editingNodeId === mod.id" v-model="editingValue" data-mm-editor
                class="flex-1 min-w-0 bg-transparent border-b border-secondary/40 text-[13px] text-on-surface font-medium outline-none resize-none leading-snug select-text"
                :style="{ minHeight: '24px', height: 'auto' }"
                @input="autoResizeTextarea($event)"
                @blur="confirmEditing(mod)" @keydown.enter.prevent="confirmEditing(mod)" @keydown.escape.prevent="cancelEditing()"
                @mousedown.stop
              ></textarea>
              <span v-else class="text-[13px] text-on-surface font-medium flex-1 whitespace-pre-wrap break-words leading-snug">{{ mod.label }}</span>
              <span class="text-[10px] text-on-surface-variant/50 bg-white/30 rounded-full px-1.5 py-0.5 shrink-0 mt-0.5 whitespace-nowrap">{{ mod.data?.count }}</span>
              <button class="p-0.5 rounded hover:bg-white/30 shrink-0 mt-0.5 select-none" @click.stop="toggleCollapse(mod)">
                <span class="material-symbols-outlined text-[14px] text-on-surface-variant/40">{{ mod.collapsed ? 'chevron_right' : 'expand_more' }}</span>
              </button>
            </div>
          </div>

          <!-- Case nodes -->
          <div v-for="c in mmCases" :key="c.id"
            class="absolute glass-panel rounded-lg px-3 py-1.5 select-none z-10 cursor-pointer border-l-[4px] transition-shadow hover:shadow-md"
            :class="[caseBorderClass(c.data?.priority), { 'ring-2 ring-secondary/50': selectedMmNodeId === c.id, 'opacity-50': mmDrag?.isDragging && mmDrag.node.id === c.id }]"
            :style="{ left: c.x + 'px', top: c.y + 'px', width: c.w + 'px', minHeight: c.h + 'px' }"
            @mousedown.stop="onMmMouseDown($event, c)"
            @dblclick.stop="startEditing(c)"
            @contextmenu.prevent="openMmCtx($event, c)"
          >
            <div class="flex items-start gap-1.5">
              <span class="w-2 h-2 rounded-full shrink-0 mt-[5px]" :class="caseDotClass(c.data?.priority)"></span>
              <span class="text-[9px] font-medium px-1.5 py-0.5 rounded-full bg-secondary/10 text-secondary/70 shrink-0 mt-[1px]">{{ c.fieldLabel }}</span>
              <textarea v-if="editingNodeId === c.id" v-model="editingValue" data-mm-editor
                class="flex-1 min-w-0 bg-transparent border-b border-secondary/40 text-[12px] text-on-surface font-medium outline-none resize-none leading-snug select-text"
                :style="{ minHeight: '20px', height: 'auto' }"
                @input="autoResizeTextarea($event)"
                @blur="confirmEditing(c)" @keydown.enter.prevent="confirmEditing(c)" @keydown.escape.prevent="cancelEditing()"
                @mousedown.stop
              ></textarea>
              <span v-else class="text-[12px] text-on-surface font-medium flex-1 whitespace-pre-wrap break-words leading-snug">{{ c.label }}</span>
              <button v-if="c.children.length > 0" class="p-0.5 rounded hover:bg-white/30 shrink-0 self-start mt-[1px]" @click.stop="toggleCollapse(c)">
                <span class="material-symbols-outlined text-[12px] text-on-surface-variant/40">{{ c.collapsed ? 'chevron_right' : 'expand_more' }}</span>
              </button>
            </div>
          </div>

          <!-- Field nodes (precondition, steps, expected, priority, remarks) -->
          <div v-for="d in mmFields" :key="d.id"
            class="absolute rounded-lg px-2.5 py-1.5 select-none z-10 text-[11px] leading-snug cursor-pointer flex items-start gap-1.5 border"
            :class="[selectedMmNodeId === d.id ? 'ring-2 ring-secondary/50 bg-white/70 border-secondary/40' : 'bg-white/50 border-secondary/20']"
            :style="{ left: d.x + 'px', top: d.y + 'px', width: d.w + 'px', minHeight: d.h + 'px' }"
            @mousedown.stop="onMmMouseDown($event, d)"
            @dblclick.stop="startEditing(d)"
            @contextmenu.prevent="openMmCtx($event, d)"
          >
            <span class="text-[9px] font-medium px-1.5 py-0.5 rounded-full shrink-0 mt-[1px] text-white"
              :style="{ background: d.field === 'steps' ? '#3b82f6' : d.field === 'expected' ? '#10b981' : d.field === 'precondition' ? '#8b5cf6' : d.field === 'priority' ? '#f59e0b' : '#6b7280' }"
            >{{ d.fieldLabel }}</span>
            <textarea v-if="editingNodeId === d.id" v-model="editingValue" data-mm-editor
              class="flex-1 min-w-0 bg-transparent border-b border-secondary/40 text-[11px] text-on-surface font-medium outline-none resize-none leading-snug select-text"
              :style="{ minHeight: '40px', height: 'auto' }"
              @input="autoResizeTextarea($event)"
              @blur="confirmEditing(d)" @keydown.escape.prevent="cancelEditing()"
              @mousedown.stop
            ></textarea>
            <span v-else class="whitespace-pre-wrap break-words flex-1 leading-snug" :class="d.label ? 'text-on-surface-variant/70' : 'text-on-surface-variant/30 italic'">{{ d.label || t('case.clickToEdit') }}</span>
          </div>
        </div>
      </div>

      <!-- Drag ghost -->
      <div v-if="mmDrag?.isDragging"
        class="fixed pointer-events-none z-[60] opacity-80 bg-white/90 backdrop-blur-md rounded-lg px-3 py-1.5 text-[12px] text-on-surface font-medium shadow-lg border border-secondary/30 whitespace-nowrap"
        :style="{ left: (mmDrag.cursorX + 12) + 'px', top: (mmDrag.cursorY + 12) + 'px' }"
      >
        <span class="material-symbols-outlined text-[12px] text-secondary/50 mr-1 align-middle" style="font-variation-settings:'FILL'1">drag_indicator</span>
        {{ mmDrag.node.label }}
      </div>

      <div class="absolute bottom-4 left-4 glass-panel rounded-lg p-1 flex items-center gap-1 z-20 shadow-sm">
        <button class="glass-button w-7 h-7 rounded flex items-center justify-center select-none" @click="mmZoomIn"><span class="material-symbols-outlined text-[16px]">add</span></button>
        <div class="w-px h-4 bg-white/20"></div>
        <button class="glass-button w-7 h-7 rounded flex items-center justify-center select-none" @click="mmZoomOut"><span class="material-symbols-outlined text-[16px]">remove</span></button>
        <div class="w-px h-4 bg-white/20"></div>
        <button class="glass-button w-7 h-7 rounded flex items-center justify-center select-none" @click="mmFit"><span class="material-symbols-outlined text-[16px]">fit_screen</span></button>
        <div class="w-px h-4 bg-white/20"></div>
        <span class="w-10 h-7 flex items-center justify-center font-caption text-caption text-on-surface-variant">{{ Math.round(mmZoom * 100) }}%</span>
      </div>

      <!-- Mind Map toolbar -->
      <div class="absolute top-4 right-4 flex items-center gap-2 z-20">
        <button class="glass-button px-3 py-1.5 rounded-lg text-caption flex items-center gap-1 shadow-sm select-none" @click="mmAddNewCase">
          <span class="material-symbols-outlined text-[14px]">add</span>
          Case
        </button>
      </div>

      <!-- Mind Map Context Menu -->
      <Teleport to="body">
        <div v-if="mmCtx.show" data-menu="mm-ctx"
          class="fixed z-50 glass-panel rounded-xl py-1 shadow-lg border border-white/50 min-w-[180px]"
          :style="{ left: mmCtx.x + 'px', top: mmCtx.y + 'px' }"
          @mousedown.stop
        >
          <div class="px-3 py-1.5 font-caption text-caption text-on-surface-variant/60 border-b border-white/20">
            {{ mmCtx.node?.fieldLabel || (mmCtx.node?.type === 'root' ? 'Root' : mmCtx.node?.type) }}
          </div>
          <template v-if="mmCtx.node?.type === 'module'">
            <button class="w-full flex items-center gap-2 px-3 py-1.5 text-[13px] text-on-surface glass-hover text-left select-none" @click="mmCtxAddCase">
              <span class="material-symbols-outlined text-[16px]">add</span> Add Case
            </button>
            <button class="w-full flex items-center gap-2 px-3 py-1.5 text-[13px] text-on-surface glass-hover text-left select-none" @click="mmCtxAddSibling">
              <span class="material-symbols-outlined text-[16px]">add</span> Add Sibling Module
            </button>
            <button class="w-full flex items-center gap-2 px-3 py-1.5 text-[13px] text-on-surface glass-hover text-left select-none" @click="mmCtxRename">
              <span class="material-symbols-outlined text-[16px]">edit</span> Rename
            </button>
          </template>
          <template v-if="mmCtx.node?.type === 'case'">
            <button class="w-full flex items-center gap-2 px-3 py-1.5 text-[13px] text-on-surface glass-hover text-left select-none" @click="mmCtxAddSibling">
              <span class="material-symbols-outlined text-[16px]">add</span> Add Sibling
            </button>
            <button class="w-full flex items-center gap-2 px-3 py-1.5 text-[13px] text-on-surface glass-hover text-left select-none" @click="mmCtxRename">
              <span class="material-symbols-outlined text-[16px]">edit</span> Rename
            </button>
            <div class="border-t border-white/10"></div>
            <button class="w-full flex items-center gap-2 px-3 py-1.5 text-[13px] text-error glass-hover text-left select-none" @click="mmCtxDelete">
              <span class="material-symbols-outlined text-[16px]">delete</span> Delete
            </button>
          </template>
        </div>
      </Teleport>

      <!-- Tab Prompt -->
      <Teleport to="body">
        <div v-if="mmTabPrompt.show" data-menu="mm-tab-prompt"
          class="fixed z-50 glass-panel rounded-xl py-1 shadow-lg border border-white/50 min-w-[160px]"
          :style="{ left: mmTabPrompt.x + 'px', top: mmTabPrompt.y + 'px' }"
          @mousedown.stop
        >
          <div class="px-3 py-1.5 font-caption text-caption text-on-surface-variant/60 border-b border-white/20">{{ t('case.addChild') }}</div>
          <button class="w-full flex items-center gap-2 px-3 py-1.5 text-[13px] text-on-surface glass-hover text-left select-none" @click="mmTabAddModule">
            <span class="material-symbols-outlined text-[16px]">create_new_folder</span> {{ t('case.subModule') }}
          </button>
          <button class="w-full flex items-center gap-2 px-3 py-1.5 text-[13px] text-on-surface glass-hover text-left select-none" @click="mmTabAddCase">
            <span class="material-symbols-outlined text-[16px]">description</span> {{ t('case.caseTitle') }}
          </button>
        </div>
      </Teleport>

      <!-- end mindmap -->
    </div>
  </div>

  <Teleport to="body">
    <div v-if="activeFilterCol" class="fixed inset-0 z-50" @click="closeFilterPopup">
      <div class="absolute bg-white rounded-lg shadow-xl border border-gray-200 py-1 text-[13px] min-w-[180px] max-h-[320px] overflow-y-auto" :style="{ top: filterPopupPos.top + 'px', left: filterPopupPos.left + 'px' }" @click.stop>
        <div class="px-3 py-1 text-[12px] font-medium text-gray-500">Sort</div>
        <button class="w-full flex items-center gap-2 px-3 py-1.5 hover:bg-gray-100 text-left select-none" :class="{ 'font-bold text-secondary': sortState?.key === activeFilterCol && sortState?.dir === 'asc' }" @click="setSort(activeFilterCol!, 'asc')">
          <span class="material-symbols-outlined text-[14px]">arrow_upward</span> Sort A→Z
        </button>
        <button class="w-full flex items-center gap-2 px-3 py-1.5 hover:bg-gray-100 text-left select-none" :class="{ 'font-bold text-secondary': sortState?.key === activeFilterCol && sortState?.dir === 'desc' }" @click="setSort(activeFilterCol!, 'desc')">
          <span class="material-symbols-outlined text-[14px]">arrow_downward</span> Sort Z→A
        </button>
        <div v-if="sortState" class="border-t border-gray-200 my-1">
          <button class="w-full flex items-center gap-2 px-3 py-1.5 hover:bg-gray-100 text-left text-gray-500 select-none" @click="clearSort">
            <span class="material-symbols-outlined text-[14px]">close</span> Clear Sort
          </button>
        </div>
        <div class="border-t border-gray-200 my-1"></div>
        <div class="px-3 py-1 flex items-center justify-between">
          <span class="text-[12px] font-medium text-gray-500">Filter by value</span>
          <button v-if="isFilterActive(activeFilterCol!)" class="text-[11px] text-secondary hover:underline select-none" @click="clearColumnFilter(activeFilterCol!)">Clear</button>
        </div>
        <label v-for="val in getUniqueValues(activeFilterCol!)" :key="val" class="flex items-center gap-2 px-3 py-1 hover:bg-gray-100 cursor-pointer">
          <input type="checkbox" :checked="columnFilters[activeFilterCol!]?.has(val)" @change="toggleFilterValue(activeFilterCol!, val)" class="accent-secondary select-text" />
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
import { useI18n } from '@/composables/useI18n'
import type { CaseFile, CaseItem, CustomFieldDef } from '@/types'
import * as XLSX from 'xlsx'

const router = useRouter()
const store = useCaseFileStore()
const { t } = useI18n()

const viewMode = ref<'excel' | 'mindmap'>('excel')
const selectedIds = ref<string[]>([])
const contextMenu = ref<{ show: boolean; x: number; y: number; targetType: 'table' | 'row' | 'header'; targetId?: string; targetCol?: string }>({ show: false, x: 0, y: 0, targetType: 'table' })
const showColumnDialog = ref(false)
const editingColumnKey = ref('')
const tagInputs = ref<Record<string, string>>({})
const colWidths = ref<Record<string, number>>({})
const resizing = ref<{ key: string; startX: number; startW: number } | null>(null)

const _docListeners = new Map<string, EventListenerOrEventListenerObject>()

function trackDocListener(event: string, handler: EventListenerOrEventListenerObject, options?: boolean | AddEventListenerOptions) {
  document.addEventListener(event, handler, options)
  _docListeners.set(event + '_' + _docListeners.size, handler)
}

let _offsetCacheItems: any[] | null = null
let _offsetCacheResult: { offsets: number[]; total: number } | null = null

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
  trackDocListener('mousemove', onResizeMove as EventListener)
  trackDocListener('mouseup', onResizeEnd as EventListener)
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
    trackDocListener('mousedown', _menuCloseHandler! as EventListener)
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
    navigator.clipboard.writeText(JSON.stringify(items, null, 2)).catch(() => {})
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

const _textareaRafMap = new WeakMap<HTMLElement, number>()

function initTextarea(el: any) {
  if (!el || !(el instanceof HTMLTextAreaElement)) return
  const existing = _textareaRafMap.get(el)
  if (existing) cancelAnimationFrame(existing)
  const id = requestAnimationFrame(() => {
    _textareaRafMap.delete(el)
    resizeTextarea(el as HTMLTextAreaElement)
  })
  _textareaRafMap.set(el, id)
}

function onTextareaInput(caseId: string, field: string, event: Event) {
  const ta = event.target as HTMLTextAreaElement
  updateField(caseId, field, ta.value)
  resizeTextarea(ta)
}

function goHome() {
  router.push('/case-space')
}

let _isSaving = false

async function saveFile() {
  if (!store.activeFile || _isSaving) return
  _isSaving = true
  const f = store.activeFile
  const content = f.cases.filter(c => hasContent(c))
  const contentCopy = JSON.parse(JSON.stringify(content))
  const backup = f.cases
  f.cases = contentCopy
  try {
    await store.saveFileToDb(f.id)
    store.markSaved(f.id)
    await store.addToRecent(f.id, f.name, content.length, 'db://' + f.id)
    importStatus.value = "Saved to database"
    setTimeout(() => importStatus.value = "", 2000)
  } finally {
    f.cases = backup
    _isSaving = false
  }
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
  const f = activeFile.value
  if (f?.customFields) {
    for (const cf of f.customFields) {
      const val = (c as any)[cf.key]
      if (val != null && val !== '' && !(Array.isArray(val) && val.length === 0)) return false
    }
  }
  return true
}

function hasContent(c: CaseItem): boolean {
  if (c.title || c.steps || c.expected || c.precondition || c.module || c.remarks || c.assignee) return true
  if (c.tags && c.tags.length > 0) return true
  const f = activeFile.value
  if (f?.customFields) {
    for (const cf of f.customFields) {
      const val = (c as any)[cf.key]
      if (val != null && val !== '' && !(Array.isArray(val) && val.length === 0)) return true
    }
  }
  return false
}

const contentRows = computed<CaseItem[]>(() => {
  const f = activeFile.value
  if (!f) return []
  return f.cases.filter(c => !isEmptyCase(c))
})

const VIRTUAL_PREFIX = '__virtual__'

function isVirtualId(id: string): boolean {
  return id.startsWith(VIRTUAL_PREFIX)
}

const displayRows = computed<(CaseItem | { id: string; _virtual: true })[]>(() => {
  const f = activeFile.value
  if (!f) return []
  const content = contentRows.value
  if (content.length >= EMPTY_ROW_COUNT) return content
  const pads: { id: string; _virtual: true }[] = []
  for (let i = 0; i < EMPTY_ROW_COUNT - content.length; i++) {
    pads.push({ id: VIRTUAL_PREFIX + content.length + i, _virtual: true })
  }
  return [...content, ...pads]
})

// ============= Mind Map (Tree Layout) =============

interface MNode {
  id: string
  type: string
  label: string
  fieldLabel: string
  x: number
  y: number
  w: number
  h: number
  children: MNode[]
  collapsed: boolean
  field?: string
  moduleDepth?: number
  data?: Record<string, any>
}

interface ModuleTree {
  name: string
  children: Record<string, ModuleTree>
  cases: CaseItem[]
}

const mindmapContainer = ref<HTMLElement>()
const mmZoom = ref(0.65)
const mmPan = ref({ x: 40, y: 60 })
const mmPanning = ref(false)
const mmPanStart = ref({ x: 0, y: 0 })
const mmPanOrigin = ref({ x: 0, y: 0 })

const mmCollapsedMods = ref<Set<string>>(new Set())

const MODULE_PALETTE = [
  '#6366f1', '#f59e0b', '#10b981', '#ef4444',
  '#8b5cf6', '#06b6d4', '#f97316', '#ec4899',
  '#84cc16', '#14b8a6',
]

function toggleCollapse(node: MNode) {
  const s = new Set(mmCollapsedMods.value)
  if (s.has(node.id)) s.delete(node.id)
  else s.add(node.id)
  mmCollapsedMods.value = s
}

const MM_H: Record<string, number> = { root: 120, module: 140, case: 100, field: 80 }
const MM_V: Record<string, number> = { root: 0, module: 20, case: 8, field: 6 }

interface MindMapResult {
  root: MNode
  modules: MNode[]
  cases: MNode[]
  fields: MNode[]
  lines: { path: string }[]
}

const mmRoot = computed<MindMapResult | null>(() => {
  const f = activeFile.value
  if (!f) return null
  return buildMindMap(f)
})

const mmModules = computed(() => mmRoot.value?.modules ?? [])
const mmCases = computed(() => mmRoot.value?.cases ?? [])
const mmFields = computed(() => mmRoot.value?.fields ?? [])
const mmLines = computed(() => mmRoot.value?.lines ?? [])

const mindMapTransform = computed(() => ({
  transform: `translate(${mmPan.value.x}px, ${mmPan.value.y}px) scale(${mmZoom.value})`,
  transformOrigin: '0 0',
}))

function computeNodeHeight(text: string, width: number, fontSize: number, minH: number): number {
  if (!text) return minH
  const charW = fontSize >= 13 ? 14 : fontSize >= 12 ? 12 : 10
  const availWidth = width - 24
  const charsPerLine = Math.max(1, Math.floor(availWidth / charW))
  let totalLines = 0
  for (const line of text.split('\n')) {
    totalLines += Math.max(1, Math.ceil(line.length / charsPerLine))
  }
  return Math.max(minH, totalLines * (fontSize * 1.4) + 14)
}

function computeFieldHeight(text: string): number {
  if (!text) return 28
  const charW = 10
  const badgeW = 42
  const paddingW = 20
  const availWidth = 300 - paddingW - badgeW
  const charsPerLine = Math.max(1, Math.floor(availWidth / charW))
  let totalLines = 0
  for (const line of text.split('\n')) {
    totalLines += Math.max(1, Math.ceil(line.length / charsPerLine))
  }
  return Math.max(28, totalLines * 15 + 14)
}

function buildMindMap(f: CaseFile): MindMapResult {
  const root: MNode = {
    id: 'root', type: 'root',
    label: f.name || 'Untitled',
    fieldLabel: '',
    x: 0, y: 0, w: 220, h: 50,
    children: [], collapsed: false,
  }

  // Build module tree by splitting module paths on '/'
  const moduleRoot: ModuleTree = { name: '', children: {}, cases: [] }
  for (const c of contentRows.value) {
    const parts = (c.module || '').split('/').filter(Boolean)
    let current = moduleRoot
    for (const part of parts) {
      if (!current.children[part]) {
        current.children[part] = { name: part, children: {}, cases: [] }
      }
      current = current.children[part]
    }
    current.cases.push(c)
  }

  function treeToNodes(tree: ModuleTree, depth: number, parentPath: string): MNode[] {
    const nodes: MNode[] = []
    const entries = Object.entries(tree.children)
    for (let i = 0; i < entries.length; i++) {
      const [name, child] = entries[i]
      const path = parentPath ? parentPath + '/' + name : name
      const modId = 'mod_' + path
      const modNode: MNode = {
        id: modId,
        type: 'module',
        label: name,
        fieldLabel: depth === 0 ? t('case.module') : t('case.subModule'),
        x: 0, y: 0, w: 240, h: computeNodeHeight(name, 240, 13, 42),
        children: [],
        collapsed: mmCollapsedMods.value.has(modId),
        moduleDepth: depth,
        data: { path, count: child.cases.length, colorIdx: depth === 0 ? i : -1 },
      }

      modNode.children.push(...treeToNodes(child, depth + 1, path))

      for (const c of child.cases) {
        const caseId = 'case_' + c.id
        const caseNode: MNode = {
          id: caseId,
          type: 'case',
          label: c.title || '(No Title)',
          fieldLabel: t('case.testCase'),
          x: 0, y: 0, w: 300, h: computeNodeHeight(c.title || '(No Title)', 300, 12, 36),
          children: [],
          collapsed: mmCollapsedMods.value.has(caseId),
          data: { caseId: c.id, priority: c.priority, casePath: path },
        }

        const fieldDefs: [string, string, string][] = [
          ['precondition', t('case.precondition'), c.precondition],
          ['steps', t('case.steps'), c.steps],
          ['expected', t('case.expected'), c.expected],
          ['priority', t('case.priority'), c.priority],
          ['remarks', t('case.remarks'), c.remarks],
        ]

        let lastFieldParent = caseNode
        for (const [fieldKey, fieldLabel, value] of fieldDefs) {
          const fieldNode: MNode = {
            id: fieldKey + '_' + c.id,
            type: 'field',
            label: value?.trim() || '',
            fieldLabel,
            x: 0, y: 0, w: 300, h: Math.max(28, computeFieldHeight(value || '')),
            children: [], collapsed: false,
            field: fieldKey,
            data: { caseId: c.id },
          }
          lastFieldParent.children.push(fieldNode)
          lastFieldParent = fieldNode
        }

        modNode.children.push(caseNode)
      }

      nodes.push(modNode)
    }
    return nodes
  }

  root.children = treeToNodes(moduleRoot, 0, '')

  computeSubtreeHeights(root)
  positionNode(root, 40, 80)

  const modules: MNode[] = []
  const cases: MNode[] = []
  const fields: MNode[] = []
  collectNodes(root, modules, cases, fields)

  const lines: { path: string }[] = []
  generateLines(root, lines)

  return { root, modules, cases, fields, lines }
}

function computeSubtreeHeights(node: MNode) {
  if (node.children.length === 0 || node.collapsed) {
    ;(node as any)._sh = node.h
    return
  }
  node.children.forEach(computeSubtreeHeights)
  let total = 0
  for (const ch of node.children) {
    total += (ch as any)._sh
  }
  const gaps = (node.children.length - 1) * (MM_V[node.children[0].type] || 10)
  ;(node as any)._sh = Math.max(node.h, total + gaps)
}

function positionNode(node: MNode, x: number, topY: number) {
  node.x = x
  const sh = (node as any)._sh

  if (node.children.length === 0 || node.collapsed) {
    node.y = topY
    return
  }

  node.y = topY + (sh - node.h) / 2

  const childX = x + node.w + (MM_H[node.type] || 200)
  let cy = topY

  for (const child of node.children) {
    positionNode(child, childX, cy)
    cy += (child as any)._sh + (MM_V[child.type] || 10)
  }
}

function collectNodes(node: MNode, modules: MNode[], cases: MNode[], fields: MNode[]) {
  if (node.type === 'module') modules.push(node)
  else if (node.type === 'case') cases.push(node)
  else if (node.type === 'field') fields.push(node)
  if (!node.collapsed) {
    node.children.forEach(ch => collectNodes(ch, modules, cases, fields))
  }
}

function generateLines(node: MNode, lines: { path: string }[]) {
  if (node.children.length === 0 || node.collapsed) return

  const sx = node.x + node.w
  const sy = node.y + node.h / 2

  for (const child of node.children) {
    const ex = child.x
    const ey = child.y + child.h / 2
    const dx = Math.max(60, ex - sx)
    lines.push({
      path: `M${sx},${sy} C${sx + dx * 0.4},${sy} ${ex - dx * 0.4},${ey} ${ex},${ey}`,
    })
    generateLines(child, lines)
  }
}

// ============= Mind Map Interaction =============

const selectedMmNodeId = ref<string | null>(null)
const editingNodeId = ref<string | null>(null)
const editingValue = ref('')
const mmCtx = ref<{ show: boolean; x: number; y: number; node: MNode | null }>({ show: false, x: 0, y: 0, node: null })
const mmTabPrompt = ref<{ show: boolean; x: number; y: number; node: MNode | null }>({ show: false, x: 0, y: 0, node: null })

const mmDrag = ref<{ node: MNode; startX: number; startY: number; cursorX: number; cursorY: number; ghostX: number; ghostY: number; isDragging: boolean } | null>(null)

let _mmCtxHandler: ((e: MouseEvent) => void) | null = null
let _mmTabPromptHandler: ((e: MouseEvent) => void) | null = null
let _mmDragMoveHandler: ((e: MouseEvent) => void) | null = null
let _mmDragEndHandler: ((e: MouseEvent) => void) | null = null

const mmAllNodes = computed(() => {
  const result: MNode[] = []
  if (!mmRoot.value) return result
  result.push(mmRoot.value.root)
  result.push(...mmRoot.value.modules)
  result.push(...mmRoot.value.cases)
  result.push(...mmRoot.value.fields)
  return result
})

const pendingMmFocusId = ref<string | null>(null)

watch(mmAllNodes, () => {
  const targetId = pendingMmFocusId.value
  if (!targetId) return
  const targetNode = mmAllNodes.value.find(n => n.id === targetId)
  if (targetNode) {
    pendingMmFocusId.value = null
    editingNodeId.value = targetId
    editingValue.value = targetNode.label
    selectedMmNodeId.value = targetId
    nextTick(() => {
      nextTick(() => {
        const el = document.querySelector('[data-mm-editor]') as HTMLTextAreaElement
        if (el) { el.focus(); el.select(); autoResizeTextarea({ target: el } as any) }
      })
    })
  }
})

function modIdToName(id: string): string {
  return id.startsWith('mod_') ? id.slice(4) : id
}

function selectMmNode(node: MNode) {
  if (editingNodeId.value) return
  selectedMmNodeId.value = node.id
}

function getSelectedMmNode(): MNode | undefined {
  return mmAllNodes.value.find(n => n.id === selectedMmNodeId.value)
}

function getSelectedMmIdx(): number {
  return mmAllNodes.value.findIndex(n => n.id === selectedMmNodeId.value)
}

// ===== Inline Editing =====

function startEditing(node: MNode) {
  editingNodeId.value = node.id
  editingValue.value = node.label
  selectedMmNodeId.value = node.id
  nextTick(() => {
    const el = document.querySelector('[data-mm-editor]') as HTMLTextAreaElement
    if (el) {
      el.focus()
      el.select()
      autoResizeTextarea({ target: el } as any)
    }
  })
}

function autoResizeTextarea(e: Event) {
  const el = e.target as HTMLTextAreaElement
  if (!el) return
  el.style.height = 'auto'
  el.style.height = el.scrollHeight + 'px'
}

function confirmEditing(node: MNode) {
  if (editingNodeId.value !== node.id) return
  const newVal = editingValue.value
  if (newVal !== node.label) {
    if (node.type === 'module') {
      const f = activeFile.value
      if (f && node.data?.path) {
        const oldPath = node.data.path
        f.cases.forEach(c => {
          if (c.module === oldPath) c.module = newVal
          else if (c.module?.startsWith(oldPath + '/')) {
            c.module = newVal + c.module.slice(oldPath.length)
          }
        })
      }
    } else if (node.type === 'case') {
      const id = node.data?.caseId
      if (id) store.updateCaseField(id, 'title', newVal)
    } else if (node.type === 'field') {
      const id = node.data?.caseId
      if (id && node.field) store.updateCaseField(id, node.field, newVal)
    }
  }
  editingNodeId.value = null
  editingValue.value = ''
}

function cancelEditing() {
  editingNodeId.value = null
  editingValue.value = ''
}

// ===== Tab Prompt =====

function showTabPrompt(node: MNode) {
  const rect = mindmapContainer.value?.getBoundingClientRect()
  if (!rect) return
  const x = rect.left + (node.x + node.w) * mmZoom.value + mmPan.value.x
  const y = rect.top + (node.y + node.h / 2) * mmZoom.value + mmPan.value.y
  mmTabPrompt.value = { show: true, x, y, node }
  if (_mmTabPromptHandler) document.removeEventListener('mousedown', _mmTabPromptHandler)
  _mmTabPromptHandler = (ev: MouseEvent) => {
    const el = document.querySelector('[data-menu="mm-tab-prompt"]')
    if (el && !el.contains(ev.target as Node)) {
      mmTabPrompt.value.show = false
      document.removeEventListener('mousedown', _mmTabPromptHandler!)
      _mmTabPromptHandler = null
    }
  }
  setTimeout(() => trackDocListener('mousedown', _mmTabPromptHandler! as EventListener), 0)
}

function mmTabAddModule() {
  const node = mmTabPrompt.value.node
  if (node?.type === 'module' && node.data?.path) {
    const newPath = node.data.path + '/New Module'
    const id = addCaseToFile(newPath)
    if (id) selectedMmNodeId.value = 'case_' + id
  }
  mmTabPrompt.value.show = false
}

function mmTabAddCase() {
  const node = mmTabPrompt.value.node
  if (node?.type === 'module' && node.data?.path) {
    const id = addCaseToFile(node.data.path)
    if (id) selectedMmNodeId.value = 'case_' + id
  }
  mmTabPrompt.value.show = false
}

// ===== Drag & Drop =====

function getNodeAtPoint(cx: number, cy: number): MNode | null {
  for (const node of mmAllNodes.value) {
    if (node.type === 'root') continue
    if (cx >= node.x && cx <= node.x + node.w &&
        cy >= node.y && cy <= node.y + node.h) {
      return node
    }
  }
  return null
}

function onMmMouseDown(e: MouseEvent, node: MNode) {
  if (e.button !== 0 || editingNodeId.value) return
  selectMmNode(node)
  if (node.type !== 'case') return

  const rect = mindmapContainer.value?.getBoundingClientRect()
  if (!rect) return

  mmDrag.value = {
    node,
    startX: e.clientX,
    startY: e.clientY,
    cursorX: e.clientX,
    cursorY: e.clientY,
    ghostX: node.x,
    ghostY: node.y,
    isDragging: false,
  }

  _mmDragMoveHandler = (ev: MouseEvent) => {
    if (!mmDrag.value) return
    mmDrag.value.cursorX = ev.clientX
    mmDrag.value.cursorY = ev.clientY
    const dx = Math.abs(ev.clientX - mmDrag.value.startX)
    const dy = Math.abs(ev.clientY - mmDrag.value.startY)
    if (!mmDrag.value.isDragging && (dx > 5 || dy > 5)) {
      mmDrag.value.isDragging = true
    }
    if (mmDrag.value.isDragging) {
      mmDrag.value.ghostX = (ev.clientX - rect.left - mmPan.value.x) / mmZoom.value - mmDrag.value.node.w / 2
      mmDrag.value.ghostY = (ev.clientY - rect.top - mmPan.value.y) / mmZoom.value - mmDrag.value.node.h / 2
    }
  }

  _mmDragEndHandler = (ev: MouseEvent) => {
    if (!mmDrag.value) return
    const wasDragging = mmDrag.value.isDragging
    if (wasDragging && mmDrag.value.node.type === 'case') {
      const cx = (ev.clientX - rect.left - mmPan.value.x) / mmZoom.value
      const cy = (ev.clientY - rect.top - mmPan.value.y) / mmZoom.value
      const target = getNodeAtPoint(cx, cy)
      if (target && target.id !== mmDrag.value.node.id) {
        const caseId = mmDrag.value.node.data?.caseId
        if (target.type === 'module' && caseId) {
          const newPath = target.data?.path || ''
          store.updateCaseField(caseId, 'module', newPath)
        } else if (target.type === 'case' && caseId) {
          const f = activeFile.value
          if (f) {
            const srcIdx = f.cases.findIndex(c => c.id === caseId)
            const tgtIdx = f.cases.findIndex(c => c.id === target.data?.caseId)
            if (srcIdx >= 0 && tgtIdx >= 0) {
              const [moved] = f.cases.splice(srcIdx, 1)
              f.cases.splice(tgtIdx, 0, moved)
            }
          }
        }
      }
    }
    mmDrag.value = null
    document.removeEventListener('mousemove', _mmDragMoveHandler!)
    document.removeEventListener('mouseup', _mmDragEndHandler!)
    _mmDragMoveHandler = null
    _mmDragEndHandler = null
  }

  trackDocListener('mousemove', _mmDragMoveHandler as EventListener)
  trackDocListener('mouseup', _mmDragEndHandler as EventListener)
}

// ===== Context Menu =====

function openMmCtx(e: MouseEvent, node: MNode) {
  if (editingNodeId.value) return
  selectedMmNodeId.value = node.id
  mmCtx.value = { show: true, x: e.clientX, y: e.clientY, node }
  if (_mmCtxHandler) document.removeEventListener('mousedown', _mmCtxHandler)
  _mmCtxHandler = (ev: MouseEvent) => {
    const el = document.querySelector('[data-menu="mm-ctx"]')
    if (el && !el.contains(ev.target as Node)) {
      mmCtx.value.show = false
      document.removeEventListener('mousedown', _mmCtxHandler!)
      _mmCtxHandler = null
    }
  }
  setTimeout(() => trackDocListener('mousedown', _mmCtxHandler! as EventListener), 0)
}

function addCaseToFile(moduleName: string = ''): string | null {
  const f = activeFile.value
  if (!f) return null
  const id = genId()
  const c: CaseItem = {
    id, module: moduleName,
    title: '', precondition: '', steps: '', expected: '',
    priority: '', tags: [], assignee: '', remarks: '',
  };
  (c as any)._activated = true
  f.cases.push(c)
  f.updatedAt = new Date().toISOString()
  return id
}

function createCaseAndEdit(moduleName: string) {
  const id = addCaseToFile(moduleName)
  if (!id) return
  const nodeId = 'case_' + id
  selectedMmNodeId.value = nodeId
  nextTick(() => {
    const node = getSelectedMmNode()
    if (node) startEditing(node)
  })
}

function mmAddNewCase() {
  const id = addCaseToFile()
  if (id) selectedMmNodeId.value = 'case_' + id
}

function mmCtxAddCase() {
  const mod = mmCtx.value.node
  if (mod?.type === 'module') {
    const path = mod.data?.path || ''
    const id = addCaseToFile(path)
    if (id) selectedMmNodeId.value = 'case_' + id
  }
  mmCtx.value.show = false
}

function mmCtxAddSibling() {
  const n = mmCtx.value.node
  if (n?.type === 'case') {
    const id = addCaseToFile(n.data?.casePath || '')
    if (id) selectedMmNodeId.value = 'case_' + id
  } else if (n?.type === 'module') {
    const id = addCaseToFile(n.data?.path || '')
    if (id) selectedMmNodeId.value = 'case_' + id
  }
  mmCtx.value.show = false
}

function mmCtxRename() {
  if (mmCtx.value.node) startEditing(mmCtx.value.node)
  mmCtx.value.show = false
}

function mmCtxDelete() {
  const n = mmCtx.value.node
  if (n?.type === 'case') {
    const id = n.data?.caseId
    if (id) store.deleteCase(id)
    selectedMmNodeId.value = null
  }
  mmCtx.value.show = false
}

function mmNavUp() {
  const idx = getSelectedMmIdx()
  if (idx > 0) selectedMmNodeId.value = mmAllNodes.value[idx - 1].id
}

function mmNavDown() {
  const idx = getSelectedMmIdx()
  if (idx >= 0 && idx < mmAllNodes.value.length - 1) selectedMmNodeId.value = mmAllNodes.value[idx + 1].id
}

function onMindMapKeydown(e: KeyboardEvent) {
  if (editingNodeId.value) return

  const node = getSelectedMmNode()
  if (!node) return

  switch (e.key) {
    case 'Enter':
      e.preventDefault()
      if (node.type === 'root') {
        createCaseAndEdit('New Module')
      } else if (node.type === 'module') {
        const path = node.data?.path || ''
        const parts = path.split('/')
        const parentPath = parts.slice(0, -1).join('/')
        const siblingPath = parentPath ? parentPath + '/New Module' : 'New Module'
        createCaseAndEdit(siblingPath)
      } else if (node.type === 'case') {
        const f = activeFile.value
        const c = f?.cases.find(oc => oc.id === node.data?.caseId)
        createCaseAndEdit(c?.module || '')
      }
      break
    case 'Tab':
      e.preventDefault()
      if (node.type === 'root') {
        createCaseAndEdit('New Module')
      } else if (node.type === 'module') {
        showTabPrompt(node)
      } else if (node.type === 'case') {
        const f = activeFile.value
        const c = f?.cases.find(oc => oc.id === node.data?.caseId)
        if (c) {
          const order = ['precondition', 'steps', 'expected', 'priority', 'remarks'] as const
          for (const field of order) {
            if (!c[field]?.trim()) {
              selectedMmNodeId.value = field + '_' + c.id
              editingNodeId.value = field + '_' + c.id
              editingValue.value = c[field] || ''
              nextTick(() => {
                const el = document.querySelector('[data-mm-editor]') as HTMLTextAreaElement
                if (el) { el.focus(); el.select(); autoResizeTextarea({ target: el } as any) }
              })
              return
            }
          }
          selectedMmNodeId.value = 'precondition_' + c.id
        }
      } else if (node.type === 'field') {
        const caseId = node.data?.caseId
        if (caseId && node.field) {
          const order = ['precondition', 'steps', 'expected', 'priority', 'remarks']
          const idx = order.indexOf(node.field)
          if (idx >= 0 && idx < order.length - 1) {
            const nextField = order[idx + 1]
            const nextId = nextField + '_' + caseId
            selectedMmNodeId.value = nextId
            editingNodeId.value = nextId
            const f = activeFile.value
            const c = f?.cases.find(oc => oc.id === caseId)
            editingValue.value = c ? ((c as any)[nextField] || '') : ''
            nextTick(() => {
              const el = document.querySelector('[data-mm-editor]') as HTMLTextAreaElement
              if (el) { el.focus(); el.select(); autoResizeTextarea({ target: el } as any) }
            })
          }
        }
      }
      break
    case 'Delete':
    case 'Backspace':
      if (node.type === 'case') {
        const id = node.data?.caseId
        if (id) { store.deleteCase(id); selectedMmNodeId.value = null }
      }
      break
    case 'F2':
      e.preventDefault()
      startEditing(node)
      break
    case 'ArrowUp': e.preventDefault(); mmNavUp(); break
    case 'ArrowDown': e.preventDefault(); mmNavDown(); break
    case 'ArrowRight':
      e.preventDefault()
      if (node.type === 'module' && node.collapsed) toggleCollapse(node)
      break
    case 'ArrowLeft':
      e.preventDefault()
      if (node.type === 'module' && !node.collapsed) toggleCollapse(node)
      break
  }
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
function mmFit() { mmZoom.value = 0.65; mmPan.value = { x: 40, y: 60 } }

function caseBorderClass(p: string): string {
  const map: Record<string, string> = {
    P0: 'border-red-400/60',
    P1: 'border-orange-400/60',
    P2: 'border-blue-400/60',
    P3: 'border-gray-400/40',
  }
  return map[p] || 'border-gray-400/40'
}

function caseDotClass(p: string): string {
  const map: Record<string, string> = {
    P0: 'bg-red-400',
    P1: 'bg-orange-400',
    P2: 'bg-blue-400',
    P3: 'bg-gray-400',
  }
  return map[p] || 'bg-gray-300'
}

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
    return
  }
  if (viewMode.value === 'mindmap') {
    e.stopPropagation()
    onMindMapKeydown(e)
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
    if (measuredHeights.size > 500) measuredHeights.clear()
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
    if (measuredHeights.size > 500) measuredHeights.clear()
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
  _resizeObserver?.disconnect()
  _resizeObserver = null
  document.removeEventListener('mousemove', onResizeMove)
  document.removeEventListener('mouseup', onResizeEnd)
  if (_menuCloseHandler) { document.removeEventListener('mousedown', _menuCloseHandler); _menuCloseHandler = null }
  if (_mmTabPromptHandler) { document.removeEventListener('mousedown', _mmTabPromptHandler); _mmTabPromptHandler = null }
  if (_mmDragMoveHandler) { document.removeEventListener('mousemove', _mmDragMoveHandler); _mmDragMoveHandler = null }
  if (_mmDragEndHandler) { document.removeEventListener('mouseup', _mmDragEndHandler); _mmDragEndHandler = null }
  if (_mmCtxHandler) { document.removeEventListener('mousedown', _mmCtxHandler); _mmCtxHandler = null }
  for (const [, handler] of _docListeners) {
    document.removeEventListener('mousedown', handler)
    document.removeEventListener('mousemove', handler)
    document.removeEventListener('mouseup', handler)
  }
  _docListeners.clear()
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
