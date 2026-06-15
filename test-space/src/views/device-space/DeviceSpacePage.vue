<template>
  <div class="flex gap-4 h-screen overflow-hidden">
    <div class="flex-1 flex flex-col gap-4 min-w-0 overflow-hidden">
    <!-- Connection Bar - always visible, moved up -->
    <div class="glass-panel rounded-xl p-3 flex items-center gap-3">
      <span class="material-symbols-outlined text-on-surface-variant text-[18px]">link</span>
      <input v-model="connectAddress"
        class="flex-1 bg-transparent border-none outline-none font-body-md text-body-md text-on-surface placeholder:text-on-surface-variant/50"
        placeholder="输入 IP 地址连接设备，例如: 192.168.1.100:5555" @keyup.enter="connectToDevice" />
      <button class="glass-button px-4 py-1.5 rounded-full font-label-md text-label-md flex items-center gap-1" @click="connectToDevice">
        <span class="material-symbols-outlined text-[16px]">add_link</span>连接
      </button>
      <div class="h-5 w-[1px] bg-glass-border-dark"></div>
      <div class="flex gap-2 flex-wrap items-center">
        <button v-for="device in devices" :key="device.serial"
          class="px-2.5 py-1 rounded-full font-caption text-caption flex items-center gap-1.5 transition-all group"
          :class="selectedDevice?.serial === device.serial ? 'glass-button glass-active' : 'glass-button'"
          @click="selectDevice(device)">
          <div class="w-2 h-2 rounded-full" :class="device.status === 'online' ? 'bg-success-indicator' : 'bg-outline-variant'"></div>
          {{ device.name }}
          <span class="material-symbols-outlined text-[12px] opacity-0 group-hover:opacity-100 transition-opacity text-on-surface-variant hover:text-error ml-0.5"
            @click.stop="disconnectDeviceHandler(device.serial)">close</span>
        </button>
        <span v-if="devices.length === 0" class="font-caption text-caption text-on-surface-variant/50">无设备连接</span>
      </div>
      <button class="glass-button px-2.5 py-1 rounded-full font-caption text-caption flex items-center gap-1" @click="scanDevices">
        <span class="material-symbols-outlined text-[14px]">refresh</span>
      </button>
    </div>

    <!-- Tab Switcher -->
    <div class="flex gap-2">
      <button v-for="tab in tabs" :key="tab.key"
        class="px-5 py-2 rounded-full font-label-md text-label-md transition-all"
        :class="activeTab === tab.key ? 'glass-active' : 'glass-button'"
        @click="activeTab = tab.key">
        <span class="material-symbols-outlined text-[16px] align-middle mr-1">{{ tab.icon }}</span>
        {{ tab.label }}
      </button>
    </div>

    <!-- Tab 1: 常用命令 -->
    <div v-show="activeTab === 'common'" class="flex flex-col gap-1 flex-grow min-h-0 overflow-hidden">
      <!-- Row 1: Info Query (left) + Text Input & Actions (right) -->
      <div class="grid grid-cols-12 gap-4">
        <div class="col-span-12 lg:col-span-5">
          <div class="glass-panel rounded-xl p-3">
            <h3 class="font-label-md text-label-md text-on-surface mb-2 flex items-center gap-1.5">
              <span class="material-symbols-outlined text-[16px]">settings_remote</span>设备操作
            </h3>
            <div class="grid grid-cols-2 gap-1.5">
              <button class="glass-button py-1.5 rounded-lg font-caption text-caption flex items-center justify-center gap-1"
                :disabled="!selectedDevice || !!infoLoading" @click="queryInfo('basic')">
                <span v-if="infoLoading === 'basic'" class="w-3 h-3 border-2 border-current border-t-transparent rounded-full animate-spin"></span>
                <span v-else class="material-symbols-outlined text-[14px]">info</span>基础信息
              </button>
              <button class="glass-button py-1.5 rounded-lg font-caption text-caption flex items-center justify-center gap-1"
                :disabled="!selectedDevice || !!infoLoading" @click="queryInfo('whaleos')">
                <span v-if="infoLoading === 'whaleos'" class="w-3 h-3 border-2 border-current border-t-transparent rounded-full animate-spin"></span>
                <span v-else class="material-symbols-outlined text-[14px]">tv</span>固件信息
              </button>
              <button class="glass-button py-1.5 rounded-lg font-caption text-caption flex items-center justify-center gap-1"
                :disabled="!selectedDevice || !!infoLoading" @click="queryInfo('keys')">
                <span v-if="infoLoading === 'keys'" class="w-3 h-3 border-2 border-current border-t-transparent rounded-full animate-spin"></span>
                <span v-else class="material-symbols-outlined text-[14px]">security</span>检查密钥
              </button>
            </div>
          </div>
        </div>
        <div class="col-span-12 lg:col-span-7">
          <div class="glass-panel rounded-xl p-3">
            <h3 class="font-label-md text-label-md text-on-surface mb-1.5 flex items-center gap-1.5">
              <span class="material-symbols-outlined text-[16px]">keyboard</span>快捷操作
            </h3>
            <div class="flex gap-2 relative mb-1.5">
              <div class="flex-1 relative">
                <input ref="textInputRef" v-model="inputTextValue"
                  class="w-full bg-white border border-outline-variant rounded-lg px-3 py-1 font-body-sm text-body-sm text-on-surface focus:ring-2 focus:ring-secondary/30 focus:border-secondary transition-all"
                  placeholder="输入要发送到设备的文本..." @keyup.enter="sendText" @focus="showTextHistory = true" @blur="hideTextHistoryDelayed" />
                <div v-if="showTextHistory && textHistory.length > 0" class="absolute top-full left-0 right-0 z-20 mt-1 glass-panel rounded-lg p-1 max-h-32 overflow-y-auto">
                  <button v-for="(h, i) in textHistory" :key="i" class="w-full text-left px-2 py-1 rounded font-caption text-caption text-on-surface hover:bg-white/30 truncate"
                    @mousedown.prevent @click="selectTextHistory(h)">{{ h }}</button>
                </div>
              </div>
              <button class="glass-button px-3 py-1.5 rounded-lg font-label-md text-label-md" @click="sendText" :disabled="!inputTextValue.trim()">发送</button>
            </div>
            <div class="flex gap-2 items-center flex-wrap">
              <button class="glass-button px-3 py-1.5 rounded-lg font-caption text-caption flex items-center gap-1" @click="takeScreenshot" :disabled="!selectedDevice">
                <span class="material-symbols-outlined text-[12px]">screenshot_monitor</span>截图
              </button>
              <button class="glass-button px-2 py-1.5 rounded-lg font-caption text-caption flex items-center gap-1"
                :class="isRecording ? 'bg-error/10 text-error border border-error/20' : ''"
                @click="toggleRecording">
                <span class="material-symbols-outlined text-[12px]">{{ isRecording ? 'stop' : 'videocam' }}</span>
                {{ isRecording ? '停止' : '录屏' }}
              </button>
              <button class="glass-button px-2 py-1.5 rounded-lg font-caption text-caption flex items-center gap-1"
                :disabled="!selectedDevice || logPrepActive" @click="clearLogcatLogs">
                <span class="material-symbols-outlined text-[12px]">delete</span>清空日志
              </button>
              <button class="glass-button px-2 py-1.5 rounded-lg font-caption text-caption flex items-center gap-1" @click="restartAdbServer">
                <span class="material-symbols-outlined text-[12px]">power_settings_new</span>重启ADB
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Row 2: Device Control (left) + Log Collection (right) — same row → aligned -->
      <div class="grid grid-cols-12 gap-4">
        <div class="col-span-12 lg:col-span-5">
          <div class="glass-panel rounded-xl p-3">
            <div class="grid grid-cols-3 gap-1.5">
              <button class="glass-button py-1.5 rounded-lg font-caption text-caption flex items-center justify-center gap-1 whitespace-nowrap" @click="confirmThen('重启设备?', rebootDevice)">
                <span class="material-symbols-outlined text-[14px]">restart_alt</span>重启
              </button>
              <button class="glass-button py-1.5 rounded-lg font-caption text-caption flex items-center justify-center gap-1 whitespace-nowrap" @click="rootDevice">
                <span class="material-symbols-outlined text-[14px]">shield</span>Root
              </button>
              <button class="glass-button py-1.5 rounded-lg font-caption text-caption flex items-center justify-center gap-1 whitespace-nowrap" @click="confirmThen('Remount 需要 root 权限，继续?', remountDevice)">
                <span class="material-symbols-outlined text-[14px]">folder_managed</span>Remount
              </button>
            </div>
          </div>
        </div>
        <div class="col-span-12 lg:col-span-7">
          <div class="glass-panel rounded-xl p-3">
            <div v-if="logPrepActive" class="mb-2 p-1.5 bg-secondary/5 rounded-lg font-caption text-caption text-secondary flex items-center gap-2">
              <span class="w-3 h-3 border-2 border-secondary border-t-transparent rounded-full animate-spin"></span>
              {{ logPrepMessage }}
            </div>
            <div class="flex gap-2 items-center flex-wrap">
              <button class="glass-button px-2.5 py-1.5 rounded-lg font-caption text-caption flex items-center gap-1"
                :class="logcatRunning ? 'bg-error/10 text-error border border-error/20' : ''"
                :disabled="logPrepActive" @click="toggleLogcat">
                <span class="material-symbols-outlined text-[12px]">{{ logcatRunning ? 'stop' : 'terminal' }}</span>
                实时日志
                <span v-if="logcatRunning" class="font-caption text-caption text-secondary bg-secondary/20 px-1 py-0.5 rounded-full text-[10px] ml-0.5">{{ logcatElapsed }}s</span>
              </button>
              <button class="glass-button px-2.5 py-1.5 rounded-lg font-caption text-caption flex items-center gap-1"
                :class="diagRunning ? 'bg-error/10 text-error border border-error/20' : ''"
                :disabled="logPrepActive" @click="toggleDiagnostic">
                <span class="material-symbols-outlined text-[12px]">{{ diagRunning ? 'stop' : 'diagnosis' }}</span>
                诊断包
                <span v-if="diagRunning" class="font-caption text-caption text-secondary bg-secondary/20 px-1 py-0.5 rounded-full text-[10px] ml-0.5">{{ diagElapsed }}s</span>
              </button>
              <button class="glass-button px-2.5 py-1.5 rounded-lg font-caption text-caption flex items-center gap-1"
                :class="bootLogcatRunning ? 'bg-error/10 text-error border border-error/20' : ''"
                :disabled="logPrepActive" @click="toggleBootLogcat">
                <span class="material-symbols-outlined text-[12px]">{{ bootLogcatRunning ? 'stop' : 'power' }}</span>
                开机日志
                <span v-if="bootLogcatRunning" class="font-caption text-caption text-secondary bg-secondary/20 px-1 py-0.5 rounded-full text-[10px] ml-0.5">{{ bootLogcatElapsed }}s</span>
              </button>
              <button class="glass-button px-2.5 py-1.5 rounded-lg font-caption text-caption flex items-center gap-1"
                :disabled="!selectedDevice" @click="generateBugreport">
                <span class="material-symbols-outlined text-[12px]">bug_report</span>Bugreport
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Row 3: Application Management (full width) -->
      <div class="flex-1 min-h-0 flex flex-col">
        <div class="glass-panel rounded-xl p-3 flex flex-col flex-1 min-h-0">
            <div class="flex items-center gap-3 mb-1">
              <h3 class="font-label-md text-label-md text-on-surface flex items-center gap-1.5 shrink-0">
                <span class="material-symbols-outlined text-[16px]">apps</span>应用管理
                <span class="font-caption text-caption text-on-surface-variant/60 font-normal">({{ sortedApps.length }})</span>
              </h3>
              <div class="flex gap-2 items-center flex-wrap">
                <button class="glass-button px-2 py-0.5 rounded-full font-caption text-caption flex items-center gap-1 text-[11px]" @click="refreshPackageList">
                  <span class="material-symbols-outlined text-[12px]">refresh</span>刷新
                </button>
                <label class="flex items-center gap-1 font-caption text-caption text-on-surface-variant cursor-pointer text-[11px]">
                  <input type="checkbox" v-model="showThirdParty" class="accent-secondary" @change="refreshPackageList" />第三方应用
                </label>
                <button class="glass-button px-2.5 py-0.5 rounded-lg font-caption text-caption flex items-center gap-1 text-[11px]" @click="apkDialogOpen = true">
                  <span class="material-symbols-outlined text-[12px]">upload</span>安装 APK
                </button>
                <button class="glass-button px-2.5 py-0.5 rounded-lg font-caption text-caption flex items-center gap-1 text-[11px]" @click="getCurrentForegroundApp">
                  <span class="material-symbols-outlined text-[12px]">center_focus_strong</span>前台应用
                </button>
              </div>
            </div>

            <!-- App Search + Path Query (dual-purpose) -->
            <div class="flex gap-2 mb-1.5 p-1.5 bg-white/10 rounded-lg items-center">
              <div class="relative">
                <span class="material-symbols-outlined absolute left-1.5 top-1/2 -translate-y-1/2 text-on-surface-variant text-[12px]">search</span>
                <input v-model="queryPackageName" class="w-72 bg-white/80 border border-outline-variant rounded-lg pl-6 pr-2 py-1 font-caption text-caption text-[11px] text-on-surface font-mono focus:ring-2 focus:ring-secondary/30"
                  placeholder="搜索应用..." @input="onAppSearchInput" @keyup.enter="queryAppPath" @focus="loadAppSearchHistory" @blur="hideAppSearchHistoryDelayed" />
                <div v-if="showAppSearchHistory && appSearchHistory.length > 0" class="absolute top-full left-0 right-0 z-20 mt-1 bg-white border border-outline-variant rounded-lg p-1 max-h-32 overflow-y-auto shadow-lg">
                  <button v-for="(h, i) in appSearchHistory" :key="i" class="w-full text-left px-2 py-1 rounded font-caption text-caption text-on-surface hover:bg-gray-100"
                    @mousedown.prevent @click="selectAppSearchHistory(h)">{{ h }}</button>
                </div>
              </div>
              <button class="glass-button px-1.5 py-1 rounded-lg font-caption text-caption flex items-center gap-1 text-[11px]" @click="queryAppPath">
                <span class="material-symbols-outlined text-[12px]">search</span>路径
              </button>
              <div class="flex-1"></div>
              <div v-if="totalPages > 1" class="flex items-center gap-1 shrink-0">
                <button class="glass-button p-0.5 rounded" :disabled="appPage <= 1" @click="appPage = Math.max(1, appPage - 1); nextTick(loadVisibleAppVersions)">
                  <span class="material-symbols-outlined text-[14px]">chevron_left</span>
                </button>
                <span class="font-caption text-caption text-on-surface-variant text-[11px] whitespace-nowrap">{{ appPage }} / {{ totalPages }}</span>
                <button class="glass-button p-0.5 rounded" :disabled="appPage >= totalPages" @click="appPage = Math.min(totalPages, appPage + 1); nextTick(loadVisibleAppVersions)">
                  <span class="material-symbols-outlined text-[14px]">chevron_right</span>
                </button>
              </div>
            </div>

            <!-- App List -->
            <div ref="appListContainer" class="flex-1 min-h-0 overflow-y-auto custom-scrollbar" :style="{ maxHeight: appListMaxHeight + 'px' }">
              <div v-if="currentPageApps.length === 0" class="text-center py-3">
                <p class="font-caption text-caption text-on-surface-variant/50">暂无应用，点击刷新加载</p>
              </div>
              <div v-for="app in currentPageApps" :key="app.package_name" :ref="(el) => { if (el && !appItemMeasured) measureAppItem(el as HTMLElement) }" class="flex items-center gap-1 py-0 px-1.5 rounded hover:bg-white/20 transition-colors border-b border-outline-variant/20 last:border-0 group">
                <div class="flex gap-0.5 shrink-0">
                  <button class="glass-button p-1 rounded" title="启动" @click="startApp(app.package_name)">
                    <span class="material-symbols-outlined text-[16px] text-success-indicator">play_arrow</span>
                  </button>
                  <button class="glass-button p-1 rounded" title="停止" @click="stopApp(app.package_name)">
                    <span class="material-symbols-outlined text-[16px] text-tertiary">stop</span>
                  </button>
                  <button class="glass-button p-1 rounded" title="详情" @click="showAppDetail(app.package_name)">
                    <span class="material-symbols-outlined text-[16px]">info</span>
                  </button>
                  <button class="glass-button p-1 rounded" title="下载APK" @click="downloadApk(app.package_name)">
                    <span class="material-symbols-outlined text-[16px]">download</span>
                  </button>
                  <button class="glass-button p-1 rounded" title="清除数据" @click="clearApp(app.package_name)">
                    <span class="material-symbols-outlined text-[16px] text-error">delete_sweep</span>
                  </button>
                  <button class="glass-button p-1 rounded" title="卸载" @click="confirmThen(`卸载 ${app.package_name}?`, () => uninstallPkg(app.package_name))">
                    <span class="material-symbols-outlined text-[16px] text-error">delete</span>
                  </button>
                </div>
                <div class="flex items-center gap-1.5 min-w-0 flex-1 ml-0.5">
                  <span class="font-body-sm text-body-sm text-on-surface font-mono cursor-pointer hover:text-secondary hover:underline truncate"
                    :title="app.package_name" @click="copyPackageName(app.package_name)">{{ app.package_name }}</span>
                  <span v-if="app.version_name" class="font-caption text-caption text-secondary bg-secondary/10 px-1 py-0.5 rounded-full cursor-pointer shrink-0 text-[10px]"
                    :title="'点击复制版本信息'" @click="copyVersionInfo(app.package_name)">
                    v{{ app.version_name }}{{ app.version_code ? ` (${app.version_code})` : '' }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

    </div>

    <!-- Tab 2: 其他命令 -->
    <div v-show="activeTab === 'other'" class="grid grid-cols-12 gap-4 flex-grow min-h-0 overflow-y-auto">
      <!-- Left Column -->
      <div class="col-span-12 lg:col-span-4 flex flex-col gap-4">

        <!-- Remote Control -->
        <div class="glass-panel rounded-xl p-3">
          <h3 class="font-label-md text-label-md text-on-surface mb-2 flex items-center gap-1.5">
            <span class="material-symbols-outlined text-[16px]">gamepad</span>遥控器
          </h3>
          <div class="relative w-36 h-36 mx-auto mb-3">
            <button class="absolute top-0 left-1/2 -translate-x-1/2 w-10 h-10 glass-button rounded-full flex items-center justify-center" @click="sendKey('19')">
              <span class="material-symbols-outlined text-[18px]">keyboard_arrow_up</span>
            </button>
            <button class="absolute bottom-0 left-1/2 -translate-x-1/2 w-10 h-10 glass-button rounded-full flex items-center justify-center" @click="sendKey('20')">
              <span class="material-symbols-outlined text-[18px]">keyboard_arrow_down</span>
            </button>
            <button class="absolute left-0 top-1/2 -translate-y-1/2 w-10 h-10 glass-button rounded-full flex items-center justify-center" @click="sendKey('21')">
              <span class="material-symbols-outlined text-[18px]">keyboard_arrow_left</span>
            </button>
            <button class="absolute right-0 top-1/2 -translate-y-1/2 w-10 h-10 glass-button rounded-full flex items-center justify-center" @click="sendKey('22')">
              <span class="material-symbols-outlined text-[18px]">keyboard_arrow_right</span>
            </button>
            <button class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-12 h-12 glass-button rounded-full flex items-center justify-center bg-secondary/10" @click="sendKey('23')">
              <span class="material-symbols-outlined text-secondary text-[20px]">check</span>
            </button>
          </div>
          <div class="grid grid-cols-5 gap-1.5 mb-2">
            <button class="glass-button py-1 rounded-lg font-caption text-caption flex flex-col items-center gap-0.5" @click="sendKey('3')">
              <span class="material-symbols-outlined text-[14px]">home</span>Home
            </button>
            <button class="glass-button py-1 rounded-lg font-caption text-caption flex flex-col items-center gap-0.5" @click="sendKey('4')">
              <span class="material-symbols-outlined text-[14px]">arrow_back</span>返回
            </button>
            <button class="glass-button py-1 rounded-lg font-caption text-caption flex flex-col items-center gap-0.5" @click="sendKey('26')">
              <span class="material-symbols-outlined text-[14px]">power_settings_new</span>电源
            </button>
            <button class="glass-button py-1 rounded-lg font-caption text-caption flex flex-col items-center gap-0.5" @click="sendKey('82')">
              <span class="material-symbols-outlined text-[14px]">menu</span>菜单
            </button>
            <button class="glass-button py-1 rounded-lg font-caption text-caption flex flex-col items-center gap-0.5" @click="sendKey('187')">
              <span class="material-symbols-outlined text-[14px]">apps</span>最近
            </button>
          </div>
          <div class="grid grid-cols-3 gap-1.5 mb-2">
            <button class="glass-button py-1.5 rounded-lg font-caption text-caption flex items-center justify-center gap-1" @click="sendKey('24')">
              <span class="material-symbols-outlined text-[14px]">volume_up</span>Vol+
            </button>
            <button class="glass-button py-1.5 rounded-lg font-caption text-caption flex items-center justify-center gap-1" @click="sendKey('25')">
              <span class="material-symbols-outlined text-[14px]">volume_down</span>Vol-
            </button>
            <button class="glass-button py-1.5 rounded-lg font-caption text-caption flex items-center justify-center gap-1" @click="sendKey('164')">
              <span class="material-symbols-outlined text-[14px]">volume_off</span>静音
            </button>
          </div>
          <div class="grid grid-cols-5 gap-1">
            <button v-for="n in 9" :key="n" class="glass-button py-1.5 rounded-lg font-caption text-caption" @click="sendKey(String(7 + n))">{{ n }}</button>
            <button class="glass-button py-1.5 rounded-lg font-caption text-caption" @click="sendKey('0')">0</button>
            <button class="glass-button py-1.5 rounded-lg font-caption text-caption flex items-center justify-center gap-0.5" @click="sendKey('176')">
              <span class="material-symbols-outlined text-[12px]">settings</span>设置
            </button>
            <button class="glass-button py-1.5 rounded-lg font-caption text-caption" @click="sendKey('66')">回车</button>
            <button class="glass-button py-1.5 rounded-lg font-caption text-caption" @click="sendKey('67')">退格</button>
            <button class="glass-button py-1.5 rounded-lg font-caption text-caption" @click="sendKey('61')">Tab</button>
          </div>
        </div>

        <!-- Custom Commands -->
        <div class="glass-panel rounded-xl p-3">
          <div class="flex justify-between items-center mb-2">
            <h3 class="font-label-md text-label-md text-on-surface flex items-center gap-1.5">
              <span class="material-symbols-outlined text-[16px]">terminal</span>快捷命令
            </h3>
            <button class="glass-button p-1 rounded" @click="addCustomCommand">
              <span class="material-symbols-outlined text-[16px]">add</span>
            </button>
          </div>
          <div v-if="editingCmdIndex !== null" class="mb-2 space-y-1.5 p-2 bg-white/10 rounded-xl">
            <input v-model="editingCmdName" class="w-full bg-white/80 border border-outline-variant rounded-lg px-2 py-1 font-caption text-caption text-on-surface focus:ring-2 focus:ring-secondary/30" placeholder="命令名称" />
            <input v-model="editingCmdValue" class="w-full bg-white/80 border border-outline-variant rounded-lg px-2 py-1 font-caption text-caption text-on-surface font-mono focus:ring-2 focus:ring-secondary/30" placeholder="shell 命令" @keyup.enter="saveCustomCommand" />
            <div class="flex gap-2 justify-end">
              <button class="glass-button px-2 py-0.5 rounded-lg font-caption text-caption" @click="cancelEditCommand">取消</button>
              <button class="glass-button px-2 py-0.5 rounded-lg font-caption text-caption" @click="saveCustomCommand">保存</button>
            </div>
          </div>
          <div class="grid grid-cols-2 gap-1.5">
            <button v-for="(cmd, idx) in customCommands" :key="idx"
              class="glass-button py-1.5 px-2 rounded-lg font-caption text-caption text-left truncate group flex items-center gap-1" @click="executeCustomCommand(cmd.command)">
              <span class="material-symbols-outlined text-[14px] shrink-0">play_arrow</span>
              <span class="truncate">{{ cmd.name }}</span>
              <span class="ml-auto material-symbols-outlined text-[12px] opacity-0 group-hover:opacity-100 text-on-surface-variant hover:text-error shrink-0"
                @click.stop="removeCustomCommand(idx)">close</span>
            </button>
            <p v-if="customCommands.length === 0" class="col-span-2 font-caption text-caption text-on-surface-variant/50 text-center py-2">点击 + 添加快捷命令</p>
          </div>
        </div>
      </div>

      <!-- Right Column -->
      <div class="col-span-12 lg:col-span-8 flex flex-col gap-4">

        <!-- File Browser -->
        <div class="glass-panel rounded-xl p-3">
          <h3 class="font-label-md text-label-md text-on-surface mb-2 flex items-center gap-1.5">
            <span class="material-symbols-outlined text-[16px]">folder_open</span>文件管理
          </h3>
          <div class="flex gap-2 mb-2">
            <div class="flex-1 relative">
              <input v-model="remotePath" ref="remotePathInputRef"
                class="w-full bg-white border border-outline-variant rounded-lg px-3 py-1.5 font-body-sm text-body-sm text-on-surface font-mono focus:ring-2 focus:ring-secondary/30 focus:border-secondary transition-all"
                placeholder="远程路径，如 /sdcard/" @focus="showRemotePathHistory = true" @blur="hideRemotePathHistoryDelayed" />
              <div v-if="showRemotePathHistory && remotePathHistory.length > 0" class="absolute top-full left-0 right-0 z-20 mt-1 glass-panel rounded-lg p-1 max-h-32 overflow-y-auto">
                <button v-for="(h, i) in remotePathHistory" :key="i" class="w-full text-left px-2 py-1 rounded font-caption text-caption text-on-surface hover:bg-white/30 truncate"
                  @mousedown.prevent @click="selectRemotePathHistory(h)">{{ h }}</button>
              </div>
            </div>
            <button class="glass-button px-3 py-1.5 rounded-lg font-caption text-caption flex items-center gap-1" @click="listRemoteDir">
              <span class="material-symbols-outlined text-[14px]">list</span>列出
            </button>
            <button class="glass-button px-3 py-1.5 rounded-lg font-caption text-caption flex items-center gap-1" @click="pushToCurrentDir">
              <span class="material-symbols-outlined text-[14px]">upload</span>上传
            </button>
            <button class="glass-button px-3 py-1.5 rounded-lg font-caption text-caption flex items-center gap-1" @click="pullFromCurrentDir">
              <span class="material-symbols-outlined text-[14px]">download</span>下载
            </button>
          </div>
          <div class="max-h-40 overflow-y-auto custom-scrollbar bg-[#1a1c1d]/5 rounded-xl font-mono text-[11px] leading-relaxed">
            <div class="p-2">
              <div v-if="directoryListing" class="text-on-surface-variant whitespace-pre-wrap">{{ directoryListing }}</div>
              <div v-else class="text-on-surface-variant/30 text-center py-3">输入路径后点击列出</div>
            </div>
          </div>
        </div>

        <!-- Device Config -->
        <div class="glass-panel rounded-xl p-3">
          <h3 class="font-label-md text-label-md text-on-surface mb-2 flex items-center gap-1.5">
            <span class="material-symbols-outlined text-[16px]">tune</span>设备配置
          </h3>
          <div class="flex gap-2 mb-2 flex-wrap">
            <button v-for="cfg in commonConfigs" :key="cfg.path"
              class="glass-button px-2.5 py-1 rounded-lg font-caption text-caption flex items-center gap-1" @click="fetchConfig(cfg.path)">
              <span class="material-symbols-outlined text-[14px]">file_copy</span>{{ cfg.name }}
            </button>
            <button class="glass-button px-2.5 py-1 rounded-lg font-caption text-caption flex items-center gap-1" @click="configDialogOpen = true">
              <span class="material-symbols-outlined text-[14px]">edit</span>修改配置
            </button>
          </div>
          <div v-if="configContent !== null" class="space-y-1.5">
            <div class="flex justify-between items-center">
              <span class="font-caption text-caption text-on-surface-variant font-mono">{{ configPath }}</span>
              <div class="flex gap-1">
                <button class="glass-button px-2.5 py-1 rounded-lg font-caption text-caption" @click="saveConfig">保存到设备</button>
                <button class="glass-button px-2.5 py-1 rounded-lg font-caption text-caption" @click="saveConfigLocally">保存到本地</button>
              </div>
            </div>
            <textarea v-model="configContent"
              class="w-full h-40 bg-[#1a1c1d]/5 rounded-xl p-2 font-mono text-[11px] text-on-surface border-0 focus:ring-2 focus:ring-secondary/30 resize-y"
              spellcheck="false"></textarea>
          </div>
        </div>

        <!-- Screen Mirror -->
        <div class="glass-panel rounded-xl p-4">
          <h3 class="font-headline-md text-headline-md text-on-surface mb-3 flex items-center gap-2">
            <span class="material-symbols-outlined text-[20px]">screenshot_monitor</span>屏幕镜像
          </h3>
          <div class="flex gap-3 items-center mb-3">
            <div class="flex items-center gap-1.5">
              <span class="font-caption text-caption text-on-surface-variant">帧率:</span>
              <input v-model.number="mirrorFps" type="range" min="1" max="10" step="1" class="w-20 accent-secondary" />
              <span class="font-caption text-caption text-on-surface font-mono w-5">{{ mirrorFps }}</span>
            </div>
            <div class="flex items-center gap-1.5">
              <span class="font-caption text-caption text-on-surface-variant">分辨率:</span>
              <select v-model="mirrorResolution"
                class="bg-white/80 border border-outline-variant rounded-lg px-2 py-1 font-caption text-caption text-on-surface focus:ring-2 focus:ring-secondary/30">
                <option value="720">720p</option>
                <option value="1080">1080p</option>
                <option value="1280">1280p</option>
              </select>
            </div>
            <button class="glass-button px-4 py-1.5 rounded-lg font-label-md text-label-md flex items-center gap-1"
              :class="isMirroring ? 'bg-error/10 text-error border border-error/20' : ''"
              @click="toggleMirror">
              <span class="material-symbols-outlined text-[16px]">{{ isMirroring ? 'stop' : 'play_arrow' }}</span>
              {{ isMirroring ? '停止镜像' : '启动镜像' }}
            </button>
            <span v-if="isMirroring" class="font-caption text-caption text-secondary">
              {{ mirrorFrameCount }}帧 · {{ currentMirrorFps.toFixed(1) }} FPS
            </span>
          </div>
          <div class="flex items-center justify-center min-h-[240px] bg-black/5 rounded-xl overflow-hidden relative">
            <canvas v-show="isMirroring && mirrorFrameCount > 0" ref="mirrorCanvas" class="max-w-full max-h-[400px]"></canvas>
            <div v-if="!isMirroring" class="text-center">
              <span class="material-symbols-outlined text-5xl text-on-surface-variant/30">screenshot_monitor</span>
              <p class="font-body-md text-body-md text-on-surface-variant/50 mt-2">启动屏幕镜像查看设备实时画面</p>
            </div>
            <div v-if="isMirroring && mirrorFrameCount === 0" class="absolute inset-0 flex items-center justify-center bg-black/20">
              <span class="font-body-md text-body-md text-white/80">等待接收图像数据...</span>
            </div>
          </div>
          <div class="flex gap-2 mt-2">
            <button class="glass-button px-3 py-1 rounded-full font-caption text-caption flex items-center gap-1" @click="takeScreenshotFromMirror">
              <span class="material-symbols-outlined text-[14px]">screenshot_monitor</span>截图
            </button>
            <button class="px-3 py-1 rounded-full font-caption text-caption flex items-center gap-1"
              :class="isRecording ? 'bg-error/10 text-error border border-error/20' : 'glass-button'"
              @click="toggleRecording">
              <span class="material-symbols-outlined text-[14px]">{{ isRecording ? 'stop' : 'videocam' }}</span>
              {{ isRecording ? '停止录屏' : '开始录屏' }}
            </button>
          </div>
        </div>
      </div>
    </div>
    </div>

    <!-- Config Modify Dialog -->
    <Teleport to="body">
      <Transition name="fade">
        <div v-if="configDialogOpen" class="fixed inset-0 z-50 flex items-center justify-center" @click.self="configDialogOpen = false">
          <div class="absolute inset-0 bg-black/10 backdrop-blur-sm"></div>
          <div class="glass-panel rounded-[2rem] p-6 w-full max-w-md relative z-10 bg-white/60">
            <div class="flex justify-between items-center mb-4">
              <h3 class="font-headline-md text-headline-md text-on-surface font-semibold">修改配置</h3>
              <button class="glass-button p-1 rounded" @click="configDialogOpen = false">
                <span class="material-symbols-outlined text-[18px]">close</span>
              </button>
            </div>
            <div class="space-y-3">
              <div>
                <label class="font-caption text-caption text-on-surface-variant mb-1 block">配置文件路径</label>
                <input v-model="configModPath" class="w-full bg-white/80 border border-outline-variant rounded-lg px-3 py-2 font-caption text-caption text-on-surface font-mono focus:ring-2 focus:ring-secondary/30"
                  placeholder="/system/build.prop" />
              </div>
              <div>
                <label class="font-caption text-caption text-on-surface-variant mb-1 block">键名</label>
                <input v-model="configModKey" class="w-full bg-white/80 border border-outline-variant rounded-lg px-3 py-2 font-caption text-caption text-on-surface font-mono focus:ring-2 focus:ring-secondary/30"
                  placeholder="ro.product.model" />
              </div>
              <div>
                <label class="font-caption text-caption text-on-surface-variant mb-1 block">值</label>
                <input v-model="configModValue" class="w-full bg-white/80 border border-outline-variant rounded-lg px-3 py-2 font-caption text-caption text-on-surface font-mono focus:ring-2 focus:ring-secondary/30"
                  placeholder="新值" @keyup.enter="handleModifyConfig" />
              </div>
              <button class="w-full glass-button py-2 rounded-lg font-label-md text-label-md flex items-center justify-center gap-1" :disabled="!configModKey.trim() || !configModValue.trim()" @click="handleModifyConfig">
                <span class="material-symbols-outlined text-[16px]">save</span>写入配置
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- Info Query Dialog -->
    <Teleport to="body">
      <Transition name="fade">
        <div v-if="infoDialog.show" class="fixed inset-0 z-50 flex items-center justify-center" @click.self="infoDialog.show = false">
          <div class="absolute inset-0 bg-black/10 backdrop-blur-sm"></div>
          <div class="glass-panel rounded-[2rem] p-6 w-full max-w-xl max-h-[80vh] relative z-10 bg-white/60 overflow-y-auto">
            <div class="flex justify-between items-center mb-4">
              <h3 class="font-label-lg text-label-lg text-on-surface font-semibold">{{ infoDialog.title }}</h3>
              <button class="glass-button p-1 rounded" @click="infoDialog.show = false">
                <span class="material-symbols-outlined text-[18px]">close</span>
              </button>
            </div>
            <div class="space-y-1.5">
              <div v-for="(item, idx) in infoDialog.entries" :key="idx" class="border-b border-outline-variant/20 py-1.5 last:border-0">
                <div class="flex flex-col gap-0.5">
                  <span class="font-label-md text-label-md text-on-surface font-medium text-[13px] break-all">{{ item.key }}</span>
                  <div class="flex items-start gap-1">
                    <span class="font-body-sm text-body-sm text-on-surface-variant break-all text-[12px]">{{ item.value }}</span>
                    <button v-if="item.raw" class="shrink-0 text-[11px] text-secondary hover:text-secondary/70" @click="toggleInfoExpand(idx)">
                      <span class="material-symbols-outlined text-[14px]">{{ infoDialogExpanded.has(idx) ? 'expand_less' : 'expand_more' }}</span>
                    </button>
                  </div>
                </div>
                <pre v-if="item.raw && infoDialogExpanded.has(idx)" class="mt-1 p-1.5 bg-black/5 rounded text-[11px] font-mono whitespace-pre-wrap break-all max-h-32 overflow-y-auto">{{ item.raw }}</pre>
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
              <h3 class="font-label-lg text-label-lg text-on-surface font-semibold">{{ resultDialog.title }}</h3>
              <button class="glass-button p-1 rounded" @click="resultDialog.show = false">
                <span class="material-symbols-outlined text-[18px]">close</span>
              </button>
            </div>
            <pre class="bg-black/5 rounded-xl p-3 text-[12px] font-mono whitespace-pre-wrap break-all max-h-64 overflow-y-auto mb-3">{{ resultDialog.content }}</pre>
            <div class="flex gap-2 justify-end">
              <button class="glass-button px-3 py-1 rounded-lg font-label-md text-label-md" @click="resultDialog.show = false">关闭</button>
              <button class="glass-button px-3 py-1 rounded-lg font-label-md text-label-md flex items-center gap-1" @click="copyToClipboard(resultDialog.content); showToast('已复制')">
                <span class="material-symbols-outlined text-[14px]">content_copy</span>复制
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
              <h3 class="font-label-lg text-label-lg text-on-surface font-semibold break-all">{{ appDetailDialog.title }}</h3>
              <button class="glass-button p-1 rounded shrink-0" @click="appDetailDialog.show = false">
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
              <button class="glass-button px-3 py-1 rounded-lg font-label-md text-label-md" @click="appDetailDialog.show = false">关闭</button>
              <button class="glass-button px-3 py-1 rounded-lg font-label-md text-label-md flex items-center gap-1" @click="copyToClipboard(appDetailDialog.pkg); showToast('包名已复制')">
                <span class="material-symbols-outlined text-[14px]">content_copy</span>复制包名
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- APK Install Dialog -->
    <Teleport to="body">
      <Transition name="fade">
        <div v-if="apkDialogOpen" class="fixed inset-0 z-50 flex items-center justify-center" @click.self="apkDialogOpen = false">
          <div class="absolute inset-0 bg-black/10 backdrop-blur-sm"></div>
          <div class="glass-panel rounded-[2rem] p-6 w-full max-w-md relative z-10 bg-white/60">
            <div class="flex justify-between items-center mb-4">
              <h3 class="font-label-md text-label-md text-on-surface font-semibold flex items-center gap-1.5">
                <span class="material-symbols-outlined text-[16px]">upload</span>安装 APK
              </h3>
              <button class="glass-button p-1 rounded" @click="apkDialogOpen = false">
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
                <p v-if="!apkFilePath" class="font-caption text-caption text-on-surface-variant/60 mt-1">拖拽 APK 文件到此处，或点击选择</p>
                <p v-else class="font-caption text-caption text-secondary font-mono mt-1 truncate">{{ apkFilePath }}</p>
              </div>
              <!-- Overwrite checkbox -->
              <label class="flex items-center gap-2 font-caption text-caption text-on-surface cursor-pointer px-1">
                <input type="checkbox" v-model="reinstallApk" class="accent-secondary" />
                覆盖安装（保留数据）
              </label>
              <!-- Actions -->
              <div class="flex gap-2 justify-end">
                <button class="glass-button px-4 py-1.5 rounded-lg font-label-md text-label-md" @click="apkDialogOpen = false">取消</button>
                <button class="glass-button px-4 py-1.5 rounded-lg font-label-md text-label-md flex items-center gap-1"
                  :disabled="!apkFilePath || apkInstalling" @click="handleApkInstall">
                  <span v-if="apkInstalling" class="w-3.5 h-3.5 border-2 border-secondary border-t-transparent rounded-full animate-spin"></span>
                  <span v-else class="material-symbols-outlined text-[16px]">upload</span>
                  {{ apkInstalling ? '安装中...' : '安装' }}
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
        <div v-if="confirmDialog.show" class="fixed inset-0 z-50 flex items-center justify-center" @click.self="confirmDialog.show = false">
          <div class="absolute inset-0 bg-black/10 backdrop-blur-sm"></div>
          <div class="glass-panel rounded-[2rem] p-6 w-full max-w-sm relative z-10 bg-white/60">
            <div class="flex items-center gap-3 mb-4">
              <span class="material-symbols-outlined text-[24px] text-error">warning</span>
              <h3 class="font-headline-md text-headline-md text-on-surface font-semibold">{{ confirmDialog.title }}</h3>
            </div>
            <div class="flex gap-2 justify-end">
              <button class="glass-button px-4 py-2 rounded-lg font-label-md text-label-md" @click="confirmDialog.show = false">取消</button>
              <button class="px-4 py-2 rounded-lg font-label-md text-label-md bg-error/10 text-error border border-error/20" @click="confirmDialog.onConfirm()">确认</button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- Command Execution Dialog -->
    <Teleport to="body">
      <Transition name="fade">
        <div v-if="cmdExec.show" class="fixed top-4 left-1/2 -translate-x-1/2 z-[100] w-[420px] max-w-[90vw]">
          <div class="glass-panel rounded-xl px-4 py-3 shadow-xl">
            <div class="flex items-center gap-2 mb-1">
              <span v-if="cmdExec.running" class="w-3.5 h-3.5 border-2 border-secondary border-t-transparent rounded-full animate-spin shrink-0"></span>
              <span v-else class="material-symbols-outlined text-[16px] text-success-indicator">check_circle</span>
              <span class="font-label-md text-label-md text-on-surface font-medium">{{ cmdExec.title }}</span>
            </div>
            <div v-if="cmdExec.command" class="text-green-600/80 font-mono text-[11px] mb-1.5 pb-1.5 border-b border-outline-variant/20">$ {{ cmdExec.command }}</div>
            <pre class="font-mono text-[11px] text-on-surface-variant max-h-[200px] overflow-y-auto custom-scrollbar whitespace-pre-wrap leading-relaxed">{{ cmdExec.output }}</pre>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- Toast -->
    <Teleport to="body">
      <Transition name="fade">
        <div v-if="toast.show" class="fixed bottom-8 left-1/2 -translate-x-1/2 z-50 glass-panel rounded-full px-5 py-2.5 flex items-center gap-2 shadow-lg">
          <span class="material-symbols-outlined text-[18px]"
            :class="toast.type === 'error' ? 'text-error' : 'text-success-indicator'">{{ toast.type === 'error' ? 'error' : 'check_circle' }}</span>
          <span class="font-body-md text-body-md text-on-surface">{{ toast.message }}</span>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from "vue";
import { useAdb, type DeviceProperties } from "@/composables/useAdb";
import { addInputHistory, getInputHistory, saveLogSession, getRunningLogSessions, removeLogSession } from "@/services/database";

const {
  listDevices, shell, installApk, uninstallApk, pushFile, pullFile, reboot, screenshot,
  connectDevice, disconnectDevice, rebootRecovery, rebootBootloader, rootDevice: adbRoot,
  remountDevice: adbRemount, getProperties, inputKeyevent, inputText: adbInputText,
  listPackages, startApp: adbStartApp, stopApp: adbStopApp, clearAppData, getCurrentApp,
  logcatClear, logcat, listDirectory, getAppInfo, logcatBufferResize, bugreport, dmesg,
  startScreenrecord, killServer, startServer, createZip,
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
const tabs = [
  { key: 'common', label: '常用命令', icon: 'terminal' },
  { key: 'other', label: '其他命令', icon: 'more_horiz' },
];
const activeTab = ref('common');

// ── Toast ──
const toast = ref({ show: false, message: "", type: "success" as "success" | "error" });
function showToast(message: string, type: "success" | "error" = "success") {
  toast.value = { show: true, message, type };
  setTimeout(() => { toast.value.show = false; }, 2500);
}

// ── Confirm Dialog ──
const confirmDialog = ref({ show: false, title: "", onConfirm: () => {} });
function confirmThen(title: string, action: () => Promise<void>) {
  confirmDialog.value = {
    show: true,
    title,
    onConfirm: async () => {
      confirmDialog.value.show = false;
      await action();
    },
  };
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
function finishCmdExec(output: string) {
  cmdExec.value.running = false;
  if (output) {
    const lastLines = cmdExec.value.output.split("\n").filter(Boolean);
    if (lastLines.length === 0 || lastLines[lastLines.length - 1] !== output) {
      cmdExec.value.output += output + "\n";
    }
  }
  cmdExecTimeout = setTimeout(() => { cmdExec.value.show = false; }, 3000);
}

// ── Device state ──
interface DeviceItem { serial: string; name: string; status: "online" | "offline"; os: string; }
const devices = ref<DeviceItem[]>([]);
const selectedDevice = ref<DeviceItem | null>(null);
const deviceProps = ref<DeviceProperties | null>(null);
const connectAddress = ref("");

const devicePropList = computed(() => {
  if (!deviceProps.value) return {};
  const p = deviceProps.value;
  return {
    "型号": p.model, "品牌": p.brand, "设备名": p.device, "产品": p.product,
    "Android": `Android ${p.android_version} (SDK ${p.sdk_version})`,
    "分辨率": p.resolution, "DPI": p.density, "Build": p.build_id,
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
const reinstallApk = ref(true);
const apkDialogOpen = ref(false);
const apkDragOver = ref(false);
const apkFilePath = ref("");
const apkInstalling = ref(false);

// ── Apps ──
interface AppEntry { package_name: string; version_name?: string; version_code?: string; }
const apps = ref<AppEntry[]>([]);
const showThirdParty = ref(false);

const showAppSearchHistory = ref(false);
const appSearchHistory = ref<string[]>([]);
const appPage = ref(1);

const loadedVersions = ref(new Set<string>());
let versionQueue: Promise<unknown> = Promise.resolve();
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
watch(activeTab, () => nextTick(recalcAppPageSize));
async function loadAppSearchHistory() {
  const entries = await getInputHistory('app_search');
  appSearchHistory.value = entries.map(e => e.value);
  showAppSearchHistory.value = true;
}

// ── File Browser + History ──
const remotePath = ref("/sdcard/");
const remotePathInputRef = ref<HTMLInputElement | null>(null);
const directoryListing = ref("");
const showRemotePathHistory = ref(false);
const remotePathHistory = ref<string[]>([]);
function hideRemotePathHistoryDelayed() { setTimeout(() => { showRemotePathHistory.value = false; }, 200); }
function selectRemotePathHistory(v: string) { remotePath.value = v; showRemotePathHistory.value = false; }
async function loadRemotePathHistory() {
  const entries = await getInputHistory('remote_path');
  remotePathHistory.value = entries.map(e => e.value);
}

// ── Device Config ──
interface ConfigItem { name: string; path: string; }
const commonConfigs: ConfigItem[] = [
  { name: "build.prop", path: "/system/build.prop" },
  { name: "default.prop", path: "/default.prop" },
  { name: "vendor/build.prop", path: "/vendor/build.prop" },
];
const configContent = ref<string | null>(null);
const configPath = ref("");
const configDialogOpen = ref(false);
const configModPath = ref("/system/build.prop");
const configModKey = ref("");
const configModValue = ref("");

// ── Custom Commands ──
interface CustomCommand { name: string; command: string; }
const customCommands = ref<CustomCommand[]>([]);
const editingCmdIndex = ref<number | null>(null);
const editingCmdName = ref("");
const editingCmdValue = ref("");

// ── Helper: yield to UI thread ──
function yieldToUI() { return new Promise(resolve => setTimeout(resolve, 0)); }

// ── Information Query ──
const infoLoading = ref("");
const infoDialog = ref({ show: false, title: "", entries: [] as { key: string; value: string; raw?: string }[] });
const infoDialogExpanded = ref(new Set<number>());
function toggleInfoExpand(idx: number) {
  if (infoDialogExpanded.value.has(idx)) infoDialogExpanded.value.delete(idx);
  else infoDialogExpanded.value.add(idx);
}

function showDeviceInfoDialog() {
  if (!selectedDevice.value || !deviceProps.value) { showToast("请先选择设备", "error"); return; }
  const p = deviceProps.value;
  infoDialog.value = { show: true, title: "设备信息", entries: [
    { key: "序列号", value: selectedDevice.value.serial },
    { key: "型号", value: p.model || "—" },
    { key: "品牌", value: p.brand || "—" },
    { key: "设备名", value: p.device || "—" },
    { key: "产品", value: p.product || "—" },
    { key: "Android", value: `${p.android_version || "—"} (SDK ${p.sdk_version || "—"})` },
    { key: "分辨率", value: p.resolution || "—" },
    { key: "DPI", value: p.density || "—" },
    { key: "Build", value: p.build_id || "—" },
  ]};
}

// ── Log Preparation (root + buffer resize, always) ──
const logPrepActive = ref(false);
const logPrepMessage = ref("");

async function prepareLogCapture() {
  if (!selectedDevice.value) { showToast("请先选择设备", "error"); return false; }
  logPrepActive.value = true;
  try {
    logPrepMessage.value = "正在获取 Root 权限...";
    await adbRoot(selectedDevice.value.serial);
    await yieldToUI();
    logPrepMessage.value = "正在扩大日志缓冲区至 64MB...";
    await logcatBufferResize(selectedDevice.value.serial, 64);
    await yieldToUI();
    return true;
  } catch (e: any) {
    showToast(`准备日志采集失败: ${e}`, "error");
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

const diagRunning = ref(false);
const diagElapsed = ref(0);
let diagTimeoutId: ReturnType<typeof setTimeout> | null = null;
const diagBuffer = ref<string[]>([]);

const bootLogcatRunning = ref(false);
const bootLogcatElapsed = ref(0);
let bootLogcatTimeoutId: ReturnType<typeof setTimeout> | null = null;
const bootLogcatBuffer = ref<string[]>([]);

// ── Screen Mirror (recursive setTimeout) ──
const isMirroring = ref(false);
const mirrorFps = ref(3);
const mirrorResolution = ref("1080");
const mirrorFrameCount = ref(0);
const currentMirrorFps = ref(0);
let mirrorTimeoutId: ReturnType<typeof setTimeout> | null = null;
const mirrorCanvas = ref<HTMLCanvasElement | null>(null);

// ── Screenshot & Recording ──
const screenshotDataUrl = ref("");
const isRecording = ref(false);

// ── Device auto-refresh ──
let autoRefreshId: ReturnType<typeof setInterval> | null = null;

// ── Custom commands ──
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
async function executeCustomCommand(cmd: string) {
  if (!selectedDevice.value) return;
  try { const r = await shell(selectedDevice.value.serial, cmd); showToast(r.substring(0, 200)); }
  catch (e: any) { showToast(`执行失败: ${e}`, "error"); }
}

// ── Device operations ──
async function scanDevices() {
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
    if (devices.value.length > 0 && !selectedDevice.value) selectDevice(devices.value[0]);
  } catch { showToast("扫描设备失败", "error"); }
}
function selectDevice(device: DeviceItem) {
  selectedDevice.value = device;
  deviceProps.value = null;

  loadDeviceProperties();
  refreshPackageList();
}
async function loadDeviceProperties() {
  if (!selectedDevice.value) return;
  try { deviceProps.value = await getProperties(selectedDevice.value.serial); }
  catch { deviceProps.value = null; }
}
async function connectToDevice() {
  if (!connectAddress.value.trim()) return;
  try {
    const addr = connectAddress.value.trim();
    const r = await connectDevice(addr);
    await addInputHistory('connect_ip', addr);
    connectAddress.value = "";
    await scanDevices();
    showCmdExec("连接设备", `adb connect ${addr}`);
    appendCmdExec(r);
    finishCmdExec("设备已连接");
    showToast("设备已连接");
  } catch (e: any) { showToast(`连接失败: ${e}`, "error"); }
}
async function disconnectDeviceHandler(serial: string) {
  try {
    await disconnectDevice(serial);
    devices.value = devices.value.filter(d => d.serial !== serial);
    if (selectedDevice.value?.serial === serial) {
      selectedDevice.value = devices.value[0] || null;
      apps.value = [];
    }
    showToast("设备已断开");
  } catch { showToast("断开失败", "error"); }
}
async function restartAdbServer() {
  showCmdExec("重启 ADB 服务", "adb kill-server && adb start-server");
  try {
    appendCmdExec("正在停止 ADB 服务...");
    await killServer();
    appendCmdExec("ADB 服务已停止");
    appendCmdExec("正在启动 ADB 服务...");
    await startServer();
    appendCmdExec("ADB 服务已启动");
    await scanDevices();
    finishCmdExec("ADB 服务已重启");
    showToast("ADB 服务已重启");
  } catch (e: any) { finishCmdExec(`重启失败: ${e}`); showToast("ADB 重启失败", "error"); }
}
async function rebootDevice() {
  if (!selectedDevice.value) return;
  showCmdExec("重启设备", "adb reboot");
  try {
    appendCmdExec("正在发送重启命令...");
    await reboot(selectedDevice.value.serial);
    finishCmdExec("重启命令已发送，设备正在重启...");
    showToast("重启命令已发送");
  } catch { finishCmdExec("重启失败"); showToast("重启失败", "error"); }
}
async function rebootToRecovery() {
  if (!selectedDevice.value) return;
  showCmdExec("重启到 Recovery", "adb reboot recovery");
  try {
    appendCmdExec("正在发送重启命令...");
    await rebootRecovery(selectedDevice.value.serial);
    finishCmdExec("正在重启到 Recovery...");
    showToast("正在重启到 Recovery...");
  } catch { finishCmdExec("操作失败"); showToast("操作失败", "error"); }
}
async function rebootToBootloader() {
  if (!selectedDevice.value) return;
  showCmdExec("重启到 Bootloader", "adb reboot bootloader");
  try {
    appendCmdExec("正在发送重启命令...");
    await rebootBootloader(selectedDevice.value.serial);
    finishCmdExec("正在重启到 Bootloader...");
    showToast("正在重启到 Bootloader...");
  } catch { finishCmdExec("操作失败"); showToast("操作失败", "error"); }
}
async function rootDevice() {
  if (!selectedDevice.value) return;
  showCmdExec("Root 设备", "adb root");
  try {
    appendCmdExec("正在执行 adb root...");
    const r = await adbRoot(selectedDevice.value.serial);
    appendCmdExec(r);
    finishCmdExec("");
    showToast(r);
  } catch (e: any) { finishCmdExec(`Root 失败: ${e}`); showToast(`Root 失败: ${e}`, "error"); }
}
async function remountDevice() {
  if (!selectedDevice.value) return;
  showCmdExec("Remount 设备", "adb remount");
  try {
    appendCmdExec("正在执行 adb remount...");
    const r = await adbRemount(selectedDevice.value.serial);
    appendCmdExec(r);
    finishCmdExec("");
    showToast(r);
  } catch (e: any) { finishCmdExec(`Remount 失败: ${e}`); showToast(`Remount 失败: ${e}`, "error"); }
}
async function sendKey(keycode: string) {
  if (!selectedDevice.value) return;
  try { await inputKeyevent(selectedDevice.value.serial, keycode); } catch {}
}
async function sendText() {
  if (!selectedDevice.value || !inputTextValue.value.trim()) return;
  const text = inputTextValue.value;
  inputTextValue.value = "";
  showCmdExec("发送文本", `adb shell input text ${text}`);
  try {
    await adbInputText(selectedDevice.value.serial, text);
    await addInputHistory('input_text', text);
    appendCmdExec(`已发送: ${text}`);
    finishCmdExec("文本已发送");
    showToast("文本已发送");
  } catch { finishCmdExec("发送失败"); showToast("发送失败", "error"); }
}

// ── App Management ──
async function refreshPackageList() {
  if (!selectedDevice.value) return;
  try {
    const raw = await listPackages(selectedDevice.value.serial, showThirdParty.value);
    const oldVersionMap = new Map(apps.value.map(a => [a.package_name, { vn: a.version_name, vc: a.version_code }]));
    apps.value = raw.map((pkg: string) => {
      const old = oldVersionMap.get(pkg);
      return { package_name: pkg, version_name: old?.vn, version_code: old?.vc };
    });
    appPage.value = 1;
    loadedVersions.value = new Set();
    // Auto-load version info for first page
    nextTick(() => loadVisibleAppVersions());
  } catch { showToast("加载应用列表失败", "error"); }
}
async function loadVisibleAppVersions() {
  if (!selectedDevice.value) return;
  for (const app of currentPageApps.value) {
    if (app.version_name || loadedVersions.value.has(app.package_name)) continue;
    loadedVersions.value = new Set(loadedVersions.value).add(app.package_name);
    versionQueue = versionQueue.then(async () => {
      try {
        const info = await getAppInfo(selectedDevice.value!.serial, app.package_name);
        const vn = info.match(/versionName=([^\s]+)/)?.[1];
        const vc = info.match(/versionCode=(\d+)/)?.[1];
        if (vn || vc) {
          apps.value = apps.value.map(a => a.package_name === app.package_name ? { ...a, version_name: vn, version_code: vc } : a);
        }
      } catch {}
    });
  }
}
async function getCurrentForegroundApp() {
  if (!selectedDevice.value) return;
  try {
    const raw = await shell(selectedDevice.value.serial, "dumpsys window");
    const lines = raw.split("\n").filter(l => l.includes("mCurrentFocus") || l.includes("mFocusedApp"));
    const raw2 = lines.length > 0 ? lines.join("\n") : raw;
    const m = raw2.match(/([\w.]+\/[\w.]+)/);
    const result = m ? m[1] : "无前台应用";
    resultDialog.value = { show: true, title: "前台应用", content: result };
  } catch { resultDialog.value = { show: true, title: "前台应用", content: "获取失败" }; }
}
const appDetailDialog = ref({ show: false, title: "", pkg: "", entries: [] as { key: string; value: string }[] });
async function showAppDetail(pkg: string) {
  if (!selectedDevice.value) return;
  try {
    const info = await getAppInfo(selectedDevice.value.serial, pkg);
    const sizeRaw = await shell(selectedDevice.value.serial, `dumpsys diskstats ${pkg}`).catch(() => "");
    const entries: { key: string; value: string }[] = [];
    const patterns: [RegExp, string][] = [
      [/versionName=([^\s\n]+)/, "当前版本"],
      [/versionCode=(\d+)/, "当前版本号"],
      [/codePath=([^\s\n]+)/, "安装路径"],
      [/nativeLibraryDir=([^\s\n]+)/, "Native 库目录"],
      [/targetSdkVersion=(\d+)/, "目标 SDK"],
      [/minSdkVersion=(\d+)/, "最低 SDK"],
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
      entries.push({ key: "版本历史", value: history.join(" → ") });
    }
    if (sizeRaw) {
      const sizeMatch = sizeRaw.match(/(\d[\d,.]+)\s*(KB|MB|GB|bytes?)/i);
      if (sizeMatch) entries.push({ key: "应用大小", value: sizeMatch[1] + " " + sizeMatch[2] });
      const cacheMatch = sizeRaw.match(/Cache\s*size:\s*(\d[\d,.]+)\s*(KB|MB|GB|bytes?)/i);
      if (cacheMatch) entries.push({ key: "缓存大小", value: cacheMatch[1] + " " + cacheMatch[2] });
      const dataMatch = sizeRaw.match(/Data\s*size:\s*(\d[\d,.]+)\s*(KB|MB|GB|bytes?)/i);
      if (dataMatch) entries.push({ key: "数据大小", value: dataMatch[1] + " " + dataMatch[2] });
    }
    if (entries.length === 0) entries.push({ key: "提示", value: "无法解析应用信息，请确认包名正确" });
    appDetailDialog.value = { show: true, title: pkg, pkg, entries };
  } catch { showToast("获取详情失败", "error"); }
}

async function startApp(pkg: string) {
  if (!selectedDevice.value) return;
  showCmdExec("启动应用", `adb shell monkey -p ${pkg} 1`);
  try {
    appendCmdExec(`正在启动 ${pkg}...`);
    await adbStartApp(selectedDevice.value.serial, pkg);
    appendCmdExec(`已启动 ${pkg}`);
    finishCmdExec("应用已启动");
    showToast(`已启动 ${pkg}`);
  } catch {
    appendCmdExec("monkey 启动失败，尝试 am start 兜底...");
    try {
      const mainAct = await shell(selectedDevice.value.serial, 
        `cmd package resolve-activity --brief ${pkg} | tail -1`);
      if (mainAct && mainAct.includes("/")) {
        await shell(selectedDevice.value.serial, `am start -n ${mainAct.trim()}`);
        appendCmdExec(`已启动 ${pkg}`);
        finishCmdExec("应用已启动");
        showToast(`已启动 ${pkg}`);
        return;
      }
    } catch {}
    finishCmdExec("启动失败"); showToast("启动失败", "error");
  }
}
async function stopApp(pkg: string) {
  if (!selectedDevice.value) return;
  showCmdExec("停止应用", `adb shell am force-stop ${pkg}`);
  try {
    appendCmdExec(`正在停止 ${pkg}...`);
    await adbStopApp(selectedDevice.value.serial, pkg);
    appendCmdExec(`已停止 ${pkg}`);
    finishCmdExec("应用已停止");
    showToast(`已停止 ${pkg}`);
  } catch { finishCmdExec("停止失败"); showToast("停止失败", "error"); }
}
async function clearApp(pkg: string) {
  if (!selectedDevice.value) return;
  showCmdExec("清除数据", `adb shell pm clear ${pkg}`);
  try {
    appendCmdExec(`正在清除 ${pkg} 数据...`);
    await clearAppData(selectedDevice.value.serial, pkg);
    appendCmdExec(`已清除 ${pkg} 数据`);
    finishCmdExec("数据已清除");
    showToast(`已清除 ${pkg} 数据`);
  } catch { finishCmdExec("清除失败"); showToast("清除失败", "error"); }
}
async function uninstallPkg(pkg: string) {
  if (!selectedDevice.value) return;
  showCmdExec("卸载应用", `adb uninstall ${pkg}`);
  try {
    appendCmdExec(`正在卸载 ${pkg}...`);
    await uninstallApk(selectedDevice.value.serial, pkg);
    apps.value = apps.value.filter(a => a.package_name !== pkg);
    appendCmdExec(`已卸载 ${pkg}`);
    finishCmdExec("应用已卸载");
    showToast(`已卸载 ${pkg}`);
  } catch { finishCmdExec("卸载失败"); showToast("卸载失败", "error"); }
}
async function selectApkFile() {
  try {
    const { open } = await import("@tauri-apps/plugin-dialog");
    const selected = await open({ multiple: false, filters: [{ name: "APK", extensions: ["apk"] }] });
    if (selected) apkFilePath.value = selected;
  } catch {}
}
function handleApkDrop(e: DragEvent) {
  apkDragOver.value = false;
  const file = e.dataTransfer?.files?.[0];
  if (file?.name.endsWith(".apk")) {
    apkFilePath.value = file.name;
    showToast("请在安装弹窗中点击选择 APK 文件路径（浏览器拖拽暂不支持）", "error");
  } else {
    showToast("请拖入 .apk 文件", "error");
  }
}
async function handleApkInstall() {
  if (!selectedDevice.value || !apkFilePath.value) return;
  apkInstalling.value = true;
  try {
    await installApk(selectedDevice.value.serial, apkFilePath.value, reinstallApk.value);
    showToast("APK 安装成功");
    apkDialogOpen.value = false;
    apkFilePath.value = "";
  } catch (e: any) {
    showToast(`安装失败: ${e}`, "error");
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
    showToast(`版本: ${vn || "N/A"} (${vc || "?"})`);
  } catch { showToast("获取版本失败", "error"); }
  finally { setAppLoading(pkg, 'version', false); }
}

async function copyPackageName(pkg: string) {
  const ok = await copyToClipboard(pkg);
  showToast(ok ? "包名已复制" : "复制失败", ok ? "success" : "error");
}
async function copyVersionInfo(pkg: string) {
  const app = apps.value.find(a => a.package_name === pkg);
  if (!app?.version_name) { showToast("暂无版本信息", "error"); return; }
  const text = `${app.version_name}${app.version_code ? ` (${app.version_code})` : ''}`;
  const ok = await copyToClipboard(text);
  showToast(ok ? "版本信息已复制" : "复制失败", ok ? "success" : "error");
}
async function downloadApk(pkg: string) {
  if (!selectedDevice.value) return;
  showCmdExec("下载 APK", `adb shell dumpsys package ${pkg} | grep path:`);
  try {
    appendCmdExec("正在查询 APK 路径...");
    const info = await getAppInfo(selectedDevice.value.serial, pkg);
    const pathMatch = info.match(/path:?\s*(\S+)/);
    if (!pathMatch) { finishCmdExec("未找到 APK 路径"); showToast("未找到APK路径", "error"); return; }
    appendCmdExec(`APK 路径: ${pathMatch[1]}`);
    const { save } = await import("@tauri-apps/plugin-dialog");
    const dest = await save({ defaultPath: `${pkg}.apk`, filters: [{ name: "APK", extensions: ["apk"] }] });
    if (!dest) { cmdExec.value.show = false; return; }
    appendCmdExec("正在拉取 APK 文件...");
    await pullFile(selectedDevice.value.serial, pathMatch[1], dest);
    appendCmdExec(`已保存到: ${dest}`);
    finishCmdExec("APK 下载完成");
    showToast("APK 已下载");
  } catch { finishCmdExec("下载失败"); showToast("下载失败", "error"); }
}

// ── App Path Query ──
const resultDialog = ref({ show: false, title: "", content: "" });
async function queryAppPath() {
  if (!selectedDevice.value || !queryPackageName.value.trim()) return;
  try {
    const result = await shell(selectedDevice.value.serial, `pm path ${queryPackageName.value.trim()}`);
    const match = result.match(/package:(.+)/);
    if (match) {
      await addInputHistory('app_search', queryPackageName.value.trim());
      resultDialog.value = { show: true, title: `APK 路径 - ${queryPackageName.value.trim()}`, content: match[1].trim() };
    } else {
      showToast("未找到该应用", "error");
    }
  } catch { showToast("查询失败", "error"); }
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
      title = "基础设备信息";
      const props = await getProperties(serial);
      entries = Object.entries(props).map(([k, v]) => ({ key: k, value: v || "N/A" }));
    } else if (type === "whaleos") {
      title = "固件信息";
      const tvKeys = ["ro.product.model", "ro.product.tv.rcu", "ro.product.tv.deviceType", "ro.vendor.product.version",
        "ro.vendor.zeasn.firmwareID", "persist.sys.cur_country", "persist.sys.cur_language", "ro.boot.pid", "ro.boot.mac"];
      const results = await Promise.all(tvKeys.map(k => shell(serial, `getprop ${k}`).catch(() => "")));
      entries = tvKeys.map((key, i) => ({ key, value: results[i].trim() || "" })).filter(e => e.value !== "");
    } else if (type === "aosp") {
      title = "AOSP 固件信息";
      const aospKeys = ["ro.product.model", "ro.build.display.id", "ro.build.description", "ro.vendor.product.version",
        "ro.build.fingerprint", "ro.build.version.sdk", "ro.build.version.security_patch", "ro.product.cpu.abi"];
      const results = await Promise.all(aospKeys.map(k => shell(serial, `getprop ${k}`).catch(() => "(空)")));
      entries = aospKeys.map((key, i) => ({ key, value: results[i].trim() || "(空)" }));
    } else if (type === "keys") {
      title = "密钥检查结果";
      const checks = [
        { name: "HDCP 1.4", cmd: "tee_provision -qt 0x31" },
        { name: "HDCP 2.2", cmd: "tee_provision -qt 0x32" },
        { name: "MGKID", cmd: "tee_provision -qt 0xa2" },
        { name: "Widevine", cmd: "drminfo -d" },
        { name: "Dolby", cmd: "dolby_fw_dolbyms12 /oem/lib/ms12/libdolbyms12.so /data/test.so" },
      ];
      const checkResults = await Promise.all(checks.map(c =>
        shell(serial, c.cmd).then(r => {
          const success = !r.toLowerCase().includes("not provisioned") && !r.toLowerCase().includes("error");
          return { key: c.name, value: `${success ? "✅ 通过" : "❌ 失败"}\n> ${c.cmd}`, raw: r };
        }).catch((e: any) => ({ key: c.name, value: `❌ 执行错误`, raw: `${e}` }))
      ));
      entries = checkResults;
    }
    infoDialog.value = { show: true, title, entries };
  } catch { showToast("查询失败", "error"); }
  infoLoading.value = "";
}

// ── Log Collection ──
async function toggleLogcat() {
  if (!selectedDevice.value) return;
  if (logcatRunning.value) {
    stopLogcatCapture();
  } else {
    const ok = await prepareLogCapture();
    if (!ok) return;
    logcatBuffer.value = [];
    logcatRunning.value = true;
    logcatElapsed.value = 0;
    const session = { id: `logcat_${Date.now()}`, type: 'logcat' as const, deviceSerial: selectedDevice.value.serial, status: 'running' as const, startedAt: new Date().toISOString() };
    await saveLogSession(session);
    scheduleLogcatCapture();
    showCmdExec("实时日志", "adb logcat");
    appendCmdExec("日志采集已开始");
    finishCmdExec("日志采集已开始");
    showToast("日志采集已开始");
  }
}
async function scheduleLogcatCapture() {
  if (!logcatRunning.value || !selectedDevice.value) return;
  logcatElapsed.value += 2;
  try {
    const raw = await logcat(selectedDevice.value.serial, "all", 1000);
    logcatBuffer.value.push(raw);
    // Circular buffer: keep only last MAX_LOG_ENTRIES
    if (logcatBuffer.value.length > MAX_LOG_ENTRIES) {
      logcatBuffer.value = logcatBuffer.value.slice(-MAX_LOG_ENTRIES);
    }
  } catch {}
  await yieldToUI();
  if (logcatRunning.value) {
    logcatTimeoutId = setTimeout(scheduleLogcatCapture, 2000);
  }
}
async function stopLogcatCapture() {
  if (logcatTimeoutId) { clearTimeout(logcatTimeoutId); logcatTimeoutId = null; }
  logcatRunning.value = false;
  try {
    const { save } = await import("@tauri-apps/plugin-dialog");
    const dest = await save({ defaultPath: `logcat_${Date.now()}.txt`, filters: [{ name: "Text", extensions: ["txt"] }] });
    if (dest) {
      const { writeTextFile } = await import("@tauri-apps/plugin-fs");
      await writeTextFile(dest, logcatBuffer.value.join("\n\n"));
    }
  } catch {}
  logcatBuffer.value = [];
  // Clear session from DB
  try {
    const sessions = await getRunningLogSessions();
    for (const s of sessions) { if (s.type === 'logcat') await removeLogSession(s.id); }
  } catch {}
  showToast("日志采集已停止");
}

async function toggleDiagnostic() {
  if (!selectedDevice.value) return;
  if (diagRunning.value) {
    stopDiagnosticCapture();
  } else {
    const ok = await prepareLogCapture();
    if (!ok) return;
    diagBuffer.value = [];
    diagRunning.value = true;
    diagElapsed.value = 0;
    const session = { id: `diag_${Date.now()}`, type: 'diagnostic' as const, deviceSerial: selectedDevice.value.serial, status: 'running' as const, startedAt: new Date().toISOString() };
    await saveLogSession(session);
    scheduleDiagTimer();
    showCmdExec("诊断包");
    appendCmdExec("采集已开始，点击停止按钮收集并保存");
    finishCmdExec("诊断日志采集已开始");
    showToast("诊断日志采集已开始");
  }
}
function scheduleDiagTimer() {
  if (!diagRunning.value) return;
  diagElapsed.value += 2;
  if (diagRunning.value) {
    diagTimeoutId = setTimeout(scheduleDiagTimer, 2000);
  }
}
async function stopDiagnosticCapture() {
  if (diagTimeoutId) { clearTimeout(diagTimeoutId); diagTimeoutId = null; }
  diagRunning.value = false;
  await yieldToUI();
  try {
    const serial = selectedDevice.value!.serial;
    showCmdExec("收集诊断信息");
    appendCmdExec("正在收集各类日志...");

    const files: { filename: string; content: string }[] = [];
    function addFile(filename: string, label: string, content: string) {
      const header = `===== ${label} =====\nCollected at: ${new Date().toISOString()}\nDevice: ${serial}\n\n`;
      files.push({ filename, content: header + content });
    }

    // Logcat dump
    appendCmdExec("  正在收集 logcat...");
    try {
      const logcatContent = await logcat(serial, "all", 2000);
      addFile("logcat.txt", "Logcat (all)", logcatContent);
      appendCmdExec("  ✓ logcat.txt");
    } catch { addFile("logcat.txt", "Logcat (all)", "(收集失败)"); appendCmdExec("  ✗ logcat.txt"); }
    await yieldToUI();

    // dmesg
    appendCmdExec("  正在收集 dmesg...");
    try {
      const dmesgContent = await dmesg(serial);
      addFile("dmesg.txt", "dmesg", dmesgContent);
      appendCmdExec("  ✓ dmesg.txt");
    } catch { addFile("dmesg.txt", "dmesg", "(收集失败)"); appendCmdExec("  ✗ dmesg.txt"); }
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
      appendCmdExec(`  正在收集 ${label}...`);
      try {
        const result = await shell(serial, cmd);
        addFile(filename, label, result);
        appendCmdExec(`  ✓ ${filename}`);
      } catch {
        addFile(filename, label, "(命令执行失败)");
        appendCmdExec(`  ✗ ${filename}`);
      }
      await yieldToUI();
    }

    // Prompt user for save location
    const { save } = await import("@tauri-apps/plugin-dialog");
    const dest = await save({ defaultPath: `diagnostic_${Date.now()}.zip`, filters: [{ name: "ZIP Archive", extensions: ["zip"] }] });
    if (dest) {
      appendCmdExec("正在生成压缩包...");
      await createZip(files, dest);
      appendCmdExec("诊断包已保存到: " + dest);
      finishCmdExec("诊断包已生成");
      showToast("诊断日志已保存");
    } else {
      cmdExec.value.show = false;
    }
  } catch (e: any) {
    finishCmdExec(`保存失败: ${e}`);
    showToast("保存失败", "error");
  }
  diagBuffer.value = [];
  try {
    const sessions = await getRunningLogSessions();
    for (const s of sessions) { if (s.type === 'diagnostic') await removeLogSession(s.id); }
  } catch {}
}

async function toggleBootLogcat() {
  if (!selectedDevice.value) return;
  if (bootLogcatRunning.value) {
    stopBootLogcatCapture();
  } else {
    const ok = await prepareLogCapture();
    if (!ok) return;
    bootLogcatBuffer.value = [];
    bootLogcatRunning.value = true;
    bootLogcatElapsed.value = 0;
    const session = { id: `boot_${Date.now()}`, type: 'boot_logcat' as const, deviceSerial: selectedDevice.value.serial, status: 'running' as const, startedAt: new Date().toISOString() };
    await saveLogSession(session);
    try {
      await logcatClear(selectedDevice.value.serial);
      await reboot(selectedDevice.value.serial);
      showToast("设备已重启，等待重新连接...");
    } catch { showToast("重启失败", "error"); }
    scheduleBootPoll();
  }
}
async function scheduleBootPoll() {
  if (!bootLogcatRunning.value || !selectedDevice.value) return;
  bootLogcatElapsed.value += 3;
  // Timeout after 180s
  if (bootLogcatElapsed.value > 180) {
    showToast("设备重连超时(180s)，请手动检查设备状态", "error");
    bootLogcatRunning.value = false;
    return;
  }
  try {
    const adbDevices = await listDevices();
    const reconnected = adbDevices.find(d => d.status === "device");
    if (reconnected) {
      bootLogcatBuffer.value.push(`[设备重新连接: ${reconnected.serial}]`);
      // Now capture the boot logs
      try {
        const raw = await logcat(reconnected.serial, "all", 2000);
        bootLogcatBuffer.value.push(raw);
      } catch {}
      if (bootLogcatTimeoutId) { clearTimeout(bootLogcatTimeoutId); bootLogcatTimeoutId = null; }
      showToast("设备已重连，日志已获取");
    } else {
      await yieldToUI();
      if (bootLogcatRunning.value) {
        bootLogcatTimeoutId = setTimeout(scheduleBootPoll, 3000);
      }
    }
  } catch {
    await yieldToUI();
    if (bootLogcatRunning.value) {
      bootLogcatTimeoutId = setTimeout(scheduleBootPoll, 3000);
    }
  }
}
async function stopBootLogcatCapture() {
  if (bootLogcatTimeoutId) { clearTimeout(bootLogcatTimeoutId); bootLogcatTimeoutId = null; }
  bootLogcatRunning.value = false;
  try {
    const { save } = await import("@tauri-apps/plugin-dialog");
    const dest = await save({ defaultPath: `boot_logcat_${Date.now()}.txt`, filters: [{ name: "Text", extensions: ["txt"] }] });
    if (dest) {
      const { writeTextFile } = await import("@tauri-apps/plugin-fs");
      await writeTextFile(dest, bootLogcatBuffer.value.join("\n"));
    }
  } catch {}
  try {
    const sessions = await getRunningLogSessions();
    for (const s of sessions) { if (s.type === 'boot_logcat') await removeLogSession(s.id); }
  } catch {}
  showToast("开机日志采集已停止");
}

async function clearLogcatLogs() {
  if (!selectedDevice.value) return;
    showCmdExec("清空日志", "adb logcat -c");
  try {
    await logcatClear(selectedDevice.value.serial);
    appendCmdExec("设备日志已清空");
    finishCmdExec("设备日志已清空");
    showToast("设备日志已清空");
  } catch { finishCmdExec("清空失败"); showToast("清空失败", "error"); }
}

async function generateBugreport() {
  if (!selectedDevice.value) return;
  showCmdExec("生成 Bugreport", "adb bugreport");
  try {
    const { save } = await import("@tauri-apps/plugin-dialog");
    const dest = await save({ defaultPath: `bugreport_${Date.now()}.zip`, filters: [{ name: "Bugreport ZIP", extensions: ["zip"] }] });
    if (!dest) { cmdExec.value.show = false; return; }
    appendCmdExec("正在生成 bugreport，请耐心等待（可能需要 30-60 秒）...");
    await bugreport(selectedDevice.value.serial, dest);
    appendCmdExec("Bugreport 已保存到: " + dest);
    finishCmdExec("Bugreport 已生成");
    showToast("Bugreport 已生成");
  } catch (e: any) { finishCmdExec(`Bugreport 生成失败: ${e}`); showToast(`Bugreport 生成失败: ${e}`, "error"); }
}

// ── File Browser ──
async function listRemoteDir() {
  if (!selectedDevice.value || !remotePath.value.trim()) return;
  try { directoryListing.value = await listDirectory(selectedDevice.value.serial, remotePath.value.trim()); }
  catch { directoryListing.value = "获取目录失败"; }
}
async function pushToCurrentDir() {
  if (!selectedDevice.value || !remotePath.value.trim()) return;
  try {
    const { open } = await import("@tauri-apps/plugin-dialog");
    const selected = await open({ multiple: false });
    if (selected) { await pushFile(selectedDevice.value.serial, selected, remotePath.value.trim()); showToast("文件已推送"); listRemoteDir(); }
  } catch { showToast("推送失败", "error"); }
}
async function pullFromCurrentDir() {
  if (!selectedDevice.value || !remotePath.value.trim()) return;
  try {
    const { save } = await import("@tauri-apps/plugin-dialog");
    const dest = await save();
    if (dest) { await pullFile(selectedDevice.value.serial, remotePath.value.trim(), dest); showToast("文件已拉取"); }
  } catch { showToast("拉取失败", "error"); }
}

// ── Device Config ──
async function fetchConfig(path: string) {
  if (!selectedDevice.value) return;
  try { configContent.value = await shell(selectedDevice.value.serial, `cat ${path}`) || "(空文件)"; configPath.value = path; }
  catch { showToast("读取配置文件失败", "error"); }
}
async function saveConfig() {
  if (!selectedDevice.value || !configPath.value || configContent.value === null) return;
  try {
    const tmpPath = `${__dirname || ""}/tmp_config_${Date.now()}`;
    await pullFile(selectedDevice.value.serial, configPath.value, tmpPath);
    await pushFile(selectedDevice.value.serial, tmpPath, configPath.value);
    showToast("配置已保存到设备");
  } catch { showToast("保存失败，可能需要 root 权限", "error"); }
}
async function saveConfigLocally() {
  if (configContent.value === null) return;
  try {
    const { save } = await import("@tauri-apps/plugin-dialog");
    const dest = await save({ defaultPath: configPath.value.split("/").pop() || "config", filters: [{ name: "All Files", extensions: ["*"] }] });
    if (dest) { const { writeTextFile } = await import("@tauri-apps/plugin-fs"); await writeTextFile(dest, configContent.value); showToast("配置已保存到本地"); }
  } catch { showToast("保存失败", "error"); }
}
async function handleModifyConfig() {
  if (!selectedDevice.value || !configModKey.value.trim() || !configModValue.value.trim()) return;
  try {
    const cmd = `sed -i 's/^${configModKey.value}=.*/${configModKey.value}=${configModValue.value}/' ${configModPath.value} || echo "${configModKey.value}=${configModValue.value}" >> ${configModPath.value}`;
    await shell(selectedDevice.value.serial, cmd);
    showToast(`配置已修改: ${configModKey.value}=${configModValue.value}`);
    configModKey.value = "";
    configModValue.value = "";
    configDialogOpen.value = false;
  } catch (e: any) { showToast(`修改配置失败: ${e}`, "error"); }
}

// ── Screen Mirror ──
function toggleMirror() {
  if (isMirroring.value) { stopMirror(); }
  else { startMirror(); }
}
function startMirror() {
  if (!selectedDevice.value) return;
  isMirroring.value = true;
  mirrorFrameCount.value = 0;
  currentMirrorFps.value = 0;
  scheduleMirrorFrame();
}
async function scheduleMirrorFrame() {
  if (!isMirroring.value || !selectedDevice.value) return;
  const startTime = performance.now();
  try {
    const result = await screenshot(selectedDevice.value.serial, "");
    const dataUrl = result.startsWith("data:") ? result : `data:image/png;base64,${result}`;
    const canvas = mirrorCanvas.value;
    if (canvas) {
      const img = new window.Image();
      await new Promise<void>((resolve) => {
        img.onload = () => {
          canvas.width = Math.min(img.width, parseInt(mirrorResolution.value));
          canvas.height = img.height * (canvas.width / img.width);
          const ctx = canvas.getContext("2d");
          if (ctx) ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
          mirrorFrameCount.value++;
          currentMirrorFps.value = 1000 / Math.max(performance.now() - startTime, 1);
          resolve();
        };
        img.onerror = () => resolve();
        img.src = dataUrl;
      });
    }
  } catch {}
  await yieldToUI();
  if (isMirroring.value) {
    const interval = Math.max(200, Math.round(1000 / mirrorFps.value));
    mirrorTimeoutId = setTimeout(scheduleMirrorFrame, interval);
  }
}
function stopMirror() {
  if (mirrorTimeoutId) { clearTimeout(mirrorTimeoutId); mirrorTimeoutId = null; }
  isMirroring.value = false;
  currentMirrorFps.value = 0;
  mirrorFrameCount.value = 0;
}

async function takeScreenshot() {
  if (!selectedDevice.value) return;
  try {
    const { save } = await import("@tauri-apps/plugin-dialog");
    const dest = await save({ defaultPath: `screenshot_${Date.now()}.png`, filters: [{ name: "PNG Image", extensions: ["png"] }] });
    if (!dest) return;
    showCmdExec("截图", "adb screencap -p");
    appendCmdExec("正在截图...");
    const result = await screenshot(selectedDevice.value.serial, dest);
    appendCmdExec(result);
    finishCmdExec("截图已保存");
    showToast("截图已保存");
  } catch (e: any) { showToast(`截图失败: ${e}`, "error"); }
}
async function takeScreenshotFromMirror() {
  await takeScreenshot();
}
async function toggleRecording() {
  if (!selectedDevice.value) return;
  if (isRecording.value) {
    try {
      showCmdExec("停止录屏", "adb shell pkill -SIGINT screenrecord");
      appendCmdExec("正在停止录屏...");
      await shell(selectedDevice.value.serial, "pkill -SIGINT screenrecord");
      await new Promise(r => setTimeout(r, 1500));
      const { save } = await import("@tauri-apps/plugin-dialog");
      const dest = await save({ defaultPath: `recording_${Date.now()}.mp4`, filters: [{ name: "MP4 Video", extensions: ["mp4"] }] });
      if (dest) {
        appendCmdExec("正在拉取录屏文件...");
        await pullFile(selectedDevice.value.serial, "/sdcard/recording.mp4", dest);
        appendCmdExec("录屏已保存到: " + dest);
        finishCmdExec("录屏已保存");
        showToast("录屏已保存");
      } else {
        cmdExec.value.show = false;
      }
    } catch (e: any) { finishCmdExec(`保存录屏失败: ${e}`); showToast(`保存录屏失败: ${e}`, "error"); }
    isRecording.value = false;
  } else {
    try {
      showCmdExec("开始录屏", "screenrecord /sdcard/recording.mp4");
      appendCmdExec("正在启动录屏...");
      await startScreenrecord(selectedDevice.value.serial, "/sdcard/recording.mp4", 1280, 720);
      isRecording.value = true;
      appendCmdExec("录屏已开始（1280x720）");
      finishCmdExec("录屏已开始");
      showToast("录屏开始");
    } catch { finishCmdExec("录屏启动失败"); showToast("录屏启动失败", "error"); }
  }
}

// ── Output Panel ──
// ── Lifecycle ──
onMounted(async () => {
  scanDevices();
  loadCustomCommands();
  loadTextHistory();
  loadRemotePathHistory();
  // Auto-refresh devices every 5s
  autoRefreshId = setInterval(scanDevices, 5000);
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
  if (mirrorTimeoutId) clearTimeout(mirrorTimeoutId);
  if (logcatTimeoutId) clearTimeout(logcatTimeoutId);
  if (diagTimeoutId) clearTimeout(diagTimeoutId);
  if (bootLogcatTimeoutId) clearTimeout(bootLogcatTimeoutId);
  if (autoRefreshId) clearInterval(autoRefreshId);
  // Note: log sessions are saved to DB; user can see "running" sessions on next visit
});
</script>
