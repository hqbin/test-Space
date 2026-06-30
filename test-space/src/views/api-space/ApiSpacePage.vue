<template>
  <div class="flex flex-col flex-1 min-h-0 gap-4 pt-0 pb-4 select-none overflow-hidden">
    <!-- Rewrite Rules Dropdown (below control bar) -->
    <div v-if="showRules" class="glass-panel rounded-xl px-5 py-3">
      <div class="flex items-center justify-between mb-2">
        <span class="font-label-md font-semibold">{{ t('api.rules') }}</span>
        <button class="glass-button px-2.5 py-1 rounded-full font-caption text-caption font-normal flex items-center gap-1 select-none" @click="showRuleEditor = true">
          <span class="material-symbols-outlined text-[14px]">add</span>
          {{ t('api.addRule') }}
        </button>
      </div>
      <div class="space-y-1 max-h-[120px] overflow-y-auto custom-scrollbar">
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

    <!-- Control Bar -->
    <div class="glass-panel rounded-xl px-4 py-2 flex items-center gap-3 flex-wrap">
      <button v-if="!api.running.value" class="glass-button px-3 py-1.5 rounded-full font-caption text-caption font-normal flex items-center gap-1.5 select-none" :disabled="api.isStarting.value" @click="handleStart">
        <span class="material-symbols-outlined text-[16px]">play_arrow</span>
        <span class="whitespace-nowrap">{{ api.isStarting.value ? 'Starting...' : t('api.start') }}</span>
      </button>
      <button v-else class="glass-button px-3 py-1.5 rounded-full font-caption text-caption font-normal flex items-center gap-1.5 select-none" :disabled="api.isStopping.value" @click="handleStop">
        <span class="material-symbols-outlined text-[16px]">stop</span>
        <span class="whitespace-nowrap">{{ api.isStopping.value ? 'Stopping...' : t('api.stop') }}</span>
      </button>

      <div v-if="api.running.value" class="flex items-center gap-2 px-3 py-1.5 bg-green-500/10 border border-green-500/20 rounded-full">
        <span class="w-2 h-2 rounded-full bg-green-500 status-pulse" />
        <span class="text-body-md text-green-600 font-medium">{{ t('api.running') }}</span>
        <span class="text-body-md text-on-surface-variant ml-1">{{ t('api.port') }}: {{ api.currentPort.value }}</span>
      </div>

      <div class="w-px h-6 bg-white/20" />

      <button class="glass-button px-3 py-1.5 rounded-full font-caption text-caption font-normal flex items-center gap-1.5 transition-all relative select-none"
        :class="api.breakpointEnabled.value ? 'glass-active' : ''"
        @click="api.toggleBreakpoint(!api.breakpointEnabled.value, breakpointUrlPattern)">
        <span class="material-symbols-outlined text-[16px]">error_outline</span>
        <span class="whitespace-nowrap">{{ t('api.breakpoint') }}</span>
        <span v-if="api.pendingCount.value > 0"
          class="absolute -top-1 -right-1 min-w-[18px] h-[18px] flex items-center justify-center rounded-full bg-red-500 text-white text-[10px] font-bold px-1">
          {{ api.pendingCount.value }}
        </span>
      </button>
      <input v-if="api.running.value" v-model="breakpointUrlPattern" class="bg-white/50 border border-outline-variant/60 rounded-xl px-3 py-1.5 text-body-md font-mono w-[140px] focus:ring-2 focus:ring-secondary/30 focus:border-secondary transition-all select-text" placeholder="/api/..." title="输入 URL 路径，仅拦截匹配的请求（留空则拦截全部）" />

      <div class="w-px h-6 bg-white/20" />

      <div class="flex items-center gap-2">
        <div ref="deviceDropdownRef" class="relative">
          <button class="bg-white/50 border border-outline-variant/60 rounded-xl px-3 py-1.5 text-body-md min-w-[140px] max-w-[200px] flex items-center gap-2 cursor-pointer select-none hover:bg-white/70 transition-all" @click="openDeviceDropdown">
            <span class="w-2 h-2 rounded-full shrink-0" :class="deviceSerial ? 'bg-green-500' : 'bg-gray-300'" />
            <span class="truncate flex-1 text-left">{{ deviceSerial ? deviceName(deviceSerial) : t('api.selectDevice') }}</span>
            <span class="material-symbols-outlined text-[14px] text-on-surface-variant">expand_more</span>
          </button>
        </div>
        <button class="glass-button px-2 py-1 rounded-full font-caption text-caption font-normal flex items-center gap-1 select-none" @click="refreshDevices" title="Refresh">
          <span class="material-symbols-outlined text-[14px]">refresh</span>
        </button>
      </div>

      <div class="w-px h-6 bg-white/20" />

      <button class="glass-button px-3 py-1.5 rounded-full font-caption text-caption font-normal flex items-center gap-1.5 transition-all select-none"
        :class="showRules ? 'glass-active' : ''"
        @click="showRules = !showRules">
        <span class="material-symbols-outlined text-[16px]">rule</span>
        <span class="whitespace-nowrap">Rules</span>
        <span v-if="localRules.length > 0" class="text-caption text-on-surface-variant bg-white/10 rounded-full px-1.5 py-0.5">{{ localRules.filter(r => r.enabled).length }}/{{ localRules.length }}</span>
      </button>
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
      <div ref="searchInputRef" class="relative flex-1 min-w-[200px]">
        <span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-[16px] text-on-surface-variant">search</span>
        <input v-model="searchQuery" class="bg-white/50 border border-outline-variant/60 rounded-xl pl-9 pr-3 py-1.5 w-full text-body-md focus:ring-2 focus:ring-secondary/30 focus:border-secondary transition-all select-text"
          :placeholder="t('api.filter')"
          @focus="onSearchFocus"
          @keydown.enter="addSearchQuery(searchQuery)" />
      </div>
      <Teleport to="body">
        <div v-if="showSearchHistory && searchHistory.length > 0" class="fixed inset-0 z-40" @click="showSearchHistory = false"></div>
        <div v-if="showSearchHistory && searchHistory.length > 0"
          class="fixed z-50 bg-white border shadow-lg rounded-lg max-h-48 overflow-y-auto"
          :style="{ top: searchDropdownPos.top + 'px', left: searchDropdownPos.left + 'px', width: searchDropdownPos.width + 'px' }">
          <button v-for="q in searchHistory" :key="q"
            class="w-full text-left px-3 py-1.5 text-caption text-on-surface hover:bg-gray-100 truncate whitespace-nowrap"
            @mousedown.prevent @click="selectSearchHistory(q)">
            {{ q }}
          </button>
        </div>
      </Teleport>

      <span class="text-caption text-on-surface-variant whitespace-nowrap">{{ t('api.capturedCount', { count: String(filteredList.length) }) }}</span>
      <button v-if="api.capturedRequests.value.length > 0" class="glass-button px-3 py-1.5 rounded-full font-caption text-caption font-normal flex items-center gap-1.5 select-none" @click="handleClear">
        <span class="material-symbols-outlined text-[16px]">delete_sweep</span>
        {{ t('api.clear') }}
      </button>
    </div>

<!-- (method/status filters removed) -->

    <!-- Main Content: Request List + Detail Panel -->
    <div class="flex-1 flex gap-4 min-h-0">
      <!-- Request List -->
      <div class="glass-panel rounded-xl flex-[0_0_40%] min-w-[360px] max-w-[50%] flex flex-col overflow-hidden shadow-md">
        <div class="flex-1 overflow-y-auto custom-scrollbar p-2">
          <div v-if="filteredList.length === 0" class="flex flex-col items-center justify-center h-full text-on-surface-variant gap-2">
            <span class="material-symbols-outlined text-[48px] opacity-40">dns</span>
            <span class="text-body-md">{{ t('api.noRequests') }}</span>
          </div>
          <div v-for="req in filteredList" :key="req.id"
            class="rounded-xl px-3 py-2.5 mb-1 cursor-pointer transition-all select-none api-request-item"
            :class="{
              'glass-card-active': selectedRequest?.id === req.id,
              'glass-hover': selectedRequest?.id !== req.id,
              'ring-2 ring-red-400/50': api.pendingBreakpoints.value.has(req.id) || api.pendingBreakpoints.value.has(req.id + '_resp')
            }"
            @click="handleRequestClick(req)">
            <div class="flex items-center gap-2 mb-1">
              <span v-if="api.pendingBreakpoints.value.has(req.id) || api.pendingBreakpoints.value.has(req.id + '_resp')"
                class="font-mono text-[10px] px-1.5 py-0.5 rounded-md font-bold bg-red-500/15 text-red-600">
                ⏸ BP
              </span>
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
      <div class="glass-panel rounded-xl flex-1 flex flex-col overflow-hidden min-w-0 shadow-md">
        <div v-if="!selectedRequest" class="flex items-center justify-center h-full text-on-surface-variant gap-2 select-text">
          <span class="material-symbols-outlined text-[48px] opacity-40">touch_app</span>
          <span class="text-body-md">{{ t('api.detailPanel') }}</span>
        </div>
        <template v-else>
          <!-- Detail Tabs -->
          <div class="flex items-center gap-1 px-4 pt-3 pb-2 border-b border-white/10 flex-shrink-0">
            <button v-for="tab in detailTabs" :key="tab.key"
              class="rounded-lg px-3 py-1.5 text-body-md transition-all"
              :class="activeDetailTab === tab.key ? 'glass-active' : 'glass-button'"
              @click="activeDetailTab = tab.key">
              {{ tab.label }}
            </button>
            <div class="flex-1" />
            <button class="glass-button px-2.5 py-1 rounded-full font-caption text-caption font-normal flex items-center gap-1 select-none" @click="handleEditRequest">
              <span class="material-symbols-outlined text-[14px]">edit</span>
              {{ t('api.edit') }}
            </button>
            <button class="glass-button px-2.5 py-1 rounded-full font-caption text-caption font-normal flex items-center gap-1 select-none" :class="{ 'opacity-50 pointer-events-none': api.isReplaying.value }" @click="handleReplay">
              <span class="material-symbols-outlined text-[14px]">replay</span>
              {{ api.isReplaying.value ? t('api.replaying') : t('api.replay') }}
            </button>
          </div>

          <!-- Detail Content -->
          <div class="flex-1 overflow-y-auto custom-scrollbar p-4 select-text">
            <!-- Request Tab -->
            <div v-if="activeDetailTab === 'request'">
              <div class="mb-3 p-3 bg-white/[0.06] rounded-xl font-mono text-caption text-on-surface break-all">
                {{ selectedRequest.method }} {{ selectedRequest.url }}
              </div>
              <div class="mb-4">
                <div class="flex items-center justify-between text-label-md font-semibold text-on-surface mb-2">
                  <span>{{ t('api.headers') }}</span>
                  <button class="glass-button px-2 py-0.5 rounded-full font-caption text-caption font-normal flex items-center gap-1 select-none" @click="copyText(formatHeaders(selectedRequest.request_headers))">
                    <span class="material-symbols-outlined text-[14px]">content_copy</span> Copy
                  </button>
                </div>
                <div class="bg-white/[0.06] rounded-xl p-3 font-mono text-caption">
                  <div v-for="h in selectedRequest.request_headers" :key="h[0]" class="mb-0.5">
                    <span class="text-primary">{{ h[0] }}</span>: <span class="text-on-surface">{{ h[1] }}</span>
                  </div>
                </div>
              </div>
              <div v-if="selectedRequest.request_body">
                <div class="flex items-center justify-between text-label-md font-semibold text-on-surface mb-2">
                  <span>{{ t('api.body') }} <span class="text-caption text-on-surface-variant font-normal">({{ formatSize(selectedRequest.request_size) }})</span>
                    <span v-if="selectedRequest.request_body_is_base64" class="text-caption text-amber-500 font-normal"> [Binary]</span>
                  </span>
                  <button v-if="!selectedRequest.request_body_is_base64" class="glass-button px-2 py-0.5 rounded-full font-caption text-caption font-normal flex items-center gap-1 select-none" @click="copyText(tryFormatJson(selectedRequest.request_body))">
                    <span class="material-symbols-outlined text-[14px]">content_copy</span> Copy
                  </button>
                </div>
                <template v-if="!selectedRequest.request_body_is_base64">
                  <pre class="bg-white/[0.06] rounded-xl p-3 font-mono text-caption text-on-surface overflow-x-auto whitespace-pre-wrap break-all custom-scrollbar"><code>{{ tryFormatJson(selectedRequest.request_body) }}</code></pre>
                </template>
                <template v-else>
                  <div class="bg-white/[0.06] rounded-xl p-3 font-mono text-caption text-on-surface-variant text-center">
                    [Binary request body — {{ formatSize(selectedRequest.request_size) }}]
                  </div>
                </template>
              </div>
            </div>

            <!-- Response Tab -->
            <div v-if="activeDetailTab === 'response'">
              <div v-if="!selectedRequest.response_status_code" class="flex items-center justify-center h-32 text-on-surface-variant">
                <span>{{ t('api.noRequests') }}</span>
              </div>
              <template v-else>
                <div class="flex items-center gap-3 mb-4">
                  <span class="font-mono text-body-md" :class="statusTextClass(selectedRequest.response_status_code)">
                    {{ selectedRequest.response_status_code }} {{ selectedRequest.response_status_text }}
                  </span>
                  <span class="text-caption text-on-surface-variant">{{ selectedRequest.duration?.toFixed(1) }}ms</span>
                  <span class="text-caption text-on-surface-variant">{{ formatSize(selectedRequest.response_size) }}</span>
                  <div class="flex-1" />
                  <button class="glass-button px-2.5 py-1 rounded-full font-caption text-caption font-normal flex items-center gap-1 select-none" @click="openBreakpointEditor(selectedRequest, 'response')">
                    <span class="material-symbols-outlined text-[14px]">edit</span>
                    {{ t('api.edit') }}
                  </button>
                </div>
                <div class="mb-4">
                  <div class="flex items-center justify-between text-label-md font-semibold text-on-surface mb-2">
                    <span>{{ t('api.resHeaders') }}</span>
                    <button class="glass-button px-2 py-0.5 rounded-full font-caption text-caption font-normal flex items-center gap-1 select-none" @click="copyText(formatHeaders(selectedRequest.response_headers ?? []))">
                      <span class="material-symbols-outlined text-[14px]">content_copy</span> Copy
                    </button>
                  </div>
                  <div class="bg-white/[0.06] rounded-xl p-3 font-mono text-caption">
                    <div v-for="h in selectedRequest.response_headers" :key="h[0]" class="mb-0.5">
                      <span class="text-secondary">{{ h[0] }}</span>: <span class="text-on-surface">{{ h[1] }}</span>
                    </div>
                  </div>
                </div>
                <div v-if="selectedRequest.response_body">
                  <div class="flex items-center justify-between text-label-md font-semibold text-on-surface mb-2">
                    <span>{{ t('api.resBody') }} <span class="text-caption text-on-surface-variant font-normal">({{ formatSize(selectedRequest.response_size) }})</span>
                      <span v-if="selectedRequest.response_body_is_base64" class="text-caption text-amber-500 font-normal"> [Binary]</span>
                    </span>
                    <button v-if="!selectedRequest.response_body_is_base64" class="glass-button px-2 py-0.5 rounded-full font-caption text-caption font-normal flex items-center gap-1 select-none" @click="copyText(tryFormatJson(selectedRequest.response_body))">
                      <span class="material-symbols-outlined text-[14px]">content_copy</span> Copy
                    </button>
                  </div>
                  <template v-if="!selectedRequest.response_body_is_base64">
                    <pre class="bg-white/[0.06] rounded-xl p-3 font-mono text-caption text-on-surface overflow-x-auto whitespace-pre-wrap break-all custom-scrollbar"><code>{{ tryFormatJson(selectedRequest.response_body) }}</code></pre>
                  </template>
                  <template v-else-if="responseBodyIsImage">
                    <div class="bg-white/[0.06] rounded-xl p-3 flex items-center justify-center">
                      <img :src="responseBodyImageSrc" class="max-w-full max-h-[400px] object-contain rounded-lg" alt="Response image" />
                    </div>
                  </template>
                  <template v-else-if="responseBodyIsVideo">
                    <div class="bg-white/[0.06] rounded-xl p-3 flex items-center justify-center">
                      <video controls class="max-w-full max-h-[400px] rounded-lg" :src="responseBodyMediaSrc"></video>
                    </div>
                  </template>
                  <template v-else-if="responseBodyIsAudio">
                    <div class="bg-white/[0.06] rounded-xl p-3">
                      <audio controls class="w-full" :src="responseBodyMediaSrc"></audio>
                    </div>
                  </template>
                  <template v-else>
                    <div class="bg-white/[0.06] rounded-xl p-3 font-mono text-caption text-on-surface-variant text-center">
                      [Binary data — {{ formatSize(selectedRequest.response_size) }} — {{ responseContentType || 'unknown' }}]
                    </div>
                  </template>
                </div>
              </template>
            </div>

            <!-- Raw Tab -->
            <div v-if="activeDetailTab === 'raw'">
              <div class="flex justify-end mb-2">
                <button class="glass-button px-2 py-0.5 rounded-full font-caption text-caption font-normal flex items-center gap-1 select-none" @click="copyText(rawContent)">
                  <span class="material-symbols-outlined text-[14px]">content_copy</span> Copy
                </button>
              </div>
              <pre class="bg-white/[0.06] rounded-xl p-3 font-mono text-caption text-on-surface overflow-x-auto whitespace-pre-wrap break-all custom-scrollbar"><code>{{ rawContent }}</code></pre>
            </div>
          </div>
        </template>
      </div>
    </div>



    <!-- Rule Editor Dialog -->
    <Teleport to="body">
      <Transition name="fade">
        <div v-if="showRuleEditor" class="fixed inset-0 z-[100] flex items-center justify-center" @click.self="showRuleEditor = false">
          <div class="absolute inset-0 bg-black/10 backdrop-blur-sm"></div>
          <div class="glass-panel rounded-[2rem] p-6 w-full max-w-md relative z-10 bg-white/90 max-h-[80vh] flex flex-col">
            <div class="flex justify-between items-center mb-4">
              <h3 class="font-label-md text-label-md text-on-surface font-semibold flex items-center gap-1.5 select-none">
                <span class="material-symbols-outlined text-[16px]">rule</span>{{ editingRule ? t('api.editRule') : t('api.addRule') }}
              </h3>
              <button class="glass-button p-1 rounded select-none" @click="showRuleEditor = false">
                <span class="material-symbols-outlined text-[18px]">close</span>
              </button>
            </div>
            <div class="flex flex-col gap-3 overflow-y-auto custom-scrollbar">
              <div>
                <label class="text-label-md text-on-surface-variant block mb-1">{{ t('api.ruleName') }}</label>
                <input v-model="ruleForm.name" class="bg-white/80 border border-outline-variant rounded-lg px-3 py-2 font-caption text-caption text-on-surface font-mono focus:ring-2 focus:ring-secondary/30 w-full select-text" />
              </div>
              <div>
                <label class="text-label-md text-on-surface-variant block mb-1">{{ t('api.rulePattern') }}</label>
                <input v-model="ruleForm.url_pattern" class="bg-white/80 border border-outline-variant rounded-lg px-3 py-2 font-caption text-caption text-on-surface font-mono focus:ring-2 focus:ring-secondary/30 w-full select-text" placeholder="/api/..." />
              </div>
              <div class="flex gap-3">
                <div class="flex-1">
                  <label class="text-label-md text-on-surface-variant block mb-1">匹配方式</label>
                  <select v-model="ruleForm.match_type" class="bg-white/80 border border-outline-variant rounded-lg px-3 py-2 font-caption text-caption text-on-surface w-full select-text">
                    <option value="contains">包含 (contains)</option>
                    <option value="exact">精确 (exact)</option>
                    <option value="prefix">前缀 (prefix)</option>
                    <option value="regex">正则 (regex)</option>
                  </select>
                </div>
                <div class="flex-1">
                  <label class="text-label-md text-on-surface-variant block mb-1">{{ t('api.filterMethod') }}</label>
                  <select v-model="ruleForm.action_type" class="bg-white/80 border border-outline-variant rounded-lg px-3 py-2 font-caption text-caption text-on-surface w-full select-text">
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
                  <input v-model="ruleForm.header_name" class="bg-white/80 border border-outline-variant rounded-lg px-3 py-2 font-caption text-caption text-on-surface font-mono focus:ring-2 focus:ring-secondary/30 w-full select-text" placeholder="e.g. Authorization" />
                </div>
                <div class="flex-1">
                  <label class="text-label-md text-on-surface-variant block mb-1">Header Value</label>
                  <input v-model="ruleForm.header_value" class="bg-white/80 border border-outline-variant rounded-lg px-3 py-2 font-caption text-caption text-on-surface focus:ring-2 focus:ring-secondary/30 w-full select-text" placeholder="new value" />
                </div>
              </div>
              <div>
                <label class="text-label-md text-on-surface-variant block mb-1">Body Search</label>
                <input v-model="ruleForm.body_search" class="bg-white/80 border border-outline-variant rounded-lg px-3 py-2 font-caption text-caption text-on-surface font-mono focus:ring-2 focus:ring-secondary/30 w-full select-text" placeholder="text to find" />
              </div>
              <div>
                <label class="text-label-md text-on-surface-variant block mb-1">Body Replace</label>
                <input v-model="ruleForm.body_replace" class="bg-white/80 border border-outline-variant rounded-lg px-3 py-2 font-caption text-caption text-on-surface focus:ring-2 focus:ring-secondary/30 w-full select-text" placeholder="replacement text" />
              </div>
            </div>
            <div class="flex justify-end gap-3 mt-5 pt-3 border-t border-outline-variant/30">
              <button class="glass-hover rounded-xl px-4 py-2 select-none" @click="showRuleEditor = false">{{ t('settings.cancel') }}</button>
              <button class="glass-button rounded-xl px-4 py-2 select-none" @click="saveRule">{{ t('settings.confirm') }}</button>
            </div>
          </div>
        </div>
      </Transition>
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
              <textarea v-if="!bodyIsBinaryForBreakpoint" v-model="breakpointBody" class="glass-input rounded-xl px-3 py-2 w-full text-body-md font-mono" rows="8" placeholder="Request/Response body" />
              <div v-else class="bg-white/[0.06] rounded-xl p-3 font-mono text-caption text-on-surface-variant text-center">[Binary body — cannot edit in text mode]</div>
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
      <Transition name="fade">
        <div v-if="resultDialog.show" class="fixed inset-0 z-[100] flex items-center justify-center" @click.self="resultDialog.show = false">
          <div class="absolute inset-0 bg-black/10 backdrop-blur-sm"></div>
          <div class="glass-panel rounded-[2rem] p-6 w-full max-w-md relative z-10 bg-white/90 max-h-[80vh] flex flex-col">
            <div class="flex justify-between items-center mb-4">
              <h3 class="font-label-md text-label-md text-on-surface font-semibold flex items-center gap-1.5 select-none">
                <span class="material-symbols-outlined text-[16px]">info</span>{{ resultDialog.title }}
              </h3>
              <button class="glass-button p-1 rounded select-none" @click="resultDialog.show = false">
                <span class="material-symbols-outlined text-[18px]">close</span>
              </button>
            </div>
            <pre class="flex-1 overflow-y-auto text-body-md text-on-surface whitespace-pre-wrap font-mono text-caption bg-white/30 rounded-xl p-3 custom-scrollbar select-text">{{ resultDialog.message }}</pre>
            <div class="flex justify-end mt-4 pt-3 border-t border-outline-variant/30">
              <button class="glass-button rounded-xl px-4 py-2 select-none" @click="resultDialog.show = false">{{ t('settings.confirm') }}</button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from "vue"
import { invoke } from "@tauri-apps/api/core"
import { useI18n } from "@/composables/useI18n"
import { useApiProxy } from "@/composables/useApiProxy"
import type { ApiCapturedRequest, ApiRewriteRule } from "@/types"
import { addInputHistory, getInputHistory } from "@/services/database"

const { t } = useI18n()
const api = useApiProxy()

const searchQuery = ref("")
const searchHistory = ref<string[]>([])
const showSearchHistory = ref(false)
const searchInputRef = ref<HTMLElement | null>(null)
const searchDropdownPos = ref({ top: 0, left: 0, width: 0 })

async function loadSearchHistory() {
  const entries = await getInputHistory('api_search');
  searchHistory.value = entries.map(e => e.value);
}
async function addSearchQuery(q: string) {
  if (!q.trim()) return
  const set = new Set(searchHistory.value)
  set.delete(q.trim())
  searchHistory.value = [q.trim(), ...set].slice(0, 20)
  await addInputHistory('api_search', q.trim())
}
function onSearchFocus() {
  if (searchHistory.value.length > 0 && searchInputRef.value) {
    const r = searchInputRef.value.getBoundingClientRect();
    searchDropdownPos.value = { top: r.bottom + 4, left: r.left, width: r.width };
    showSearchHistory.value = true;
  }
}
function selectSearchHistory(q: string) {
  searchQuery.value = q;
  showSearchHistory.value = false;
}

const selectedRequest = api.selectedRequest
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

const ruleForm = ref({
  name: "", url_pattern: "", match_type: "contains", action_type: "modify_request_header",
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
  return list
})

const rawContent = computed(() => {
  if (!selectedRequest.value) return ""
  const req = selectedRequest.value
  let out = `${req.method} ${req.url} HTTP/1.1\n`
  for (const h of req.request_headers) out += `${h[0]}: ${h[1]}\n`
  if (req.request_body) out += `\n${req.request_body_is_base64 ? '[Binary request body]' : req.request_body}\n`
  if (req.response_status_code) {
    out += `\n--- Response ---\nHTTP/1.1 ${req.response_status_code} ${req.response_status_text}\n`
    if (req.response_headers) for (const h of req.response_headers) out += `${h[0]}: ${h[1]}\n`
    if (req.response_body) out += `\n${req.response_body_is_base64 ? '[Binary response body]' : req.response_body}\n`
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

function findHeader(headers: string[][] | null, name: string): string | null {
  if (!headers) return null
  const lower = name.toLowerCase()
  for (const [key, value] of headers) {
    if (key.toLowerCase() === lower) return value
  }
  return null
}

const responseContentType = computed(() => {
  if (!selectedRequest.value?.response_headers) return null
  return findHeader(selectedRequest.value.response_headers, 'content-type')
})

const responseBodyIsImage = computed(() => {
  const ct = responseContentType.value
  return ct ? ct.startsWith('image/') : false
})

const responseBodyIsVideo = computed(() => {
  const ct = responseContentType.value
  return ct ? ct.startsWith('video/') : false
})

const responseBodyIsAudio = computed(() => {
  const ct = responseContentType.value
  return ct ? ct.startsWith('audio/') : false
})

const responseBodyImageSrc = computed(() => {
  if (!responseBodyIsImage.value || !selectedRequest.value?.response_body_is_base64) return ''
  const ct = responseContentType.value
  return `data:${ct};base64,${selectedRequest.value.response_body}`
})

const responseBodyMediaSrc = computed(() => {
  if (!selectedRequest.value?.response_body_is_base64) return ''
  const ct = responseContentType.value
  if (!ct) return ''
  if (!ct.startsWith('video/') && !ct.startsWith('audio/')) return ''
  return `data:${ct};base64,${selectedRequest.value.response_body}`
})

const bodyIsBinaryForBreakpoint = computed(() => {
  if (!selectedRequest.value) return false
  if (breakpointPhase.value === 'request') return selectedRequest.value.request_body_is_base64
  return selectedRequest.value.response_body_is_base64
})

function tryFormatJson(str: string): string {
  try {
    const parsed = JSON.parse(str)
    return JSON.stringify(parsed, null, 2)
  } catch {
    return str
  }
}

async function copyText(text: string) {
  try {
    await navigator.clipboard.writeText(text)
  } catch { /* fallback */ }
}

function formatHeaders(headers: string[][]): string {
  return headers.map(h => `${h[0]}: ${h[1]}`).join("\n")
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

async function handleRequestClick(req: ApiCapturedRequest) {
  selectedRequest.value = req
  const isPending = api.pendingBreakpoints.value.has(req.id) || api.pendingBreakpoints.value.has(`${req.id}_resp`)
  if (isPending && !showBreakpointEditor.value) {
    const phase = api.pendingBreakpoints.value.has(`${req.id}_resp`) ? "response" : "request"
    openBreakpointEditor(req, phase)
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

function openBreakpointEditor(req: ApiCapturedRequest, phase: "request" | "response") {
  selectedRequest.value = req
  if (phase === "response" && req.response_headers) {
    breakpointHeaders.value = req.response_headers.map(h => `${h[0]}: ${h[1]}`).join("\n")
    breakpointBody.value = req.response_body || ""
  } else {
    breakpointHeaders.value = req.request_headers.map(h => `${h[0]}: ${h[1]}`).join("\n")
    breakpointBody.value = req.request_body || ""
  }
  breakpointRequestId.value = req.id
  breakpointPhase.value = phase
  showBreakpointEditor.value = true
}

function handleEditRequest() {
  if (!selectedRequest.value) return
  openBreakpointEditor(selectedRequest.value, "request")
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

  if (selectedRequest.value) {
    const reqId = breakpointPhase.value === "request" ? breakpointRequestId.value : `${breakpointRequestId.value}_resp`
    try {
      await api.continueRequest(reqId, actionData)
      api.markBreakpointResolved(breakpointRequestId.value)
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
    match_type: rule.match_type,
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
    match_type: ruleForm.value.match_type as ApiRewriteRule["match_type"],
    action_type: ruleForm.value.action_type as ApiRewriteRule["action_type"],
    header_name: ruleForm.value.header_name || null,
    header_value: ruleForm.value.header_value || null,
    body_search: ruleForm.value.body_search || null,
    body_replace: ruleForm.value.body_replace || null,
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
  ruleForm.value = { name: "", url_pattern: "", match_type: "contains", action_type: "modify_request_header", header_name: "", header_value: "", body_search: "", body_replace: "" }
}

watch(() => api.breakpointEvent.value, (evt) => {
  if (evt) {
    api.breakpointEvent.value = null
  }
})

onMounted(async () => {
  await api.init()
  await api.getCaptured()
  localRules.value = [...api.rewriteRules.value]
  await refreshDevices()
  await loadSearchHistory()
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
.api-request-item.glass-hover:hover {
  transform: scale(1.01);
}
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
