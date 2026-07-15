<template>
  <div class="flex flex-col flex-1 min-h-0 gap-4 pt-0 pb-4 select-none overflow-hidden">
    <!-- Top Bar -->
    <div class="glass-panel rounded-xl px-4 py-2 flex items-center gap-3 flex-wrap">
      <button class="glass-button px-3 py-1.5 rounded-full font-caption text-caption font-normal flex items-center gap-1.5 select-none" @click="$emit('back')">
        <span class="material-symbols-outlined text-[16px]">arrow_back</span>
        <span class="whitespace-nowrap">返回抓包</span>
      </button>

      <div class="w-px h-6 bg-white/20" />

      <button class="glass-button px-3 py-1.5 rounded-full font-caption text-caption font-normal flex items-center gap-1.5 select-none" :disabled="test.isGenerating.value" @click="handleGenerate(false)">
        <span class="material-symbols-outlined text-[16px]">auto_fix_high</span>
        <span class="whitespace-nowrap">{{ isSmartGenerating ? '生成中...' : '智能生成用例' }}</span>
      </button>

      <button class="glass-button px-3 py-1.5 rounded-full font-caption text-caption font-normal flex items-center gap-1.5 select-none" :disabled="test.isGenerating.value" @click="handleGenerateAI">
        <span class="material-symbols-outlined text-[16px]">psychology</span>
        <span class="whitespace-nowrap">{{ isAiGenerating ? 'AI生成中...' : 'AI 生成用例' }}</span>
      </button>

      <button class="glass-button px-3 py-1.5 rounded-full font-caption text-caption font-normal flex items-center gap-1.5 select-none" @click="showReportList = true">
        <span class="material-symbols-outlined text-[16px]">assessment</span>
        <span class="whitespace-nowrap">测试报告</span>
        <span v-if="test.reports.value.length > 0" class="text-caption text-on-surface-variant bg-white/10 rounded-full px-1.5 py-0.5">{{ test.reports.value.length }}</span>
      </button>

      <button class="glass-button px-3 py-1.5 rounded-full font-caption text-caption font-normal flex items-center gap-1.5 select-none" @click="handleOpenGlobalAuth">
        <span class="material-symbols-outlined text-[16px]">key</span>
        <span class="whitespace-nowrap">全局认证</span>
        <span v-if="test.globalAuthHeaders.value.length > 0" class="text-caption text-green-500 bg-green-500/10 rounded-full px-1.5 py-0.5">{{ test.globalAuthHeaders.value.length }}项</span>
      </button>

      <button class="glass-button px-3 py-1.5 rounded-full font-caption text-caption font-normal flex items-center gap-1.5 select-none" @click="handleOpenDomainKeywords">
        <span class="material-symbols-outlined text-[16px]">dns</span>
        <span class="whitespace-nowrap">域名过滤</span>
        <span class="text-caption text-on-surface-variant bg-white/10 rounded-full px-1.5 py-0.5">{{ test.domainKeywords.value.length }}</span>
      </button>
    </div>

    <!-- Filter & Stats Bar -->
    <div class="glass-panel rounded-xl px-5 py-2.5 flex items-center gap-3 flex-wrap">
      <div class="relative flex-1 min-w-[200px]">
        <span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-[16px] text-on-surface-variant">search</span>
        <input v-model="test.searchQuery.value" class="bg-white/50 border border-outline-variant/60 rounded-xl pl-9 pr-3 py-1.5 w-full text-body-md focus:ring-2 focus:ring-secondary/30 focus:border-secondary transition-all select-text"
          placeholder="搜索用例名称/URL/描述..." />
      </div>

      <!-- Custom group dropdown -->
      <div class="relative" ref="groupDropdownRef">
        <button class="glass-hover rounded-xl px-3 py-1.5 text-body-md flex items-center gap-2 min-w-[120px] select-none"
          @click="toggleGroupDropdown">
          <span class="flex-1 text-left truncate">{{ test.selectedGroup.value?.name || '全部组' }}</span>
          <span class="material-symbols-outlined text-[16px] transition-transform" :class="groupDropdownOpen ? 'rotate-180' : ''">expand_more</span>
        </button>
      </div>
      <Teleport to="body">
        <Transition name="fade-scale">
          <div v-if="groupDropdownOpen" class="fixed z-[9999]" :style="groupDropdownStyle" @click.stop>
            <div class="glass-panel rounded-2xl py-1 shadow-xl" style="min-width:160px">
              <div class="px-3 py-1 text-caption text-on-surface-variant select-none">选择分组</div>
              <div class="flex items-center gap-2 rounded-xl px-3 py-1.5 cursor-pointer select-none mx-1"
                :class="!test.selectedGroupId.value ? 'bg-white/20 font-medium' : 'hover:bg-white/10'"
                @click.stop="selectGroup('')">
                <span class="material-symbols-outlined text-[14px] text-on-surface-variant shrink-0" :class="!test.selectedGroupId.value ? 'visible' : 'invisible'">check</span>
                <span class="text-body-md">全部组</span>
              </div>
              <div v-for="g in test.groups.value" :key="g.id"
                class="flex items-center gap-2 rounded-xl px-3 py-1.5 cursor-pointer select-none mx-1"
                :class="test.selectedGroupId.value === g.id ? 'bg-white/20 font-medium' : 'hover:bg-white/10'"
                @click.stop="selectGroup(g.id)">
                <span class="w-2.5 h-2.5 rounded-full shrink-0" :style="{ backgroundColor: g.color }"></span>
                <span class="flex-1 text-body-md truncate">{{ g.name }}</span>
                <span class="material-symbols-outlined text-[14px] text-on-surface-variant shrink-0" :class="test.selectedGroupId.value === g.id ? 'visible' : 'invisible'">check</span>
              </div>
              <div class="border-t border-white/10 mx-2 my-1" />
              <button class="flex items-center gap-2 rounded-xl px-3 py-1.5 w-full text-body-md hover:bg-white/10 select-none"
                @click.stop="showGroupManager = true; groupDropdownOpen = false">
                <span class="material-symbols-outlined text-[14px]">settings</span>
                <span>管理分组</span>
              </button>
            </div>
          </div>
        </Transition>
      </Teleport>

      <span class="text-caption text-on-surface-variant whitespace-nowrap">
        {{ test.filteredCases.value.length }} 用例
      </span>

    </div>

    <!-- Test Cases Area -->
    <div class="flex-1 flex gap-4 min-h-0">
      <!-- Case List: Endpoint-grouped expandable view -->
      <div class="glass-panel rounded-xl flex-[0_0_45%] min-w-[400px] max-w-[55%] flex flex-col overflow-hidden shadow-md">
        <div class="flex-1 overflow-y-auto custom-scrollbar p-2">
          <div v-if="test.testCases.value.length === 0" class="flex flex-col items-center justify-center h-full text-on-surface-variant gap-2 px-8 text-center">
            <span class="material-symbols-outlined text-[48px] opacity-40">science</span>
            <span class="text-body-md font-semibold">暂无测试用例</span>
            <span class="text-caption max-w-[300px]">1. 在「抓包」页面启动代理<br/>2. 在设备上手动操作触发接口请求<br/>3. 回到此页点击「智能生成用例」自动生成</span>
          </div>

          <!-- Grouped by group, then by endpoint -->
          <template v-for="group in test.groups.value" :key="group.id">
            <div v-if="endpointEntries(group.id).length > 0" class="mb-3">
              <!-- Group header -->
              <div class="flex items-center gap-2 px-2 py-1.5 mb-1">
                <span class="w-3 h-3 rounded-full shrink-0" :style="{ backgroundColor: group.color }"></span>
                <span class="font-label-md font-semibold text-on-surface">{{ group.name }}</span>
                <span class="text-caption text-on-surface-variant shrink-0">{{ endpointEntries(group.id).length }} 接口</span>
                <span v-if="pageSize > 0" class="flex items-center gap-1 text-caption text-on-surface-variant shrink-0 ml-1">
                  <span class="select-none">{{ paginatedEndpointEntries(group.id).currentPage }}/{{ paginatedEndpointEntries(group.id).totalPages }}</span>
                  <button class="glass-hover rounded p-0.5 text-on-surface-variant disabled:opacity-30" :disabled="paginatedEndpointEntries(group.id).currentPage <= 1" @click="goGroupPage(group.id, -1)">
                    <span class="material-symbols-outlined text-[14px]">chevron_left</span>
                  </button>
                  <button class="glass-hover rounded p-0.5 text-on-surface-variant disabled:opacity-30" :disabled="paginatedEndpointEntries(group.id).currentPage >= paginatedEndpointEntries(group.id).totalPages" @click="goGroupPage(group.id, 1)">
                    <span class="material-symbols-outlined text-[14px]">chevron_right</span>
                  </button>
                </span>
                <div class="flex-1" />
                <button class="glass-button px-2 py-0.5 rounded-full font-caption text-caption font-normal flex items-center gap-1 select-none" :disabled="test.isRunning.value" @click="handleRunGroup(group.id)">
                  <span v-if="test.isRunning.value && runProgress.groupId === group.id" class="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
                  <span v-else class="material-symbols-outlined text-[14px]">play_arrow</span>
                  <span>{{ test.isRunning.value && runProgress.groupId === group.id ? `${runProgress.current}/${runProgress.total}` : '运行' }}</span>
                </button>
                <button class="glass-button px-2 py-0.5 rounded-full font-caption text-caption font-normal flex items-center gap-1 select-none" @click="showAddEndpoint(group.id)">
                  <span class="material-symbols-outlined text-[14px]">add</span>
                  <span>添加接口</span>
                </button>
                <button class="glass-button px-2 py-0.5 rounded-full font-caption text-caption font-normal flex items-center gap-1 select-none hover:!bg-red-500/10 hover:!border-red-400/30" @click="handleClearGroupCases(group)">
                  <span class="material-symbols-outlined text-[14px]">delete_sweep</span>
                  <span>清空</span>
                </button>
              </div>

              <!-- Endpoint groups (expandable) -->
              <div v-for="ep in paginatedEndpointEntries(group.id).entries" :key="ep.key" class="mb-1">
                <div class="flex items-center gap-2 px-3 py-1.5 rounded-lg glass-hover group relative">
                  <div class="absolute inset-0 rounded-lg cursor-pointer" @click="toggleEndpoint(ep.key)" />
                  <span class="material-symbols-outlined text-[14px] text-on-surface-variant transition-transform relative pointer-events-none" :class="expandedEndpoints.has(ep.key) ? 'rotate-90' : ''">chevron_right</span>
                  <span class="font-mono text-caption px-1.5 py-0.5 rounded-md font-semibold whitespace-nowrap relative pointer-events-none" :class="methodClass(ep.method)">{{ ep.method }}</span>
                  <span v-if="editingEndpointName === ep.key" class="relative z-10 flex-1 min-w-0" @click.stop>
                    <input ref="endpointNameInput" v-model="editingEndpointNameValue" class="bg-white/80 border border-secondary rounded-lg px-2 py-0.5 text-body-md w-full" placeholder="输入接口名称" @blur="saveEndpointName(ep)" @keydown.enter="saveEndpointName(ep)" @keydown.escape="cancelEditEndpointName" />
                  </span>
                  <span class="text-body-md truncate relative flex-1 min-w-0 pointer-events-none" :title="test.getEndpointName(group.id, ep.method, ep.path) || ep.path">
                    <span v-if="test.getEndpointName(group.id, ep.method, ep.path)" class="text-on-surface font-semibold">{{ test.getEndpointName(group.id, ep.method, ep.path) }}</span>
                    <span v-else class="text-on-surface/60">{{ ep.path }}</span>
                  </span>
                  <span class="text-caption text-on-surface-variant shrink-0 relative pointer-events-none">{{ ep.cases.length }}</span>
                  <button class="glass-hover rounded-lg p-2 text-on-surface-variant hover:text-secondary opacity-0 group-hover:opacity-100 transition-all relative z-20 flex items-center justify-center" @click.stop="startEditEndpointName(ep)">
                    <span class="material-symbols-outlined text-[16px]">edit</span>
                  </button>
                  <button class="glass-hover rounded-lg p-2 text-on-surface-variant hover:text-red-500 opacity-0 group-hover:opacity-100 transition-all relative z-20 flex items-center justify-center" @click.stop="handleDeleteEndpoint(group.id, ep.method, ep.path)">
                    <span class="material-symbols-outlined text-[16px]">delete</span>
                  </button>
                </div>

                <!-- Expanded cases for this endpoint -->
                <div v-if="expandedEndpoints.has(ep.key)" class="ml-4 border-l-2 border-white/10 pl-2">
                  <div v-for="tc in ep.cases" :key="tc.id"
                    class="rounded-xl px-3 py-2 mb-1 cursor-pointer transition-all select-none"
                    :class="selectedCase?.id === tc.id ? 'glass-card-active' : 'glass-hover'"
                    @click="selectedCase = tc">
                    <div class="flex items-center gap-2 mb-1">
                      <span class="text-caption px-1.5 py-0.5 rounded-md font-semibold whitespace-nowrap"
                        :class="tc.type === 'positive' ? 'bg-green-500/10 text-green-600' : 'bg-red-500/10 text-red-600'">
                        {{ tc.type === 'positive' ? '正向' : '反向' }}
                      </span>
                      <span v-if="test.runningCaseIds.value.has(tc.id)" class="text-caption text-blue-500 flex items-center gap-1">
                        <span class="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
                        运行中
                      </span>
                      <span v-else-if="caseResultMap[tc.id]" class="text-caption flex items-center gap-1" :class="caseResultMap[tc.id].passed ? 'text-green-500' : 'text-red-500'">
                        {{ caseResultMap[tc.id].duration?.toFixed(0) }}ms
                      </span>
                      <div class="flex-1" />
                      <span v-if="caseResultMap[tc.id]" class="shrink-0">
                        <span class="material-symbols-outlined text-[18px]" :class="caseResultMap[tc.id].passed ? 'text-green-500' : 'text-red-500'">{{ caseResultMap[tc.id].passed ? 'check_circle' : 'cancel' }}</span>
                      </span>
                      <button class="glass-hover rounded-lg p-0.5 text-on-surface-variant opacity-0 hover:opacity-100 transition-opacity" @click.stop="test.toggleCaseEnabled(tc)">
                        <span class="material-symbols-outlined text-[14px]" :class="tc.enabled ? 'text-green-500' : 'text-gray-300'">{{ tc.enabled ? 'toggle_on' : 'toggle_off' }}</span>
                      </button>
                    </div>
                    <div class="text-body-md text-on-surface pl-1 truncate">{{ tc.name }}</div>
                  </div>
                </div>
              </div>
            </div>
          </template>
        </div>
      </div>

      <!-- Case Detail Panel -->
      <div class="glass-panel rounded-xl flex-1 flex flex-col overflow-hidden min-w-0 shadow-md">
        <div v-if="!selectedCase" class="flex items-center justify-center h-full text-on-surface-variant gap-2 select-text">
          <span class="material-symbols-outlined text-[48px] opacity-40">touch_app</span>
          <span class="text-body-md">选择一个用例查看详情</span>
        </div>
        <template v-else>
          <div class="flex items-center gap-1 px-4 pt-3 pb-2 border-b border-white/10 flex-shrink-0">
            <button v-for="tab in detailTabs" :key="tab.key"
              class="rounded-lg px-3 py-1.5 text-body-md transition-all"
              :class="activeDetailTab === tab.key ? 'glass-active' : 'glass-button'"
              @click="activeDetailTab = tab.key">
              {{ tab.label }}
            </button>
            <div class="flex-1" />
            <button class="glass-button px-2.5 py-1 rounded-full font-caption text-caption font-normal flex items-center gap-1 select-none"
              :disabled="test.runningCaseIds.value.has(selectedCase.id)"
              @click="handleRunSingle(selectedCase)">
              <span class="material-symbols-outlined text-[14px]">play_arrow</span>
              {{ test.runningCaseIds.value.has(selectedCase.id) ? '运行中...' : '运行' }}
            </button>
            <button class="glass-button px-2.5 py-1 rounded-full font-caption text-caption font-normal flex items-center gap-1 select-none" @click="showDeleteConfirm(selectedCase)">
              <span class="material-symbols-outlined text-[14px]">delete</span>
              删除
            </button>
          </div>

          <div class="flex-1 overflow-y-auto custom-scrollbar p-4 select-text flex flex-col">
            <!-- Overview Tab -->
            <div v-if="activeDetailTab === 'overview'" class="flex-1">
              <div class="space-y-4">
                <div>
                  <span class="text-label-md text-on-surface-variant block mb-1">用例名称</span>
                  <input v-model="selectedCase.name" class="bg-white/50 border border-outline-variant/60 rounded-xl px-3 py-2 w-full text-body-md select-text" @change="test.updateTestCase(selectedCase)" />
                </div>
                <div>
                  <span class="text-label-md text-on-surface-variant block mb-1">描述</span>
                  <input v-model="selectedCase.description" class="bg-white/50 border border-outline-variant/60 rounded-xl px-3 py-2 w-full text-caption select-text" @change="test.updateTestCase(selectedCase)" placeholder="无描述" />
                </div>
                <div class="flex gap-3">
                  <div class="flex-1">
                    <span class="text-label-md text-on-surface-variant block mb-1">方法</span>
                    <div class="bg-white/[0.06] rounded-xl px-3 py-2 font-mono text-caption" :class="methodTextClass(selectedCase.method)">{{ selectedCase.method }}</div>
                  </div>
                  <div class="flex-1">
                    <span class="text-label-md text-on-surface-variant block mb-1">类型</span>
                    <div class="bg-white/[0.06] rounded-xl px-3 py-2 font-mono text-caption" :class="selectedCase.type === 'positive' ? 'text-green-600' : 'text-red-600'">{{ selectedCase.type === 'positive' ? '正向测试' : '反向测试' }}</div>
                  </div>
                  <div class="flex-1">
                    <span class="text-label-md text-on-surface-variant block mb-1">所属分组</span>
                    <div class="bg-white/[0.06] rounded-xl px-3 py-2 font-caption text-caption">{{ groupName(selectedCase.groupId) }}</div>
                  </div>
                </div>
                <div>
                  <span class="text-label-md text-on-surface-variant block mb-1">请求 URL</span>
                  <textarea v-model="selectedCase.url" class="bg-white/50 border border-outline-variant/60 rounded-xl px-3 py-2 w-full font-mono text-caption select-text resize-y break-all min-h-[3em] overflow-hidden" @change="test.updateTestCase(selectedCase)" @input="autoResizeTextarea($event)" />
                </div>
                <div v-if="selectedCase.query">
                  <span class="text-label-md text-on-surface-variant block mb-1">Query 参数</span>
                  <textarea v-model="selectedCase.query" class="bg-white/50 border border-outline-variant/60 rounded-xl px-3 py-2 w-full font-mono text-caption select-text resize-y break-all min-h-[2.5em] overflow-hidden" @change="test.updateTestCase(selectedCase)" @input="autoResizeTextarea($event)" />
                </div>
              </div>
            </div>

            <!-- Headers Tab -->
            <div v-if="activeDetailTab === 'headers'">
              <div class="space-y-1.5">
                <div v-for="(h, hi) in selectedCase.headers" :key="hi" class="flex items-start gap-1.5">
                  <textarea v-model="h[0]" class="bg-white/50 border border-outline-variant/60 rounded-lg px-2 py-1.5 font-mono text-caption flex-[0_0_35%] min-w-0 select-text resize-y min-h-[2.5em] overflow-hidden" placeholder="Header名" @change="test.updateTestCase(selectedCase)" @input="autoResizeTextarea($event)" />
                  <textarea v-model="h[1]" class="bg-white/50 border border-outline-variant/60 rounded-lg px-2 py-1.5 font-mono text-caption flex-1 min-w-0 select-text resize-y min-h-[2.5em] overflow-hidden" placeholder="Header值" @change="test.updateTestCase(selectedCase)" @input="autoResizeTextarea($event)" />
                  <button class="glass-hover rounded-lg p-0.5 text-on-surface-variant hover:text-red-500 shrink-0 mt-1" @click="removeHeader(hi)">
                    <span class="material-symbols-outlined text-[16px]">remove_circle</span>
                  </button>
                </div>
                <div v-if="selectedCase.headers.length === 0" class="text-on-surface-variant text-center py-4">无请求头</div>
                <button class="glass-button px-3 py-1.5 rounded-full font-caption text-caption font-normal flex items-center gap-1 select-none" @click="addHeader">
                  <span class="material-symbols-outlined text-[14px]">add</span>添加请求头
                </button>
              </div>
            </div>

            <!-- Body Tab -->
            <div v-if="activeDetailTab === 'body'">
              <textarea v-model="selectedCase.body" class="bg-white/50 border border-outline-variant/60 rounded-xl px-3 py-2 w-full font-mono text-caption select-text resize-y whitespace-pre-wrap break-all min-h-[120px] overflow-hidden" placeholder="无请求体（留空）" @change="test.updateTestCase(selectedCase)" @input="autoResizeTextarea($event)" />
            </div>

            <!-- Assertions Tab -->
            <div v-if="activeDetailTab === 'assertions'">
              <div class="space-y-2">
                <div v-for="(a, ai) in selectedCase.assertions" :key="a.id"
                  class="bg-white/[0.06] rounded-xl px-3 py-2.5">
                  <div class="flex flex-col gap-1.5">
                    <!-- Row 1: type | operator | target -->
                    <div class="flex items-center gap-1.5">
                      <select v-model="a.type" class="bg-white/80 border border-outline-variant/60 rounded-lg px-2 py-1 text-caption font-mono flex-[0_0_auto] min-w-0" @change="onAssertionTypeChange(a)">
                        <option value="status_code">状态码</option>
                        <option value="body_contains">响应体包含</option>
                        <option value="json_path">JSON路径</option>
                        <option value="header">响应头</option>
                        <option value="response_time">响应时间</option>
                        <option value="json_schema">JSON Schema</option>
                      </select>
                      <select v-if="a.type !== 'body_contains' && a.type !== 'response_time'" v-model="a.operator" class="bg-white/80 border border-outline-variant/60 rounded-lg px-2 py-1 text-caption font-mono flex-[0_0_auto] min-w-0" @change="test.updateTestCase(selectedCase)">
                        <option value="equals">equals</option>
                        <option value="not_equals">not_equals</option>
                        <option value="contains">contains</option>
                        <option value="not_contains">not_contains</option>
                        <option value="greater_than">greater_than</option>
                        <option value="less_than">less_than</option>
                      </select>
                      <input v-if="a.type === 'json_path'" v-model="a.target" class="bg-white/80 border border-outline-variant/60 rounded-lg px-2 py-1 text-caption font-mono flex-1 min-w-0" placeholder="JSON路径, 如 data.token" @change="test.updateTestCase(selectedCase)" />
                      <input v-else-if="a.type === 'header'" v-model="a.target" class="bg-white/80 border border-outline-variant/60 rounded-lg px-2 py-1 text-caption font-mono flex-1 min-w-0" placeholder="响应头名称, 如 Content-Type" @change="test.updateTestCase(selectedCase)" />
                      <input v-else-if="a.type === 'body_contains'" v-model="a.target" class="bg-white/80 border border-outline-variant/60 rounded-lg px-2 py-1 text-caption font-mono flex-1 min-w-0" placeholder="要搜索的文本" @change="test.updateTestCase(selectedCase)" />
                      <input v-else-if="a.type === 'response_time'" v-model="a.expectedValue" type="number" class="bg-white/80 border border-outline-variant/60 rounded-lg px-2 py-1 text-caption font-mono flex-[0_0_120px]" placeholder="最大毫秒" @change="onResponseTimeAssertion(a)" />
                      <span v-else class="text-caption text-on-surface-variant flex-1">响应状态码</span>
                      <button class="glass-hover rounded-lg p-0.5 text-on-surface-variant hover:text-red-500 shrink-0" @click="removeAssertion(ai)">
                        <span class="material-symbols-outlined text-[16px]">remove_circle</span>
                      </button>
                      <span v-if="resultAssertionPassed(a.id) === true" class="text-green-500 shrink-0">
                        <span class="material-symbols-outlined text-[16px]">check_circle</span>
                      </span>
                      <span v-else-if="resultAssertionPassed(a.id) === false" class="text-red-500 shrink-0">
                        <span class="material-symbols-outlined text-[16px]">cancel</span>
                      </span>
                    </div>
                    <!-- Row 2: expectedValue (for types that need it) -->
                    <div v-if="a.type !== 'body_contains' && a.type !== 'response_time' && a.type !== 'status_code'">
                      <textarea v-model="a.expectedValue" class="bg-white/80 border border-outline-variant/60 rounded-lg px-2 py-1 text-caption font-mono w-full resize-y min-h-[2.5em] overflow-hidden" placeholder="期望值" @change="test.updateTestCase(selectedCase)" @input="autoResizeTextarea($event)" />
                    </div>
                    <div v-else-if="a.type === 'status_code'">
                      <input v-model="a.expectedValue" class="bg-white/80 border border-outline-variant/60 rounded-lg px-2 py-1 text-caption font-mono flex-1" placeholder="如 200" @change="test.updateTestCase(selectedCase)" />
                    </div>
                  </div>
                </div>
                <div v-if="selectedCase.assertions.length === 0" class="text-on-surface-variant text-center py-4">无断言</div>
                <button class="glass-button px-3 py-1.5 rounded-full font-caption text-caption font-normal flex items-center gap-1 select-none" @click="addAssertion">
                  <span class="material-symbols-outlined text-[14px]">add</span>添加断言
                </button>
              </div>
            </div>

            <!-- Result Tab -->
            <div v-if="activeDetailTab === 'result'" class="flex-1 flex flex-col">
              <div v-if="!caseResultMap[selectedCase.id]" class="text-on-surface-variant text-center py-8">尚未运行此用例</div>
              <template v-else>
                <div class="flex items-center gap-3 mb-4">
                  <span class="font-mono text-body-md" :class="caseResultMap[selectedCase.id].passed ? 'text-green-500' : 'text-red-500'">
                    <span class="material-symbols-outlined text-[20px] align-middle">{{ caseResultMap[selectedCase.id].passed ? 'check_circle' : 'cancel' }}</span>
                    {{ caseResultMap[selectedCase.id].passed ? '通过' : '失败' }}
                  </span>
                  <span class="text-caption text-on-surface-variant">状态码: {{ caseResultMap[selectedCase.id].statusCode || '-' }}</span>
                  <span class="text-caption text-on-surface-variant">耗时: {{ caseResultMap[selectedCase.id].duration?.toFixed(1) }}ms</span>
                </div>
                <div v-if="caseResultMap[selectedCase.id].errorMessage" class="bg-red-500/10 rounded-xl p-3 mb-4">
                  <span class="text-label-md text-red-600">错误信息</span>
                  <pre class="font-mono text-caption text-red-500 mt-1 whitespace-pre-wrap">{{ caseResultMap[selectedCase.id].errorMessage }}</pre>
                </div>
                <div class="mb-4">
                  <span class="text-label-md font-semibold text-on-surface block mb-2">断言结果</span>
                  <div v-for="ar in caseResultMap[selectedCase.id].assertionResults" :key="ar.assertionId"
                    class="flex items-center gap-2 bg-white/[0.06] rounded-lg px-3 py-1.5 mb-1">
                    <span class="material-symbols-outlined text-[14px]" :class="ar.passed ? 'text-green-500' : 'text-red-500'">{{ ar.passed ? 'check_circle' : 'cancel' }}</span>
                    <span class="font-mono text-caption text-on-surface">期望: {{ ar.expected }}</span>
                    <span class="text-caption text-on-surface-variant">实际: {{ ar.actual }}</span>
                  </div>
                </div>
                <div v-if="caseResultMap[selectedCase.id].responseHeaders" class="flex-1 flex flex-col mb-4">
                  <span class="text-label-md font-semibold text-on-surface block mb-2">响应头</span>
                  <div class="bg-white/[0.06] rounded-xl p-3 font-mono text-caption flex-1 overflow-y-auto">
                    <div v-for="h in caseResultMap[selectedCase.id].responseHeaders" :key="h[0]" class="mb-0.5">
                      <span class="text-primary">{{ h[0] }}</span>: <span class="text-on-surface">{{ h[1] }}</span>
                    </div>
                  </div>
                </div>
                <div v-if="caseResultMap[selectedCase.id].responseBody" class="flex-1 flex flex-col">
                  <span class="text-label-md font-semibold text-on-surface block mb-2">响应体</span>
                  <pre class="bg-white/[0.06] rounded-xl p-3 font-mono text-caption text-on-surface overflow-x-auto whitespace-pre-wrap break-all custom-scrollbar flex-1"><code>{{ tryFormatJson(caseResultMap[selectedCase.id].responseBody || '') }}</code></pre>
                </div>
                <div v-if="responseBodyJson" class="mt-4">
                  <span class="text-label-md font-semibold text-on-surface block mb-2">JSON 路径探索 <span class="text-caption text-on-surface-variant font-normal">（点击节点添加断言）</span></span>
                  <div class="bg-white/[0.06] rounded-xl p-3">
                    <JsonExplorer :data="responseBodyJson" @select="addJsonAssertion" />
                  </div>
                </div>
              </template>
            </div>
          </div>
        </template>
      </div>
    </div>

    <!-- Group Manager Dialog -->
    <Teleport to="body">
      <Transition name="fade">
        <div v-if="showGroupManager" class="fixed inset-0 z-[100] flex items-center justify-center" @click.self="showGroupManager = false">
          <div class="absolute inset-0 bg-black/10 backdrop-blur-sm"></div>
          <div class="glass-panel rounded-[2rem] p-6 w-full max-w-md relative z-10 bg-white/90 max-h-[80vh] flex flex-col">
            <div class="flex justify-between items-center mb-4">
              <h3 class="font-label-md text-label-md text-on-surface font-semibold flex items-center gap-1.5 select-none">
                <span class="material-symbols-outlined text-[16px]">folder_special</span>分组管理
              </h3>
              <button class="glass-button p-1 rounded select-none" @click="showGroupManager = false">
                <span class="material-symbols-outlined text-[18px]">close</span>
              </button>
            </div>
            <div class="flex gap-2 mb-4">
              <input v-model="newGroupName" class="bg-white/80 border border-outline-variant rounded-lg px-3 py-2 font-caption text-caption flex-1 select-text" placeholder="新分组名称" @keydown.enter="handleAddGroup" />
              <input v-model="newGroupColor" type="color" class="w-10 h-10 rounded-lg cursor-pointer border border-outline-variant" />
              <button class="glass-button rounded-lg px-3 py-2 select-none" @click="handleAddGroup">
                <span class="material-symbols-outlined text-[16px]">add</span>
              </button>
            </div>
            <div class="flex-1 overflow-y-auto custom-scrollbar space-y-1">
              <div v-for="g in test.groups.value" :key="g.id"
                class="flex items-center gap-2 bg-white/5 rounded-lg px-3 py-2">
                <span class="w-3 h-3 rounded-full shrink-0" :style="{ backgroundColor: g.color }"></span>
                <input v-model="g.name" class="bg-transparent border-b border-transparent hover:border-outline-variant focus:border-secondary focus:outline-none flex-1 text-body-md px-1 select-text" @change="handleUpdateGroup(g)" />
                <button class="glass-hover rounded-lg p-1 text-on-surface-variant hover:text-red-500" @click="handleDeleteGroup(g.id)">
                  <span class="material-symbols-outlined text-[14px]">delete</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- Report List Dialog -->
    <Teleport to="body">
      <Transition name="fade">
        <div v-if="showReportList" class="fixed inset-0 z-[100] flex items-center justify-center" @click.self="showReportList = false">
          <div class="absolute inset-0 bg-black/10 backdrop-blur-sm"></div>
          <div class="glass-panel rounded-[2rem] p-6 w-full max-w-2xl relative z-10 bg-white/90 max-h-[80vh] flex flex-col">
            <div class="flex justify-between items-center mb-4">
              <h3 class="font-label-md text-label-md text-on-surface font-semibold flex items-center gap-1.5 select-none">
                <span class="material-symbols-outlined text-[16px]">assessment</span>测试报告
              </h3>
              <button class="glass-button p-1 rounded select-none" @click="showReportList = false">
                <span class="material-symbols-outlined text-[18px]">close</span>
              </button>
            </div>
            <div class="flex-1 overflow-y-auto custom-scrollbar space-y-2">
              <div v-for="r in test.reports.value" :key="r.id"
                class="bg-white/5 rounded-xl px-4 py-3 cursor-pointer transition-all hover:bg-white/10"
                @click="handleViewReport(r)">
                <div class="flex items-center gap-3">
                  <span class="material-symbols-outlined text-[20px]"
                    :class="r.status === 'completed' ? (r.failedCases === 0 ? 'text-green-500' : 'text-red-500') : 'text-blue-500'">
                    {{ r.status === 'completed' ? (r.failedCases === 0 ? 'check_circle' : 'warning') : 'hourglass_top' }}
                  </span>
                  <div class="flex-1 min-w-0">
                    <div class="font-label-md text-on-surface truncate">{{ r.name }}</div>
                    <div class="text-caption text-on-surface-variant">
                      {{ new Date(r.startedAt).toLocaleString() }} —
                      通过 {{ r.passedCases }}/{{ r.totalCases }}，
                      耗时 {{ r.totalDuration?.toFixed(0) }}ms
                    </div>
                  </div>
                  <div class="flex items-center gap-2 shrink-0">
                    <div class="flex gap-0.5">
                      <div class="w-2 h-4 rounded-sm bg-green-500" :style="{ height: Math.max(4, (r.passedCases / Math.max(1, r.totalCases)) * 40) + 'px' }" />
                      <div class="w-2 h-4 rounded-sm bg-red-500" :style="{ height: Math.max(4, (r.failedCases / Math.max(1, r.totalCases)) * 40) + 'px' }" />
                    </div>
                    <button class="glass-hover rounded-lg p-1 text-on-surface-variant hover:text-red-500" @click.stop="handleDeleteReport(r.id)">
                      <span class="material-symbols-outlined text-[14px]">delete</span>
                    </button>
                  </div>
                </div>
              </div>
              <div v-if="test.reports.value.length === 0" class="text-on-surface-variant text-center py-8">暂无测试报告</div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- Report Detail Dialog -->
    <Teleport to="body">
      <Transition name="fade">
        <div v-if="showReportDetail && test.currentReport.value" class="fixed inset-0 z-[100] flex items-center justify-center" @click.self="showReportDetail = false">
          <div class="absolute inset-0 bg-black/10 backdrop-blur-sm"></div>
          <div class="glass-panel rounded-[2rem] p-6 w-full max-w-3xl relative z-10 bg-white/90 max-h-[min(85vh,750px)] flex flex-col">
            <div class="flex justify-between items-center mb-4">
              <h3 class="font-label-md text-label-md text-on-surface font-semibold flex items-center gap-1.5 select-none">
                <span class="material-symbols-outlined text-[16px]">assessment</span>{{ test.currentReport.value.name }}
              </h3>
              <div class="flex items-center gap-2">
                <button class="glass-button px-2.5 py-1 rounded-full font-caption text-caption font-normal flex items-center gap-1 select-none" @click="handleExportReport(test.currentReport.value.id)">
                  <span class="material-symbols-outlined text-[14px]">download</span>
                  导出
                </button>
                <button class="glass-button p-1 rounded select-none" @click="showReportDetail = false">
                  <span class="material-symbols-outlined text-[18px]">close</span>
                </button>
              </div>
            </div>

            <!-- Report Summary -->
            <div class="grid grid-cols-4 gap-3 mb-4">
              <div class="bg-white/[0.06] rounded-xl p-3 text-center">
                <div class="text-headline-md font-bold text-on-surface">{{ test.currentReport.value.totalCases }}</div>
                <div class="text-caption text-on-surface-variant">总用例</div>
              </div>
              <div class="bg-white/[0.06] rounded-xl p-3 text-center">
                <div class="text-headline-md font-bold text-green-500">{{ test.currentReport.value.passedCases }}</div>
                <div class="text-caption text-on-surface-variant">通过</div>
              </div>
              <div class="bg-white/[0.06] rounded-xl p-3 text-center">
                <div class="text-headline-md font-bold text-red-500">{{ test.currentReport.value.failedCases }}</div>
                <div class="text-caption text-on-surface-variant">失败</div>
              </div>
              <div class="bg-white/[0.06] rounded-xl p-3 text-center">
                <div class="text-headline-md font-bold text-on-surface">{{ ((test.currentReport.value.passedCases / Math.max(1, test.currentReport.value.totalCases)) * 100).toFixed(0) }}%</div>
                <div class="text-caption text-on-surface-variant">通过率</div>
              </div>
            </div>

            <div class="text-caption text-on-surface-variant mb-4">
              开始时间: {{ new Date(test.currentReport.value.startedAt).toLocaleString() }}
              <span v-if="test.currentReport.value.completedAt">
                &nbsp;|&nbsp;完成时间: {{ new Date(test.currentReport.value.completedAt).toLocaleString() }}
              </span>
              <span v-if="test.currentReport.value.totalDuration">
                &nbsp;|&nbsp;总耗时: {{ test.currentReport.value.totalDuration.toFixed(0) }}ms
              </span>
            </div>

            <!-- Result List (when no result selected) -->
            <div v-if="!selectedReportResult" class="flex-1 overflow-y-auto custom-scrollbar space-y-1">
              <div v-for="result in test.currentResults.value" :key="result.id"
                class="flex items-center gap-3 bg-white/[0.04] rounded-lg px-3 py-2 cursor-pointer transition-all"
                :class="result.passed ? 'hover:bg-white/[0.08]' : 'bg-red-500/5 hover:bg-red-500/10'"
                @click="selectedReportResult = result">
                <span class="material-symbols-outlined text-[16px]" :class="result.passed ? 'text-green-500' : 'text-red-500'">
                  {{ result.passed ? 'check_circle' : 'cancel' }}
                </span>
                <div class="flex-1 min-w-0">
                  <div class="font-mono text-caption text-on-surface truncate">{{ findCaseName(result.caseId) }}</div>
                  <div class="text-caption text-on-surface-variant">
                    状态码: {{ result.statusCode || '-' }} | 耗时: {{ result.duration?.toFixed(1) }}ms
                  </div>
                </div>
                <span v-if="result.errorMessage" class="text-caption text-red-500 truncate max-w-[200px]" :title="result.errorMessage">{{ result.errorMessage }}</span>
                <div class="flex gap-0.5">
                  <div v-for="ar in result.assertionResults.slice(0, 3)" :key="ar.assertionId"
                    class="w-1.5 h-1.5 rounded-full"
                    :class="ar.passed ? 'bg-green-500' : 'bg-red-500'"
                    :title="`期望: ${ar.expected}, 实际: ${ar.actual}`" />
                </div>
              </div>
            </div>

            <!-- Result Detail (full view when a result is selected) -->
            <div v-else class="min-h-0 overflow-y-auto custom-scrollbar space-y-3 self-start w-full">
              <button class="glass-button px-2 py-1 rounded-full font-caption text-caption font-normal flex items-center gap-1 select-none" @click="selectedReportResult = null">
                <span class="material-symbols-outlined text-[14px]">arrow_back</span>返回列表
              </button>
              <div class="flex items-center gap-2">
                <span class="font-label-md font-semibold text-on-surface">{{ findCaseName(selectedReportResult.caseId) }}</span>
                <span class="material-symbols-outlined text-[16px]" :class="selectedReportResult.passed ? 'text-green-500' : 'text-red-500'">
                  {{ selectedReportResult.passed ? 'check_circle' : 'cancel' }}
                </span>
                <span class="font-mono text-caption" :class="selectedReportResult.passed ? 'text-green-500' : 'text-red-500'">
                  {{ selectedReportResult.passed ? '通过' : '失败' }}
                </span>
              </div>
              <div class="bg-white/[0.04] rounded-lg px-3 py-2">
                <span class="text-caption text-on-surface-variant">状态码: </span>
                <span class="font-mono text-caption text-on-surface">{{ selectedReportResult.statusCode || '-' }}</span>
                <span class="ml-4 text-caption text-on-surface-variant">耗时: </span>
                <span class="font-mono text-caption text-on-surface">{{ selectedReportResult.duration?.toFixed(1) }}ms</span>
              </div>
              <div v-if="selectedReportResult.errorMessage" class="bg-red-500/10 rounded-lg px-3 py-2">
                <span class="text-caption text-red-500">{{ selectedReportResult.errorMessage }}</span>
              </div>
              <div class="bg-white/[0.04] rounded-lg px-3 py-2">
                <div v-for="ar in selectedReportResult.assertionResults" :key="ar.assertionId" class="flex items-center gap-2 py-0.5">
                  <span class="material-symbols-outlined text-[14px]" :class="ar.passed ? 'text-green-500' : 'text-red-500'">{{ ar.passed ? 'check_circle' : 'cancel' }}</span>
                  <span class="font-mono text-caption text-on-surface">期望: {{ ar.expected }}</span>
                  <span class="text-caption text-on-surface-variant">实际: {{ ar.actual }}</span>
                </div>
              </div>
              <div v-if="selectedReportResult.responseHeaders">
                <span class="text-label-md font-semibold text-on-surface block mb-1">响应头</span>
                <div class="bg-white/[0.04] rounded-lg px-3 py-2 font-mono text-caption">
                  <div v-for="h in selectedReportResult.responseHeaders" :key="h[0]" class="mb-0.5">
                    <span class="text-primary">{{ h[0] }}</span>: <span class="text-on-surface">{{ h[1] }}</span>
                  </div>
                </div>
              </div>
              <div v-if="selectedReportResult.responseBody">
                <span class="text-label-md font-semibold text-on-surface block mb-1">响应体</span>
                <pre class="bg-white/[0.04] rounded-lg px-3 py-2 font-mono text-caption text-on-surface overflow-x-auto whitespace-pre-wrap break-all max-h-[300px]"><code>{{ tryFormatJson(selectedReportResult.responseBody || '') }}</code></pre>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- Global Auth Dialog -->
    <Teleport to="body">
      <Transition name="fade">
        <div v-if="showGlobalAuth" class="fixed inset-0 z-[100] flex items-center justify-center" @click.self="showGlobalAuth = false">
          <div class="absolute inset-0 bg-black/10 backdrop-blur-sm"></div>
          <div class="glass-panel rounded-[2rem] p-6 w-full max-w-md relative z-10 bg-white/90">
            <div class="flex justify-between items-center mb-4">
              <h3 class="font-label-md text-label-md text-on-surface font-semibold flex items-center gap-1.5 select-none">
                <span class="material-symbols-outlined text-[16px]">key</span>全局认证
              </h3>
              <button class="glass-button p-1 rounded select-none" @click="showGlobalAuth = false">
                <span class="material-symbols-outlined text-[18px]">close</span>
              </button>
            </div>
            <p class="text-caption text-on-surface-variant mb-4">全局认证头部会自动从抓包响应中提取，也可手动添加。运行时会覆盖用例中同名请求头，并新增未设置的认证头。</p>
            <div class="space-y-2 max-h-[300px] overflow-y-auto custom-scrollbar">
              <div v-for="(h, hi) in authHeaders" :key="hi" class="flex items-center gap-2">
                <input v-model="h.name" class="bg-white/80 border border-outline-variant rounded-lg px-2 py-1.5 text-body-md flex-[0_0_40%] min-w-0 select-text" placeholder="名称, 如 Authorization" />
                <input v-model="h.value" class="bg-white/80 border border-outline-variant rounded-lg px-2 py-1.5 font-mono text-caption flex-1 min-w-0 select-text" placeholder="值, 如 Bearer xxx" />
                <button class="glass-hover rounded-lg p-1 text-on-surface-variant hover:text-red-500 shrink-0" @click="authHeaders.splice(hi, 1)">
                  <span class="material-symbols-outlined text-[16px]">remove_circle</span>
                </button>
              </div>
            </div>
            <button class="glass-button px-3 py-1.5 rounded-full font-caption text-caption font-normal flex items-center gap-1 select-none mt-3" @click="authHeaders.push({ name: '', value: '' })">
              <span class="material-symbols-outlined text-[14px]">add</span>添加认证头
            </button>
            <div class="flex justify-end gap-3 mt-4">
              <button class="glass-button px-4 py-2 rounded-xl select-none" @click="handleReDetectAuth">
                <span class="material-symbols-outlined text-[14px]">refresh</span> 重新获取
              </button>
              <button class="glass-button px-4 py-2 rounded-xl select-none" @click="handleClearAuth">清除</button>
              <button class="glass-button px-4 py-2 rounded-xl select-none bg-primary/20 border-primary/30" @click="handleSaveAuth">保存</button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- Domain Keywords Dialog -->
    <Teleport to="body">
      <Transition name="fade">
        <div v-if="showDomainKeywords" class="fixed inset-0 z-[100] flex items-center justify-center" @click.self="showDomainKeywords = false">
          <div class="absolute inset-0 bg-black/10 backdrop-blur-sm"></div>
          <div class="glass-panel rounded-[2rem] p-6 w-full max-w-md relative z-10 bg-white/90">
            <div class="flex justify-between items-center mb-4">
              <h3 class="font-label-md text-label-md text-on-surface font-semibold flex items-center gap-1.5 select-none">
                <span class="material-symbols-outlined text-[16px]">dns</span>域名过滤关键字
              </h3>
              <button class="glass-button p-1 rounded select-none" @click="showDomainKeywords = false">
                <span class="material-symbols-outlined text-[18px]">close</span>
              </button>
            </div>
            <p class="text-caption text-on-surface-variant mb-4">只对URL域名中包含以下关键字的接口生成测试用例（每行一个关键字，留空则不过滤）</p>
            <textarea v-model="domainKeywordsText" class="bg-white/80 border border-outline-variant rounded-xl px-3 py-2 w-full text-body-md select-text min-h-[120px] font-mono text-caption" placeholder="zeasn&#10;whaletv" />
            <div class="flex justify-end gap-3 mt-4">
              <button class="glass-button px-4 py-2 rounded-xl select-none bg-primary/20 border-primary/30" @click="handleSaveDomainKeywords">保存</button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- Delete Confirm Dialog -->
    <Teleport to="body">
      <Transition name="fade">
        <div v-if="deleteConfirm" class="fixed inset-0 z-[100] flex items-center justify-center" @click.self="deleteConfirm = null">
          <div class="absolute inset-0 bg-black/10 backdrop-blur-sm"></div>
          <div class="glass-panel rounded-[2rem] p-6 w-full max-w-sm relative z-10 bg-white/90">
            <h3 class="font-label-md text-label-md text-on-surface font-semibold mb-3">确认删除</h3>
            <p class="text-body-md text-on-surface mb-5">确定要删除用例「{{ deleteConfirm.name }}」吗？</p>
            <div class="flex justify-end gap-3">
              <button class="glass-hover rounded-xl px-4 py-2 select-none" @click="deleteConfirm = null">取消</button>
              <button class="glass-button rounded-xl px-4 py-2 select-none !bg-red-500/20 !border-red-400/30" @click="handleDeleteCase">删除</button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- Batch Delete Confirm Dialog -->
    <Teleport to="body">
      <Transition name="fade">
        <div v-if="batchDeleteConfirm" class="fixed inset-0 z-[100] flex items-center justify-center" @click.self="batchDeleteConfirm = null">
          <div class="absolute inset-0 bg-black/10 backdrop-blur-sm"></div>
          <div class="glass-panel rounded-[2rem] p-6 w-full max-w-sm relative z-10 bg-white/90">
            <h3 class="font-label-md text-label-md text-on-surface font-semibold mb-3">确认清空</h3>
            <p class="text-body-md text-on-surface mb-5">确定要清空分组「{{ batchDeleteConfirm.name }}」下的所有用例吗？此操作不可恢复。</p>
            <div class="flex justify-end gap-3">
              <button class="glass-hover rounded-xl px-4 py-2 select-none" @click="batchDeleteConfirm = null">取消</button>
              <button class="glass-button rounded-xl px-4 py-2 select-none !bg-red-500/20 !border-red-400/30" @click="handleBatchDeleteConfirm">清空</button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- Add Endpoint Dialog -->
    <Teleport to="body">
      <Transition name="fade">
        <div v-if="showAddEndpointDialog" class="fixed inset-0 z-[100] flex items-center justify-center" @click.self="showAddEndpointDialog = false">
          <div class="absolute inset-0 bg-black/10 backdrop-blur-sm"></div>
          <div class="glass-panel rounded-[2rem] p-6 w-full max-w-lg relative z-10 bg-white/90">
            <div class="flex justify-between items-center mb-4">
              <h3 class="font-label-md text-label-md text-on-surface font-semibold flex items-center gap-1.5 select-none">
                <span class="material-symbols-outlined text-[16px]">add_circle</span>手动添加接口
              </h3>
              <button class="glass-button p-1 rounded select-none" @click="showAddEndpointDialog = false">
                <span class="material-symbols-outlined text-[18px]">close</span>
              </button>
            </div>
            <div class="space-y-4 max-h-[60vh] overflow-y-auto custom-scrollbar pr-2">
              <div>
                <span class="text-label-md text-on-surface-variant block mb-1">所属分组</span>
                <select v-model="addEndpointForm.groupId" class="bg-white/80 border border-outline-variant rounded-xl px-3 py-2 w-full text-body-md">
                  <option v-for="g in test.groups.value" :key="g.id" :value="g.id">{{ g.name }}</option>
                </select>
              </div>
              <div class="flex gap-3">
                <div class="flex-[0_0_120px]">
                  <span class="text-label-md text-on-surface-variant block mb-1">请求方法</span>
                  <select v-model="addEndpointForm.method" class="bg-white/80 border border-outline-variant rounded-xl px-3 py-2 w-full text-body-md">
                    <option v-for="m in ['GET','POST','PUT','DELETE','PATCH','HEAD','OPTIONS']" :key="m" :value="m">{{ m }}</option>
                  </select>
                </div>
                <div class="flex-1 min-w-0">
                  <span class="text-label-md text-on-surface-variant block mb-1">URL</span>
                  <input v-model="addEndpointForm.url" class="bg-white/80 border border-outline-variant rounded-xl px-3 py-2 w-full text-body-md select-text font-mono" placeholder="https://api.example.com/v1/users" />
                </div>
              </div>
              <div>
                <span class="text-label-md text-on-surface-variant block mb-1">接口名称</span>
                <input v-model="addEndpointForm.name" class="bg-white/80 border border-outline-variant rounded-xl px-3 py-2 w-full text-body-md select-text" placeholder="获取用户列表" />
              </div>
              <div>
                <span class="text-label-md text-on-surface-variant block mb-1">用例类型</span>
                <div class="flex gap-3">
                  <label class="flex items-center gap-2 cursor-pointer">
                    <input type="radio" v-model="addEndpointForm.type" value="positive" class="accent-primary" />
                    <span class="text-body-md">正向测试</span>
                  </label>
                  <label class="flex items-center gap-2 cursor-pointer">
                    <input type="radio" v-model="addEndpointForm.type" value="negative" class="accent-primary" />
                    <span class="text-body-md">反向测试</span>
                  </label>
                </div>
              </div>
              <div>
                <div class="flex items-center gap-2 mb-1">
                  <span class="text-label-md text-on-surface-variant">请求头</span>
                  <button class="glass-hover rounded-lg p-0.5 text-on-surface-variant" @click="addFormHeaders.push(['', ''])">
                    <span class="material-symbols-outlined text-[14px]">add</span>
                  </button>
                </div>
                <div v-for="(h, hi) in addFormHeaders" :key="hi" class="flex items-start gap-1.5 mb-1">
                  <textarea v-model="h[0]" class="bg-white/80 border border-outline-variant rounded-lg px-2 py-1 text-caption font-mono flex-[0_0_35%] min-w-0 resize-y min-h-[2em] overflow-hidden" placeholder="Header名" @input="autoResizeTextarea($event)" />
                  <textarea v-model="h[1]" class="bg-white/80 border border-outline-variant rounded-lg px-2 py-1 text-caption font-mono flex-1 min-w-0 resize-y min-h-[2em] overflow-hidden" placeholder="Header值" @input="autoResizeTextarea($event)" />
                  <button class="glass-hover rounded-lg p-0.5 text-on-surface-variant hover:text-red-500 shrink-0 self-start" @click="addFormHeaders.splice(hi, 1)">
                    <span class="material-symbols-outlined text-[14px]">remove_circle</span>
                  </button>
                </div>
              </div>
              <div v-if="showAddFormBody">
                <span class="text-label-md text-on-surface-variant block mb-1">请求体</span>
                <textarea v-model="addEndpointForm.body" class="bg-white/80 border border-outline-variant rounded-xl px-3 py-2 w-full text-caption font-mono select-text resize-y min-h-[80px] overflow-hidden" placeholder='{"key": "value"}' @input="autoResizeTextarea($event)" />
              </div>
            </div>
            <div class="flex justify-end gap-3 mt-4 pt-3 border-t border-white/10">
              <button class="glass-button px-4 py-2 rounded-xl select-none" @click="showAddEndpointDialog = false">取消</button>
              <button class="glass-button px-4 py-2 rounded-xl select-none bg-primary/20 border-primary/30" :disabled="!addEndpointForm.url || !addEndpointForm.name" @click="handleAddEndpoint">添加</button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- Toast -->
    <Teleport to="body">
      <Transition name="fade">
        <div v-if="toastMsg" class="fixed bottom-8 left-1/2 -translate-x-1/2 z-[200] glass-panel rounded-full px-5 py-2.5 flex items-center gap-2 shadow-lg">
          <span class="material-symbols-outlined text-[18px]"
            :class="toastType === 'error' ? 'text-error' : toastType === 'info' ? 'text-blue-500' : 'text-success-indicator'">
            {{ toastType === 'error' ? 'error' : toastType === 'info' ? 'info' : 'check_circle' }}
          </span>
          <span class="font-body-md text-body-md text-on-surface">{{ toastMsg }}</span>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
defineOptions({ name: 'ApiTestPage' })
import { ref, reactive, computed, watch, onMounted, onUnmounted, inject, nextTick } from 'vue'
import { useApiTest } from '@/composables/useApiTest'
import { useApiProxy } from '@/composables/useApiProxy'
import type { ApiTestCase, ApiTestGroup, ApiTestReport, ApiTestResult, ApiTestAssertion } from '@/types'
import JsonExplorer from '@/components/JsonExplorer.vue'

const emit = defineEmits<{ back: [] }>()

const test = useApiTest()
const api = inject<ReturnType<typeof useApiProxy>>('apiProxy') || useApiProxy()

// Expose re-detection so templates can call it
function handleReDetectAuth() {
  test.clearGlobalAuth()
  test.autoDetectToken(api.capturedRequests.value)
  authHeaders.value = test.globalAuthHeaders.value.map(h => ({ ...h }))
  if (test.globalAuthHeaders.value.length > 0) {
    showToast(`已自动获取 ${test.globalAuthHeaders.value.length} 个认证头`)
  } else {
    showToast('未在抓包记录中找到认证信息，请先在设备上触发登录/认证请求', 'info')
  }
}

const selectedCase = ref<ApiTestCase | null>(null)
watch(selectedCase, () => {
  nextTick(() => {
    document.querySelectorAll('textarea.resize-y').forEach(el => {
      const ta = el as HTMLTextAreaElement
      ta.style.height = 'auto'
      ta.style.height = ta.scrollHeight + 'px'
    })
  })
})
const activeDetailTab = ref('overview')
const showGroupManager = ref(false)
const showReportList = ref(false)
const showReportDetail = ref(false)
const selectedReportResult = ref<ApiTestResult | null>(null)
const showGlobalAuth = ref(false)
const showDomainKeywords = ref(false)
const newGroupName = ref('')
const newGroupColor = ref('#6366f1')
const deleteConfirm = ref<ApiTestCase | null>(null)
const batchDeleteConfirm = ref<ApiTestGroup | null>(null)
const authHeaders = ref<{ name: string; value: string }[]>([])
const domainKeywordsText = ref('')
const expandedEndpoints = ref<Set<string>>(new Set())
const editingEndpointName = ref<string | null>(null)
const editingEndpointNameValue = ref('')
const editingEndpointEntry = ref<EndpointEntry | null>(null)
const endpointNameInput = ref<HTMLInputElement | null>(null)
const groupDropdownOpen = ref(false)
const groupDropdownRef = ref<HTMLElement | null>(null)
const groupDropdownStyle = ref({ top: '0px', left: '0px' })

const pageSize = ref(10)
const groupPages = ref<Record<string, number>>({})

function calcPageSize() {
  const availHeight = window.innerHeight - 220
  pageSize.value = Math.max(5, Math.floor(availHeight / 42))
}

const resizeHandler = () => { calcPageSize(); groupPages.value = {} }
onMounted(() => { calcPageSize(); window.addEventListener('resize', resizeHandler) })
onUnmounted(() => window.removeEventListener('resize', resizeHandler))

function paginatedEndpointEntries(groupId: string) {
  const all = endpointEntries(groupId)
  const pg = groupPages.value[groupId] || 1
  const total = Math.max(1, Math.ceil(all.length / pageSize.value))
  const page = Math.min(pg, total)
  return {
    entries: all.slice((page - 1) * pageSize.value, page * pageSize.value),
    currentPage: page,
    totalPages: total,
  }
}

function goGroupPage(groupId: string, delta: number) {
  const all = endpointEntries(groupId)
  const total = Math.max(1, Math.ceil(all.length / pageSize.value))
  const cur = groupPages.value[groupId] || 1
  const next = Math.max(1, Math.min(cur + delta, total))
  groupPages.value = { ...groupPages.value, [groupId]: next }
}

const showAddEndpointDialog = ref(false)
const addEndpointForm = reactive({
  groupId: '',
  name: '',
  method: 'GET',
  url: '',
  type: 'positive' as 'positive' | 'negative',
  body: '',
})
const addFormHeaders = ref<string[][]>([])
const showAddFormBody = computed(() => ['POST', 'PUT', 'PATCH'].includes(addEndpointForm.method))

function showAddEndpoint(groupId: string) {
  addEndpointForm.groupId = groupId
  addEndpointForm.name = ''
  addEndpointForm.method = 'GET'
  addEndpointForm.url = ''
  addEndpointForm.type = 'positive'
  addEndpointForm.body = ''
  addFormHeaders.value = []
  showAddEndpointDialog.value = true
}

async function handleAddEndpoint() {
  if (!addEndpointForm.url || !addEndpointForm.name) return
  try {
    const tc = await test.createManualTestCase({
      groupId: addEndpointForm.groupId,
      name: addEndpointForm.name,
      method: addEndpointForm.method,
      url: addEndpointForm.url,
      headers: addFormHeaders.value.filter(h => h[0].trim() && h[1].trim()),
      body: addEndpointForm.body || null,
      type: addEndpointForm.type,
    })
    showAddEndpointDialog.value = false
    showToast(`已添加接口「${tc.name}」`)
  } catch (e: any) {
    showToast(`添加失败: ${e.message}`, 'error')
  }
}

function toggleGroupDropdown() {
  if (groupDropdownOpen.value) {
    groupDropdownOpen.value = false
    return
  }
  if (groupDropdownRef.value) {
    const rect = groupDropdownRef.value.getBoundingClientRect()
    groupDropdownStyle.value = {
      top: `${rect.bottom + 4}px`,
      left: `${rect.left}px`,
    }
  }
  groupDropdownOpen.value = true
}

function selectGroup(id: string) {
  test.selectedGroupId.value = id
  groupDropdownOpen.value = false
}

function onDocumentClick(e: MouseEvent) {
  if (editingEndpointName.value && editingEndpointEntry.value) {
    const input = endpointNameInput.value
    if (input && !input.parentElement?.contains(e.target as Node)) {
      saveEndpointName(editingEndpointEntry.value)
    }
    return
  }
  if (groupDropdownOpen.value) {
    if (groupDropdownRef.value && !groupDropdownRef.value.contains(e.target as Node)) {
      groupDropdownOpen.value = false
    }
  }
}
onMounted(() => document.addEventListener('click', onDocumentClick))
onUnmounted(() => document.removeEventListener('click', onDocumentClick))

const runProgress = ref({ groupId: '', current: 0, total: 0 })
const isSmartGenerating = ref(false)
const isAiGenerating = ref(false)
const toastMsg = ref('')
const toastType = ref<'success' | 'error' | 'info'>('success')
let toastTimer: number | null = null

function onAssertionTypeChange(a: ApiTestAssertion) {
  // Reset fields based on new type
  if (a.type === 'status_code') {
    a.operator = 'equals'
    a.target = 'status_code'
    a.expectedValue = '200'
  } else if (a.type === 'body_contains') {
    a.operator = 'contains'
    a.target = ''
    a.expectedValue = ''
  } else if (a.type === 'response_time') {
    a.operator = 'less_than'
    a.target = 'duration_ms'
    a.expectedValue = '5000'
  } else if (a.type === 'json_path') {
    a.operator = 'equals'
    a.target = ''
    a.expectedValue = ''
  } else if (a.type === 'header') {
    a.operator = 'equals'
    a.target = ''
    a.expectedValue = ''
  } else if (a.type === 'json_schema') {
    a.operator = 'equals'
    a.target = ''
    a.expectedValue = '{}'
  }
  test.updateTestCase(selectedCase.value!)
}

function onResponseTimeAssertion(a: ApiTestAssertion) {
  a.operator = 'less_than'
  a.target = 'duration_ms'
  test.updateTestCase(selectedCase.value!)
}

function autoResizeTextarea(e: Event) {
  const ta = e.target as HTMLTextAreaElement
  ta.style.height = 'auto'
  ta.style.height = ta.scrollHeight + 'px'
}

function addAssertion() {
  if (!selectedCase.value) return
  selectedCase.value.assertions.push({
    id: crypto.randomUUID(),
    type: 'status_code',
    operator: 'equals',
    target: 'status_code',
    expectedValue: '200',
  })
  test.updateTestCase(selectedCase.value)
}

function removeAssertion(index: number) {
  if (!selectedCase.value) return
  selectedCase.value.assertions.splice(index, 1)
  test.updateTestCase(selectedCase.value)
}

const responseBodyJson = computed(() => {
  if (!selectedCase.value || !caseResultMap.value[selectedCase.value.id]) return null
  const body = caseResultMap.value[selectedCase.value.id].responseBody
  if (!body) return null
  try { return JSON.parse(body) } catch { return null }
})

function addJsonAssertion(path: string, value: string) {
  if (!selectedCase.value) return
  selectedCase.value.assertions.push({
    id: crypto.randomUUID(),
    type: 'json_path',
    operator: 'equals',
    target: path.startsWith('$.') ? path.slice(2) : path.startsWith('$') ? path.slice(1) : path,
    expectedValue: value,
  })
  test.updateTestCase(selectedCase.value)
  showToast(`已添加断言: ${path}`)
}

function addHeader() {
  if (!selectedCase.value) return
  selectedCase.value.headers.push(['', ''])
  test.updateTestCase(selectedCase.value)
}

function removeHeader(index: number) {
  if (!selectedCase.value) return
  selectedCase.value.headers.splice(index, 1)
  test.updateTestCase(selectedCase.value)
}
function showToast(msg: string, type: 'success' | 'error' | 'info' = 'success') {
  toastMsg.value = msg
  toastType.value = type
  if (toastTimer) clearTimeout(toastTimer)
  toastTimer = window.setTimeout(() => { toastMsg.value = '' }, 2500)
}

const detailTabs = [
  { key: 'overview', label: '概览' },
  { key: 'headers', label: '请求头' },
  { key: 'body', label: '请求体' },
  { key: 'assertions', label: '断言' },
  { key: 'result', label: '结果' },
]

function methodClass(method: string): string {
  const map: Record<string, string> = {
    GET: 'bg-blue-500/10 text-blue-600',
    POST: 'bg-emerald-500/10 text-emerald-600',
    PUT: 'bg-orange-500/10 text-orange-600',
    DELETE: 'bg-red-500/10 text-red-600',
    PATCH: 'bg-purple-500/10 text-purple-600',
  }
  return map[method] || 'bg-gray-500/10 text-gray-600'
}

function methodTextClass(method: string): string {
  const map: Record<string, string> = {
    GET: 'text-blue-600', POST: 'text-emerald-600', PUT: 'text-orange-600',
    DELETE: 'text-red-600', PATCH: 'text-purple-600',
  }
  return map[method] || 'text-gray-600'
}

function groupName(id: string): string {
  return test.groups.value.find(g => g.id === id)?.name || '未知'
}

function tryFormatJson(str: string): string {
  try {
    const parsed = JSON.parse(str)
    return JSON.stringify(parsed, null, 2)
  } catch { return str }
}

const caseResultMap = computed(() => {
  const map: Record<string, ApiTestResult> = {}
  for (const r of test.currentResults.value) {
    map[r.caseId] = r
  }
  return map
})

function resultAssertionPassed(assertionId: string): boolean | null {
  if (!selectedCase.value) return null
  const result = caseResultMap.value[selectedCase.value.id]
  if (!result) return null
  const ar = result.assertionResults.find(a => a.assertionId === assertionId)
  return ar ? ar.passed : null
}

interface EndpointEntry {
  key: string
  method: string
  path: string
  cases: ApiTestCase[]
}

function endpointEntries(groupId: string): EndpointEntry[] {
  const map = test.getEndpointCases(groupId)
  const entries: EndpointEntry[] = []
  for (const [key, cases] of map) {
    const first = cases[0]
    // Normalize display path: strip trailing slash for consistent grouping
    const displayPath = first.path.replace(/\/+$/, '') || first.path
    entries.push({ key, method: first.method, path: displayPath, cases })
  }
  return entries
}

function toggleEndpoint(key: string) {
  if (editingEndpointName.value) return
  const s = new Set(expandedEndpoints.value)
  if (s.has(key)) s.delete(key)
  else s.add(key)
  expandedEndpoints.value = s
}

function startEditEndpointName(ep: EndpointEntry) {
  editingEndpointName.value = ep.key
  editingEndpointEntry.value = ep
  const groupId = ep.cases[0]?.groupId || ''
  editingEndpointNameValue.value = test.getEndpointName(groupId, ep.method, ep.path)
  nextTick(() => {
    endpointNameInput.value?.focus()
    endpointNameInput.value?.select()
  })
}

function saveEndpointName(ep: EndpointEntry) {
  if (!editingEndpointName.value) return
  const groupId = ep.cases[0]?.groupId
  if (groupId) {
    test.setEndpointName(groupId, ep.method, ep.path, editingEndpointNameValue.value)
  }
  editingEndpointName.value = null
  editingEndpointNameValue.value = ''
  editingEndpointEntry.value = null
}

function cancelEditEndpointName() {
  editingEndpointName.value = null
  editingEndpointNameValue.value = ''
  editingEndpointEntry.value = null
}

function findCaseName(caseId: string): string {
  return test.testCases.value.find(c => c.id === caseId)?.name || caseId.slice(0, 8)
}

async function handleGenerate(useAi: boolean) {
  if (api.capturedRequests.value.length === 0) {
    showToast('未捕获到接口请求，请先启动代理并在设备上操作触发接口', 'error')
    return
  }
  if (useAi) isAiGenerating.value = true; else isSmartGenerating.value = true
  try {
    const cases = await test.generateCases(api.capturedRequests.value, useAi)
    const mode = useAi ? 'AI' : '智能'
    const filteredCount = test.filterByDomainKeywords(api.capturedRequests.value).length
    const msg = cases.length > 0
      ? `${mode}生成完成：新增 ${cases.length} 个用例（域名过滤匹配 ${filteredCount} 个接口）`
      : `${mode}生成完成，未产生新用例（无匹配域名或接口已全部覆盖）`
    showToast(msg)
  } catch (e: any) {
    showToast(`生成失败: ${e.message}`, 'error')
  } finally {
    isSmartGenerating.value = false
    isAiGenerating.value = false
  }
}

async function handleGenerateAI() {
  await handleGenerate(true)
}

async function handleRunAll() {
  const enabled = test.testCases.value.filter(c => c.enabled)
  if (enabled.length === 0) {
    showToast('没有启用的测试用例', 'error')
    return
  }
  try {
    const { report } = await test.runAll()
    showReportDetail.value = true
    showToast(`运行完成: ${report.passedCases}/${report.totalCases} 通过`)
  } catch (e: any) {
    showToast(`运行失败: ${e.message}`, 'error')
  }
}

async function handleRunGroup(groupId: string) {
  const enabled = test.testCases.value.filter(c => c.groupId === groupId && c.enabled)
  if (enabled.length === 0) {
    showToast('该分组没有启用的用例', 'error')
    return
  }
  runProgress.value = { groupId, current: 0, total: enabled.length }
  try {
    const { report } = await test.runGroup(groupId, (idx) => { runProgress.value = { ...runProgress.value, current: idx } })
    showReportDetail.value = true
    showToast(`组运行完成: ${report.passedCases}/${report.totalCases} 通过`)
  } catch (e: any) {
    showToast(`运行失败: ${e.message}`, 'error')
  } finally {
    runProgress.value = { groupId: '', current: 0, total: 0 }
  }
}

async function handleRunSingle(tc: ApiTestCase) {
  try {
    const result = await test.runSingle(tc)
    activeDetailTab.value = 'result'
    showToast(result.passed ? '用例通过' : '用例失败', result.passed ? 'success' : 'error')
  } catch (e: any) {
    showToast(`运行失败: ${e.message}`, 'error')
  }
}

async function handleAddGroup() {
  if (!newGroupName.value.trim()) return
  await test.addGroup(newGroupName.value.trim(), newGroupColor.value)
  newGroupName.value = ''
  showToast('分组已创建')
}

async function handleUpdateGroup(group: ApiTestGroup) {
  await test.updateGroup(group)
}

async function handleDeleteGroup(id: string) {
  await test.deleteGroup(id)
  showToast('分组已删除')
}

async function handleClearGroupCases(group: ApiTestGroup) {
  batchDeleteConfirm.value = group
}

async function handleBatchDeleteConfirm() {
  if (!batchDeleteConfirm.value) return
  await test.deleteCasesByGroup(batchDeleteConfirm.value.id)
  if (selectedCase.value && selectedCase.value.groupId === batchDeleteConfirm.value.id) {
    selectedCase.value = null
    activeDetailTab.value = 'overview'
  }
  showToast(`已清空分组「${batchDeleteConfirm.value.name}」下的所有用例`)
  batchDeleteConfirm.value = null
}

async function handleExportReport(reportId: string) {
  try {
    await test.exportReport(reportId)
    showToast('报告已导出')
  } catch (e: any) {
    showToast(`导出失败: ${e.message}`, 'error')
  }
}

function handleOpenGlobalAuth() {
  authHeaders.value = test.globalAuthHeaders.value.map(h => ({ ...h }))
  if (authHeaders.value.length === 0) authHeaders.value = [{ name: '', value: '' }]
  showGlobalAuth.value = true
}

function handleClearAuth() {
  authHeaders.value = [{ name: '', value: '' }]
}

async function handleSaveAuth() {
  await test.saveGlobalAuthHeader(authHeaders.value.filter(h => h.name.trim()))
  showToast('全局认证已保存，下次运行时生效')
  showGlobalAuth.value = false
}

function handleOpenDomainKeywords() {
  domainKeywordsText.value = test.domainKeywords.value.join('\n')
  showDomainKeywords.value = true
}

async function handleSaveDomainKeywords() {
  const keywords = domainKeywordsText.value.split('\n').map(s => s.trim()).filter(Boolean)
  await test.saveDomainKeywords(keywords)
  showToast('域名关键字已保存')
  showDomainKeywords.value = false
}

function showDeleteConfirm(tc: ApiTestCase) {
  deleteConfirm.value = tc
}

async function handleDeleteCase() {
  if (!deleteConfirm.value) return
  await test.deleteTestCase(deleteConfirm.value.id)
  if (selectedCase.value?.id === deleteConfirm.value.id) {
    selectedCase.value = null
    activeDetailTab.value = 'overview'
  }
  showToast('用例已删除')
  deleteConfirm.value = null
}

async function handleViewReport(report: ApiTestReport) {
  selectedReportResult.value = null
  await test.loadReport(report.id)
  showReportDetail.value = true
}

async function handleDeleteReport(id: string) {
  await test.deleteReport(id)
  showToast('报告已删除')
}

async function handleDeleteEndpoint(groupId: string, method: string, path: string) {
  try {
    await test.deleteEndpointCases(groupId, method, path)
    if (selectedCase.value && selectedCase.value.groupId === groupId && selectedCase.value.method === method && selectedCase.value.path === path) {
      selectedCase.value = null
      activeDetailTab.value = 'overview'
    }
    showToast(`已删除接口 ${method} ${path} 下的所有用例`)
  } catch (e: any) {
    showToast(`删除失败: ${e.message}`, 'error')
  }
}

onMounted(async () => {
  await test.loadAll()
  await test.loadReports()
})
</script>

<style scoped>
.glass-panel {
  backdrop-filter: blur(60px);
  -webkit-backdrop-filter: blur(60px);
}
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
.fade-scale-enter-active,
.fade-scale-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}
.fade-scale-enter-from,
.fade-scale-leave-to {
  opacity: 0;
  transform: scale(0.95) translateY(-4px);
}
</style>
