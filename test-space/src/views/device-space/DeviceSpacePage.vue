<template>
  <div class="flex gap-4 h-full overflow-hidden select-none">
    <div class="flex-1 flex flex-col gap-4 min-w-0 overflow-hidden">
    <!-- Connection Bar - always visible, moved up -->
    <div class="glass-panel rounded-xl p-3 px-5 flex items-center gap-3 flex-nowrap overflow-hidden">
      <!-- Tab Switcher (leftmost) -->
      <div class="flex gap-2 shrink-0">
        <button v-for="tab in tabs" :key="tab.key"
          class="px-5 py-2 rounded-full font-label-md text-label-md transition-all flex items-center hover:scale-105 select-none"
          :class="activeTab === tab.key ? 'bg-secondary/10 text-secondary border border-secondary/30' : 'bg-transparent text-on-surface-variant/70 border border-transparent hover:bg-white/30'"
          @click="activeTab = tab.key">
          <span class="material-symbols-outlined text-[16px] align-middle mr-1.5">{{ tab.icon }}</span>
          {{ tab.label }}
        </button>
      </div>
      <div class="h-5 w-[1px] bg-glass-border-dark shrink-0 ml-auto"></div>
      <div ref="connectIpInputRef" class="relative flex-1 min-w-[160px] max-w-[360px]">
        <div class="flex items-center border border-outline-variant/60 rounded-full px-4 py-2 bg-white/50">
          <span class="material-symbols-outlined text-on-surface-variant text-[16px] mr-2">link</span>
          <input v-model="connectAddress"
            class="flex-1 bg-transparent border-none outline-none font-body-sm text-body-sm text-on-surface placeholder:text-on-surface-variant/50 focus:ring-0 p-0 select-text"
            :placeholder="t('device.inputHint')" @keyup.enter="connectToDevice"
            @focus="onConnectIpFocus" />
        </div>
      </div>
      <Teleport to="body">
        <div v-if="showConnectIpHistory && connectIpHistory.length > 0" class="fixed inset-0 z-40" @click="showConnectIpHistory = false"></div>
        <div v-if="showConnectIpHistory && connectIpHistory.length > 0" class="fixed z-50 bg-white rounded-lg p-1 max-h-32 overflow-y-auto custom-scrollbar shadow-lg"
          :style="{ top: connectIpDropdownPos.top + 'px', left: connectIpDropdownPos.left + 'px', width: connectIpDropdownPos.width + 'px' }">
          <button v-for="h in connectIpHistory" :key="h" class="w-full flex items-center gap-2 px-2 py-1.5 rounded font-caption text-caption text-on-surface hover:bg-gray-100 select-none text-left no-border whitespace-nowrap"
            @mousedown.prevent @click="selectConnectIpHistory(h)">{{ h }}</button>
        </div>
      </Teleport>
      <button class="bg-white/30 border border-outline-variant/30 px-4 py-2 rounded-full font-label-md text-label-md flex items-center gap-1 hover:bg-secondary/10 hover:border-secondary/30 hover:scale-105 transition-all shrink-0 select-none backdrop-blur-sm" @click="connectToDevice" :disabled="connecting">
        <span v-if="connecting" class="w-3.5 h-3.5 border-2 border-secondary border-t-transparent rounded-full animate-spin"></span>
        <span v-else class="material-symbols-outlined text-[16px]">add_link</span>{{ connecting ? t('device.connecting') : t('device.connect') }}
      </button>
      <div class="h-5 w-[1px] bg-glass-border-dark"></div>
      <div class="flex items-center gap-2 shrink-0">
        <div v-if="devices.length > 0">
          <button ref="deviceDropdownBtnRef" @click="toggleDeviceDropdown"
            class="flex items-center gap-2 bg-white/30 border border-outline-variant/30 rounded-full pl-3 pr-3 py-2 font-caption text-caption text-on-surface cursor-pointer hover:bg-secondary/10 hover:border-secondary/30 hover:scale-105 transition-all min-w-[130px] max-w-[200px] backdrop-blur-sm">
            <div class="w-2 h-2 rounded-full shrink-0" :class="selectedDevice?.status === 'online' ? 'bg-success-indicator' : 'bg-outline-variant'"></div>
            <span class="truncate flex-1 text-left">{{ selectedDevice?.name || t('device.selectDeviceFirst') }}</span>
            <span class="material-symbols-outlined text-[14px] text-on-surface-variant shrink-0">unfold_more</span>
          </button>
        </div>
        <button v-if="selectedDevice" class="text-on-surface-variant hover:text-error hover:scale-105 transition-all select-none flex items-center no-border" :title="t('device.disconnect')"
          @click="disconnectDeviceHandler(selectedDevice.serial)">
          <span class="material-symbols-outlined text-[16px]">close</span>
        </button>
        <span v-if="devices.length === 0" class="font-caption text-caption text-on-surface-variant/50 whitespace-nowrap">{{ t('device.noDevice') }}</span>
      </div>
      <button class="text-on-surface-variant hover:text-secondary hover:scale-105 transition-all select-none no-border" @click="scanDevices()" :disabled="scanLoading">
        <span class="material-symbols-outlined text-[18px] block" :class="scanLoading ? 'animate-spin' : ''">refresh</span>
      </button>
    </div>

    <!-- Tab 1: 常用命令 -->
    <div v-show="activeTab === 'common'" class="flex flex-col gap-4 flex-grow min-h-0 overflow-hidden">
      <!-- Operations & Actions Grid -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 shrink-0">
        <!-- Device Operations Card -->
        <div class="glass-panel rounded-xl p-5 flex flex-col gap-4 shadow-md">
          <h3 class="flex items-center gap-2 font-label-md text-label-md text-on-surface select-none">
            <span class="material-symbols-outlined text-[16px] text-on-surface-variant">settings_remote</span> {{ t('device.deviceOps') }}
          </h3>
          <div class="grid grid-cols-3 gap-3">
            <button class="bg-white/30 border border-outline-variant/30 py-1.5 px-3 rounded-xl font-caption text-caption flex items-center justify-center gap-2 hover:bg-secondary/10 hover:border-secondary/30 hover:scale-105 transition-all text-sm text-on-surface backdrop-blur-sm select-none"
              :disabled="!selectedDevice || !!infoLoading" @click="queryInfo('basic')">
              <span v-if="infoLoading === 'basic'" class="w-3 h-3 border-2 border-current border-t-transparent rounded-full animate-spin"></span>
              <span v-else class="material-symbols-outlined text-[16px] text-on-surface-variant">info</span> {{ t('device.basicInfo') }}
            </button>
            <button class="bg-white/30 border border-outline-variant/30 py-1.5 px-3 rounded-xl font-caption text-caption flex items-center justify-center gap-2 hover:bg-secondary/10 hover:border-secondary/30 hover:scale-105 transition-all text-sm text-on-surface backdrop-blur-sm select-none"
              :disabled="!selectedDevice || !!infoLoading" @click="queryInfo('mac')">
              <span v-if="infoLoading === 'mac'" class="w-3 h-3 border-2 border-current border-t-transparent rounded-full animate-spin"></span>
              <span v-else class="material-symbols-outlined text-[16px] text-on-surface-variant">wifi</span> {{ t('device.macInfo') }}
            </button>
            <button class="bg-white/30 border border-outline-variant/30 py-1.5 px-3 rounded-xl font-caption text-caption flex items-center justify-center gap-2 hover:bg-secondary/10 hover:border-secondary/30 hover:scale-105 transition-all text-sm text-on-surface backdrop-blur-sm select-none"
              :disabled="!selectedDevice || !!infoLoading" @click="queryInfo('whaleos')">
              <span v-if="infoLoading === 'whaleos'" class="w-3 h-3 border-2 border-current border-t-transparent rounded-full animate-spin"></span>
              <span v-else class="material-symbols-outlined text-[16px] text-on-surface-variant">description</span> {{ t('device.firmwareInfo') }}
            </button>
            <button class="bg-white/30 border border-outline-variant/30 py-1.5 px-3 rounded-xl font-caption text-caption flex items-center justify-center gap-2 hover:bg-secondary/10 hover:border-secondary/30 hover:scale-105 transition-all text-sm text-on-surface backdrop-blur-sm select-none"
              :disabled="!selectedDevice || !!infoLoading" @click="queryInfo('storage')">
              <span v-if="infoLoading === 'storage'" class="w-3 h-3 border-2 border-current border-t-transparent rounded-full animate-spin"></span>
              <span v-else class="material-symbols-outlined text-[16px] text-on-surface-variant">database</span> {{ t('device.storageInfo') }}
            </button>
            <button class="bg-white/30 border border-outline-variant/30 py-1.5 px-3 rounded-xl font-caption text-caption flex items-center justify-center gap-2 hover:bg-secondary/10 hover:border-secondary/30 hover:scale-105 transition-all text-sm text-on-surface backdrop-blur-sm col-span-2 select-none"
              :disabled="!selectedDevice || !!infoLoading" @click="queryInfo('keys')">
              <span v-if="infoLoading === 'keys'" class="w-3 h-3 border-2 border-current border-t-transparent rounded-full animate-spin"></span>
              <span v-else class="material-symbols-outlined text-[16px] text-on-surface-variant">vpn_key</span> {{ t('device.checkKeys') }}
            </button>
          </div>
          <hr class="border-outline-variant/30 my-1">
          <div class="flex flex-wrap gap-2">
            <button class="bg-white/30 border border-outline-variant/30 px-2.5 py-1 rounded-xl font-caption text-caption flex items-center gap-1 hover:bg-secondary/10 hover:border-secondary/30 hover:scale-105 transition-all backdrop-blur-sm select-none" :disabled="!selectedDevice" @click="confirmThen(t('device.rebootConfirm2'), rebootDevice)">
              <span class="material-symbols-outlined text-[14px] text-on-surface-variant">restart_alt</span> {{ t('device.reboot') }}
            </button>
            <button class="bg-white/30 border border-outline-variant/30 px-2.5 py-1 rounded-xl font-caption text-caption flex items-center gap-1 hover:bg-secondary/10 hover:border-secondary/30 hover:scale-105 transition-all backdrop-blur-sm select-none" :disabled="!selectedDevice" @click="rootDevice">
              <span class="material-symbols-outlined text-[14px] text-on-surface-variant">shield</span> Root
            </button>
            <button class="bg-white/30 border border-outline-variant/30 px-2.5 py-1 rounded-xl font-caption text-caption flex items-center gap-1 hover:bg-secondary/10 hover:border-secondary/30 hover:scale-105 transition-all backdrop-blur-sm select-none" :disabled="!selectedDevice" @click="confirmThen(t('device.remountConfirm'), remountDevice)">
              <span class="material-symbols-outlined text-[14px] text-on-surface-variant">published_with_changes</span> Remount
            </button>
          </div>
        </div>
        <!-- Quick Actions Card -->
        <div class="glass-panel rounded-xl p-5 flex flex-col gap-4 shadow-md">
          <h3 class="flex items-center gap-2 font-label-md text-label-md text-on-surface select-none">
            <span class="material-symbols-outlined text-[16px] text-on-surface-variant">keyboard_command_key</span> {{ t('device.quickActions') }}
          </h3>
          <div class="flex gap-2">
            <div class="flex-1 relative">
              <input ref="textInputRef" v-model="inputTextValue"
                class="w-full bg-white/50 border border-outline-variant/60 rounded-full px-3 py-1.5 font-body-sm text-body-sm text-on-surface placeholder:text-on-surface-variant/50 focus:ring-2 focus:ring-secondary/30 focus:border-secondary transition-all select-text"
                :placeholder="t('device.textHint')" @keyup.enter="sendText" @focus="showTextHistory = true" @blur="hideTextHistoryDelayed" />
              <div v-if="showTextHistory && textHistory.length > 0" class="absolute top-full left-0 right-0 z-20 mt-1 bg-white rounded-lg p-1 max-h-32 overflow-y-auto custom-scrollbar shadow-lg">
                <button v-for="h in textHistory" :key="h" class="w-full flex items-center gap-2 px-2 py-1.5 rounded font-caption text-caption text-on-surface hover:bg-gray-100 select-none text-left no-border"
                  @mousedown.prevent @click="selectTextHistory(h)">{{ h }}</button>
              </div>
            </div>
            <button class="bg-white/30 border border-outline-variant/30 text-on-surface px-4 py-1.5 rounded-xl font-label-md text-label-md hover:bg-secondary/10 hover:border-secondary/30 hover:scale-105 transition-all backdrop-blur-sm select-none" @click="sendText" :disabled="!selectedDevice || !inputTextValue.trim()">{{ t('device.send') }}</button>
          </div>
          <hr class="border-outline-variant/30 my-1">
          <div class="flex flex-wrap gap-2">
            <button class="bg-white/30 border border-outline-variant/30 px-2.5 py-1 rounded-xl font-caption text-caption flex items-center gap-1 hover:bg-secondary/10 hover:border-secondary/30 hover:scale-105 transition-all backdrop-blur-sm select-none" @click="takeScreenshot" :disabled="!selectedDevice">
              <span class="material-symbols-outlined text-[14px] text-on-surface-variant">image</span> {{ t('device.screenshot') }}
            </button>
            <button class="bg-white/30 border border-outline-variant/30 px-2.5 py-1 rounded-xl font-caption text-caption flex items-center gap-1 hover:bg-secondary/10 hover:border-secondary/30 hover:scale-105 transition-all backdrop-blur-sm select-none"
              :class="isRecording ? 'bg-error/10 text-error border border-error/20' : ''"
              :disabled="!selectedDevice || recordingLoading" @click="toggleRecording">
              <span v-if="recordingLoading" class="w-3 h-3 border-2 border-current border-t-transparent rounded-full animate-spin"></span>
              <span v-else class="material-symbols-outlined text-[14px]">{{ isRecording ? 'stop' : 'videocam' }}</span>
              {{ recordingLoading ? (isRecording ? t('device.stopping') : t('device.starting')) : (isRecording ? t('device.stopRecording') : t('device.screenrec')) }}
            </button>
            <button class="bg-white/30 border border-outline-variant/30 px-2.5 py-1 rounded-xl font-caption text-caption flex items-center gap-1 hover:bg-secondary/10 hover:border-secondary/30 hover:scale-105 transition-all backdrop-blur-sm select-none"
              :disabled="!selectedDevice || logPrepActive" @click="clearLogcatLogs">
              <span class="material-symbols-outlined text-[14px] text-on-surface-variant">delete_sweep</span> {{ t('device.clearLogs') }}
            </button>
            <button class="bg-white/30 border border-outline-variant/30 px-2.5 py-1 rounded-xl font-caption text-caption flex items-center gap-1 hover:bg-secondary/10 hover:border-secondary/30 hover:scale-105 transition-all backdrop-blur-sm select-none" :disabled="!selectedDevice" @click="restartAdbServer">
              <span class="material-symbols-outlined text-[14px] text-on-surface-variant">power_settings_new</span> {{ t('device.restartAdb') }}
            </button>
          </div>
          <div v-if="logPrepActive" class="flex items-center gap-2 p-2 bg-secondary/5 rounded-lg font-caption text-caption text-secondary">
            <span class="w-3 h-3 border-2 border-secondary border-t-transparent rounded-full animate-spin"></span>
            {{ logPrepMessage }}
          </div>
          <div class="flex flex-wrap gap-2">
            <button class="bg-white/30 border border-outline-variant/30 px-3 py-1.5 rounded-xl font-caption text-caption flex items-center gap-1.5 hover:bg-secondary/10 hover:border-secondary/30 hover:scale-105 transition-all text-xs text-on-surface backdrop-blur-sm select-none"
              :class="logcatRunning ? 'bg-error/20 text-error border-error/30 hover:bg-error/30' : ''"
              :disabled="!selectedDevice || logPrepActive || (diagRunning && !logcatRunning)" @click="toggleLogcat">
              <span class="material-symbols-outlined text-[14px]" :class="logcatRunning ? 'text-error' : 'text-on-surface-variant'">{{ logcatRunning ? 'stop' : 'assignment' }}</span>
              <span v-if="logcatRunning" class="flex items-center gap-1.5">
                {{ t('device.stop') }} <span class="font-mono text-[11px] opacity-80">{{ logcatElapsed }}s</span>
              </span>
              <span v-else>{{ t('device.realtimeLogs') }}</span>
            </button>
            <button class="bg-white/30 border border-outline-variant/30 px-3 py-1.5 rounded-xl font-caption text-caption flex items-center gap-1.5 hover:bg-secondary/10 hover:border-secondary/30 hover:scale-105 transition-all text-xs text-on-surface backdrop-blur-sm select-none"
              :class="diagRunning ? 'bg-error/20 text-error border-error/30 hover:bg-error/30' : ''"
              :disabled="!selectedDevice || logPrepActive || (logcatRunning && !diagRunning)" @click="toggleDiagnostic">
              <span class="material-symbols-outlined text-[14px]" :class="diagRunning ? 'text-error' : 'text-on-surface-variant'">{{ diagRunning ? 'stop' : 'work' }}</span>
              <span v-if="diagRunning" class="flex items-center gap-1.5">
                {{ t('device.stop') }} <span class="font-mono text-[11px] opacity-80">{{ diagElapsed }}s</span>
              </span>
              <span v-else>{{ t('device.diagnostics') }}</span>
            </button>
            <button class="bg-white/30 border border-outline-variant/30 px-3 py-1.5 rounded-xl font-caption text-caption flex items-center gap-1.5 hover:bg-secondary/10 hover:border-secondary/30 hover:scale-105 transition-all text-xs text-on-surface backdrop-blur-sm select-none"
              :class="bootLogcatRunning ? 'bg-error/20 text-error border-error/30 hover:bg-error/30' : ''"
              :disabled="!selectedDevice || logPrepActive || logcatRunning || diagRunning" @click="toggleBootLogcat">
              <span class="material-symbols-outlined text-[14px]" :class="bootLogcatRunning ? 'text-error' : 'text-on-surface-variant'">{{ bootLogcatRunning ? 'stop' : 'pest_control' }}</span>
              <span v-if="bootLogcatRunning" class="flex items-center gap-1.5">
                {{ t('device.stop') }} <span class="font-mono text-[11px] opacity-80">{{ bootLogcatElapsed }}s</span>
              </span>
              <span v-else>{{ t('device.bootLogs') }}</span>
            </button>
            <button class="bg-white/30 border border-outline-variant/30 px-3 py-1.5 rounded-xl font-caption text-caption flex items-center gap-1.5 hover:bg-secondary/10 hover:border-secondary/30 hover:scale-105 transition-all text-xs text-on-surface backdrop-blur-sm select-none"
              :disabled="!selectedDevice" @click="generateBugreport">
              <span class="material-symbols-outlined text-[14px] text-on-surface-variant">bug_report</span> Bugreport
            </button>
          </div>
        </div>
      </div>

      <!-- Bottom Layout: App Management + 快捷指令 -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-4 flex-1 min-h-0 pb-3">
        <!-- App Management -->
        <div class="lg:col-span-2 glass-panel rounded-xl flex flex-col min-h-0 overflow-hidden shadow-md">
            <!-- App Management Header -->
            <div class="p-4 border-b border-outline-variant/30 flex flex-col gap-3">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-4">
                  <h3 class="font-label-md text-label-md text-on-surface flex items-center gap-2 shrink-0 select-none">
                    <span class="material-symbols-outlined text-[16px] text-on-surface-variant">apps</span>{{ t('device.appManagement') }}
                    <span class="font-caption text-caption text-on-surface-variant/60 font-normal text-sm">({{ sortedApps.length }})</span>
                  </h3>
                  <div class="flex items-center gap-2 text-sm text-on-surface-variant">
                    <button class="bg-white/30 border border-outline-variant/30 px-2 py-1 rounded-xl flex items-center gap-1 hover:bg-secondary/10 hover:border-secondary/30 hover:scale-105 transition-all backdrop-blur-sm select-none" @click="refreshPackageList" :disabled="!selectedDevice || pkgLoading">
                      <span v-if="pkgLoading" class="w-3 h-3 border-2 border-secondary border-t-transparent rounded-full animate-spin"></span>
                      <span v-else class="material-symbols-outlined text-[14px]">refresh</span>{{ t('device.refresh') }}
                    </button>
                    <label class="flex items-center cursor-pointer hover:scale-105 transition-all px-2 py-1 rounded-xl bg-white/30 border border-outline-variant/30 backdrop-blur-sm hover:bg-secondary/10 hover:border-secondary/30">
                      <input type="checkbox" v-model="showThirdParty" class="rounded border-outline-variant text-secondary focus:ring-secondary mr-1 w-3.5 h-3.5 accent-secondary select-text" @change="refreshPackageList" />
                      {{ t('device.thirdPartyApps') }}
                    </label>
                    <button class="bg-white/30 border border-outline-variant/30 px-2 py-1 rounded-xl flex items-center gap-1 hover:bg-secondary/10 hover:border-secondary/30 hover:scale-105 transition-all backdrop-blur-sm select-none" :disabled="!selectedDevice" @click="apkDialogOpen = true">
                      <span class="material-symbols-outlined text-[14px]">file_upload</span> {{ t('device.installApk') }}
                    </button>
                    <button class="bg-white/30 border border-outline-variant/30 px-2 py-1 rounded-xl flex items-center gap-1 hover:bg-secondary/10 hover:border-secondary/30 hover:scale-105 transition-all backdrop-blur-sm select-none" @click="getCurrentForegroundApp" :disabled="!selectedDevice || loadingForeground">
                      <span v-if="loadingForeground" class="inline-block w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                      <span v-else class="material-symbols-outlined text-[14px]">center_focus_strong</span> {{ t('device.foregroundApp') }}
                    </button>
                  </div>
                </div>
              </div>
              <div class="flex items-center gap-4">
                <div class="relative">
                  <div class="flex items-center border border-outline-variant/60 rounded-full px-3 py-1.5 bg-white/50 w-80">
                    <span class="material-symbols-outlined text-on-surface-variant text-[16px] mr-2">search</span>
                    <input v-model="queryPackageName" class="bg-transparent border-none outline-none w-full font-body-sm text-body-sm text-on-surface placeholder:text-on-surface-variant/50 focus:ring-0 p-0 select-text"
                      :placeholder="t('device.searchApp')" @input="onAppSearchInput" @keyup.enter="queryAppPath" @focus="loadAppSearchHistory" @blur="hideAppSearchHistoryDelayed" />
                  </div>
                  <div v-if="showAppSearchHistory && appSearchHistory.length > 0" class="absolute top-full left-0 right-0 z-20 mt-1 bg-white rounded-lg p-1 max-h-32 overflow-y-auto custom-scrollbar shadow-lg">
                    <button v-for="h in appSearchHistory" :key="h" class="w-full flex items-center gap-2 px-2 py-1.5 rounded font-caption text-caption text-on-surface hover:bg-gray-100 select-none text-left no-border"
                      @mousedown.prevent @click="selectAppSearchHistory(h)">{{ h }}</button>
                  </div>
                </div>
                <button class="bg-white/30 border border-outline-variant/30 px-2 py-1 rounded-xl flex items-center gap-1 hover:bg-secondary/10 hover:border-secondary/30 hover:scale-105 transition-all backdrop-blur-sm select-none" :disabled="!selectedDevice" @click="queryAppPath">
                  <span class="material-symbols-outlined text-[14px]">folder_open</span> {{ t('device.path') }}
                </button>
                <div v-if="totalPages > 1" class="flex items-center gap-2 text-sm text-on-surface bg-white/30 border border-outline-variant/30 rounded-xl px-3 py-1 ml-auto backdrop-blur-sm">
                  <button class="hover:bg-secondary/10 hover:border-secondary/30 hover:scale-105 rounded-full p-0.5 transition-all disabled:opacity-50 select-none" :disabled="appPage <= 1" @click="appPage = Math.max(1, appPage - 1); nextTick(loadVisibleAppVersions)">
                    <span class="material-symbols-outlined text-[16px]">chevron_left</span>
                  </button>
                  <span class="whitespace-nowrap">{{ appPage }} / {{ totalPages }}</span>
                  <button class="hover:bg-secondary/10 hover:border-secondary/30 hover:scale-105 rounded-full p-0.5 transition-all disabled:opacity-50 select-none" :disabled="appPage >= totalPages" @click="appPage = Math.min(totalPages, appPage + 1); nextTick(loadVisibleAppVersions)">
                    <span class="material-symbols-outlined text-[16px]">chevron_right</span>
                  </button>
                </div>
              </div>
            </div>

            <!-- App List -->
            <div ref="appListContainer" class="flex-1 min-h-0 overflow-y-auto custom-scrollbar p-2" :style="{ maxHeight: appListMaxHeight + 'px' }">
              <div v-if="currentPageApps.length === 0" class="text-center py-3">
                <p class="font-caption text-caption text-on-surface-variant/50">{{ t('device.noApp') }}</p>
              </div>
              <table v-else class="w-full text-sm text-left whitespace-nowrap">
                <tbody class="divide-y divide-outline-variant/30">
                  <tr v-for="app in currentPageApps" :key="app.package_name" :ref="(el) => { if (el && !appItemMeasured) measureAppItem(el as HTMLElement) }" class="hover:bg-white/30 transition-colors group">
                    <td class="pl-1 pr-0 py-2">
                      <span class="material-symbols-outlined text-success-indicator text-[16px] cursor-pointer hover:scale-125 transition-transform" :title="t('device.start')" @click="startApp(app.package_name)">play_arrow</span>
                    </td>
                    <td class="px-0 py-2">
                      <span class="material-symbols-outlined text-error text-[16px] cursor-pointer hover:scale-125 transition-transform" :title="t('device.stop')" @click="stopApp(app.package_name)">stop_circle</span>
                    </td>
                    <td class="px-0 py-2">
                      <span class="material-symbols-outlined text-on-surface-variant text-[16px] cursor-pointer hover:scale-125 transition-transform" :title="t('device.detail')" @click="showAppDetail(app.package_name)">info</span>
                    </td>
                    <td class="px-0 py-2">
                      <span class="material-symbols-outlined text-on-surface-variant text-[16px] cursor-pointer hover:scale-125 transition-transform" :title="t('device.downloadApk')" @click="downloadApk(app.package_name)">download</span>
                    </td>
                    <td class="px-0 py-2">
                      <span class="material-symbols-outlined text-error/70 text-[16px] cursor-pointer hover:scale-125 transition-transform" :title="t('device.clearData')" @click="clearApp(app.package_name)">cleaning_services</span>
                    </td>
                    <td class="pr-1 pl-0 py-2">
                      <span class="material-symbols-outlined text-error text-[16px] cursor-pointer hover:scale-125 transition-transform" :title="t('device.uninstall')" @click="confirmThen(`${t('device.uninstallConfirm')} ${app.package_name}?`, () => uninstallPkg(app.package_name))">delete</span>
                    </td>
                    <td class="pl-2 pr-2 py-2 font-medium text-on-surface">
                      <span class="font-mono cursor-pointer hover:text-secondary hover:underline truncate" :title="app.package_name" @click="copyPackageName(app.package_name)">{{ app.package_name }}</span>
                      <span v-if="app.version_name" class="text-xs bg-secondary/10 text-secondary px-2 py-0.5 rounded ml-2 border border-secondary/20 cursor-pointer"
                        :title="t('device.copyVersionInfo')" @click="copyVersionInfo(app.package_name)">
                        v{{ app.version_name }}{{ app.version_code ? ` (${app.version_code})` : '' }}
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
          </div>
        </div>
        <!-- 快捷指令 Sidebar -->
        <div class="glass-panel rounded-xl p-5 flex flex-col gap-6 overflow-y-auto shadow-md">
          <div class="flex flex-col gap-3">
            <div class="flex items-center justify-between">
              <h3 class="flex items-center gap-2 font-label-md text-label-md text-on-surface select-none">
                <span class="material-symbols-outlined text-[16px] text-on-surface-variant">bolt</span> {{ t('device.shortcuts') }}
              </h3>
              <div class="flex items-center gap-1">
                <button class="bg-white/30 border border-outline-variant/30 px-2 py-1 rounded-xl hover:bg-secondary/10 hover:border-secondary/30 hover:scale-105 transition-all text-on-surface-variant backdrop-blur-sm select-none" :title="t('device.manage')" @click="showCmdManager = true">
                  <span class="material-symbols-outlined text-[18px]">edit_note</span>
                </button>
              </div>
            </div>

            <!-- Normal Mode -->
            <div v-if="customCommands.length === 0" class="flex flex-col gap-2">
              <div class="text-xs text-on-surface-variant/50 italic p-3 border border-dashed border-outline-variant/60 rounded-lg text-center">{{ t('device.noCommands') }}</div>
            </div>
            <div v-if="customCommands.length > 0" class="grid grid-cols-2 gap-2">
              <div v-for="(cmd, idx) in customCommands" :key="idx"
                class="flex items-center px-3 py-1.5 bg-white/30 border border-outline-variant/30 rounded-xl cursor-pointer hover:bg-secondary/10 hover:border-secondary/30 hover:scale-105 transition-all backdrop-blur-sm" @click="executeCustomCommand(cmd.command)">
                <div class="font-caption text-caption text-on-surface leading-tight break-all">{{ cmd.name }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Tab 2: 其他命令 -->
    <div v-show="activeTab === 'other'" class="grid grid-cols-1 lg:grid-cols-5 gap-4 flex-grow min-h-0 overflow-hidden">

      <!-- Left Column: Screen Mirror + Remote Control -->
      <div class="col-span-1 lg:col-span-3 flex flex-col gap-4 min-h-0 overflow-hidden">

        <!-- Screen Mirror -->
        <div class="glass-panel rounded-xl p-3 flex-1 min-h-0 flex flex-col shadow-md">
          <div class="flex items-center gap-3 mb-2 flex-wrap shrink-0">
            <div class="flex items-center gap-2 shrink-0">
              <span class="material-symbols-outlined text-[16px]">screenshot_monitor</span>
              <span class="font-label-md text-label-md text-on-surface">{{ t('device.screenMirror') }}</span>
              <span v-if="mirrorMode !== 'idle' || mirrorErrorMsg"
                class="ml-1 px-2 py-0.5 rounded-full font-caption text-[11px] leading-tight select-none"
                :class="mirrorMode === 'scrcpy' ? 'bg-success-indicator/20 text-success-indicator border border-success-indicator/30' : 'bg-amber-100 text-amber-700 border border-amber-200'"
                :title="mirrorErrorMsg">
                {{ mirrorMode === 'scrcpy' ? 'scrcpy' : (mirrorMode === 'legacy' ? 'screencap' : mirrorErrorMsg) }}
              </span>
            </div>
            <button class="glass-button px-4 py-1.5 rounded-lg font-label-md text-label-md flex items-center gap-1 select-none"
              :class="isMirroring ? 'bg-error/10 text-error border border-error/20' : ''"
              :disabled="!selectedDevice"
              @click="toggleMirror">
              <span class="material-symbols-outlined text-[16px]">{{ isMirroring ? 'stop' : 'play_arrow' }}</span>
              {{ isMirroring ? t('device.stopMirror') : t('device.startMirror') }}
            </button>
            <button class="glass-button px-2 py-1.5 rounded-lg font-caption text-caption flex items-center gap-1 select-none ml-1"
              :disabled="!selectedDevice"
              :title="qualityMode === 'smooth' ? '流畅优先' : '画质优先'"
              @click="toggleQualityMode">
              <span class="material-symbols-outlined text-[14px]">hdr_weak</span>
              <span class="text-[11px] leading-none whitespace-nowrap">{{ qualityMode === 'smooth' ? '流畅' : '画质' }}</span>
            </button>
            <button v-if="isMirroring" class="glass-button p-1.5 rounded-lg flex items-center select-none ml-1" title="Open in separate window" :disabled="!selectedDevice" @click="mirrorPopout">
              <span class="material-symbols-outlined text-[16px]">open_in_new</span>
            </button>
          </div>
          <div class="flex-1 min-h-0 bg-black/5 rounded-xl overflow-hidden relative border border-dashed border-outline-variant/40" style="aspect-ratio:16/9;min-height:200px">
            <canvas v-show="isMirroring && mirrorFrameCount > 0" ref="mirrorCanvas" class="w-full h-full object-contain block"
              @mousedown="handleMirrorPointerDown"
              @mouseup="handleMirrorPointerUp"
              @touchstart.prevent="handleMirrorPointerDown($event.touches[0])"
              @touchend.prevent="handleMirrorPointerUp($event.changedTouches[0])"
              @contextmenu.prevent="handleMirrorRightClick"></canvas>
            <div v-if="!isMirroring" class="absolute inset-0 flex items-center justify-center">
              <span class="material-symbols-outlined text-4xl text-on-surface-variant/30">screenshot_monitor</span>
              <p class="font-body-sm text-body-sm text-on-surface-variant/50 mt-1">Screen mirror inactive</p>
            </div>
            <div v-if="isMirroring && mirrorFrameCount === 0" class="absolute inset-0 flex items-center justify-center bg-black/20">
              <span class="font-body-md text-body-md text-white/80">{{ t('device.waitingImage') }}</span>
            </div>
          </div>
        </div>

        <!-- Remote Control -->
        <div class="glass-panel rounded-xl p-3 lg:p-4 xl:p-5 2xl:p-6 shadow-md mb-3 overflow-x-auto">
          <h3 class="font-label-md text-label-md text-on-surface mb-2 lg:mb-3 xl:mb-4 2xl:mb-5 flex items-center gap-1.5 select-none">
            <span class="material-symbols-outlined text-[14px] lg:text-[16px] xl:text-[18px] 2xl:text-[22px] select-none">gamepad</span><span class="select-none">{{ t('device.remoteControl') }}</span>
          </h3>
          <div class="flex gap-2 lg:gap-4 xl:gap-6 2xl:gap-8 items-start justify-center" :class="{ 'remote-disabled': !selectedDevice }">
            <!-- Left: Back, Home, Settings -->
            <div class="flex flex-col gap-1 lg:gap-1.5">
              <button class="glass-button px-2 py-1 lg:px-3 lg:py-1.5 xl:px-4 xl:py-2 2xl:px-6 2xl:py-3 rounded-lg font-caption text-caption text-[10px] lg:text-[11px] xl:text-[13px] 2xl:text-[15px] flex items-center gap-1 select-none" @click="sendKey('4')">
                <span class="material-symbols-outlined text-[12px] lg:text-[14px] xl:text-[16px] 2xl:text-[20px] select-none">arrow_back</span><span class="select-none">{{ t('device.back') }}</span>
              </button>
              <button class="glass-button px-2 py-1 lg:px-3 lg:py-1.5 xl:px-4 xl:py-2 2xl:px-6 2xl:py-3 rounded-lg font-caption text-caption text-[10px] lg:text-[11px] xl:text-[13px] 2xl:text-[15px] flex items-center gap-1 select-none" @click="sendKey('3')">
                <span class="material-symbols-outlined text-[12px] lg:text-[14px] xl:text-[16px] 2xl:text-[20px] select-none">home</span><span class="select-none">Home</span>
              </button>
              <button class="glass-button px-2 py-1 lg:px-3 lg:py-1.5 xl:px-4 xl:py-2 2xl:px-6 2xl:py-3 rounded-lg font-caption text-caption text-[10px] lg:text-[11px] xl:text-[13px] 2xl:text-[15px] flex items-center gap-1 select-none" @click="sendKey('176')">
                <span class="material-symbols-outlined text-[12px] lg:text-[14px] xl:text-[16px] 2xl:text-[20px] select-none">settings</span><span class="select-none">{{ t('device.settings') }}</span>
              </button>
            </div>
            <!-- Center: D-pad -->
            <div class="relative w-[110px] h-[110px] lg:w-[140px] lg:h-[140px] xl:w-[170px] xl:h-[170px] 2xl:w-[220px] 2xl:h-[220px] flex-none">
              <div class="absolute top-0 left-1/2 -translate-x-1/2">
                <button class="w-[26px] h-[26px] lg:w-[32px] lg:h-[32px] xl:w-[40px] xl:h-[40px] 2xl:w-[52px] 2xl:h-[52px] glass-button rounded-full flex items-center justify-center select-none" @click="sendKey('19')">
                  <span class="material-symbols-outlined text-[12px] lg:text-[16px] xl:text-[20px] 2xl:text-[26px] select-none">keyboard_arrow_up</span>
                </button>
              </div>
              <div class="absolute bottom-0 left-1/2 -translate-x-1/2">
                <button class="w-[26px] h-[26px] lg:w-[32px] lg:h-[32px] xl:w-[40px] xl:h-[40px] 2xl:w-[52px] 2xl:h-[52px] glass-button rounded-full flex items-center justify-center select-none" @click="sendKey('20')">
                  <span class="material-symbols-outlined text-[12px] lg:text-[16px] xl:text-[20px] 2xl:text-[26px] select-none">keyboard_arrow_down</span>
                </button>
              </div>
              <div class="absolute left-0 top-1/2 -translate-y-1/2">
                <button class="w-[26px] h-[26px] lg:w-[32px] lg:h-[32px] xl:w-[40px] xl:h-[40px] 2xl:w-[52px] 2xl:h-[52px] glass-button rounded-full flex items-center justify-center select-none" @click="sendKey('21')">
                  <span class="material-symbols-outlined text-[12px] lg:text-[16px] xl:text-[20px] 2xl:text-[26px] select-none">keyboard_arrow_left</span>
                </button>
              </div>
              <div class="absolute right-0 top-1/2 -translate-y-1/2">
                <button class="w-[26px] h-[26px] lg:w-[32px] lg:h-[32px] xl:w-[40px] xl:h-[40px] 2xl:w-[52px] 2xl:h-[52px] glass-button rounded-full flex items-center justify-center select-none" @click="sendKey('22')">
                  <span class="material-symbols-outlined text-[12px] lg:text-[16px] xl:text-[20px] 2xl:text-[26px] select-none">keyboard_arrow_right</span>
                </button>
              </div>
              <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
                <button class="w-[32px] h-[32px] lg:w-[40px] lg:h-[40px] xl:w-[48px] xl:h-[48px] 2xl:w-[64px] 2xl:h-[64px] glass-button rounded-full flex items-center justify-center bg-secondary/10 select-none" @click="sendKey('23')">
                  <span class="material-symbols-outlined text-secondary text-[16px] lg:text-[20px] xl:text-[24px] 2xl:text-[32px] select-none">check</span>
                </button>
              </div>
            </div>
            <!-- Right: Power, Volume, Numpad -->
            <div class="flex flex-col gap-1 lg:gap-1.5">
              <button class="glass-button px-2 py-1 lg:px-3 lg:py-1.5 xl:px-4 xl:py-2 2xl:px-6 2xl:py-3 rounded-lg font-caption text-caption text-[10px] lg:text-[11px] xl:text-[13px] 2xl:text-[15px] flex items-center justify-center gap-1 bg-error/10 text-error border border-error/20 select-none" @click="sendKey('26')">
                <span class="material-symbols-outlined text-[12px] lg:text-[14px] xl:text-[16px] 2xl:text-[20px] select-none">power_settings_new</span><span class="select-none">{{ t('device.power') }}</span>
              </button>
              <div class="grid grid-cols-3 gap-0.5 lg:gap-1 xl:gap-1.5">
                <button class="glass-button p-1 lg:p-1.5 xl:p-2 2xl:p-3 rounded-lg font-caption text-caption text-[10px] lg:text-[11px] xl:text-[13px] 2xl:text-[15px] flex items-center justify-center select-none" @click="sendKey('24')">
                  <span class="material-symbols-outlined text-[12px] lg:text-[14px] xl:text-[16px] 2xl:text-[20px] select-none">volume_up</span>
                </button>
                <button class="glass-button p-1 lg:p-1.5 xl:p-2 2xl:p-3 rounded-lg font-caption text-caption text-[10px] lg:text-[11px] xl:text-[13px] 2xl:text-[15px] flex items-center justify-center select-none" @click="sendKey('25')">
                  <span class="material-symbols-outlined text-[12px] lg:text-[14px] xl:text-[16px] 2xl:text-[20px] select-none">volume_down</span>
                </button>
                <button class="glass-button p-1 lg:p-1.5 xl:p-2 2xl:p-3 rounded-lg font-caption text-caption text-[10px] lg:text-[11px] xl:text-[13px] 2xl:text-[15px] flex items-center justify-center select-none" @click="sendKey('164')">
                  <span class="material-symbols-outlined text-[12px] lg:text-[14px] xl:text-[16px] 2xl:text-[20px] select-none">volume_off</span>
                </button>
              </div>
              <div class="grid grid-cols-5 gap-0.5 lg:gap-1 xl:gap-1.5">
                <button v-for="n in 9" :key="n" class="glass-button px-1 py-0.5 lg:px-1.5 lg:py-1 xl:px-2 xl:py-1.5 2xl:px-3 2xl:py-2 rounded-lg font-caption text-caption text-[10px] lg:text-[11px] xl:text-[13px] 2xl:text-[15px] select-none" @click="sendKey(String(7 + n))"><span class="select-none">{{ n }}</span></button>
                <button class="glass-button px-1 py-0.5 lg:px-1.5 lg:py-1 xl:px-2 xl:py-1.5 2xl:px-3 2xl:py-2 rounded-lg font-caption text-caption text-[10px] lg:text-[11px] xl:text-[13px] 2xl:text-[15px] select-none" @click="sendKey('0')"><span class="select-none">0</span></button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Right Column: File Manager -->
      <div class="col-span-1 lg:col-span-2 flex flex-col min-h-0 mb-3">
        <div class="glass-panel rounded-xl p-3 flex flex-col flex-1 min-h-0 shadow-md">
          <div class="flex items-center justify-between mb-2 shrink-0">
            <h3 class="font-label-md text-label-md text-on-surface flex items-center gap-1.5 select-none">
              <span class="material-symbols-outlined text-[16px] select-none">folder_open</span><span class="select-none">{{ t('device.fileManager') }}</span>
            </h3>
            <div class="flex gap-1.5">
              <button class="glass-button px-2.5 py-1.5 rounded-lg font-caption text-caption flex items-center gap-1 select-none" :disabled="!selectedDevice" @click="uploadFile">
                <span class="material-symbols-outlined text-[14px]">upload</span>{{ t('device.upload') }}
              </button>
            </div>
          </div>
          <div class="relative mb-2 shrink-0">
            <input v-model="remotePath" ref="remotePathInputRef"
              class="w-full bg-white border border-outline-variant rounded-lg px-3 py-1.5 font-body-sm text-body-sm text-on-surface font-mono focus:ring-2 focus:ring-secondary/30 focus:border-secondary transition-all select-text"
              :placeholder="t('device.remotePathHint')" @focus="showRemotePathHistory = true" @blur="hideRemotePathHistoryDelayed" @keyup.enter="navigateToPath" />
            <div v-if="showRemotePathHistory && remotePathHistory.length > 0" class="absolute top-full left-0 right-0 z-20 mt-1 bg-white rounded-lg p-1 max-h-32 overflow-y-auto custom-scrollbar shadow-lg">
              <button v-for="h in remotePathHistory" :key="h" class="w-full flex items-center gap-2 px-2 py-1.5 rounded font-caption text-caption text-on-surface hover:bg-gray-100 select-none text-left no-border"
                @mousedown.prevent @click="selectRemotePathHistory(h)">{{ h }}</button>
            </div>
          </div>
            <div class="relative flex-1 min-h-0" @click="closeFileContextMenu" @dragenter.prevent="onFileDragEnter" @dragover.prevent @dragleave="onFileDragLeave" @drop.prevent="onFileDrop">
            <div v-if="dragOverFileList" class="absolute inset-0 z-10 flex items-center justify-center bg-white/80 backdrop-blur-sm rounded-lg border-2 border-dashed border-secondary/50 pointer-events-none">
              <div class="flex flex-col items-center gap-2 text-secondary">
                <span class="material-symbols-outlined text-3xl">cloud_upload</span>
                <span class="font-label-md text-label-md font-semibold">{{ t('device.dropToUpload') }}</span>
              </div>
            </div>
            <div class="absolute inset-0 overflow-y-auto overflow-x-hidden custom-scrollbar text-[12px] leading-relaxed select-none">
              <div v-if="fileEntries.length === 0" class="text-center py-8 text-on-surface-variant/40">
                <span class="material-symbols-outlined text-3xl">folder_open</span>
                <p class="font-body-sm text-body-sm mt-1">{{ t('device.pathHint') }}</p>
              </div>
              <div v-for="entry in fileEntries" :key="entry.name"
                class="flex items-center gap-1.5 px-2 py-1 hover:bg-secondary/5 hover:scale-[1.02] cursor-pointer border-b border-outline-variant/20 last:border-0 group transition-transform duration-200 rounded select-none"
                @click="handleEntryClick(entry, $event)" @contextmenu="showFileContextMenu($event, entry)">
                <span class="material-symbols-outlined text-[16px] shrink-0"
                  :class="entry.name === '..' ? 'text-secondary' : (entry.isDir ? 'text-secondary' : 'text-on-surface-variant/60')">{{ entry.name === '..' ? 'arrow_back' : (entry.isDir ? 'folder' : 'description') }}</span>
                <span class="flex-1 truncate font-mono text-[12px] text-on-surface" :class="entry.name === '..' ? 'text-secondary' : ''">{{ entry.name }}</span>
                <div v-if="entry.name !== '..'" class="flex gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
                  <button class="glass-button p-0.5 rounded select-none" :title="t('device.download')" @click.stop="entry.isDir ? downloadDir(entry.name) : downloadFile(entry.name)">
                    <span class="material-symbols-outlined text-[14px]">download</span>
                  </button>
                  <button v-if="!entry.isDir" class="glass-button p-0.5 rounded select-none" :title="t('device.edit')" @click.stop="editFile(entry.name)">
                    <span class="material-symbols-outlined text-[14px]">edit</span>
                  </button>
                  <button class="glass-button p-0.5 rounded select-none" :title="t('device.delete')" @click.stop="confirmThen(`${t('device.delete')} ${entry.name}?`, () => deleteFile(entry.name))">
                    <span class="material-symbols-outlined text-[14px] text-error">delete</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Device Dropdown (teleported to body to escape glass-panel backdrop-filter) -->
    <Teleport to="body">
      <div v-if="showDeviceDropdown" class="fixed inset-0 z-50" @click="showDeviceDropdown = false"></div>
      <div v-if="showDeviceDropdown" class="fixed z-50 bg-white rounded-lg p-1 max-h-48 overflow-y-auto custom-scrollbar shadow-lg min-w-[200px]"
        :style="{ top: deviceDropdownPos.top + 'px', left: deviceDropdownPos.left + 'px' }">
        <button v-for="d in devices" :key="d.serial"
          class="w-full flex items-center gap-2 px-2 py-1.5 rounded font-caption text-caption text-on-surface hover:bg-gray-100 select-none text-left"
          @mousedown.prevent @click="selectDevice(d); showDeviceDropdown = false">
          <div class="w-2 h-2 rounded-full shrink-0" :class="d.status === 'online' ? 'bg-success-indicator' : 'bg-outline-variant'"></div>
          <span class="truncate flex-1">{{ d.name }}</span>
          <span class="text-[10px] text-on-surface-variant/50 truncate max-w-[80px]">{{ d.serial }}</span>
          <span class="material-symbols-outlined text-[12px] text-on-surface-variant hover:text-error ml-1 shrink-0"
            @click.stop="disconnectDeviceHandler(d.serial)">close</span>
        </button>
      </div>
    </Teleport>

    <!-- Preview Dialog -->
    <Teleport to="body">
      <div v-if="previewDialog.show" class="fixed inset-0 z-50 flex items-center justify-center">
        <div class="absolute inset-0 bg-black/10 backdrop-blur-sm" @click="cancelPreview"></div>
        <div class="glass-panel rounded-[2rem] p-3 lg:p-4 xl:p-6 w-[95vw] lg:w-[90vw] max-w-7xl max-h-[85vh] lg:max-h-[90vh] relative z-10 bg-white/60 flex flex-col">
          <div class="flex justify-between items-center mb-2 shrink-0">
            <h3 class="font-label-md text-label-md text-on-surface font-semibold truncate select-none">{{ previewDialog.name }}</h3>
            <div class="flex items-center gap-1 shrink-0">
              <span class="font-caption text-caption text-on-surface-variant/60 select-none text-[11px]">{{ Math.round(previewScale * 100) }}%</span>
              <button class="glass-button p-1 rounded-lg select-none" :disabled="previewScale <= 0.25" @click.stop="zoomPreviewOut">
                <span class="material-symbols-outlined text-[16px]">zoom_out</span>
              </button>
              <button class="glass-button p-1 rounded-lg select-none" @click.stop="resetPreviewScale">
                <span class="material-symbols-outlined text-[16px]">zoom_in_map</span>
              </button>
              <button class="glass-button p-1 rounded-lg select-none" :disabled="previewScale >= 5" @click.stop="zoomPreviewIn">
                <span class="material-symbols-outlined text-[16px]">zoom_in</span>
              </button>
              <span class="w-px h-4 bg-outline-variant/30 mx-1"></span>
              <button class="glass-button px-3 py-1.5 rounded-lg font-label-md text-label-md flex items-center gap-1 select-none" @click.stop="editFile(previewDialog.name)">
                <span class="material-symbols-outlined text-[16px]">edit</span>{{ t('device.edit') }}
              </button>
              <button class="glass-button p-1.5 rounded-lg select-none" @click.stop="cancelPreview">
                <span class="material-symbols-outlined text-[20px]">close</span>
              </button>
            </div>
          </div>
          <div v-if="previewDialog.loading" class="flex-1 flex flex-col items-center justify-center gap-3">
            <span class="w-6 h-6 border-2 border-secondary border-t-transparent rounded-full animate-spin"></span>
            <button class="glass-button px-4 py-1.5 rounded-lg font-label-md text-label-md flex items-center gap-1 select-none" @click.stop="cancelPreview">
              <span class="material-symbols-outlined text-[16px]">close</span>{{ t('device.cancel') }}
            </button>
          </div>
          <div v-else-if="previewDialog.content" ref="previewContainerRef" class="flex-1 min-h-0 flex items-center justify-center overflow-auto">
            <div v-if="isAudioFile(previewDialog.name)" class="flex items-center justify-center p-4 w-full max-w-lg">
              <audio :src="previewDialog.content" controls autoplay class="w-full"></audio>
            </div>
            <div v-else class="flex items-center justify-center min-w-0 min-h-0" :style="{ transform: `scale(${previewScale})`, transformOrigin: 'center center' }">
              <img v-if="isImageFile(previewDialog.name)" :src="previewDialog.content" class="max-w-full max-h-full object-contain rounded-lg select-none" draggable="false" />
              <video v-else :src="previewDialog.content" controls autoplay class="max-w-full max-h-full rounded-lg"></video>
            </div>
          </div>
          <div v-else class="flex-1 flex items-center justify-center text-on-surface-variant/50">
            <span class="font-body-sm text-body-sm">{{ t('device.previewNotAvailable') }}</span>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- File Context Menu -->
    <Teleport to="body">
      <div v-if="fileContextMenu.show" class="fixed inset-0 z-50" @click="closeFileContextMenu" @contextmenu.prevent="closeFileContextMenu"></div>
      <div v-if="fileContextMenu.show" class="fixed z-50 bg-white border border-outline-variant rounded-lg py-1 min-w-[160px] shadow-lg"
        :style="{ top: fileContextMenu.y + 'px', left: fileContextMenu.x + 'px' }">
        <button class="w-full flex items-center gap-2 px-3 py-1.5 font-body-sm text-body-sm text-on-surface hover:bg-gray-100 select-none text-left" @click="copyFilePath(fileContextMenu.entry!)">
          <span class="material-symbols-outlined text-[16px] text-on-surface-variant">content_copy</span>{{ t('device.copyPath') }}
        </button>
        <div class="border-t border-outline-variant/30 my-1"></div>
        <button class="w-full flex items-center gap-2 px-3 py-1.5 font-body-sm text-body-sm text-on-surface hover:bg-gray-100 select-none text-left"
          @click="fileContextMenu.entry!.isDir ? downloadDir(fileContextMenu.entry!.name) : downloadFile(fileContextMenu.entry!.name); closeFileContextMenu()">
          <span class="material-symbols-outlined text-[16px] text-on-surface-variant">download</span>{{ t('device.download') }}
        </button>
        <button v-if="!fileContextMenu.entry!.isDir" class="w-full flex items-center gap-2 px-3 py-1.5 font-body-sm text-body-sm text-on-surface hover:bg-gray-100 select-none text-left"
          @click="editFile(fileContextMenu.entry!.name); closeFileContextMenu()">
          <span class="material-symbols-outlined text-[16px] text-on-surface-variant">edit</span>{{ t('device.edit') }}
        </button>
        <div class="border-t border-outline-variant/30 my-1"></div>
        <button class="w-full flex items-center gap-2 px-3 py-1.5 font-body-sm text-body-sm text-error hover:bg-red-50 select-none text-left"
          @click="confirmThen(`${t('device.delete')} ${fileContextMenu.entry!.name}?`, () => deleteFile(fileContextMenu.entry!.name)); closeFileContextMenu()">
          <span class="material-symbols-outlined text-[16px]">delete</span>{{ t('device.delete') }}
        </button>
      </div>
    </Teleport>

    <!-- File Edit Dialog -->
    <Teleport to="body">
      <Transition name="fade">
        <div v-if="fileEditDialog.show" class="fixed inset-0 z-50 flex items-center justify-center" @click.self="fileEditDialog.show = false">
          <div class="absolute inset-0 bg-black/10 backdrop-blur-sm"></div>
          <div class="glass-panel rounded-[2rem] p-4 w-full max-w-6xl h-[85vh] relative z-10 bg-white/60 flex flex-col">
            <div class="flex justify-between items-center mb-2 shrink-0">
              <div class="flex items-center gap-2 min-w-0">
                <h3 class="font-label-md text-label-md text-on-surface font-semibold truncate select-none">{{ fileEditDialog.filePath }}</h3>
                <span v-if="fileEditDialog.loading" class="w-3.5 h-3.5 border-2 border-secondary border-t-transparent rounded-full animate-spin"></span>
              </div>
              <div class="flex gap-2 shrink-0">
                <button class="glass-button px-3 py-1.5 rounded-lg font-label-md text-label-md flex items-center gap-1 select-none" :disabled="fileEditDialog.loading" @click="saveEditedFile">
                  <span class="material-symbols-outlined text-[16px]">save</span>{{ t('device.save') }}
                </button>
                <button class="glass-button px-3 py-1.5 rounded-lg font-label-md text-label-md flex items-center gap-1 select-none" @click="downloadFileFromEdit">
                  <span class="material-symbols-outlined text-[16px]">download</span>{{ t('device.download') }}
                </button>
                <button class="glass-button p-1.5 rounded-lg select-none" @click="fileEditDialog.show = false">
                  <span class="material-symbols-outlined text-[20px]">close</span>
                </button>
              </div>
            </div>
            <div v-if="fileEditDialog.loading" class="flex-1 flex items-center justify-center bg-[#1a1c1d] rounded-xl">
              <div class="flex flex-col items-center gap-3">
                <span class="w-6 h-6 border-2 border-white/40 border-t-white rounded-full animate-spin"></span>
                <span class="font-body-sm text-body-sm text-gray-400">{{ t('device.readingFile') }}</span>
              </div>
            </div>
            <textarea v-show="!fileEditDialog.loading" v-model="fileEditDialog.content"
              class="flex-1 w-full bg-[#1a1c1d] text-gray-200 rounded-xl p-4 font-mono text-[14px] leading-relaxed border-0 focus:ring-2 focus:ring-secondary/30 resize-none select-text"
              spellcheck="false"></textarea>
          </div>
        </div>
      </Transition>
    </Teleport>
    </div>

    <!-- Info Query Dialog -->
    <Teleport to="body">
      <Transition name="fade">
        <div v-if="infoDialog.show" class="fixed inset-0 z-50 flex items-center justify-center" @click.self="infoDialog.show = false">
          <div class="absolute inset-0 bg-black/10 backdrop-blur-sm"></div>
          <div class="glass-panel rounded-[2rem] p-6 w-full max-w-xl max-h-[80vh] relative z-10 bg-white/60 overflow-y-auto">
            <div class="flex justify-between items-center mb-4">
              <h3 class="font-label-lg text-label-lg text-on-surface font-semibold select-none">{{ infoDialog.title }}</h3>
              <button class="glass-button p-1 rounded select-none" @click="infoDialog.show = false">
                <span class="material-symbols-outlined text-[18px]">close</span>
              </button>
            </div>
            <div class="space-y-1.5">
              <div v-for="(item, idx) in infoDialog.entries" :key="idx" class="border-b border-outline-variant/20 py-1.5 last:border-0">
                <div class="flex flex-col gap-0.5">
                  <span class="font-label-md text-label-md text-on-surface font-medium text-[13px] break-all">{{ item.key }}</span>
                  <div class="flex items-start gap-1">
                    <span class="font-body-sm text-body-sm text-secondary break-all text-[12px]">{{ item.value }}</span>
                    <button v-if="item.raw" class="shrink-0 text-[11px] text-secondary hover:text-secondary/70 select-none" @click="toggleInfoExpand(idx)">
                      <span class="material-symbols-outlined text-[14px]">{{ infoDialogExpanded.has(idx) ? 'expand_less' : 'expand_more' }}</span>
                    </button>
                  </div>
                </div>
                <pre v-if="item.raw && infoDialogExpanded.has(idx)" class="mt-1 p-1.5 bg-black/5 rounded text-[11px] font-mono whitespace-pre-wrap break-all max-h-32 overflow-y-auto select-text">{{ item.raw }}</pre>
              </div>
            </div>
          </div>
        </div>
      </Transition>

      <!-- Result Dialog -->
      <Transition name="fade">
        <div v-if="resultDialog.show" class="fixed inset-0 z-50 flex items-center justify-center" @click.self="resultDialog.show = false">
          <div class="absolute inset-0 bg-black/10 backdrop-blur-sm"></div>
          <div class="glass-panel rounded-[2rem] p-6 w-full max-w-lg relative z-10 bg-white/60">
            <div class="flex justify-between items-center mb-3">
              <h3 class="font-label-lg text-label-lg text-on-surface font-semibold select-none">{{ resultDialog.title }}</h3>
              <button class="glass-button p-1 rounded select-none" @click="resultDialog.show = false">
                <span class="material-symbols-outlined text-[18px]">close</span>
              </button>
            </div>
            <pre class="bg-black/5 rounded-xl p-3 text-[12px] font-mono whitespace-pre-wrap break-all max-h-64 overflow-y-auto mb-3 select-text">{{ resultDialog.content }}</pre>
            <div class="flex gap-2 justify-end">
              <button class="glass-button px-3 py-1 rounded-lg font-label-md text-label-md select-none" @click="resultDialog.show = false">{{ t('device.close') }}</button>
              <button class="glass-button px-3 py-1 rounded-lg font-label-md text-label-md flex items-center gap-1 select-none" @click="copyToClipboard(resultDialog.content); showToast(t('device.copied'))">
                <span class="material-symbols-outlined text-[14px]">content_copy</span>{{ t('device.copy') }}
              </button>
            </div>
          </div>
        </div>
      </Transition>

      <!-- App Detail Dialog -->
      <Transition name="fade">
        <div v-if="appDetailDialog.show" class="fixed inset-0 z-50 flex items-center justify-center" @click.self="appDetailDialog.show = false">
          <div class="absolute inset-0 bg-black/10 backdrop-blur-sm"></div>
          <div class="glass-panel rounded-[2rem] p-6 w-full max-w-lg relative z-10 bg-white/60">
            <div class="flex justify-between items-center mb-3">
              <h3 class="font-label-lg text-label-lg text-on-surface font-semibold break-all select-none">{{ appDetailDialog.title }}</h3>
              <button class="glass-button p-1 rounded shrink-0 select-none" @click="appDetailDialog.show = false">
                <span class="material-symbols-outlined text-[18px]">close</span>
              </button>
            </div>
            <div class="space-y-1.5">
              <div v-for="(item, idx) in appDetailDialog.entries" :key="idx" class="flex border-b border-outline-variant/20 py-1.5 last:border-0">
                <span class="font-label-md text-label-md text-on-surface font-medium min-w-[90px] text-[13px] shrink-0">{{ item.key }}</span>
                <span class="font-body-sm text-body-sm text-on-surface-variant break-all text-[12px] font-mono">{{ item.value }}</span>
              </div>
            </div>
            <div class="flex gap-2 justify-end mt-4">
              <button class="glass-button px-3 py-1 rounded-lg font-label-md text-label-md select-none" @click="appDetailDialog.show = false">{{ t('device.close') }}</button>
              <button class="glass-button px-3 py-1 rounded-lg font-label-md text-label-md flex items-center gap-1 select-none" @click="copyToClipboard(appDetailDialog.pkg); showToast(t('device.pkgCopied'))">
                <span class="material-symbols-outlined text-[14px]">content_copy</span>{{ t('device.copyPkgName') }}
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- APK Install Dialog -->
    <Teleport to="body">
      <Transition name="fade">
        <div v-if="apkDialogOpen" class="fixed inset-0 z-50 flex items-center justify-center" @click.self="closeApkDialog">
          <div class="absolute inset-0 bg-black/10 backdrop-blur-sm pointer-events-none"></div>
          <div class="glass-panel rounded-[2rem] p-6 w-full max-w-md relative z-10 bg-white/60">
            <div class="flex justify-between items-center mb-4">
              <h3 class="font-label-md text-label-md text-on-surface font-semibold flex items-center gap-1.5 select-none">
                <span class="material-symbols-outlined text-[16px]">upload</span>{{ t('device.installApk') }}
              </h3>
              <button class="glass-button p-1 rounded select-none" @click="closeApkDialog">
                <span class="material-symbols-outlined text-[18px]">close</span>
              </button>
            </div>
            <div class="space-y-4">
              <!-- Drop zone -->
              <div class="border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all"
                :class="apkDragOver ? 'border-secondary bg-secondary/5' : 'border-outline-variant hover:border-secondary/50'"
                @dragover.prevent="apkDragOver = true"
                @dragleave.prevent="apkDragOver = false"
                @drop.prevent="handleApkDrop"
                @click="selectApkFile">
                <span class="material-symbols-outlined text-3xl text-on-surface-variant/40">file_open</span>
                <p v-if="!apkFilePath" class="font-caption text-caption text-on-surface-variant/60 mt-1">{{ t('device.dragApkHint') }}</p>
                <p v-else :title="apkFilePath" class="font-caption text-caption text-secondary font-mono mt-1 truncate">{{ apkFilePath }}</p>
              </div>
              <!-- Overwrite checkbox -->
              <label class="flex items-center gap-2 font-caption text-caption text-on-surface cursor-pointer px-1">
                <input type="checkbox" v-model="reinstallApk" class="accent-secondary select-text" />
                {{ t('device.reinstallApk') }}
              </label>
              <!-- Actions -->
              <div class="flex gap-2 justify-end">
                <button class="glass-button px-4 py-1.5 rounded-lg font-label-md text-label-md select-none" @click="closeApkDialog">{{ t('device.cancel') }}</button>
                <button class="glass-button px-4 py-1.5 rounded-lg font-label-md text-label-md flex items-center gap-1 select-none"
                  :disabled="!apkFilePath || apkInstalling" @click="handleApkInstall">
                  <span v-if="apkInstalling" class="w-3.5 h-3.5 border-2 border-secondary border-t-transparent rounded-full animate-spin"></span>
                  <span v-else class="material-symbols-outlined text-[16px]">upload</span>
                  {{ apkInstalling ? t('device.installing') : t('device.install') }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- Cmd Manager Dialog -->
    <Teleport to="body">
      <Transition name="fade">
        <div v-if="showCmdManager" class="fixed inset-0 z-50 flex items-center justify-center" @click.self="showCmdManager = false">
          <div class="absolute inset-0 bg-black/10 backdrop-blur-sm"></div>
          <div class="glass-panel rounded-[2rem] p-6 w-full max-w-md relative z-10 bg-white/60 max-h-[80vh] flex flex-col">
            <div class="flex justify-between items-center mb-4">
              <h3 class="font-label-md text-label-md text-on-surface font-semibold flex items-center gap-1.5 select-none">
                <span class="material-symbols-outlined text-[16px]">edit_note</span>{{ editingCmdIndex !== null ? (editingCmdIndex === -1 ? t('device.addShortcut') : t('device.editShortcut')) : t('device.manageShortcuts') }}
              </h3>
              <button class="glass-button p-1 rounded select-none" @click="showCmdManager = false; cancelEditCommand()">
                <span class="material-symbols-outlined text-[18px]">close</span>
              </button>
            </div>

            <!-- Edit / Add Form -->
            <div v-if="editingCmdIndex !== null" class="flex flex-col gap-3">
              <input v-model="editingCmdName" class="bg-white/80 border border-outline-variant rounded-lg px-3 py-2 font-caption text-caption text-on-surface font-mono focus:ring-2 focus:ring-secondary/30 w-full select-text"
                :placeholder="t('device.cmdNameHint')" @keyup.enter="saveCustomCommand" />
              <input v-model="editingCmdValue" class="bg-white/80 border border-outline-variant rounded-lg px-3 py-2 font-caption text-caption text-on-surface font-mono focus:ring-2 focus:ring-secondary/30 w-full select-text"
                :placeholder="t('device.cmdHint')" @keyup.enter="saveCustomCommand" />
              <div class="flex gap-2 justify-end pt-2">
                <button class="glass-button px-4 py-2 rounded-lg font-label-md text-label-md select-none" @click="cancelEditCommand">{{ t('device.cancel') }}</button>
                <button class="glass-button px-4 py-2 rounded-lg font-label-md text-label-md select-none" @click="saveCustomCommand">{{ t('device.save') }}</button>
              </div>
            </div>

            <!-- Command List -->
            <div v-else class="flex flex-col gap-2 flex-1 min-h-0">
              <div v-if="customCommands.length === 0" class="text-xs text-on-surface-variant/50 italic p-4 text-center">{{ t('device.noCmds') }}</div>
              <div v-else class="flex-1 overflow-y-auto space-y-2">
                <div v-for="(cmd, idx) in customCommands" :key="idx"
                  class="flex items-center justify-between gap-2 p-3 bg-white/30 rounded-xl">
                  <div class="font-caption text-caption text-on-surface leading-tight truncate min-w-0">{{ cmd.name }}</div>
                  <div class="flex gap-2 shrink-0">
                    <button class="glass-button px-2.5 py-1.5 rounded-lg flex items-center gap-1 text-caption font-caption select-none" :title="t('device.edit')" @click="startEditCustomCommand(idx)">
                      <span class="material-symbols-outlined text-[14px]">edit</span>{{ t('device.edit') }}
                    </button>
                    <button class="glass-button px-2.5 py-1.5 rounded-lg flex items-center gap-1 text-caption font-caption text-error select-none" :title="t('device.delete')" @click="confirmThen(`${t('device.delete')}「${cmd.name}」?`, async () => removeCustomCommand(idx))">
                      <span class="material-symbols-outlined text-[14px]">delete</span>{{ t('device.delete') }}
                    </button>
                  </div>
                </div>
              </div>
              <div class="pt-3 border-t border-outline-variant/30">
                <button class="text-sm text-on-surface-variant hover:text-secondary flex items-center gap-1 transition-colors select-none no-border" @click="addCustomCommand">
                  <span class="material-symbols-outlined text-[16px]">add</span>{{ t('device.addShortcut') }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- Confirm Dialog -->
    <Teleport to="body">
      <Transition name="fade">
        <div v-if="confirmDialog.show" class="fixed inset-0 z-50 flex items-center justify-center" @click.self="confirmDialog.onCancel()">
          <div class="absolute inset-0 bg-black/10 backdrop-blur-sm"></div>
          <div class="glass-panel rounded-[2rem] p-6 w-full max-w-sm relative z-10 bg-white/60">
            <div class="flex items-center gap-3 mb-4">
              <span class="material-symbols-outlined text-[24px] text-error">warning</span>
              <h3 class="font-headline-md text-headline-md text-on-surface font-semibold select-none">{{ confirmDialog.title }}</h3>
            </div>
            <div class="flex gap-2 justify-end">
              <button class="glass-button px-4 py-2 rounded-lg font-label-md text-label-md select-none" @click="confirmDialog.onCancel()">{{ t('device.cancel') }}</button>
              <button class="px-4 py-2 rounded-lg font-label-md text-label-md bg-error/10 text-error border border-error/20 select-none" @click="confirmDialog.onConfirm()">{{ t('device.confirm') }}</button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- Command Execution Dialog -->
    <Teleport to="body">
      <Transition name="fade">
        <div v-if="cmdExec.show" class="fixed top-4 left-1/2 -translate-x-1/2 z-[100] w-[420px] max-w-[90vw]" @mouseenter="pauseCmdExecAutoClose" @mouseleave="resumeCmdExecAutoClose">
          <div class="glass-panel rounded-xl px-4 py-3 shadow-xl">
            <div class="flex items-center justify-between gap-2 mb-1">
              <div class="flex items-center gap-2 min-w-0">
                <span v-if="cmdExec.running" class="w-3.5 h-3.5 border-2 border-secondary border-t-transparent rounded-full animate-spin shrink-0"></span>
                <span v-else class="material-symbols-outlined text-[16px] text-success-indicator shrink-0">check_circle</span>
                <span class="font-label-md text-label-md text-on-surface font-medium truncate">{{ cmdExec.title }}</span>
              </div>
              <button v-if="!cmdExec.running" class="glass-button p-0.5 rounded-full shrink-0 select-none" @click="closeCmdExec">
                <span class="material-symbols-outlined text-[14px]">close</span>
              </button>
            </div>
            <div v-if="cmdExec.command" class="text-green-600/80 font-mono text-[11px] mb-1.5 pb-1.5 border-b border-outline-variant/20">$ {{ cmdExec.command }}</div>
            <pre class="font-mono text-[11px] text-on-surface-variant max-h-[200px] overflow-y-auto custom-scrollbar whitespace-pre-wrap leading-relaxed select-text">{{ cmdExec.output }}</pre>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- Toast -->
    <Teleport to="body">
      <Transition name="fade">
        <div v-if="toast.show" class="fixed bottom-8 left-1/2 -translate-x-1/2 z-50 glass-panel rounded-full px-5 py-2.5 flex items-center gap-2 shadow-lg">
          <span v-if="toast.type === 'loading'" class="material-symbols-outlined text-[18px] text-secondary animate-spin">progress_activity</span>
          <span v-else class="material-symbols-outlined text-[18px]"
            :class="toast.type === 'error' ? 'text-error' : 'text-success-indicator'">{{ toast.type === 'error' ? 'error' : 'check_circle' }}</span>
          <span class="font-body-md text-body-md text-on-surface">{{ toast.message }}</span>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from "vue";
import { invoke } from "@tauri-apps/api/core";
import { getCurrentWebviewWindow } from "@tauri-apps/api/webviewWindow";
import { useAdb, type DeviceProperties } from "@/composables/useAdb";
import { useI18n } from "@/composables/useI18n";

const { t } = useI18n();
// preview dialog & drag-drop keys will be in useI18n.ts

const appWindow = getCurrentWebviewWindow();
const listenTarget = { target: { kind: 'WebviewWindow' as const, label: appWindow.label } };

interface ScriptResult { stdout: string; stderr: string; exit_code: number; }
import { addInputHistory, getInputHistory, saveLogSession, getRunningLogSessions, removeLogSession } from "@/services/database";

const {
  listDevices, shell, installApk, uninstallApk, pushFile, pullFile, reboot, screenshot,
  connectDevice, disconnectDevice, rebootRecovery, rebootBootloader, rootDevice: adbRoot,
  remountDevice: adbRemount, getProperties, inputKeyevent, inputText: adbInputText,
  listPackages, startApp: adbStartApp, stopApp: adbStopApp, clearAppData,
  logcatClear, logcat, getAppInfo, logcatBufferResize, bugreport, dmesg,
  startScreenrecord, killServer, startServer, createZip, listDirectory,
} = useAdb();

// ── AppInfo interface + sortApps (matches web-adb-tool sort order) ──
interface AppInfo { package_name: string; version_name?: string; version_code?: string; }
function sortApps(apps: AppInfo[]): AppInfo[] {
  return [...apps].sort((a, b) => {
    const aPkg = a.package_name.toLowerCase();
    const bPkg = b.package_name.toLowerCase();
    if (aPkg.includes('overlay') && !bPkg.includes('overlay')) return 1;
    if (!aPkg.includes('overlay') && bPkg.includes('overlay')) return -1;
    const bigFour = ['com.netflix.ninja', 'disney', 'youtube', 'amazonvideo'];
    const aBig = bigFour.some(s => aPkg.includes(s));
    const bBig = bigFour.some(s => bPkg.includes(s));
    if (aBig && !bBig) return -1;
    if (!aBig && bBig) return 1;
    const priority = ['com.whaletv.launcher','com.zeasn.whaleos.settings','com.whaletv.aivoice','com.zeasn.tv.cast','com.zeasn.tokenapp','com.zeasn.deviceportal.asdprovider.certified'];
    const aIdx = priority.indexOf(a.package_name);
    const bIdx = priority.indexOf(b.package_name);
    if (aIdx !== -1 && bIdx !== -1) return aIdx - bIdx;
    if (aIdx !== -1) return -1;
    if (bIdx !== -1) return 1;
    if (aPkg.includes('whaletv') && !bPkg.includes('whaletv')) return -1;
    if (!aPkg.includes('whaletv') && bPkg.includes('whaletv')) return 1;
    if ((aPkg.includes('zeasn') || aPkg.includes('rlaxxtv')) && !(bPkg.includes('zeasn') || bPkg.includes('rlaxxtv'))) return -1;
    if (!(aPkg.includes('zeasn') || aPkg.includes('rlaxxtv')) && (bPkg.includes('zeasn') || bPkg.includes('rlaxxtv'))) return 1;
    return aPkg.localeCompare(bPkg);
  });
}
async function copyToClipboard(text: string) {
  try { await navigator.clipboard.writeText(text); return true; } catch { return false; }
}

// ── Tabs ──
const tabs = computed(() => [
  { key: 'common', label: t('device.commonCommands'), icon: 'dashboard' },
  { key: 'other', label: t('device.otherCommands'), icon: 'more_horiz' },
]);
const activeTab = ref('common');

// ── Toast ──
const toast = ref({ show: false, message: "", type: "success" as "success" | "error" | "loading" });
let toastTimer: number | null = null;
function showToast(message: string, type: "success" | "error" | "loading" = "success") {
  toast.value = { show: true, message, type };
  if (toastTimer) clearTimeout(toastTimer);
  if (type !== "loading") {
    toastTimer = window.setTimeout(() => { toast.value.show = false; }, 2500);
  }
}
function hideToast() {
  if (toastTimer) clearTimeout(toastTimer);
  toast.value.show = false;
}

// ── Confirm Dialog ──
const confirmDialog = ref({ show: false, title: "", onConfirm: () => {}, onCancel: () => {} });
function confirmThen(title: string, action?: () => Promise<void>): Promise<boolean> {
  return new Promise((resolve) => {
    confirmDialog.value = {
      show: true,
      title,
      onConfirm: async () => {
        confirmDialog.value.show = false;
        if (action) await action();
        resolve(true);
      },
      onCancel: () => {
        confirmDialog.value.show = false;
        resolve(false);
      },
    };
  });
}

// ── Command Execution Dialog ──
const cmdExec = ref({ show: false, title: "", command: "", output: "", running: false });
let cmdExecTimeout: ReturnType<typeof setTimeout> | null = null;
function showCmdExec(title: string, command = "") {
  if (cmdExecTimeout) clearTimeout(cmdExecTimeout);
  cmdExec.value = { show: true, title, command, output: "", running: true };
}
function appendCmdExec(text: string) {
  cmdExec.value.output += text + "\n";
}
function finishCmdExec(summary?: string) {
  if (summary) cmdExec.value.output += summary + "\n";
  cmdExec.value.running = false;
  scheduleCmdExecClose();
}
function scheduleCmdExecClose() {
  if (cmdExecTimeout) clearTimeout(cmdExecTimeout);
  cmdExecTimeout = setTimeout(() => { cmdExec.value.show = false; }, 3000);
}
function pauseCmdExecAutoClose() {
  if (cmdExecTimeout) { clearTimeout(cmdExecTimeout); cmdExecTimeout = null; }
}
function resumeCmdExecAutoClose() {
  if (!cmdExec.value.running && cmdExec.value.show) scheduleCmdExecClose();
}
function closeCmdExec() {
  if (cmdExecTimeout) clearTimeout(cmdExecTimeout);
  cmdExec.value.show = false;
}

// ── Loading states ──
const scanLoading = ref(false);
const pkgLoading = ref(false);
const connecting = ref(false);
const recordingLoading = ref(false);
let versionGen = 0;

// ── Device state ──
interface DeviceItem { serial: string; name: string; status: "online" | "offline"; os: string; }
const devices = ref<DeviceItem[]>([]);
const selectedDevice = ref<DeviceItem | null>(null);
const showDeviceDropdown = ref(false);
const deviceDropdownBtnRef = ref<HTMLElement | null>(null);
const deviceDropdownPos = ref({ top: 0, left: 0 });
function toggleDeviceDropdown() {
  if (showDeviceDropdown.value) { showDeviceDropdown.value = false; return; }
  if (deviceDropdownBtnRef.value) {
    const r = deviceDropdownBtnRef.value.getBoundingClientRect();
    deviceDropdownPos.value = { top: r.bottom + 4, left: Math.max(4, Math.min(r.left, window.innerWidth - 210)) };
  }
  showDeviceDropdown.value = true;
}
const deviceProps = ref<DeviceProperties | null>(null);
const connectAddress = ref("");
const showConnectIpHistory = ref(false);
const connectIpHistory = ref<string[]>([]);
const connectIpInputRef = ref<HTMLElement | null>(null);
const connectIpDropdownPos = ref({ top: 0, left: 0, width: 0 });

const devicePropList = computed(() => {
  if (!deviceProps.value) return {};
  const p = deviceProps.value;
  return {
    [t('device.model')]: p.model, [t('device.brand')]: p.brand, [t('device.deviceName')]: p.device, [t('device.product')]: p.product,
    "Android": `Android ${p.android_version} (SDK ${p.sdk_version})`,
    [t('device.resolution')]: p.resolution, [t('device.density')]: p.density, "Build": p.build_id,
  };
});

// ── Text Input + History ──
const textInputRef = ref<HTMLInputElement | null>(null);
const inputTextValue = ref("");
const showTextHistory = ref(false);
const textHistory = ref<string[]>([]);
function hideTextHistoryDelayed() { setTimeout(() => { showTextHistory.value = false; }, 200); }
function selectTextHistory(v: string) { inputTextValue.value = v; showTextHistory.value = false; }
async function loadTextHistory() {
  const entries = await getInputHistory('input_text');
  textHistory.value = entries.map(e => e.value);
}

// ── APK Install ──
const reinstallApk = ref(false);
const loadingForeground = ref(false);
const apkDialogOpen = ref(false);
const apkDragOver = ref(false);
const apkFilePath = ref("");
const apkInstalling = ref(false);
const apkTempPaths = ref<string[]>([]);

async function cleanApkTempPath(path: string) {
  if (!path) return;
  const idx = apkTempPaths.value.indexOf(path);
  if (idx >= 0) apkTempPaths.value.splice(idx, 1);
  try {
    const { remove } = await import('@tauri-apps/plugin-fs');
    await remove(path);
  } catch {}
}

// ── Apps ──
interface AppEntry { package_name: string; version_name?: string; version_code?: string; }
const apps = ref<AppEntry[]>([]);
const showThirdParty = ref(false);

const showAppSearchHistory = ref(false);
const appSearchHistory = ref<string[]>([]);
const appPage = ref(1);

const loadedVersions = ref(new Set<string>());
const appLoadingState = ref<Record<string, Record<string, boolean>>>({});
const appListContainer = ref<HTMLElement | null>(null);
const appItemHeight = ref(28);
const appItemMeasured = ref(false);
const maxVisibleApps = ref(14);
const appListMaxHeight = ref(400);
const queryPackageName = ref("");
function measureAppItem(el: HTMLElement) {
  if (appItemMeasured.value) return;
  const h = el.getBoundingClientRect().height;
  if (h > 5) { appItemHeight.value = h; appItemMeasured.value = true; recalcAppPageSize(); }
}
function recalcAppPageSize() {
  if (!appListContainer.value) return;
  const panel = appListContainer.value.closest('.glass-panel') as HTMLElement;
  if (!panel) return;
  const panelH = panel.getBoundingClientRect().height;
  if (panelH < 50) return;
  const listOffsetTop = appListContainer.value.getBoundingClientRect().top - panel.getBoundingClientRect().top;
  const avail = panelH - listOffsetTop - 8;
  const newCount = Math.max(4, Math.floor(avail / appItemHeight.value));
  if (avail > 5) {
    maxVisibleApps.value = newCount;
    appListMaxHeight.value = avail;
  }
}

const sortedApps = computed(() => sortApps(apps.value));
const filteredApps = computed(() => {
  const q = queryPackageName.value.trim().toLowerCase();
  if (!q) return sortedApps.value;
  return sortedApps.value.filter(a => a.package_name.toLowerCase().includes(q));
});
const totalPages = computed(() => Math.max(1, Math.ceil(filteredApps.value.length / maxVisibleApps.value)));
const currentPageApps = computed(() => filteredApps.value.slice((appPage.value - 1) * maxVisibleApps.value, appPage.value * maxVisibleApps.value));

function setAppLoading(pkg: string, action: string, loading: boolean) {
  appLoadingState.value = { ...appLoadingState.value, [pkg]: { ...appLoadingState.value[pkg], [action]: loading } };
}

function onAppSearchInput() { appPage.value = 1; }
function hideAppSearchHistoryDelayed() { setTimeout(() => { showAppSearchHistory.value = false; }, 200); }
function selectAppSearchHistory(v: string) { queryPackageName.value = v; showAppSearchHistory.value = false; }
let lastFilterKey = "";
watch(filteredApps, () => {
  const key = queryPackageName.value.trim().toLowerCase() + "|" + filteredApps.value.length;
  if (key !== lastFilterKey) { lastFilterKey = key; appPage.value = 1; }
  nextTick(recalcAppPageSize);
});
watch(activeTab, () => {
  nextTick(recalcAppPageSize);
  if (activeTab.value === 'other') loadFileList();
});
async function loadAppSearchHistory() {
  const entries = await getInputHistory('app_search');
  appSearchHistory.value = entries.map(e => e.value);
  showAppSearchHistory.value = true;
}

// ── File Browser + History ──
const remotePath = ref("/");
const remotePathInputRef = ref<HTMLInputElement | null>(null);
const showRemotePathHistory = ref(false);
const remotePathHistory = ref<string[]>([]);
function hideRemotePathHistoryDelayed() { setTimeout(() => { showRemotePathHistory.value = false; }, 200); }
function selectRemotePathHistory(v: string) { remotePath.value = v; showRemotePathHistory.value = false; }
async function loadRemotePathHistory() {
  const entries = await getInputHistory('remote_path');
  remotePathHistory.value = entries.map(e => e.value);
}

// ── Custom Commands (auto-detect type, support multi-command chaining) ──
interface CustomCommand { name: string; command: string; }
const customCommands = ref<CustomCommand[]>([]);
const editingCmdIndex = ref<number | null>(null);
const editingCmdName = ref("");
const editingCmdValue = ref("");
const showCmdManager = ref(false);
function loadCustomCommands() {
  try {
    const stored = localStorage.getItem("test-space:adb-custom-commands");
    if (stored) customCommands.value = JSON.parse(stored);
  } catch {}
}
function saveCustomCommands() {
  localStorage.setItem("test-space:adb-custom-commands", JSON.stringify(customCommands.value));
}
function addCustomCommand() { editingCmdIndex.value = -1; editingCmdName.value = ""; editingCmdValue.value = ""; }
function startEditCustomCommand(idx: number) {
  editingCmdIndex.value = idx;
  editingCmdName.value = customCommands.value[idx].name;
  editingCmdValue.value = customCommands.value[idx].command;
}
function saveCustomCommand() {
  if (!editingCmdName.value.trim() || !editingCmdValue.value.trim()) return;
  const cmd = { name: editingCmdName.value.trim(), command: editingCmdValue.value.trim() };
  if (editingCmdIndex.value === -1) customCommands.value.push(cmd);
  else if (editingCmdIndex.value !== null) customCommands.value[editingCmdIndex.value] = cmd;
  saveCustomCommands();
  editingCmdIndex.value = null;
}
function cancelEditCommand() { editingCmdIndex.value = null; }
function removeCustomCommand(idx: number) { customCommands.value.splice(idx, 1); saveCustomCommands(); }

async function runOneCommand(cmd: string): Promise<string> {
  if (cmd.startsWith('adb ')) {
    const r = await invoke<ScriptResult>("script_execute_shell", { command: cmd });
    return r.stdout + (r.stderr ? '\n' + r.stderr : '');
  }
  if (selectedDevice.value) {
    try { return await shell(selectedDevice.value.serial, cmd); } catch {}
  }
  try {
    const r = await invoke<ScriptResult>("script_execute_shell", { command: cmd });
    return r.stdout + (r.stderr ? '\n' + r.stderr : '');
  } catch (e: any) {
    throw new Error(t('device.execFailed', { e: String(e) }));
  }
}
async function executeCustomCommand(fullCmd: string) {
  if (!fullCmd.trim()) return;
  const commands = fullCmd.split(/\s*&&\s*|\s*;\s*|\s*&\s*/).filter(c => c.trim());
  showCmdExec(t('device.executingCmd'), fullCmd);
  let ok = true;
  for (let i = 0; i < commands.length; i++) {
    const c = commands[i].trim();
    appendCmdExec(`[${i + 1}/${commands.length}] $ ${c}`);
    try {
      const r = await runOneCommand(c);
      if (r) appendCmdExec(r);
      else appendCmdExec(t('device.cmdNoOutput'));
      if (i < commands.length - 1) appendCmdExec(`--- ${t('device.cmdProgress', { i: String(i + 1), total: String(commands.length) })} ---`);
    } catch (e: any) {
      ok = false;
      appendCmdExec(`${t('device.error')}: ${e}`);
    }
  }
  appendCmdExec(ok ? `─ ${t('device.allCmdsDone')} ─` : `─ ${t('device.someCmdsFailed')} ─`);
  appendCmdExec(`${t('device.exitStatus')}: ${ok ? t('device.success') : t('device.failed')}`);
  cmdExec.value.running = false;
  scheduleCmdExecClose();
  if (ok) showToast(t('device.cmdSuccess'));
  else showToast(t('device.someCmdsFailed'), "error");
}

// ── File Manager (tree view) ──
interface FileEntry { name: string; isDir: boolean; size: string; rawSize: number; }
const dragOverFileList = ref(false);
const fileEntries = ref<FileEntry[]>([]);
function isImageFile(name: string) { return /\.(png|jpg|jpeg|gif|bmp|webp|svg)$/i.test(name); }
function isAudioFile(name: string) { return /\.(flac|mp3|wav|ogg|aac|m4a|wma)$/i.test(name); }
function isMediaFile(name: string) { return isImageFile(name) || isAudioFile(name) || /\.(mp4|webm|ogg|mov|avi|mkv)$/i.test(name); }
function isUnsupportedFile(name: string) { return /\.(apk|exe|dll|so|dylib|bin|dat|db|sqlite|zip|tar|gz|rar|7z|zst|woff2?|ttf|otf|pyc|class|o|a|lib|jar|war|ear|msi|dmg|iso|img|vmdk|vdi|qcow2)$/i.test(name); }
async function handleEntryClick(entry: FileEntry, e: MouseEvent) {
  e.stopPropagation();
  if (entry.name === "..") { await navigateToParent(); return; }
  if (entry.isDir) { await navigateToDir(entry.name); return; }
  if (isMediaFile(entry.name)) { await previewFile(entry); return; }
  if (isUnsupportedFile(entry.name)) { showToast(t('device.unsupportedFile'), 'error'); return; }
  editFile(entry.name);
}
async function navigateToPath() {
  if (!selectedDevice.value || !remotePath.value.trim()) return;
  await addInputHistory('remote_path', remotePath.value);
  remotePathHistory.value = [remotePath.value, ...remotePathHistory.value.filter(h => h !== remotePath.value)].slice(0, 15);
  await loadFileList();
}
async function navigateToDir(name: string) {
  const base = remotePath.value.replace(/\/?$/, '/');
  remotePath.value = base + name.trim();
  await addInputHistory('remote_path', remotePath.value);
  remotePathHistory.value = [remotePath.value, ...remotePathHistory.value.filter(h => h !== remotePath.value)].slice(0, 15);
  await loadFileList();
}
async function navigateToParent() {
  const p = remotePath.value.replace(/\/$/, '');
  const parent = p.substring(0, p.lastIndexOf('/'));
  remotePath.value = parent || '/';
  await loadFileList();
}
function parseLsLine(line: string): { name: string; isDir: boolean; size: string; rawSize: number } | null {
  const parts = line.split(/\s+/);
  if (parts.length < 7) return null;
  const perms = parts[0];
  if (perms.length < 9 || !/^[drwxlst.+-]/.test(perms[0])) return null;
  const isDir = perms[0] === 'd';
  let sizeIdx = 4, nameIdx = 7;
  if (/^\d+$/.test(parts[3]) && parts.length >= 7 && !/^\d+$/.test(parts[4])) {
    sizeIdx = 3; nameIdx = 6;
  } else if (/^\d+$/.test(parts[3]) && parts.length >= 6) {
    sizeIdx = 3; nameIdx = 6;
  }
  const sizeVal = parseInt(parts[sizeIdx]) || 0;
  const sizeFormatted = sizeVal > 1024 ? Math.round(sizeVal / 1024) + 'KB' : sizeVal + 'B';
  const name = parts.slice(nameIdx).join(' ').trim();
  if (!name) return null;
  return { name, isDir, size: sizeFormatted, rawSize: sizeVal };
}
let loadFileListGen = 0;
async function loadFileList() {
  dragOverFileList.value = false;
  if (!selectedDevice.value) return;
  const gen = ++loadFileListGen;
  try {
    const raw = await shell(selectedDevice.value.serial, `ls -la "${remotePath.value}"`);
    if (gen !== loadFileListGen) return;
    const lines = raw.split('\n').filter(l => l.trim() && !l.startsWith('total'));
    const entries = lines.map(l => parseLsLine(l)).filter((e): e is NonNullable<typeof e> => e !== null && e.name !== '.' && e.name !== '..')
      .sort((a, b) => {
        if (a.isDir !== b.isDir) return a.isDir ? -1 : 1;
        return a.name.localeCompare(b.name);
      });
    if (remotePath.value !== '/') entries.unshift({ name: '..', isDir: true, size: '', rawSize: 0 });
    fileEntries.value = entries;
  } catch { fileEntries.value = remotePath.value !== '/' ? [{ name: '..', isDir: true, size: '', rawSize: 0 }] : []; showToast(t('device.dirReadFail'), "error"); }
}
async function uploadFilePath(filePath: string) {
  if (!selectedDevice.value) return;
  try {
    showCmdExec(t('device.uploadFile'), `adb push "${filePath}" "${remotePath.value}"`);
    appendCmdExec(t('device.uploading'));
    await pushFile(selectedDevice.value.serial, filePath, remotePath.value);
    appendCmdExec(t('device.uploadDone'));
    finishCmdExec(t('device.fileUploaded'));
    showToast(t('device.fileUploaded'));
    loadFileList();
  } catch (e: any) { appendCmdExec(`[${t('device.error')}] ${e}`); finishCmdExec(t('device.uploadFailed')); showToast(t('device.uploadFailed'), "error"); }
}
function onFileDragEnter() {
  dragOverFileList.value = true
}

function onFileDragLeave(event: DragEvent) {
  const el = event.currentTarget as HTMLElement
  if (!el.contains(event.relatedTarget as Node)) {
    dragOverFileList.value = false
  }
}

async function onFileDrop(event: DragEvent) {
  dragOverFileList.value = false
  if (!selectedDevice.value || activeTab.value !== 'other') return
  const files = event.dataTransfer?.files
  if (!files || files.length === 0) return

  const uris = event.dataTransfer?.getData('text/uri-list')
  if (uris) {
    const lines = uris.split('\n').map(u => u.trim()).filter(u => u.startsWith('file:///'))
    for (const uri of lines) {
      const path = decodeURIComponent(uri.replace(/^file:\/\/\//, '')).replace(/\r$/, '')
      if (path) {
        await uploadFilePath(path)
        return
      }
    }
  }

  showCmdExec(t('device.uploadFile'), t('device.uploading'))
  const { invoke } = await import('@tauri-apps/api/core')
  for (let i = 0; i < files.length; i++) {
    const file = files[i]
    try {
      const buffer = await file.arrayBuffer()
      await invoke('adb_push_bytes', {
        serial: selectedDevice.value.serial,
        remote: remotePath.value,
        filename: file.name,
        data: Array.from(new Uint8Array(buffer)),
      })
      appendCmdExec(`${t('device.uploadDone')} ${file.name}`)
    } catch (e: any) {
      appendCmdExec(`[${t('device.error')}] ${file.name}: ${e}`)
    }
  }
  finishCmdExec(t('device.fileUploaded'))
  showToast(t('device.fileUploaded'))
  loadFileList()
}

async function uploadFile() {
  if (!selectedDevice.value || !remotePath.value.trim()) return;
  try {
    const { open } = await import("@tauri-apps/plugin-dialog");
    const selected = await open({ multiple: false });
    if (selected) { await uploadFilePath(selected); }
  } catch { showToast(t('device.uploadFailed'), "error"); }
}
async function downloadFile(name: string) {
  if (!selectedDevice.value) return;
  const remoteFile = remotePath.value.replace(/\/?$/, '/') + name.trim();
  try {
    const { save } = await import("@tauri-apps/plugin-dialog");
    const dest = await save({ defaultPath: name });
    if (dest) {
      showCmdExec(t('device.downloadFile'), `adb pull "${remoteFile}" "${dest}"`);
      appendCmdExec(t('device.downloading'));
      await pullFile(selectedDevice.value.serial, remoteFile, dest);
      appendCmdExec(t('device.downloadDone'));
      finishCmdExec(t('device.fileDownloaded'));
      showToast(t('device.fileDownloaded'));
    }
  } catch (e: any) { appendCmdExec(`[${t('device.error')}] ${e}`); finishCmdExec(t('device.downloadFailed')); showToast(t('device.downloadFailed'), "error"); }
}
async function downloadDir(name: string) {
  if (!selectedDevice.value) return;
  const parentPath = remotePath.value.replace(/\/?$/, '');
  const dirPath = parentPath + '/' + name.trim();
  try {
    const { open } = await import("@tauri-apps/plugin-dialog");
    const dest = await open({ directory: true, defaultPath: name });
    if (!dest) return;
    showCmdExec(t('device.downloadDir'), `adb pull "${dirPath}" "${dest}/${name}"`);
    appendCmdExec(t('device.downloading'));
    await pullFile(selectedDevice.value.serial, dirPath, dest);
    appendCmdExec(t('device.downloadDone'));
    finishCmdExec(t('device.dirDownloaded'));
    showToast(t('device.dirDownloaded'));
  } catch (e: any) { appendCmdExec(`[${t('device.error')}] ${e}`); finishCmdExec(t('device.downloadFailed')); showToast(t('device.downloadFailedWith', { e: String(e) }), "error"); }
}
async function deleteFile(name: string) {
  if (!selectedDevice.value) return;
  const remoteFile = remotePath.value.replace(/\/?$/, '/') + name.trim();
  try {
    await shell(selectedDevice.value.serial, `rm -rf "${remoteFile}"`);
    showToast(t("device.fileDeleted"));
    loadFileList();
  } catch { showToast(t("device.deleteFail"), "error"); }
}

// ── File Edit ──
const previewDialog = ref({ show: false, name: "", loading: false, content: "" });
const previewContainerRef = ref<HTMLElement | null>(null);
const fileEditDialog = ref({ show: false, filePath: "", content: "", loading: false, originContent: "" });
const previewScale = ref(1);
let previewGen = 0;
function resetPreviewScale() { previewScale.value = 1; }
function zoomPreviewIn() { previewScale.value = Math.min(previewScale.value + 0.25, 5); }
function zoomPreviewOut() { previewScale.value = Math.max(previewScale.value - 0.25, 0.25); }
function onPreviewWheel(e: WheelEvent) {
  e.preventDefault();
  if (e.deltaY < 0) zoomPreviewIn(); else zoomPreviewOut();
}
watch(() => previewDialog.value.content, async (content) => {
  await nextTick();
  if (content && previewContainerRef.value) {
    previewContainerRef.value.addEventListener('wheel', onPreviewWheel, { passive: false });
  }
});
async function previewFile(entry: FileEntry) {
  if (entry.rawSize > 10 * 1024 * 1024) {
    const ok = await confirmThen(t('device.largeFileConfirm', { name: entry.name }));
    if (!ok) return;
    showToast(t('device.largeFileLoading'), 'loading');
  }
  previewGen++;
  previewDialog.value = { show: true, name: entry.name, loading: true, content: '' };
  previewScale.value = 1;
  await nextTick();
  await loadPreviewContent(entry.name);
  hideToast();
}
function cancelPreview() {
  previewGen++;
  previewDialog.value = { show: false, name: previewDialog.value.name, loading: false, content: '' };
}
async function loadPreviewContent(name: string) {
  if (!selectedDevice.value) return;
  const gen = ++previewGen;
  const filePath = remotePath.value.replace(/\/?$/, '/') + name.trim();
  const vMime: Record<string, string> = { webm: 'video/webm', ogg: 'video/ogg', mp4: 'video/mp4', mov: 'video/quicktime', avi: 'video/x-msvideo', mkv: 'video/x-matroska' };
  const aMime: Record<string, string> = { flac: 'audio/flac', mp3: 'audio/mpeg', wav: 'audio/wav', ogg: 'audio/ogg', aac: 'audio/aac', m4a: 'audio/mp4', wma: 'audio/x-ms-wma' };
  const iMime: Record<string, string> = { jpg: 'jpeg', jpeg: 'jpeg', png: 'png', gif: 'gif', webp: 'webp', bmp: 'bmp', svg: 'svg+xml', ico: 'x-icon' };
  const ext = name.replace(/.*\./, '').toLowerCase();
  try {
    const raw = await shell(selectedDevice.value.serial, `cat "${filePath}" | base64`);
    if (gen !== previewGen) return;
    const mime = isImageFile(name) ? `image/${iMime[ext] || ext}` : (isAudioFile(name) ? (aMime[ext] || 'audio/mpeg') : (vMime[ext] || 'video/mp4'));
    previewDialog.value.content = `data:${mime};base64,${raw.trim()}`;
  } catch { if (gen === previewGen) previewDialog.value.content = ''; }
  if (gen === previewGen) previewDialog.value.loading = false;
}

const fileContextMenu = ref({ show: false, x: 0, y: 0, entry: null as FileEntry | null });
function showFileContextMenu(e: MouseEvent, entry: FileEntry) {
  e.preventDefault();
  e.stopPropagation();
  if (entry.name === '..') return;
  fileContextMenu.value = { show: true, x: e.clientX, y: e.clientY, entry };
}
function closeFileContextMenu() { fileContextMenu.value.show = false; }
async function copyFilePath(entry: FileEntry) {
  const fullPath = remotePath.value.replace(/\/?$/, '/') + entry.name;
  try { await navigator.clipboard.writeText(fullPath); showToast(t('device.copyPath'), 'success'); } catch { showToast(t('device.copyFailed'), 'error'); }
  closeFileContextMenu();
}

async function editFile(name: string) {
  if (!selectedDevice.value) return;
  const remoteFile = remotePath.value.replace(/\/?$/, '/') + name.trim();
  let needLoadingToast = false;
  try {
    const sizeStr = await shell(selectedDevice.value.serial, `wc -c < "${remoteFile}"`);
    const fileSize = parseInt(sizeStr.trim()) || 0;
    if (fileSize > 5 * 1024 * 1024) {
      const ok = await confirmThen(t('device.largeFileConfirm', { name }));
      if (!ok) return;
      showToast(t('device.largeFileLoading'), 'loading');
      needLoadingToast = true;
    }
  } catch {}
  fileEditDialog.value = { show: true, filePath: remoteFile, content: "", loading: true, originContent: "" };
  try {
    const content = await shell(selectedDevice.value.serial, `cat "${remoteFile}"`);
    fileEditDialog.value = { ...fileEditDialog.value, content, originContent: content, loading: false };
  } catch {
    fileEditDialog.value = { ...fileEditDialog.value, content: `// ${t('device.readFileFailed')}`, loading: false };
    showToast(t('device.readFileFailed'), "error");
  }
  if (needLoadingToast) hideToast();
}
async function saveEditedFile() {
  if (!selectedDevice.value || !fileEditDialog.value.filePath) return;
  fileEditDialog.value.loading = true;
  try {
    const tmpName = `tmp_edit_${Date.now()}`;
    const { writeTextFile, remove } = await import("@tauri-apps/plugin-fs");
    const { tempDir, join } = await import("@tauri-apps/api/path");
    const tmpDir = await tempDir();
    const tmpPath = await join(tmpDir, tmpName);
    await writeTextFile(tmpPath, fileEditDialog.value.content);
    await pushFile(selectedDevice.value.serial, tmpPath, fileEditDialog.value.filePath);
    try { await remove(tmpPath); } catch {}
    fileEditDialog.value.loading = false;
    showToast(t("device.fileSaved"));
  } catch (e: any) {
    fileEditDialog.value.loading = false;
    showToast(`${t("device.saveFail")}: ${e}`, "error");
  }
}
async function downloadFileFromEdit() {
  if (!selectedDevice.value || !fileEditDialog.value.filePath) return;
  try {
    const { save } = await import("@tauri-apps/plugin-dialog");
    const name = fileEditDialog.value.filePath.split('/').pop() || 'file';
    const dest = await save({ defaultPath: name });
    if (dest) {
      const { writeTextFile } = await import("@tauri-apps/plugin-fs");
      await writeTextFile(dest, fileEditDialog.value.content);
      showToast(t('device.fileDownloadedToLocal'));
    }
  } catch { showToast(t('device.downloadFailed'), "error"); }
}

// ── Helper: yield to UI thread ──
function yieldToUI() { return new Promise(resolve => setTimeout(resolve, 0)); }

// ── Helper: sanitize shell arguments ──
function sanitizeShellArg(s: string): string {
  return s.replace(/[;&|`$(){}!<>\\'"*?#\n\r\t]/g, '')
}

// ── Information Query ──
const infoLoading = ref("");
const infoDialog = ref({ show: false, title: "", entries: [] as { key: string; value: string; raw?: string }[] });
const infoDialogExpanded = ref(new Set<number>());
function toggleInfoExpand(idx: number) {
  const s = new Set(infoDialogExpanded.value);
  if (s.has(idx)) s.delete(idx); else s.add(idx);
  infoDialogExpanded.value = s;
}

function showDeviceInfoDialog() {
  if (!selectedDevice.value || !deviceProps.value) { showToast(t("device.selectDeviceFirst"), "error"); return; }
  const p = deviceProps.value;
  infoDialog.value = { show: true, title: t('device.deviceInfo'), entries: [
    { key: t('device.serial'), value: selectedDevice.value.serial },
    { key: t('device.model'), value: p.model || "—" },
    { key: t('device.brand'), value: p.brand || "—" },
    { key: t('device.deviceName'), value: p.device || "—" },
    { key: t('device.product'), value: p.product || "—" },
    { key: "Android", value: `${p.android_version || "—"} (SDK ${p.sdk_version || "—"})` },
    { key: t('device.resolution'), value: p.resolution || "—" },
    { key: t('device.density'), value: p.density || "—" },
    { key: "Build", value: p.build_id || "—" },
  ]};
}

// ── Log Preparation (root + buffer resize, always) ──
const logPrepActive = ref(false);
const logPrepMessage = ref("");

async function prepareLogCapture() {
  if (!selectedDevice.value) { showToast(t("device.selectDeviceFirst"), "error"); return false; }
  logPrepActive.value = true;
  try {
    logPrepMessage.value = t("device.executingAdbRoot");
    await adbRoot(selectedDevice.value.serial);
    await yieldToUI();
    logPrepMessage.value = t("device.expandingLogBuffer");
    await logcatBufferResize(selectedDevice.value.serial, 64);
    await yieldToUI();
    return true;
  } catch (e: any) {
    showToast(`${t('device.operationFailed')}: ${e}`, "error");
    return false;
  } finally {
    logPrepActive.value = false;
  }
}

// ── Log Collection (circular buffer, max 500 entries) ──
const MAX_LOG_ENTRIES = 500;
const logcatRunning = ref(false);
const logcatElapsed = ref(0);
let logcatTimeoutId: ReturnType<typeof setTimeout> | null = null;
const logcatBuffer = ref<string[]>([]);
let logcatSerial = "";

const diagRunning = ref(false);
const diagElapsed = ref(0);
let diagTimeoutId: ReturnType<typeof setTimeout> | null = null;
const diagBuffer = ref<string[]>([]);
let diagSerial = "";

const bootLogcatRunning = ref(false);
const bootLogcatElapsed = ref(0);
const bootLogcatStartTime = ref(0);
let bootLogcatTimeoutId: ReturnType<typeof setTimeout> | null = null;
const bootLogcatBuffer = ref<string[]>([]);
const bootLogcatPhase = ref<'wait_for_device' | 'wait_disconnect' | 'wait_reconnect' | 'capturing'>('wait_disconnect');
const bootLogcatSerial = ref<string | null>(null);

// ── Screen Mirror (adb screencap polling) ──
const isMirroring = ref(false);
const mirrorFrameCount = ref(0);
const mirrorMode = ref<'idle' | 'scrcpy' | 'legacy'>('idle');
const mirrorErrorMsg = ref('');
let mirrorCtx: CanvasRenderingContext2D | null = null;
let mirrorUnlisten: (() => void)[] = [];
const mirrorCanvas = ref<HTMLCanvasElement | null>(null);
const mirrorWidth = ref(0);
const mirrorHeight = ref(0);
const deviceWidth = ref(0);
const deviceHeight = ref(0);
const mirrorPopoutActive = ref(false);
const qualityMode = ref<'smooth' | 'quality'>('smooth');
function toggleQualityMode() {
  qualityMode.value = qualityMode.value === 'smooth' ? 'quality' : 'smooth';
}

let mirrorTapX1 = 0, mirrorTapY1 = 0, mirrorTapping = false;

function mirrorCanvasCoords(e: { clientX: number; clientY: number }): { x: number; y: number } | null {
  const canvas = mirrorCanvas.value;
  if (!canvas || mirrorWidth.value === 0 || mirrorHeight.value === 0 || deviceWidth.value === 0) return null;
  const rect = canvas.getBoundingClientRect();
  const imgAspect = mirrorWidth.value / mirrorHeight.value;
  const containerAspect = rect.width / rect.height;
  let displayW: number, displayH: number, offX: number, offY: number;
  if (imgAspect > containerAspect) {
    displayW = rect.width;
    displayH = rect.width / imgAspect;
    offX = 0; offY = (rect.height - displayH) / 2;
  } else {
    displayH = rect.height;
    displayW = rect.height * imgAspect;
    offX = (rect.width - displayW) / 2; offY = 0;
  }
  const imgX = e.clientX - rect.left - offX;
  const imgY = e.clientY - rect.top - offY;
  if (imgX < 0 || imgX > displayW || imgY < 0 || imgY > displayH) return null;
  // Map from video pixel → device pixel
  const vx = Math.round(imgX * (mirrorWidth.value / displayW));
  const vy = Math.round(imgY * (mirrorHeight.value / displayH));
  return {
    x: Math.round(vx * (deviceWidth.value / mirrorWidth.value)),
    y: Math.round(vy * (deviceHeight.value / mirrorHeight.value)),
  };
}

async function handleMirrorPointerDown(e: MouseEvent | Touch) {
  if (!selectedDevice.value) return;
  const coords = mirrorCanvasCoords(e);
  if (!coords) return;
  mirrorTapX1 = coords.x; mirrorTapY1 = coords.y; mirrorTapping = true;
  const { invoke } = await import("@tauri-apps/api/core");
  await invoke("adb_input_tap", { serial: selectedDevice.value.serial, x: coords.x, y: coords.y });
}

async function handleMirrorPointerUp(e: MouseEvent | Touch) {
  if (!selectedDevice.value) return;
  if (!mirrorTapping) return;
  mirrorTapping = false;
  const coords = mirrorCanvasCoords(e);
  if (!coords) return;
  if (Math.abs(coords.x - mirrorTapX1) > 10 || Math.abs(coords.y - mirrorTapY1) > 10) {
    const { invoke } = await import("@tauri-apps/api/core");
    await invoke("adb_input_swipe", { serial: selectedDevice.value.serial, x1: mirrorTapX1, y1: mirrorTapY1, x2: coords.x, y2: coords.y, duration: 200 });
  }
}

async function handleMirrorRightClick() {
  if (!selectedDevice.value) return;
  const { invoke } = await import("@tauri-apps/api/core");
  await invoke("adb_input_keyevent", { serial: selectedDevice.value.serial, keycode: "BACK" });
}

async function mirrorPopout() {
  const { invoke } = await import("@tauri-apps/api/core");
  const { WebviewWindow } = await import("@tauri-apps/api/webviewWindow");
  await stopMirror();
  if (!selectedDevice.value) return;
  const serial = selectedDevice.value.serial;

  // Query device display size for orientation-adaptive window
  let winWidth = 480, winHeight = 800;
  try {
    const [dw, dh] = await invoke<[number, number]>("adb_get_display_size", { serial });
    const isLandscape = dw > dh;
    if (isLandscape) {
      winWidth = 854;
      winHeight = Math.round(854 * (dh / dw));
    } else {
      winHeight = 800;
      winWidth = Math.round(800 * (dw / dh));
    }
  } catch {}

  const win = new WebviewWindow(`mirror-${serial.replace(/[^a-zA-Z0-9_-]/g, '_')}`, {
    url: `/mirror?serial=${serial}&quality=${qualityMode.value}`,
    title: `Screen Mirror - ${serial}`,
    width: winWidth,
    height: winHeight + 220, // extra space for remote control bar
  });
  win.once('tauri://created', () => { mirrorPopoutActive.value = true; });
  win.once('tauri://error', (e) => { console.error("[mirror] popout failed:", e); });
}

// ── Screenshot & Recording ──
const screenshotDataUrl = ref("");
const isRecording = ref(false);
const recordingFilename = ref("");

// ── Device auto-refresh ──
let autoRefreshId: ReturnType<typeof setInterval> | null = null;

// ── Custom commands stored in localStorage

// ── Device operations ──
async function scanDevices(silent = false) {
  scanLoading.value = true;
  showDeviceDropdown.value = false;
  try {
    const adbDevices = await listDevices();
    devices.value = adbDevices.map(d => ({
      serial: d.serial, name: d.model || d.serial,
      status: d.status === "device" ? "online" as const : "offline" as const, os: d.android_version || "Android",
    }));
    if (selectedDevice.value && !devices.value.some(d => d.serial === selectedDevice.value!.serial)) {
      selectedDevice.value = null;
      apps.value = [];
      deviceProps.value = null;
    }
    if (devices.value.length > 0 && !selectedDevice.value) {
      const savedSerial = localStorage.getItem('last_device_serial');
      const savedDevice = savedSerial ? devices.value.find(d => d.serial === savedSerial) : null;
      selectDevice(savedDevice || devices.value[0]);
    }
    if (!silent) showToast(t('device.deviceCount', { count: String(devices.value.length) }));
  } catch { if (!silent) showToast(t("device.scanFailed"), "error"); }
  finally { scanLoading.value = false; }
}
function onConnectIpFocus() {
  if (connectIpHistory.value.length > 0 && connectIpInputRef.value) {
    const r = connectIpInputRef.value.getBoundingClientRect();
    connectIpDropdownPos.value = { top: r.bottom + 4, left: r.left, width: r.width };
    showConnectIpHistory.value = true;
  }
}
function selectConnectIpHistory(v: string) { connectAddress.value = v; showConnectIpHistory.value = false; }
async function loadConnectIpHistory() {
  const entries = await getInputHistory('connect_ip');
  connectIpHistory.value = entries.map(e => e.value);
}
function selectDevice(device: DeviceItem) {
  selectedDevice.value = device;
  localStorage.setItem('last_device_serial', device.serial);
  deviceProps.value = null;

  loadDeviceProperties();
  refreshPackageList();
  if (activeTab.value === 'other') loadFileList();
}
async function loadDeviceProperties() {
  if (!selectedDevice.value) return;
  try { deviceProps.value = await getProperties(selectedDevice.value.serial); }
  catch { deviceProps.value = null; }
}
async function connectToDevice() {
  if (!connectAddress.value.trim()) {
    showToast(t("device.inputIp"), "error");
    return;
  }
  connecting.value = true;
  try {
    const addr = connectAddress.value.trim();
    const r = await connectDevice(addr);
    await addInputHistory('connect_ip', addr);
    connectAddress.value = "";
    await scanDevices();
    showCmdExec(t("device.connectingDevice"), `adb connect ${addr}`);
    appendCmdExec(r);
    finishCmdExec(t("device.connected"));
    showToast(t("device.connected"));
  } catch (e: any) { showToast(`${t("device.connectFail")}: ${e}`, "error"); }
  finally { connecting.value = false; }
}
async function disconnectDeviceHandler(serial: string) {
  try {
    await disconnectDevice(serial);
    devices.value = devices.value.filter(d => d.serial !== serial);
    if (selectedDevice.value?.serial === serial) {
      selectedDevice.value = devices.value[0] || null;
      apps.value = [];
      localStorage.removeItem('last_device_serial');
    }
    showToast(t("device.disconnected"));
  } catch { showToast(t("device.disconnectFailed"), "error"); }
}
async function restartAdbServer() {
  showCmdExec(t("device.restartAdbService"), "adb kill-server && adb start-server");
  try {
    appendCmdExec(t("device.stoppingAdb"));
    await killServer();
    appendCmdExec(t("device.adbStopped"));
    appendCmdExec(t("device.startingAdb"));
    await startServer();
    appendCmdExec(t("device.adbStarted"));
    await scanDevices();
    finishCmdExec(t("device.adbRestarted"));
    showToast(t("device.adbRestarted"));
  } catch (e: any) { finishCmdExec(t('device.restartFailedWith', { e: String(e) })); showToast(t("device.adbRestartFailed"), "error"); }
}
function clearDeviceState() {
  apps.value = [];
  deviceProps.value = null;
  selectedDevice.value = null;
  devices.value = [];
}
async function rebootDevice() {
  if (!selectedDevice.value) return;
  showCmdExec(t("device.rebootDevice"), "adb reboot");
  try {
    appendCmdExec(t("device.sendingRebootCmd"));
    await reboot(selectedDevice.value.serial);
    finishCmdExec(t("device.restarting"));
    showToast(t("device.rebootSent"));
    clearDeviceState();
  } catch { finishCmdExec(t("device.rebootFailed")); showToast(t("device.rebootFailed"), "error"); }
}
async function rebootToRecovery() {
  if (!selectedDevice.value) return;
  showCmdExec(t("device.rebootToRecovery"), "adb reboot recovery");
  try {
    appendCmdExec(t("device.sendingRebootCmd"));
    await rebootRecovery(selectedDevice.value.serial);
    finishCmdExec(t("device.rebootingToRecovery"));
    showToast(t("device.rebootingToRecovery"));
    clearDeviceState();
  } catch { finishCmdExec(t("device.operationFailed")); showToast(t("device.operationFailed"), "error"); }
}
async function rebootToBootloader() {
  if (!selectedDevice.value) return;
  showCmdExec(t("device.rebootToBootloader"), "adb reboot bootloader");
  try {
    appendCmdExec(t("device.sendingRebootCmd"));
    await rebootBootloader(selectedDevice.value.serial);
    finishCmdExec(t("device.rebootingToBootloader"));
    showToast(t("device.rebootingToBootloader"));
    clearDeviceState();
  } catch { finishCmdExec(t("device.operationFailed")); showToast(t("device.operationFailed"), "error"); }
}
async function rootDevice() {
  if (!selectedDevice.value) return;
  showCmdExec(t("device.rootDevice"), "adb root");
  try {
    appendCmdExec(t("device.executingAdbRoot"));
    const r = await adbRoot(selectedDevice.value.serial);
    appendCmdExec(r);
    finishCmdExec(t("device.rootDone"));
    showToast(t("device.rootDone"));
  } catch (e: any) { finishCmdExec(t('device.rootFailedWith', { e: String(e) })); showToast(t('device.rootFailedWith', { e: String(e) }), "error"); }
}
async function remountDevice() {
  if (!selectedDevice.value) return;
  showCmdExec(t("device.remountDevice"), "adb remount");
  try {
    appendCmdExec(t("device.executingRemount"));
    const r = await adbRemount(selectedDevice.value.serial);
    appendCmdExec(r);
    finishCmdExec(t("device.remountDone"));
    showToast(t("device.remountDone"));
  } catch (e: any) { finishCmdExec(t('device.remountFailedWith', { e: String(e) })); showToast(t('device.remountFailedWith', { e: String(e) }), "error"); }
}
async function sendKey(keycode: string) {
  if (!selectedDevice.value) return;
  try { await inputKeyevent(selectedDevice.value.serial, keycode); } catch {}
}
async function sendText() {
  if (!selectedDevice.value || !inputTextValue.value.trim()) return;
  const text = inputTextValue.value;
  inputTextValue.value = "";
  showCmdExec(t("device.sendTextAction"), `adb shell input text ${text}`);
  try {
    await adbInputText(selectedDevice.value.serial, text);
    await addInputHistory('input_text', text);
    textHistory.value = [text, ...textHistory.value.filter(h => h !== text)].slice(0, 15);
    appendCmdExec(t('device.textSentWith', { text }));
    finishCmdExec(t("device.textSent"));
    showToast(t("device.textSent"));
  } catch { finishCmdExec(t("device.sendFailed")); showToast(t("device.sendFailed"), "error"); }
}

// ── App Management ──
async function refreshPackageList() {
  if (!selectedDevice.value) return;
  pkgLoading.value = true;
  try {
    const raw = await listPackages(selectedDevice.value.serial, showThirdParty.value);
    const oldVersionMap = new Map(apps.value.map(a => [a.package_name, { vn: a.version_name, vc: a.version_code }]));
    apps.value = raw.map((pkg: string) => {
      const old = oldVersionMap.get(pkg);
      return { package_name: pkg, version_name: old?.vn, version_code: old?.vc };
    });
    appPage.value = 1;
    loadedVersions.value = new Set();
    showToast(t('device.loadedApps', { count: String(apps.value.length) }));
    // Auto-load version info for first page
    nextTick(() => loadVisibleAppVersions());
  } catch { showToast(t("device.loadAppsFailed"), "error"); }
  finally { pkgLoading.value = false; }
}
async function loadVisibleAppVersions() {
  if (!selectedDevice.value) return;
  const currentGen = ++versionGen;
  const pageApps = currentPageApps.value.filter(a => !a.version_name && !loadedVersions.value.has(a.package_name));
  for (const app of pageApps) loadedVersions.value = new Set(loadedVersions.value).add(app.package_name);
  const updates = new Map<string, { vn?: string; vc?: string }>();
  for (let i = 0; i < pageApps.length; i += 4) {
    if (currentGen !== versionGen) return;
    await Promise.all(pageApps.slice(i, i + 4).map(async app => {
      if (currentGen !== versionGen) return;
      try {
        const info = await getAppInfo(selectedDevice.value!.serial, app.package_name);
        if (currentGen !== versionGen) return;
        const vn = info.match(/versionName=([^\s]+)/)?.[1];
        const vc = info.match(/versionCode=(\d+)/)?.[1];
        if (vn || vc) {
          updates.set(app.package_name, { vn, vc });
        }
      } catch {}
    }));
  }
  if (currentGen !== versionGen || updates.size === 0) return;
  apps.value = apps.value.map(a => {
    const u = updates.get(a.package_name);
    return u ? { ...a, version_name: u.vn, version_code: u.vc } : a;
  });
}
async function getCurrentForegroundApp() {
  if (!selectedDevice.value) return;
  loadingForeground.value = true;
  try {
    const raw = await shell(selectedDevice.value.serial, "dumpsys window");
    const lines = raw.split("\n").filter(l => l.includes("mCurrentFocus") || l.includes("mFocusedApp"));
    const raw2 = lines.length > 0 ? lines.join("\n") : raw;
    const m = raw2.match(/([\w.]+\/[\w.]+)/);
    const result = m ? m[1] : t("device.noForegroundApp");
    resultDialog.value = { show: true, title: t("device.foregroundApp"), content: result };
  } catch { resultDialog.value = { show: true, title: t("device.foregroundApp"), content: t("device.getFailed") }; }
  finally { loadingForeground.value = false; }
}
const appDetailDialog = ref({ show: false, title: "", pkg: "", entries: [] as { key: string; value: string }[] });
async function showAppDetail(pkg: string) {
  if (!selectedDevice.value) return;
  try {
    const info = await getAppInfo(selectedDevice.value.serial, pkg);
    const sizeRaw = await shell(selectedDevice.value.serial, `dumpsys diskstats ${pkg}`).catch(() => "");
    const entries: { key: string; value: string }[] = [];
    const patterns: [RegExp, string][] = [
      [/versionName=([^\s\n]+)/, t("device.currentVersion")],
      [/versionCode=(\d+)/, t("device.currentVersionCode")],
      [/codePath=([^\s\n]+)/, t("device.installPath")],
      [/nativeLibraryDir=([^\s\n]+)/, t("device.nativeLibDir")],
      [/targetSdkVersion=(\d+)/, t("device.targetSdk")],
      [/minSdkVersion=(\d+)/, t("device.minSdk")],
    ];
    for (const [reg, label] of patterns) {
      const m = info.match(reg);
      if (m) entries.push({ key: label, value: m[1] });
    }
    const versionMatches = [...info.matchAll(/versionName=([^\s\n]+)/g)];
    const codeMatches = [...info.matchAll(/versionCode=(\d+)/g)];
    if (versionMatches.length > 1) {
      const history: string[] = [];
      for (let i = 0; i < versionMatches.length; i++) {
        const vn = versionMatches[i][1];
        const vc = codeMatches[i]?.[1] || "?";
        history.push(`${vn} (${vc})`);
      }
      entries.push({ key: t("device.versionHistory"), value: history.join(" → ") });
    }
    if (sizeRaw) {
      const sizeMatch = sizeRaw.match(/(\d[\d,.]+)\s*(KB|MB|GB|bytes?)/i);
      if (sizeMatch) entries.push({ key: t("device.appSize"), value: sizeMatch[1] + " " + sizeMatch[2] });
      const cacheMatch = sizeRaw.match(/Cache\s*size:\s*(\d[\d,.]+)\s*(KB|MB|GB|bytes?)/i);
      if (cacheMatch) entries.push({ key: t("device.cacheSize"), value: cacheMatch[1] + " " + cacheMatch[2] });
      const dataMatch = sizeRaw.match(/Data\s*size:\s*(\d[\d,.]+)\s*(KB|MB|GB|bytes?)/i);
      if (dataMatch) entries.push({ key: t("device.dataSize"), value: dataMatch[1] + " " + dataMatch[2] });
    }
    if (entries.length === 0) entries.push({ key: t("device.hint"), value: t("device.parseFail") });
    appDetailDialog.value = { show: true, title: pkg, pkg, entries };
  } catch { showToast(t("device.getDetailFailed"), "error"); }
}

async function startApp(pkg: string) {
  if (!selectedDevice.value) return;
  showCmdExec(t("device.startAppAction"), `adb shell monkey -p ${sanitizeShellArg(pkg)} 1`);
  try {
    appendCmdExec(t('device.startingApp', { pkg }));
    await adbStartApp(selectedDevice.value.serial, pkg);
    appendCmdExec(t('device.startedApp', { pkg }));
    finishCmdExec(t("device.appStarted"));
    showToast(t('device.startedApp', { pkg }));
  } catch {
    appendCmdExec(t("device.monkeyFailedFallback"));
    try {
      const mainAct = await shell(selectedDevice.value.serial, 
        `cmd package resolve-activity --brief ${sanitizeShellArg(pkg)} | tail -1`);
      if (mainAct && mainAct.includes("/")) {
        await shell(selectedDevice.value.serial, `am start -n ${sanitizeShellArg(mainAct.trim())}`);
        appendCmdExec(t('device.startedApp', { pkg }));
        finishCmdExec(t("device.appStarted"));
        showToast(t('device.startedApp', { pkg }));
        return;
      }
    } catch {}
    finishCmdExec(t("device.startFailed")); showToast(t("device.startFailed"), "error");
  }
}
async function stopApp(pkg: string) {
  if (!selectedDevice.value) return;
  showCmdExec(t("device.stopAppAction"), `adb shell am force-stop ${sanitizeShellArg(pkg)}`);
  try {
    appendCmdExec(t('device.stoppingApp', { pkg }));
    await adbStopApp(selectedDevice.value.serial, pkg);
    appendCmdExec(t('device.stoppedApp', { pkg }));
    finishCmdExec(t("device.appStopped"));
    showToast(t('device.stoppedApp', { pkg }));
  } catch { finishCmdExec(t("device.stopFailed")); showToast(t("device.stopFailed"), "error"); }
}
async function clearApp(pkg: string) {
  if (!selectedDevice.value) return;
  showCmdExec(t("device.clearDataAction"), `adb shell pm clear ${sanitizeShellArg(pkg)}`);
  try {
    appendCmdExec(t('device.clearingData', { pkg }));
    await clearAppData(selectedDevice.value.serial, pkg);
    appendCmdExec(t('device.clearedData', { pkg }));
    finishCmdExec(t("device.dataCleared"));
    showToast(t('device.clearedData', { pkg }));
  } catch { finishCmdExec(t("device.clearDataFailed")); showToast(t("device.clearDataFailed"), "error"); }
}
async function uninstallPkg(pkg: string) {
  if (!selectedDevice.value) return;
  showCmdExec(t("device.uninstallAction"), `adb uninstall ${pkg}`);
  try {
    appendCmdExec(t('device.uninstallingApp', { pkg }));
    await uninstallApk(selectedDevice.value.serial, pkg);
    apps.value = apps.value.filter(a => a.package_name !== pkg);
    appendCmdExec(t('device.uninstalledApp', { pkg }));
    finishCmdExec(t("device.appUninstalled"));
    showToast(t('device.uninstalledApp', { pkg }));
  } catch { finishCmdExec(t("device.uninstallFailed")); showToast(t("device.uninstallFailed"), "error"); }
}
async function selectApkFile() {
  try {
    const { open } = await import("@tauri-apps/plugin-dialog");
    const selected = await open({ multiple: false, filters: [{ name: "APK", extensions: ["apk"] }] });
    if (selected) {
      await cleanApkTempPath(apkFilePath.value);
      apkFilePath.value = selected;
    }
  } catch {}
}
let apkDropPending = false;
async function handleApkDrop(e: DragEvent) {
  apkDragOver.value = false;
  if (apkDropPending) return;

  // Grab everything we need from dataTransfer IMMEDIATELY before it expires
  const uris = e.dataTransfer?.getData('text/uri-list') || '';
  const files = e.dataTransfer?.files;
  const file = files?.[0];

  // Try file:/// URI first (works when dragging from Windows Explorer)
  if (uris) {
    const line = uris.split('\n')[0].trim();
    if (line.startsWith('file:///')) {
      const path = decodeURIComponent(line.replace(/^file:\/\//, ''));
      if (path.endsWith('.apk')) {
        await cleanApkTempPath(apkFilePath.value);
        apkFilePath.value = path;
        return;
      }
    }
  }

  // Fall back to reading file data
  if (!file || !file.name.endsWith('.apk')) {
    showToast(t("device.apkDragHintFile"), "error");
    return;
  }

  // Read file data BEFORE setting pending (before any await)
  let buf: ArrayBuffer;
  try {
    buf = await file.arrayBuffer();
  } catch {
    showToast(t("device.apkDragHintBrowser"), "error");
    return;
  }

  apkDropPending = true;
  try {
    const { appDataDir } = await import('@tauri-apps/api/path');
    const { writeFile } = await import('@tauri-apps/plugin-fs');
    const baseDir = await appDataDir();
    const sep = baseDir.endsWith('\\') || baseDir.endsWith('/') ? '' : '/';
    const tmpPath = `${baseDir}${sep}drop_apk_${Date.now()}_${file.name.replace(/[^a-zA-Z0-9._-]/g, '_')}`;
    await writeFile(tmpPath, new Uint8Array(buf));
    await cleanApkTempPath(apkFilePath.value);
    apkFilePath.value = tmpPath;
    apkTempPaths.value.push(tmpPath);
  } catch (e: any) {
    showToast(`${t("device.apkDragHintBrowser")} (${String(e)})`, "error");
  } finally {
    apkDropPending = false;
  }
}
async function closeApkDialog() {
  apkDialogOpen.value = false;
  await cleanApkTempPath(apkFilePath.value);
  apkFilePath.value = "";
}
async function handleApkInstall() {
  if (!selectedDevice.value || !apkFilePath.value) return;
  apkInstalling.value = true;
  try {
    await installApk(selectedDevice.value.serial, apkFilePath.value, reinstallApk.value);
    showToast(t("device.apkInstallSuccess"));
    apkDialogOpen.value = false;
    await cleanApkTempPath(apkFilePath.value);
    apkFilePath.value = "";
  } catch (e: any) {
    showToast(t('device.installFailedWith', { e: String(e) }), "error");
  } finally {
    apkInstalling.value = false;
  }
}
async function fetchAppVersion(pkg: string) {
  if (!selectedDevice.value) return;
  setAppLoading(pkg, 'version', true);
  try {
    const info = await getAppInfo(selectedDevice.value.serial, pkg);
    const vn = info.match(/versionName=([^\s]+)/)?.[1];
    const vc = info.match(/versionCode=(\d+)/)?.[1];
    apps.value = apps.value.map(a => a.package_name === pkg ? { ...a, version_name: vn, version_code: vc } : a);
    showToast(t("device.versionDisplay", { vn: vn || "N/A", vc: vc || "?" }));
  } catch { showToast(t("device.getVersionFailed"), "error"); }
  finally { setAppLoading(pkg, 'version', false); }
}

async function copyPackageName(pkg: string) {
  const ok = await copyToClipboard(pkg);
  showToast(ok ? t("device.pkgCopied") : t("device.copyFailed"), ok ? "success" : "error");
}
async function copyVersionInfo(pkg: string) {
  const app = apps.value.find(a => a.package_name === pkg);
  if (!app?.version_name) { showToast(t("device.noVersion"), "error"); return; }
  const text = `${app.version_name}${app.version_code ? ` (${app.version_code})` : ''}`;
  const ok = await copyToClipboard(text);
  showToast(ok ? t("device.versionInfoCopied") : t("device.copyFailed"), ok ? "success" : "error");
}
async function downloadApk(pkg: string) {
  if (!selectedDevice.value) return;
  showCmdExec(t("device.downloadApkTitle"), `adb shell dumpsys package ${pkg} | grep path:`);
  try {
    appendCmdExec(t("device.queryingApkPath"));
    const info = await getAppInfo(selectedDevice.value.serial, pkg);
    const pathMatch = info.match(/path:?\s*(\S+)/);
    if (!pathMatch) { finishCmdExec(t("device.apkPathNotFound")); showToast(t("device.apkPathNotFound"), "error"); return; }
    appendCmdExec(`${t("device.apkPathKey")}: ${pathMatch[1]}`);
    const { save } = await import("@tauri-apps/plugin-dialog");
    const dest = await save({ defaultPath: `${pkg}.apk`, filters: [{ name: "APK", extensions: ["apk"] }] });
    if (!dest) { closeCmdExec(); return; }
    appendCmdExec(t("device.pullingApk"));
    await pullFile(selectedDevice.value.serial, pathMatch[1], dest);
    appendCmdExec(t("device.savedTo", { path: dest }));
    finishCmdExec(t("device.apkDownloadDone"));
    showToast(t("device.apkDownloaded"));
  } catch { finishCmdExec(t("device.downloadFailed")); showToast(t("device.downloadFailed"), "error"); }
}

// ── App Path Query ──
const resultDialog = ref({ show: false, title: "", content: "" });
async function queryAppPath() {
  if (!selectedDevice.value) return;
  if (!queryPackageName.value.trim()) {
    showToast(t("device.inputPkg"), "error");
    return;
  }
  try {
    const result = await shell(selectedDevice.value.serial, `pm path ${sanitizeShellArg(queryPackageName.value.trim())}`);
    const match = result.match(/package:(.+)/);
    if (match) {
      await addInputHistory('app_search', queryPackageName.value.trim());
      appSearchHistory.value = [queryPackageName.value.trim(), ...appSearchHistory.value.filter(h => h !== queryPackageName.value.trim())].slice(0, 15);
      resultDialog.value = { show: true, title: t("device.apkPathTitle", { pkg: queryPackageName.value.trim() }), content: match[1].trim() };
    } else {
      showToast(t("device.appNotFound"), "error");
    }
  } catch { showToast(t("device.queryFailed"), "error"); }
}

// ── Information Query ──
async function queryInfo(type: string) {
  if (!selectedDevice.value) return;
  infoLoading.value = type;
  try {
    const serial = selectedDevice.value.serial;
    let title = "";
    let entries: { key: string; value: string }[] = [];
    if (type === "basic") {
      title = t("device.basicDeviceInfo");
      const props = await getProperties(serial);
      entries = Object.entries(props).map(([k, v]) => ({ key: k, value: v || "N/A" }));
    } else if (type === "mac") {
      title = t("device.macInfoTitle");
      try { await adbRoot(serial); } catch {}
      const [wlanMac, ethMac] = await Promise.all([
        shell(serial, "cat /sys/class/net/wlan0/address 2>/dev/null || ip link show wlan0 2>/dev/null | grep link/ether | awk '{print $2}'").catch(() => ""),
        shell(serial, "cat /sys/class/net/eth0/address 2>/dev/null || ip link show eth0 2>/dev/null | grep link/ether | awk '{print $2}'").catch(() => ""),
      ]);
      const wlan = wlanMac.trim();
      const eth = ethMac.trim();
      if (wlan) entries.push({ key: "WiFi MAC", value: wlan });
      if (eth) entries.push({ key: t("device.physicalMac"), value: eth });
      if (entries.length === 0) entries.push({ key: t("device.macAddress"), value: t("device.macInfoNotFound") });
    } else if (type === "whaleos") {
      title = t("device.firmwareInfoTitle");
      const tvKeys = ["ro.product.model", "ro.product.tv.rcu", "ro.product.tv.deviceType", "ro.vendor.product.version",
        "ro.vendor.zeasn.firmwareID", "persist.sys.cur_country", "persist.sys.cur_language", "ro.boot.pid", "ro.boot.mac"];
      const results = await Promise.all(tvKeys.map(k => shell(serial, `getprop ${k}`).catch(() => "")));
      entries = tvKeys.map((key, i) => ({ key, value: results[i].trim() || "" })).filter(e => e.value !== "");
    } else if (type === "aosp") {
      title = t("device.aospFirmwareInfo");
      const aospKeys = ["ro.product.model", "ro.build.display.id", "ro.build.description", "ro.vendor.product.version",
        "ro.build.fingerprint", "ro.build.version.sdk", "ro.build.version.security_patch", "ro.product.cpu.abi"];
      const results = await Promise.all(aospKeys.map(k => shell(serial, `getprop ${k}`).catch(() => t("device.empty"))));
      entries = aospKeys.map((key, i) => ({ key, value: results[i].trim() || t("device.empty") }));
    } else if (type === "keys") {
      title = t("device.keyCheckResult");
      const checks = [
        { name: "HDCP 1.4", cmd: "tee_provision -qt 0x31" },
        { name: "HDCP 2.2", cmd: "tee_provision -qt 0x32" },
        { name: "MGKID", cmd: "tee_provision -qt 0xa2" },
        { name: "Widevine", cmd: "drminfo -d" },
        { name: "Dolby", cmd: "dolby_fw_dolbyms12 /smart/etc/ms12/libdolbyms12.so /data/test.so" },
      ];
      const checkResults = await Promise.all(checks.map(c =>
        shell(serial, c.cmd).then(r => {
          const success = !r.toLowerCase().includes("not provisioned") && !r.toLowerCase().includes("error");
          return { key: c.name, value: `${success ? t("device.keyPassed") : t("device.keyFailed")}\n> ${c.cmd}`, raw: r };
        }).catch((e: any) => ({ key: c.name, value: t("device.keyExecError"), raw: `${e}` }))
      ));
      entries = checkResults;
    } else if (type === "storage") {
      title = t("device.storageInfoTitle");
      const toGBMB = (kb: number): string => {
        const gb = (kb / (1024 * 1024)).toFixed(2);
        const mb = (kb / 1024).toFixed(2);
        return `${gb}G(${mb}MB)`;
      };
      // 运行内存: adb shell free -h
      const freeResult = await shell(serial, "free -h").catch(() => "");
      if (freeResult) {
        const lines = freeResult.trim().split("\n");
        if (lines.length > 1) {
          const memLine = lines[1].split(/\s+/);
          if (memLine.length > 1) {
            entries.push({ key: t("device.ram"), value: memLine[1] });
          }
        }
      }
      // 物理存储容量: adb shell cat /sys/block/mmcblk0/size
      const sizeResult = await shell(serial, "cat /sys/block/mmcblk0/size").catch(() => "");
      if (sizeResult && sizeResult.trim()) {
        const sectors = parseInt(sizeResult.trim());
        if (!isNaN(sectors)) {
          const bytesSize = sectors * 512;
          const gbSize = (bytesSize / (1024 * 1024 * 1024)).toFixed(2);
          const mbSize = (bytesSize / (1024 * 1024)).toFixed(2);
          entries.push({ key: t("device.physicalStorage"), value: `${gbSize}G(${mbSize}MB)` });
        }
      }
      // 可使用总存储空间 / 剩余存储空间: adb shell df /data
      const dfResult = await shell(serial, "df /data").catch(() => "");
      if (dfResult) {
        const lines = dfResult.trim().split("\n");
        if (lines.length > 1) {
          const parts = lines[1].split(/\s+/);
          if (parts.length >= 4) {
            const totalKb = parseFloat(parts[1]);
            const availKb = parseFloat(parts[3]);
            if (!isNaN(totalKb)) {
              entries.push({ key: t("device.totalStorage"), value: toGBMB(totalKb) });
            }
            if (!isNaN(availKb)) {
              entries.push({ key: t("device.availableStorage"), value: toGBMB(availKb) });
            }
          }
        }
      }
      // Available: adb shell stat -f /data → Available 值 / 256 = MB
      const statResult = await shell(serial, "stat -f /data").catch(() => "");
      if (statResult) {
        const match = statResult.match(/Available:\s*(\d+)/i);
        if (match) {
          const availBlocks = parseInt(match[1]);
          const availMB = (availBlocks / 256).toFixed(2);
          const availGB = (availBlocks / 256 / 1024).toFixed(2);
          entries.push({ key: "Available", value: `${availGB}G(${availMB}MB)` });
        }
      }
    }
    infoDialog.value = { show: true, title, entries };
  } catch { showToast(t("device.queryFailed"), "error"); }
  infoLoading.value = "";
}

// ── Log Collection ──
async function toggleLogcat() {
  if (!selectedDevice.value) return;
  if (logcatRunning.value) {
    await stopLogcatCapture();
  } else {
    const ok = await prepareLogCapture();
    if (!ok) return;
    try { await logcatClear(selectedDevice.value.serial); } catch {}
    logcatBuffer.value = [];
    logcatRunning.value = true;
    logcatElapsed.value = 0;
    logcatSerial = selectedDevice.value.serial;
    const session = { id: `logcat_${Date.now()}`, type: 'logcat' as const, deviceSerial: selectedDevice.value.serial, status: 'running' as const, startedAt: new Date().toISOString() };
    await saveLogSession(session);
    scheduleLogcatTimer();
    showCmdExec(t("device.realtimeLogsTitle"), "adb logcat");
    appendCmdExec(t("device.logCollectStarted"));
    finishCmdExec(t("device.logCollectStarted"));
    showToast(t("device.logCollectStarted"));
  }
}
function scheduleLogcatTimer() {
  if (!logcatRunning.value) return;
  if (!selectedDevice.value) { stopLogcatCapture(); return; }
  logcatElapsed.value += 1;
  logcatTimeoutId = setTimeout(scheduleLogcatTimer, 1000);
}
async function stopLogcatCapture() {
  if (logcatTimeoutId) { clearTimeout(logcatTimeoutId); logcatTimeoutId = null; }
  logcatRunning.value = false;
  const serial = logcatSerial;
  logcatSerial = "";
  if (serial) {
    try {
      const raw = await logcat(serial, "all", 0);
      const { save } = await import("@tauri-apps/plugin-dialog");
      const dest = await save({ defaultPath: `logcat_${Date.now()}.txt`, filters: [{ name: "Text", extensions: ["txt"] }] });
      if (dest) {
        const { writeTextFile } = await import("@tauri-apps/plugin-fs");
        await writeTextFile(dest, raw);
        showToast(t("device.logSaved"));
      }
    } catch {}
  }
  logcatBuffer.value = [];
  try {
    const sessions = await getRunningLogSessions();
    for (const s of sessions) { if (s.type === 'logcat') await removeLogSession(s.id); }
  } catch {}
  if (!serial) showToast(t("device.deviceDisconnected"), "error");
  else showToast(t("device.logCollectStopped"));
}

async function toggleDiagnostic() {
  if (!selectedDevice.value) return;
  if (diagRunning.value) {
    await stopDiagnosticCapture();
  } else {
    const ok = await prepareLogCapture();
    if (!ok) return;
    try { await logcatClear(selectedDevice.value.serial); } catch {}
    diagBuffer.value = [];
    diagRunning.value = true;
    diagElapsed.value = 0;
    diagSerial = selectedDevice.value.serial;
    const session = { id: `diag_${Date.now()}`, type: 'diagnostic' as const, deviceSerial: selectedDevice.value.serial, status: 'running' as const, startedAt: new Date().toISOString() };
    await saveLogSession(session);
    scheduleDiagTimer();
    showCmdExec(t("device.diagnostics"));
    appendCmdExec(t("device.diagStarted"));
    finishCmdExec(t("device.diagCollectStarted"));
    showToast(t("device.diagCollectStarted"));
  }
}
function scheduleDiagTimer() {
  if (!diagRunning.value) return;
  if (!selectedDevice.value) { stopDiagnosticCapture(); return; }
  diagElapsed.value += 1;
  if (diagRunning.value) {
    diagTimeoutId = setTimeout(scheduleDiagTimer, 1000);
  }
}
async function stopDiagnosticCapture() {
  if (diagTimeoutId) { clearTimeout(diagTimeoutId); diagTimeoutId = null; }
  diagRunning.value = false;
  const serial = diagSerial;
  diagSerial = "";
  if (!serial) { showToast(t("device.deviceDisconnected"), "error"); return; }
  await yieldToUI();
  try {
    showCmdExec(t("device.collectingDiag"));
    appendCmdExec(t("device.collectingLogs"));

    const files: { filename: string; content: string }[] = [];
    function addFile(filename: string, _label: string, content: string) {
      files.push({ filename, content });
    }

    // Logcat dump
    appendCmdExec(`  ${t("device.collectingLogcat")}`);
    try {
      const logcatContent = await logcat(serial, "all", 0);
      addFile("logcat.txt", "Logcat (all)", logcatContent);
      appendCmdExec("  ✓ logcat.txt");
    } catch { addFile("logcat.txt", "Logcat (all)", `(${t("device.collectFailed")})`); appendCmdExec("  ✗ logcat.txt"); }
    await yieldToUI();

    // dmesg
    appendCmdExec(`  ${t("device.collectingDmesg")}`);
    try {
      const dmesgContent = await dmesg(serial);
      addFile("dmesg.txt", "dmesg", dmesgContent);
      appendCmdExec("  ✓ dmesg.txt");
    } catch { addFile("dmesg.txt", "dmesg", `(${t("device.collectFailed")})`); appendCmdExec("  ✗ dmesg.txt"); }
    await yieldToUI();

    // System info - each into its own file
    const infoFiles: [string, string, string][] = [
      ["getprop.txt", "getprop", "getprop"],
      ["uptime.txt", "uptime", "uptime"],
      ["free.txt", "free -m", "free"],
      ["df.txt", "df -h", "df"],
      ["battery.txt", "dumpsys battery", "dumpsys battery"],
      ["power.txt", "dumpsys power", "dumpsys power"],
      ["ps.txt", "ps", "ps"],
    ];
    for (const [filename, cmd, label] of infoFiles) {
      appendCmdExec(`  ${t("device.collectingLabel", { label })}`);
      try {
        const result = await shell(serial, cmd);
        addFile(filename, label, result);
        appendCmdExec(`  ✓ ${filename}`);
      } catch {
        addFile(filename, label, `(${t("device.cmdExecFailed")})`);
        appendCmdExec(`  ✗ ${filename}`);
      }
      await yieldToUI();
    }

    // Dumpsys services (matching web-adb-tool)
    const dumpsysServices = ["package", "SurfaceFlinger", "activity", "input", "window", "settings"];
    for (const service of dumpsysServices) {
      appendCmdExec(`  ${t("device.collectingDumpsys", { service })}`);
      try {
        const result = await shell(serial, `dumpsys ${service}`);
        addFile(`dumpsys_${service}.txt`, `dumpsys ${service}`, result);
        appendCmdExec(`  ✓ dumpsys_${service}.txt`);
      } catch {
        addFile(`dumpsys_${service}.txt`, `dumpsys ${service}`, `(${t("device.collectFailed")})`);
        appendCmdExec(`  ✗ dumpsys_${service}.txt`);
      }
      await yieldToUI();
    }

    // ANR traces
    appendCmdExec(`  ${t("device.collectingAnr")}`);
    try {
      const anrListing = await listDirectory(serial, "/data/anr");
      const anrFiles = anrListing.split("\n").map(l => l.trim().split(/\s+/).pop()).filter(f => f && f !== "." && f !== "..");
      for (const anrFile of anrFiles) {
        try {
          const anrContent = await shell(serial, `cat "/data/anr/${anrFile}"`);
          addFile(`anr/${anrFile}`, `ANR: ${anrFile}`, anrContent);
          appendCmdExec(`  ✓ anr/${anrFile}`);
        } catch {
          addFile(`anr/${anrFile}`, `ANR: ${anrFile}`, `(${t("device.collectFailed")})`);
          appendCmdExec(`  ✗ anr/${anrFile}`);
        }
      }
      if (anrFiles.length === 0) appendCmdExec(`  ${t("device.anrCollectFailed")}`);
      else appendCmdExec(`  ${t("device.anrCollected")}`);
    } catch {
      appendCmdExec(`  ✗ ${t("device.anrCollectFailed")}`);
    }
    await yieldToUI();

    // Prompt user for save location
    const { save } = await import("@tauri-apps/plugin-dialog");
    const dest = await save({ defaultPath: `diagnostic_${Date.now()}.zip`, filters: [{ name: "ZIP Archive", extensions: ["zip"] }] });
    if (dest) {
      appendCmdExec(t("device.generatingZip"));
      await createZip(files, dest);
      appendCmdExec(t("device.diagSaved", { path: dest }));
      finishCmdExec(t("device.diagGenerated"));
      showToast(t("device.diagLogSaved"));
    } else {
      closeCmdExec();
    }
  } catch (e: any) {
    finishCmdExec(`${t("device.saveFail")}: ${e}`);
    showToast(t("device.saveFail"), "error");
  }
  diagBuffer.value = [];
  try {
    const sessions = await getRunningLogSessions();
    for (const s of sessions) { if (s.type === 'diagnostic') await removeLogSession(s.id); }
  } catch {}
}

async function toggleBootLogcat() {
  if (bootLogcatRunning.value) {
    await stopBootLogcatCapture();
  } else {
    bootLogcatBuffer.value = [];
    bootLogcatRunning.value = true;
    bootLogcatElapsed.value = 0;
    bootLogcatStartTime.value = Date.now();
    bootLogcatSerial.value = null;
    if (selectedDevice.value) {
      bootLogcatPhase.value = 'wait_disconnect';
      bootLogcatSerial.value = selectedDevice.value.serial;
      const session = { id: `boot_${Date.now()}`, type: 'boot_logcat' as const, deviceSerial: selectedDevice.value.serial, status: 'running' as const, startedAt: new Date().toISOString() };
      await saveLogSession(session);
      try {
        await logcatClear(selectedDevice.value.serial);
        await reboot(selectedDevice.value.serial);
        showToast(t("device.restarting"));
      } catch { showToast(t("device.rebootFailed"), "error"); }
    } else {
      bootLogcatPhase.value = 'wait_for_device';
      showToast(t("device.waitingForDevice"));
    }
    scheduleBootPoll();
  }
}
async function scheduleBootPoll() {
  if (!bootLogcatRunning.value) return;
  const serial = bootLogcatSerial.value;
  bootLogcatElapsed.value = Math.floor((Date.now() - bootLogcatStartTime.value) / 1000);
  if (bootLogcatPhase.value === 'wait_disconnect' || bootLogcatPhase.value === 'wait_reconnect') {
    if (bootLogcatElapsed.value > 180) {
      showToast(t("device.reconnectTimeout"), "error");
      bootLogcatRunning.value = false;
      return;
    }
  }
  try {
    const adbDevices = await listDevices();
    if (bootLogcatPhase.value === 'wait_for_device') {
      const found = adbDevices.find(d => d.status === "device");
      if (found) {
        bootLogcatSerial.value = found.serial;
        try { await logcatClear(found.serial); } catch {}
        try { await adbRoot(found.serial); } catch {}
        try { await logcatBufferResize(found.serial, 256); } catch {}
        bootLogcatPhase.value = 'capturing';
        showToast(t("device.deviceReconnectedLogsGot"));
      }
      bootLogcatTimeoutId = setTimeout(scheduleBootPoll, 500);
    } else if (!serial) {
      bootLogcatRunning.value = false;
    } else {
      const isOnline = adbDevices.some(d => d.serial === serial && d.status === "device");
      if (bootLogcatPhase.value === 'wait_disconnect') {
        if (!isOnline) bootLogcatPhase.value = 'wait_reconnect';
        bootLogcatTimeoutId = setTimeout(scheduleBootPoll, 2000);
      } else if (bootLogcatPhase.value === 'wait_reconnect') {
        if (isOnline) {
          bootLogcatPhase.value = 'capturing';
          try { await adbRoot(serial); } catch {}
          try { await logcatBufferResize(serial, 256); } catch {}
          showToast(t("device.deviceReconnectedLogsGot"));
        } else if (serial && serial.includes(':') && bootLogcatElapsed.value > 3) {
          try { await connectDevice(serial); } catch {}
        }
        bootLogcatTimeoutId = setTimeout(scheduleBootPoll, 500);
      } else {
        bootLogcatTimeoutId = setTimeout(scheduleBootPoll, 1000);
      }
    }
  } catch {
    if (bootLogcatRunning.value) {
      bootLogcatTimeoutId = setTimeout(scheduleBootPoll, 2000);
    }
  }
}
async function stopBootLogcatCapture() {
  if (bootLogcatTimeoutId) { clearTimeout(bootLogcatTimeoutId); bootLogcatTimeoutId = null; }
  bootLogcatRunning.value = false;
  const serial = bootLogcatSerial.value;
  bootLogcatSerial.value = null;
  if (serial) {
    try {
      const raw = await logcat(serial, "all", 0);
      const { save } = await import("@tauri-apps/plugin-dialog");
      const dest = await save({ defaultPath: `boot_logcat_${Date.now()}.txt`, filters: [{ name: "Text", extensions: ["txt"] }] });
      if (dest) {
        const { writeTextFile } = await import("@tauri-apps/plugin-fs");
        await writeTextFile(dest, raw);
      }
    } catch {}
  }
  bootLogcatBuffer.value = [];
  try {
    const sessions = await getRunningLogSessions();
    for (const s of sessions) { if (s.type === 'boot_logcat') await removeLogSession(s.id); }
  } catch {}
  showToast(t("device.bootLogStopped"));
}

async function clearLogcatLogs() {
  if (!selectedDevice.value) return;
    showCmdExec(t("device.clearLogsTitle"), "adb logcat -c");
  try {
    await logcatClear(selectedDevice.value.serial);
    appendCmdExec(t("device.logsCleared"));
    finishCmdExec(t("device.logsCleared"));
    showToast(t("device.logsCleared"));
  } catch { finishCmdExec(t("device.clearLogsFailed")); showToast(t("device.clearLogsFailed"), "error"); }
}

async function generateBugreport() {
  if (!selectedDevice.value) return;
  showCmdExec(t("device.genBugreport"), "adb bugreport");
  try {
    const { save } = await import("@tauri-apps/plugin-dialog");
    const dest = await save({ defaultPath: `bugreport_${Date.now()}.zip`, filters: [{ name: "Bugreport ZIP", extensions: ["zip"] }] });
    if (!dest) { closeCmdExec(); return; }
    appendCmdExec(t("device.generatingBugreport"));
    await bugreport(selectedDevice.value.serial, dest);
    appendCmdExec(t("device.bugreportSaved", { path: dest }));
    finishCmdExec(t("device.bugreportGenerated"));
    showToast(t("device.bugreportGenerated"));
  } catch (e: any) { finishCmdExec(t('device.bugreportFailedWith', { e: String(e) })); showToast(t('device.bugreportFailedWith', { e: String(e) }), "error"); }
}

// ── (removed) old file browser replaced by tree view above

// ── (removed) device config module removed

// ── Screen Mirror (scrcpy-server H.264 + WebCodecs, fallback to screencap) ──
async function toggleMirror() {
  if (isMirroring.value) { await stopMirror(); }
  else { await startMirror(); }
}
async function startMirror() {
  console.log("[mirror] startMirror called");
  if (!selectedDevice.value) { console.log("[mirror] no device selected, abort"); return; }
  isMirroring.value = true;
  mirrorFrameCount.value = 0;
  mirrorCtx = mirrorCanvas.value?.getContext("2d") || null;
  console.log("[mirror] mirrorCtx:", !!mirrorCtx, "canvas:", !!mirrorCanvas.value);

  let useScrcpy = false;
  let videoDecoder: VideoDecoder | null = null;

  try {
    const { listen } = await import("@tauri-apps/api/event");
    const { invoke } = await import("@tauri-apps/api/core");
    console.log("[mirror] tauri APIs imported");

    // Query device display size for accurate touch mapping
    try {
      const [dw, dh] = await invoke<[number, number]>("adb_get_display_size", { serial: selectedDevice.value.serial });
      deviceWidth.value = dw;
      deviceHeight.value = dh;
      console.log("[mirror] device display size:", dw, "x", dh);
    } catch (e) { console.warn("[mirror] failed to get display size:", e); }

    const listeners: (() => void)[] = [];

    listeners.push(await listen<string>("mirror:mode", (event) => {
      console.log("[mirror] mode event received:", event.payload);
      mirrorMode.value = event.payload as 'scrcpy' | 'legacy';
      useScrcpy = event.payload === "scrcpy";
      if (useScrcpy) {
        console.log("[mirror] creating VideoDecoder for scrcpy");
        videoDecoder = new VideoDecoder({
          output: (frame: VideoFrame) => {
            if (!mirrorCtx || !mirrorCanvas.value) { frame.close(); return; }
            mirrorCanvas.value.width = frame.displayWidth;
            mirrorCanvas.value.height = frame.displayHeight;
            mirrorWidth.value = frame.displayWidth;
            mirrorHeight.value = frame.displayHeight;
            mirrorCtx.drawImage(frame, 0, 0);
            frame.close();
            mirrorFrameCount.value++;
          },
          error: (e: any) => { console.error("[mirror] WebCodecs error:", e); gotKeyFrame = false; }
        });
      }
    }, listenTarget));

    const { Channel } = await import("@tauri-apps/api/core");
    let gotKeyFrame = false;
    let decoderConfigured = false;
    const serial = selectedDevice.value.serial;

    const onFrame = new Channel<ArrayBuffer>();
    onFrame.onmessage = (raw: ArrayBuffer) => {
      if (!isMirroring.value) return;
      if (!raw || raw.byteLength === 0) return;
      const bytes = new Uint8Array(raw);
      // Byte 0xFF marks decoder config (avcC), 0x00/0x01 marks frame key flag
      if (bytes[0] === 0xFF) {
        if (useScrcpy && videoDecoder && !decoderConfigured) {
          try {
            videoDecoder.configure({
              codec: "avc1.42E01E",
              description: bytes.subarray(1),
              codedWidth: 1280, codedHeight: 720,
            });
            decoderConfigured = true;
            console.log("[mirror] VideoDecoder configured successfully");
          } catch (e) { console.error("[mirror] Config failed:", e); }
        }
        return;
      }
      const isKey = bytes[0] === 1;
      const frameData = bytes.subarray(1);

      if (isKey) gotKeyFrame = true;
      if (!gotKeyFrame) return;

      if (useScrcpy && videoDecoder && decoderConfigured) {
        videoDecoder.decode(new EncodedVideoChunk({
          type: isKey ? "key" : "delta",
          timestamp: performance.now() * 1000,
          data: frameData,
        }));
      } else if (!useScrcpy) {
        const canvas = mirrorCanvas.value;
        if (!canvas || !mirrorCtx) return;
        const blob = new Blob([frameData], { type: "image/png" });
        const url = URL.createObjectURL(blob);
        const img = new window.Image();
        img.onload = () => {
          if (!canvas || !mirrorCtx) return;
          canvas.width = img.width;
          canvas.height = img.height;
          mirrorWidth.value = img.width;
          mirrorHeight.value = img.height;
          mirrorCtx.drawImage(img, 0, 0);
          mirrorFrameCount.value++;
          URL.revokeObjectURL(url);
        };
        img.onerror = () => URL.revokeObjectURL(url);
        img.src = url;
      }
    };

    listeners.push(await listen<string>("mirror:diagnostic", (event) => {
      console.log("[mirror] diagnostic:", event.payload);
      const msg = event.payload;
      if (msg.startsWith("scrcpy-server jar not found")) mirrorErrorMsg.value = t("device.mirrorDiagJarNotFound");
      else if (msg.startsWith("scrcpy-server push failed")) mirrorErrorMsg.value = t("device.mirrorDiagPushFailed", { detail: msg.split("scrcpy-server push failed: ")[1] || msg });
      else if (msg.startsWith("ADB forward failed")) mirrorErrorMsg.value = t("device.mirrorDiagForwardFailed", { detail: msg.split("ADB forward failed: ")[1] || msg });
      else if (msg.startsWith("ADB reverse failed")) mirrorErrorMsg.value = t("device.mirrorDiagForwardFailed", { detail: msg.split("ADB reverse failed: ")[1] || msg });
      else if (msg.startsWith("scrcpy-server start failed")) mirrorErrorMsg.value = t("device.mirrorDiagStartFailed", { detail: msg.split("scrcpy-server start failed: ")[1] || msg });
      else if (msg.startsWith("scrcpy: Server not ready after 30s") || msg.includes("Server not ready after 30s")) mirrorErrorMsg.value = t("device.mirrorDiagStreamFailed");
      else if (msg.startsWith("scrcpy: Codec config not received") || msg.includes("Codec config not received")) mirrorErrorMsg.value = t("device.mirrorDiagStreamFailed");
      else if (msg.startsWith("scrcpy: Stream ended") || msg.includes("Stream ended")) mirrorErrorMsg.value = t("device.mirrorDiagStreamFailed");
      else if (msg.startsWith("scrcpy: Failed to read codec meta") || msg.includes("Failed to read codec meta")) mirrorErrorMsg.value = t("device.mirrorDiagStreamFailed");
      else if (msg.startsWith("scrcpy:")) mirrorErrorMsg.value = t("device.mirrorDiagStreamFailed");
      else mirrorErrorMsg.value = msg;
    }, listenTarget));

    listeners.push(await listen<string>("mirror:error", async (event) => {
      console.log("[mirror] error event:", event.payload);
      mirrorErrorMsg.value = event.payload;
      showToast(event.payload, "error");
      await stopMirror();
    }, listenTarget));

    listeners.push(await listen("mirror:ready", () => {
      console.log("[mirror] ready event");
      if (useScrcpy) showToast(t("device.mirrorStarted"), "success");
    }, listenTarget));

    mirrorUnlisten = listeners;
    mirrorUnlisten.push(() => { if (videoDecoder) { console.log("[mirror] closing decoder"); videoDecoder.close(); } });
    console.log("[mirror] invoking adb_mirror_start");
    await invoke("adb_mirror_start", {
      serial: selectedDevice.value.serial,
      onFrame,
      maxSize: qualityMode.value === 'quality' ? 1080 : 960,
      videoBitRate: qualityMode.value === 'quality' ? 5_000_000 : 3_000_000,
      maxFps: qualityMode.value === 'quality' ? 24 : 15,
    });
    console.log("[mirror] invoke returned successfully");
  } catch (e) {
    console.error("[mirror] invoke failed:", e);
    showToast(t("device.mirrorStartFailed"), "error");
    await stopMirror();
  }
}
async function stopMirror() {
  console.log("[mirror] stopMirror called");
  const serial = selectedDevice.value?.serial;
  if (!serial) return;
  try {
    const { invoke } = await import("@tauri-apps/api/core");
    await invoke("adb_mirror_stop", { serial });
    console.log("[mirror] adb_mirror_stop called");
  } catch (e) { console.error("[mirror] stop error:", e); }
  for (const u of mirrorUnlisten) { u(); }
  mirrorUnlisten = [];
  mirrorCtx = null;
  isMirroring.value = false;
  mirrorFrameCount.value = 0;
  mirrorMode.value = 'idle';
  mirrorErrorMsg.value = '';
  console.log("[mirror] stopped");
}

async function takeScreenshot() {
  if (!selectedDevice.value) return;
  try {
    const { save } = await import("@tauri-apps/plugin-dialog");
    const dest = await save({ defaultPath: `screenshot_${Date.now()}.png`, filters: [{ name: "PNG Image", extensions: ["png"] }] });
    if (!dest) return;
    showCmdExec(t("device.screenshotAction"), "adb screencap -p");
    appendCmdExec(t("device.takingScreenshot"));
    const result = await screenshot(selectedDevice.value.serial, dest);
    appendCmdExec(result);
    finishCmdExec(t("device.screenshotSaved"));
    showToast(t("device.screenshotSaved"));
  } catch (e: any) { finishCmdExec(); showToast(t('device.screenshotFailedWith', { e: String(e) }), "error"); }
}
async function takeScreenshotFromMirror() {
  await takeScreenshot();
}
async function toggleRecording() {
  if (!selectedDevice.value) return;
  recordingLoading.value = true;
  if (isRecording.value) {
    try {
      showCmdExec(t("device.stopRecordingAction"), "adb shell pkill -SIGINT screenrecord");
      appendCmdExec(t("device.stoppingRecording"));
      // Send SIGINT first, then pkill -9 as fallback (matching web-adb-tool)
      await shell(selectedDevice.value.serial, "pkill -SIGINT screenrecord");
      await new Promise(r => setTimeout(r, 500));
      await shell(selectedDevice.value.serial, "pkill -9 screenrecord").catch(() => {});
      await new Promise(r => setTimeout(r, 1000));
      const { save } = await import("@tauri-apps/plugin-dialog");
      const dest = await save({ defaultPath: `recording_${Date.now()}.mp4`, filters: [{ name: "MP4 Video", extensions: ["mp4"] }] });
      if (dest) {
        appendCmdExec(t("device.pullingRecording"));
        await pullFile(selectedDevice.value.serial, recordingFilename.value, dest);
        appendCmdExec(t("device.cleaningDeviceFiles"));
        await shell(selectedDevice.value.serial, `rm ${sanitizeShellArg(recordingFilename.value)}`).catch(() => {});
        appendCmdExec(t("device.screenrecSaved") + ": " + dest);
        finishCmdExec(t("device.screenrecSaved"));
        showToast(t("device.screenrecSaved"));
      } else {
        closeCmdExec();
      }
    } catch (e: any) { finishCmdExec(`${t("device.screenrecFail")}: ${e}`); showToast(`${t("device.screenrecFail")}: ${e}`, "error"); }
    isRecording.value = false;
    recordingFilename.value = "";
  } else {
    try {
      const remotePath = `/sdcard/recording_${Date.now()}.mp4`;
      recordingFilename.value = remotePath;
      showCmdExec(t("device.startRecordingAction"), `screenrecord ${remotePath}`);
      appendCmdExec(t("device.startingRecording"));
      await startScreenrecord(selectedDevice.value.serial, remotePath, 1280, 720);
      isRecording.value = true;
      appendCmdExec(t("device.recordingStartedFull"));
      finishCmdExec(t("device.recordingStarted"));
      showToast(t("device.recordingStartedShort"));
    } catch { finishCmdExec(t("device.recordingStartFailed")); showToast(t("device.recordingStartFailed"), "error"); }
  }
  recordingLoading.value = false;
}

// ── Output Panel ──
// ── Lifecycle ──
onMounted(async () => {
  scanDevices(true);
  loadCustomCommands();
  loadTextHistory();
  loadRemotePathHistory();
  loadConnectIpHistory();
  // Auto-refresh devices every 5s (silent, no toast)
  autoRefreshId = setInterval(() => { if (!pkgLoading.value && !scanLoading.value && !connecting.value && !recordingLoading.value) scanDevices(true); }, 5000);
  nextTick(() => {
    recalcAppPageSize();
    let rafId: number;
    const ro = new ResizeObserver(() => { cancelAnimationFrame(rafId); rafId = requestAnimationFrame(recalcAppPageSize); });
    const panel = appListContainer.value?.closest('.glass-panel');
    if (panel) ro.observe(panel);
    window.addEventListener('resize', recalcAppPageSize);
    setTimeout(recalcAppPageSize, 500);
  });
  // Restore running log sessions
  try {
    const sessions = await getRunningLogSessions();
    for (const s of sessions) {
      if (s.type === 'logcat') { /* previously running - could auto-restore */ }
    }
  } catch {}

});

onUnmounted(() => {
  window.removeEventListener('resize', recalcAppPageSize);
  if ((window as any).__appListResizeObserver) (window as any).__appListResizeObserver.disconnect();
  // Don't stop mirror if standalone popout window is active
  if (!mirrorPopoutActive.value) {
    for (const u of mirrorUnlisten) { u(); }
    mirrorUnlisten = [];
    const serial = selectedDevice.value?.serial;
    if (serial) {
      import("@tauri-apps/api/core").then(m => m.invoke("adb_mirror_stop", { serial })).catch(() => {});
    }
  }
  if (logcatTimeoutId) clearTimeout(logcatTimeoutId);
  if (diagTimeoutId) clearTimeout(diagTimeoutId);
  if (bootLogcatTimeoutId) clearTimeout(bootLogcatTimeoutId);
  if (autoRefreshId) clearInterval(autoRefreshId);
  if (cmdExecTimeout) clearTimeout(cmdExecTimeout);
  // Clean up APK temp files
  for (const p of apkTempPaths.value) {
    import("@tauri-apps/plugin-fs").then(m => m.remove(p)).catch(() => {});
  }
  // Note: log sessions are saved to DB; user can see "running" sessions on next visit
});
</script>

<style scoped>
.text-caption { font-size: 15px !important; font-weight: 400 !important; }
.text-label-md { font-size: 16px !important; }
.glass-button { font-weight: 400 !important; }

/* Enhanced button borders with depth (inset shadow, not border, to preserve dynamic border-error states) */
.glass-panel button:not(.glass-button):not(.no-border) {
  box-shadow:
    inset 0 0 0 1px rgba(0, 0, 0, 0.09),
    inset 0 -1px 0 rgba(0, 0, 0, 0.15),
    inset 0 1px 0 rgba(255, 255, 255, 0.7),
    0 1px 2px rgba(0, 0, 0, 0.04);
}

/* Disabled state for inline buttons */
button:disabled,
button:disabled:hover {
  opacity: 0.4 !important;
  cursor: not-allowed !important;
  filter: grayscale(0.5);
  transform: none !important;
  background: rgba(255, 255, 255, 0.12) !important;
  border-color: rgba(0, 0, 0, 0.04) !important;
  box-shadow: none !important;
  animation: none !important;
  pointer-events: auto !important;
}

/* Disabled state for glass-button */
.glass-button:disabled,
.glass-button:disabled:hover {
  opacity: 0.4 !important;
  cursor: not-allowed !important;
  filter: grayscale(0.5);
  transform: none !important;
  box-shadow: none !important;
  animation: none !important;
}

/* Disabled area for remote control section */
.remote-disabled {
  opacity: 0.4;
  pointer-events: none;
}
</style>
