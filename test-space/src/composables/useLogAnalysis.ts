import { ref, onUnmounted, type Ref } from 'vue'
import { invoke } from '@tauri-apps/api/core'

export type ModuleStatus = 'ok' | 'error' | 'warning' | 'info' | 'unknown'

export interface LogEvent {
  id: number
  time: string
  moduleKey: string
  moduleName: string
  status: ModuleStatus
  summary: string
  raw: string
}

export interface ModuleState {
  key: string
  name: string
  icon: string
  status: ModuleStatus
  summary: string
  lastUpdated: string
  eventCount: number
  apiCount: number
}

export interface ApiParam {
  key: string
  value: string
}

export interface ApiRequest {
  id: number
  time: string
  method: string
  url: string
  domain: string
  path: string
  queryParams: ApiParam[]
  requestHeaders: ApiParam[]
  requestBody: string
  responseStatus: number | null
  responseHeaders: ApiParam[]
  responseBody: string
  durationMs: string
  raw: string
  moduleKey: string
  moduleName: string
}

interface PatternRule {
  regex: RegExp
  status: ModuleStatus
  summary: string | ((m: RegExpMatchArray) => string)
}

interface ModuleDef {
  name: string
  icon: string
  patterns: PatternRule[]
}

export const MODULE_ORDER = [
  'boot', 'ad', 'ota', 'tou', 'analytics',
  'alexa', 'screensaver', 'network',
  'account', 'appInstall', 'player',
]

// 域名 → 模块映射（只匹配核心域名，不依赖 acc-/dev-/prod- 等环境前缀）
const DOMAIN_MODULE_MAP: Array<{ pattern: RegExp; moduleKey: string }> = [
  { pattern: /tou\.zeasn\.tv|\/tou\/device/, moduleKey: 'tou' },
  // auth-api 和账号相关路径优先匹配，避免被下面的 saas 规则吞掉
  { pattern: /saas\.zeasn\.tv.*\/auth[-_]api|saas\.zeasn\.tv.*\/auth\/|saas\.zeasn\.tv.*\/device/, moduleKey: 'account' },
  { pattern: /saas\.zeasn\.tv|log\.saas\.|saas.*\/log\//, moduleKey: 'analytics' },
  { pattern: /smarttv\.zeasn\.tv|BluePortServlets/, moduleKey: 'remoteConfig' },
  { pattern: /recommend\.zeasn\.tv/, moduleKey: 'recommend' },
  { pattern: /whalelive\.zeasn\.tv|whalelive\./, moduleKey: 'player' },
  { pattern: /deviceportal\.zeasn\.tv|\/direct\/|\/accdirect\//, moduleKey: 'account' },
  { pattern: /bd\.zeasn\.tv/, moduleKey: 'account' },
  { pattern: /\bad\.zeasn\.tv|vast\.zeasn|\/vast\//, moduleKey: 'ad' },
  { pattern: /ota\.zeasn\.tv|upgrade\.zeasn\.tv|firmware\.zeasn|\/upgrade\/|\/ota\//, moduleKey: 'ota' },
  { pattern: /banner\.zeasn\.tv|\/banner\//, moduleKey: 'banner' },
]

function detectModuleFromUrl(url: string): { moduleKey: string; moduleName: string } {
  for (const { pattern, moduleKey } of DOMAIN_MODULE_MAP) {
    if (pattern.test(url)) {
      const def = MODULE_DEFS[moduleKey]
      return { moduleKey, moduleName: def?.name || moduleKey }
    }
  }
  return { moduleKey: '', moduleName: '' }
}

const MODULE_DEFS: Record<string, ModuleDef> = {
  boot: {
    name: '开机流程',
    icon: 'power_settings_new',
    patterns: [
      { regex: /android\.intent\.action\.BOOT_COMPLETED/, status: 'ok', summary: '系统开机广播已收到' },
      { regex: /BootReceiver.*onReceive/, status: 'info', summary: '开机广播接收器触发' },
      { regex: /SYS_LAUNCHER_BOOT_FIRST_FRAME_COMPLETE/, status: 'ok', summary: 'Launcher 首帧渲染完成' },
      { regex: /recordBootTime.*cost[=:\s]+(\d+)/i, status: 'info', summary: m => `开机耗时: ${m[1]} ms` },
      { regex: /recordBootTime/i, status: 'info', summary: '开机时间已记录' },
      { regex: /initDataAfterFirstFrame/, status: 'info', summary: '首帧后数据初始化' },
      { regex: /bootComplete\b|boot_complete\b/i, status: 'ok', summary: '开机流程完成' },
      { regex: /boot\s*animation.*finish/i, status: 'ok', summary: '开机动画结束' },
      { regex: /LauncherActivity.*onCreate/, status: 'info', summary: 'Launcher 主界面已创建' },
      { regex: /launcherReady\b|homeReady\b|appReady\b/i, status: 'ok', summary: '首页已就绪' },
      { regex: /initComplete.*cost[=:\s]+(\d+)/i, status: 'info', summary: m => `初始化完成，耗时 ${m[1]} ms` },
      { regex: /firstFrame.*cost[=:\s]+(\d+)/i, status: 'info', summary: m => `首帧耗时 ${m[1]} ms` },
      { regex: /WhaleTvApplication.*onCreate/i, status: 'info', summary: 'WhaleTv Application 已创建' },
      { regex: /LauncherApplication.*onCreate/i, status: 'info', summary: 'Launcher Application 已创建' },
      { regex: /HomeActivity.*onCreate/i, status: 'info', summary: 'HomeActivity 已创建' },
      { regex: /SystemBoot.*complete/i, status: 'ok', summary: '系统启动完成' },
      { regex: /startup.*task.*complete/i, status: 'ok', summary: '启动任务全部完成' },
      { regex: /ActivityManager.*Displayed com\.(?:zeasn|whaletv)[^\s]*[:\s]+\+(\d+s\d+ms|\d+ms)/i, status: 'ok', summary: m => `Launcher 启动耗时: ${m[1]}` },
      { regex: /ActivityManager.*Displayed com\.(?:zeasn|whaletv)/i, status: 'ok', summary: 'ActivityManager: Launcher 已显示' },
    ],
  },
  ad: {
    name: '广告 SDK',
    icon: 'ad_units',
    patterns: [
      // SDK 加载步骤（宽松匹配，覆盖"ad sdk加载步骤"各种格式）
      { regex: /ad\s*sdk.*加载步骤[：:\s]*(.{0,100})/i, status: 'info', summary: m => `Ad SDK 加载步骤: ${m[1]?.trim().substring(0, 80) || ''}` },
      { regex: /加载步骤.*ad\s*sdk/i, status: 'info', summary: '广告 SDK 加载步骤' },
      { regex: /loadAdStep[=:\s]+(.+)/i, status: 'info', summary: m => `Ad SDK 加载步骤: ${m[1]?.trim().substring(0, 80)}` },
      { regex: /AdLoadStep[=:\s]+(.+)/i, status: 'info', summary: m => `Ad SDK 加载步骤: ${m[1]?.trim().substring(0, 80)}` },
      { regex: /adStep[=:\s]+(.+)/i, status: 'info', summary: m => `广告加载阶段: ${m[1]?.trim().substring(0, 60)}` },
      // SDK 初始化
      { regex: /ZeasnAdSDK initialized/, status: 'ok', summary: 'Ad SDK 初始化成功' },
      { regex: /ZeasnAdSDK\.init\s+error[:\s]+(.+)/, status: 'error', summary: m => `Ad SDK 初始化失败: ${m[1]?.trim()}` },
      { regex: /ZeasnAdSDK\.init\s+msg[:\s]+(.+)/, status: 'info', summary: m => `Ad SDK 消息: ${m[1]?.trim()}` },
      { regex: /adsdkversion\s*=\s*([^\s\n]+)/i, status: 'info', summary: m => `Ad SDK 版本: ${m[1]?.trim()}` },
      // 生命周期
      { regex: /onAdPrepared\b|onAdReady\b/i, status: 'info', summary: '广告资源已就绪' },
      { regex: /onAdStart(?:ed)?\b/i, status: 'ok', summary: '广告开始播放' },
      { regex: /onAdShown?\b|onAdImpression\b/i, status: 'ok', summary: '广告已展示（计曝光）' },
      { regex: /=====>>>onAdLoaded/, status: 'ok', summary: '广告加载成功' },
      { regex: /onAdLoaded\b/i, status: 'ok', summary: '广告加载完成' },
      { regex: /onAdLoadFailed\b/i, status: 'error', summary: '广告加载失败' },
      { regex: /onAdFinished?\b|onAdCompleted?\b/i, status: 'ok', summary: '广告播放完毕' },
      { regex: /onAdClosed?\b|onAdDismissed?\b/i, status: 'info', summary: '广告已关闭' },
      { regex: /onAdClicked?\b|clickAd\b|adClick\b/i, status: 'info', summary: '用户点击广告' },
      { regex: /onAdSkipped?\b/i, status: 'info', summary: '用户跳过广告' },
      { regex: /onAdBuffering?\b/i, status: 'info', summary: '广告缓冲中' },
      { regex: /onAdError[:\s]+(.+)/i, status: 'error', summary: m => `广告播放错误: ${m[1]?.trim().substring(0, 60)}` },
      { regex: /onAdBilling\b/i, status: 'info', summary: '广告计费事件' },
      { regex: /onAdReward\b/i, status: 'ok', summary: '广告奖励已发放' },
      // 请求/加载
      { regex: /adInitBean is null/, status: 'error', summary: '广告初始化失败: adInitBean 为空' },
      { regex: /adInitBean no null/i, status: 'info', summary: '广告数据就绪，开始加载' },
      { regex: /loadAdTask signOn/, status: 'info', summary: '广告加载任务触发' },
      { regex: /AdError \[errorType:\s*([^\]]+)/, status: 'error', summary: m => `广告错误: ${m[1]?.trim()}` },
      { regex: /=====>>>loadDiscoveryAd.*no null/, status: 'info', summary: '发现页广告开始加载' },
      { regex: /adType[=:\s]+(\w+)/i, status: 'info', summary: m => `广告类型: ${m[1]?.trim()}` },
      { regex: /adPosition[=:\s]+(\w+)/i, status: 'info', summary: m => `广告位: ${m[1]?.trim()}` },
      { regex: /adDuration[=:\s]+(\d+)/i, status: 'info', summary: m => `广告时长: ${m[1]} s` },
      { regex: /isLimitAdTracking(?:Enabled)?[=:\s]*(true|false)/i, status: 'info', summary: m => `限制广告追踪(LAT): ${m[1] === 'true' ? '已开启（广告受限）' : '未开启'}` },
      { regex: /limitAdTracking[=:\s]*(true|false)/i, status: 'info', summary: m => `LAT 开关: ${m[1] === 'true' ? '已开启（广告受限）' : '未开启'}` },
      { regex: /LimitAdTracking[=:\s]*(true|false)/i, status: 'info', summary: m => `LAT 状态: ${m[1] === 'true' ? '已开启（广告受限）' : '未开启'}` },
      { regex: /AdvertisingId[=:\s]+([^\s,}\n]{4,})/i, status: 'info', summary: m => `广告 ID: ${m[1]?.trim().substring(0, 40)}` },
      { regex: /getAdvertisingId.*fail|AdvertisingId.*error/i, status: 'error', summary: '获取广告 ID 失败' },
      { regex: /adId[=:\s]+([^\s,}\n]{3,40})/i, status: 'info', summary: m => `广告 ID: ${m[1]?.trim()}` },
      { regex: /vastAd\b|VastCreativeType/i, status: 'info', summary: 'VAST 广告事件' },
      { regex: /WhaleOSADpClient.*cpuSerial\s*==\s*(.+)/i, status: 'info', summary: m => `广告 cpuSerial: ${m[1]?.trim()}` },
      { regex: /loadAd after release/i, status: 'warning', summary: '广告资源释放后再次加载' },
    ],
  },
  ota: {
    name: 'OTA / 静默安装',
    icon: 'system_update',
    patterns: [
      { regex: /upgrade.*check.*start/i, status: 'info', summary: '开始检查升级' },
      { regex: /upgrade.*no.*update|no.*new.*version/i, status: 'ok', summary: '已是最新版本，无需升级' },
      { regex: /found\.\s*Local version is\s+(\S+)\s+and remote version is\s+(\S+)/i, status: 'info', summary: m => `版本对比: 本地 ${m[1]} → 远端 ${m[2]}` },
      { regex: /newVersionName[=:]\s*([^\s\n]+)/, status: 'info', summary: m => `检测到新版本: ${m[1]?.trim()}` },
      { regex: /newVersionCode[=:]\s*([^\s\n]+)/, status: 'info', summary: m => `新版本号: ${m[1]?.trim()}` },
      { regex: /oldVersion[=:]\s*([^\s\n]+)/i, status: 'info', summary: m => `当前版本: ${m[1]?.trim()}` },
      { regex: /DOWNLOAD_FAIL_INSUFFICIENT_SPACE/i, status: 'error', summary: 'OTA 下载失败: 存储空间不足' },
      { regex: /filter pkg=\s*(.+)/i, status: 'info', summary: m => `升级包筛选: ${m[1]?.trim()}` },
      { regex: /upgradeUrl[=:\s]*(https?:\/\/\S+)/i, status: 'info', summary: m => `升级包地址: ${m[1]?.trim()}` },
      { regex: /apkSize[=:\s]+(\d+)/i, status: 'info', summary: m => `升级包大小: ${Math.round(Number(m[1]) / 1024 / 1024 * 100) / 100} MB` },
      { regex: /apkMd5[=:\s]+([a-fA-F0-9]{16,})/i, status: 'info', summary: m => `升级包 MD5: ${m[1]?.trim()}` },
      { regex: /forceUpgrade[=:\s]*(true|false)/i, status: 'info', summary: m => `强制升级: ${m[1] === 'true' ? '是' : '否'}` },
      { regex: /upgrade:download onSuccess/, status: 'ok', summary: 'OTA 包下载完成' },
      { regex: /upgrade:download failed,\s*reason[:\s]*(.+)/, status: 'error', summary: m => `OTA 下载失败: ${m[1]?.trim()}` },
      { regex: /Silent:startUpgradeFileDownload:completed/, status: 'ok', summary: '静默升级文件下载完成' },
      { regex: /Silent:startUpgradeFileDownload:progress[:\s]*(.+)/, status: 'info', summary: m => `下载进度: ${m[1]?.trim()}` },
      { regex: /Silent:startUpgradeFileDownload:error[:\s]*(.*)/, status: 'error', summary: m => `静默升级下载错误${m[1] ? ': ' + m[1].trim() : ''}` },
      { regex: /Silent:startUpgradeFileDownload:paused/, status: 'warning', summary: '下载已暂停' },
      { regex: /silentInstall.*onInstallSuccess/, status: 'ok', summary: '静默安装成功' },
      { regex: /silentInstall.*onInstallFailed.*errorCode\s*=\s*(.+)/, status: 'error', summary: m => `静默安装失败，错误码: ${m[1]?.trim()}` },
      { regex: /notifyViewsRefresh:\s*INSTALL_FINISH/, status: 'ok', summary: '应用安装完成' },
      { regex: /notifyViewsRefresh:\s*INSTALL_FAILED/, status: 'error', summary: '应用安装失败' },
      { regex: /checkUpgrade:isInstallFailMaxCount/i, status: 'warning', summary: '已达最大安装失败次数' },
      { regex: /upgrade:DownloadResumeHelper network restored/, status: 'ok', summary: 'OTA 断点续传恢复' },
    ],
  },
  tou: {
    name: 'TOU 用户协议',
    icon: 'gavel',
    patterns: [
      // 精确方法名（APK 反编译确认）
      { regex: /maybeShowUserAgreement:\s*already accepted/i, status: 'ok', summary: 'TOU 协议已被接受，无需再次展示' },
      { regex: /maybeShowUserAgreement:\s*not accepted yet/i, status: 'warning', summary: 'TOU 协议未接受，将展示协议' },
      { regex: /maybeShowUserAgreement/i, status: 'info', summary: 'TOU 协议展示检查触发' },
      { regex: /setUserAgreementAccepted:\s*write result=\s*(.+)/i, status: 'ok', summary: m => `TOU 接受状态已写入: ${m[1]?.trim()}` },
      { regex: /setUserAgreementAccepted/i, status: 'info', summary: 'TOU 接受状态写入操作' },
      { regex: /preInitCmpForUserAgreement:\s*no network/i, status: 'error', summary: 'TOU 初始化失败: 无网络' },
      { regex: /preInitCmpForUserAgreement/i, status: 'info', summary: 'TOU CMP 预初始化' },
      // 请求/更新流程
      { regex: /initObserve:\s*requestTouUpdate start/, status: 'info', summary: 'TOU 协议检查已触发' },
      { regex: /fetchFuture:\s*requestTouUpdate cost=\s*(.+)/, status: 'ok', summary: m => `TOU 更新请求完成，耗时: ${m[1]?.trim()}` },
      { regex: /fetchFuture:\s*requestTouData cost=\s*(.+)/, status: 'ok', summary: m => `TOU 数据请求完成，耗时: ${m[1]?.trim()}` },
      { regex: /fetchFuture:.*requestTou.*empty.*fallback to cache\/asset/, status: 'warning', summary: 'TOU 服务端返回空，已回退至缓存' },
      { regex: /checkTouUpdate.*updateInfo\.data isnull/, status: 'error', summary: 'TOU 更新数据为空' },
      // 状态变更
      { regex: /---\s*TOU state=\s*(.+)/, status: 'info', summary: m => `TOU 状态变更: ${m[1]?.trim()}` },
      { regex: /---TOUItem:(.+)/, status: 'info', summary: m => `TOU 协议条目: ${m[1]?.trim().substring(0, 80)}` },
      { regex: /TouHttpMethods.*langcode[:\s]*(.+)/, status: 'info', summary: m => `TOU 请求语言: ${m[1]?.trim()}` },
      { regex: /touVersion[=:\s]+([^\s\n]+)/i, status: 'info', summary: m => `TOU 版本: ${m[1]?.trim()}` },
      { regex: /TouUpdateFetch.*start/i, status: 'info', summary: 'TOU 更新检查开始' },
      { regex: /TouUpdateFetch.*complete/i, status: 'ok', summary: 'TOU 更新检查完成' },
      // TAG 级别宽松匹配（TAG 中含 Tou 的行）
      { regex: /[/\s]Tou[A-Za-z]*[/:\s].*(?:init|start|check|show|accept|dialog)/i, status: 'info', summary: 'TOU 模块操作' },
      { regex: /UserAgreement.*(?:show|accept|decline|check|init)/i, status: 'info', summary: '用户协议操作' },
      { regex: /acc-tou\.zeasn\.tv|dev-tou\.zeasn\.tv/i, status: 'info', summary: 'TOU 服务端接口请求' },
    ],
  },
  analytics: {
    name: '埋点上报',
    icon: 'analytics',
    // 所有规则必须含精确 TAG 前缀，避免误命中系统日志
    patterns: [
      // Zeasn_db — 本地写入
      { regex: /Zeasn_db[^:]*:\s*(insert|save|write)/i, status: 'info', summary: '埋点数据写入本地数据库' },
      { regex: /Zeasn_db[^:]*:.*event[=:\s]+([^\n]{3,60})/i, status: 'info', summary: m => `埋点入库: ${m[1]?.trim().substring(0, 60)}` },
      { regex: /Zeasn_db[^:]*:.*count[=:\s]+(\d+)/i, status: 'info', summary: m => `本地埋点数据库 ${m[1]} 条` },
      { regex: /Zeasn_db[^:]*:.*delete.*(\d+)/i, status: 'info', summary: m => `本地埋点已清理 ${m[1]} 条` },
      // Zeasn_http — 网络上报
      { regex: /Zeasn_http[^:]*:.*(send|upload|report)/i, status: 'ok', summary: '埋点数据 HTTP 上报中' },
      { regex: /Zeasn_http[^:]*:.*(success|200)/i, status: 'ok', summary: '埋点 HTTP 上报成功' },
      { regex: /Zeasn_http[^:]*:.*url[=:\s]+(https?:\/\/\S+)/i, status: 'info', summary: m => `埋点上报地址: ${m[1]?.trim()}` },
      { regex: /Zeasn_http[^:]*:.*count[=:\s]+(\d+)/i, status: 'info', summary: m => `本次上报 ${m[1]} 条` },
      // ZeasnTrackerSdk
      { regex: /ZeasnTrackerSdk[^:]*:.*init/i, status: 'ok', summary: 'ZeasnTracker SDK 初始化成功' },
      { regex: /ZeasnTrackerSdk[^:]*:.*version[=:\s]+([^\s\n]+)/i, status: 'info', summary: m => `Tracker SDK 版本: ${m[1]?.trim()}` },
      // TrackConfig
      { regex: /TrackConfig[^:]*:.*userId[:\s=]+([^\s,}\n]+)/, status: 'info', summary: m => `埋点 userId: ${m[1]?.trim().substring(0, 40)}` },
      { regex: /TrackConfig[^:]*:.*ZeasnSN[:\s=]+([^\s,}\n]+)/i, status: 'info', summary: m => `ZeasnSN: ${m[1]?.trim().substring(0, 40)}` },
      { regex: /TrackConfig[^:]*:.*deviceSN[:\s=]+([^\s,}\n]+)/i, status: 'info', summary: m => `设备 SN: ${m[1]?.trim().substring(0, 40)}` },
      { regex: /TrackConfig[^:]*:.*firmwareVersion[:\s=]+([^\s,}\n]+)/i, status: 'info', summary: m => `固件版本: ${m[1]?.trim()}` },
      { regex: /TrackConfig[^:]*:.*deviceType[:\s=]+([^\s,}\n]+)/i, status: 'info', summary: m => `设备类型: ${m[1]?.trim()}` },
      { regex: /TrackConfig[^:]*:.*model[:\s=]+([^\s,}\n]+)/i, status: 'info', summary: m => `设备型号: ${m[1]?.trim()}` },
      // 通用（仍需含特定前缀词）
      { regex: /\binitTrackConfig\b/i, status: 'info', summary: '埋点配置开始初始化' },
      { regex: /\bapplyTrackConfig\b/i, status: 'ok', summary: '埋点配置已应用' },
      { regex: /acc-saas\.zeasn\.tv/i, status: 'info', summary: '埋点上报请求（acc-saas）' },
      { regex: /log\.saas\.zeasn\.tv/i, status: 'info', summary: '埋点上报请求（log.saas）' },
      { regex: /batch.*event.*count[=:\s]+(\d+)/i, status: 'info', summary: m => `批量上报事件 ${m[1]} 条` },
      { regex: /flush.*event.*queue/i, status: 'info', summary: '埋点事件队列刷新' },
    ],
  },
  banner: {
    name: 'Banner 展示',
    icon: 'view_carousel',
    patterns: [
      { regex: /SDK initialized with Banner data/i, status: 'ok', summary: 'SDK 已初始化 Banner 数据' },
      { regex: /Banner data fetch api success\s*:\s*(.*)/, status: 'ok', summary: m => `Banner 数据拉取成功${m[1] ? ': ' + m[1].trim() : ''}` },
      { regex: /Banner data fetch api failed\s*:\s*(.*)/, status: 'error', summary: m => `Banner 数据拉取失败: ${m[1]?.trim()}` },
      { regex: /Time taken for Banner data fetch:\s*(.+)/, status: 'info', summary: m => `Banner 加载耗时: ${m[1]?.trim()}` },
      { regex: /Banner data retrieved/i, status: 'ok', summary: 'Banner 数据已取回' },
      { regex: /filterMenuAppData\s+bannerList.*size[=:\s]*(\d+)/i, status: 'info', summary: m => `主页 Banner 列表 ${m[1]} 条` },
      { regex: /filterMenuAppData\s+bannerList/, status: 'info', summary: '主页 Banner 列表已过滤' },
      { regex: /filterWaterFullData\s+bannerList.*size[=:\s]*(\d+)/i, status: 'info', summary: m => `瀑布流 Banner ${m[1]} 条` },
      { regex: /filterWaterFullData\s+bannerList/, status: 'info', summary: '瀑布流 Banner 数据已过滤' },
      { regex: /filterHotelBannerData.*size[=:\s]*(\d+)/i, status: 'info', summary: m => `Hotel Banner ${m[1]} 条` },
      { regex: /filterHotelBannerData/i, status: 'info', summary: 'Hotel Banner 数据已过滤' },
      { regex: /filterRecommendData\s+bannerList.*size[=:\s]*(\d+)/i, status: 'info', summary: m => `推荐 Banner ${m[1]} 条` },
      { regex: /bannerList.*size[=:\s]*(\d+)/i, status: 'info', summary: m => `Banner 列表 ${m[1]} 条` },
      { regex: /bannerCount[=:\s]+(\d+)/i, status: 'info', summary: m => `Banner 数量: ${m[1]}` },
      { regex: /bannerType[=:\s]+(\w+)/i, status: 'info', summary: m => `Banner 类型: ${m[1]?.trim()}` },
      { regex: /bannerUrl[=:\s]+(https?:\/\/\S+)/i, status: 'info', summary: m => `Banner URL: ${m[1]?.trim().substring(0, 80)}` },
      { regex: /Banner shown status\s*:\s*(.+)/, status: 'info', summary: m => `Banner 展示状态: ${m[1]?.trim()}` },
      { regex: /Detail Banner show/, status: 'ok', summary: '详情页 Banner 已展示' },
      { regex: /TopicRequest onRespData.*banner/i, status: 'ok', summary: 'Banner Topic 响应已收到' },
      { regex: /mHomeBanner onclick.*packageName==\s*(.+)/, status: 'info', summary: m => `用户点击 Banner: ${m[1]?.trim()}` },
      { regex: /requestFocusBannerOrAd.*visibility[=:\s]*(\d+)/i, status: 'info', summary: m => `Banner 可见性: ${m[1]}` },
      { regex: /requestFocusBannerOrAd/i, status: 'info', summary: 'Banner/广告焦点请求' },
      { regex: /HomeBanner.*set.*data.*size[=:\s]*(\d+)/i, status: 'info', summary: m => `HomeBanner 数据 ${m[1]} 条` },
      { regex: /HomeBanner.*load.*fail/i, status: 'error', summary: 'HomeBanner 加载失败' },
    ],
  },
  recommend: {
    name: '推荐内容',
    icon: 'recommend',
    patterns: [
      { regex: /refreshApps size\(\)=(\d+)/i, status: 'ok', summary: m => `应用列表刷新，共 ${m[1]} 条` },
      { regex: /appsUpdateLiveData onRespData:\s*data size=(\d+)/i, status: 'ok', summary: m => `应用更新数据: ${m[1]} 条` },
      { regex: /appList.*size[=:\s]*(\d+)/i, status: 'info', summary: m => `应用列表 ${m[1]} 条` },
      { regex: /hotApp.*count[=:\s]+(\d+)/i, status: 'info', summary: m => `热门应用 ${m[1]} 条` },
      { regex: /newApp.*count[=:\s]+(\d+)/i, status: 'info', summary: m => `新应用 ${m[1]} 条` },
      { regex: /featuredApp.*count[=:\s]+(\d+)/i, status: 'info', summary: m => `精选应用 ${m[1]} 条` },
      { regex: /TopicRequest onRespData isCache[=:\s]*(true|false)/i, status: 'info', summary: m => `Topic 响应，命中缓存: ${m[1]}` },
      { regex: /TopicRequest onRespData.*size[=:\s]*(\d+)/i, status: 'ok', summary: m => `Topic 响应数据 ${m[1]} 条` },
      { regex: /TopicRequest onRespData/i, status: 'ok', summary: 'Topic 请求响应已收到' },
      { regex: /RequestLeoApi.*Topic topicId[:\s]*(.+)/i, status: 'info', summary: m => `推荐 Topic 请求: ${m[1]?.trim()}` },
      { regex: /RequestLeoApi.*responseCode[=:\s]*(\d+)/i, status: 'info', summary: m => `推荐内容响应码: ${m[1]}` },
      { regex: /RequestLeoApi.*data.*size[=:\s]*(\d+)/i, status: 'ok', summary: m => `推荐数据 ${m[1]} 条` },
      { regex: /HomeFeed.*success/i, status: 'ok', summary: '首页 Feed 加载成功' },
      { regex: /HomeFeed.*fail/i, status: 'error', summary: '首页 Feed 加载失败' },
      { regex: /HomeFeed.*size[=:\s]*(\d+)/i, status: 'info', summary: m => `首页 Feed ${m[1]} 条` },
      { regex: /contentList.*size[=:\s]+(\d+)/i, status: 'info', summary: m => `内容列表 ${m[1]} 条` },
      { regex: /filterRecommendData\s+bannerList.*size[=:\s]*(\d+)/i, status: 'info', summary: m => `推荐 Banner ${m[1]} 条` },
      { regex: /filterRecommendData\s+bannerList/, status: 'info', summary: '推荐 Banner 列表已加载' },
      { regex: /filterWaterFullData.*count[=:\s]+(\d+)/i, status: 'info', summary: m => `瀑布流数据 ${m[1]} 条` },
      { regex: /Discovery.*fetch.*complete/i, status: 'ok', summary: '发现页内容加载完成' },
      { regex: /Discovery.*size[=:\s]*(\d+)/i, status: 'info', summary: m => `发现页数据 ${m[1]} 条` },
      { regex: /Recommend.*loaded.*count[=:\s]+(\d+)/i, status: 'ok', summary: m => `推荐内容已加载，共 ${m[1]} 条` },
      { regex: /Recommend.*loaded\b/i, status: 'ok', summary: '推荐内容已加载' },
    ],
  },
  alexa: {
    name: '语音 / Alexa',
    icon: 'mic',
    patterns: [
      { regex: /alexaFlag[:\s=]*(true|false)/i, status: 'info', summary: m => `Alexa 标志: ${m[1]}` },
      { regex: /alexaFlag[:\s=]*([^\s\n]+)/, status: 'info', summary: m => `Alexa 标志: ${m[1]?.trim()}` },
      { regex: /Alexa.*config.*update/i, status: 'info', summary: 'Alexa 配置已更新' },
      { regex: /Alexa.*support.*true/i, status: 'ok', summary: '设备支持 Alexa' },
      { regex: /Alexa.*support.*false/i, status: 'warning', summary: '设备不支持 Alexa' },
      { regex: /VoiceAssist.*type[:\s=]+([^\s,}\n]+)/i, status: 'info', summary: m => `语音助手类型: ${m[1]?.trim()}` },
      { regex: /AVSManager.*init/i, status: 'info', summary: 'AVS 管理器初始化' },
      { regex: /SpeechRecognizer.*start/i, status: 'info', summary: '语音识别已启动' },
      { regex: /Alexa.*token.*refresh/i, status: 'info', summary: 'Alexa Token 刷新' },
      { regex: /Alexa.*error/i, status: 'error', summary: 'Alexa 出错' },
      { regex: /wakeWord[=:\s]+([^\s\n]+)/i, status: 'info', summary: m => `唤醒词: ${m[1]?.trim()}` },
      { regex: /voice.*assistant.*ready/i, status: 'ok', summary: '语音助手已就绪' },
    ],
  },
  screensaver: {
    name: '屏保 / 休眠',
    icon: 'dark_mode',
    patterns: [
      // 精确 TAG，避免误命中 screen/fullscreen 等词
      { regex: /DreamService.*onDreamingStarted|DreamService.*start\b/i, status: 'info', summary: '屏保已激活（DreamService）' },
      { regex: /DreamService.*onDreamingStopped|DreamService.*stop\b/i, status: 'info', summary: '屏保已退出（DreamService）' },
      { regex: /\benterDream\b/i, status: 'info', summary: '进入屏保状态' },
      { regex: /\bexitDream\b/i, status: 'info', summary: '退出屏保状态' },
      { regex: /Screensaver.*started/i, status: 'info', summary: '屏保服务已启动' },
      { regex: /Screensaver.*stopped/i, status: 'info', summary: '屏保服务已停止' },
      { regex: /Screensaver.*error/i, status: 'error', summary: '屏保服务报错' },
      { regex: /screensaverType[=:\s]+([^\s,}\n]+)/i, status: 'info', summary: m => `屏保类型: ${m[1]?.trim()}` },
      { regex: /idleTimeout[=:\s]+(\d+)/i, status: 'info', summary: m => `休眠超时: ${m[1]} ms` },
      { regex: /PowerManager.*goToSleep/i, status: 'info', summary: 'PowerManager: 进入睡眠' },
      { regex: /PowerManager.*wakeUp/i, status: 'info', summary: 'PowerManager: 从睡眠唤醒' },
      { regex: /\bdisplayOff\b/i, status: 'info', summary: '显示已关闭' },
      { regex: /\bdisplayOn\b/i, status: 'info', summary: '显示已开启' },
    ],
  },
  network: {
    name: '网络状态',
    icon: 'network_check',
    patterns: [
      { regex: /NetWorkStateReceiver Available/i, status: 'ok', summary: '网络监听: 网络可用' },
      { regex: /NetWorkStateReceiver Not Available/i, status: 'error', summary: '网络监听: 网络不可用' },
      { regex: /NetWorkStateReceiver[^:]*:.*(?:available|connected)/i, status: 'ok', summary: '网络监听: 网络可用' },
      { regex: /NetWorkStateReceiver[^:]*:.*(?:unavailable|disconnected|lost)/i, status: 'error', summary: '网络监听: 网络不可用' },
      { regex: /ConnectivityService.*(?:CONNECTED|available).*(?:WIFI|MOBILE|ETHERNET)/i, status: 'ok', summary: m => `ConnectivityService: 网络已连接` },
      { regex: /ConnectivityService.*(?:DISCONNECTED|lost).*(?:WIFI|MOBILE|ETHERNET)/i, status: 'error', summary: 'ConnectivityService: 网络已断开' },
      { regex: /NetworkConnectionInfo\{networkType=([^}]+)}/i, status: 'info', summary: m => `网络连接信息: ${m[1]?.trim()}` },
      { regex: /NetworkCallback.*onAvailable/, status: 'ok', summary: '网络回调: 连接可用' },
      { regex: /NetworkCallback.*onLost/, status: 'error', summary: '网络回调: 连接断开' },
      { regex: /network restored/i, status: 'ok', summary: '网络已恢复' },
      { regex: /networkType[=:\s]+(WIFI|MOBILE|ETHERNET|\d+)/i, status: 'info', summary: m => `网络类型: ${m[1]?.trim()}` },
      { regex: /wifiSsid[=:\s]+([^\s,}\n]+)/i, status: 'info', summary: m => `Wi-Fi SSID: ${m[1]?.trim()}` },
      { regex: /wifiRssi[=:\s]+(-?\d+)/i, status: 'info', summary: m => `Wi-Fi 信号: ${m[1]} dBm` },
      { regex: /ipAddress[=:\s]+([\d.]+)/i, status: 'info', summary: m => `IP 地址: ${m[1]}` },
      { regex: /continueDownload retry/i, status: 'info', summary: '下载重试中' },
      { regex: /continueDownload skipped/i, status: 'warning', summary: '下载已跳过' },
      { regex: /WifiManager.*connected/i, status: 'ok', summary: 'Wi-Fi 已连接' },
      { regex: /WifiManager.*disconnected/i, status: 'error', summary: 'Wi-Fi 已断开' },
      { regex: /\bdns.*fail\b|\bdns.*error\b/i, status: 'error', summary: 'DNS 解析失败' },
    ],
  },
  account: {
    name: '用户 / 账号',
    icon: 'account_circle',
    patterns: [
      // 限定在账号相关 TAG/前缀，避免命中埋点等模块的 userId 字段
      { regex: /AccountManager[^:]*:.*userId[=:\s]+([^\s,}\n]{4,})/i, status: 'info', summary: m => `AccountManager userId: ${m[1]?.trim().substring(0, 40)}` },
      { regex: /UserManager[^:]*:.*userId[=:\s]+([^\s,}\n]{4,})/i, status: 'info', summary: m => `UserManager userId: ${m[1]?.trim().substring(0, 40)}` },
      { regex: /deviceportal[^:]*:.*userId[=:\s]+([^\s,}\n]{4,})/i, status: 'info', summary: m => `DevicePortal userId: ${m[1]?.trim().substring(0, 40)}` },
      { regex: /userId.*bind\b/i, status: 'ok', summary: '用户 ID 已绑定' },
      { regex: /userId.*change\b/i, status: 'info', summary: '用户 ID 变更' },
      { regex: /AccountManager.*login.*success/i, status: 'ok', summary: '账号登录成功' },
      { regex: /AccountManager.*login.*fail/i, status: 'error', summary: '账号登录失败' },
      { regex: /user.*login.*success/i, status: 'ok', summary: '用户登录成功' },
      { regex: /user.*logout\b/i, status: 'info', summary: '用户已登出' },
      { regex: /deviceId[=:\s]+([^\s,}\n]{4,})/i, status: 'info', summary: m => `设备 ID: ${m[1]?.trim().substring(0, 40)}` },
      { regex: /deviceCode[=:\s]+([^\s,}\n]{4,})/i, status: 'info', summary: m => `设备码: ${m[1]?.trim().substring(0, 40)}` },
      { regex: /tokenExpir/i, status: 'warning', summary: 'Token 已过期' },
      { regex: /tokenRefresh.*success/i, status: 'ok', summary: 'Token 刷新成功' },
      { regex: /\bauthFail\b|\bauth.*failed\b/i, status: 'error', summary: '鉴权失败' },
      { regex: /activate.*success\b|device.*activated\b/i, status: 'ok', summary: '设备激活成功' },
      { regex: /activate.*fail\b|activation.*failed\b/i, status: 'error', summary: '设备激活失败' },
      { regex: /register.*success\b/i, status: 'ok', summary: '设备注册成功' },
    ],
  },
  appInstall: {
    name: '应用安装管理',
    icon: 'install_mobile',
    patterns: [
      { regex: /getSilentInstallObserver.*isSuccessful=true/i, status: 'ok', summary: '静默安装成功' },
      { regex: /getSilentInstallObserver.*isSuccessful=false/i, status: 'error', summary: '静默安装失败' },
      { regex: /silentInstall.*install xapk.*onInstallSuccess/i, status: 'ok', summary: 'XAPK 安装成功' },
      { regex: /silentInstall.*install xapk.*onInstallFailed.*errorCode\s*=\s*(.+)/i, status: 'error', summary: m => `XAPK 安装失败，码: ${m[1]?.trim()}` },
      { regex: /STATE_SILENT_INSTALL/i, status: 'info', summary: '静默安装状态触发' },
      { regex: /silentInstall.*packageName[=:\s]+([\w.]+)/i, status: 'info', summary: m => `静默安装包: ${m[1]?.trim()}` },
      { regex: /uninstall.*packageName[=:\s]+([\w.]+)/i, status: 'info', summary: m => `卸载包: ${m[1]?.trim()}` },
      { regex: /md5.*check.*fail/i, status: 'error', summary: 'APK MD5 校验失败' },
      { regex: /versionDowngrade.*reject/i, status: 'warning', summary: '版本降级被拒绝' },
      { regex: /PackageInstaller.*success\b/i, status: 'ok', summary: '包安装器: 安装成功' },
      { regex: /PackageInstaller.*fail\b/i, status: 'error', summary: '包安装器: 安装失败' },
      { regex: /UpgradeDownloadManager.*isSameDigit/i, status: 'info', summary: '升级包签名校验中' },
      { regex: /install.*pkg[=:\s]+([\w.]+)/i, status: 'info', summary: m => `安装包: ${m[1]?.trim()}` },
      { regex: /getSilentInstallObserver.*packageName[=:\s]+([\w.]+)/i, status: 'info', summary: m => `安装包名: ${m[1]?.trim()}` },
    ],
  },
  player: {
    name: '视频播放',
    icon: 'play_circle',
    patterns: [
      { regex: /ExoPlayer.*STATE_READY/i, status: 'ok', summary: 'ExoPlayer 已就绪' },
      { regex: /ExoPlayer.*STATE_BUFFERING/i, status: 'info', summary: 'ExoPlayer 缓冲中' },
      { regex: /ExoPlayer.*STATE_ENDED/i, status: 'info', summary: 'ExoPlayer 播放结束' },
      { regex: /ExoPlayer.*error[:\s]*(.+)/i, status: 'error', summary: m => `ExoPlayer 错误: ${m[1]?.trim().substring(0, 60)}` },
      { regex: /MediaPlayer.*error.*\((-?\d+),\s*(-?\d+)\)/i, status: 'error', summary: m => `MediaPlayer 错误 (${m[1]}, ${m[2]})` },
      { regex: /MediaPlayer.*start\b/i, status: 'ok', summary: 'MediaPlayer 开始播放' },
      { regex: /ExoPlayer.*start\b/i, status: 'ok', summary: 'ExoPlayer 开始播放' },
      { regex: /VideoView.*start\b/i, status: 'ok', summary: 'VideoView 开始播放' },
      { regex: /playUrl[=:\s]+(https?:\/\/\S+)/i, status: 'info', summary: m => `播放地址: ${m[1]?.trim().substring(0, 80)}` },
      { regex: /bufferProgress[=:\s]+(\d+)%/i, status: 'info', summary: m => `缓冲进度: ${m[1]}%` },
      { regex: /bitrate[=:\s]+(\d+)/i, status: 'info', summary: m => `码率: ${m[1]} bps` },
      { regex: /VideoPlayer.*init/i, status: 'info', summary: '视频播放器初始化' },
      { regex: /\bDRM.*ready\b|\bdrm.*success\b/i, status: 'ok', summary: 'DRM 已就绪' },
      { regex: /\bDRM.*error\b|\bdrm.*fail\b/i, status: 'error', summary: 'DRM 错误' },
      { regex: /playerType[=:\s]+([^\s\n]+)/i, status: 'info', summary: m => `播放器类型: ${m[1]?.trim()}` },
    ],
  },
  remoteConfig: {
    name: '远程配置',
    icon: 'cloud_download',
    patterns: [
      { regex: /TokenAppConfig.*success/i, status: 'ok', summary: '远程配置拉取成功' },
      { regex: /TokenAppConfig.*fail/i, status: 'error', summary: '远程配置拉取失败' },
      { regex: /TokenAppConfig.*size[:\s]*(\d+)/i, status: 'info', summary: m => `远程配置响应大小: ${m[1]} 字节` },
      { regex: /RemoteConfig.*activated/i, status: 'ok', summary: 'RemoteConfig 已激活' },
      { regex: /RemoteConfig.*fetch.*success/i, status: 'ok', summary: 'RemoteConfig 获取成功' },
      { regex: /RemoteConfig.*fetch.*fail/i, status: 'error', summary: 'RemoteConfig 获取失败' },
      { regex: /firebase.*config.*update/i, status: 'info', summary: 'Firebase 配置已更新' },
      { regex: /configVersion[=:\s]+([^\s,}\n]+)/i, status: 'info', summary: m => `配置版本: ${m[1]?.trim()}` },
      { regex: /BluePortServlets.*success/i, status: 'ok', summary: 'SmartTV 配置请求成功' },
      { regex: /BluePortServlets.*fail/i, status: 'error', summary: 'SmartTV 配置请求失败' },
      { regex: /remoteConfig.*parse.*complete/i, status: 'ok', summary: '远程配置解析完成' },
      { regex: /featureFlag[=:\s]+([^\s,}\n]+)/i, status: 'info', summary: m => `功能开关: ${m[1]?.trim()}` },
    ],
  },
  firebase: {
    name: 'Firebase 崩溃',
    icon: 'bug_report',
    patterns: [
      { regex: /Crashlytics.*initialized|CrashlyticsCore.*init/i, status: 'ok', summary: 'Crashlytics 初始化完成' },
      { regex: /Crashlytics.*crash.*report/i, status: 'error', summary: '崩溃报告已触发' },
      { regex: /FirebaseCrashlytics.*upload/i, status: 'info', summary: '崩溃报告上传中' },
      { regex: /\bNDK\s*crash\b/i, status: 'error', summary: 'NDK 崩溃已检测' },
      { regex: /FATAL EXCEPTION/i, status: 'error', summary: '致命异常发生' },
      { regex: /ANR in (.+)/i, status: 'error', summary: m => `ANR: ${m[1]?.trim().substring(0, 50)}` },
      { regex: /FirebaseApp.*initialized/i, status: 'ok', summary: 'Firebase App 已初始化' },
      { regex: /Crashlytics.*session/i, status: 'info', summary: 'Crashlytics 会话' },
      { regex: /\buncaughtException\b/i, status: 'error', summary: '未捕获异常' },
      { regex: /OutOfMemoryError/i, status: 'error', summary: 'OOM: 内存不足' },
      { regex: /StackOverflowError/i, status: 'error', summary: '栈溢出错误' },
    ],
  },
  permission: {
    name: '权限 / GDPR',
    icon: 'privacy_tip',
    patterns: [
      // 限定在 Launcher/EcoService 相关权限，避免命中 Android 系统权限日志
      { regex: /PermissionResult.*allow/i, status: 'ok', summary: '权限请求已允许' },
      { regex: /PermissionResult.*deny/i, status: 'warning', summary: '权限请求被拒绝' },
      { regex: /requestPermission[:\s]+([\w.]+)/i, status: 'info', summary: m => `请求权限: ${m[1]?.trim()}` },
      { regex: /AdConsentInfo.*status[:\s=]+([^\s,}\n]+)/i, status: 'info', summary: m => `广告隐私 Consent: ${m[1]?.trim()}` },
      { regex: /gdpr.*consent.*true/i, status: 'ok', summary: 'GDPR 用户已同意' },
      { regex: /gdpr.*consent.*false/i, status: 'warning', summary: 'GDPR 用户未同意' },
      { regex: /consent.*status[:\s=]+([^\s,}\n]+)/i, status: 'info', summary: m => `隐私 Consent 状态: ${m[1]?.trim()}` },
      { regex: /privacyPolicy.*accept\b/i, status: 'ok', summary: '用户接受隐私政策' },
      { regex: /privacyPolicy.*decline\b/i, status: 'warning', summary: '用户拒绝隐私政策' },
      // 仅当含 zeasn/whaletv 包名时才匹配权限授权，避免误命中系统权限日志
      { regex: /(?:com\.zeasn|com\.whaletv).*permission.*granted/i, status: 'ok', summary: 'Zeasn 应用权限已授权' },
      { regex: /(?:com\.zeasn|com\.whaletv).*permission.*denied/i, status: 'error', summary: 'Zeasn 应用权限被拒绝' },
    ],
  },
}

// ── HTTP 日志解析 ──

// TAG 识别正则：匹配已知 HTTP 日志 TAG
const HTTP_TAG_PATTERN = /\/(?:WhaleTvHttpLogg|NetLogInterceptor|NetLog1|NetLog2|WhaleOSADp|RequestLeoApi|Zeasn_http)[\s:]/i

const OKHTTP_REQ_LINE = /-->\s*(GET|POST|PUT|DELETE|PATCH|HEAD)\s+(https?:\/\/\S+)/i
const OKHTTP_RESP_LINE = /<--\s*(\d{3})\s+(?:\S+\s*)?\((\d+)ms\)|<--\s*(\d{3})\s+/i
const HEADER_LINE = /^([A-Za-z][\w-]{1,60}):\s(.+)$/
const JSON_BODY_LINE = /^\s*(\{.{2,}\}|\[.{2,}\])\s*$/
const WHALE_AD_LINE = /WhaleOSADpClient.*>>+\s*(\w+)\s*[==:]+\s*(.{0,250})/i
const LEO_TOPIC_LINE = /RequestLeoApi.*-+>Topic topicId[:\s]*(.+)/i
const LEO_RESP_LINE = /RequestLeoApi.*responseCode[=:\s]*(\d+)/i

interface HttpCtx {
  method: string; url: string; domain: string; path: string
  queryParams: ApiParam[]; requestHeaders: ApiParam[]; requestBody: string
  responseHeaders: ApiParam[]
  responseBody: string
  pendingResponseStatus: number | null
  pendingDurationMs: string
  time: string; rawLines: string[]
  phase: 'req_headers' | 'req_body' | 'resp_headers' | 'resp_body'
}

function parseUrlInfo(rawUrl: string): { domain: string; path: string; queryParams: ApiParam[] } {
  try {
    const u = new URL(rawUrl)
    const queryParams: ApiParam[] = []
    u.searchParams.forEach((v, k) => queryParams.push({ key: k, value: v }))
    return { domain: u.hostname, path: u.pathname, queryParams }
  } catch {
    const q = rawUrl.indexOf('?')
    const s = rawUrl.indexOf('/', 8)
    return {
      domain: s > 0 ? rawUrl.substring(0, s) : rawUrl,
      path: q > 0 ? rawUrl.substring(s > 0 ? s : 0, q) : (s > 0 ? rawUrl.substring(s) : '/'),
      queryParams: [],
    }
  }
}

function parseLogTime(line: string): string {
  const m = line.match(/^(\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+)/)
  return m ? m[1] : ''
}

function extractBody(line: string): string {
  const m = line.match(/\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+\s+\d+\s+\d+\s+[VDIWEF]\/[^:]+:\s*(.*)/)
  return m ? m[1] : line
}

function getSummary(rule: PatternRule, match: RegExpMatchArray): string {
  if (typeof rule.summary === 'function') {
    try { return rule.summary(match) } catch { return String(rule.summary) }
  }
  return rule.summary
}

// ── Composable ──

export function useLogAnalysis(serial: Ref<string | null | undefined>) {
  const isRunning = ref(false)
  const totalEvents = ref(0)
  const modules = ref<Record<string, ModuleState>>({})
  const events = ref<LogEvent[]>([])
  const apiRequests = ref<ApiRequest[]>([])

  let eventIdCounter = 0
  let apiIdCounter = 0
  const seenEventHashes = new Set<string>()
  const seenApiKeys = new Set<string>()
  let httpCtx: HttpCtx | null = null
  let unlisten: (() => void) | null = null

  function initModules() {
    const result: Record<string, ModuleState> = {}
    for (const [key, def] of Object.entries(MODULE_DEFS)) {
      result[key] = { key, name: def.name, icon: def.icon, status: 'unknown', summary: '等待日志数据…', lastUpdated: '', eventCount: 0, apiCount: 0 }
    }
    modules.value = result
  }

  function dedupEvent(line: string): boolean {
    const hash = line.substring(0, 120)
    if (seenEventHashes.has(hash)) return false
    seenEventHashes.add(hash)
    if (seenEventHashes.size > 6000) {
      const arr = Array.from(seenEventHashes).slice(3000)
      seenEventHashes.clear()
      arr.forEach(h => seenEventHashes.add(h))
    }
    return true
  }

  function emitApi(ctx: HttpCtx, responseStatus: number | null, durationMs: string) {
    const apiKey = `${ctx.time.substring(3, 18)}|${ctx.method}|${ctx.url.substring(0, 60)}`
    if (seenApiKeys.has(apiKey)) return
    seenApiKeys.add(apiKey)
    if (seenApiKeys.size > 2000) {
      const arr = Array.from(seenApiKeys).slice(1000)
      seenApiKeys.clear()
      arr.forEach(h => seenApiKeys.add(h))
    }
    const { moduleKey, moduleName } = detectModuleFromUrl(ctx.url)
    const api: ApiRequest = {
      id: ++apiIdCounter, time: ctx.time, method: ctx.method, url: ctx.url,
      domain: ctx.domain, path: ctx.path, queryParams: ctx.queryParams,
      requestHeaders: ctx.requestHeaders, requestBody: ctx.requestBody,
      responseStatus, responseHeaders: ctx.responseHeaders, responseBody: ctx.responseBody,
      durationMs, raw: ctx.rawLines.join('\n'),
      moduleKey, moduleName,
    }
    apiRequests.value.unshift(api)
    if (apiRequests.value.length > 300) apiRequests.value.splice(250)
    if (moduleKey && modules.value[moduleKey]) modules.value[moduleKey].apiCount++
  }

  function processHttpLine(line: string) {
    const time = parseLogTime(line)
    const body = extractBody(line)

    const adMatch = line.match(WHALE_AD_LINE)
    if (adMatch) {
      const apiKey = `${time.substring(3, 18)}|AD|${adMatch[1]}`
      if (!seenApiKeys.has(apiKey)) {
        seenApiKeys.add(apiKey)
        apiRequests.value.unshift({
          id: ++apiIdCounter, time, method: 'AD', url: '', domain: 'WhaleOSADpClient',
          path: `/${adMatch[1]}`,
          queryParams: [{ key: adMatch[1], value: adMatch[2]?.trim().substring(0, 300) }],
          requestHeaders: [], requestBody: '', responseStatus: null,
          responseHeaders: [], responseBody: '', durationMs: '',
          raw: line, moduleKey: 'ad', moduleName: '广告 SDK',
        })
        if (apiRequests.value.length > 300) apiRequests.value.splice(250)
        if (modules.value['ad']) modules.value['ad'].apiCount++
      }
      return
    }

    const leoMatch = line.match(LEO_TOPIC_LINE)
    if (leoMatch) {
      const apiKey = `${time.substring(3, 18)}|LEO|${leoMatch[1].trim().substring(0, 30)}`
      if (!seenApiKeys.has(apiKey)) {
        seenApiKeys.add(apiKey)
        apiRequests.value.unshift({
          id: ++apiIdCounter, time, method: 'GET', url: '', domain: 'acc-recommend.zeasn.tv',
          path: '/topic',
          queryParams: [{ key: 'topicId', value: leoMatch[1]?.trim() }],
          requestHeaders: [], requestBody: '', responseStatus: null,
          responseHeaders: [], responseBody: '', durationMs: '',
          raw: line, moduleKey: 'recommend', moduleName: '推荐内容',
        })
        if (apiRequests.value.length > 300) apiRequests.value.splice(250)
        if (modules.value['recommend']) modules.value['recommend'].apiCount++
      }
      return
    }

    const leoResp = line.match(LEO_RESP_LINE)
    if (leoResp) {
      const idx = apiRequests.value.findIndex(a => a.moduleKey === 'recommend' && a.responseStatus === null)
      if (idx >= 0) apiRequests.value[idx] = { ...apiRequests.value[idx], responseStatus: Number(leoResp[1]) }
      return
    }

    const reqMatch = body.match(OKHTTP_REQ_LINE) || line.match(OKHTTP_REQ_LINE)
    if (reqMatch) {
      if (httpCtx) emitApi(httpCtx, httpCtx.pendingResponseStatus, httpCtx.pendingDurationMs)
      const rawUrl = reqMatch[2].replace(/[,;)\s]+$/, '')
      const { domain, path, queryParams } = parseUrlInfo(rawUrl)
      httpCtx = {
        method: reqMatch[1].toUpperCase(), url: rawUrl, domain, path, queryParams,
        requestHeaders: [], requestBody: '', responseHeaders: [],
        responseBody: '', pendingResponseStatus: null, pendingDurationMs: '',
        time, rawLines: [line], phase: 'req_headers',
      }
      return
    }

    const respMatch = body.match(OKHTTP_RESP_LINE) || line.match(OKHTTP_RESP_LINE)
    if (respMatch && httpCtx) {
      httpCtx.rawLines.push(line)
      httpCtx.pendingResponseStatus = Number(respMatch[1] || respMatch[3])
      httpCtx.pendingDurationMs = respMatch[2] || ''
      httpCtx.phase = 'resp_headers'
      return
    }

    if (/<-- END HTTP/i.test(body) && httpCtx) {
      httpCtx.rawLines.push(line)
      emitApi(httpCtx, httpCtx.pendingResponseStatus, httpCtx.pendingDurationMs)
      httpCtx = null
      return
    }

    if (httpCtx) {
      httpCtx.rawLines.push(line)
      if (body.trim() === '') {
        if (httpCtx.phase === 'req_headers') httpCtx.phase = 'req_body'
        else if (httpCtx.phase === 'resp_headers') httpCtx.phase = 'resp_body'
        return
      }
      const headerMatch = body.match(HEADER_LINE)
      if (headerMatch) {
        if (httpCtx.phase === 'req_headers') httpCtx.requestHeaders.push({ key: headerMatch[1], value: headerMatch[2] })
        else if (httpCtx.phase === 'resp_headers') httpCtx.responseHeaders.push({ key: headerMatch[1], value: headerMatch[2] })
        return
      }
      if (httpCtx.phase === 'req_body' && body.trim().length > 0) {
        const t = body.trim()
        httpCtx.requestBody = httpCtx.requestBody.length === 0 ? t : httpCtx.requestBody + '\n' + t
      }
      if (httpCtx.phase === 'resp_body' && body.trim().length > 0 && httpCtx.responseBody.length < 8000) {
        const t = body.trim()
        httpCtx.responseBody = httpCtx.responseBody.length === 0 ? t : httpCtx.responseBody + '\n' + t
      }
      return
    }

    const urlMatch = line.match(/(https?:\/\/[a-zA-Z0-9][-a-zA-Z0-9.]*\.(?:zeasn|whaletv)[^\s"'<>]{0,300})/i)
    if (urlMatch) {
      const rawUrl = urlMatch[1].replace(/[,;)"'\s]+$/, '')
      const apiKey = `${time.substring(3, 15)}|URL|${rawUrl.substring(0, 60)}`
      if (!seenApiKeys.has(apiKey)) {
        seenApiKeys.add(apiKey)
        const { domain, path, queryParams } = parseUrlInfo(rawUrl)
        const statusMatch = line.match(/\b(200|201|204|301|302|400|401|403|404|500|502|503)\b/)
        const methodMatch = line.match(/\b(GET|POST|PUT|DELETE|PATCH)\b/i)
        const { moduleKey, moduleName } = detectModuleFromUrl(rawUrl)
        apiRequests.value.unshift({
          id: ++apiIdCounter, time,
          method: methodMatch ? methodMatch[1].toUpperCase() : 'HTTP',
          url: rawUrl, domain, path, queryParams,
          requestHeaders: [], requestBody: '',
          responseStatus: statusMatch ? Number(statusMatch[1]) : null,
          responseHeaders: [], responseBody: '',
          durationMs: '', raw: line, moduleKey, moduleName,
        })
        if (apiRequests.value.length > 300) apiRequests.value.splice(250)
        if (moduleKey && modules.value[moduleKey]) modules.value[moduleKey].apiCount++
      }
    }
  }

  function processLines(lines: string[]) {
    const newEvents: LogEvent[] = []
    const newApis: ApiRequest[] = []
    const modUpdates = new Map<string, { status: ModuleStatus; summary: string; time: string }>()

    const origApiRequests = apiRequests.value
    apiRequests.value = newApis as typeof apiRequests.value

    for (const line of lines) {
      const isHttpTag = HTTP_TAG_PATTERN.test(line)
        || /-->\s*(GET|POST|PUT|DELETE|PATCH)/i.test(line)
        || /<--\s*\d{3}/i.test(line)

      if (isHttpTag || httpCtx !== null) {
        processHttpLine(line)
      }

      matchEventLine(line, newEvents, modUpdates)
    }

    apiRequests.value = origApiRequests
    if (newApis.length > 0) {
      apiRequests.value.unshift(...newApis)
      if (apiRequests.value.length > 300) apiRequests.value.splice(250)
    }

    for (const [key, upd] of modUpdates) {
      const mod = modules.value[key]
      if (mod) {
        mod.status = upd.status
        mod.summary = upd.summary
        mod.lastUpdated = upd.time
        mod.eventCount += newEvents.filter(e => e.moduleKey === key).length
      }
    }

    if (newEvents.length > 0) {
      events.value.unshift(...newEvents)
      if (events.value.length > 600) events.value.splice(500)
      totalEvents.value += newEvents.length
    }
  }

  // matchEventLine 改为接收批量缓冲，不直接写 reactive
  function matchEventLine(line: string, newEvents: LogEvent[], modUpdates: Map<string, { status: ModuleStatus; summary: string; time: string }>) {
    if (!dedupEvent(line)) return

    const time = parseLogTime(line)
    for (const [key, def] of Object.entries(MODULE_DEFS)) {
      for (const rule of def.patterns) {
        const m = line.match(rule.regex)
        if (m) {
          const summary = getSummary(rule, m)
          modUpdates.set(key, { status: rule.status, summary, time: time || new Date().toLocaleTimeString() })
          newEvents.push({
            id: ++eventIdCounter, time: time || new Date().toLocaleTimeString(),
            moduleKey: key, moduleName: def.name,
            status: rule.status, summary,
            raw: line,
          })
          break
        }
      }
    }
  }

  async function start() {
    if (!serial.value || isRunning.value) return
    isRunning.value = true
    events.value = []; apiRequests.value = []; totalEvents.value = 0
    seenEventHashes.clear(); seenApiKeys.clear(); httpCtx = null
    initModules()

    const { listen } = await import('@tauri-apps/api/event')
    const eventName = `logcat://lines:${serial.value}`
    unlisten = await listen<{ serial: string; lines: string[] }>(eventName, (e) => {
      if (!isRunning.value) return
      processLines(e.payload.lines)
    })
  }

  function stop() {
    isRunning.value = false
    httpCtx = null
    if (unlisten) { unlisten(); unlisten = null }
  }

  function clear() {
    events.value = []; apiRequests.value = []; totalEvents.value = 0
    seenEventHashes.clear(); seenApiKeys.clear(); httpCtx = null
    initModules()
  }

  function getModuleApis(moduleKey: string): ApiRequest[] {
    return apiRequests.value.filter(a => a.moduleKey === moduleKey)
  }

  onUnmounted(stop)
  return { isRunning, totalEvents, modules, events, apiRequests, start, stop, clear, getModuleApis }
}
