<template>
  <div class="pt-12 flex flex-col gap-5 min-h-[calc(100vh-80px)]">
    <!-- Connection Bar -->
    <div class="glass-panel rounded-xl p-4 flex items-center gap-4">
      <span class="material-symbols-outlined text-on-surface-variant">link</span>
      <input v-model="connectAddress"
        class="flex-1 bg-transparent border-none outline-none font-body-md text-body-md text-on-surface placeholder:text-on-surface-variant/50"
        placeholder="输入 IP 地址连接设备，例如: 192.168.1.100:5555" @keyup.enter="connectToDevice" />
      <button class="glass-button px-5 py-2 rounded-full font-label-md text-label-md flex items-center gap-1" @click="connectToDevice">
        <span class="material-symbols-outlined text-[16px]">add_link</span>连接
      </button>
      <div class="h-6 w-[1px] bg-glass-border-dark"></div>
      <div class="flex gap-2 flex-wrap items-center">
        <button v-for="device in devices" :key="device.serial"
          class="px-3 py-1.5 rounded-full font-caption text-caption flex items-center gap-1.5 transition-all group"
          :class="selectedDevice?.serial === device.serial ? 'glass-button glass-active' : 'glass-button'"
          @click="selectDevice(device)">
          <div class="w-2 h-2 rounded-full" :class="device.status === 'online' ? 'bg-success-indicator' : 'bg-outline-variant'"></div>
          {{ device.name }}
          <span class="material-symbols-outlined text-[12px] opacity-0 group-hover:opacity-100 transition-opacity text-on-surface-variant hover:text-error ml-0.5"
            @click.stop="disconnectDeviceHandler(device.serial)">close</span>
        </button>
        <span v-if="devices.length === 0" class="font-caption text-caption text-on-surface-variant/50">无设备连接</span>
      </div>
      <button class="glass-button px-3 py-1.5 rounded-full font-caption text-caption flex items-center gap-1" @click="scanDevices">
        <span class="material-symbols-outlined text-[14px]">refresh</span>
      </button>
    </div>

    <!-- Main Content -->
    <div class="grid grid-cols-12 gap-5 flex-grow">
      <!-- Left Column -->
      <div class="col-span-12 lg:col-span-4 flex flex-col gap-5">

        <!-- Device Info -->
        <div class="glass-panel rounded-xl p-5">
          <h3 class="font-headline-md text-headline-md text-on-surface mb-4 flex items-center gap-2">
            <span class="material-symbols-outlined text-[20px]">info</span>设备信息
          </h3>
          <div v-if="deviceProps" class="space-y-2">
            <div v-for="(val, key) in devicePropList" :key="key" class="flex justify-between font-label-md text-label-md">
              <span class="text-on-surface-variant">{{ key }}</span>
              <span class="font-medium font-mono text-xs truncate max-w-[200px]" :title="val">{{ val }}</span>
            </div>
            <button class="glass-button w-full mt-2 py-2 rounded-lg font-label-md text-label-md flex items-center justify-center gap-1" @click="loadDeviceProperties">
              <span class="material-symbols-outlined text-[16px]">refresh</span>刷新信息
            </button>
          </div>
          <div v-else class="text-center py-6">
            <span class="material-symbols-outlined text-4xl text-on-surface-variant/30">smartphone</span>
            <p class="font-body-md text-body-md text-on-surface-variant/50 mt-2">选择设备查看信息</p>
          </div>
        </div>

        <!-- Information Query -->
        <div class="glass-panel rounded-xl p-5">
          <h3 class="font-headline-md text-headline-md text-on-surface mb-4 flex items-center gap-2">
            <span class="material-symbols-outlined text-[20px]">query_stats</span>信息查询
          </h3>
          <div class="grid grid-cols-2 gap-2">
            <button class="glass-button py-2.5 rounded-lg font-caption text-caption flex items-center justify-center gap-1"
              :disabled="!selectedDevice || infoLoading === 'basic'" @click="queryInfo('basic')">
              <span v-if="infoLoading === 'basic'" class="w-3 h-3 border-2 border-current border-t-transparent rounded-full animate-spin"></span>
              <span v-else class="material-symbols-outlined text-[16px]">info</span>
              基础信息
            </button>
            <button class="glass-button py-2.5 rounded-lg font-caption text-caption flex items-center justify-center gap-1"
              :disabled="!selectedDevice || infoLoading === 'whaleos'" @click="queryInfo('whaleos')">
              <span v-if="infoLoading === 'whaleos'" class="w-3 h-3 border-2 border-current border-t-transparent rounded-full animate-spin"></span>
              <span v-else class="material-symbols-outlined text-[16px]">tv</span>
              WhaleOS
            </button>
            <button class="glass-button py-2.5 rounded-lg font-caption text-caption flex items-center justify-center gap-1"
              :disabled="!selectedDevice || infoLoading === 'aosp'" @click="queryInfo('aosp')">
              <span v-if="infoLoading === 'aosp'" class="w-3 h-3 border-2 border-current border-t-transparent rounded-full animate-spin"></span>
              <span v-else class="material-symbols-outlined text-[16px]">developer_board</span>
              AOSP
            </button>
            <button class="glass-button py-2.5 rounded-lg font-caption text-caption flex items-center justify-center gap-1"
              :disabled="!selectedDevice || infoLoading === 'keys'" @click="queryInfo('keys')">
              <span v-if="infoLoading === 'keys'" class="w-3 h-3 border-2 border-current border-t-transparent rounded-full animate-spin"></span>
              <span v-else class="material-symbols-outlined text-[16px]">security</span>
              检查密钥
            </button>
          </div>
        </div>

        <!-- Device Control -->
        <div class="glass-panel rounded-xl p-5">
          <h3 class="font-headline-md text-headline-md text-on-surface mb-4 flex items-center gap-2">
            <span class="material-symbols-outlined text-[20px]">settings_remote</span>设备控制
          </h3>
          <div class="grid grid-cols-2 gap-2">
            <button class="glass-button py-2.5 rounded-lg font-label-md text-label-md flex items-center justify-center gap-1" @click="rebootDevice">
              <span class="material-symbols-outlined text-[16px]">restart_alt</span>重启
            </button>
            <button class="glass-button py-2.5 rounded-lg font-label-md text-label-md flex items-center justify-center gap-1" @click="rebootToRecovery">
              <span class="material-symbols-outlined text-[16px]">build</span>Recovery
            </button>
            <button class="glass-button py-2.5 rounded-lg font-label-md text-label-md flex items-center justify-center gap-1" @click="rebootToBootloader">
              <span class="material-symbols-outlined text-[16px]">developer_board</span>Bootloader
            </button>
            <button class="glass-button py-2.5 rounded-lg font-label-md text-label-md flex items-center justify-center gap-1" @click="rootDevice">
              <span class="material-symbols-outlined text-[16px]">shield</span>Root
            </button>
            <button class="glass-button py-2.5 rounded-lg font-label-md text-label-md flex items-center justify-center gap-1" @click="remountDevice">
              <span class="material-symbols-outlined text-[16px]">folder_managed</span>Remount
            </button>
            <button class="glass-button py-2.5 rounded-lg font-label-md text-label-md flex items-center justify-center gap-1" @click="restartAdbServer">
              <span class="material-symbols-outlined text-[16px]">power_settings_new</span>重启ADB
            </button>
          </div>
        </div>

        <!-- Remote Control -->
        <div class="glass-panel rounded-xl p-5">
          <h3 class="font-headline-md text-headline-md text-on-surface mb-4 flex items-center gap-2">
            <span class="material-symbols-outlined text-[20px]">gamepad</span>遥控器
          </h3>
          <div class="relative w-40 h-40 mx-auto mb-4">
            <button class="absolute top-0 left-1/2 -translate-x-1/2 w-12 h-12 glass-button rounded-full flex items-center justify-center" @click="sendKey('19')">
              <span class="material-symbols-outlined">keyboard_arrow_up</span>
            </button>
            <button class="absolute bottom-0 left-1/2 -translate-x-1/2 w-12 h-12 glass-button rounded-full flex items-center justify-center" @click="sendKey('20')">
              <span class="material-symbols-outlined">keyboard_arrow_down</span>
            </button>
            <button class="absolute left-0 top-1/2 -translate-y-1/2 w-12 h-12 glass-button rounded-full flex items-center justify-center" @click="sendKey('21')">
              <span class="material-symbols-outlined">keyboard_arrow_left</span>
            </button>
            <button class="absolute right-0 top-1/2 -translate-y-1/2 w-12 h-12 glass-button rounded-full flex items-center justify-center" @click="sendKey('22')">
              <span class="material-symbols-outlined">keyboard_arrow_right</span>
            </button>
            <button class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-14 h-14 glass-button rounded-full flex items-center justify-center bg-secondary/10" @click="sendKey('23')">
              <span class="material-symbols-outlined text-secondary">check</span>
            </button>
          </div>
          <div class="grid grid-cols-5 gap-2 mb-3">
            <button class="glass-button py-1.5 rounded-lg font-caption text-caption flex flex-col items-center gap-0.5" @click="sendKey('3')">
              <span class="material-symbols-outlined text-[16px]">home</span>Home
            </button>
            <button class="glass-button py-1.5 rounded-lg font-caption text-caption flex flex-col items-center gap-0.5" @click="sendKey('4')">
              <span class="material-symbols-outlined text-[16px]">arrow_back</span>Back
            </button>
            <button class="glass-button py-1.5 rounded-lg font-caption text-caption flex flex-col items-center gap-0.5" @click="sendKey('26')">
              <span class="material-symbols-outlined text-[16px]">power_settings_new</span>Power
            </button>
            <button class="glass-button py-1.5 rounded-lg font-caption text-caption flex flex-col items-center gap-0.5" @click="sendKey('82')">
              <span class="material-symbols-outlined text-[16px]">menu</span>Menu
            </button>
            <button class="glass-button py-1.5 rounded-lg font-caption text-caption flex flex-col items-center gap-0.5" @click="sendKey('187')">
              <span class="material-symbols-outlined text-[16px]">apps</span>最近
            </button>
          </div>
          <div class="grid grid-cols-3 gap-2 mb-3">
            <button class="glass-button py-2 rounded-lg font-caption text-caption flex items-center justify-center gap-1" @click="sendKey('24')">
              <span class="material-symbols-outlined text-[16px]">volume_up</span>Vol+
            </button>
            <button class="glass-button py-2 rounded-lg font-caption text-caption flex items-center justify-center gap-1" @click="sendKey('25')">
              <span class="material-symbols-outlined text-[16px]">volume_down</span>Vol-
            </button>
            <button class="glass-button py-2 rounded-lg font-caption text-caption flex items-center justify-center gap-1" @click="sendKey('164')">
              <span class="material-symbols-outlined text-[16px]">volume_off</span>静音
            </button>
          </div>
          <div class="grid grid-cols-5 gap-1.5">
            <button v-for="n in 9" :key="n" class="glass-button py-2 rounded-lg font-caption text-caption" @click="sendKey(String(7 + n))">{{ n }}</button>
            <button class="glass-button py-2 rounded-lg font-caption text-caption" @click="sendKey('0')">0</button>
            <button class="glass-button py-2 rounded-lg font-caption text-caption flex items-center justify-center gap-0.5" @click="sendKey('176')">
              <span class="material-symbols-outlined text-[14px]">settings</span>设置
            </button>
            <button class="glass-button py-2 rounded-lg font-caption text-caption" @click="sendKey('66')">回车</button>
            <button class="glass-button py-2 rounded-lg font-caption text-caption" @click="sendKey('67')">退格</button>
            <button class="glass-button py-2 rounded-lg font-caption text-caption" @click="sendKey('61')">Tab</button>
          </div>
        </div>

        <!-- Custom Commands -->
        <div class="glass-panel rounded-xl p-5">
          <div class="flex justify-between items-center mb-4">
            <h3 class="font-headline-md text-headline-md text-on-surface flex items-center gap-2">
              <span class="material-symbols-outlined text-[20px]">terminal</span>快捷命令
            </h3>
            <button class="glass-button p-1 rounded" @click="addCustomCommand">
              <span class="material-symbols-outlined text-[16px]">add</span>
            </button>
          </div>
          <div v-if="editingCmdIndex !== null" class="mb-3 space-y-2 p-3 bg-white/10 rounded-xl">
            <input v-model="editingCmdName" class="w-full bg-white/80 border border-outline-variant rounded-lg px-3 py-1.5 font-caption text-caption text-on-surface focus:ring-2 focus:ring-secondary/30" placeholder="命令名称" />
            <input v-model="editingCmdValue" class="w-full bg-white/80 border border-outline-variant rounded-lg px-3 py-1.5 font-caption text-caption text-on-surface font-mono focus:ring-2 focus:ring-secondary/30" placeholder="shell 命令" @keyup.enter="saveCustomCommand" />
            <div class="flex gap-2 justify-end">
              <button class="glass-button px-3 py-1 rounded-lg font-caption text-caption" @click="cancelEditCommand">取消</button>
              <button class="glass-button px-3 py-1 rounded-lg font-caption text-caption" @click="saveCustomCommand">保存</button>
            </div>
          </div>
          <div class="grid grid-cols-2 gap-1.5">
            <button v-for="(cmd, idx) in customCommands" :key="idx"
              class="glass-button py-2 px-3 rounded-lg font-caption text-caption text-left truncate group flex items-center gap-1" @click="executeCustomCommand(cmd.command)">
              <span class="material-symbols-outlined text-[14px] shrink-0">play_arrow</span>
              <span class="truncate">{{ cmd.name }}</span>
              <span class="ml-auto material-symbols-outlined text-[12px] opacity-0 group-hover:opacity-100 text-on-surface-variant hover:text-error shrink-0"
                @click.stop="removeCustomCommand(idx)">close</span>
            </button>
            <p v-if="customCommands.length === 0" class="col-span-2 font-caption text-caption text-on-surface-variant/50 text-center py-3">点击 + 添加快捷命令</p>
          </div>
        </div>
      </div>

      <!-- Right Column -->
      <div class="col-span-12 lg:col-span-8 flex flex-col gap-5">

        <!-- Text Input -->
        <div class="glass-panel rounded-xl p-5">
          <h3 class="font-headline-md text-headline-md text-on-surface mb-4 flex items-center gap-2">
            <span class="material-symbols-outlined text-[20px]">keyboard</span>文本输入
          </h3>
          <div class="flex gap-3">
            <input v-model="inputTextValue"
              class="flex-1 bg-white border border-outline-variant rounded-lg px-4 py-2.5 font-body-md text-body-md text-on-surface focus:ring-2 focus:ring-secondary/30 focus:border-secondary transition-all"
              placeholder="输入要发送到设备的文本..." @keyup.enter="sendText" />
            <button class="glass-button px-5 py-2.5 rounded-lg font-label-md text-label-md" @click="sendText" :disabled="!inputTextValue.trim()">发送文本</button>
          </div>
        </div>

        <!-- APK Install -->
        <div class="glass-panel rounded-xl p-5">
          <h3 class="font-headline-md text-headline-md text-on-surface mb-4 flex items-center gap-2">
            <span class="material-symbols-outlined text-[20px]">package</span>APK 安装
          </h3>
          <div class="flex gap-3 items-center">
            <button class="glass-button px-5 py-2.5 rounded-lg font-label-md text-label-md flex items-center gap-2" @click="installApkFile">
              <span class="material-symbols-outlined text-[16px]">upload</span>安装 APK
            </button>
            <label class="flex items-center gap-1.5 font-caption text-cursor-pointer cursor-pointer px-3 py-2 rounded-lg glass-hover transition-all"
              :class="reinstallApk ? 'bg-secondary/10 border border-secondary/30' : ''">
              <span class="material-symbols-outlined text-[18px]" :class="reinstallApk ? 'text-secondary' : 'text-on-surface-variant'">
                {{ reinstallApk ? 'check_box' : 'check_box_outline_blank' }}
              </span>
              <span class="text-on-surface font-caption" :class="reinstallApk ? 'text-secondary' : ''">覆盖安装 (-r)</span>
              <input type="checkbox" v-model="reinstallApk" class="hidden" />
            </label>
            <div class="h-6 w-[1px] bg-glass-border-dark"></div>
            <button class="glass-button px-4 py-2 rounded-lg font-caption text-caption flex items-center gap-1" @click="getCurrentForegroundApp">
              <span class="material-symbols-outlined text-[14px]">center_focus_strong</span>前台
            </button>
          </div>
          <div v-if="currentForegroundApp" class="mt-3 p-2 bg-secondary/5 rounded-lg font-caption text-caption text-secondary flex items-center gap-2">
            <span class="material-symbols-outlined text-[14px]">center_focus_strong</span>
            当前前台: {{ currentForegroundApp }}
          </div>
        </div>

        <!-- Application Management -->
        <div class="glass-panel rounded-xl p-5">
          <div class="flex justify-between items-center mb-3">
            <h3 class="font-headline-md text-headline-md text-on-surface flex items-center gap-2">
              <span class="material-symbols-outlined text-[20px]">apps</span>应用管理
            </h3>
            <div class="flex gap-2 items-center flex-wrap">
              <div class="relative">
                <span class="material-symbols-outlined absolute left-2 top-1/2 -translate-y-1/2 text-on-surface-variant text-[14px]">search</span>
                <input v-model="appSearch" class="w-36 glass-input rounded-md pl-7 pr-2 py-1 font-caption text-caption text-on-surface placeholder:text-on-surface-variant/50 focus:outline-none" placeholder="搜索..." />
              </div>
              <button class="glass-button px-3 py-1.5 rounded-full font-caption text-caption flex items-center gap-1" @click="refreshPackageList">
                <span class="material-symbols-outlined text-[14px]">refresh</span>刷新
              </button>
              <label class="flex items-center gap-1 font-caption text-caption text-on-surface-variant cursor-pointer">
                <input type="checkbox" v-model="showSystemApps" class="accent-secondary" @change="refreshPackageList" />系统应用
              </label>
            </div>
          </div>
          <div class="max-h-56 overflow-y-auto custom-scrollbar">
            <div v-if="filteredPackages.length === 0" class="text-center py-6">
              <p class="font-body-md text-body-md text-on-surface-variant/50">暂无应用，点击刷新加载</p>
            </div>
            <div v-for="pkg in filteredPackages" :key="pkg" class="flex items-center justify-between py-1.5 px-2 rounded-lg hover:bg-white/20 transition-colors border-b border-outline-variant/20 last:border-0 group">
              <span class="font-body-sm text-body-sm text-on-surface font-mono truncate max-w-[260px]">{{ pkg }}</span>
              <div class="flex gap-0.5 opacity-60 group-hover:opacity-100 transition-opacity">
                <button class="glass-button p-1 rounded" title="启动" @click="startApp(pkg)">
                  <span class="material-symbols-outlined text-[16px] text-success-indicator">play_arrow</span>
                </button>
                <button class="glass-button p-1 rounded" title="停止" @click="stopApp(pkg)">
                  <span class="material-symbols-outlined text-[16px] text-tertiary">stop</span>
                </button>
                <button class="glass-button p-1 rounded" title="版本信息" @click="fetchAppVersion(pkg)">
                  <span class="material-symbols-outlined text-[16px]">info</span>
                </button>
                <button class="glass-button p-1 rounded" title="下载APK" @click="downloadApk(pkg)">
                  <span class="material-symbols-outlined text-[16px]">download</span>
                </button>
                <button class="glass-button p-1 rounded" title="清除数据" @click="clearApp(pkg)">
                  <span class="material-symbols-outlined text-[16px] text-error">delete_sweep</span>
                </button>
                <button class="glass-button p-1 rounded" title="卸载" @click="uninstallPkg(pkg)">
                  <span class="material-symbols-outlined text-[16px] text-error">delete</span>
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Log Collection -->
        <div class="glass-panel rounded-xl p-5">
          <h3 class="font-headline-md text-headline-md text-on-surface mb-4 flex items-center gap-2">
            <span class="material-symbols-outlined text-[20px]">article</span>日志采集
          </h3>
          <div class="grid grid-cols-2 gap-3">
            <!-- Logcat -->
            <div class="glass-card rounded-xl p-4">
              <div class="flex justify-between items-center mb-2">
                <span class="font-label-md text-label-md flex items-center gap-1">
                  <span class="material-symbols-outlined text-[16px]">terminal</span>
                  实时日志
                </span>
                <span v-if="logcatRunning" class="font-caption text-caption text-secondary bg-secondary/10 px-2 py-0.5 rounded-full">{{ logcatElapsed }}s</span>
              </div>
              <button class="w-full glass-button py-2 rounded-lg font-caption text-caption flex items-center justify-center gap-1"
                :class="logcatRunning ? 'bg-error/10 text-error border border-error/20' : ''"
                @click="toggleLogcat">
                <span class="material-symbols-outlined text-[16px]">{{ logcatRunning ? 'stop' : 'play_arrow' }}</span>
                {{ logcatRunning ? '停止采集' : '开始采集' }}
              </button>
            </div>
            <!-- Diagnostic Log -->
            <div class="glass-card rounded-xl p-4">
              <div class="flex justify-between items-center mb-2">
                <span class="font-label-md text-label-md flex items-center gap-1">
                  <span class="material-symbols-outlined text-[16px]">diagnosis</span>
                  诊断日志包
                </span>
                <span v-if="diagRunning" class="font-caption text-caption text-secondary bg-secondary/10 px-2 py-0.5 rounded-full">{{ diagElapsed }}s</span>
              </div>
              <button class="w-full glass-button py-2 rounded-lg font-caption text-caption flex items-center justify-center gap-1"
                :class="diagRunning ? 'bg-error/10 text-error border border-error/20' : ''"
                @click="toggleDiagnostic">
                <span class="material-symbols-outlined text-[16px]">{{ diagRunning ? 'stop' : 'play_arrow' }}</span>
                {{ diagRunning ? '停止采集' : '采集完整诊断包' }}
              </button>
            </div>
            <!-- Boot Logcat -->
            <div class="glass-card rounded-xl p-4">
              <div class="flex justify-between items-center mb-2">
                <span class="font-label-md text-label-md flex items-center gap-1">
                  <span class="material-symbols-outlined text-[16px]">power</span>
                  开机日志
                </span>
                <span v-if="bootLogcatRunning" class="font-caption text-caption text-secondary bg-secondary/10 px-2 py-0.5 rounded-full">{{ bootLogcatElapsed }}s</span>
              </div>
              <button class="w-full glass-button py-2 rounded-lg font-caption text-caption flex items-center justify-center gap-1"
                :class="bootLogcatRunning ? 'bg-error/10 text-error border border-error/20' : ''"
                @click="toggleBootLogcat">
                <span class="material-symbols-outlined text-[16px]">{{ bootLogcatRunning ? 'stop' : 'play_arrow' }}</span>
                {{ bootLogcatRunning ? '停止采集' : '开机日志采集' }}
              </button>
            </div>
            <!-- Clear Logcat -->
            <div class="glass-card rounded-xl p-4 flex flex-col justify-center items-center">
              <button class="w-full glass-button py-2 rounded-lg font-caption text-caption flex items-center justify-center gap-1 text-error"
                @click="clearLogcatLogs">
                <span class="material-symbols-outlined text-[16px]">delete</span>
                清空设备日志
              </button>
            </div>
          </div>
        </div>

        <!-- File Browser -->
        <div class="glass-panel rounded-xl p-5">
          <h3 class="font-headline-md text-headline-md text-on-surface mb-4 flex items-center gap-2">
            <span class="material-symbols-outlined text-[20px]">folder_open</span>文件管理
          </h3>
          <div class="flex gap-2 mb-3">
            <input v-model="remotePath"
              class="flex-1 bg-white border border-outline-variant rounded-lg px-3 py-2 font-body-sm text-body-sm text-on-surface font-mono focus:ring-2 focus:ring-secondary/30 focus:border-secondary transition-all"
              placeholder="远程路径，如 /sdcard/" />
            <button class="glass-button px-4 py-2 rounded-lg font-caption text-caption flex items-center gap-1" @click="listRemoteDir">
              <span class="material-symbols-outlined text-[14px]">list</span>列出
            </button>
            <button class="glass-button px-4 py-2 rounded-lg font-caption text-caption flex items-center gap-1" @click="pushToCurrentDir">
              <span class="material-symbols-outlined text-[14px]">upload</span>上传
            </button>
            <button class="glass-button px-4 py-2 rounded-lg font-caption text-caption flex items-center gap-1" @click="pullFromCurrentDir">
              <span class="material-symbols-outlined text-[14px]">download</span>下载
            </button>
          </div>
          <div class="max-h-48 overflow-y-auto custom-scrollbar bg-[#1a1c1d]/5 rounded-xl font-mono text-[11px] leading-relaxed">
            <div class="p-3">
              <div v-if="directoryListing" class="text-on-surface-variant whitespace-pre-wrap">{{ directoryListing }}</div>
              <div v-else class="text-on-surface-variant/30 text-center py-4">输入路径后点击列出</div>
            </div>
          </div>
        </div>

        <!-- Device Config -->
        <div class="glass-panel rounded-xl p-5">
          <h3 class="font-headline-md text-headline-md text-on-surface mb-4 flex items-center gap-2">
            <span class="material-symbols-outlined text-[20px]">tune</span>设备配置
          </h3>
          <div class="flex gap-2 mb-3 flex-wrap">
            <button v-for="cfg in commonConfigs" :key="cfg.path"
              class="glass-button px-3 py-1.5 rounded-lg font-caption text-caption flex items-center gap-1" @click="fetchConfig(cfg.path)">
              <span class="material-symbols-outlined text-[14px]">file_copy</span>{{ cfg.name }}
            </button>
          </div>
          <div v-if="configContent !== null" class="space-y-2">
            <div class="flex justify-between items-center">
              <span class="font-caption text-caption text-on-surface-variant font-mono">{{ configPath }}</span>
              <div class="flex gap-1">
                <button class="glass-button px-3 py-1 rounded-lg font-caption text-caption" @click="saveConfig">保存到设备</button>
                <button class="glass-button px-3 py-1 rounded-lg font-caption text-caption" @click="saveConfigLocally">保存到本地</button>
              </div>
            </div>
            <textarea v-model="configContent"
              class="w-full h-48 bg-[#1a1c1d]/5 rounded-xl p-3 font-mono text-[11px] text-on-surface border-0 focus:ring-2 focus:ring-secondary/30 resize-y"
              spellcheck="false"></textarea>
          </div>
        </div>

        <!-- Screen Mirror -->
        <div class="glass-panel rounded-xl p-5">
          <h3 class="font-headline-md text-headline-md text-on-surface mb-4 flex items-center gap-2">
            <span class="material-symbols-outlined text-[20px]">screenshot_monitor</span>屏幕镜像
          </h3>
          <div class="flex gap-4 items-center mb-4">
            <div class="flex items-center gap-2">
              <span class="font-caption text-caption text-on-surface-variant">帧率:</span>
              <input v-model.number="mirrorFps" type="range" min="1" max="10" step="1" class="w-24 accent-secondary" />
              <span class="font-caption text-caption text-on-surface font-mono w-6">{{ mirrorFps }}</span>
            </div>
            <div class="flex items-center gap-2">
              <span class="font-caption text-caption text-on-surface-variant">分辨率:</span>
              <select v-model="mirrorResolution"
                class="bg-white/80 border border-outline-variant rounded-lg px-2 py-1 font-caption text-caption text-on-surface focus:ring-2 focus:ring-secondary/30">
                <option value="720">720p</option>
                <option value="1080">1080p</option>
                <option value="1280">1280p</option>
              </select>
            </div>
            <button class="glass-button px-5 py-2 rounded-lg font-label-md text-label-md flex items-center gap-1"
              :class="isMirroring ? 'bg-error/10 text-error border border-error/20' : ''"
              @click="toggleMirror">
              <span class="material-symbols-outlined text-[16px]">{{ isMirroring ? 'stop' : 'play_arrow' }}</span>
              {{ isMirroring ? '停止镜像' : '启动屏幕镜像' }}
            </button>
            <span v-if="isMirroring" class="font-caption text-caption text-secondary">
              {{ mirrorFrameCount }}帧 · {{ currentMirrorFps.toFixed(1) }} FPS
            </span>
          </div>
          <div class="flex items-center justify-center min-h-[300px] bg-black/5 rounded-xl overflow-hidden relative">
            <canvas v-show="isMirroring && mirrorFrameCount > 0" ref="mirrorCanvas" class="max-w-full max-h-[500px]"></canvas>
            <div v-if="!isMirroring" class="text-center">
              <span class="material-symbols-outlined text-5xl text-on-surface-variant/30">screenshot_monitor</span>
              <p class="font-body-md text-body-md text-on-surface-variant/50 mt-2">启动屏幕镜像查看设备实时画面</p>
            </div>
            <div v-if="isMirroring && mirrorFrameCount === 0" class="absolute inset-0 flex items-center justify-center bg-black/20">
              <span class="font-body-md text-body-md text-white/80">等待接收图像数据...</span>
            </div>
          </div>
          <div class="flex gap-2 mt-3">
            <button class="glass-button px-4 py-1.5 rounded-full font-caption text-caption flex items-center gap-1" @click="takeScreenshot">
              <span class="material-symbols-outlined text-[14px]">screenshot_monitor</span>截图
            </button>
            <button class="px-4 py-1.5 rounded-full font-caption text-caption flex items-center gap-1"
              :class="isRecording ? 'bg-error/10 text-error border border-error/20' : 'glass-button'"
              @click="toggleRecording">
              <span class="material-symbols-outlined text-[14px]">{{ isRecording ? 'stop' : 'videocam' }}</span>
              {{ isRecording ? '停止录屏' : '开始录屏' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Info Query Dialog -->
    <Teleport to="body">
      <Transition name="fade">
        <div v-if="infoDialog.show" class="fixed inset-0 z-50 flex items-center justify-center" @click.self="infoDialog.show = false">
          <div class="absolute inset-0 bg-black/10 backdrop-blur-sm"></div>
          <div class="glass-panel rounded-[2rem] p-6 w-full max-w-xl max-h-[80vh] relative z-10 bg-white/60 overflow-y-auto">
            <div class="flex justify-between items-center mb-4">
              <h3 class="font-headline-md text-headline-md text-on-surface font-semibold">{{ infoDialog.title }}</h3>
              <button class="glass-button p-1 rounded" @click="infoDialog.show = false">
                <span class="material-symbols-outlined text-[18px]">close</span>
              </button>
            </div>
            <div class="space-y-2">
              <div v-for="(item, idx) in infoDialog.entries" :key="idx" class="flex border-b border-outline-variant/20 py-2">
                <span class="font-label-md text-label-md text-on-surface font-medium min-w-[180px]">{{ item.key }}</span>
                <span class="font-body-sm text-body-sm text-on-surface-variant break-all">{{ item.value }}</span>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- Toast -->
    <Teleport to="body">
      <Transition name="fade">
        <div v-if="toast.show" class="fixed bottom-8 left-1/2 -translate-x-1/2 z-50 glass-panel rounded-full px-6 py-3 flex items-center gap-2 shadow-lg">
          <span class="material-symbols-outlined text-[18px]"
            :class="toast.type === 'error' ? 'text-error' : 'text-success-indicator'">{{ toast.type === 'error' ? 'error' : 'check_circle' }}</span>
          <span class="font-body-md text-body-md text-on-surface">{{ toast.message }}</span>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from "vue";
import { useAdb, type DeviceProperties } from "@/composables/useAdb";

const {
  listDevices, shell, installApk, uninstallApk, pushFile, pullFile, reboot, screenshot,
  connectDevice, disconnectDevice, rebootRecovery, rebootBootloader, rootDevice: adbRoot, remountDevice: adbRemount,
  getProperties, inputKeyevent, inputText: adbInputText, listPackages, startApp: adbStartApp, stopApp: adbStopApp,
  clearAppData, getCurrentApp, logcatClear, logcat, listDirectory, getAppInfo,
} = useAdb();

// Toast
const toast = ref({ show: false, message: "", type: "success" as "success" | "error" });
function showToast(message: string, type: "success" | "error" = "success") {
  toast.value = { show: true, message, type };
  setTimeout(() => { toast.value.show = false; }, 2500);
}

// Device state
interface DeviceItem { serial: string; name: string; status: "online" | "offline"; os: string; }
const devices = ref<DeviceItem[]>([]);
const selectedDevice = ref<DeviceItem | null>(null);
const deviceProps = ref<DeviceProperties | null>(null);
const connectAddress = ref("");

const devicePropList = computed(() => {
  if (!deviceProps.value) return {};
  return {
    "型号": deviceProps.value.model,
    "品牌": deviceProps.value.brand,
    "设备名": deviceProps.value.device,
    "产品": deviceProps.value.product,
    "Android": `Android ${deviceProps.value.android_version} (SDK ${deviceProps.value.sdk_version})`,
    "分辨率": deviceProps.value.resolution,
    "DPI": deviceProps.value.density,
    "Build": deviceProps.value.build_id,
  };
});

// Text Input
const inputTextValue = ref("");

// APK Install
const reinstallApk = ref(true);

// Apps
const packageList = ref<string[]>([]);
const showSystemApps = ref(false);
const currentForegroundApp = ref("");
const appSearch = ref("");
const filteredPackages = computed(() => {
  if (!appSearch.value.trim()) return packageList.value;
  return packageList.value.filter(p => p.toLowerCase().includes(appSearch.value.toLowerCase()));
});

// File Browser
const remotePath = ref("/sdcard/");
const directoryListing = ref("");

// Device Config
interface ConfigItem { name: string; path: string; }
const commonConfigs: ConfigItem[] = [
  { name: "build.prop", path: "/system/build.prop" },
  { name: "default.prop", path: "/default.prop" },
  { name: "vendor/build.prop", path: "/vendor/build.prop" },
];
const configContent = ref<string | null>(null);
const configPath = ref("");

// Custom Commands
interface CustomCommand { name: string; command: string; }
const customCommands = ref<CustomCommand[]>([]);
const editingCmdIndex = ref<number | null>(null);
const editingCmdName = ref("");
const editingCmdValue = ref("");

// Helper: yield to UI thread between async operations
function yieldToUI() {
  return new Promise(resolve => setTimeout(resolve, 0));
}

// Information Query
const infoLoading = ref("");
const infoDialog = ref({ show: false, title: "", entries: [] as { key: string; value: string }[] });

// Log Collection (recursive setTimeout, never setInterval)
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

// Screen Mirror (recursive setTimeout)
const isMirroring = ref(false);
const mirrorFps = ref(3);
const mirrorResolution = ref("1080");
const mirrorFrameCount = ref(0);
const currentMirrorFps = ref(0);
let mirrorTimeoutId: ReturnType<typeof setTimeout> | null = null;
const mirrorCanvas = ref<HTMLCanvasElement | null>(null);

// Screenshot & Recording
const screenshotUrl = ref("");
const isRecording = ref(false);

// Load custom commands
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

async function scanDevices() {
  try {
    const adbDevices = await listDevices();
    devices.value = adbDevices.map(d => ({
      serial: d.serial, name: d.model || d.serial,
      status: d.status === "device" ? "online" as const : "offline" as const, os: d.android_version || "Android",
    }));
    if (devices.value.length > 0 && !selectedDevice.value) selectDevice(devices.value[0]);
  } catch { showToast("扫描设备失败", "error"); }
}
function selectDevice(device: DeviceItem) {
  selectedDevice.value = device;
  deviceProps.value = null;
  loadDeviceProperties();
}
async function loadDeviceProperties() {
  if (!selectedDevice.value) return;
  try { deviceProps.value = await getProperties(selectedDevice.value.serial); }
  catch { deviceProps.value = null; }
}
async function connectToDevice() {
  if (!connectAddress.value.trim()) return;
  try {
    await connectDevice(connectAddress.value.trim());
    connectAddress.value = "";
    await scanDevices();
    showToast("设备已连接");
  } catch (e: any) { showToast(`连接失败: ${e}`, "error"); }
}
async function disconnectDeviceHandler(serial: string) {
  try {
    await disconnectDevice(serial);
    devices.value = devices.value.filter(d => d.serial !== serial);
    if (selectedDevice.value?.serial === serial) selectedDevice.value = devices.value[0] || null;
    showToast("设备已断开");
  } catch { showToast("断开失败", "error"); }
}
async function restartAdbServer() {
  try { await shell(selectedDevice.value?.serial || "", "echo restart"); showToast("ADB 服务已重启"); } catch {}
}
async function rebootDevice() {
  if (!selectedDevice.value) return;
  try { await reboot(selectedDevice.value.serial); showToast("重启命令已发送"); } catch { showToast("重启失败", "error"); }
}
async function rebootToRecovery() {
  if (!selectedDevice.value) return;
  try { await rebootRecovery(selectedDevice.value.serial); showToast("正在重启到 Recovery..."); } catch { showToast("操作失败", "error"); }
}
async function rebootToBootloader() {
  if (!selectedDevice.value) return;
  try { await rebootBootloader(selectedDevice.value.serial); showToast("正在重启到 Bootloader..."); } catch { showToast("操作失败", "error"); }
}
async function rootDevice() {
  if (!selectedDevice.value) return;
  try { const r = await adbRoot(selectedDevice.value.serial); showToast(r); } catch (e: any) { showToast(`Root 失败: ${e}`, "error"); }
}
async function remountDevice() {
  if (!selectedDevice.value) return;
  try { const r = await adbRemount(selectedDevice.value.serial); showToast(r); } catch (e: any) { showToast(`Remount 失败: ${e}`, "error"); }
}
async function sendKey(keycode: string) {
  if (!selectedDevice.value) return;
  try { await inputKeyevent(selectedDevice.value.serial, keycode); } catch {}
}
async function sendText() {
  if (!selectedDevice.value || !inputTextValue.value.trim()) return;
  try { await adbInputText(selectedDevice.value.serial, inputTextValue.value); inputTextValue.value = ""; showToast("文本已发送"); }
  catch { showToast("发送失败", "error"); }
}

// App Management
async function refreshPackageList() {
  if (!selectedDevice.value) return;
  try { packageList.value = await listPackages(selectedDevice.value.serial, !showSystemApps.value); }
  catch { showToast("加载应用列表失败", "error"); }
}
async function getCurrentForegroundApp() {
  if (!selectedDevice.value) return;
  try { currentForegroundApp.value = await getCurrentApp(selectedDevice.value.serial); }
  catch { currentForegroundApp.value = "获取失败"; }
}
async function startApp(pkg: string) {
  if (!selectedDevice.value) return;
  try { await adbStartApp(selectedDevice.value.serial, pkg); showToast(`已启动 ${pkg}`); } catch { showToast("启动失败", "error"); }
}
async function stopApp(pkg: string) {
  if (!selectedDevice.value) return;
  try { await adbStopApp(selectedDevice.value.serial, pkg); showToast(`已停止 ${pkg}`); } catch { showToast("停止失败", "error"); }
}
async function clearApp(pkg: string) {
  if (!selectedDevice.value) return;
  try { await clearAppData(selectedDevice.value.serial, pkg); showToast(`已清除 ${pkg} 数据`); } catch { showToast("清除失败", "error"); }
}
async function uninstallPkg(pkg: string) {
  if (!selectedDevice.value) return;
  try { await uninstallApk(selectedDevice.value.serial, pkg); packageList.value = packageList.value.filter(p => p !== pkg); showToast(`已卸载 ${pkg}`); }
  catch { showToast("卸载失败", "error"); }
}
async function installApkFile() {
  if (!selectedDevice.value) return;
  try {
    const { open } = await import("@tauri-apps/plugin-dialog");
    const selected = await open({ multiple: false, filters: [{ name: "APK", extensions: ["apk"] }] });
    if (selected) {
      await installApk(selectedDevice.value.serial, selected, reinstallApk.value);
      showToast("APK 安装成功");
    }
  } catch { showToast("安装失败", "error"); }
}
async function fetchAppVersion(pkg: string) {
  if (!selectedDevice.value) return;
  try {
    const info = await getAppInfo(selectedDevice.value.serial, pkg);
    const verMatch = info.match(/versionName=([^\s]+)/);
    const codeMatch = info.match(/versionCode=(\d+)/);
    const pathMatch = info.match(/path:?\s*(\S+)/);
    let msg = `版本: ${verMatch?.[1] || "N/A"} (${codeMatch?.[1] || "?"})`;
    if (pathMatch) msg += ` | 路径: ${pathMatch[1]}`;
    showToast(msg);
  } catch { showToast("获取版本失败", "error"); }
}
async function downloadApk(pkg: string) {
  if (!selectedDevice.value) return;
  try {
    const info = await getAppInfo(selectedDevice.value.serial, pkg);
    const pathMatch = info.match(/path:?\s*(\S+)/);
    if (!pathMatch) { showToast("未找到APK路径", "error"); return; }
    const { save } = await import("@tauri-apps/plugin-dialog");
    const dest = await save({ defaultPath: `${pkg}.apk`, filters: [{ name: "APK", extensions: ["apk"] }] });
    if (dest) { await pullFile(selectedDevice.value.serial, pathMatch[1], dest); showToast(`APK 已下载`); }
  } catch { showToast("下载失败", "error"); }
}

// Information Query
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
      title = "WhaleOS 固件信息";
      const tvKeys = ["ro.product.model", "ro.product.tv.rcu", "ro.product.tv.deviceType", "ro.vendor.product.version",
        "ro.vendor.zeasn.firmwareID", "persist.sys.cur_country", "persist.sys.cur_language", "ro.boot.pid", "ro.boot.mac",
        "ro.product.tv.def.country", "ro.product.tv.language.list", "ro.product.tv.country.list"];
      const results = await Promise.all(tvKeys.map(k => shell(serial, `getprop ${k}`).catch(() => "(空)")));
      entries = tvKeys.map((key, i) => ({ key, value: results[i].trim() || "(空)" }));
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
          return { key: c.name, value: success ? "✅ 通过" : `❌ 失败: ${r.substring(0, 100)}` };
        }).catch((e: any) => ({ key: c.name, value: `❌ 失败: ${e.substring(0, 100)}` }))
      ));
      entries = checkResults;
    }
    infoDialog.value = { show: true, title, entries };
  } catch { showToast("查询失败", "error"); }
  infoLoading.value = "";
}

// Log Collection (recursive setTimeout)
async function toggleLogcat() {
  if (!selectedDevice.value) return;
  if (logcatRunning.value) {
    stopLogcatCapture();
  } else {
    logcatBuffer.value = [];
    logcatRunning.value = true;
    logcatElapsed.value = 0;
    scheduleLogcatCapture();
    showToast("日志采集已开始");
  }
}
async function scheduleLogcatCapture() {
  if (!logcatRunning.value || !selectedDevice.value) return;
  logcatElapsed.value += 2;
  try {
    const raw = await logcat(selectedDevice.value.serial, "main", 200);
    logcatBuffer.value = [raw];
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
  showToast("日志采集已停止");
}

async function toggleDiagnostic() {
  if (!selectedDevice.value) return;
  if (diagRunning.value) {
    stopDiagnosticCapture();
  } else {
    diagBuffer.value = [];
    diagRunning.value = true;
    diagElapsed.value = 0;
    scheduleDiagCapture();
    showToast("诊断日志采集已开始");
  }
}
async function scheduleDiagCapture() {
  if (!diagRunning.value || !selectedDevice.value) return;
  diagElapsed.value += 2;
  try {
    const raw = await logcat(selectedDevice.value!.serial, "main", 200);
    diagBuffer.value = [raw];
  } catch {}
  await yieldToUI();
  if (diagRunning.value) {
    diagTimeoutId = setTimeout(scheduleDiagCapture, 2000);
  }
}
async function stopDiagnosticCapture() {
  if (diagTimeoutId) { clearTimeout(diagTimeoutId); diagTimeoutId = null; }
  diagRunning.value = false;
  await yieldToUI();
  try {
    const serial = selectedDevice.value!.serial;
    const lines: string[] = [];
    lines.push("===== Logcat =====");
    lines.push(diagBuffer.value.join("\n\n"));
    const infoCommands: [string, string][] = [
      ["getprop", "getprop"], ["uptime", "uptime"], ["free", "free -m"],
      ["df", "df -h"], ["dumpsys battery", "dumpsys battery"],
      ["dumpsys power", "dumpsys power"], ["dmesg", "dmesg"], ["ps", "ps"],
    ];
    // Run all info commands in parallel, yielding mid-way
    const batchSize = 3;
    for (let i = 0; i < infoCommands.length; i += batchSize) {
      const batch = infoCommands.slice(i, i + batchSize);
      const batchResults = await Promise.all(batch.map(([label, cmd]) =>
        shell(serial, cmd).then(r => `\n===== ${label} =====\n${r}`).catch(() => `\n===== ${label} =====\n(命令执行失败)`)
      ));
      lines.push(...batchResults);
      await yieldToUI();
    }
    const { save } = await import("@tauri-apps/plugin-dialog");
    const dest = await save({ defaultPath: `diagnostic_${Date.now()}.txt`, filters: [{ name: "Text", extensions: ["txt"] }] });
    if (dest) {
      const { writeTextFile } = await import("@tauri-apps/plugin-fs");
      await writeTextFile(dest, lines.join("\n"));
    }
  } catch {}
  diagBuffer.value = [];
  showToast("诊断日志采集已停止");
}

async function toggleBootLogcat() {
  if (!selectedDevice.value) return;
  if (bootLogcatRunning.value) {
    stopBootLogcatCapture();
  } else {
    bootLogcatBuffer.value = [];
    bootLogcatRunning.value = true;
    bootLogcatElapsed.value = 0;
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
  try {
    const adbDevices = await listDevices();
    const reconnected = adbDevices.find(d => d.status === "device");
    if (reconnected) {
      bootLogcatBuffer.value.push(`[设备重新连接: ${reconnected.serial}]`);
      const raw = await logcat(reconnected.serial, "all", 500);
      bootLogcatBuffer.value.push(raw);
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
  showToast("开机日志采集已停止");
}

async function clearLogcatLogs() {
  if (!selectedDevice.value) return;
  try { await logcatClear(selectedDevice.value.serial); showToast("设备日志已清空"); }
  catch { showToast("清空失败", "error"); }
}

// File Browser
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

// Device Config
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

// Screen Mirror (recursive setTimeout)
function toggleMirror() {
  if (isMirroring.value) {
    stopMirror();
  } else {
    startMirror();
  }
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
          const elapsed = performance.now() - startTime;
          currentMirrorFps.value = 1000 / Math.max(elapsed, 1);
          resolve();
        };
        img.onerror = () => resolve();
        img.src = dataUrl;
      });
    }
  } catch {}
  // Yield to UI, then schedule next frame
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
}

async function takeScreenshot() {
  if (!selectedDevice.value) return;
  screenshotUrl.value = "";
  try {
    const result = await screenshot(selectedDevice.value.serial, "");
    screenshotUrl.value = result.startsWith("data:") ? result : `data:image/png;base64,${result}`;
  } catch { showToast("截图失败", "error"); }
}
function toggleRecording() {
  if (!selectedDevice.value) return;
  isRecording.value = !isRecording.value;
  if (isRecording.value) {
    shell(selectedDevice.value.serial, "screenrecord --size 1280x720 /sdcard/recording.mp4").catch(() => {});
    showToast("录屏开始");
  } else {
    shell(selectedDevice.value.serial, "pkill -SIGINT screenrecord").catch(() => {});
    showToast("录屏已停止");
  }
}

onMounted(() => { scanDevices(); loadCustomCommands(); });
onUnmounted(() => {
  if (mirrorTimeoutId) clearTimeout(mirrorTimeoutId);
  if (logcatTimeoutId) clearTimeout(logcatTimeoutId);
  if (diagTimeoutId) clearTimeout(diagTimeoutId);
  if (bootLogcatTimeoutId) clearTimeout(bootLogcatTimeoutId);
});
</script>
