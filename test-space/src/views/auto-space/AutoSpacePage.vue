<template>
  <div class="flex flex-col flex-1 min-h-0 -mx-margin-page pb-2 box-border select-none">
    <!-- Top Toolbar -->
    <div class="flex items-center gap-3 mb-2 flex-shrink-0 ml-3">
      <div class="flex items-center gap-1.5 text-[12px] text-on-surface-variant/60 bg-white/10 rounded-full px-3 py-1.5">
        <span class="material-symbols-outlined text-[16px] text-on-surface-variant/40">developer_board</span>
        <span>{{ connectedDevice ? connectedDevice : t('auto.noDevice') }}</span>
      </div>

      <div class="flex items-center gap-1">
        <button class="glass-button px-3 py-1.5 rounded-full font-caption text-caption font-normal flex items-center gap-1.5 select-none" :class="selectedCaseIds.length === 0 ? 'opacity-40' : ''" :disabled="selectedCaseIds.length === 0 || running" @click="runSelected">
          <span class="material-symbols-outlined text-[16px]">play_arrow</span>
          <span class="text-[12px]">{{ t('auto.runSelected') }}</span>
        </button>
        <button class="glass-button px-3 py-1.5 rounded-full font-caption text-caption font-normal flex items-center gap-1.5 select-none" :class="caseList.length === 0 ? 'opacity-40' : ''" :disabled="caseList.length === 0 || running" @click="runAll">
          <span class="material-symbols-outlined text-[16px]">play_circle</span>
          <span class="text-[12px]">{{ t('auto.runAll') }}</span>
        </button>
        <button v-if="running" class="glass-button px-3 py-1.5 rounded-full font-caption text-caption font-normal flex items-center gap-1.5 select-none text-red-400" @click="stopRun">
          <span class="material-symbols-outlined text-[16px]">stop</span>
          <span class="text-[12px]">{{ t('auto.stop') }}</span>
        </button>
      </div>

      <div class="flex-1"></div>

      <button class="glass-button px-3 py-1.5 rounded-full font-caption text-caption font-normal flex items-center gap-1.5 select-none" @click="showNewDialog = true">
        <span class="material-symbols-outlined text-[16px]">add</span>
        <span class="text-[12px]">{{ t('auto.newCase') }}</span>
      </button>
      <button class="glass-button px-3 py-1.5 rounded-full font-caption text-caption font-normal flex items-center gap-1.5 select-none" @click="importYaml">
        <span class="material-symbols-outlined text-[16px]">file_download</span>
        <span class="text-[12px]">{{ t('auto.importYaml') }}</span>
      </button>
      <button class="glass-button px-3 py-1.5 rounded-full font-caption text-caption font-normal flex items-center gap-1.5 select-none" @click="activeTab = 'report' as const">
        <span class="material-symbols-outlined text-[16px]">history</span>
        <span class="text-[12px]">{{ t('auto.reportHistory') }}</span>
      </button>
    </div>

    <div class="flex-1 flex gap-4 min-h-0">
      <!-- Left Panel: Case List -->
      <div class="w-56 flex-shrink-0 ml-3 rounded-xl bg-white/10 backdrop-blur-[60px] border border-white/50 shadow-lg flex flex-col overflow-hidden">
        <div class="px-3 py-2 border-b border-white/10 space-y-1.5">
          <div class="relative">
            <input v-model="searchQuery" class="w-full bg-white/5 border border-white/10 rounded-lg px-2.5 py-1 text-[12px] text-on-surface placeholder-on-surface-variant/40 focus:outline-none focus:border-white/20 select-text" :placeholder="t('auto.searchCases')" />
            <span v-if="searchQuery" class="absolute right-1.5 top-1/2 -translate-y-1/2 text-on-surface-variant/40 cursor-pointer" @click="searchQuery = ''">
              <span class="material-symbols-outlined text-[14px]">close</span>
            </span>
          </div>
          <select v-model="moduleFilter" class="w-full bg-white/5 border border-white/10 rounded-lg px-2.5 py-1 text-[11px] text-on-surface-variant/70 focus:outline-none focus:border-white/20 select-text">
            <option value="">{{ t('auto.allModules') }}</option>
            <option v-for="m in moduleList" :key="m" :value="m">{{ m }}</option>
          </select>
        </div>
        <div class="flex-1 overflow-y-auto custom-scrollbar">
          <div v-if="pagedCases.length === 0" class="p-4 text-[12px] text-on-surface-variant/40 text-center">
            {{ t('auto.noCases') }}
          </div>
          <template v-for="group in groupedCases" :key="group.tag">
            <div class="flex items-center gap-1 px-3 py-1.5 text-[11px] text-on-surface-variant/40 font-medium cursor-pointer select-none hover:text-on-surface-variant/60" @click="group.expanded = !group.expanded">
              <span class="material-symbols-outlined text-[14px] transition-transform" :class="group.expanded ? '' : '-rotate-90'">expand_more</span>
              <span class="material-symbols-outlined text-[13px] text-amber-400">folder</span>
              <span>{{ group.tag }}</span>
              <span class="ml-auto text-[10px]">{{ group.cases.length }}</span>
            </div>
            <div v-if="group.expanded">
              <div v-for="c in group.cases" :key="c.id"
                class="flex items-center gap-2 px-3 py-1.5 cursor-pointer transition-colors text-[12px] border-b border-white/[2%] group relative"
                :class="[
                  currentCase?.id === c.id ? 'bg-white/15 text-on-surface font-medium' : 'text-on-surface-variant hover:bg-white/5 hover:text-on-surface',
                ]"
                @click="selectCase(c)"
                @contextmenu.prevent="showContextMenu($event, c)">
                <input type="checkbox" :checked="selectedCaseIds.includes(c.id)" class="w-3 h-3 accent-purple-500 flex-shrink-0" @click.stop @change="toggleCaseSelect(c.id)" />
                <span class="material-symbols-outlined text-[14px] text-on-surface-variant/50 flex-shrink-0" :class="{'text-green-400': c.priority === 'P0', 'text-orange-400': c.priority === 'P1'}">description</span>
                <span class="truncate flex-1">{{ c.name }}</span>
                <span class="text-[10px] px-1 rounded font-mono" :class="pClass(c.priority)">{{ c.priority }}</span>
                <button class="p-0.5 rounded hover:bg-red-500/20 text-on-surface-variant/20 hover:text-red-400 transition-colors flex-shrink-0 select-none opacity-0 group-hover:opacity-100" @click.stop="confirmDelete(c)">
                  <span class="material-symbols-outlined text-[12px]">close</span>
                </button>
              </div>
            </div>
          </template>
        </div>
        <div v-if="totalPages > 1" class="px-3 py-1.5 border-t border-white/10 flex items-center justify-between text-[11px] text-on-surface-variant/50">
          <button class="glass-button px-1.5 py-0.5 rounded select-none" :class="currentPage <= 1 ? 'opacity-30' : ''" :disabled="currentPage <= 1" @click="currentPage--">
            <span class="material-symbols-outlined text-[14px]">chevron_left</span>
          </button>
          <span>{{ currentPage }} / {{ totalPages }}</span>
          <button class="glass-button px-1.5 py-0.5 rounded select-none" :class="currentPage >= totalPages ? 'opacity-30' : ''" :disabled="currentPage >= totalPages" @click="currentPage++">
            <span class="material-symbols-outlined text-[14px]">chevron_right</span>
          </button>
        </div>
        <div class="px-3 py-1.5 border-t border-white/10 flex items-center gap-1">
          <button class="glass-button px-2 py-1 rounded text-[11px] flex items-center gap-1 select-none flex-1 justify-center" @click="showNewDialog = true">
            <span class="material-symbols-outlined text-[13px]">add</span>
            <span>{{ t('auto.newCase') }}</span>
          </button>
        </div>
      </div>

      <!-- Right Workspace -->
      <div class="flex-1 flex flex-col min-h-0 pr-3">
        <!-- Tab switcher -->
        <div class="flex items-center gap-1 mb-2 flex-shrink-0">
          <button v-for="tab in workspaceTabs" :key="tab.key"
            class="glass-hover rounded-lg px-3 py-1.5 text-[12px] flex items-center gap-1.5 transition-colors"
            :class="activeTab === tab.key ? 'glass-active font-semibold' : 'text-on-surface-variant'"
            @click="activeTab = tab.key">
            <span class="material-symbols-outlined text-[15px]" :style="{ fontVariationSettings: `'FILL' ${activeTab === tab.key ? 1 : 0}` }">{{ tab.icon }}</span>
            <span>{{ t(tab.labelKey) }}</span>
          </button>
        </div>

        <!-- Tab: Editor -->
        <div v-show="activeTab === 'editor'" class="flex-1 flex flex-col min-h-0">
          <div v-if="currentCase" class="flex-1 flex flex-col min-h-0">
            <div class="flex items-center gap-3 px-4 py-2 flex-shrink-0 flex-wrap">
              <input v-model="editingName" class="bg-transparent border-b border-transparent focus:border-secondary/40 focus:outline-none text-[20px] font-bold text-on-surface px-1 -ml-1 min-w-0 max-w-[50%] truncate select-text" :placeholder="t('auto.caseNamePlaceholder')" />
              <span class="text-[11px] flex items-center gap-1 flex-shrink-0 select-none" :class="saved ? 'text-green-400/70' : 'text-on-surface-variant/40'">
                <span class="w-1.5 h-1.5 rounded-full flex-shrink-0" :class="saved ? 'bg-green-400/70' : 'bg-on-surface-variant/40 animate-pulse'" />
                {{ saved ? t('auto.saved') : t('auto.saving') }}
              </span>
              <div class="flex-1"></div>
              <span class="text-[11px] font-mono px-2 py-0.5 rounded" :class="pClass(currentCase.priority)">{{ currentCase.priority }}</span>
              <div class="flex items-center gap-1 flex-wrap">
                <span v-for="tag in editingTags" :key="tag" class="text-[10px] px-2 py-0.5 rounded-full bg-white/10 text-on-surface-variant/70">{{ tag }}</span>
              </div>
            </div>
            <div class="flex items-center gap-2 px-4 pb-1 flex-shrink-0">
              <span class="material-symbols-outlined text-[14px] text-amber-400">folder</span>
              <input v-model="editingModule" class="bg-transparent border-b border-transparent focus:border-secondary/40 focus:outline-none text-[12px] text-on-surface-variant/70 px-1 -ml-1 min-w-0 w-48 select-text" :placeholder="t('auto.modulePlaceholder')" />
              <div class="flex-1"></div>
              <button class="glass-button px-2 py-0.5 rounded text-[10px] flex items-center gap-1 select-none" @click="showVersionHistory = true">
                <span class="material-symbols-outlined text-[12px]">history</span>
                {{ t('auto.viewVersions') }}
              </button>
            </div>
            <!-- Monaco Editor -->
            <div class="flex-1 min-h-0 rounded-2xl overflow-hidden border border-white/10 flex flex-col">
              <div class="flex items-center gap-3 px-4 py-2 bg-[#1a1c1d] border-b border-white/5 flex-shrink-0">
                <div class="flex gap-1.5">
                  <span class="w-3 h-3 rounded-full bg-[#ff5f56]"></span>
                  <span class="w-3 h-3 rounded-full bg-[#ffbd2e]"></span>
                  <span class="w-3 h-3 rounded-full bg-[#27c93f]"></span>
                </div>
                <div class="flex-1"></div>
                <div class="flex items-center gap-1">
                  <button class="flex items-center gap-1 px-3 py-1 rounded-full text-[11px] bg-white/5 hover:bg-white/15 text-on-surface-variant/70 hover:text-on-surface transition-colors select-none" @click="saveCurrentCase">
                    <span class="material-symbols-outlined text-[13px]">save</span>
                    {{ t('auto.save') }}
                  </button>
                  <button class="flex items-center gap-1 px-3 py-1 rounded-full text-[11px] bg-white/5 hover:bg-white/15 text-on-surface-variant/70 hover:text-on-surface transition-colors select-none" @click="exportYaml">
                    <span class="material-symbols-outlined text-[13px]">file_upload</span>
                    {{ t('auto.exportYaml') }}
                  </button>
                  <button class="flex items-center gap-1 px-3 py-1 rounded-full text-[11px] bg-white/5 hover:bg-white/15 text-on-surface-variant/70 hover:text-on-surface transition-colors select-none" @click="validateYaml">
                    <span class="material-symbols-outlined text-[13px]">check_circle</span>
                    {{ t('auto.validateYaml') }}
                  </button>
                  <button class="flex items-center gap-1 px-3 py-1 rounded-full text-[11px] bg-green-500/20 hover:bg-green-500/30 text-green-400 transition-colors select-none" @click="runSingle">
                    <span class="material-symbols-outlined text-[13px]">play_arrow</span>
                    {{ t('auto.run') }}
                  </button>
                </div>
              </div>
              <div class="flex-1 flex" style="background: #0d0d1a;">
                <MonacoEditor v-model="editingContent" language="yaml" />
              </div>
            </div>
          </div>
          <div v-else class="flex-1 min-h-0 flex items-center justify-center rounded-2xl border border-white/10" style="background: #0d0d1a;">
            <div class="text-center text-[#4a5568]">
              <span class="material-symbols-outlined text-5xl mb-3 block">smart_toy</span>
              <p class="text-[14px]">{{ t('scripts.placeholder') }}</p>
            </div>
          </div>
        </div>

        <!-- Tab: Console -->
        <div v-show="activeTab === 'console'" class="flex-1 flex min-h-0 gap-2 rounded-2xl overflow-hidden border border-white/10">
          <div class="flex-1 flex flex-col min-h-0">
            <div class="flex items-center justify-between px-4 py-2 bg-[#1a1c1d] border-b border-white/5 flex-shrink-0">
              <div class="flex items-center gap-3">
                <span class="material-symbols-outlined text-[14px] text-[#6b7280]">terminal</span>
                <span class="text-[12px] font-medium text-[#9ca3af]">{{ t('auto.console') }}</span>
                <span v-if="running" class="flex items-center gap-1.5 text-[11px] text-green-400">
                  <span class="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse"></span>
                  {{ t('auto.executing') }}
                </span>
              </div>
              <div class="flex items-center gap-2">
                <button class="glass-button px-2.5 py-1 rounded-full text-[11px] flex items-center gap-1 select-none" @click="consoleOutput = []">
                  <span class="material-symbols-outlined text-[13px]">delete</span>
                  {{ t('scripts.clear') }}
                </button>
              </div>
            </div>
            <div ref="outputContainer" class="flex-1 overflow-y-auto font-mono text-[13px] leading-relaxed px-4 py-3 custom-scrollbar" style="background: #0d0d1a;">
              <div v-if="consoleOutput.length === 0" class="text-[#6b7280]">
                <span class="text-green-400/60">$</span> {{ t('scripts.outputHint') }}
              </div>
              <div v-for="(line, idx) in consoleOutput" :key="idx" class="whitespace-pre-wrap">
                <span :class="line.type === 'step_start' ? 'text-blue-400' : line.type === 'step_done' ? 'text-green-400' : line.type === 'step_heal' ? 'text-orange-400' : line.type === 'step_fail' ? 'text-red-400' : line.type === 'info' ? 'text-on-surface-variant/60' : 'text-[#e4e5e7]'">
                  <span v-if="line.type === 'step_start'" class="mr-1">▶</span>
                  <span v-else-if="line.type === 'step_done'" class="mr-1">✅</span>
                  <span v-else-if="line.type === 'step_heal'" class="mr-1">🔧</span>
                  <span v-else-if="line.type === 'step_fail'" class="mr-1">❌</span>
                  <span v-else-if="line.type === 'info'" class="mr-1">ℹ</span>
                  {{ line.text }}
                </span>
              </div>
            </div>
            <div v-if="!running && lastRunId" class="flex items-center gap-2 px-4 py-2 bg-[#1a1c1d] border-t border-white/5 flex-shrink-0">
              <button class="glass-button px-3 py-1 rounded-lg text-[11px] flex items-center gap-1 select-none" @click="viewLastReport">
                <span class="material-symbols-outlined text-[13px]">visibility</span>
                {{ t('auto.viewReport') }}
              </button>
            </div>
          </div>
          <!-- Screenshot preview panel -->
          <div v-if="latestScreenshot" class="w-48 flex-shrink-0 border-l border-white/10 flex flex-col" style="background: #0d0d1a;">
            <div class="text-[11px] text-[#6b7280] px-3 py-2 border-b border-white/5">{{ t('auto.latestScreenshot') }}</div>
            <div class="flex-1 flex items-center justify-center p-2">
              <img :src="latestScreenshot" class="max-w-full max-h-full object-contain rounded-lg cursor-pointer" @click="screenshotZoom = latestScreenshot" />
            </div>
          </div>
        </div>

        <!-- Tab: Report -->
        <div v-show="activeTab === 'report'" class="flex-1 flex flex-col min-h-0">
          <ReportViewer v-if="reportRunId" :runId="reportRunId" @back="reportRunId = null" />
          <div v-else class="flex-1 flex flex-col min-h-0">
            <div v-if="runRecords.length === 0" class="flex-1 flex items-center justify-center rounded-2xl border border-white/10">
              <div class="text-center text-on-surface-variant/40">
                <span class="material-symbols-outlined text-5xl mb-3 block">history</span>
                <p class="text-[14px]">{{ t('auto.noReports') }}</p>
              </div>
            </div>
            <div v-else class="flex-1 overflow-y-auto custom-scrollbar">
              <div v-for="r in runRecords" :key="r.id" class="glass-panel rounded-2xl p-4 mb-2 bg-white/40">
                <div class="flex flex-col gap-2">
                  <div class="flex items-center justify-between">
                    <div class="flex items-center gap-3">
                      <span class="material-symbols-outlined text-[20px]" :class="r.status === 'done' ? 'text-green-400' : r.status === 'aborted' ? 'text-red-400' : 'text-blue-400'">{{ r.status === 'done' ? 'check_circle' : r.status === 'aborted' ? 'cancel' : 'hourglass_top' }}</span>
                      <div>
                        <div class="text-[13px] font-medium">{{ r.startedAt ? new Date(r.startedAt).toLocaleString() : '-' }}</div>
                        <div class="text-[11px] text-on-surface-variant/60">
                          {{ r.total }} {{ t('auto.cases') }} | ✅{{ r.passed }} ❌{{ r.failed }} 🔧{{ r.healed }} ⏭{{ r.skipped }} | {{ r.status }}
                        </div>
                      </div>
                    </div>
                    <div class="flex items-center gap-2">
                      <button class="glass-button px-3 py-1 rounded-lg text-[11px] flex items-center gap-1 select-none" @click="reportRunId = r.id">
                        <span class="material-symbols-outlined text-[13px]">visibility</span>
                        {{ t('auto.viewReport') }}
                      </button>
                      <button class="glass-button px-2 py-1 rounded-lg text-[11px] flex items-center gap-1 select-none" @click="deleteRunRecord(r)">
                        <span class="material-symbols-outlined text-[13px]">delete</span>
                      </button>
                    </div>
                  </div>
                  <div v-if="r.status === 'running'" class="w-full h-1 rounded-full bg-white/10 overflow-hidden">
                    <div class="h-full rounded-full bg-green-400 transition-all" :style="{ width: r.total > 0 ? ((r.passed + r.failed) / r.total * 100) + '%' : '0%' }"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- New Case Dialog -->
    <Teleport to="body">
      <div v-if="showNewDialog" class="fixed inset-0 z-50 flex items-center justify-center" @click.self="showNewDialog = false">
        <div class="absolute inset-0 bg-black/30 backdrop-blur-sm"></div>
        <div class="glass-panel rounded-[2rem] p-6 w-full max-w-md relative z-10 bg-white/60">
          <div class="flex justify-between items-center mb-4">
            <h3 class="font-label-md text-label-md text-on-surface font-semibold flex items-center gap-1.5 select-none">
              <span class="material-symbols-outlined text-[16px]">smart_toy</span>{{ t('auto.newCaseDialogTitle') }}
            </h3>
            <button class="glass-button p-1 rounded select-none" @click="showNewDialog = false">
              <span class="material-symbols-outlined text-[18px]">close</span>
            </button>
          </div>
          <div class="space-y-3">
            <div>
              <label class="text-[12px] text-on-surface-variant/70 block mb-1">{{ t('auto.newCaseName') }}</label>
              <input v-model="newCaseName" class="glass-input w-full rounded-xl px-3 py-2 text-[13px] select-text" :placeholder="t('auto.newCaseNamePlaceholder')" @keydown.enter="createNewCase" />
            </div>
            <div>
              <label class="text-[12px] text-on-surface-variant/70 block mb-1">{{ t('auto.module') }}</label>
              <input v-model="newCaseModule" class="glass-input w-full rounded-xl px-3 py-2 text-[13px] select-text" placeholder="e.g. HomePage, Playback, Settings" list="module-suggestions" />
              <datalist id="module-suggestions">
                <option v-for="m in moduleList" :key="m" :value="m" />
              </datalist>
            </div>
            <div>
              <label class="text-[12px] text-on-surface-variant/70 block mb-1">{{ t('auto.newCaseTags') }}</label>
              <input v-model="newCaseTags" class="glass-input w-full rounded-xl px-3 py-2 text-[13px] select-text" placeholder="smoke, home, playback" />
            </div>
            <div>
              <label class="text-[12px] text-on-surface-variant/70 block mb-1">{{ t('auto.newCasePriority') }}</label>
              <select v-model="newCasePriority" class="glass-input w-full rounded-xl px-3 py-2 text-[13px] bg-white/40 select-text">
                <option value="P0">P0</option>
                <option value="P1">P1</option>
                <option value="P2">P2</option>
                <option value="P3">P3</option>
              </select>
            </div>
          </div>
          <div class="flex gap-2 justify-end pt-4 border-t border-outline-variant/30 mt-4">
            <button class="glass-button px-4 py-2 rounded-lg font-label-md text-label-md select-none" @click="showNewDialog = false">{{ t('auto.newCaseCancel') }}</button>
            <button class="glass-button px-4 py-2 rounded-lg font-label-md text-label-md select-none" @click="createNewCase">{{ t('auto.newCaseCreate') }}</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Import Conflict Dialog -->
    <Teleport to="body">
      <div v-if="importConflict" class="fixed inset-0 z-50 flex items-center justify-center" @click.self="importConflict = null">
        <div class="absolute inset-0 bg-black/30 backdrop-blur-sm"></div>
        <div class="glass-panel rounded-[2rem] p-6 w-full max-w-md relative z-10 bg-white/60">
          <h3 class="font-label-md text-label-md text-on-surface font-semibold mb-3">{{ t('auto.importConflict') }}</h3>
          <div class="text-[13px] text-on-surface-variant/80 mb-2">{{ t('auto.importConflictDesc', { name: importConflict.name }) }}</div>
          <div class="text-[11px] text-on-surface-variant/60 mb-4">{{ t('auto.importConflictResolve') }}</div>
          <div class="flex gap-2 justify-end">
            <button class="glass-button px-4 py-2 rounded-lg text-[12px] select-none" @click="importConflict = null">{{ t('auto.importSkip') }}</button>
            <button class="glass-button px-4 py-2 rounded-lg text-[12px] select-none" @click="importOverwrite">{{ t('auto.importOverwrite') }}</button>
            <button class="glass-button px-4 py-2 rounded-lg text-[12px] select-none" @click="importNewCopy">{{ t('auto.importNewCopy') }}</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Context Menu -->
    <Teleport to="body">
      <div v-if="contextMenu" class="fixed z-[9999]" :style="{ left: contextMenu.x + 'px', top: contextMenu.y + 'px' }" @click.self="contextMenu = null">
        <div class="glass-panel rounded-xl p-1 shadow-2xl border border-white/20 bg-white/80 min-w-[140px]" @mouseleave="contextMenu = null">
          <button class="w-full text-left px-3 py-1.5 text-[12px] hover:bg-white/30 rounded-lg flex items-center gap-2 select-none" @click="contextMenuAction('edit')">
            <span class="material-symbols-outlined text-[14px]">edit</span> {{ t('auto.edit') }}
          </button>
          <button class="w-full text-left px-3 py-1.5 text-[12px] hover:bg-white/30 rounded-lg flex items-center gap-2 select-none" @click="contextMenuAction('duplicate')">
            <span class="material-symbols-outlined text-[14px]">content_copy</span> {{ t('auto.duplicate') }}
          </button>
          <button class="w-full text-left px-3 py-1.5 text-[12px] hover:bg-white/30 rounded-lg flex items-center gap-2 select-none" @click="contextMenuAction('export')">
            <span class="material-symbols-outlined text-[14px]">file_upload</span> {{ t('auto.exportYaml') }}
          </button>
          <div class="border-t border-white/10 my-1"></div>
          <button class="w-full text-left px-3 py-1.5 text-[12px] hover:bg-red-500/20 text-red-400 rounded-lg flex items-center gap-2 select-none" @click="contextMenuAction('delete')">
            <span class="material-symbols-outlined text-[14px]">delete</span> {{ t('auto.deleteConfirm') }}
          </button>
        </div>
      </div>
    </Teleport>

    <!-- Version History Dialog -->
    <VersionHistoryDialog v-if="showVersionHistory && currentCase"
      :caseId="currentCase.id"
      :currentContent="editingContent"
      @close="showVersionHistory = false"
      @restore="restoreVersion" />

    <!-- Screenshot Zoom -->
    <Teleport to="body">
      <div v-if="screenshotZoom" class="fixed inset-0 z-50 flex items-center justify-center" @click.self="screenshotZoom = null">
        <div class="absolute inset-0 bg-black/60 backdrop-blur-sm"></div>
        <img :src="screenshotZoom" class="max-w-[90vw] max-h-[90vh] object-contain relative z-10 rounded-2xl shadow-2xl" @click="screenshotZoom = null" />
      </div>
    </Teleport>

    <!-- Delete confirmation -->
    <Teleport to="body">
      <div v-if="deleteTarget" class="fixed inset-0 z-50 flex items-center justify-center" @click.self="deleteTarget = null">
        <div class="absolute inset-0 bg-black/30 backdrop-blur-sm"></div>
        <div class="glass-panel rounded-[2rem] p-6 w-full max-w-md relative z-10 bg-white/60">
          <div class="flex justify-between items-center mb-4">
            <h3 class="font-label-md text-label-md text-on-surface font-semibold flex items-center gap-1.5 select-none">
              <span class="material-symbols-outlined text-[16px] text-red-400">warning</span>{{ t('auto.deleteTitle') }}
            </h3>
            <button class="glass-button p-1 rounded select-none" @click="deleteTarget = null">
              <span class="material-symbols-outlined text-[18px]">close</span>
            </button>
          </div>
          <div class="text-[13px] text-on-surface-variant/80 mb-4">{{ t('auto.deleteDesc', { name: deleteTarget.name }) }}</div>
          <div class="flex gap-2 justify-end border-t border-outline-variant/30 pt-4">
            <button class="glass-button px-4 py-2 rounded-lg font-label-md text-label-md select-none" @click="deleteTarget = null">{{ t('auto.deleteCancel') }}</button>
            <button class="glass-button px-4 py-2 rounded-lg font-label-md text-label-md select-none text-red-400" @click="doDelete">{{ t('auto.deleteConfirm') }}</button>
          </div>
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
defineOptions({ name: 'AutoSpacePage' })
import { ref, computed, nextTick, onMounted, onUnmounted, watch } from "vue"
import * as db from "@/services/database"
import type { AutoCase, AutoRunRecord } from "@/types"
import { useI18n } from "@/composables/useI18n"
import { runAutoCase, runAutoSuite, stopAutoRun, listenAutoEvents } from "@/services/autoRunService"
import type { AutoStepEvent } from "@/services/autoRunService"
import MonacoEditor from "@/components/MonacoEditor.vue"
import VersionHistoryDialog from "./VersionHistoryDialog.vue"
import ReportViewer from "./ReportViewer.vue"

const { t } = useI18n()

// ── State ─────────────────────────────────────────────────────
const caseList = ref<AutoCase[]>([])
const currentCase = ref<AutoCase | null>(null)
const editingName = ref("")
const editingModule = ref("")
const editingTags = ref<string[]>([])
const editingContent = ref("")
const saved = ref(true)
const searchQuery = ref("")
const moduleFilter = ref("")
const currentPage = ref(1)
const PAGE_SIZE = 50

const activeTab = ref<'editor' | 'console' | 'report'>('editor')
const running = ref(false)
const currentRunId = ref<string | null>(null)
const lastRunId = ref<string | null>(null)
const selectedCaseIds = ref<string[]>([])

const outputContainer = ref<HTMLElement | null>(null)
const consoleOutput = ref<{ text: string; type: string }[]>([])
const latestScreenshot = ref<string | null>(null)
const runRecords = ref<AutoRunRecord[]>([])
const reportRunId = ref<string | null>(null)
const screenshotZoom = ref<string | null>(null)

const showVersionHistory = ref(false)

const workspaceTabs = [
  { key: 'editor' as const, icon: 'edit', labelKey: 'auto.editor' },
  { key: 'console' as const, icon: 'terminal', labelKey: 'auto.console' },
  { key: 'report' as const, icon: 'history', labelKey: 'auto.report' },
]

let autoSaveTimer: ReturnType<typeof setTimeout> | null = null
let eventUnlisten: (() => void) | null = null

const connectedDevice = ref(localStorage.getItem('last_device_serial') || '')

// ── New Case Dialog ────────────────────────────────────────────
const showNewDialog = ref(false)
const newCaseName = ref("")
const newCaseModule = ref("")
const newCaseTags = ref("")
const newCasePriority = ref("P2")

// ── Import Conflict ──────────────────────────────────────────
const importConflict = ref<{ name: string; id: string; file_key: string; content: string } | null>(null)
const pendingImports = ref<{ name: string; file_key: string; content: string }[]>([])

// ── Context Menu ─────────────────────────────────────────────
const contextMenu = ref<{ x: number; y: number; case: AutoCase } | null>(null)

// ── Delete ────────────────────────────────────────────────────
const deleteTarget = ref<AutoCase | null>(null)

// ── Delete run record ────────────────────────────────────────
async function deleteRunRecord(r: AutoRunRecord) {
  if (!confirm('Delete this run record?')) return
  await db.deleteAutoRunRecord?.(r.id)
  await loadRunRecords()
}

// ── Toast ─────────────────────────────────────────────────────
const toast = ref<{ msg: string; ok: boolean } | null>(null)
let toastTimer: ReturnType<typeof setTimeout> | null = null

function showToast(msg: string, ok: boolean) {
  if (toastTimer) clearTimeout(toastTimer)
  toast.value = { msg, ok }
  toastTimer = setTimeout(() => { toast.value = null }, 2000)
}

function pClass(p: string) {
  if (p === 'P0') return 'bg-green-500/20 text-green-400'
  if (p === 'P1') return 'bg-orange-500/20 text-orange-400'
  if (p === 'P2') return 'bg-blue-500/20 text-blue-400'
  return 'bg-gray-500/20 text-gray-400'
}

// ── Module list ───────────────────────────────────────────────
const moduleList = computed(() => {
  const modules = new Set<string>()
  for (const c of caseList.value) { if (c.module) modules.add(c.module) }
  return Array.from(modules).sort()
})

// ── Case filtering & grouping ─────────────────────────────────
const filteredCases = computed(() => {
  let list = caseList.value
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.trim().toLowerCase()
    list = list.filter(c => c.name.toLowerCase().includes(q) || c.tags.some(t => t.toLowerCase().includes(q)))
  }
  if (moduleFilter.value) list = list.filter(c => c.module === moduleFilter.value)
  return list
})

const pagedCases = computed(() => filteredCases.value.slice(0, currentPage.value * PAGE_SIZE))
const totalPages = computed(() => Math.ceil(filteredCases.value.length / PAGE_SIZE))

const groupedCases = computed(() => {
  const groups: { tag: string; cases: AutoCase[]; expanded: boolean }[] = []
  const moduleMap = new Map<string, AutoCase[]>()
  for (const c of pagedCases.value) {
    const mod = c.module || 'Other'
    if (!moduleMap.has(mod)) moduleMap.set(mod, [])
    moduleMap.get(mod)!.push(c)
  }
  for (const [mod, cases] of moduleMap) {
    groups.push({ tag: mod, cases, expanded: true })
  }
  groups.sort((a, b) => a.tag.localeCompare(b.tag))
  return groups
})

// ── CRUD ──────────────────────────────────────────────────────
function genId(): string { return crypto.randomUUID().replace(/-/g, '').slice(0, 12) }
function fileKeyFromName(name: string): string {
  return `TC-${name.replace(/[<>:"/\\|?*\s]/g, '_').toLowerCase()}`
}

function yamlSkeleton(name: string, moduleName: string, tags: string[], priority: string): string {
  const tagStr = tags.map(t => `    - "${t}"`).join('\n')
  return `# Test Space Automation Case v1.0
meta:
  id: "${fileKeyFromName(name)}"
  name: "${name}"
  module: "${moduleName}"
  author: ""
  version: "1.0"
  tags:
${tagStr}
  priority: "${priority}"
  description: ""

setup:
  - action: launch_app
    package: ""
    wait_activity: ""
    timeout: 8000

steps:
  - id: "step_01"
    desc: "step description"
    action: navigate_to
    target:
      primary:
        by: resource_id
        value: ""
    on_failure: "ai_heal"

teardown:
  - action: press_key
    key: HOME
`
}

async function createNewCase() {
  const name = newCaseName.value.trim()
  if (!name) { showToast(t('auto.caseNameRequired'), false); return }
  const tags = newCaseTags.value.split(',').map(t => t.trim()).filter(Boolean)
  const modName = newCaseModule.value.trim()
  const priority = newCasePriority.value
  const id = genId()
  const fkey = fileKeyFromName(name)
  const yaml = yamlSkeleton(name, modName, tags, priority)
  await db.saveAutoCase({ id, name, file_key: fkey, module: modName, tags, priority, yaml_content: yaml } as any)
  showNewDialog.value = false
  newCaseName.value = ""
  newCaseModule.value = ""
  newCaseTags.value = ""
  await loadCaseList()
  selectCaseById(id)
  showToast(t('auto.yamlSkeleton'), true)
}

async function selectCase(c: AutoCase) {
  const full = await db.loadAutoCase(c.id)
  if (full) {
    currentCase.value = full
    editingName.value = full.name
    editingModule.value = full.module
    editingTags.value = full.tags
    editingContent.value = full.yaml_content
    saved.value = true
    activeTab.value = 'editor'
  }
}

function selectCaseById(id: string) {
  const c = caseList.value.find(x => x.id === id)
  if (c) selectCase(c)
}

function toggleCaseSelect(id: string) {
  const idx = selectedCaseIds.value.indexOf(id)
  if (idx >= 0) selectedCaseIds.value.splice(idx, 1)
  else selectedCaseIds.value.push(id)
}

async function confirmDelete(c: AutoCase) { deleteTarget.value = c }

async function doDelete() {
  if (!deleteTarget.value) return
  const id = deleteTarget.value.id
  try {
    await db.deleteAutoCase(id)
    if (currentCase.value?.id === id) {
      currentCase.value = null
      editingName.value = ""
      editingModule.value = ""
      editingTags.value = []
      editingContent.value = ""
    }
    deleteTarget.value = null
    await loadCaseList()
  } catch (e: any) {
    showToast(t('auto.saveFail') + ': ' + (e?.message || e), false)
    deleteTarget.value = null
  }
}

async function duplicateCase(c: AutoCase) {
  const newId = genId()
  await db.saveAutoCase({
    id: newId, name: c.name + ' (copy)', file_key: c.file_key + '_copy',
    module: c.module, tags: c.tags, priority: c.priority,
    yaml_content: c.yaml_content,
  })
  await loadCaseList()
  showToast(t('auto.duplicateSuccess'), true)
}

async function saveCurrentCase() {
  if (!currentCase.value) return
  const name = editingName.value.trim()
  if (!name) { showToast(t('auto.caseNameRequired'), false); return }
  if (autoSaveTimer) { clearTimeout(autoSaveTimer); autoSaveTimer = null }
  try {
    const c = currentCase.value
    await db.saveAutoCase({
      id: c.id, name, file_key: c.file_key, module: editingModule.value, tags: editingTags.value,
      priority: c.priority, author: c.author, description: c.description,
      yaml_content: editingContent.value, version: c.version,
    })
    await db.saveAutoCaseVersion(c.id, c.version, editingContent.value)
    currentCase.value = { ...c, name, module: editingModule.value, yaml_content: editingContent.value, updated_at: new Date().toISOString() }
    saved.value = true
    await loadCaseList()
    showToast(t('auto.saveSuccess'), true)
  } catch (e: any) {
    showToast(t('auto.saveFail') + ': ' + (e?.message || e), false)
  }
}

function restoreVersion(versionId: string, yamlContent: string) {
  editingContent.value = yamlContent
  showVersionHistory.value = false
  showToast('Version restored. Save to persist.', true)
}

// ── Context Menu ─────────────────────────────────────────────
function showContextMenu(e: MouseEvent, c: AutoCase) {
  contextMenu.value = { x: e.clientX, y: e.clientY, case: c }
}

function contextMenuAction(action: string) {
  if (!contextMenu.value) return
  const c = contextMenu.value.case
  contextMenu.value = null
  if (action === 'edit') selectCase(c)
  else if (action === 'duplicate') duplicateCase(c)
  else if (action === 'export') exportSingleCase(c)
  else if (action === 'delete') deleteTarget.value = c
}

async function exportSingleCase(c: AutoCase) {
  try {
    const { save } = await import("@tauri-apps/plugin-dialog")
    const { writeTextFile } = await import("@tauri-apps/plugin-fs")
    const path = await save({ defaultPath: `${c.file_key}.yaml`, filters: [{ name: "YAML", extensions: ["yaml"] }] })
    if (!path) return
    await writeTextFile(path, c.yaml_content)
    showToast(t('auto.exportSuccess'), true)
  } catch (e: any) { showToast(t('auto.exportFail'), false) }
}

// ── Auto-save ─────────────────────────────────────────────────
function scheduleAutoSave() {
  if (!currentCase.value) return
  saved.value = false
  if (autoSaveTimer) clearTimeout(autoSaveTimer)
  autoSaveTimer = setTimeout(doAutoSave, 1500)
}

async function doAutoSave() {
  if (!currentCase.value) return
  const name = editingName.value.trim()
  if (!name) return
  const c = currentCase.value
  if (editingContent.value === c.yaml_content && editingName.value === c.name && editingModule.value === c.module) {
    saved.value = true; return
  }
  try {
    await db.saveAutoCase({
      id: c.id, name, file_key: c.file_key, module: editingModule.value, tags: editingTags.value,
      priority: c.priority, author: c.author, description: c.description,
      yaml_content: editingContent.value, version: c.version,
    })
    currentCase.value = { ...c, name, module: editingModule.value, yaml_content: editingContent.value, updated_at: new Date().toISOString() }
    const idx = caseList.value.findIndex(x => x.id === c.id)
    if (idx >= 0) caseList.value[idx] = { ...caseList.value[idx], name, module: editingModule.value, updated_at: new Date().toISOString() }
    saved.value = true
  } catch (e: any) { console.error('[AutoSpace] autosave failed:', e) }
}

// ── Import / Export YAML ──────────────────────────────────────
async function importYaml() {
  try {
    const { open } = await import("@tauri-apps/plugin-dialog")
    const files = await open({ multiple: true, filters: [{ name: "YAML", extensions: ["yaml", "yml"] }] })
    if (!files) return
    const fileList = Array.isArray(files) ? files : [files]
    pendingImports.value = []
    for (const fp of fileList) {
      if (!fp) continue
      const path = fp as string
      const content = await (await import("@tauri-apps/plugin-fs")).readTextFile(path)
      const parts = path.replace(/\\/g, '/').split('/')
      const fileName = parts.pop() || 'untitled'
      const name = fileName.replace(/\.(yaml|yml)$/i, '')
      const fkey = fileKeyFromName(name)
      // Check for conflict
      const existing = caseList.value.find(c => c.file_key === fkey)
      if (existing) {
        importConflict.value = { name, id: existing.id, file_key: fkey, content }
        return
      }
      pendingImports.value.push({ name, file_key: fkey, content })
    }
    await flushImports()
  } catch (e: any) { showToast(t('auto.importFail'), false) }
}

async function flushImports() {
  let count = 0
  for (const p of pendingImports.value) {
    let modName = ''; let priority = 'P2'; let tags: string[] = []
    const modMatch = p.content.match(/^\s*module:\s*"([^"]+)"/m)
    if (modMatch) modName = modMatch[1]
    const priMatch = p.content.match(/^\s*priority:\s*"([^"]+)"/m)
    if (priMatch) priority = priMatch[1]
    const tagMatch = p.content.match(/^\s*tags:\s*\[([^\]]*)\]/m)
    if (tagMatch) tags = tagMatch[1].split(',').map(t => t.trim().replace(/"/g, '')).filter(Boolean)
    const id = genId()
    await db.saveAutoCase({ id, name: p.name, file_key: p.file_key, module: modName, tags, priority, yaml_content: p.content })
    count++
  }
  pendingImports.value = []
  await loadCaseList()
  showToast(t('auto.importSuccess', { count: String(count) }), true)
}

function importOverwrite() {
  if (!importConflict.value) return
  pendingImports.value.push({ name: importConflict.value.name, file_key: importConflict.value.file_key, content: importConflict.value.content })
  importConflict.value = null
  flushImports()
}

function importNewCopy() {
  if (!importConflict.value) return
  const orig = importConflict.value
  pendingImports.value.push({ name: orig.name + '_imported', file_key: orig.file_key + '_imported', content: orig.content })
  importConflict.value = null
  flushImports()
}

async function exportYaml() {
  if (!currentCase.value) return
  try {
    const { save } = await import("@tauri-apps/plugin-dialog")
    const { writeTextFile } = await import("@tauri-apps/plugin-fs")
    const path = await save({ defaultPath: `${currentCase.value.file_key}.yaml`, filters: [{ name: "YAML", extensions: ["yaml"] }] })
    if (!path) return
    await writeTextFile(path, editingContent.value)
    showToast(t('auto.exportSuccess'), true)
  } catch (e: any) { showToast(t('auto.exportFail'), false) }
}

// ── Validate YAML ─────────────────────────────────────────────
function validateYaml() {
  try {
    const lines = editingContent.value.split('\n')
    const hasMeta = lines.some(l => l.trim().startsWith('meta:'))
    const hasSteps = lines.some(l => l.trim().startsWith('steps:'))
    showToast(hasMeta && hasSteps ? t('auto.yamlValid') : t('auto.yamlInvalid'), hasMeta && hasSteps)
  } catch { showToast(t('auto.yamlInvalid'), false) }
}

// ── Run ─────────────────────────────────────────────────────
function onAutoEvent(event: AutoStepEvent) {
  if (event.type === 'step_start') {
    consoleOutput.value.push({ text: `▶ ${event.desc || event.step_id || ''}`, type: 'step_start' })
  } else if (event.type === 'step_done') {
    consoleOutput.value.push({ text: `  ✅ ${event.step_id || ''} passed (${event.ms || 0}ms)`, type: 'step_done' })
  } else if (event.type === 'step_heal') {
    consoleOutput.value.push({ text: `  🔧 ${event.step_id || ''} healed (${event.ms || 0}ms, ${event.method || ''})`, type: 'step_heal' })
  } else if (event.type === 'step_fail') {
    consoleOutput.value.push({ text: `  ❌ ${event.step_id || ''} failed: ${event.error || ''}`, type: 'step_fail' })
  } else if (event.type === 'screenshot') {
    latestScreenshot.value = event.path || null
  } else if (event.type === 'suite_done') {
    consoleOutput.value.push({ text: `  ✅ Suite completed (passed: ${event.passed || 0}, failed: ${event.failed || 0}, healed: ${event.healed || 0})`, type: 'step_done' })
    if (currentRunId.value) {
      db.saveAutoRunRecord({
        id: currentRunId.value, status: 'done',
        passed: event.passed || 0, failed: event.failed || 0, healed: event.healed || 0,
        startedAt: new Date().toISOString(), endedAt: new Date().toISOString(),
      })
    }
    running.value = false
    lastRunId.value = currentRunId.value
    currentRunId.value = null
    if (eventUnlisten) { eventUnlisten(); eventUnlisten = null }
    loadRunRecords()
    showToast('Run completed', true)
  } else {
    consoleOutput.value.push({ text: `  ${event.desc || ''}`, type: 'info' })
  }
  scrollToBottom()
}

async function runSingle() {
  if (!currentCase.value || running.value) return
  await runCases([currentCase.value])
}

async function runSelected() {
  if (selectedCaseIds.value.length === 0 || running.value) return
  await runCases(caseList.value.filter(c => selectedCaseIds.value.includes(c.id)))
}

async function runAll() {
  if (caseList.value.length === 0 || running.value) return
  await runCases(caseList.value)
}

async function runCases(cases: AutoCase[]) {
  running.value = true
  activeTab.value = 'console'
  consoleOutput.value = []
  latestScreenshot.value = null
  const runId = genId()
  currentRunId.value = runId
  const now = new Date().toISOString()
  await db.saveAutoRunRecord({ id: runId, total: cases.length, startedAt: now })
  eventUnlisten = await listenAutoEvents(onAutoEvent)
  try {
    if (cases.length === 1) {
      consoleOutput.value.push({ text: `▶ Running: ${cases[0].name}`, type: 'step_start' })
      await runAutoCase(runId, cases[0].id, connectedDevice.value)
    } else {
      consoleOutput.value.push({ text: `▶ Running suite: ${cases.length} cases`, type: 'step_start' })
      await runAutoSuite(runId, cases.map(c => c.id), connectedDevice.value)
    }
  } catch (e: any) {
    consoleOutput.value.push({ text: `  ❌ ${e?.message || e}`, type: 'step_fail' })
    running.value = false
    currentRunId.value = null
    await db.saveAutoRunRecord({ id: runId, status: 'aborted', total: cases.length, startedAt: now, endedAt: new Date().toISOString() })
    await loadRunRecords()
    showToast('Run failed: ' + (e?.message || e), false)
    if (eventUnlisten) { eventUnlisten(); eventUnlisten = null }
  }
  setTimeout(() => {
    if (running.value && currentRunId.value) {
      running.value = false; currentRunId.value = null
      if (eventUnlisten) { eventUnlisten(); eventUnlisten = null }
      loadRunRecords(); showToast('Run completed', true)
    }
  }, 60000)
}

async function stopRun() {
  if (currentRunId.value) await stopAutoRun(currentRunId.value)
  running.value = false
  consoleOutput.value.push({ text: '⏹ Run stopped by user', type: 'info' })
  if (eventUnlisten) { eventUnlisten(); eventUnlisten = null }
  lastRunId.value = currentRunId.value
  currentRunId.value = null
}

function viewLastReport() {
  if (lastRunId.value) {
    reportRunId.value = lastRunId.value
    activeTab.value = 'report'
  }
}

// ── Data loading ──────────────────────────────────────────────
async function loadCaseList() { caseList.value = await db.listAutoCases() }
async function loadRunRecords() { runRecords.value = await db.listAutoRunRecords(20) }

async function scrollToBottom() {
  await nextTick()
  if (outputContainer.value) outputContainer.value.scrollTop = outputContainer.value.scrollHeight
}

// ── Lifecycle ─────────────────────────────────────────────────
onMounted(async () => {
  await loadCaseList()
  await loadRunRecords()
  window.addEventListener('storage', (e: any) => {
    if (e.key === 'last_device_serial') connectedDevice.value = e.newValue || ''
  })
})

onUnmounted(() => {
  if (autoSaveTimer) clearTimeout(autoSaveTimer)
  if (toastTimer) clearTimeout(toastTimer)
  if (eventUnlisten) eventUnlisten()
})

watch(editingContent, () => { scheduleAutoSave() })
watch(editingName, () => { scheduleAutoSave() })
watch(editingModule, () => { scheduleAutoSave() })
watch(searchQuery, () => { currentPage.value = 1 })
watch(moduleFilter, () => { currentPage.value = 1 })
</script>

<style scoped>
.dropdown-enter-active,
.dropdown-leave-active { transition: all 0.15s ease; }
.dropdown-enter-from,
.dropdown-leave-to { opacity: 0; transform: translateY(-6px); }
</style>
