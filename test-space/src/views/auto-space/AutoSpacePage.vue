<template>
  <div class="flex flex-col flex-1 min-h-0 -mx-margin-page pb-2 box-border select-none">
    <!-- Top Toolbar -->
    <div class="flex items-center gap-3 mb-2 flex-shrink-0 ml-3">
      <div class="relative" @click.stop>
        <button ref="deviceDropdownBtnRef" @click="toggleDeviceDropdown"
          class="flex items-center gap-2 bg-white/30 border border-outline-variant/30 rounded-full pl-3 pr-3 py-2 font-caption text-caption text-on-surface cursor-pointer hover:bg-secondary/10 hover:border-secondary/30 hover:scale-105 transition-all min-w-[130px] max-w-[200px] backdrop-blur-sm select-none">
          <div class="w-2 h-2 rounded-full shrink-0" :class="deviceList.length > 0 ? 'bg-success-indicator' : 'bg-outline-variant'"></div>
          <span class="truncate flex-1 text-left">{{ selectedDevice ? deviceList.find(d => d.serial === selectedDevice)?.model || selectedDevice : t('auto.noDevice') }}</span>
          <span class="material-symbols-outlined text-[14px] text-on-surface-variant shrink-0">unfold_more</span>
        </button>
        <Teleport to="body">
          <div v-if="showDeviceDropdown" class="fixed inset-0 z-50" @click="showDeviceDropdown = false"></div>
          <div v-if="showDeviceDropdown" class="fixed z-50 bg-white rounded-lg p-1 max-h-48 overflow-y-auto custom-scrollbar shadow-lg min-w-[200px]"
            :style="{ top: deviceDropdownPos.top + 'px', left: deviceDropdownPos.left + 'px' }">
            <button class="w-full flex items-center gap-2 px-2 py-1.5 rounded font-caption text-caption text-on-surface hover:bg-gray-100 select-none text-left"
              @mousedown.prevent @click="selectDevice(''); showDeviceDropdown = false">
              <div class="w-2 h-2 rounded-full shrink-0 bg-outline-variant"></div>
              <span class="text-on-surface-variant/40">{{ t('auto.noDevice') }}</span>
            </button>
            <div v-if="deviceList.length === 0" class="px-3 py-2 text-[11px] text-on-surface-variant/30 text-center">
              {{ t('auto.scanning') }}
            </div>
            <button v-for="d in deviceList" :key="d.serial"
              class="w-full flex items-center gap-2 px-2 py-1.5 rounded font-caption text-caption text-on-surface hover:bg-gray-100 select-none text-left"
              @mousedown.prevent @click="selectDevice(d.serial); showDeviceDropdown = false">
              <div class="w-2 h-2 rounded-full shrink-0" :class="d.status === 'online' ? 'bg-success-indicator' : 'bg-outline-variant'"></div>
              <span class="truncate flex-1">{{ d.model || d.serial }}</span>
              <span class="text-[10px] text-on-surface-variant/50 truncate max-w-[80px]">{{ d.serial }}</span>
            </button>
          </div>
        </Teleport>
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

      <div class="relative" @click.stop>
        <button class="flex items-center gap-1.5 rounded px-2.5 py-1.5 text-[12px] select-none border border-white/10 hover:border-white/20 transition-colors min-w-0 text-on-surface-variant/80"
          :class="tagFilterOpen ? 'border-white/30 bg-white/5' : ''"
          @click="tagFilterOpen = !tagFilterOpen">
          <span class="truncate max-w-[80px]">{{ tagFilter || t('auto.filterTag') }}</span>
          <span class="material-symbols-outlined text-[14px] transition-transform" :class="tagFilterOpen ? 'rotate-180' : ''">expand_more</span>
        </button>
        <div v-if="tagFilterOpen" class="absolute top-full left-0 mt-1 z-50 min-w-[130px] rounded-lg py-1 shadow-xl border border-white/10 bg-white/90 backdrop-blur-xl" @mouseleave="tagFilterOpen = false">
          <button class="w-full text-left px-3 py-1.5 text-[12px] hover:bg-black/5 flex items-center gap-2 select-none" :class="!tagFilter ? 'text-on-surface font-semibold' : 'text-on-surface-variant/70'" @click="tagFilter = ''; tagFilterOpen = false">
            <span class="material-symbols-outlined text-[14px]" :class="!tagFilter ? '' : 'invisible'">check</span>
            <span>{{ t('auto.filterTag') }}</span>
          </button>
          <button v-for="tag in uniqueTags" :key="tag" class="w-full text-left px-3 py-1.5 text-[12px] hover:bg-black/5 flex items-center gap-2 select-none" :class="tagFilter === tag ? 'text-on-surface font-semibold' : 'text-on-surface-variant/70'" @click="tagFilter = tag; tagFilterOpen = false">
            <span class="material-symbols-outlined text-[14px]" :class="tagFilter === tag ? '' : 'invisible'">check</span>
            <span>{{ tag }}</span>
          </button>
        </div>
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
      <div v-show="!leftPanelCollapsed" class="w-56 flex-shrink-0 ml-1 rounded-lg bg-white/10 backdrop-blur-[60px] border border-white/50 shadow-lg flex flex-col overflow-hidden">
        <div class="px-3 py-2 border-b border-white/10 space-y-1.5">
          <div class="relative">
            <input v-model="searchQuery" class="w-full bg-white/5 border border-white/10 rounded-lg px-2.5 py-1 text-[12px] text-on-surface placeholder-on-surface-variant/40 focus:outline-none focus:border-white/20 select-text" :placeholder="t('auto.searchCases')" />
            <span v-if="searchQuery" class="absolute right-1.5 top-1/2 -translate-y-1/2 text-on-surface-variant/40 cursor-pointer" @click="searchQuery = ''">
              <span class="material-symbols-outlined text-[14px]">close</span>
            </span>
          </div>
          <div class="relative" @click.stop>
            <button class="flex items-center gap-1.5 rounded px-2 py-1.5 text-[12px] w-full select-none border border-white/10 hover:border-white/20 transition-colors text-on-surface-variant/80"
              :class="moduleFilterOpen ? 'border-white/30 bg-white/5' : ''"
              @click="moduleFilterOpen = !moduleFilterOpen">
              <span class="truncate flex-1 text-left">{{ moduleFilter || t('auto.allModules') }}</span>
              <span class="material-symbols-outlined text-[14px] transition-transform flex-shrink-0" :class="moduleFilterOpen ? 'rotate-180' : ''">expand_more</span>
            </button>
            <div v-if="moduleFilterOpen" class="absolute top-full left-0 mt-1 z-50 w-full rounded-lg py-1 shadow-xl border border-white/10 bg-white/90 backdrop-blur-xl" @mouseleave="moduleFilterOpen = false">
              <button class="w-full text-left px-3 py-1.5 text-[12px] hover:bg-black/5 flex items-center gap-2 select-none" :class="!moduleFilter ? 'text-on-surface font-semibold' : 'text-on-surface-variant/70'" @click="moduleFilter = ''; moduleFilterOpen = false">
                <span class="material-symbols-outlined text-[14px]" :class="!moduleFilter ? '' : 'invisible'">check</span>
                <span>{{ t('auto.allModules') }}</span>
              </button>
              <button v-for="m in moduleList" :key="m" class="w-full text-left px-3 py-1.5 text-[12px] hover:bg-black/5 flex items-center gap-2 select-none" :class="moduleFilter === m ? 'text-on-surface font-semibold' : 'text-on-surface-variant/70'" @click="moduleFilter = m; moduleFilterOpen = false">
                <span class="material-symbols-outlined text-[14px]" :class="moduleFilter === m ? '' : 'invisible'">check</span>
                <span>{{ m }}</span>
              </button>
            </div>
          </div>
        </div>
        <div class="flex-1 overflow-y-auto custom-scrollbar">
          <div v-if="pagedCases.length === 0" class="p-4 text-[12px] text-on-surface-variant/40 text-center">
            {{ t('auto.noCases') }}
          </div>
          <template v-for="group in groupedCases" :key="group.tag">
            <div class="flex items-center gap-1 px-3 py-1.5 text-[11px] text-on-surface-variant/40 font-medium cursor-pointer select-none hover:text-on-surface-variant/60" @click="toggleGroup(group.tag)">
              <span class="material-symbols-outlined text-[14px] transition-transform" :class="group.expanded ? '' : '-rotate-90'">expand_more</span>
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
            <!-- Monaco Editor -->
            <div class="flex-1 min-h-0 rounded-2xl overflow-hidden border border-white/10 flex flex-col">
              <div class="flex items-center gap-3 px-4 py-2 bg-white/10 border-b border-white/5 flex-shrink-0">
                <div class="flex-1"></div>
                <div class="flex items-center gap-1">
                  <button class="flex items-center gap-1 px-3 py-1 rounded-full text-[11px] text-on-surface-variant/80 hover:bg-white/20 transition-colors select-none glass-button" @click="saveCurrentCase">
                    <span class="material-symbols-outlined text-[13px]">save</span>
                    {{ t('auto.save') }}
                  </button>
                  <button class="flex items-center gap-1 px-3 py-1 rounded-full text-[11px] text-on-surface-variant/80 hover:bg-white/20 transition-colors select-none glass-button" @click="exportYaml">
                    <span class="material-symbols-outlined text-[13px]">file_upload</span>
                    {{ t('auto.exportYaml') }}
                  </button>
                  <button class="flex items-center gap-1 px-3 py-1 rounded-full text-[11px] text-on-surface-variant/80 hover:bg-white/20 transition-colors select-none glass-button" @click="validateYaml">
                    <span class="material-symbols-outlined text-[13px]">check_circle</span>
                    {{ t('auto.validateYaml') }}
                  </button>
                  <button class="flex items-center gap-1 px-3 py-1 rounded-full text-[11px] bg-green-500/25 hover:bg-green-500/35 text-green-500 transition-colors select-none" @click="runSingle">
                    <span class="material-symbols-outlined text-[13px]">play_arrow</span>
                    {{ t('auto.run') }}
                  </button>
                </div>
              </div>
              <div class="flex-1 flex flex-col" style="min-height:0">
                <VisualEditor
                  :yaml="editingContent"
                  :name="editingName"
                  :module="editingModule"
                  :tags="editingTagsText"
                  :priority="currentCase?.priority || 'P2'"
                  :description="currentCase?.description || ''"
                  :screenshot-path="screenshotResult"
                  @update:yaml="editingContent = $event; scheduleAutoSave()"
                  @update:name="editingName = $event; scheduleAutoSave()"
                  @update:module="editingModule = $event; scheduleAutoSave()"
                  @update:tags="editingTagsText = $event; syncTagsFromText(); scheduleAutoSave()"
                  @update:priority="if (currentCase) { currentCase.priority = $event; scheduleAutoSave() }"
                  @update:description="if (currentCase) { currentCase.description = $event; scheduleAutoSave() }"
                  @request-screenshot="handleEditorScreenshot" />
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
                <span v-if="running && consoleStepTotal > 0" class="text-[11px] text-on-surface-variant/60">
                  step {{ consoleStepCurrent }}/{{ consoleStepTotal }}
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
                      <button class="glass-button px-3 py-1 rounded-lg text-[11px] flex items-center gap-1 select-none" @click="exportRunRecord(r)">
                        <span class="material-symbols-outlined text-[13px]">file_download</span>
                        {{ t('auto.exportRecord') }}
                      </button>
                      <button class="glass-button px-3 py-1 rounded-lg text-[11px] flex items-center gap-1 select-none" @click="reportRunId = r.id">
                        <span class="material-symbols-outlined text-[13px]">visibility</span>
                        {{ t('auto.viewReport') }}
                      </button>
                      <button class="glass-button px-2 py-1 rounded-lg text-[11px] flex items-center gap-1 select-none" @click="deleteRunRecordTarget = r">
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

    <!-- Screenshot Zoom -->
    <Teleport to="body">
      <div v-if="screenshotZoom" class="fixed inset-0 z-50 flex items-center justify-center" @click.self="screenshotZoom = null">
        <div class="absolute inset-0 bg-black/60 backdrop-blur-sm"></div>
        <img :src="screenshotZoom" class="max-w-[90vw] max-h-[90vh] object-contain relative z-10 rounded-2xl shadow-2xl" @click="screenshotZoom = null" />
      </div>
    </Teleport>

    <!-- Delete case confirmation -->
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

    <!-- Delete run record confirmation -->
    <Teleport to="body">
      <div v-if="deleteRunRecordTarget" class="fixed inset-0 z-50 flex items-center justify-center" @click.self="deleteRunRecordTarget = null">
        <div class="absolute inset-0 bg-black/30 backdrop-blur-sm"></div>
        <div class="glass-panel rounded-[2rem] p-6 w-full max-w-md relative z-10 bg-white/60">
          <div class="flex justify-between items-center mb-4">
            <h3 class="font-label-md text-label-md text-on-surface font-semibold flex items-center gap-1.5 select-none">
              <span class="material-symbols-outlined text-[16px] text-red-400">warning</span>{{ t('auto.deleteTitle') }}
            </h3>
            <button class="glass-button p-1 rounded select-none" @click="deleteRunRecordTarget = null">
              <span class="material-symbols-outlined text-[18px]">close</span>
            </button>
          </div>
          <div class="text-[13px] text-on-surface-variant/80 mb-4">{{ t('auto.deleteDesc', { name: deleteRunRecordTarget.id }) }}</div>
          <div class="flex gap-2 justify-end border-t border-outline-variant/30 pt-4">
            <button class="glass-button px-4 py-2 rounded-lg font-label-md text-label-md select-none" @click="deleteRunRecordTarget = null">{{ t('auto.deleteCancel') }}</button>
            <button class="glass-button px-4 py-2 rounded-lg font-label-md text-label-md select-none text-red-400" @click="confirmDeleteRunRecord">{{ t('auto.deleteConfirm') }}</button>
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
import { useAdb } from "@/composables/useAdb"
import type { AdbDeviceInfo } from "@/composables/useAdb"
import { runAutoCase, runAutoSuite, stopAutoRun, listenAutoEvents } from "@/services/autoRunService"
import type { AutoStepEvent } from "@/services/autoRunService"
import VisualEditor from "./VisualEditor.vue"
import ReportViewer from "./ReportViewer.vue"

const { t } = useI18n()

// ── State ─────────────────────────────────────────────────────
const caseList = ref<AutoCase[]>([])
const currentCase = ref<AutoCase | null>(null)
const editingName = ref("")
const editingModule = ref("")
const editingTags = ref<string[]>([])
const editingTagsText = ref("")
const editingContent = ref("")
const saved = ref(true)
const searchQuery = ref("")
const moduleFilter = ref("")
const tagFilter = ref("")
const moduleFilterOpen = ref(false)
const tagFilterOpen = ref(false)
const currentPage = ref(1)
const PAGE_SIZE = 50
const leftPanelCollapsed = ref(false)

const activeTab = ref<'editor' | 'console' | 'report'>('editor')
const running = ref(false)
const currentRunId = ref<string | null>(null)
const lastRunId = ref<string | null>(null)
const selectedCaseIds = ref<string[]>([])

const outputContainer = ref<HTMLElement | null>(null)
const consoleOutput = ref<{ text: string; type: string }[]>([])
const consoleStepCurrent = ref(0)
const consoleStepTotal = ref(0)
const latestScreenshot = ref<string | null>(null)
const runRecords = ref<AutoRunRecord[]>([])
const reportRunId = ref<string | null>(null)
const screenshotZoom = ref<string | null>(null)

const workspaceTabs = [
  { key: 'editor' as const, icon: 'edit', labelKey: 'auto.editor' },
  { key: 'console' as const, icon: 'terminal', labelKey: 'auto.console' },
  { key: 'report' as const, icon: 'history', labelKey: 'auto.report' },
]

let autoSaveTimer: ReturnType<typeof setTimeout> | null = null
let eventUnlisten: (() => void) | null = null

const { listDevices, screenshot: adbScreenshot } = useAdb()
const screenshotResult = ref('')
const deviceList = ref<AdbDeviceInfo[]>([])
const selectedDevice = ref(localStorage.getItem('last_device_serial') || '')
const showDeviceDropdown = ref(false)
const deviceDropdownBtnRef = ref<HTMLElement | null>(null)
const deviceDropdownPos = ref({ top: 0, left: 0 })
let devicePollTimer: ReturnType<typeof setInterval> | null = null

function toggleDeviceDropdown() {
  if (showDeviceDropdown.value) {
    showDeviceDropdown.value = false
    return
  }
  if (deviceDropdownBtnRef.value) {
    const rect = deviceDropdownBtnRef.value.getBoundingClientRect()
    deviceDropdownPos.value = { top: rect.bottom + 4, left: rect.left }
  }
  showDeviceDropdown.value = true
}

function selectDevice(serial: string) {
  selectedDevice.value = serial
  if (serial) localStorage.setItem('last_device_serial', serial)
  else localStorage.removeItem('last_device_serial')
}

async function handleEditorScreenshot() {
  const serial = selectedDevice.value
  if (!serial) { showToast('No device connected', false); return }
  const ts = new Date().toISOString().replace(/[:.]/g, '-')
  const savePath = `screenshot_${ts}.png`
  try {
    screenshotResult.value = ''
    const result = await adbScreenshot(serial, savePath)
    screenshotResult.value = result || savePath
    showToast('Screenshot captured', true)
  } catch (e) {
    showToast(`Screenshot failed: ${e}`, false)
  }
}

async function pollDevices() {
  try {
    deviceList.value = await listDevices()
    if (selectedDevice.value && !deviceList.value.find(d => d.serial === selectedDevice.value)) {
      selectDevice('')
    } else if (!selectedDevice.value && deviceList.value.length > 0) {
      selectDevice(deviceList.value[0].serial)
    }
  } catch {}
}

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
const deleteRunRecordTarget = ref<AutoRunRecord | null>(null)

async function confirmDeleteRunRecord() {
  if (!deleteRunRecordTarget.value) return
  await db.deleteAutoRunRecord?.(deleteRunRecordTarget.value.id)
  deleteRunRecordTarget.value = null
  await loadRunRecords()
}

// ── Export run record ────────────────────────────────────────
async function exportRunRecord(r: AutoRunRecord) {
  try {
    const { save } = await import("@tauri-apps/plugin-dialog")
    const { writeTextFile } = await import("@tauri-apps/plugin-fs")
    const steps = await db.listAutoRunSteps(r.id)
    const summary = {
      runId: r.id, status: r.status, deviceSerial: r.deviceSerial,
      startedAt: r.startedAt, endedAt: r.endedAt,
      total: r.total, passed: r.passed, failed: r.failed,
      healed: r.healed, skipped: r.skipped, durationMs: r.durationMs,
      steps: steps.map(s => ({
        id: s.id, stepId: s.stepId, stepDesc: s.stepDesc,
        caseId: s.caseId, status: s.status, durationMs: s.durationMs,
        errorMessage: s.errorMessage, healLog: s.healLog, locatorUsed: s.locatorUsed,
      })),
    }
    const path = await save({ defaultPath: `summary-${r.id}.json`, filters: [{ name: "JSON", extensions: ["json"] }] })
    if (!path) return
    await writeTextFile(path, JSON.stringify(summary, null, 2))
    showToast(t('auto.exportSuccess'), true)
  } catch (e: any) { showToast(t('auto.exportFail'), false) }
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

function syncTagsFromText() {
  editingTags.value = editingTagsText.value.split(',').map(t => t.trim()).filter(Boolean)
}

// ── Module list ───────────────────────────────────────────────
const moduleList = computed(() => {
  const modules = new Set<string>()
  for (const c of caseList.value) { if (c.module) modules.add(c.module) }
  return Array.from(modules).sort()
})

// ── Tag list ──────────────────────────────────────────────────
const uniqueTags = computed(() => {
  const tags = new Set<string>()
  for (const c of caseList.value) {
    for (const t of c.tags) tags.add(t)
  }
  return Array.from(tags).sort()
})

// ── Case filtering & grouping ─────────────────────────────────
const filteredCases = computed(() => {
  let list = caseList.value
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.trim().toLowerCase()
    list = list.filter(c => c.name.toLowerCase().includes(q) || c.tags.some(t => t.toLowerCase().includes(q)))
  }
  if (moduleFilter.value) list = list.filter(c => c.module === moduleFilter.value)
  if (tagFilter.value) list = list.filter(c => c.tags.includes(tagFilter.value))
  return list
})

const pagedCases = computed(() => {
  const start = (currentPage.value - 1) * PAGE_SIZE
  return filteredCases.value.slice(start, start + PAGE_SIZE)
})
const totalPages = computed(() => Math.max(1, Math.ceil(filteredCases.value.length / PAGE_SIZE)))

const groupExpandedState = ref<Record<string, boolean>>({})

function toggleGroup(tag: string) {
  groupExpandedState.value[tag] = !(groupExpandedState.value[tag] ?? true)
}

const groupedCases = computed(() => {
  const groups: { tag: string; cases: AutoCase[]; expanded: boolean }[] = []
  const tagMap = new Map<string, AutoCase[]>()
  for (const c of pagedCases.value) {
    const tags = c.tags.length > 0 ? c.tags : [t('auto.noTags')]
    for (const tag of tags) {
      if (!tagMap.has(tag)) tagMap.set(tag, [])
      if (!tagMap.get(tag)!.find(x => x.id === c.id)) tagMap.get(tag)!.push(c)
    }
  }
  for (const [tag, cases] of tagMap) {
    groups.push({ tag, cases, expanded: groupExpandedState.value[tag] ?? true })
  }
  groups.sort((a, b) => a.tag.localeCompare(b.tag))
  return groups
})

// ── CRUD ──────────────────────────────────────────────────────
function genId(): string { return crypto.randomUUID().replace(/-/g, '').slice(0, 12) }
function fileKeyFromName(name: string): string {
  return `TC-${name.replace(/[<>:"/\\|?*\s]/g, '_').toLowerCase()}`
}

function yamlSkeleton(name: string, _moduleName: string, tags: string[], priority: string): string {
  const tagStr = tags.map(t => `    - "${t}"`).join('\n')
  return `# Test Space Automation Case v1.0
meta:
  id: "${fileKeyFromName(name)}"
  name: "${name}"
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
    editingTagsText.value = full.tags.join(', ')
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
  selectCaseById(newId)
  showToast(t('auto.duplicateSuccess'), true)
}

async function saveCurrentCase() {
  if (!currentCase.value) return
  const name = editingName.value.trim()
  if (!name) { showToast(t('auto.caseNameRequired'), false); return }
  if (autoSaveTimer) { clearTimeout(autoSaveTimer); autoSaveTimer = null }
  syncTagsFromText()
  try {
    const c = currentCase.value
    await db.saveAutoCase({
      id: c.id, name, file_key: c.file_key, module: editingModule.value, tags: editingTags.value,
      priority: c.priority, author: c.author, description: c.description,
      yaml_content: editingContent.value, version: c.version,
    })
    currentCase.value = { ...c, name, module: editingModule.value, yaml_content: editingContent.value, updated_at: new Date().toISOString() }
    saved.value = true
    await loadCaseList()
    showToast(t('auto.saveSuccess'), true)
  } catch (e: any) {
    showToast(t('auto.saveFail') + ': ' + (e?.message || e), false)
  }
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
  syncTagsFromText()
  const c = currentCase.value
  const changed = editingContent.value !== c.yaml_content || editingName.value !== c.name || editingModule.value !== c.module || JSON.stringify(editingTags.value) !== JSON.stringify(c.tags)
  if (!changed) {
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

async function importOverwrite() {
  if (!importConflict.value) return
  pendingImports.value.push({ name: importConflict.value.name, file_key: importConflict.value.file_key, content: importConflict.value.content })
  importConflict.value = null
  await flushImports()
}

async function importNewCopy() {
  if (!importConflict.value) return
  const orig = importConflict.value
  pendingImports.value.push({ name: orig.name + '_imported', file_key: orig.file_key + '_imported', content: orig.content })
  importConflict.value = null
  await flushImports()
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
    const content = editingContent.value
    const lines = content.split('\n')
    const errors: string[] = []

    const hasMeta = lines.some(l => l.trim().startsWith('meta:'))
    if (!hasMeta) errors.push('Missing meta: section')

    const hasSteps = lines.some(l => l.trim().startsWith('steps:'))
    if (!hasSteps) errors.push('Missing steps: section')

    const hasSetup = lines.some(l => l.trim().startsWith('setup:'))
    if (!hasSetup) errors.push('Missing setup: section')

    const hasTeardown = lines.some(l => l.trim().startsWith('teardown:'))
    if (!hasTeardown) errors.push('Missing teardown: section')

    // Check for basic YAML syntax issues (indentation, colons)
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i]
      const trimmed = line.trim()
      if (trimmed && !trimmed.startsWith('#') && !trimmed.includes(':') && !trimmed.startsWith('-')) {
        errors.push(`Line ${i + 1}: missing colon - "${trimmed.slice(0, 40)}"`)
      }
    }

    // Check id uniqueness in steps
    const stepIds = new Set<string>()
    const idRegex = /^\s*id:\s*"([^"]+)"/
    for (let i = 0; i < lines.length; i++) {
      const m = lines[i].match(idRegex)
      if (m) {
        if (stepIds.has(m[1])) errors.push(`Duplicate step id: "${m[1]}" at line ${i + 1}`)
        stepIds.add(m[1])
      }
    }

    if (errors.length === 0) {
      showToast(t('auto.yamlValid'), true)
    } else {
      showToast(`YAML issues: ${errors.slice(0, 3).join('; ')}${errors.length > 3 ? `... (+${errors.length - 3} more)` : ''}`, false)
    }
  } catch { showToast(t('auto.yamlInvalid'), false) }
}

// ── Run ─────────────────────────────────────────────────────
function onAutoEvent(event: AutoStepEvent) {
  if (event.type === 'step_start') {
    consoleStepCurrent.value++
    if (event.step_total) consoleStepTotal.value = event.step_total
    consoleOutput.value.push({ text: `▶ ${event.desc || event.step_id || ''}`, type: 'step_start' })
  } else if (event.type === 'step_done') {
    consoleOutput.value.push({ text: `  ✅ ${event.step_id || ''} passed (${event.ms || 0}ms)`, type: 'step_done' })
    if (currentRunId.value && event.step_id) {
      db.saveAutoRunStep({
        id: genId(), runId: currentRunId.value, caseId: event.step_id || '', stepId: event.step_id,
        stepDesc: event.desc || '', status: event.status || 'passed', durationMs: event.ms || 0,
        healLog: null,
      }).catch(() => {})
    }
  } else if (event.type === 'step_heal') {
    consoleOutput.value.push({ text: `  🔧 ${event.step_id || ''} healed (${event.ms || 0}ms, ${event.method || ''})`, type: 'step_heal' })
    if (currentRunId.value && event.step_id) {
      let healLog: any = null
      try { if (event.heal_log) healLog = JSON.parse(event.heal_log) } catch {}
      db.saveAutoRunStep({
        id: genId(), runId: currentRunId.value, caseId: event.step_id || '', stepId: event.step_id,
        stepDesc: event.desc || '', status: 'healed', durationMs: event.ms || 0,
        healLog: healLog ? JSON.stringify(healLog) : null,
      }).catch(() => {})
    }
  } else if (event.type === 'step_fail') {
    consoleOutput.value.push({ text: `  ❌ ${event.step_id || ''} failed: ${event.error || ''}`, type: 'step_fail' })
    if (currentRunId.value && event.step_id) {
      db.saveAutoRunStep({
        id: genId(), runId: currentRunId.value, caseId: event.step_id || '', stepId: event.step_id,
        stepDesc: event.desc || '', status: 'failed', durationMs: event.ms || 0,
        errorMessage: event.error || '', healLog: null,
      }).catch(() => {})
    }
  } else if (event.type === 'screenshot') {
    latestScreenshot.value = event.path || null
  } else if (event.type === 'suite_done') {
    consoleOutput.value.push({ text: `  ✅ Suite completed (passed: ${event.passed || 0}, failed: ${event.failed || 0}, healed: ${event.healed || 0})`, type: 'step_done' })
    const isRealRun = (event.passed || 0) > 0 || (event.failed || 0) > 0 || (event.healed || 0) > 0
    if (!isRealRun) {
      consoleOutput.value.push({ text: '  ⚠ No steps were executed - Python engine may not be set up', type: 'step_fail' })
    }
    if (currentRunId.value) {
      db.saveAutoRunRecord({
        id: currentRunId.value, status: isRealRun ? 'done' : 'aborted',
        passed: event.passed || 0, failed: event.failed || 0, healed: event.healed || 0,
        startedAt: new Date().toISOString(), endedAt: new Date().toISOString(),
      }).catch(() => {})
    }
    cleanupRun()
    showToast(isRealRun ? 'Run completed' : 'No engine - install Python dependencies', isRealRun)
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
  consoleStepCurrent.value = 0
  consoleStepTotal.value = 0
  const runId = genId()
  currentRunId.value = runId
  const now = new Date().toISOString()
  await db.saveAutoRunRecord({ id: runId, total: cases.length, startedAt: now })
  eventUnlisten = await listenAutoEvents(onAutoEvent)
  const device = selectedDevice.value
  try {
    if (cases.length === 1) {
      consoleOutput.value.push({ text: `▶ Running: ${cases[0].name}`, type: 'step_start' })
      await runAutoCase(runId, cases[0].id, device)
    } else {
      consoleOutput.value.push({ text: `▶ Running suite: ${cases.length} cases`, type: 'step_start' })
      await runAutoSuite(runId, cases.map(c => c.id), device)
    }
  } catch (e: any) {
    consoleOutput.value.push({ text: `  ❌ ${e?.message || e}`, type: 'step_fail' })
    await db.saveAutoRunRecord({ id: runId, status: 'aborted', startedAt: now, endedAt: new Date().toISOString() }).catch(() => {})
    cleanupRun()
    showToast('Run failed: ' + (e?.message || e), false)
  }
  // If suite_done never fires (engine not running), abort after 10s
  setTimeout(() => {
    if (running.value && currentRunId.value) {
      const rid = currentRunId.value
      consoleOutput.value.push({ text: '  ❌ No response from engine - check Python environment', type: 'step_fail' })
      db.saveAutoRunRecord({ id: rid, status: 'aborted', startedAt: now, endedAt: new Date().toISOString() }).catch(() => {})
      cleanupRun()
      showToast('Engine not responding', false)
    }
  }, 10000)
}

function cleanupRun() {
  const runId = currentRunId.value
  running.value = false
  if (runId) lastRunId.value = runId
  currentRunId.value = null
  if (eventUnlisten) { eventUnlisten(); eventUnlisten = null }
  loadRunRecords()
}

async function stopRun() {
  if (currentRunId.value) await stopAutoRun(currentRunId.value)
  consoleOutput.value.push({ text: '⏹ Run stopped by user', type: 'info' })
  db.saveAutoRunRecord({ id: currentRunId.value!, status: 'aborted', startedAt: new Date().toISOString(), endedAt: new Date().toISOString() }).catch(() => {})
  cleanupRun()
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
function onDocumentClick() {
  tagFilterOpen.value = false
  moduleFilterOpen.value = false
  showDeviceDropdown.value = false
}

function onKeydown(e: KeyboardEvent) {
  if ((e.ctrlKey || e.metaKey) && e.key === 's') {
    e.preventDefault()
    saveCurrentCase()
  }
}

onMounted(async () => {
  await loadCaseList()
  await loadRunRecords()
  await pollDevices()
  devicePollTimer = setInterval(pollDevices, 5000)
  window.addEventListener('keydown', onKeydown)
  document.addEventListener('click', onDocumentClick)
})

onUnmounted(() => {
  if (autoSaveTimer) clearTimeout(autoSaveTimer)
  if (toastTimer) clearTimeout(toastTimer)
  if (eventUnlisten) eventUnlisten()
  if (devicePollTimer) clearInterval(devicePollTimer)
  window.removeEventListener('keydown', onKeydown)
  document.removeEventListener('click', onDocumentClick)
})

watch(editingContent, () => { scheduleAutoSave() })
watch(editingName, () => { scheduleAutoSave() })
watch(editingModule, () => { scheduleAutoSave() })
watch(editingTagsText, () => { scheduleAutoSave() })
watch(searchQuery, () => { currentPage.value = 1 })
watch(moduleFilter, () => { currentPage.value = 1 })
watch(tagFilter, () => { currentPage.value = 1 })
</script>

<style scoped>
.dropdown-enter-active,
.dropdown-leave-active { transition: all 0.15s ease; }
.dropdown-enter-from,
.dropdown-leave-to { opacity: 0; transform: translateY(-6px); }
</style>
