/**
 * AppList 组件
 * 
 * 已安装应用列表和操作
 * 使用虚拟滚动优化大量应用的渲染性能
 */

import React, { useState, useCallback, memo } from 'react'
import { FixedSizeList as List } from 'react-window'
import {
  Box,
  Paper,
  Typography,
  TextField,
  ListItem,
  ListItemText,
  IconButton,
  Tooltip,
  Chip,
  CircularProgress,
  InputAdornment,
  FormControlLabel,
  Switch,
} from '@mui/material'
import {
  Delete as DeleteIcon,
  PlayArrow as StartIcon,
  Stop as StopIcon,
  Clear as ClearIcon,
  Info as InfoIcon,
  Search as SearchIcon,
  Refresh as RefreshIcon,
  Download as DownloadIcon,
} from '@mui/icons-material'
import { getInstalledApps, uninstallApp, startApp, stopApp, clearAppData, getAppVersion, downloadApk } from '@services/localAgent'
import { useTranslation } from '@hooks/useTranslation'
import { copyToClipboard } from '@utils/clipboard'

interface AppInfo {
  package_name: string
  version_name?: string
  version_code?: string
}

// Loading 状态类型
type LoadingState = {
  [packageName: string]: {
    [action: string]: boolean
  }
}

// 独立的应用项组件，使用 memo 避免不必要的重渲染
interface AppItemProps {
  app: AppInfo
  loadingState: LoadingState
  onUninstall: (packageName: string) => void
  onStart: (packageName: string) => void
  onStop: (packageName: string) => void
  onClearData: (packageName: string) => void
  onGetVersion: (packageName: string) => void
  onCopyVersion: (versionName: string, versionCode: string) => void
  onCopyPackageName: (packageName: string) => void
  onDownloadApk: (packageName: string) => void
}

const AppItem = memo<AppItemProps>(({
  app,
  loadingState,
  onUninstall,
  onStart,
  onStop,
  onClearData,
  onGetVersion,
  onCopyVersion,
  onCopyPackageName,
  onDownloadApk,
}) => {
  const { t } = useTranslation()
  const pkgLoading = loadingState[app.package_name] || {}
  const hasAnyLoading = Object.values(pkgLoading).some(v => v)

  return (
    <ListItem
      sx={{
        border: 1,
        borderColor: 'divider',
        borderRadius: 1,
        mb: 1,
      }}
      secondaryAction={
        <Box>
          <Tooltip title={t.apps.downloadApk || 'Download APK'}>
            <IconButton
              edge="end"
              onClick={() => onDownloadApk(app.package_name)}
              disabled={hasAnyLoading}
              size="small"
              color="primary"
            >
              {pkgLoading.download ? (
                <CircularProgress size={20} />
              ) : (
                <DownloadIcon />
              )}
            </IconButton>
          </Tooltip>
          <Tooltip title={t.apps.appVersion}>
            <IconButton
              edge="end"
              onClick={() => onGetVersion(app.package_name)}
              disabled={hasAnyLoading}
              size="small"
            >
              {pkgLoading.version ? (
                <CircularProgress size={20} />
              ) : (
                <InfoIcon />
              )}
            </IconButton>
          </Tooltip>
          <Tooltip title={t.apps.startApp}>
            <IconButton
              edge="end"
              onClick={() => onStart(app.package_name)}
              disabled={hasAnyLoading}
              size="small"
            >
              {pkgLoading.start ? (
                <CircularProgress size={20} />
              ) : (
                <StartIcon />
              )}
            </IconButton>
          </Tooltip>
          <Tooltip title={t.apps.stopApp}>
            <IconButton
              edge="end"
              onClick={() => onStop(app.package_name)}
              disabled={hasAnyLoading}
              size="small"
            >
              {pkgLoading.stop ? (
                <CircularProgress size={20} />
              ) : (
                <StopIcon />
              )}
            </IconButton>
          </Tooltip>
          <Tooltip title={t.apps.clearData}>
            <IconButton
              edge="end"
              onClick={() => onClearData(app.package_name)}
              disabled={hasAnyLoading}
              size="small"
            >
              {pkgLoading.clear ? (
                <CircularProgress size={20} />
              ) : (
                <ClearIcon />
              )}
            </IconButton>
          </Tooltip>
          <Tooltip title={t.apps.uninstallApp}>
            <IconButton
              edge="end"
              onClick={() => onUninstall(app.package_name)}
              disabled={hasAnyLoading}
              size="small"
              color="error"
            >
              {pkgLoading.uninstall ? (
                <CircularProgress size={20} />
              ) : (
                <DeleteIcon />
              )}
            </IconButton>
          </Tooltip>
        </Box>
      }
    >
      <ListItemText
        primary={
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Tooltip title={t.apps.copyPackageName || 'Click to copy package name'}>
              <Typography 
                variant="body1"
                sx={{ 
                  cursor: 'pointer',
                  '&:hover': {
                    color: 'primary.main',
                    textDecoration: 'underline',
                  }
                }}
                onClick={() => onCopyPackageName(app.package_name)}
              >
                {app.package_name}
              </Typography>
            </Tooltip>
            {app.version_name && app.version_code && (
              <Tooltip title={t.apps.copyVersion || 'Click to copy version'}>
                <Chip
                  label={`v${app.version_name} (${app.version_code})`}
                  size="small"
                  color="primary"
                  onClick={() => onCopyVersion(app.version_name!, app.version_code!)}
                  sx={{ 
                    height: 22, 
                    fontSize: '0.75rem',
                    cursor: 'pointer',
                    '&:hover': {
                      opacity: 0.8,
                    }
                  }}
                />
              </Tooltip>
            )}
          </Box>
        }
      />
    </ListItem>
  )
})

AppItem.displayName = 'AppItem'

interface AppListProps {
  deviceId: string | null
  onSuccess?: (message: string) => void
  onError?: (error: string) => void
  refreshTrigger?: number
  defaultIncludeSystem?: boolean
}

export const AppList: React.FC<AppListProps> = ({
  deviceId,
  onSuccess,
  onError,
  refreshTrigger,
  defaultIncludeSystem = false,
}) => {
  const { t } = useTranslation()
  const [apps, setApps] = useState<AppInfo[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [loadingState, setLoadingState] = useState<LoadingState>({})
  const [loadingList, setLoadingList] = useState(false)
  const [includeSystem, setIncludeSystem] = useState(defaultIncludeSystem)
  const [loadedVersions, setLoadedVersions] = useState<Set<string>>(new Set())
  const listRef = React.useRef<List>(null)

  // 设置特定应用的特定操作的 loading 状态
  const setActionLoading = useCallback((packageName: string, action: string, loading: boolean) => {
    setLoadingState(prev => ({
      ...prev,
      [packageName]: {
        ...prev[packageName],
        [action]: loading
      }
    }))
  }, [])

  // 过滤和排序应用列表
  const filteredApps = apps.filter((app) =>
    app.package_name.toLowerCase().includes(searchQuery.toLowerCase())
  )

  // 自定义排序规则
  const sortedApps = React.useMemo(() => {
    return [...filteredApps].sort((a, b) => {
      const aPackage = a.package_name.toLowerCase()
      const bPackage = b.package_name.toLowerCase()
      
      // 0. overlay 排最后
      const aHasOverlay = aPackage.includes('overlay')
      const bHasOverlay = bPackage.includes('overlay')
      if (aHasOverlay && !bHasOverlay) return 1
      if (!aHasOverlay && bHasOverlay) return -1
      
      // 1. 四大应用排最前（特定包名）
      const bigFourApps = [
        'com.netflix.ninja',  // Netflix 特定包名
        'disney',             // Disney
        'youtube',            // YouTube
        'amazonvideo'         // Amazon Video
      ]
      const aIsBigFour = bigFourApps.some(app => aPackage.includes(app))
      const bIsBigFour = bigFourApps.some(app => bPackage.includes(app))
      if (aIsBigFour && !bIsBigFour) return -1
      if (!aIsBigFour && bIsBigFour) return 1
      
      // 2. 特定顺序的6个应用（在四大应用之后）
      const priorityApps = [
        'com.whaletv.launcher',
        'com.zeasn.whaleos.settings',
        'com.whaletv.aivoice',
        'com.zeasn.tv.cast',
        'com.zeasn.tokenapp',
        'com.zeasn.deviceportal.asdprovider.certified'
      ]
      const aIndex = priorityApps.indexOf(a.package_name)
      const bIndex = priorityApps.indexOf(b.package_name)
      const aIsPriority = aIndex !== -1
      const bIsPriority = bIndex !== -1
      
      if (aIsPriority && bIsPriority) {
        return aIndex - bIndex  // 按照数组顺序排序
      }
      if (aIsPriority && !bIsPriority) return -1
      if (!aIsPriority && bIsPriority) return 1
      
      // 3. whaletv 排第三（排除已在优先级列表中的）
      const aHasWhaletv = aPackage.includes('whaletv')
      const bHasWhaletv = bPackage.includes('whaletv')
      if (aHasWhaletv && !bHasWhaletv) return -1
      if (!aHasWhaletv && bHasWhaletv) return 1
      
      // 4. zeasn 或 rlaxxtv 排第四（排除已在优先级列表中的）
      const aHasZeasnOrRlaxxtv = aPackage.includes('zeasn') || aPackage.includes('rlaxxtv')
      const bHasZeasnOrRlaxxtv = bPackage.includes('zeasn') || bPackage.includes('rlaxxtv')
      if (aHasZeasnOrRlaxxtv && !bHasZeasnOrRlaxxtv) return -1
      if (!aHasZeasnOrRlaxxtv && bHasZeasnOrRlaxxtv) return 1
      
      // 5. 其他按字母顺序排序（包括其他 netflix 应用）
      return aPackage.localeCompare(bPackage)
    })
  }, [filteredApps])

  // 加载应用列表
  const loadApps = async () => {
    if (!deviceId) return

    setLoadingList(true)
    try {
      const response = await getInstalledApps(deviceId, includeSystem)
      if (response.success) {
        const packageNames = JSON.parse(response.output)
        
        // 创建旧版本信息的映射
        const oldVersionMap = new Map(
          apps.map(app => [app.package_name, {
            version_name: app.version_name,
            version_code: app.version_code
          }])
        )
        
        // 将包名列表转换为 AppInfo 对象，保留已有的版本信息
        const appList: AppInfo[] = packageNames.map((packageName: string) => {
          const oldVersion = oldVersionMap.get(packageName)
          return {
            package_name: packageName,
            version_name: oldVersion?.version_name,
            version_code: oldVersion?.version_code,
          }
        })
        setApps(appList)
        // 不清空已加载版本的记录，保留已有的版本信息
      } else {
        onError?.(`获取应用列表失败: ${response.error}`)
      }
    } catch (error: any) {
      onError?.(`获取应用列表失败: ${error.message}`)
    } finally {
      setLoadingList(false)
    }
  }

  // 获取单个应用的版本号
  const fetchVersion = useCallback(async (packageName: string) => {
    if (!deviceId || loadedVersions.has(packageName)) return
    
    // 标记为已加载，避免重复请求
    setLoadedVersions(prev => new Set(prev).add(packageName))
    
    try {
      const response = await getAppVersion(deviceId, packageName)
      if (response.success && response.output) {
        // 解析版本信息（output 是 JSON 字符串）
        const versionInfo = JSON.parse(response.output)
        // 更新应用列表中的版本信息
        setApps(prevApps => 
          prevApps.map(a => 
            a.package_name === packageName 
              ? { 
                  ...a, 
                  version_name: versionInfo.version_name,
                  version_code: versionInfo.version_code?.toString()
                }
              : a
          )
        )
      }
    } catch (error) {
      // 忽略版本获取失败
      console.warn(`Failed to get version for ${packageName}:`, error)
    }
  }, [deviceId, loadedVersions])

  // 当可见项改变时，加载版本号
  const handleItemsRendered = useCallback(({ visibleStartIndex, visibleStopIndex }: {
    visibleStartIndex: number
    visibleStopIndex: number
  }) => {
    // 获取可见范围内的应用
    const visibleApps = sortedApps.slice(visibleStartIndex, visibleStopIndex + 1)
    
    // 为每个可见应用加载版本号
    visibleApps.forEach(app => {
      if (!app.version_name && !loadedVersions.has(app.package_name)) {
        fetchVersion(app.package_name)
      }
    })
  }, [sortedApps, loadedVersions, fetchVersion])

  React.useEffect(() => {
    loadApps()
  }, [deviceId, includeSystem])

  // 监听refreshTrigger变化，刷新应用列表
  React.useEffect(() => {
    if (refreshTrigger && refreshTrigger > 0) {
      loadApps()
    }
  }, [refreshTrigger])

  const handleUninstall = useCallback(async (packageName: string) => {
    if (!deviceId) return

    setActionLoading(packageName, 'uninstall', true)
    try {
      const response = await uninstallApp(deviceId, packageName)
      if (response.success) {
        onSuccess?.(`已卸载 ${packageName}`)
        // 从列表中移除
        setApps(prevApps => prevApps.filter(a => a.package_name !== packageName))
      } else {
        onError?.(`卸载应用失败: ${response.error}`)
      }
    } catch (error: any) {
      onError?.(`卸载应用失败: ${error.message}`)
    } finally {
      setActionLoading(packageName, 'uninstall', false)
    }
  }, [deviceId, onSuccess, onError, setActionLoading])

  const handleStart = useCallback(async (packageName: string) => {
    if (!deviceId) return

    setActionLoading(packageName, 'start', true)
    try {
      const response = await startApp(deviceId, packageName)
      if (response.success) {
        onSuccess?.(`已启动 ${packageName}`)
      } else {
        onError?.(`启动应用失败: ${response.error}`)
      }
    } catch (error: any) {
      onError?.(`启动应用失败: ${error.message}`)
    } finally {
      setActionLoading(packageName, 'start', false)
    }
  }, [deviceId, onSuccess, onError, setActionLoading])

  const handleStop = useCallback(async (packageName: string) => {
    if (!deviceId) return

    setActionLoading(packageName, 'stop', true)
    try {
      const response = await stopApp(deviceId, packageName)
      if (response.success) {
        onSuccess?.(`已停止 ${packageName}`)
      } else {
        onError?.(`停止应用失败: ${response.error}`)
      }
    } catch (error: any) {
      onError?.(`停止应用失败: ${error.message}`)
    } finally {
      setActionLoading(packageName, 'stop', false)
    }
  }, [deviceId, onSuccess, onError, setActionLoading])

  const handleClearData = useCallback(async (packageName: string) => {
    if (!deviceId) return

    setActionLoading(packageName, 'clear', true)
    try {
      const response = await clearAppData(deviceId, packageName)
      if (response.success) {
        onSuccess?.(`已清除 ${packageName} 的数据`)
      } else {
        onError?.(`清除数据失败: ${response.error}`)
      }
    } catch (error: any) {
      onError?.(`清除数据失败: ${error.message}`)
    } finally {
      setActionLoading(packageName, 'clear', false)
    }
  }, [deviceId, onSuccess, onError, setActionLoading])

  const handleGetVersion = useCallback(async (packageName: string) => {
    if (!deviceId) return

    setActionLoading(packageName, 'version', true)
    try {
      const response = await getAppVersion(deviceId, packageName)
      if (response.success) {
        const versionInfo = JSON.parse(response.output)
        // 更新应用列表中的版本信息
        setApps(prevApps => 
          prevApps.map(a => 
            a.package_name === packageName 
              ? { 
                  ...a, 
                  version_name: versionInfo.version_name,
                  version_code: versionInfo.version_code?.toString()
                }
              : a
          )
        )
        onSuccess?.(
          t.apps.versionInfo
            .replace('{name}', versionInfo.version_name)
            .replace('{code}', versionInfo.version_code.toString())
        )
      } else {
        onError?.(`${t.apps.getVersionFailed}: ${response.error}`)
      }
    } catch (error: any) {
      onError?.(`${t.apps.getVersionFailed}: ${error.message}`)
    } finally {
      setActionLoading(packageName, 'version', false)
    }
  }, [deviceId, onSuccess, onError, setActionLoading, t])

  const handleCopyVersion = useCallback(async (versionName: string, versionCode: string) => {
    const versionText = `${versionName} (${versionCode})`
    const success = await copyToClipboard(versionText)
    if (success) {
      onSuccess?.(t.apps.versionCopied)
    } else {
      onError?.('复制失败')
    }
  }, [onSuccess, onError, t])

  const handleCopyPackageName = useCallback(async (packageName: string) => {
    const success = await copyToClipboard(packageName)
    if (success) {
      onSuccess?.('包名已复制到剪贴板')
    } else {
      onError?.('复制失败')
    }
  }, [onSuccess, onError])

  const handleDownloadApk = useCallback(async (packageName: string) => {
    if (!deviceId) return

    setActionLoading(packageName, 'download', true)
    try {
      const blob = await downloadApk(deviceId, packageName)
      
      // Create download link
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `${packageName}.apk`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      
      onSuccess?.(`APK 已下载: ${packageName}.apk`)
    } catch (error: any) {
      console.error('Download APK error:', error)
      const errorMessage = error.message || '下载 APK 失败'
      onError?.(errorMessage)
    } finally {
      setActionLoading(packageName, 'download', false)
    }
  }, [deviceId, onSuccess, onError, setActionLoading])

  if (!deviceId) {
    return (
      <Paper sx={{ p: 3, textAlign: 'center' }}>
        <Typography color="text.secondary">{t.devices.pleaseSelectDevice}</Typography>
      </Paper>
    )
  }

  // 虚拟列表行渲染器
  const Row = ({ index, style }: { index: number; style: React.CSSProperties }) => {
    const app = sortedApps[index]
    return (
      <div style={style}>
        <AppItem
          app={app}
          loadingState={loadingState}
          onUninstall={handleUninstall}
          onStart={handleStart}
          onStop={handleStop}
          onClearData={handleClearData}
          onGetVersion={handleGetVersion}
          onCopyVersion={handleCopyVersion}
          onCopyPackageName={handleCopyPackageName}
          onDownloadApk={handleDownloadApk}
        />
      </div>
    )
  }

  return (
    <Paper sx={{ p: 3 }}>
      {/* 标题栏 */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">
          {t.apps.installedApps}
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <FormControlLabel
            control={
              <Switch
                checked={includeSystem}
                onChange={(e) => setIncludeSystem(e.target.checked)}
                size="small"
              />
            }
            label={t.apps.showSystemApps || '显示系统应用'}
          />
          <Tooltip title={t.apps.refreshApps}>
            <span>
              <IconButton onClick={loadApps} disabled={loadingList} size="small">
                {loadingList ? <CircularProgress size={20} /> : <RefreshIcon />}
              </IconButton>
            </span>
          </Tooltip>
        </Box>
      </Box>

      <TextField
        fullWidth
        placeholder={t.apps.searchApps}
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
        size="small"
        sx={{ mb: 2 }}
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <SearchIcon />
            </InputAdornment>
          ),
        }}
      />

      {loadingList ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
        </Box>
      ) : sortedApps.length === 0 ? (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <Typography color="text.secondary">
            {searchQuery ? t.apps.noApps : t.apps.noApps}
          </Typography>
        </Box>
      ) : (
        <Box sx={{ height: 'calc(100vh - 350px)', minHeight: 400 }}>
          <List
            ref={listRef}
            height={Math.min(sortedApps.length * 72, window.innerHeight - 350)}
            itemCount={sortedApps.length}
            itemSize={72}
            width="100%"
            onItemsRendered={handleItemsRendered}
          >
            {Row}
          </List>
        </Box>
      )}

      <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block' }}>
        {t.apps.totalApps || '共'} {sortedApps.length} {t.apps.apps || '个应用'}
      </Typography>
    </Paper>
  )
}
