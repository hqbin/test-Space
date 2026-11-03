<template>
  <div class="flex flex-col gap-3 flex-1 min-h-0 overflow-hidden pb-3">
    <!-- 控制栏 -->
    <div class="glass-panel rounded-xl px-4 py-2.5 flex items-center gap-3 shrink-0 flex-wrap">
      <button
        class="glass-button px-3 py-1.5 rounded-lg flex items-center gap-1.5 font-label-md text-label-md select-none"
        :class="isRunning ? 'text-error' : ''"
        :disabled="!serial"
        @click="isRunning ? stop() : start()">
        <span class="material-symbols-outlined text-[15px]"
          :style="{ fontVariationSettings: `'FILL' ${isRunning ? 1 : 0}` }">
          {{ isRunning ? 'stop_circle' : 'play_circle' }}
        </span>
        <span class="text-[12px] font-semibold">{{ isRunning ? '停止分析' : '开始分析' }}</span>
        <span v-if="isRunning" class="w-2 h-2 rounded-full bg-error animate-pulse ml-0.5"></span>
      </button>

      <button
        class="glass-button px-3 py-1.5 rounded-lg flex items-center gap-1.5 font-label-md text-label-md select-none"
        :disabled="!isRunning && totalEvents === 0"
        @click="clear">
        <span class="material-symbols-outlined text-[15px]">clear_all</span>
        <span class="text-[12px] font-semibold">清空面板</span>
      </button>

      <button
        class="glass-button px-3 py-1.5 rounded-lg flex items-center gap-1.5 font-label-md text-label-md select-none"
        :disabled="!serial || clearingDevice"
        @click="clearDeviceLog">
        <span v-if="clearingDevice" class="w-3.5 h-3.5 border-2 border-current border-t-transparent rounded-full animate-spin"></span>
        <span v-else class="material-symbols-outlined text-[15px]">delete_sweep</span>
        <span class="text-[12px] font-semibold">清空设备日志</span>
      </button>

      <div class="h-4 w-[1px] bg-glass-border-dark shrink-0"></div>

      <div class="flex items-center gap-3 font-caption text-caption text-on-surface-variant select-none flex-wrap">
        <span class="flex items-center gap-1">
          <span class="material-symbols-outlined text-[13px]">event_note</span>
          {{ totalEvents }} 条事件
        </span>
        <span class="flex items-center gap-1">
          <span class="material-symbols-outlined text-[13px]">http</span>
          {{ apiRequests.length }} 个接口
        </span>
        <span class="flex items-center gap-1.5">
          <span class="w-1.5 h-1.5 rounded-full" :class="okCount > 0 ? 'bg-success-indicator' : 'bg-outline-variant/40'"></span>{{ okCount }} 正常
          <span class="w-1.5 h-1.5 rounded-full ml-1" :class="errorCount > 0 ? 'bg-error' : 'bg-outline-variant/40'"></span>{{ errorCount }} 异常
          <span class="w-1.5 h-1.5 rounded-full ml-1" :class="warnCount > 0 ? 'bg-yellow-400' : 'bg-outline-variant/40'"></span>{{ warnCount }} 警告
        </span>
      </div>

      <!-- 事件流过滤（仅在全局视图下显示） -->
      <div v-if="activeView === 'all'" class="ml-auto flex items-center gap-2 flex-wrap">
        <input v-model="eventSearch"
          class="bg-white/40 border border-outline-variant/40 rounded-lg px-3 py-1 font-caption text-[11px] text-on-surface placeholder:text-on-surface-variant/40 focus:outline-none focus:ring-1 focus:ring-secondary/30 select-text w-36"
          placeholder="搜索事件…" />
        <div class="h-3 w-[1px] bg-glass-border-dark shrink-0"></div>
        <span class="font-caption text-[11px] text-on-surface-variant/60 select-none flex items-center gap-1">
          <span class="material-symbols-outlined text-[12px]">filter_list</span>筛选
        </span>
        <button v-for="f in filters" :key="f.key"
          class="glass-hover rounded-md px-2 py-0.5 flex items-center gap-1 select-none"
          :class="activeFilter === f.key ? 'glass-active font-semibold' : 'text-on-surface-variant'"
          @click="activeFilter = f.key">
          <span class="w-1.5 h-1.5 rounded-full shrink-0" :class="f.dotClass"></span>
          <span class="text-[11px]">{{ f.label }}</span>
        </button>
      </div>
      <!-- 接口面板搜索过滤 -->
      <div v-else-if="activeView === 'api'" class="ml-auto flex items-center gap-2 flex-wrap">
        <input v-model="apiSearch"
          class="bg-white/40 border border-outline-variant/40 rounded-lg px-3 py-1 font-caption text-[11px] text-on-surface placeholder:text-on-surface-variant/40 focus:outline-none focus:ring-1 focus:ring-secondary/30 select-text w-44"
          placeholder="搜索路径或域名…" />
        <div class="flex gap-1">
          <button v-for="m in httpMethods" :key="m"
            class="text-[9px] px-1.5 py-0.5 rounded font-mono select-none transition-colors"
            :class="apiMethodFilter === m ? methodBadgeActiveClass(m) : 'bg-outline-variant/20 text-on-surface-variant hover:bg-outline-variant/30'"
            @click="apiMethodFilter = apiMethodFilter === m ? null : m">{{ m }}</button>
        </div>
      </div>
    </div>

    <!-- 设备清空结果提示 -->
    <Transition name="fade">
      <div v-if="deviceClearToast.show"
        class="fixed bottom-8 left-1/2 -translate-x-1/2 z-50 glass-panel rounded-full px-5 py-2.5 flex items-center gap-2 select-none">
        <span class="material-symbols-outlined text-[18px]"
          :class="deviceClearToast.ok ? 'text-success-indicator' : 'text-error'"
          :style="{ fontVariationSettings: `'FILL' 1` }">
          {{ deviceClearToast.ok ? 'check_circle' : 'error' }}
        </span>
        <span class="font-body-md text-body-md text-on-surface">{{ deviceClearToast.msg }}</span>
      </div>
    </Transition>

    <!-- 主体 -->
    <div class="flex gap-3 flex-1 min-h-0 overflow-hidden">

      <!-- 左：模块列表 -->
      <div class="w-[380px] shrink-0 overflow-y-auto custom-scrollbar flex flex-col gap-1.5 pr-1">

        <!-- 接口监控特殊卡片（最顶部） -->
        <div
          class="glass-panel rounded-xl px-3 py-2.5 flex items-center gap-2.5 shrink-0 cursor-pointer transition-all glass-hover"
          :class="activeView === 'api' ? 'ring-1 ring-secondary/50' : ''"
          @click="selectView('api')">
          <div class="w-[3px] self-stretch rounded-full shrink-0"
            :class="apiRequests.length > 0 ? 'bg-secondary' : 'bg-outline-variant/30'"></div>
          <span class="material-symbols-outlined text-[15px] shrink-0"
            :class="apiRequests.length > 0 ? 'text-secondary' : 'text-outline-variant/50'"
            :style="{ fontVariationSettings: `'FILL' ${apiRequests.length > 0 ? 1 : 0}` }">http</span>
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-1.5">
              <span class="font-label-md text-[11px] font-semibold text-on-surface select-none">接口监控</span>
              <span v-if="apiRequests.length > 0"
                class="text-[9px] font-mono px-1 py-px rounded select-none bg-secondary/15 text-secondary shrink-0">
                {{ apiRequests.length }}
              </span>
            </div>
            <p class="font-caption text-[10px] mt-0.5 select-none line-clamp-1 text-on-surface-variant">
              {{ apiRequests.length === 0 ? '等待捕获接口请求…' : latestApiSummary }}
            </p>
          </div>
          <div class="w-2 h-2 rounded-full shrink-0 flex-shrink-0"
            :class="activeView === 'api' ? 'bg-secondary' : (apiRequests.length > 0 ? 'bg-secondary/50' : 'bg-outline-variant/30')"></div>
        </div>

        <!-- 分隔线 -->
        <div class="flex items-center gap-2 px-1 py-0.5 shrink-0">
          <div class="h-[1px] flex-1 bg-outline-variant/20"></div>
          <span class="font-caption text-[9px] text-on-surface-variant/40 select-none">{{ moduleList.length }} 个模块</span>
          <div class="h-[1px] flex-1 bg-outline-variant/20"></div>
        </div>

        <!-- 16 个模块卡片 -->
        <div
          v-for="mod in moduleList" :key="mod.key"
          class="glass-panel rounded-xl px-3 py-2.5 flex items-center gap-2.5 shrink-0 transition-all cursor-pointer glass-hover"
          :class="activeView === 'module' && activeModuleKey === mod.key ? 'ring-1 ring-secondary/40' : ''"
          @click="selectModule(mod.key)">
          <div class="w-[3px] self-stretch rounded-full shrink-0" :class="statusBarClass(mod.status)"></div>
          <span class="material-symbols-outlined text-[15px] shrink-0"
            :class="mod.status === 'unknown' ? 'text-outline-variant/40' : 'text-on-surface-variant'"
            :style="{ fontVariationSettings: `'FILL' ${mod.status === 'ok' ? 1 : 0}` }">{{ mod.icon }}</span>
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-1.5 flex-wrap">
              <span class="font-label-md text-[11px] font-semibold text-on-surface select-none">{{ mod.name }}</span>
              <span v-if="mod.eventCount > 0"
                class="text-[9px] font-mono px-1 py-px rounded select-none shrink-0"
                :class="statusBadgeClass(mod.status)">{{ mod.eventCount }}</span>
              <span v-if="mod.apiCount > 0"
                class="text-[9px] font-mono px-1 py-px rounded select-none shrink-0 bg-secondary/15 text-secondary">
                {{ mod.apiCount }} 接口
              </span>
            </div>
            <p class="font-caption text-[10px] mt-0.5 select-none line-clamp-1"
              :class="mod.status === 'unknown' ? 'text-on-surface-variant/40' : 'text-on-surface-variant'">
              {{ mod.summary }}
            </p>
          </div>
          <div class="flex flex-col items-end gap-0.5 shrink-0">
            <div class="w-2 h-2 rounded-full" :class="statusDotClass(mod.status)"></div>
            <span v-if="mod.lastUpdated" class="font-mono text-[8px] text-on-surface-variant/40 select-none whitespace-nowrap">
              {{ mod.lastUpdated.substring(6) }}
            </span>
          </div>
        </div>

        <!-- 空态 -->
        <div v-if="!serial" class="text-center py-10 text-on-surface-variant/40 font-caption select-none flex flex-col items-center gap-2">
          <span class="material-symbols-outlined text-[32px] opacity-30">device_unknown</span>
          请先连接设备
        </div>
        <div v-else-if="!isRunning && totalEvents === 0"
          class="text-center py-10 text-on-surface-variant/40 font-caption select-none flex flex-col items-center gap-2">
          <span class="material-symbols-outlined text-[32px] opacity-30">play_circle</span>
          点击「开始分析」开始监控
        </div>
      </div>

      <!-- 右：内容区 -->
      <div class="flex-1 glass-panel rounded-xl flex flex-col min-h-0 overflow-hidden">

        <!-- ① 接口面板 -->
        <template v-if="activeView === 'api'">
          <div class="px-3 py-2 flex items-center gap-2 shrink-0 border-b border-outline-variant/15">
            <span class="material-symbols-outlined text-[14px] text-secondary" :style="{ fontVariationSettings: `'FILL' 1` }">http</span>
            <span class="font-label-md text-[11px] font-semibold text-on-surface select-none">接口监控</span>
            <span class="ml-auto font-caption text-[10px] text-on-surface-variant/50 select-none">{{ filteredApis.length }} 条</span>
          </div>

          <div v-if="filteredApis.length === 0"
            class="flex-1 flex items-center justify-center text-on-surface-variant/30 flex-col gap-2 select-none">
            <span class="material-symbols-outlined text-[36px] opacity-30">{{ isRunning ? 'hourglass_empty' : 'http' }}</span>
            <span class="font-caption text-[11px]">{{ isRunning ? '等待捕获接口请求…' : '暂无接口记录' }}</span>
          </div>

          <div v-else class="flex-1 overflow-y-auto custom-scrollbar">
            <div v-for="api in filteredApis" :key="api.id"
              class="px-3 py-2.5 border-b border-outline-variant/10 last:border-0 hover:bg-white/15 transition-colors cursor-pointer"
              @click="openApiModal(api)">
              <div class="flex items-center gap-1.5 flex-wrap">
                <span class="text-[9px] font-mono px-1.5 py-0.5 rounded font-semibold shrink-0" :class="methodBadgeClass(api.method)">{{ api.method }}</span>
                <span v-if="api.responseStatus" class="text-[9px] font-mono px-1 py-0.5 rounded shrink-0"
                  :class="api.responseStatus >= 400 ? 'bg-error/15 text-error' : 'bg-success-indicator/15 text-green-700'">{{ api.responseStatus }}</span>
                <span v-if="api.durationMs" class="text-[9px] font-mono text-on-surface-variant/60 shrink-0">{{ api.durationMs }}ms</span>
                <span class="ml-auto font-mono text-[9px] text-on-surface-variant/40 shrink-0">{{ api.time.substring(6) }}</span>
              </div>
              <div class="mt-1 flex items-baseline gap-1.5">
                <span class="font-caption text-[10px] text-on-surface-variant/60 shrink-0">{{ api.domain }}</span>
                <span class="font-mono text-[11px] text-on-surface truncate">{{ api.path }}</span>
              </div>
              <div v-if="api.queryParams.length > 0" class="mt-1 flex flex-wrap gap-1">
                <span v-for="p in api.queryParams.slice(0, 3)" :key="p.key"
                  class="text-[9px] font-mono bg-black/5 px-1.5 py-0.5 rounded text-on-surface-variant/70 select-text">
                  {{ p.key }}={{ p.value.substring(0, 20) }}{{ p.value.length > 20 ? '…' : '' }}
                </span>
                <span v-if="api.queryParams.length > 3" class="text-[9px] font-mono text-on-surface-variant/40">
                  +{{ api.queryParams.length - 3 }} 个
                </span>
              </div>
            </div>
          </div>
        </template>

        <!-- ② 模块混合视图 -->
        <template v-else-if="activeView === 'module' && activeModuleKey">
          <div class="px-3 py-2 flex items-center gap-2 shrink-0 border-b border-outline-variant/15">
            <span class="material-symbols-outlined text-[14px] text-on-surface-variant">
              {{ modules[activeModuleKey]?.icon }}
            </span>
            <span class="font-label-md text-[11px] font-semibold text-on-surface select-none">
              {{ modules[activeModuleKey]?.name }}
            </span>
            <span v-if="moduleEvents.length > 0"
              class="text-[9px] font-mono px-1 py-px rounded select-none"
              :class="statusBadgeClass(modules[activeModuleKey]?.status || 'unknown')">
              {{ moduleEvents.length }} 事件
            </span>
            <span v-if="moduleApis.length > 0"
              class="text-[9px] font-mono px-1 py-px rounded select-none bg-secondary/15 text-secondary">
              {{ moduleApis.length }} 接口
            </span>
            <button class="ml-auto text-on-surface-variant hover:text-on-surface no-border" @click="selectView('all')">
              <span class="material-symbols-outlined text-[14px]">close</span>
            </button>
          </div>

          <div class="flex-1 overflow-y-auto custom-scrollbar">
            <!-- 接口记录区 -->
            <div v-if="moduleApis.length > 0" class="border-b border-outline-variant/15">
              <button
                class="w-full px-3 py-2 flex items-center gap-2 hover:bg-white/10 transition-colors select-none"
                @click="moduleApiExpanded = !moduleApiExpanded">
                <span class="material-symbols-outlined text-[13px] text-secondary">http</span>
                <span class="font-caption text-[10px] font-semibold text-secondary">接口请求 ({{ moduleApis.length }})</span>
                <span class="material-symbols-outlined text-[13px] text-on-surface-variant ml-auto transition-transform"
                  :class="moduleApiExpanded ? 'rotate-180' : ''">expand_more</span>
              </button>
              <div v-if="moduleApiExpanded">
                <div v-for="api in moduleApis" :key="api.id"
                  class="px-3 py-2 border-t border-outline-variant/8 hover:bg-white/15 transition-colors cursor-pointer"
                  @click="openApiModal(api)">
                  <div class="flex items-center gap-1.5">
                    <span class="text-[9px] font-mono px-1.5 py-0.5 rounded font-semibold shrink-0" :class="methodBadgeClass(api.method)">{{ api.method }}</span>
                    <span v-if="api.responseStatus" class="text-[9px] font-mono px-1 py-0.5 rounded shrink-0"
                      :class="api.responseStatus >= 400 ? 'bg-error/15 text-error' : 'bg-success-indicator/15 text-green-700'">{{ api.responseStatus }}</span>
                    <span v-if="api.durationMs" class="text-[9px] font-mono text-on-surface-variant/60 shrink-0">{{ api.durationMs }}ms</span>
                    <span class="font-mono text-[10px] text-on-surface truncate flex-1 ml-1">{{ api.path }}</span>
                    <span class="font-mono text-[9px] text-on-surface-variant/40 shrink-0">{{ api.time.substring(6) }}</span>
                  </div>
                  <div v-if="api.queryParams.length > 0" class="mt-0.5 flex flex-wrap gap-1">
                    <span v-for="p in api.queryParams.slice(0, 2)" :key="p.key"
                      class="text-[9px] font-mono text-on-surface-variant/60 select-text">
                      {{ p.key }}={{ p.value.substring(0, 20) }}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <!-- 事件日志区 -->
            <div>
              <div class="px-3 py-2 flex items-center gap-2 select-none border-b border-outline-variant/8">
                <span class="material-symbols-outlined text-[13px] text-on-surface-variant">receipt_long</span>
                <span class="font-caption text-[10px] font-semibold text-on-surface-variant">事件日志 ({{ moduleEvents.length }})</span>
              </div>
              <div v-if="moduleEvents.length === 0"
                class="py-8 text-center text-on-surface-variant/30 font-caption text-[11px] select-none">
                {{ isRunning ? '等待事件…' : '暂无事件' }}
              </div>
              <div v-for="event in moduleEvents" :key="event.id">
                <div
                  class="flex items-start gap-2 px-3 py-1.5 hover:bg-white/15 transition-colors cursor-pointer border-b border-outline-variant/5 last:border-0"
                  @click="expandedRaw = expandedRaw === event.id ? null : event.id">
                  <span class="material-symbols-outlined text-[12px] shrink-0 mt-0.5"
                    :class="eventIconClass(event.status)" :style="{ fontVariationSettings: `'FILL' 1` }">{{ eventIcon(event.status) }}</span>
                  <span class="font-mono text-[9px] text-on-surface-variant/40 shrink-0 mt-0.5 w-[54px] whitespace-nowrap">{{ event.time.substring(6, 14) }}</span>
                  <span class="font-caption text-[11px] text-on-surface flex-1 min-w-0 select-text leading-relaxed">{{ event.summary }}</span>
                  <span class="material-symbols-outlined text-[11px] text-on-surface-variant/40 shrink-0 mt-0.5">
                    {{ expandedRaw === event.id ? 'expand_less' : 'expand_more' }}
                  </span>
                </div>
                <div v-if="expandedRaw === event.id" class="px-3 pb-2 pt-1 bg-black/5">
                  <pre class="font-mono text-[10px] text-on-surface-variant whitespace-pre-wrap break-all select-text leading-relaxed max-h-[240px] overflow-y-auto custom-scrollbar">{{ event.raw }}</pre>
                </div>
              </div>
            </div>
          </div>
        </template>

        <!-- ③ 全部事件流（默认） -->
        <template v-else>
          <div class="px-3 py-2 flex items-center gap-2 shrink-0 border-b border-outline-variant/15">
            <span class="material-symbols-outlined text-[14px] text-on-surface-variant">receipt_long</span>
            <span class="font-label-md text-[11px] font-semibold text-on-surface select-none">实时事件流</span>
            <span class="ml-auto font-caption text-[10px] text-on-surface-variant/50 select-none">{{ filteredEvents.length }} 条</span>
          </div>

          <div v-if="filteredEvents.length === 0"
            class="flex-1 flex items-center justify-center text-on-surface-variant/30 flex-col gap-2 select-none">
            <span class="material-symbols-outlined text-[36px] opacity-30">{{ isRunning ? 'hourglass_empty' : 'inbox' }}</span>
            <span class="font-caption text-[11px]">{{ isRunning ? '等待匹配到事件…' : '暂无事件' }}</span>
          </div>

          <div v-else class="flex-1 overflow-y-auto custom-scrollbar">
            <div v-for="event in filteredEvents" :key="event.id">
              <div
                class="flex items-start gap-2 px-3 py-1.5 hover:bg-white/15 transition-colors cursor-pointer border-b border-outline-variant/5 last:border-0"
                @click="expandedRaw = expandedRaw === event.id ? null : event.id">
                <span class="material-symbols-outlined text-[12px] shrink-0 mt-0.5"
                  :class="eventIconClass(event.status)" :style="{ fontVariationSettings: `'FILL' 1` }">{{ eventIcon(event.status) }}</span>
                <span class="font-mono text-[9px] text-on-surface-variant/40 shrink-0 mt-0.5 w-[54px] whitespace-nowrap">{{ event.time.substring(6, 14) }}</span>
                <span class="text-[9px] px-1 py-px rounded-sm shrink-0 font-caption mt-0.5 max-w-[60px] truncate select-none"
                  :class="statusBadgeClass(event.status)">{{ event.moduleName }}</span>
                <span class="font-caption text-[11px] text-on-surface flex-1 min-w-0 select-text leading-relaxed pl-0.5">{{ event.summary }}</span>
                <span class="material-symbols-outlined text-[11px] text-on-surface-variant/40 shrink-0 mt-0.5">
                  {{ expandedRaw === event.id ? 'expand_less' : 'expand_more' }}
                </span>
              </div>
              <div v-if="expandedRaw === event.id" class="px-3 pb-2 pt-1 bg-black/5">
                <pre class="font-mono text-[10px] text-on-surface-variant whitespace-pre-wrap break-all select-text leading-relaxed max-h-[240px] overflow-y-auto custom-scrollbar">{{ event.raw }}</pre>
              </div>
            </div>
          </div>
        </template>
      </div>
    </div>

    <!-- 接口详情弹窗 -->
    <Teleport to="body">
      <Transition name="fade">
        <div v-if="apiModal" class="fixed inset-0 z-50 flex items-center justify-center" @click.self="apiModal = null">
          <div class="absolute inset-0 bg-black/30 backdrop-blur-sm"></div>
          <div class="glass-panel rounded-[2rem] p-6 w-full max-w-2xl relative z-10 bg-white/60 max-h-[82vh] flex flex-col">
            <!-- 标题栏 -->
            <div class="flex justify-between items-center mb-4 shrink-0">
              <h3 class="font-label-md text-label-md text-on-surface font-semibold flex items-center gap-2 select-none min-w-0">
                <span class="text-[10px] font-mono px-2 py-1 rounded font-semibold shrink-0"
                  :class="methodBadgeClass(apiModal.method)">{{ apiModal.method }}</span>
                <span class="truncate">{{ apiModal.path }}</span>
              </h3>
              <button class="glass-button p-1 rounded select-none shrink-0 ml-2" @click="apiModal = null">
                <span class="material-symbols-outlined text-[18px]">close</span>
              </button>
            </div>

            <div class="flex-1 min-h-0 overflow-y-auto custom-scrollbar space-y-3">
              <!-- 状态行 -->
              <div class="flex items-center gap-3 flex-wrap">
                <span v-if="apiModal.responseStatus" class="text-[11px] font-mono px-2 py-0.5 rounded font-semibold"
                  :class="apiModal.responseStatus >= 400 ? 'bg-error/15 text-error' : 'bg-success-indicator/15 text-green-700'">
                  {{ apiModal.responseStatus }}
                </span>
                <span v-if="apiModal.durationMs" class="text-[11px] font-mono text-on-surface-variant">耗时 {{ apiModal.durationMs }} ms</span>
                <span class="text-[11px] font-mono text-on-surface-variant/60">{{ apiModal.time }}</span>
                <span v-if="apiModal.moduleName" class="text-[10px] px-1.5 py-0.5 rounded-full bg-secondary/15 text-secondary font-caption select-none">
                  {{ apiModal.moduleName }}
                </span>
              </div>

              <!-- 完整 URL -->
              <div class="bg-black/5 rounded-xl p-3">
                <div class="text-[10px] font-semibold text-on-surface-variant/60 mb-2 select-none">完整请求 URL</div>
                <a v-if="apiModal.url" :href="apiModal.url" target="_blank" rel="noopener noreferrer"
                  class="font-mono text-[11px] text-secondary break-all select-text hover:underline">{{ apiModal.url }}</a>
                <span v-else class="font-mono text-[11px] text-on-surface-variant/60">（内部接口，无 URL）</span>
              </div>

              <!-- Query 参数 -->
              <div v-if="apiModal.queryParams.length > 0" class="bg-black/5 rounded-xl p-3">
                <div class="text-[10px] font-semibold text-on-surface-variant/60 mb-2 select-none">
                  请求参数 ({{ apiModal.queryParams.length }})
                </div>
                <div class="space-y-1.5">
                  <div v-for="p in apiModal.queryParams" :key="p.key"
                    class="grid gap-3" style="grid-template-columns: minmax(80px,160px) 1fr">
                    <span class="font-mono text-[10px] text-secondary font-semibold select-text truncate">{{ p.key }}</span>
                    <span class="font-mono text-[10px] text-on-surface break-all select-text">{{ p.value }}</span>
                  </div>
                </div>
              </div>

              <!-- Request Headers（可折叠） -->
              <div v-if="apiModal.requestHeaders.length > 0" class="bg-black/5 rounded-xl overflow-hidden">
                <button class="w-full px-3 py-2 flex items-center gap-2 hover:bg-black/5 transition-colors select-none"
                  @click="showReqHeaders = !showReqHeaders">
                  <span class="text-[10px] font-semibold text-on-surface-variant/60">
                    请求 Headers ({{ apiModal.requestHeaders.length }})
                  </span>
                  <span class="material-symbols-outlined text-[13px] text-on-surface-variant/40 ml-auto transition-transform"
                    :class="showReqHeaders ? 'rotate-180' : ''">expand_more</span>
                </button>
                <div v-if="showReqHeaders" class="px-3 pb-3 space-y-1">
                  <div v-for="h in apiModal.requestHeaders" :key="h.key"
                    class="grid gap-3" style="grid-template-columns: minmax(80px,160px) 1fr">
                    <span class="font-mono text-[10px] text-secondary/80 select-text truncate">{{ h.key }}</span>
                    <span class="font-mono text-[10px] text-on-surface-variant break-all select-text">{{ h.value }}</span>
                  </div>
                </div>
              </div>

              <!-- Request Body -->
              <div v-if="apiModal.requestBody" class="bg-black/5 rounded-xl p-3">
                <div class="text-[10px] font-semibold text-on-surface-variant/60 mb-2 select-none">请求体</div>
                <pre class="font-mono text-[10px] text-on-surface-variant whitespace-pre-wrap break-all select-text max-h-40 overflow-y-auto">{{ formatJson(apiModal.requestBody) }}</pre>
              </div>

              <!-- Response Body -->
              <div v-if="apiModal.responseBody" class="bg-black/5 rounded-xl p-3">
                <div class="text-[10px] font-semibold text-on-surface-variant/60 mb-2 select-none">响应体</div>
                <pre class="font-mono text-[10px] text-on-surface-variant whitespace-pre-wrap break-all select-text max-h-48 overflow-y-auto custom-scrollbar">{{ formatJson(apiModal.responseBody) }}</pre>
              </div>

              <!-- 原始日志 -->
              <div class="bg-black/5 rounded-xl p-3">
                <div class="text-[10px] font-semibold text-on-surface-variant/60 mb-2 select-none">原始日志</div>
                <pre class="font-mono text-[10px] text-on-surface-variant/70 whitespace-pre-wrap break-all select-text max-h-32 overflow-y-auto">{{ apiModal.raw }}</pre>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, type Ref } from 'vue'
import { useLogAnalysis, MODULE_ORDER, type ModuleStatus, type ApiRequest } from '@/composables/useLogAnalysis'

const props = defineProps<{ serial: string | null | undefined }>()

const serialRef = computed(() => props.serial) as Ref<string | null | undefined>
const { isRunning, totalEvents, modules, events, apiRequests, start, stop, clear, getModuleApis } = useLogAnalysis(serialRef)

watch(() => props.serial, (val, old) => { if (val !== old && isRunning.value) stop() })

// ── 视图状态 ──
// activeView: 'all' | 'api' | 'module'
const activeView = ref<'all' | 'api' | 'module'>('all')
const activeModuleKey = ref<string | null>(null)
const expandedRaw = ref<number | null>(null)
const moduleApiExpanded = ref(true)
const apiModal = ref<ApiRequest | null>(null)
const showReqHeaders = ref(false)
const apiSearch = ref('')
const apiMethodFilter = ref<string | null>(null)
const activeFilter = ref<'all' | 'ok' | 'error' | 'warning' | 'info'>('all')
const eventSearch = ref('')
const clearingDevice = ref(false)
const deviceClearToast = ref<{ show: boolean; ok: boolean; msg: string }>({ show: false, ok: true, msg: '' })
let deviceClearToastTimer: number | null = null

async function clearDeviceLog() {
  if (!props.serial || clearingDevice.value) return
  clearingDevice.value = true
  try {
    const { invoke } = await import('@tauri-apps/api/core')
    await invoke('adb_shell', { serial: props.serial, command: 'logcat -c' })
    showDeviceClearToast(true, '设备日志已清空')
  } catch {
    showDeviceClearToast(false, '清空失败，请检查设备连接')
  } finally {
    clearingDevice.value = false
  }
}

function showDeviceClearToast(ok: boolean, msg: string) {
  if (deviceClearToastTimer !== null) clearTimeout(deviceClearToastTimer)
  deviceClearToast.value = { show: true, ok, msg }
  deviceClearToastTimer = window.setTimeout(() => { deviceClearToast.value.show = false }, 2500)
}

const filters = [
  { key: 'all' as const, label: '全部', dotClass: 'bg-on-surface-variant/30' },
  { key: 'ok' as const, label: '正常', dotClass: 'bg-success-indicator' },
  { key: 'error' as const, label: '异常', dotClass: 'bg-error' },
  { key: 'warning' as const, label: '警告', dotClass: 'bg-yellow-400' },
  { key: 'info' as const, label: '信息', dotClass: 'bg-secondary' },
]
const httpMethods = ['GET', 'POST', 'PUT', 'DELETE']

function selectView(v: 'all' | 'api') {
  activeView.value = v
  activeModuleKey.value = null
  expandedRaw.value = null
}

function selectModule(key: string) {
  if (activeView.value === 'module' && activeModuleKey.value === key) {
    activeView.value = 'all'
    activeModuleKey.value = null
  } else {
    activeView.value = 'module'
    activeModuleKey.value = key
    expandedRaw.value = null
    moduleApiExpanded.value = true
  }
}

function openApiModal(api: ApiRequest) {
  apiModal.value = api
  showReqHeaders.value = false
}

// ── 计算 ──
const moduleList = computed(() => MODULE_ORDER.map(k => modules.value[k]).filter(Boolean))

const okCount = computed(() => moduleList.value.filter(m => m.status === 'ok').length)
const errorCount = computed(() => moduleList.value.filter(m => m.status === 'error').length)
const warnCount = computed(() => moduleList.value.filter(m => m.status === 'warning').length)

const filteredEvents = computed(() => {
  let list = events.value
  if (activeFilter.value !== 'all') list = list.filter(e => e.status === activeFilter.value)
  if (eventSearch.value.trim()) {
    const q = eventSearch.value.trim().toLowerCase()
    list = list.filter(e => e.summary.toLowerCase().includes(q) || e.raw.toLowerCase().includes(q))
  }
  return list
})

const filteredApis = computed(() => {
  let list = apiRequests.value
  if (apiMethodFilter.value) list = list.filter(a => a.method === apiMethodFilter.value)
  if (apiSearch.value.trim()) {
    const q = apiSearch.value.trim().toLowerCase()
    list = list.filter(a => a.url.toLowerCase().includes(q) || a.path.toLowerCase().includes(q) || a.domain.toLowerCase().includes(q))
  }
  return list
})

const moduleEvents = computed(() => activeModuleKey.value ? events.value.filter(e => e.moduleKey === activeModuleKey.value) : [])
const moduleApis = computed(() => activeModuleKey.value ? getModuleApis(activeModuleKey.value) : [])

const latestApiSummary = computed(() => {
  const first = apiRequests.value[0]
  if (!first) return '等待捕获…'
  return `${first.method} ${first.path.substring(0, 36)}${first.path.length > 36 ? '…' : ''}`
})

// ── 工具函数 ──
function formatJson(s: string): string {
  try { return JSON.stringify(JSON.parse(s), null, 2) } catch { return s }
}
function statusBarClass(s: ModuleStatus) {
  return { ok: 'bg-success-indicator', error: 'bg-error', warning: 'bg-yellow-400', info: 'bg-secondary', unknown: 'bg-outline-variant/20' }[s]
}
function statusDotClass(s: ModuleStatus) {
  return { ok: 'bg-success-indicator', error: 'bg-error animate-pulse', warning: 'bg-yellow-400', info: 'bg-secondary', unknown: 'bg-outline-variant/30' }[s]
}
function statusBadgeClass(s: ModuleStatus) {
  return { ok: 'bg-success-indicator/15 text-green-700', error: 'bg-error/15 text-error', warning: 'bg-yellow-400/20 text-yellow-700', info: 'bg-secondary/15 text-secondary', unknown: 'bg-outline-variant/15 text-on-surface-variant' }[s]
}
function eventIcon(s: ModuleStatus) {
  return { ok: 'check_circle', error: 'error', warning: 'warning', info: 'info', unknown: 'radio_button_unchecked' }[s]
}
function eventIconClass(s: ModuleStatus) {
  return { ok: 'text-success-indicator', error: 'text-error', warning: 'text-yellow-500', info: 'text-secondary', unknown: 'text-outline-variant' }[s]
}
function methodBadgeClass(method: string) {
  const map: Record<string, string> = { GET: 'bg-success-indicator/15 text-green-700', POST: 'bg-secondary/15 text-secondary', PUT: 'bg-yellow-400/20 text-yellow-700', DELETE: 'bg-error/15 text-error', PATCH: 'bg-purple-400/20 text-purple-700', AD: 'bg-orange-400/20 text-orange-700', HTTP: 'bg-outline-variant/20 text-on-surface-variant' }
  return map[method] || 'bg-outline-variant/20 text-on-surface-variant'
}
function methodBadgeActiveClass(method: string) {
  const map: Record<string, string> = { GET: 'bg-success-indicator/30 text-green-700', POST: 'bg-secondary/30 text-secondary', PUT: 'bg-yellow-400/40 text-yellow-700', DELETE: 'bg-error/30 text-error' }
  return map[method] || 'bg-secondary/20 text-secondary'
}
</script>
