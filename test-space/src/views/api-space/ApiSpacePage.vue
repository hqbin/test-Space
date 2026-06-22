<template>
  <div class="h-screen flex flex-col gap-4 py-4 select-none overflow-hidden">
    <!-- Control Bar -->
    <div class="glass-panel rounded-xl px-5 py-3 flex items-center gap-4 flex-wrap">
      <button v-if="!api.running.value" class="glass-button px-5 py-2 rounded-xl flex items-center gap-2" :disabled="api.isStarting.value" @click="handleStart">
        <span class="material-symbols-outlined text-[18px]">play_arrow</span>
        <span class="font-label-md whitespace-nowrap">{{ api.isStarting.value ? 'Starting...' : t('api.start') }}</span>
      </button>
      <button v-else class="glass-button px-5 py-2 rounded-xl flex items-center gap-2 !bg-red-500/20 !border-red-400/30" :disabled="api.isStopping.value" @click="handleStop">
        <span class="material-symbols-outlined text-[18px]">stop</span>
        <span class="font-label-md whitespace-nowrap">{{ api.isStopping.value ? 'Stopping...' : t('api.stop') }}</span>
      </button>

      <div v-if="api.running.value" class="flex items-center gap-2 px-3 py-1.5 bg-green-500/10 border border-green-500/20 rounded-full">
        <span class="w-2 h-2 rounded-full bg-green-500 status-pulse" />
        <span class="text-body-md text-green-600 font-medium">{{ t('api.running') }}</span>
        <span class="text-body-md text-on-surface-variant ml-1">{{ t('api.port') }}: {{ api.currentPort.value }}</span>
      </div>

      <div class="w-px h-6 bg-white/20" />

      <button class="glass-hover rounded-xl px-3 py-2 flex items-center gap-2"
        :class="api.breakpointEnabled.value ? 'glass-active' : ''"
        @click="api.toggleBreakpoint(!api.breakpointEnabled.value, breakpointUrlPattern)">
        <span class="material-symbols-outlined text-[18px]">error_outline</span>
        <span class="font-label-md whitespace-nowrap">{{ t('api.breakpoint') }}</span>
      </button>
      <input v-if="api.running.value" v-model="breakpointUrlPattern" class="glass-input rounded-xl px-3 py-1.5 text-body-md font-mono w-[140px]" placeholder="/api/..." title="仅拦截匹配该路径的请求（留空则拦截全部）" />

      <div class="w-px h-6 bg-white/20" />

      <div class="flex items-center gap-2">
        <div ref="deviceDropdownRef" class="relative">
          <button class="glass-input rounded-xl px-3 py-1.5 text-body-md min-w-[140px] max-w-[200px] flex items-center gap-2 cursor-pointer select-none" @click="openDeviceDropdown">
            <span class="w-2 h-2 rounded-full shrink-0" :class="deviceSerial ? 'bg-green-500' : 'bg-gray-300'" />
            <span class="truncate flex-1 text-left">{{ deviceSerial ? deviceName(deviceSerial) : t('api.selectDevice') }}</span>
            <span class="material-symbols-outlined text-[14px] text-on-surface-variant">expand_more</span>
          </button>
        </div>
        <button class="glass-hover rounded-xl px-2 py-1.5 flex items-center gap-1" @click="refreshDevices" title="Refresh">
          <span class="material-symbols-outlined text-[16px]">refresh</span>
        </button>
      </div>
    </div>

    <!-- Device Dropdown (Teleport to body) -->
    <Teleport to="body">
      <div v-if="showDeviceDropdown" class="fixed inset-0 z-50" @click="showDeviceDropdown = false" />
      <div v-if="showDeviceDropdown" class="fixed z-50 bg-white rounded-lg p-1 max-h-48 overflow-y-auto custom-scrollbar shadow-lg min-w-[200px]"
        :style="{ top: deviceDropdownPos.top + 'px', left: deviceDropdownPos.left + 'px', width: deviceDropdownPos.width + 'px' }">
        <button v-for="d in devices" :key="d.serial"
          class="w-full flex items-center gap-2 px-2 py-1.5 rounded font-caption text-caption text-on-surface hover:bg-gray-100 select-none text-left no-border"
          @mousedown.prevent @click="selectDevice(d)">
          <span class="w-2 h-2 rounded-full shrink-0 bg-green-500" />
          <span class="truncate flex-1">{{ d.model || d.serial }}</span>
          <span class="text-[10px] text-on-surface-variant/50 truncate max-w-[80px]">{{ d.serial }}</span>
        </button>
        <div v-if="devices.length === 0" class="px-2 py-1.5 text-caption text-on-surface-variant/50">{{ t('api.noDevice') }}</div>
      </div>
    </Teleport>

    <!-- Filter Bar -->
    <div class="glass-panel rounded-xl px-5 py-2.5 flex items-center gap-3 flex-wrap">
      <div class="relative flex-1 min-w-[200px]">
        <span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-[16px] text-on-surface-variant">search</span>
        <input v-model="searchQuery" class="glass-input rounded-xl pl-9 pr-3 py-1.5 w-full text-body-md" :placeholder="t('api.filter')" />
      </div>
      <!-- Method Filter Dropdown -->
      <div ref="methodDropdownRef" class="relative">
        <button class="glass-input rounded-xl px-3 py-1.5 text-body-md min-w-[90px] flex items-center gap-2 cursor-pointer select-none" @click="openMethodDropdown">
          <span class="flex-1 text-left">{{ methodFilter || t('api.filterMethod') }}</span>
          <span class="material-symbols-outlined text-[14px] text-on-surface-variant">expand_more</span>
        </button>
      </div>
      <!-- Status Filter Dropdown -->
      <div ref="statusDropdownRef" class="relative">
        <button class="glass-input rounded-xl px-3 py-1.5 text-body-md min-w-[90px] flex items-center gap-2 cursor-pointer select-none" @click="openStatusDropdown">
          <span class="flex-1 text-left">{{ statusFilter || t('api.filterStatus') }}</span>
          <span class="material-symbols-outlined text-[14px] text-on-surface-variant">expand_more</span>
        </button>
      </div>
      <span class="text-caption text-on-surface-variant whitespace-nowrap">{{ t('api.capturedCount', { count: String(filteredList.length) }) }}</span>
      <button v-if="api.capturedRequests.value.length > 0" class="glass-hover rounded-xl px-3 py-1.5 flex items-center gap-1" @click="handleClear">
        <span class="material-symbols-outlined text-[16px]">delete_sweep</span>
        <span class="font-label-md">{{ t('api.clear') }}</span>
      </button>
    </div>

    <!-- Method Dropdown (Teleport to body) -->
    <Teleport to="body">
      <div v-if="showMethodDropdown" class="fixed inset-0 z-50" @click="showMethodDropdown = false" />
      <div v-if="showMethodDropdown" class="fixed z-50 bg-white rounded-lg p-1 max-h-48 overflow-y-auto custom-scrollbar shadow-lg"
        :style="{ top: methodDropdownPos.top + 'px', left: methodDropdownPos.left + 'px', width: methodDropdownPos.width + 'px' }">
        <button class="w-full flex items-center gap-2 px-2 py-1.5 rounded font-caption text-caption text-on-surface hover:bg-gray-100 select-none text-left no-border"
          @mousedown.prevent @click="methodFilter = ''; showMethodDropdown = false">{{ t('api.filterMethod') }}</button>
        <button v-for="m in methodOptions" :key="m"
          class="w-full flex items-center gap-2 px-2 py-1.5 rounded font-caption text-caption text-on-surface hover:bg-gray-100 select-none text-left no-border"
          @mousedown.prevent @click="methodFilter = m; showMethodDropdown = false">
          <span class="font-mono" :class="methodTextClass(m)">{{ m }}</span>
        </button>
      </div>
    </Teleport>

    <!-- Status Dropdown (Teleport to body) -->
    <Teleport to="body">
      <div v-if="showStatusDropdown" class="fixed inset-0 z-50" @click="showStatusDropdown = false" />
      <div v-if="showStatusDropdown" class="fixed z-50 bg-white rounded-lg p-1 max-h-48 overflow-y-auto custom-scrollbar shadow-lg"
        :style="{ top: statusDropdownPos.top + 'px', left: statusDropdownPos.left + 'px', width: statusDropdownPos.width + 'px' }">
        <button class="w-full flex items-center gap-2 px-2 py-1.5 rounded font-caption text-caption text-on-surface hover:bg-gray-100 select-none text-left no-border"
          @mousedown.prevent @click="statusFilter = ''; showStatusDropdown = false">{{ t('api.filterStatus') }}</button>
        <button v-for="s in statusOptions" :key="s"
          class="w-full flex items-center gap-2 px-2 py-1.5 rounded font-caption text-caption text-on-surface hover:bg-gray-100 select-none text-left no-border"
          @mousedown.prevent @click="statusFilter = s; showStatusDropdown = false">
          {{ s }}
        </button>
      </div>
    </Teleport>

    <!-- Main Content: Request List + Detail Panel -->
    <div class="flex-1 flex gap-4 min-h-0 overflow-hidden">
      <!-- Request List -->
      <div class="glass-panel rounded-xl w-[480px] min-w-[400px] flex flex-col overflow-hidden">
        <div class="flex-1 overflow-y-auto custom-scrollbar p-2">
          <div v-if="filteredList.length === 0" class="flex flex-col items-center justify-center h-full text-on-surface-variant gap-2">
            <span class="material-symbols-outlined text-[48px] opacity-40">dns</span>
            <span class="text-body-md">{{ t('api.noRequests') }}</span>
          </div>
          <div v-for="req in filteredList" :key="req.id"
            class="rounded-xl px-3 py-2.5 mb-1 cursor-pointer transition-all select-none"
            :class="selectedRequest?.id === req.id ? 'glass-card-active' : 'glass-hover'"
            @click="selectedRequest = req">
            <div class="flex items-center gap-2 mb-1">
              <span class="font-mono text-caption px-1.5 py-0.5 rounded-md font-semibold whitespace-nowrap"
                :class="methodClass(req.method)">{{ req.method }}</span>
              <span v-if="req.response_status_code" class="font-mono text-caption px-1.5 py-0.5 rounded-md whitespace-nowrap"
                :class="statusClass(req.response_status_code)">
                {{ req.response_status_code }}
              </span>
              <span v-else class="font-mono text-caption px-1.5 py-0.5 rounded-md bg-amber-500/10 text-amber-600">...</span>
              <span v-if="req.is_https" class="text-[10px] px-1 rounded bg-emerald-500/10 text-emerald-600 font-medium">HTTPS</span>
            </div>
            <div class="text-body-md truncate text-on-surface pl-1">{{ req.path }}</div>
            <div class="flex items-center gap-3 text-caption text-on-surface-variant pl-1 mt-0.5">
              <span>{{ req.host }}</span>
              <span v-if="req.duration !== null">{{ req.duration.toFixed(1) }}ms</span>
              <span v-if="req.response_size > 0">{{ formatSize(req.response_size) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Detail Panel -->
      <div class="glass-panel rounded-xl flex-1 flex flex-col overflow-hidden min-w-0">
        <div v-if="!selectedRequest" class="flex items-center justify-center h-full text-on-surface-variant gap-2">
          <span class="material-symbols-outlined text-[48px] opacity-40">touch_app</span>
          <span class="text-body-md">{{ t('api.detailPanel') }}</span>
        </div>
        <template v-else>
          <!-- Detail Tabs -->
          <div class="flex items-center gap-1 px-4 pt-3 pb-2 border-b border-white/10 flex-shrink-0">
            <button v-for="tab in detailTabs" :key="tab.key"
              class="rounded-lg px-3 py-1.5 text-body-md transition-colors"
              :class="activeDetailTab === tab.key ? 'glass-active font-semibold' : 'text-on-surface-variant glass-hover'"
              @click="activeDetailTab = tab.key">
              {{ tab.label }}
            </button>
            <div class="flex-1" />
            <button class="glass-hover rounded-lg px-2.5 py-1.5 flex items-center gap-1" @click="handleEditRequest">
              <span class="material-symbols-outlined text-[16px]">edit</span>
              <span class="font-label-md">{{ t('api.edit') }}</span>
            </button>
            <button class="glass-hover rounded-lg px-2.5 py-1.5 flex items-center gap-1" :class="{ 'opacity-50 pointer-events-none': api.isReplaying.value }" @click="handleReplay">
              <span class="material-symbols-outlined text-[16px]">replay</span>
              <span class="font-label-md">{{ api.isReplaying.value ? t('api.replaying') : t('api.replay') }}</span>
            </button>
          </div>

          <!-- Detail Content -->
          <div class="flex-1 overflow-y-auto custom-scrollbar p-4">
            <!-- Request Tab -->
            <div v-if="activeDetailTab === 'request'">
              <div class="mb-4">
                <div class="text-label-md font-semibold text-on-surface mb-2">{{ t('api.headers') }}</div>
                <div class="bg-white/5 rounded-xl p-3 font-mono text-caption">
                  <div v-for="h in selectedRequest.request_headers" :key="h[0]" class="mb-0.5">
                    <span class="text-primary">{{ h[0] }}</span>: <span class="text-on-surface">{{ h[1] }}</span>
                  </div>
                </div>
              </div>
              <div v-if="selectedRequest.request_body">
                <div class="text-label-md font-semibold text-on-surface mb-2">{{ t('api.body') }} <span class="text-caption text-on-surface-variant font-normal">({{ formatSize(selectedRequest.request_size) }})</span></div>
                <pre class="bg-[#1a1c2e]/80 rounded-xl p-3 font-mono text-caption text-on-surface overflow-x-auto whitespace-pre-wrap max-h-[400px] custom-scrollbar"><code>{{ tryFormatJson(selectedRequest.request_body) }}</code></pre>
              </div>
            </div>

            <!-- Response Tab -->
            <div v-if="activeDetailTab === 'response'">
              <div v-if="!selectedRequest.response_status_code" class="flex items-center justify-center h-32 text-on-surface-variant">
                <span>{{ t('api.noRequests') }}</span>
              </div>
              <template v-else>
                <div class="flex items-center gap-3 mb-4">
                  <span class="font-mono text-headline-md font-bold" :class="statusTextClass(selectedRequest.response_status_code)">
                    {{ selectedRequest.response_status_code }} {{ selectedRequest.response_status_text }}
                  </span>
                  <span class="text-caption text-on-surface-variant">{{ selectedRequest.duration?.toFixed(1) }}ms</span>
                  <span class="text-caption text-on-surface-variant">{{ formatSize(selectedRequest.response_size) }}</span>
                </div>
                <div class="mb-4">
                  <div class="text-label-md font-semibold text-on-surface mb-2">{{ t('api.resHeaders') }}</div>
                  <div class="bg-white/5 rounded-xl p-3 font-mono text-caption">
                    <div v-for="h in selectedRequest.response_headers" :key="h[0]" class="mb-0.5">
                      <span class="text-secondary">{{ h[0] }}</span>: <span class="text-on-surface">{{ h[1] }}</span>
                    </div>
                  </div>
                </div>
                <div v-if="selectedRequest.response_body">
                  <div class="text-label-md font-semibold text-on-surface mb-2">{{ t('api.resBody') }} <span class="text-caption text-on-surface-variant font-normal">({{ formatSize(selectedRequest.response_size) }})</span></div>
                  <pre class="bg-[#1a1c2e]/80 rounded-xl p-3 font-mono text-caption text-on-surface overflow-x-auto whitespace-pre-wrap max-h-[400px] custom-scrollbar"><code>{{ tryFormatJson(selectedRequest.response_body) }}</code></pre>
                </div>
              </template>
            </div>

            <!-- Raw Tab -->
            <div v-if="activeDetailTab === 'raw'">
              <div class="text-label-md font-semibold text-on-surface mb-2">{{ selectedRequest.method }} {{ selectedRequest.url }}</div>
              <pre class="bg-[#1a1c2e]/80 rounded-xl p-3 font-mono text-caption text-on-surface overflow-x-auto whitespace-pre-wrap max-h-[600px] custom-scrollbar"><code>{{ rawContent }}</code></pre>
            </div>
          </div>
        </template>
      </div>
    </div>

    <!-- Rewrite Rules Panel -->
    <div class="glass-panel rounded-xl">
      <div class="flex items-center justify-between px-5 py-2.5 cursor-pointer select-none" @click="showRules = !showRules">
        <div class="flex items-center gap-2">
          <span class="material-symbols-outlined text-[18px] text-on-surface-variant">rule</span>
          <span class="font-label-md font-semibold">{{ t('api.rules') }}</span>
          <span v-if="localRules.length > 0" class="text-caption text-on-surface-variant">({{ localRules.filter(r => r.enabled).length }}/{{ localRules.length }})</span>
        </div>
        <div class="flex items-center gap-2">
          <button class="glass-hover rounded-lg px-2.5 py-1 flex items-center gap-1" @click.stop="showRuleEditor = true">
            <span class="material-symbols-outlined text-[14px]">add</span>
            <span class="font-label-md">{{ t('api.addRule') }}</span>
          </button>
          <span class="material-symbols-outlined text-[18px] text-on-surface-variant transition-transform" :class="{ 'rotate-180': showRules }">expand_more</span>
        </div>
      </div>
      <div v-show="showRules" class="px-5 pb-3 space-y-1.5 max-h-[120px] overflow-y-auto custom-scrollbar">
        <div v-if="localRules.length === 0" class="text-caption text-on-surface-variant py-2 text-center">{{ t('api.noRules') }}</div>
        <div v-for="rule in localRules" :key="rule.id" class="flex items-center gap-2 bg-white/5 rounded-lg px-3 py-1.5">
          <button class="text-[16px]" :class="rule.enabled ? 'text-green-500' : 'text-on-surface-variant'" @click="toggleRule(rule)">
            <span class="material-symbols-outlined">{{ rule.enabled ? 'toggle_on' : 'toggle_off' }}</span>
          </button>
          <span class="font-mono text-caption flex-1 truncate">{{ rule.name }} — <span class="text-on-surface-variant">{{ rule.url_pattern }}</span></span>
          <button class="glass-hover rounded-lg p-1 text-on-surface-variant" @click="editRule(rule)">
            <span class="material-symbols-outlined text-[14px]">edit</span>
          </button>
          <button class="glass-hover rounded-lg p-1 text-on-surface-variant" @click="deleteRule(rule.id)">
            <span class="material-symbols-outlined text-[14px]">close</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Debug Logs Panel -->
    <div class="glass-panel rounded-xl">
      <div class="flex items-center justify-between px-5 py-2.5 cursor-pointer select-none" @click="showDebugLogs = !showDebugLogs">
        <div class="flex items-center gap-2">
          <span class="material-symbols-outlined text-[18px] text-on-surface-variant">bug_report</span>
          <span class="font-label-md font-semibold">{{ t('api.debugLogs') }}</span>
          <span v-if="api.debugLogs.value.length > 0" class="text-caption text-on-surface-variant">({{ api.debugLogs.value.length }})</span>
        </div>
        <div class="flex items-center gap-2">
          <button class="glass-hover rounded-lg px-2.5 py-1 flex items-center gap-1" @click.stop="api.debugLogs.value = []">
            <span class="font-label-md">{{ t('api.clear') }}</span>
          </button>
          <span class="material-symbols-outlined text-[18px] text-on-surface-variant transition-transform" :class="{ 'rotate-180': showDebugLogs }">expand_more</span>
        </div>
      </div>
      <div v-show="showDebugLogs" class="px-5 pb-3 max-h-[150px] overflow-y-auto custom-scrollbar">
        <div v-if="api.debugLogs.value.length === 0" class="text-caption text-on-surface-variant py-2 text-center">{{ t('api.noDebugLogs') }}</div>
        <pre v-for="(log, i) in api.debugLogs.value" :key="i" class="font-mono text-caption text-on-surface py-0.5 border-b border-white/5 last:border-0">{{ log }}</pre>
      </div>
    </div>

    <!-- Rule Editor Dialog -->
    <Teleport to="body">
      <div v-if="showRuleEditor" class="fixed inset-0 z-[100] flex items-center justify-center bg-black/20 backdrop-blur-sm" @click.self="showRuleEditor = false">
        <div class="glass-panel rounded-2xl p-6 w-[500px] max-h-[80vh] overflow-y-auto" @click.stop>
          <div class="text-headline-md font-semibold mb-4">{{ editingRule ? t('api.editRule') : t('api.addRule') }}</div>
          <div class="space-y-3">
            <div>
              <label class="text-label-md text-on-surface-variant block mb-1">{{ t('api.ruleName') }}</label>
              <input v-model="ruleForm.name" class="glass-input rounded-xl px-3 py-2 w-full text-body-md" />
            </div>
            <div>
              <label class="text-label-md text-on-surface-variant block mb-1">{{ t('api.rulePattern') }}</label>
              <input v-model="ruleForm.url_pattern" class="glass-input rounded-xl px-3 py-2 w-full text-body-md font-mono" placeholder="/api/..." />
            </div>
            <div class="flex gap-3">
              <div class="flex-1">
                <label class="text-label-md text-on-surface-variant block mb-1">{{ t('api.filterMethod') }}</label>
                <select v-model="ruleForm.action_type" class="glass-input rounded-xl px-3 py-2 w-full text-body-md">
                  <option value="modify_request_header">Modify Request Header</option>
                  <option value="modify_request_body">Modify Request Body</option>
                  <option value="modify_response_header">Modify Response Header</option>
                  <option value="modify_response_body">Modify Response Body</option>
                  <option value="drop">Drop Request</option>
                </select>
              </div>
            </div>
            <div class="flex gap-3">
              <div class="flex-1">
                <label class="text-label-md text-on-surface-variant block mb-1">Header Name</label>
                <input v-model="ruleForm.header_name" class="glass-input rounded-xl px-3 py-2 w-full text-body-md font-mono" placeholder="e.g. Authorization" />
              </div>
              <div class="flex-1">
                <label class="text-label-md text-on-surface-variant block mb-1">Header Value</label>
                <input v-model="ruleForm.header_value" class="glass-input rounded-xl px-3 py-2 w-full text-body-md" placeholder="new value" />
              </div>
            </div>
            <div>
              <label class="text-label-md text-on-surface-variant block mb-1">Body Search</label>
              <input v-model="ruleForm.body_search" class="glass-input rounded-xl px-3 py-2 w-full text-body-md font-mono" placeholder="text to find" />
            </div>
            <div>
              <label class="text-label-md text-on-surface-variant block mb-1">Body Replace</label>
              <input v-model="ruleForm.body_replace" class="glass-input rounded-xl px-3 py-2 w-full text-body-md" placeholder="replacement text" />
            </div>
          </div>
          <div class="flex justify-end gap-3 mt-5">
            <button class="glass-hover rounded-xl px-4 py-2" @click="showRuleEditor = false">{{ t('settings.cancel') }}</button>
            <button class="glass-button rounded-xl px-4 py-2" @click="saveRule">{{ t('settings.confirm') }}</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Breakpoint Edit Dialog -->
    <Teleport to="body">
      <div v-if="showBreakpointEditor" class="fixed inset-0 z-[100] flex items-center justify-center bg-black/20 backdrop-blur-sm" @click.self="showBreakpointEditor = false">
        <div class="glass-panel rounded-2xl p-6 w-[700px] max-h-[85vh] overflow-y-auto" @click.stop>
          <div class="text-headline-md font-semibold mb-4">{{ breakpointPhase === 'request' ? 'Edit Request' : 'Edit Response' }}</div>
          <div class="space-y-3 mb-4">
            <div>
              <label class="text-label-md text-on-surface-variant block mb-1">{{ t('api.headers') }}</label>
              <textarea v-model="breakpointHeaders" class="glass-input rounded-xl px-3 py-2 w-full text-body-md font-mono" rows="4" placeholder="key: value&#10;key2: value2" />
            </div>
            <div>
              <label class="text-label-md text-on-surface-variant block mb-1">{{ t('api.body') }}</label>
              <textarea v-model="breakpointBody" class="glass-input rounded-xl px-3 py-2 w-full text-body-md font-mono" rows="8" placeholder="Request/Response body" />
            </div>
          </div>
          <div class="flex justify-end gap-3">
            <button class="glass-hover rounded-xl px-4 py-2" @click="breakpointAction('forward')">
              <span class="font-label-md">{{ t('api.forward') }}</span>
            </button>
            <button class="glass-hover rounded-xl px-4 py-2 !bg-red-500/10 !border-red-400/30" @click="breakpointAction('drop')">
              <span class="font-label-md">{{ t('api.drop') }}</span>
            </button>
            <button class="glass-button rounded-xl px-4 py-2" @click="breakpointAction('modify')">
              <span class="font-label-md">{{ t('api.modifyAndForward') }}</span>
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Result Dialog -->
    <Teleport to="body">
      <div v-if="resultDialog.show" class="fixed inset-0 z-[100] flex items-center justify-center bg-black/20 backdrop-blur-sm" @click.self="resultDialog.show = false">
        <div class="glass-panel rounded-2xl p-6 w-[600px] max-h-[70vh] overflow-y-auto" @click.stop>
          <div class="text-headline-md font-semibold mb-2">{{ resultDialog.title }}</div>
          <pre class="text-body-md text-on-surface whitespace-pre-wrap font-mono text-caption bg-white/5 rounded-xl p-3 max-h-[400px] overflow-y-auto custom-scrollbar">{{ resultDialog.message }}</pre>
          <div class="flex justify-end mt-4">
            <button class="glass-button rounded-xl px-4 py-2" @click="resultDialog.show = false">{{ t('settings.confirm') }}</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from "vue"
import { invoke } from "@tauri-apps/api/core"
import { useI18n } from "@/composables/useI18n"
import { useApiProxy } from "@/composables/useApiProxy"
import type { ApiCapturedRequest, ApiRewriteRule } from "@/types"

const { t } = useI18n()
const api = useApiProxy()

const searchQuery = ref("")
const methodFilter = ref("")
const statusFilter = ref("")
const selectedRequest = ref<ApiCapturedRequest | null>(null)
const activeDetailTab = ref("request")
const showRules = ref(false)
const showRuleEditor = ref(false)
const editingRule = ref<ApiRewriteRule | null>(null)
const showBreakpointEditor = ref(false)
const breakpointPhase = ref<"request" | "response">("request")
const breakpointRequestId = ref("")
const breakpointHeaders = ref("")
const breakpointBody = ref("")
const breakpointUrlPattern = ref("")
const showDebugLogs = ref(false)

const ruleForm = ref({
  name: "", url_pattern: "", action_type: "modify_request_header",
  header_name: "", header_value: "", body_search: "", body_replace: "",
})

const localRules = ref<ApiRewriteRule[]>([])

interface DialogState { show: boolean; title: string; message: string }
const resultDialog = ref<DialogState>({ show: false, title: "", message: "" })

const devices = ref<{ serial: string; model: string }[]>([])
const deviceSerial = ref("")

const showDeviceDropdown = ref(false)
const deviceDropdownPos = ref({ top: 0, left: 0, width: 0 })
const deviceDropdownRef = ref<HTMLDivElement | null>(null)
function openDeviceDropdown() {
  const el = deviceDropdownRef.value
  if (!el) return
  const r = el.getBoundingClientRect()
  deviceDropdownPos.value = { top: r.bottom + 4, left: r.left, width: r.width }
  showDeviceDropdown.value = true
}
function selectDevice(d: { serial: string; model: string }) {
  deviceSerial.value = d.serial
  showDeviceDropdown.value = false
}
function deviceName(serial: string) {
  const d = devices.value.find(x => x.serial === serial)
  return d ? (d.model || d.serial) : serial
}

const showMethodDropdown = ref(false)
const showStatusDropdown = ref(false)
const methodDropdownRef = ref<HTMLDivElement | null>(null)
const statusDropdownRef = ref<HTMLDivElement | null>(null)
const methodDropdownPos = ref({ top: 0, left: 0, width: 0 })
const statusDropdownPos = ref({ top: 0, left: 0, width: 0 })
const methodOptions = ["GET", "POST", "PUT", "DELETE", "PATCH"]
const statusOptions = ["2xx", "3xx", "4xx", "5xx"]

function openMethodDropdown() {
  const el = methodDropdownRef.value
  if (!el) return
  const r = el.getBoundingClientRect()
  methodDropdownPos.value = { top: r.bottom + 4, left: r.left, width: r.width }
  showMethodDropdown.value = true
}
function openStatusDropdown() {
  const el = statusDropdownRef.value
  if (!el) return
  const r = el.getBoundingClientRect()
  statusDropdownPos.value = { top: r.bottom + 4, left: r.left, width: r.width }
  showStatusDropdown.value = true
}

async function refreshDevices() {
  try {
    const list = await invoke<{ serial: string; model: string }[]>("adb_list_devices")
    devices.value = list
    if (list.length > 0 && !deviceSerial.value) {
      deviceSerial.value = list[0].serial
    }
  } catch { /* no adb or no devices */ }
}

const detailTabs = computed(() => [
  { key: "request", label: t("api.requestTab") },
  { key: "response", label: t("api.responseTab") },
  { key: "raw", label: t("api.rawTab") },
])

const filteredList = computed(() => {
  let list = api.capturedRequests.value
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    list = list.filter(r => r.url.toLowerCase().includes(q) || r.host.toLowerCase().includes(q) || r.path.toLowerCase().includes(q))
  }
  if (methodFilter.value) {
    list = list.filter(r => r.method === methodFilter.value)
  }
  if (statusFilter.value) {
    const code = parseInt(statusFilter.value)
    list = list.filter(r => r.response_status_code !== null && Math.floor(r.response_status_code / 100) === code / 100)
  }
  return list
})

const rawContent = computed(() => {
  if (!selectedRequest.value) return ""
  const req = selectedRequest.value
  let out = `${req.method} ${req.url} HTTP/1.1\n`
  for (const h of req.request_headers) out += `${h[0]}: ${h[1]}\n`
  if (req.request_body) out += `\n${req.request_body}\n`
  if (req.response_status_code) {
    out += `\n--- Response ---\nHTTP/1.1 ${req.response_status_code} ${req.response_status_text}\n`
    if (req.response_headers) for (const h of req.response_headers) out += `${h[0]}: ${h[1]}\n`
    if (req.response_body) out += `\n${req.response_body}\n`
  }
  return out
})

function methodClass(method: string): string {
  const map: Record<string, string> = {
    GET: "bg-blue-500/10 text-blue-600",
    POST: "bg-emerald-500/10 text-emerald-600",
    PUT: "bg-orange-500/10 text-orange-600",
    DELETE: "bg-red-500/10 text-red-600",
    PATCH: "bg-purple-500/10 text-purple-600",
  }
  return map[method] || "bg-gray-500/10 text-gray-600"
}

function methodTextClass(method: string): string {
  const map: Record<string, string> = {
    GET: "text-blue-600",
    POST: "text-emerald-600",
    PUT: "text-orange-600",
    DELETE: "text-red-600",
    PATCH: "text-purple-600",
  }
  return map[method] || "text-gray-600"
}

function statusClass(code: number): string {
  if (code < 200) return "bg-gray-500/10 text-gray-600"
  if (code < 300) return "bg-emerald-500/10 text-emerald-600"
  if (code < 400) return "bg-blue-500/10 text-blue-600"
  if (code < 500) return "bg-amber-500/10 text-amber-600"
  return "bg-red-500/10 text-red-600"
}

function statusTextClass(code: number): string {
  if (code < 300) return "text-emerald-500"
  if (code < 400) return "text-blue-500"
  if (code < 500) return "text-amber-500"
  return "text-red-500"
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes}B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)}MB`
}

function tryFormatJson(str: string): string {
  try {
    const parsed = JSON.parse(str)
    return JSON.stringify(parsed, null, 2)
  } catch {
    return str
  }
}

async function handleStart() {
  try {
    const msg = await api.startProxy(deviceSerial.value || undefined)
    resultDialog.value = { show: true, title: "Proxy Started", message: msg }
  } catch (e: any) {
    resultDialog.value = { show: true, title: "Error", message: String(e) }
  }
}

async function handleStop() {
  try {
    const msg = await api.stopProxy(deviceSerial.value || undefined)
    resultDialog.value = { show: true, title: "Proxy Stopped", message: msg }
  } catch (e: any) {
    resultDialog.value = { show: true, title: "Error", message: String(e) }
  }
}

async function handleClear() {
  await api.clearCaptured()
  selectedRequest.value = null
}

async function handleReplay() {
  if (!selectedRequest.value || api.isReplaying.value) return
  try {
    const result = await api.replay(selectedRequest.value)
    api.capturedRequests.value.unshift(result)
    selectedRequest.value = result
  } catch (e: any) {
    resultDialog.value = { show: true, title: "Replay Error", message: String(e) }
  }
}

function handleEditRequest() {
  if (!selectedRequest.value) return
  const req = selectedRequest.value
  breakpointHeaders.value = req.request_headers.map(h => `${h[0]}: ${h[1]}`).join("\n")
  breakpointBody.value = req.request_body || ""
  breakpointRequestId.value = req.id
  breakpointPhase.value = "request"
  showBreakpointEditor.value = true
}

async function breakpointAction(action: string) {
  showBreakpointEditor.value = false
  const actionData: Record<string, any> = { type: "forward" }
  if (action === "drop") {
    actionData.type = "drop"
  } else if (action === "modify") {
    actionData.type = "modify"
    const headers: Record<string, string> = {}
    breakpointHeaders.value.split("\n").forEach(line => {
      const idx = line.indexOf(":")
      if (idx > 0) headers[line.slice(0, idx).trim()] = line.slice(idx + 1).trim()
    })
    if (Object.keys(headers).length > 0) actionData.headers = headers
    if (breakpointBody.value) actionData.body = breakpointBody.value
  }

  // Continue breakpoint or just add to captured
  if (selectedRequest.value) {
    const reqId = breakpointPhase.value === "request" ? breakpointRequestId.value : `${breakpointRequestId.value}_resp`
    try {
      await api.continueRequest(reqId, actionData)
    } catch { /* maybe not needed */ }
  }
}

function toggleRule(rule: ApiRewriteRule) {
  rule.enabled = !rule.enabled
  api.updateRule(rule)
}

function editRule(rule: ApiRewriteRule) {
  editingRule.value = rule
  ruleForm.value = {
    name: rule.name,
    url_pattern: rule.url_pattern,
    action_type: rule.action_type,
    header_name: rule.header_name || "",
    header_value: rule.header_value || "",
    body_search: rule.body_search || "",
    body_replace: rule.body_replace || "",
  }
  showRuleEditor.value = true
}

function deleteRule(ruleId: string) {
  api.removeRule(ruleId)
  localRules.value = localRules.value.filter(r => r.id !== ruleId)
}

function saveRule() {
  const rule: ApiRewriteRule = {
    id: editingRule.value?.id || crypto.randomUUID(),
    name: ruleForm.value.name,
    enabled: true,
    url_pattern: ruleForm.value.url_pattern,
    match_type: "contains",
    action_type: ruleForm.value.action_type as ApiRewriteRule["action_type"],
    header_name: ruleForm.value.header_name || null,
    header_value: ruleForm.value.header_value || null,
    body_search: ruleForm.value.body_search || null,
    body_replace: ruleForm.value.body_replace || null,
    redirect_url: null,
    status_code: null,
  }
  if (editingRule.value) {
    api.updateRule(rule)
    const idx = localRules.value.findIndex(r => r.id === rule.id)
    if (idx !== -1) localRules.value[idx] = rule
  } else {
    api.addRule(rule)
    localRules.value.push(rule)
  }
  showRuleEditor.value = false
  editingRule.value = null
  ruleForm.value = { name: "", url_pattern: "", action_type: "modify_request_header", header_name: "", header_value: "", body_search: "", body_replace: "" }
}

onMounted(async () => {
  await api.init()
  await api.getCaptured()
  await refreshDevices()
})

// Auto-expand debug panel when logs arrive
watch(() => api.debugLogs.value.length, (n, o) => {
  if (n > o) showDebugLogs.value = true
})

onUnmounted(() => {
  api.cleanup()
})
</script>

<style scoped>
.glass-panel {
  backdrop-filter: blur(60px);
  -webkit-backdrop-filter: blur(60px);
}
</style>
