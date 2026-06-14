/**
 * 仪表板页面 - 紧凑型单屏布局
 *
 * 设计目标：
 * - 1366x768 笔记本屏幕一屏内不滚动
 * - 设备信息独占左栏；右栏纵向排列：设备信息(查询) → 设备控制 → 日志采集 → 其他 → 应用管理
 * - 视觉风格：靛蓝主题 + 轻毛玻璃按钮
 * - 后端调用与字段沿用既有实现
 * - 所有输入框带历史记录（按 key 隔离，最多 15 条）
 */

import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  Fade,
  FormControlLabel,
  IconButton,
  Pagination,
  Paper,
  Snackbar,
  Stack,
  Switch,
  Tooltip,
  Typography,
} from '@mui/material'
import {
  Add as AddIcon,
  Apps as AppsIcon,
  Article as ArticleIcon,
  Cable as CableIcon,
  CameraAlt as CameraIcon,
  CheckBox as CheckBoxIcon,
  CheckBoxOutlineBlank as CheckBoxOutlineBlankIcon,
  CheckCircle as CheckCircleIcon,
  ChevronRight as ChevronRightIcon,
  CleaningServices as CleaningServicesIcon,
  Close as CloseIcon,
  CloudUpload as UploadIcon,
  ContentCopy as CopyIcon,
  Delete as DeleteIcon,
  DeleteSweep as ClearIcon,
  Download as DownloadIcon,
  ErrorOutline as ErrorIcon,
  ExtensionOutlined as ExtensionIcon,
  FiberManualRecord as RecordIcon,
  FolderOpen as FolderIcon,
  Info as InfoIcon,
  KeyboardReturn as ReturnIcon,
  Memory as MemoryIcon,
  PlayArrow as PlayIcon,
  PowerSettingsNew as PowerIcon,
  Refresh as RefreshIcon,
  RestartAlt as RestartIcon,
  Screenshot as ScreenshotIcon,
  Search as SearchIcon,
  Security as SecurityIcon,
  Send as SendIcon,
  Settings as SettingsIcon,
  Stop as StopIcon,
  Storage as StorageIcon,
  TouchApp as TouchAppIcon,
  Tune as TuneIcon,
  Visibility as VisibilityIcon,
  WarningAmber as WarningIcon,
} from '@mui/icons-material'
import { useNavigate } from 'react-router-dom'
import { useDeviceStore } from '@store/deviceStore'
import { useRecordingSessionStore } from '@store/recordingSessionStore'
import { useLogSessionStore } from '@store/logSessionStore'
import { apiClient } from '@services/api'
import {
  checkDeviceKeys,
  clearAppData,
  clearLogcat as clearLogcatLocal,
  downloadApk,
  downloadScreenshot,
  executeAdbCommand,
  executeShellCommand,
  getAospFirmwareInfo,
  getAppVersion,
  getDeviceBasicInfo,
  getDeviceFirmwareInfo,
  getInstalledApps,
  inputText as sendText,
  modifyDeviceConfig,
  rebootDevice as rebootDeviceCmd,
  remountDevice as remountDeviceCmd,
  restartAdb,
  rootDevice as rootDeviceCmd,
  startApp,
  startDiagnosticLog,
  startLogcatSession,
  startRecordingSession,
  stopApp,
  stopDiagnosticLog,
  stopLogcatSession,
  stopRecordingSession,
  uninstallApp,
  uploadAndInstallApk,
} from '@services/localAgent'
import {
  addInputHistory,
  addIpToHistory,
} from '@utils/localStorage'
import { useTranslation } from '@hooks/useTranslation'
import { copyToClipboard } from '@utils/clipboard'
import {
  HistoryTextField,
  type HistoryTextFieldHandle,
} from '@components/common/HistoryTextField'
import { CustomButtonsPanel } from '@components/CustomButtons/CustomButtonsPanel'
import {
  getCustomButtons,
  type CustomButton as CustomButtonType,
} from '@utils/localStorage'

type SnackbarSeverity = 'success' | 'error' | 'info' | 'warning'

interface InfoDialogState {
  open: boolean
  title: string
  content: React.ReactNode
}

interface AppInfo {
  package_name: string
  version_name?: string
  version_code?: string
}

type AppActionLoading = {
  [packageName: string]: { [action: string]: boolean }
}

const PAGE_SIZE = 14

// ============== 视觉常量 ==============

const cardSx = {
  p: 1.5,
  borderRadius: 2,
  border: '1px solid rgba(226, 232, 240, 0.9)',
  bgcolor: 'rgba(255, 255, 255, 0.85)',
  backdropFilter: 'blur(12px)',
  WebkitBackdropFilter: 'blur(12px)',
  boxShadow: '0 1px 3px rgba(15, 23, 42, 0.04)',
  display: 'flex',
  flexDirection: 'column',
  minHeight: 0,
}

const sectionTitleSx = {
  display: 'flex',
  alignItems: 'center',
  gap: 0.75,
  mb: 1,
  fontSize: '1.05rem',
  fontWeight: 700,
  color: '#0f172a',
  '& .MuiSvgIcon-root': {
    fontSize: 20,
    color: '#6366f1',
  },
}

// 毛玻璃按钮（默认）
const glassBtnSx = {
  py: 0.45,
  px: 1.25,
  fontSize: '0.85rem',
  fontWeight: 500,
  textTransform: 'none' as const,
  borderRadius: '8px',
  minHeight: 32,
  lineHeight: 1.3,
  whiteSpace: 'nowrap' as const,
  color: '#475569',
  bgcolor: 'rgba(255, 255, 255, 0.6)',
  border: '1px solid rgba(226, 232, 240, 0.8)',
  backdropFilter: 'blur(8px)',
  WebkitBackdropFilter: 'blur(8px)',
  boxShadow: '0 1px 2px rgba(15, 23, 42, 0.03)',
  transition: 'all 0.15s ease',
  cursor: 'pointer',
  '&:hover': {
    bgcolor: 'rgba(238, 242, 255, 0.85)',
    borderColor: '#6366f1',
    color: '#4f46e5',
    boxShadow: '0 4px 10px rgba(99, 102, 241, 0.12)',
    transform: 'translateY(-1px)',
  },
  '&.Mui-disabled': {
    color: '#cbd5e1',
    bgcolor: 'rgba(248, 250, 252, 0.6)',
    borderColor: 'rgba(226, 232, 240, 0.6)',
    boxShadow: 'none',
  },
  '& .MuiButton-startIcon': {
    color: '#6366f1',
    mr: 0.5,
  },
  '&:hover .MuiButton-startIcon': {
    color: '#4f46e5',
  },
  '&.Mui-disabled .MuiButton-startIcon': {
    color: '#cbd5e1',
  },
}

const dangerGlassBtnSx = {
  ...glassBtnSx,
  color: '#dc2626',
  '& .MuiButton-startIcon': { color: '#ef4444', mr: 0.5 },
  '&:hover': {
    bgcolor: 'rgba(254, 242, 242, 0.85)',
    borderColor: '#ef4444',
    color: '#b91c1c',
    boxShadow: '0 4px 10px rgba(239, 68, 68, 0.12)',
    transform: 'translateY(-1px)',
  },
  '&:hover .MuiButton-startIcon': { color: '#dc2626' },
}

const activePrimaryBtnSx = {
  ...glassBtnSx,
  color: '#fff',
  bgcolor: 'rgba(99, 102, 241, 0.92)',
  borderColor: 'rgba(99, 102, 241, 0.92)',
  '& .MuiButton-startIcon': { color: '#fff', mr: 0.5 },
  '&:hover': {
    bgcolor: 'rgba(79, 70, 229, 1)',
    borderColor: 'rgba(79, 70, 229, 1)',
    color: '#fff',
    boxShadow: '0 6px 14px rgba(99, 102, 241, 0.32)',
    transform: 'translateY(-1px)',
  },
  '&:hover .MuiButton-startIcon': { color: '#fff' },
}

const activeRecordingBtnSx = {
  ...glassBtnSx,
  color: '#fff',
  bgcolor: 'rgba(239, 68, 68, 0.92)',
  borderColor: 'rgba(239, 68, 68, 0.92)',
  '& .MuiButton-startIcon': { color: '#fff', mr: 0.5 },
  '&:hover': {
    bgcolor: 'rgba(220, 38, 38, 1)',
    borderColor: 'rgba(220, 38, 38, 1)',
    color: '#fff',
    boxShadow: '0 6px 14px rgba(239, 68, 68, 0.32)',
  },
  '&:hover .MuiButton-startIcon': { color: '#fff' },
}

const activeDiagBtnSx = {
  ...glassBtnSx,
  color: '#fff',
  bgcolor: 'rgba(14, 165, 233, 0.92)',
  borderColor: 'rgba(14, 165, 233, 0.92)',
  '& .MuiButton-startIcon': { color: '#fff', mr: 0.5 },
  '&:hover': {
    bgcolor: 'rgba(2, 132, 199, 1)',
    borderColor: 'rgba(2, 132, 199, 1)',
    color: '#fff',
    boxShadow: '0 6px 14px rgba(14, 165, 233, 0.32)',
  },
  '&:hover .MuiButton-startIcon': { color: '#fff' },
}

const inputSx = {
  bgcolor: 'rgba(255, 255, 255, 0.7)',
  borderRadius: '8px',
  fontSize: '0.92rem',
  '& .MuiInputBase-input': { fontSize: '0.92rem', py: 0.85 },
  '& .MuiOutlinedInput-notchedOutline': { borderColor: 'rgba(226, 232, 240, 0.8)' },
  '&:hover .MuiOutlinedInput-notchedOutline': { borderColor: '#6366f1' },
  '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
    borderColor: '#6366f1',
    borderWidth: '1px',
  },
}

// 与原 AppList 一致的排序规则
function sortApps(apps: AppInfo[]): AppInfo[] {
  return [...apps].sort((a, b) => {
    const aPackage = a.package_name.toLowerCase()
    const bPackage = b.package_name.toLowerCase()

    const aHasOverlay = aPackage.includes('overlay')
    const bHasOverlay = bPackage.includes('overlay')
    if (aHasOverlay && !bHasOverlay) return 1
    if (!aHasOverlay && bHasOverlay) return -1

    const bigFourApps = ['com.netflix.ninja', 'disney', 'youtube', 'amazonvideo']
    const aIsBigFour = bigFourApps.some((app) => aPackage.includes(app))
    const bIsBigFour = bigFourApps.some((app) => bPackage.includes(app))
    if (aIsBigFour && !bIsBigFour) return -1
    if (!aIsBigFour && bIsBigFour) return 1

    const priorityApps = [
      'com.whaletv.launcher',
      'com.zeasn.whaleos.settings',
      'com.whaletv.aivoice',
      'com.zeasn.tv.cast',
      'com.zeasn.tokenapp',
      'com.zeasn.deviceportal.asdprovider.certified',
    ]
    const aIndex = priorityApps.indexOf(a.package_name)
    const bIndex = priorityApps.indexOf(b.package_name)
    const aIsPriority = aIndex !== -1
    const bIsPriority = bIndex !== -1
    if (aIsPriority && bIsPriority) return aIndex - bIndex
    if (aIsPriority && !bIsPriority) return -1
    if (!aIsPriority && bIsPriority) return 1

    const aHasWhaletv = aPackage.includes('whaletv')
    const bHasWhaletv = bPackage.includes('whaletv')
    if (aHasWhaletv && !bHasWhaletv) return -1
    if (!aHasWhaletv && bHasWhaletv) return 1

    const aHasZeasnOrRlaxxtv =
      aPackage.includes('zeasn') || aPackage.includes('rlaxxtv')
    const bHasZeasnOrRlaxxtv =
      bPackage.includes('zeasn') || bPackage.includes('rlaxxtv')
    if (aHasZeasnOrRlaxxtv && !bHasZeasnOrRlaxxtv) return -1
    if (!aHasZeasnOrRlaxxtv && bHasZeasnOrRlaxxtv) return 1

    return aPackage.localeCompare(bPackage)
  })
}

// 输入历史 keys
const HK_IP = 'connect_ip'
const HK_PORT = 'connect_port'
const HK_TEXT = 'input_text'
const HK_PKG_QUERY = 'app_path_pkg'
const HK_CONFIG_PATH = 'config_path'
const HK_CONFIG_KEY = 'config_key'
const HK_CONFIG_VALUE = 'config_value'
const HK_APP_SEARCH = 'app_search'

export const DashboardPage: React.FC = () => {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const {
    devices,
    selectedDevice,
    fetchingDevices,
    connecting,
    error,
    fetchDevices,
    selectDevice,
    connectDevice,
    disconnectDevice,
    clearError,
  } = useDeviceStore()

  const { recordingSession, setRecordingSession, clearRecordingSession } =
    useRecordingSessionStore()
  const {
    logcatSession,
    setLogcatSession,
    diagnosticSession,
    setDiagnosticSession,
    bootLogcatSession,
    setBootLogcatSession,
  } = useLogSessionStore()

  const [snackbar, setSnackbar] = useState<{
    open: boolean
    message: string
    severity: SnackbarSeverity
  }>({ open: false, message: '', severity: 'success' })

  // 连接表单
  const [ip, setIp] = useState('')
  const [port, setPort] = useState('5555')
  const ipHistoryRef = useRef<HistoryTextFieldHandle>(null)
  const portHistoryRef = useRef<HistoryTextFieldHandle>(null)

  // 输入文本
  const [textInput, setTextInput] = useState('')
  const textHistoryRef = useRef<HistoryTextFieldHandle>(null)

  // 应用相关
  const [currentApp, setCurrentApp] = useState('')
  const [queryPackage, setQueryPackage] = useState('')
  const [appPath, setAppPath] = useState('')
  const apkInputRef = useRef<HTMLInputElement | null>(null)
  const pkgQueryHistoryRef = useRef<HistoryTextFieldHandle>(null)
  const [reinstallApk, setReinstallApk] = useState(true)

  // 已安装应用列表
  const [apps, setApps] = useState<AppInfo[]>([])
  const [appsLoading, setAppsLoading] = useState(false)
  const [appSearch, setAppSearch] = useState('')
  const appSearchHistoryRef = useRef<HistoryTextFieldHandle>(null)
  const [includeSystem, setIncludeSystem] = useState(true)
  const [appPage, setAppPage] = useState(1)
  const [appLoadingState, setAppLoadingState] = useState<AppActionLoading>({})
  const loadedVersionsRef = useRef<Set<string>>(new Set())

  // 修改配置
  const [configDialogOpen, setConfigDialogOpen] = useState(false)
  const [configPath, setConfigPath] = useState('')
  const [configKey, setConfigKey] = useState('')
  const [configValue, setConfigValue] = useState('')
  const configPathHistoryRef = useRef<HistoryTextFieldHandle>(null)
  const configKeyHistoryRef = useRef<HistoryTextFieldHandle>(null)
  const configValueHistoryRef = useRef<HistoryTextFieldHandle>(null)

  // 加载状态
  const [actionLoading, setActionLoading] = useState<string | null>(null)

  // 通用对话框
  const [confirmDialog, setConfirmDialog] = useState<{
    open: boolean
    title: string
    message: string
    action: () => void | Promise<void>
  }>({ open: false, title: '', message: '', action: () => {} })

  const [infoDialog, setInfoDialog] = useState<InfoDialogState>({
    open: false,
    title: '',
    content: null,
  })

  // 录屏 / 诊断日志 / 开机日志计时
  const [recordingElapsed, setRecordingElapsed] = useState(0)
  const [diagnosticElapsed, setDiagnosticElapsed] = useState(0)
  const [bootElapsed, setBootElapsed] = useState(0)

  // 自定义按钮面板（右栏转场）
  const [showCustomButtonsPanel, setShowCustomButtonsPanel] = useState(false)
  const [topCustomButtons, setTopCustomButtons] = useState<CustomButtonType[]>([])
  const [executingCustomBtn, setExecutingCustomBtn] = useState<string | null>(null)
  const [customExecResult, setCustomExecResult] = useState<{
    open: boolean
    name: string
    command: string
    output: string
    returnCode: number
  }>({ open: false, name: '', command: '', output: '', returnCode: 0 })

  // Boot logcat 轮询
  const bootPollRef = useRef<number | null>(null)

  // ==================== 工具函数 ====================
  const showSnackbar = (message: string, severity: SnackbarSeverity = 'success') => {
    setSnackbar({ open: true, message, severity })
  }

  useEffect(() => {
    if (error) {
      showSnackbar(error, 'error')
      clearError()
    }
  }, [error])

  useEffect(() => {
    if (!recordingSession) {
      setRecordingElapsed(0)
      return
    }
    const startTime = recordingSession.startTime
    const id = window.setInterval(() => {
      setRecordingElapsed(Math.floor((Date.now() - startTime) / 1000))
    }, 1000)
    return () => window.clearInterval(id)
  }, [recordingSession?.sessionId])

  useEffect(() => {
    if (!diagnosticSession) {
      setDiagnosticElapsed(0)
      return
    }
    const startTime = diagnosticSession.startTime
    const id = window.setInterval(() => {
      setDiagnosticElapsed(Math.floor((Date.now() - startTime) / 1000))
    }, 1000)
    return () => window.clearInterval(id)
  }, [diagnosticSession?.sessionId])

  useEffect(() => {
    if (!bootLogcatSession) {
      setBootElapsed(0)
      return
    }
    const startTime = bootLogcatSession.startTime
    const id = window.setInterval(() => {
      setBootElapsed(Math.floor((Date.now() - startTime) / 1000))
    }, 1000)
    return () => window.clearInterval(id)
  }, [bootLogcatSession?.sessionId])

  const isOnline = selectedDevice?.status === 'device'
  const deviceId = selectedDevice?.device_id || null

  const requireDevice = (): boolean => {
    if (!deviceId) {
      showSnackbar(t.messages.pleaseSelectDevice, 'warning')
      return false
    }
    return true
  }

  const runAction = async (
    key: string,
    fn: () => Promise<{ success: boolean; output: string; error: string }>,
    successMsg: string,
    failMsg: string,
  ) => {
    setActionLoading(key)
    try {
      const res = await fn()
      if (res.success) {
        showSnackbar(successMsg, 'success')
        return true
      }
      showSnackbar(`${failMsg}: ${res.error || res.output || ''}`.trim(), 'error')
      return false
    } catch (err: any) {
      showSnackbar(`${failMsg}: ${err?.message || t.messages.unknownError}`, 'error')
      return false
    } finally {
      setActionLoading(null)
    }
  }

  const formatDuration = (seconds: number): string => {
    const m = Math.floor(seconds / 60)
    const s = seconds % 60
    return `${m}:${s.toString().padStart(2, '0')}`
  }

  // ==================== 连接 / 断开 ====================
  const handleConnect = async (e?: React.FormEvent) => {
    e?.preventDefault()
    const trimmedIp = ip.trim()
    const portNum = parseInt(port, 10)
    if (!/^(\d{1,3}\.){3}\d{1,3}$/.test(trimmedIp)) {
      showSnackbar(t.devices.enterIpAddress, 'error')
      return
    }
    if (isNaN(portNum) || portNum < 1 || portNum > 65535) {
      showSnackbar(t.devices.enterPort, 'error')
      return
    }
    const ok = await connectDevice(trimmedIp, portNum)
    if (ok) {
      addIpToHistory(trimmedIp, portNum)
      addInputHistory(HK_IP, trimmedIp)
      addInputHistory(HK_PORT, String(portNum))
      ipHistoryRef.current?.commit()
      portHistoryRef.current?.commit()
      setIp('')
      showSnackbar(`${t.messages.connectSuccess}: ${trimmedIp}:${portNum}`)
    }
  }

  const handleDisconnect = async (id: string) => {
    await disconnectDevice(id)
    showSnackbar(`${t.messages.disconnectSuccess}: ${id}`)
  }

  // ==================== 输入文本 ====================
  const handleSendText = async () => {
    if (!requireDevice()) return
    if (!textInput.trim()) {
      showSnackbar(t.devices.enterTextToSend, 'warning')
      return
    }
    const ok = await runAction(
      'send-text',
      () => sendText(deviceId!, textInput),
      t.devices.textSent,
      t.messages.operationFailed,
    )
    if (ok) {
      textHistoryRef.current?.commit()
      setTextInput('')
    }
  }

  // ==================== 设备控制 ====================
  const handleRestartAdb = () =>
    runAction(
      'restart-adb',
      () => restartAdb(),
      t.devices.adbRestarted,
      t.messages.operationFailed,
    )

  const handleReboot = () => {
    if (!requireDevice()) return
    setConfirmDialog({
      open: true,
      title: t.devices.rebootConfirm,
      message: t.devices.rebootMessage,
      action: async () => {
        setConfirmDialog((s) => ({ ...s, open: false }))
        await runAction(
          'reboot',
          () => rebootDeviceCmd(deviceId!),
          t.devices.rebootSuccess,
          t.messages.operationFailed,
        )
      },
    })
  }

  const handleRoot = () => {
    if (!requireDevice()) return
    runAction(
      'root',
      () => rootDeviceCmd(deviceId!),
      t.devices.rootSuccess,
      t.messages.operationFailed,
    )
  }

  const handleRemount = () => {
    if (!requireDevice()) return
    setConfirmDialog({
      open: true,
      title: 'Remount',
      message: t.devices.remountMessage,
      action: async () => {
        setConfirmDialog((s) => ({ ...s, open: false }))
        await runAction(
          'remount',
          () => remountDeviceCmd(deviceId!),
          t.devices.remountSuccess,
          t.messages.operationFailed,
        )
      },
    })
  }

  // ==================== 信息查询 ====================
  const showKeyValueDialog = (
    title: string,
    data: Array<{ key: string; value: string }>,
  ) => {
    setInfoDialog({
      open: true,
      title,
      content: (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.75 }}>
          {data.length === 0 && (
            <Typography variant="body2" color="text.secondary">
              {t.devices.keyCheckNoOutput}
            </Typography>
          )}
          {data.map((item, idx) => (
            <Box
              key={idx}
              sx={{
                display: 'flex',
                gap: 2,
                py: 0.5,
                borderBottom: idx < data.length - 1 ? '1px solid #f1f5f9' : 'none',
              }}
            >
              <Typography
                variant="body2"
                sx={{ fontWeight: 600, minWidth: 220, color: '#475569' }}
              >
                {item.key}
              </Typography>
              <Typography
                variant="body2"
                sx={{ wordBreak: 'break-all', color: '#0f172a', flex: 1 }}
              >
                {item.value}
              </Typography>
            </Box>
          ))}
        </Box>
      ),
    })
  }

  const handleBasicInfo = async () => {
    if (!requireDevice()) return
    setActionLoading('basic-info')
    try {
      const res = await getDeviceBasicInfo(deviceId!)
      if (res.success) {
        const data = JSON.parse(res.output) as Array<{ key: string; value: string }>
        showKeyValueDialog(t.devices.basicInfo, data)
      } else {
        showSnackbar(`${t.devices.getInfoFailed}: ${res.error}`, 'error')
      }
    } catch (e: any) {
      showSnackbar(`${t.devices.getInfoFailed}: ${e.message}`, 'error')
    } finally {
      setActionLoading(null)
    }
  }

  const handleWhaleOSInfo = async () => {
    if (!requireDevice()) return
    setActionLoading('whaleos-info')
    try {
      const res = await getDeviceFirmwareInfo(deviceId!)
      if (res.success) {
        const data = JSON.parse(res.output) as Record<string, string>
        showKeyValueDialog(
          t.devices.whaleOSInfo,
          Object.entries(data).map(([key, value]) => ({ key, value: String(value) })),
        )
      } else {
        showSnackbar(`${t.devices.getWhaleOSInfoFailed}: ${res.error}`, 'error')
      }
    } catch (e: any) {
      showSnackbar(`${t.devices.getWhaleOSInfoFailed}: ${e.message}`, 'error')
    } finally {
      setActionLoading(null)
    }
  }

  const handleFirmwareInfo = async () => {
    if (!requireDevice()) return
    setActionLoading('firmware-info')
    try {
      const res = await getAospFirmwareInfo(deviceId!)
      if (res.success) {
        const data = JSON.parse(res.output)
        const sections: Array<{ key: string; value: string }> = []
        if (data.firmware) {
          Object.entries(data.firmware).forEach(([k, v]) =>
            sections.push({ key: k, value: String(v) }),
          )
        }
        if (data.dp && Object.keys(data.dp).length) {
          sections.push({ key: '— DP —', value: '' })
          Object.entries(data.dp).forEach(([k, v]) =>
            sections.push({ key: k, value: String(v) }),
          )
        }
        if (data.adservice?.status) {
          sections.push({ key: '— ADService —', value: '' })
          sections.push({ key: t.devices.status, value: data.adservice.status })
          if (data.adservice.version_info) {
            sections.push({
              key: t.devices.versionInfo,
              value: data.adservice.version_info,
            })
          }
        }
        showKeyValueDialog(t.devices.aospInfo, sections)
      } else {
        showSnackbar(`${t.devices.getAospInfoFailed}: ${res.error}`, 'error')
      }
    } catch (e: any) {
      showSnackbar(`${t.devices.getAospInfoFailed}: ${e.message}`, 'error')
    } finally {
      setActionLoading(null)
    }
  }

  const handleCheckKeys = async () => {
    if (!requireDevice()) return
    setActionLoading('check-keys')
    try {
      const res = await checkDeviceKeys(deviceId!)
      if (res.success) {
        const results = JSON.parse(res.output) as Array<{
          name: string
          status: string
          message: string
          warning?: string
        }>
        setInfoDialog({
          open: true,
          title: t.devices.keyCheckTitle,
          content: (
            <Stack spacing={1.5}>
              {results.map((r, i) => {
                const ok = r.status === 'success'
                const color = ok ? '#10b981' : r.status === 'error' ? '#ef4444' : '#f59e0b'
                return (
                  <Box
                    key={i}
                    sx={{
                      p: 1.5,
                      borderRadius: 1.5,
                      border: `1px solid ${color}33`,
                      bgcolor: `${color}0d`,
                    }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                      {ok ? (
                        <CheckCircleIcon sx={{ fontSize: 18, color }} />
                      ) : r.status === 'error' ? (
                        <ErrorIcon sx={{ fontSize: 18, color }} />
                      ) : (
                        <WarningIcon sx={{ fontSize: 18, color }} />
                      )}
                      <Typography
                        sx={{ fontWeight: 600, fontSize: '0.875rem', color: '#0f172a' }}
                      >
                        {r.name}
                      </Typography>
                    </Box>
                    <Typography sx={{ fontSize: '0.8rem', color: '#475569' }}>
                      {r.message}
                    </Typography>
                    {r.warning && (
                      <Typography
                        sx={{
                          fontSize: '0.75rem',
                          color: '#b45309',
                          mt: 0.5,
                          fontStyle: 'italic',
                        }}
                      >
                        {r.warning}
                      </Typography>
                    )}
                  </Box>
                )
              })}
            </Stack>
          ),
        })
      } else {
        showSnackbar(`${t.devices.checkKeysFailed}: ${res.error}`, 'error')
      }
    } catch (e: any) {
      showSnackbar(`${t.devices.checkKeysFailed}: ${e.message}`, 'error')
    } finally {
      setActionLoading(null)
    }
  }

  // ==================== 截图 ====================
  const handleQuickScreenshot = async () => {
    if (!requireDevice()) return
    setActionLoading('screenshot')
    try {
      const blob = await downloadScreenshot(deviceId!)
      const ts = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `screenshot_${deviceId}_${ts}.png`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
      showSnackbar(t.screen.captureSuccess)
    } catch (e: any) {
      showSnackbar(e?.message || t.screen.captureFailed, 'error')
    } finally {
      setActionLoading(null)
    }
  }

  // ==================== 录屏 ====================
  const handleStartRecording = async () => {
    if (!requireDevice()) return
    setActionLoading('start-recording')
    try {
      const filename = `recording_${Date.now()}.mp4`
      const res = await startRecordingSession(deviceId!, filename)
      if (res.success && res.session_id) {
        setRecordingSession({
          sessionId: res.session_id,
          deviceId: deviceId!,
          startTime: Date.now(),
        })
        showSnackbar(t.screen.recordingStarted)
      } else {
        showSnackbar(res.error || t.screen.recordingFailed, 'error')
      }
    } catch (e: any) {
      showSnackbar(e?.message || t.screen.recordingFailed, 'error')
    } finally {
      setActionLoading(null)
    }
  }

  const handleStopRecording = async () => {
    if (!recordingSession) return
    setActionLoading('stop-recording')
    try {
      const blob = await stopRecordingSession(
        recordingSession.sessionId,
        recordingSession.deviceId,
      )
      const ts = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5)
      const dev = recordingSession.deviceId.replace(/:/g, '_')
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `recording_${dev}_${ts}.mp4`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
      showSnackbar(t.screen.recordingStopped)
      clearRecordingSession()
    } catch (e: any) {
      showSnackbar(e?.message || t.screen.recordingFailed, 'error')
    } finally {
      setActionLoading(null)
    }
  }

  // ==================== Logcat ====================
  const handleStartLogcat = async () => {
    if (!requireDevice()) return
    setActionLoading('start-logcat')
    try {
      const res = await startLogcatSession(deviceId!)
      if (res.success && res.session_id) {
        setLogcatSession({
          sessionId: res.session_id,
          deviceId: deviceId!,
          startTime: Date.now(),
        })
        showSnackbar(t.logs.startCaptureLog)
      } else {
        showSnackbar(res.error || t.logs.startCaptureFailed, 'error')
      }
    } catch (e: any) {
      showSnackbar(e?.message || t.logs.startCaptureFailed, 'error')
    } finally {
      setActionLoading(null)
    }
  }

  const handleStopLogcat = async () => {
    if (!logcatSession) return
    setActionLoading('stop-logcat')
    try {
      const blob = await stopLogcatSession(logcatSession.sessionId)
      const ts = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5)
      const dev = (logcatSession.deviceId || 'unknown').replace(/:/g, '_')
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `logcat_${dev}_${ts}.txt`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
      showSnackbar(t.logs.logDownloaded)
      setLogcatSession(null)
    } catch (e: any) {
      showSnackbar(e?.message || t.logs.stopCaptureFailed, 'error')
    } finally {
      setActionLoading(null)
    }
  }

  const handleClearLogcat = async () => {
    if (!requireDevice()) return
    await runAction(
      'clear-logcat',
      () => clearLogcatLocal(deviceId!),
      t.logs.deviceLogCleared,
      t.logs.clearDeviceLogFailed,
    )
  }

  // ==================== 完整诊断日志 ====================
  const handleStartDiagnostic = async () => {
    if (!requireDevice()) return
    setActionLoading('start-diag')
    try {
      const res = await startDiagnosticLog(deviceId!)
      if (res.success && res.session_id) {
        setDiagnosticSession({
          sessionId: res.session_id,
          deviceId: deviceId!,
          startTime: Date.now(),
        })
        showSnackbar(t.logs.captureStarted)
      } else {
        showSnackbar(res.error || t.logs.captureFailed, 'error')
      }
    } catch (e: any) {
      showSnackbar(e?.message || t.logs.captureFailed, 'error')
    } finally {
      setActionLoading(null)
    }
  }

  const handleStopDiagnostic = async () => {
    if (!diagnosticSession) return
    setActionLoading('stop-diag')
    try {
      const blob = await stopDiagnosticLog(diagnosticSession.sessionId)
      const ts = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5)
      const dev = diagnosticSession.deviceId.replace(/:/g, '_')
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `diagnostic_${dev}_${ts}.zip`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
      showSnackbar(t.logs.logDownloaded)
      setDiagnosticSession(null)
    } catch (e: any) {
      showSnackbar(e?.message || t.logs.captureFailed, 'error')
    } finally {
      setActionLoading(null)
    }
  }

  // ==================== Boot Logcat（开机日志） ====================
  const startBootLogcatPolling = useCallback(
    (sessionId: string) => {
      if (bootPollRef.current) {
        window.clearInterval(bootPollRef.current)
      }
      bootPollRef.current = window.setInterval(async () => {
        try {
          const statusResponse = await apiClient.getBootLogcatStatus(sessionId)
          if (statusResponse.success && statusResponse.data) {
            const status = statusResponse.data
            const current = useLogSessionStore.getState().bootLogcatSession
            if (current) {
              setBootLogcatSession({
                ...current,
                lineCount: status.line_count,
                connected: status.connected,
              })
            }
          }
        } catch (err) {
          console.error('Failed to get boot logcat status:', err)
        }
      }, 2000)
    },
    [setBootLogcatSession],
  )

  useEffect(() => {
    if (bootLogcatSession?.sessionId) {
      startBootLogcatPolling(bootLogcatSession.sessionId)
    }
    return () => {
      if (bootPollRef.current) {
        window.clearInterval(bootPollRef.current)
        bootPollRef.current = null
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [bootLogcatSession?.sessionId])

  const handleStartBootLogcat = async () => {
    setActionLoading('start-boot')
    try {
      const response = await apiClient.startBootLogcat(deviceId || undefined)
      if (response.success && response.data) {
        const { session_id, mode, device_id } = response.data
        setBootLogcatSession({
          sessionId: session_id,
          mode,
          deviceId: device_id,
          lineCount: 0,
          connected: mode === 'reboot',
          startTime: Date.now(),
        })
        showSnackbar(
          mode === 'reboot' ? t.devices.rebootSuccess : t.logs.capturing,
          'success',
        )
        startBootLogcatPolling(session_id)
      } else {
        showSnackbar(t.logs.startBootLogcatFailed, 'error')
      }
    } catch (err: any) {
      showSnackbar(
        err?.response?.data?.message || err?.message || t.logs.startBootLogcatFailed,
        'error',
      )
    } finally {
      setActionLoading(null)
    }
  }

  const handleStopBootLogcat = async () => {
    if (!bootLogcatSession) return
    setActionLoading('stop-boot')
    try {
      const blob = await apiClient.stopBootLogcat(bootLogcatSession.sessionId)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      const ts = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5)
      const dev = bootLogcatSession.deviceId?.replace(/:/g, '_') || 'unknown'
      a.download = `boot_logcat_${dev}_${ts}.txt`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
      showSnackbar(t.logs.logDownloaded)
      if (bootPollRef.current) {
        window.clearInterval(bootPollRef.current)
        bootPollRef.current = null
      }
      setBootLogcatSession(null)
    } catch (err: any) {
      showSnackbar(err?.message || t.logs.startBootLogcatFailed, 'error')
    } finally {
      setActionLoading(null)
    }
  }

  // ==================== 自定义按钮（左栏快捷执行） ====================
  const reloadTopCustomButtons = () => {
    try {
      // 展示全部按钮，按钮列表区域可滚动
      setTopCustomButtons(getCustomButtons())
    } catch {
      setTopCustomButtons([])
    }
  }

  useEffect(() => {
    reloadTopCustomButtons()
  }, [])

  // 当面板关闭时刷新左栏
  useEffect(() => {
    if (!showCustomButtonsPanel) {
      reloadTopCustomButtons()
    }
  }, [showCustomButtonsPanel])

  const handleQuickExecuteCustomButton = async (button: CustomButtonType) => {
    try {
      setExecutingCustomBtn(button.id)
      const originalCommand = button.command.trim()
      let response: any
      if (originalCommand.includes('adb')) {
        const globalCmds = [
          'devices',
          'start-server',
          'kill-server',
          'version',
          'help',
          'connect',
          'disconnect',
        ]
        const isGlobalCmd = globalCmds.some((c) =>
          originalCommand.includes(`adb ${c}`),
        )
        let adbArgs = originalCommand.replace(/^adb\s+/, '').trim()
        if (!isGlobalCmd && !adbArgs.startsWith('-s') && selectedDevice) {
          adbArgs = `-s ${selectedDevice.device_id} ${adbArgs}`
        }
        const args = adbArgs.match(/(?:[^\s"]+|"[^"]*")+/g) || []
        response = await executeAdbCommand(args)
      } else {
        response = await executeShellCommand(originalCommand)
      }
      setCustomExecResult({
        open: true,
        name: button.name,
        command: originalCommand,
        output: response.success
          ? response.output || ''
          : response.output || response.error || t.messages.unknownError,
        returnCode: response.success ? 0 : 1,
      })
      if (!response.success) {
        showSnackbar(
          `${t.customButtons.executeFailed}: ${response.error || ''}`,
          'error',
        )
      }
    } catch (err: any) {
      setCustomExecResult({
        open: true,
        name: button.name,
        command: button.command,
        output: err?.message || t.messages.unknownError,
        returnCode: 1,
      })
      showSnackbar(
        `${t.customButtons.executeFailed}: ${err?.message || ''}`,
        'error',
      )
    } finally {
      setExecutingCustomBtn(null)
    }
  }
  const handleSelectApk = () => {
    apkInputRef.current?.click()
  }

  const handleApkChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    if (!file.name.endsWith('.apk')) {
      showSnackbar(t.apps.selectApkFile, 'error')
      e.target.value = ''
      return
    }
    if (!deviceId) {
      showSnackbar(t.devices.pleaseSelectDevice, 'warning')
      e.target.value = ''
      return
    }
    setActionLoading('install-apk')
    try {
      const res = await uploadAndInstallApk(deviceId, file, reinstallApk)
      if (res.success) {
        showSnackbar(t.apps.installSuccess)
        loadApps()
      } else {
        showSnackbar(res.error || t.apps.installFailed, 'error')
      }
    } catch (err: any) {
      showSnackbar(err?.message || t.apps.installFailed, 'error')
    } finally {
      setActionLoading(null)
      e.target.value = ''
    }
  }

  const handleGetCurrentApp = async () => {
    if (!requireDevice()) return
    setActionLoading('current-app')
    try {
      const response = await executeAdbCommand([
        '-s',
        deviceId!,
        'shell',
        'dumpsys window | grep mCurrentFocus',
      ])
      if (response.success && response.output) {
        const match = response.output.match(/\{.*\s+(\S+)\//)
        if (match && match[1]) {
          setCurrentApp(match[1])
          showSnackbar(t.apps.currentAppIs.replace('{package}', match[1]))
        } else {
          showSnackbar(t.apps.getCurrentAppFailed, 'error')
        }
      } else {
        showSnackbar(t.apps.getCurrentAppFailed, 'error')
      }
    } catch (e: any) {
      showSnackbar(e?.message || t.apps.getCurrentAppFailed, 'error')
    } finally {
      setActionLoading(null)
    }
  }

  const handleGetAppPath = async () => {
    if (!requireDevice()) return
    if (!queryPackage.trim()) {
      showSnackbar(t.apps.enterPackageNamePrompt, 'warning')
      return
    }
    setActionLoading('app-path')
    try {
      const response = await executeAdbCommand([
        '-s',
        deviceId!,
        'shell',
        'pm',
        'path',
        queryPackage,
      ])
      if (response.success && response.output) {
        const match = response.output.match(/package:(.+)/)
        if (match && match[1]) {
          const path = match[1].trim()
          setAppPath(path)
          pkgQueryHistoryRef.current?.commit()
          showSnackbar(t.apps.appPathIs.replace('{path}', path))
        } else {
          showSnackbar(t.apps.getAppPathFailed, 'error')
        }
      } else {
        showSnackbar(response.error || t.apps.getAppPathFailed, 'error')
      }
    } catch (e: any) {
      showSnackbar(e?.message || t.apps.getAppPathFailed, 'error')
    } finally {
      setActionLoading(null)
    }
  }

  // ==================== 已安装应用列表 ====================
  const loadApps = useCallback(async (retries = 3) => {
    if (!deviceId) {
      setApps([])
      return
    }
    setAppsLoading(true)
    for (let attempt = 1; attempt <= retries; attempt++) {
      try {
        const response = await getInstalledApps(deviceId, includeSystem)
        if (response.success) {
          const packageNames: string[] = JSON.parse(response.output)
          const oldVersionMap = new Map(
            apps.map((a) => [
              a.package_name,
              { version_name: a.version_name, version_code: a.version_code },
            ]),
          )
          const list: AppInfo[] = packageNames.map((pkg) => {
            const old = oldVersionMap.get(pkg)
            return {
              package_name: pkg,
              version_name: old?.version_name,
              version_code: old?.version_code,
            }
          })
          setApps(list)
          setAppPage(1)
          break
        }
        if (attempt < retries) {
          await new Promise((r) => setTimeout(r, 2000))
        } else {
          showSnackbar(`${t.apps.getCurrentAppFailed}: ${response.error}`, 'error')
        }
      } catch (e: any) {
        if (attempt < retries) {
          await new Promise((r) => setTimeout(r, 2000))
        } else {
          showSnackbar(`${e?.message || 'Failed'}`, 'error')
        }
      }
    }
    setAppsLoading(false)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [deviceId, includeSystem])

  useEffect(() => {
    // 延迟 1 秒再加载，给设备一点准备时间
    const timer = setTimeout(() => loadApps(), 1000)
    return () => clearTimeout(timer)
  }, [deviceId, includeSystem]) // eslint-disable-line react-hooks/exhaustive-deps

  const sortedApps = useMemo(() => sortApps(apps), [apps])
  const filteredApps = useMemo(() => {
    const q = appSearch.trim().toLowerCase()
    if (!q) return sortedApps
    return sortedApps.filter((a) => a.package_name.toLowerCase().includes(q))
  }, [sortedApps, appSearch])

  const totalPages = Math.max(1, Math.ceil(filteredApps.length / PAGE_SIZE))
  const currentPageApps = useMemo(
    () => filteredApps.slice((appPage - 1) * PAGE_SIZE, appPage * PAGE_SIZE),
    [filteredApps, appPage],
  )

  // 用于排队顺序加载版本号，避免并发淹没本地代理 / 设备
  const versionQueueRef = useRef<Promise<unknown>>(Promise.resolve())

  useEffect(() => {
    if (!deviceId) return
    const localDeviceId = deviceId
    currentPageApps.forEach((app) => {
      if (
        !app.version_name &&
        !loadedVersionsRef.current.has(app.package_name)
      ) {
        loadedVersionsRef.current.add(app.package_name)
        // 排队执行：每个版本查询等前一个完成后再发起，
        // 避免一次性发起 14 个 dumpsys 调用阻塞 UI
        versionQueueRef.current = versionQueueRef.current
          .then(() => getAppVersion(localDeviceId, app.package_name))
          .then((res) => {
            if (res && res.success && res.output) {
              const info = JSON.parse(res.output)
              setApps((prev) =>
                prev.map((a) =>
                  a.package_name === app.package_name
                    ? {
                        ...a,
                        version_name: info.version_name,
                        version_code: info.version_code?.toString(),
                      }
                    : a,
                ),
              )
            }
          })
          .catch(() => {
            // ignore
          })
      }
    })
  }, [currentPageApps, deviceId])

  const setAppActionLoading = (pkg: string, action: string, loading: boolean) => {
    setAppLoadingState((prev) => ({
      ...prev,
      [pkg]: { ...prev[pkg], [action]: loading },
    }))
  }

  const handleAppDownload = async (pkg: string) => {
    if (!deviceId) return
    setAppActionLoading(pkg, 'download', true)
    try {
      const blob = await downloadApk(deviceId, pkg)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${pkg}.apk`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
      showSnackbar(`APK ${t.messages.completed}: ${pkg}.apk`)
    } catch (e: any) {
      showSnackbar(e?.message || 'Download failed', 'error')
    } finally {
      setAppActionLoading(pkg, 'download', false)
    }
  }

  const handleAppVersion = async (pkg: string) => {
    if (!deviceId) return
    setAppActionLoading(pkg, 'version', true)
    try {
      const res = await getAppVersion(deviceId, pkg)
      if (res.success) {
        const info = JSON.parse(res.output)
        setApps((prev) =>
          prev.map((a) =>
            a.package_name === pkg
              ? {
                  ...a,
                  version_name: info.version_name,
                  version_code: info.version_code?.toString(),
                }
              : a,
          ),
        )
        showSnackbar(
          t.apps.versionInfo
            .replace('{name}', info.version_name)
            .replace('{code}', info.version_code?.toString() || ''),
        )
      } else {
        showSnackbar(`${t.apps.getVersionFailed}: ${res.error}`, 'error')
      }
    } catch (e: any) {
      showSnackbar(`${t.apps.getVersionFailed}: ${e.message}`, 'error')
    } finally {
      setAppActionLoading(pkg, 'version', false)
    }
  }

  const handleAppStart = async (pkg: string) => {
    if (!deviceId) return
    setAppActionLoading(pkg, 'start', true)
    try {
      const res = await startApp(deviceId, pkg)
      if (res.success) {
        showSnackbar(`${t.apps.startSuccess}: ${pkg}`)
      } else {
        showSnackbar(`${t.apps.startFailed}: ${res.error}`, 'error')
      }
    } catch (e: any) {
      showSnackbar(`${t.apps.startFailed}: ${e.message}`, 'error')
    } finally {
      setAppActionLoading(pkg, 'start', false)
    }
  }

  const handleAppStop = async (pkg: string) => {
    if (!deviceId) return
    setAppActionLoading(pkg, 'stop', true)
    try {
      const res = await stopApp(deviceId, pkg)
      if (res.success) {
        showSnackbar(`${t.apps.stopSuccess}: ${pkg}`)
      } else {
        showSnackbar(`${t.apps.stopFailed}: ${res.error}`, 'error')
      }
    } catch (e: any) {
      showSnackbar(`${t.apps.stopFailed}: ${e.message}`, 'error')
    } finally {
      setAppActionLoading(pkg, 'stop', false)
    }
  }

  const handleAppClearData = async (pkg: string) => {
    if (!deviceId) return
    setAppActionLoading(pkg, 'clear', true)
    try {
      const res = await clearAppData(deviceId, pkg)
      if (res.success) {
        showSnackbar(`${t.apps.clearDataSuccess}: ${pkg}`)
      } else {
        showSnackbar(`${t.apps.clearDataFailed}: ${res.error}`, 'error')
      }
    } catch (e: any) {
      showSnackbar(`${t.apps.clearDataFailed}: ${e.message}`, 'error')
    } finally {
      setAppActionLoading(pkg, 'clear', false)
    }
  }

  const handleAppUninstall = async (pkg: string) => {
    if (!deviceId) return
    setAppActionLoading(pkg, 'uninstall', true)
    try {
      const res = await uninstallApp(deviceId, pkg)
      if (res.success) {
        showSnackbar(`${t.apps.uninstallSuccess}: ${pkg}`)
        setApps((prev) => prev.filter((a) => a.package_name !== pkg))
      } else {
        showSnackbar(`${t.apps.uninstallFailed}: ${res.error}`, 'error')
      }
    } catch (e: any) {
      showSnackbar(`${t.apps.uninstallFailed}: ${e.message}`, 'error')
    } finally {
      setAppActionLoading(pkg, 'uninstall', false)
    }
  }

  // ==================== 修改配置 ====================
  const handleModifyConfig = async () => {
    if (!requireDevice()) return
    if (!configKey.trim() || !configValue.trim()) {
      showSnackbar(t.devices.enterConfigKeyValue, 'warning')
      return
    }
    setActionLoading('modify-config')
    try {
      const res = await modifyDeviceConfig(
        deviceId!,
        configPath.trim(),
        configKey.trim(),
        configValue.trim(),
      )
      if (res.success) {
        showSnackbar(t.devices.modifyConfigSuccess)
        configPathHistoryRef.current?.commit()
        configKeyHistoryRef.current?.commit()
        configValueHistoryRef.current?.commit()
        setConfigPath('')
        setConfigKey('')
        setConfigValue('')
        setConfigDialogOpen(false)
      } else {
        showSnackbar(`${t.devices.modifyConfigFailed}: ${res.error}`, 'error')
      }
    } catch (e: any) {
      showSnackbar(`${t.devices.modifyConfigFailed}: ${e.message}`, 'error')
    } finally {
      setActionLoading(null)
    }
  }

  // ==================== 复制 ====================
  const handleCopyText = async (text: string) => {
    if (!text) return
    const ok = await copyToClipboard(text)
    showSnackbar(ok ? t.messages.copySuccess : t.messages.copyFailed, ok ? 'success' : 'error')
  }

  // ==================== 设备信息字段 ====================
  const deviceInfoRows: Array<{ label: string; value?: string; mono?: boolean }> =
    selectedDevice
      ? [
          { label: t.devices.deviceId, value: selectedDevice.device_id, mono: true },
          { label: t.devices.model, value: selectedDevice.model },
          { label: t.devices.androidVersion, value: selectedDevice.android_version },
          { label: t.devices.sdkVersion, value: selectedDevice.sdk_version },
          { label: t.screen.resolution, value: selectedDevice.resolution },
          { label: t.devices.density, value: selectedDevice.density },
          {
            label: t.devices.buildFingerprint,
            value: selectedDevice.build_fingerprint,
            mono: true,
          },
        ]
      : []

  // ==================== 渲染 ====================
  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        gap: 1,
        // 用 flex: 1 继承父容器（main）的剩余高度
        // 不用 100vh 减固定值，这样 zoom 缩放后高度也能正确响应
        flex: 1,
        minHeight: 0,
        overflow: 'hidden',
      }}
    >
      {/* ==================== 顶部：连接条 + 设备列表 ==================== */}
      <Paper sx={{ ...cardSx, p: 1, flexShrink: 0 }}>
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 1,
            flexWrap: { xs: 'wrap', md: 'nowrap' },
          }}
        >
          {/* 连接表单 */}
          <Box
            component="form"
            onSubmit={handleConnect}
            sx={{ display: 'flex', alignItems: 'center', gap: 0.75, flexShrink: 0 }}
          >
            <CableIcon sx={{ color: '#6366f1', fontSize: 20 }} />
            <Box sx={{ width: 320 }}>
              <HistoryTextField
                ref={ipHistoryRef}
                historyKey={HK_IP}
                value={ip}
                onChange={setIp}
                placeholder="192.168.1.100"
                disabled={connecting}
                size="small"
                inputSx={inputSx}
              />
            </Box>
            <Box sx={{ width: 100 }}>
              <HistoryTextField
                ref={portHistoryRef}
                historyKey={HK_PORT}
                value={port}
                onChange={setPort}
                placeholder="5555"
                disabled={connecting}
                size="small"
                inputSx={inputSx}
              />
            </Box>
            <Button
              type="submit"
              variant="contained"
              disabled={connecting || !ip}
              startIcon={
                connecting ? (
                  <CircularProgress size={14} color="inherit" />
                ) : (
                  <AddIcon sx={{ fontSize: 18 }} />
                )
              }
              sx={{
                py: 0.85,
                px: 1.75,
                fontSize: '0.88rem',
                minHeight: 36,
                cursor: 'pointer',
                bgcolor: '#6366f1',
                boxShadow: '0 2px 6px rgba(99, 102, 241, 0.25)',
                '&:hover': {
                  bgcolor: '#4f46e5',
                  boxShadow: '0 4px 10px rgba(99, 102, 241, 0.35)',
                },
              }}
            >
              {connecting ? t.devices.connecting : t.devices.connect}
            </Button>
          </Box>

          <Divider orientation="vertical" flexItem sx={{ mx: 0.5 }} />

          {/* 设备列表 - 横向 chips */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75, flex: 1, minWidth: 0 }}>
            <Tooltip title={t.devices.refreshDevices}>
              <span>
                <IconButton
                  size="small"
                  onClick={fetchDevices}
                  disabled={fetchingDevices}
                  sx={{ cursor: 'pointer', color: '#64748b' }}
                >
                  {fetchingDevices ? (
                    <CircularProgress size={16} />
                  ) : (
                    <RefreshIcon sx={{ fontSize: 18 }} />
                  )}
                </IconButton>
              </span>
            </Tooltip>

            <Box
              sx={{
                display: 'flex',
                gap: 0.5,
                overflowX: 'auto',
                flex: 1,
                minWidth: 0,
                pb: 0.5,
                '&::-webkit-scrollbar': { height: 4 },
                '&::-webkit-scrollbar-thumb': {
                  bgcolor: '#cbd5e1',
                  borderRadius: 2,
                },
              }}
            >
              {devices.length === 0 ? (
                <Chip
                  size="small"
                  label={t.devices.noDevices}
                  sx={{
                    fontSize: '0.82rem',
                    bgcolor: '#f1f5f9',
                    color: '#64748b',
                    fontWeight: 500,
                  }}
                />
              ) : (
                devices.map((d) => {
                  const active = d.device_id === deviceId
                  const dOnline = d.status === 'device'
                  return (
                    <Chip
                      key={d.device_id}
                      size="small"
                      onClick={() => selectDevice(d)}
                      onDelete={() => handleDisconnect(d.device_id)}
                      deleteIcon={<CloseIcon sx={{ fontSize: 14 }} />}
                      label={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          <Box
                            sx={{
                              width: 6,
                              height: 6,
                              borderRadius: '50%',
                              bgcolor: dOnline ? '#10b981' : '#ef4444',
                              flexShrink: 0,
                            }}
                          />
                          <Typography
                            sx={{
                              fontSize: '0.82rem',
                              fontWeight: active ? 600 : 500,
                              maxWidth: 180,
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                            }}
                          >
                            {d.model || d.device_id}
                          </Typography>
                        </Box>
                      }
                      sx={{
                        cursor: 'pointer',
                        height: 28,
                        bgcolor: active ? '#eef2ff' : 'rgba(255,255,255,0.7)',
                        backdropFilter: 'blur(4px)',
                        border: '1px solid',
                        borderColor: active ? '#6366f1' : '#e2e8f0',
                        color: active ? '#4f46e5' : '#0f172a',
                        '&:hover': {
                          bgcolor: active ? '#e0e7ff' : '#f8fafc',
                          borderColor: '#6366f1',
                        },
                        '& .MuiChip-deleteIcon': {
                          color: '#94a3b8',
                          '&:hover': { color: '#ef4444' },
                        },
                      }}
                    />
                  )
                })
              )}
            </Box>
          </Box>

          {/* 全局操作 */}
          <Box sx={{ display: 'flex', gap: 0.5, flexShrink: 0 }}>
            <Button
              size="small"
              variant="outlined"
              onClick={handleRestartAdb}
              disabled={actionLoading === 'restart-adb'}
              startIcon={
                actionLoading === 'restart-adb' ? (
                  <CircularProgress size={12} />
                ) : (
                  <RefreshIcon sx={{ fontSize: 16 }} />
                )
              }
              sx={glassBtnSx}
            >
              {t.devices.restartAdb}
            </Button>
            <Tooltip title={t.settings.title}>
              <IconButton
                size="small"
                onClick={() => navigate('/settings')}
                sx={{ cursor: 'pointer', color: '#64748b' }}
              >
                <SettingsIcon sx={{ fontSize: 18 }} />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>
      </Paper>

      {/* ==================== 主体：左 设备信息 / 右 操作 + 应用 ==================== */}
      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: '1fr', md: '320px 1fr' },
          gridTemplateRows: '1fr',  // 让行高撑满 flex 分配的高度
          gap: 1,
          flex: 1,
          minHeight: 0,
          overflow: 'hidden',
        }}
      >
        {/* ----- 左栏：设备信息 + 快捷按钮 ----- */}
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            gap: 1,
            minHeight: 0,
            height: '100%',  // 撑满 grid 分配的行高
          }}
        >
          <Paper
            sx={{
              ...cardSx,
              overflow: 'auto',
              minHeight: 0,
            }}
          >
          <Box sx={sectionTitleSx}>
            <InfoIcon />
            {t.devices.deviceInfo}
          </Box>

          {!selectedDevice ? (
            <Box
              sx={{
                py: 3,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: 1,
                color: '#94a3b8',
                textAlign: 'center',
              }}
            >
              <InfoIcon sx={{ fontSize: 36, opacity: 0.4 }} />
              <Typography sx={{ fontSize: '0.95rem' }}>
                {t.devices.pleaseSelectDevice}
              </Typography>
              <Typography sx={{ fontSize: '0.85rem', opacity: 0.8 }}>
                {t.messages.adbSetupInfo}
              </Typography>
            </Box>
          ) : (
            <Stack spacing={0.75}>
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1,
                  p: 1,
                  bgcolor: '#f8fafc',
                  borderRadius: 1,
                  border: '1px solid #e2e8f0',
                }}
              >
                <Box
                  sx={{
                    width: 8,
                    height: 8,
                    borderRadius: '50%',
                    bgcolor: isOnline ? '#10b981' : '#ef4444',
                  }}
                />
                <Typography
                  sx={{ fontSize: '0.88rem', fontWeight: 600, color: '#0f172a' }}
                >
                  {isOnline ? t.devices.online : t.devices.offline}
                </Typography>
                <Box sx={{ flex: 1 }} />
                {selectedDevice.model && (
                  <Typography sx={{ fontSize: '0.82rem', color: '#64748b' }}>
                    {selectedDevice.model}
                  </Typography>
                )}
              </Box>

              {deviceInfoRows.map(
                (row) =>
                  row.value && (
                    <Box
                      key={row.label}
                      sx={{
                        display: 'flex',
                        flexDirection: 'column',
                        gap: 0.25,
                        py: 0.5,
                        borderBottom: '1px solid #f1f5f9',
                      }}
                    >
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        <Typography
                          sx={{
                            fontSize: '0.85rem',
                            color: '#64748b',
                            fontWeight: 600,
                            textTransform: 'uppercase',
                            letterSpacing: '0.03em',
                            flex: 1,
                          }}
                        >
                          {row.label}
                        </Typography>
                        <IconButton
                          size="small"
                          onClick={() => handleCopyText(row.value || '')}
                          sx={{ cursor: 'pointer', p: 0.25, color: '#cbd5e1' }}
                        >
                          <CopyIcon sx={{ fontSize: 14 }} />
                        </IconButton>
                      </Box>
                      <Typography
                        sx={{
                          fontSize: '0.85rem',
                          color: '#0f172a',
                          wordBreak: 'break-all',
                          fontFamily: row.mono
                            ? 'ui-monospace, SFMono-Regular, monospace'
                            : 'inherit',
                          lineHeight: 1.4,
                        }}
                      >
                        {row.value}
                      </Typography>
                    </Box>
                  ),
              )}
            </Stack>
          )}
        </Paper>

        {/* 快捷自定义按钮 */}
        <Paper
          sx={{
            ...cardSx,
            flex: 1,
            minHeight: 0,
            p: 1.25,
            overflow: 'hidden',
          }}
        >
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 0.5,
              mb: 0.75,
              flexShrink: 0,
            }}
          >
            <TouchAppIcon sx={{ fontSize: 18, color: '#6366f1' }} />
            <Typography
              sx={{ fontSize: '0.88rem', fontWeight: 700, color: '#0f172a' }}
            >
              {t.customButtons.title}
            </Typography>
            <Typography
              sx={{ fontSize: '0.78rem', color: '#94a3b8', ml: 0.25 }}
            >
              ({topCustomButtons.length})
            </Typography>
            <Box sx={{ flex: 1 }} />
            <Tooltip title={t.common.edit}>
              <IconButton
                size="small"
                onClick={() => setShowCustomButtonsPanel(true)}
                sx={{
                  p: 0.25,
                  color: '#94a3b8',
                  '&:hover': { color: '#6366f1' },
                }}
              >
                <ChevronRightIcon sx={{ fontSize: 16 }} />
              </IconButton>
            </Tooltip>
          </Box>

          {topCustomButtons.length === 0 ? (
            <Box
              sx={{
                flex: 1,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 0.75,
                color: '#94a3b8',
                textAlign: 'center',
                px: 1,
              }}
            >
              <Typography sx={{ fontSize: '0.88rem' }}>
                {t.customButtons.noButtons}
              </Typography>
              <Button
                size="small"
                variant="outlined"
                startIcon={<AddIcon sx={{ fontSize: 14 }} />}
                onClick={() => setShowCustomButtonsPanel(true)}
                sx={glassBtnSx}
              >
                {t.customButtons.addButton}
              </Button>
            </Box>
          ) : (
            <Box
              sx={{
                flex: 1,
                minHeight: 0,
                overflow: 'auto',
                pr: 0.25,
                '&::-webkit-scrollbar': { width: 4 },
                '&::-webkit-scrollbar-thumb': {
                  bgcolor: '#cbd5e1',
                  borderRadius: 2,
                },
              }}
            >
              <Stack spacing={0.5}>
                {topCustomButtons.map((btn) => (
                  <Tooltip
                    key={btn.id}
                    title={btn.command}
                    placement="right"
                    enterDelay={500}
                  >
                    <Button
                      size="small"
                      variant="outlined"
                      fullWidth
                      onClick={() => handleQuickExecuteCustomButton(btn)}
                      disabled={executingCustomBtn === btn.id}
                      startIcon={
                        executingCustomBtn === btn.id ? (
                          <CircularProgress size={12} />
                        ) : (
                          <PlayIcon sx={{ fontSize: 14 }} />
                        )
                      }
                      sx={{
                        ...glassBtnSx,
                        justifyContent: 'flex-start',
                        '& .MuiButton-startIcon': {
                          color: '#10b981',
                          mr: 0.75,
                        },
                        '&:hover .MuiButton-startIcon': { color: '#059669' },
                      }}
                    >
                      <Box
                        component="span"
                        sx={{
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                          flex: 1,
                          textAlign: 'left',
                        }}
                      >
                        {btn.name}
                      </Box>
                    </Button>
                  </Tooltip>
                ))}
              </Stack>
            </Box>
          )}
        </Paper>
        </Box>

        {/* ----- 右栏 ----- */}
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            gap: 1,
            minWidth: 0,
            minHeight: 0,
            height: '100%',  // 撑满 grid 分配的行高
            overflow: 'hidden auto',
            pr: 0.5,
            // 自定义滚动条样式
            '&::-webkit-scrollbar': { width: 5 },
            '&::-webkit-scrollbar-thumb': {
              bgcolor: 'rgba(203, 213, 225, 0.7)',
              borderRadius: 3,
            },
            '&::-webkit-scrollbar-track': { bgcolor: 'transparent' },
          }}
        >
          {showCustomButtonsPanel ? (
            <Fade in timeout={250}>
              <Box sx={{ flex: 1, minHeight: 0, display: 'flex' }}>
                <CustomButtonsPanel
                  onBack={() => setShowCustomButtonsPanel(false)}
                />
              </Box>
            </Fade>
          ) : (
          <>
          {/* 信息查询 */}
          <Paper sx={{ ...cardSx }}>
            <Box sx={sectionTitleSx}>
              <InfoIcon />
              信息查询
            </Box>
            <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
              <Button
                variant="outlined"
                size="small"
                startIcon={
                  actionLoading === 'basic-info' ? (
                    <CircularProgress size={12} />
                  ) : (
                    <InfoIcon sx={{ fontSize: 16 }} />
                  )
                }
                onClick={handleBasicInfo}
                disabled={!isOnline || actionLoading === 'basic-info'}
                sx={glassBtnSx}
              >
                {t.devices.basicInfo}
              </Button>
              <Button
                variant="outlined"
                size="small"
                startIcon={
                  actionLoading === 'whaleos-info' ? (
                    <CircularProgress size={12} />
                  ) : (
                    <MemoryIcon sx={{ fontSize: 16 }} />
                  )
                }
                onClick={handleWhaleOSInfo}
                disabled={!isOnline || actionLoading === 'whaleos-info'}
                sx={glassBtnSx}
              >
                {t.devices.whaleOSInfo}
              </Button>
              <Button
                variant="outlined"
                size="small"
                startIcon={
                  actionLoading === 'firmware-info' ? (
                    <CircularProgress size={12} />
                  ) : (
                    <StorageIcon sx={{ fontSize: 16 }} />
                  )
                }
                onClick={handleFirmwareInfo}
                disabled={!isOnline || actionLoading === 'firmware-info'}
                sx={glassBtnSx}
              >
                {t.devices.aospInfo}
              </Button>
              <Button
                variant="outlined"
                size="small"
                startIcon={
                  actionLoading === 'check-keys' ? (
                    <CircularProgress size={12} />
                  ) : (
                    <SecurityIcon sx={{ fontSize: 16 }} />
                  )
                }
                onClick={handleCheckKeys}
                disabled={!isOnline || actionLoading === 'check-keys'}
                sx={glassBtnSx}
              >
                {t.devices.checkKeys}
              </Button>
            </Box>
          </Paper>

          {/* 设备控制 */}
          <Paper sx={{ ...cardSx }}>
            <Box sx={sectionTitleSx}>
              <PowerIcon />
              {t.devices.deviceControl}
            </Box>

            {/* 输入文本 */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75, mb: 1 }}>
              <HistoryTextField
                ref={textHistoryRef}
                historyKey={HK_TEXT}
                value={textInput}
                onChange={setTextInput}
                placeholder={t.devices.enterTextToSend}
                disabled={!isOnline || actionLoading === 'send-text'}
                onEnter={handleSendText}
                startAdornment={
                  <SendIcon sx={{ fontSize: 16, color: '#94a3b8', mr: 0.75 }} />
                }
                inputSx={inputSx}
                sx={{ maxWidth: 380 }}
              />
              <Button
                variant="contained"
                size="small"
                onClick={handleSendText}
                disabled={!isOnline || !textInput.trim() || actionLoading === 'send-text'}
                startIcon={
                  actionLoading === 'send-text' ? (
                    <CircularProgress size={14} color="inherit" />
                  ) : (
                    <ReturnIcon sx={{ fontSize: 16 }} />
                  )
                }
                sx={{
                  fontSize: '0.88rem',
                  minHeight: 36,
                  px: 1.75,
                  cursor: 'pointer',
                  whiteSpace: 'nowrap',
                  bgcolor: '#6366f1',
                  boxShadow: '0 2px 6px rgba(99, 102, 241, 0.25)',
                  '&:hover': {
                    bgcolor: '#4f46e5',
                    boxShadow: '0 4px 10px rgba(99, 102, 241, 0.35)',
                  },
                }}
              >
                {t.devices.sendText}
              </Button>
            </Box>

            {/* 控制按钮 */}
            <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
              <Button
                variant="outlined"
                size="small"
                startIcon={
                  actionLoading === 'reboot' ? (
                    <CircularProgress size={12} />
                  ) : (
                    <RestartIcon sx={{ fontSize: 16 }} />
                  )
                }
                onClick={handleReboot}
                disabled={!isOnline || actionLoading === 'reboot'}
                sx={glassBtnSx}
              >
                {t.devices.rebootDevice}
              </Button>
              <Button
                variant="outlined"
                size="small"
                startIcon={
                  actionLoading === 'root' ? (
                    <CircularProgress size={12} />
                  ) : (
                    <SecurityIcon sx={{ fontSize: 16 }} />
                  )
                }
                onClick={handleRoot}
                disabled={!isOnline || actionLoading === 'root'}
                sx={glassBtnSx}
              >
                Root
              </Button>
              <Button
                variant="outlined"
                size="small"
                startIcon={
                  actionLoading === 'remount' ? (
                    <CircularProgress size={12} />
                  ) : (
                    <SecurityIcon sx={{ fontSize: 16 }} />
                  )
                }
                onClick={handleRemount}
                disabled={!isOnline || actionLoading === 'remount'}
                sx={glassBtnSx}
              >
                Remount
              </Button>
              <Button
                variant="outlined"
                size="small"
                startIcon={
                  actionLoading === 'screenshot' ? (
                    <CircularProgress size={12} />
                  ) : (
                    <CameraIcon sx={{ fontSize: 16 }} />
                  )
                }
                onClick={handleQuickScreenshot}
                disabled={!isOnline || actionLoading === 'screenshot'}
                sx={glassBtnSx}
              >
                {t.screen.screenshot}
              </Button>
              {recordingSession ? (
                <Button
                  variant="contained"
                  size="small"
                  startIcon={
                    actionLoading === 'stop-recording' ? (
                      <CircularProgress size={12} color="inherit" />
                    ) : (
                      <StopIcon sx={{ fontSize: 16 }} />
                    )
                  }
                  onClick={handleStopRecording}
                  disabled={actionLoading === 'stop-recording'}
                  sx={activeRecordingBtnSx}
                >
                  {t.screen.stopRecord} {formatDuration(recordingElapsed)}
                </Button>
              ) : (
                <Button
                  variant="outlined"
                  size="small"
                  startIcon={
                    actionLoading === 'start-recording' ? (
                      <CircularProgress size={12} />
                    ) : (
                      <RecordIcon sx={{ fontSize: 16, color: '#ef4444' }} />
                    )
                  }
                  onClick={handleStartRecording}
                  disabled={!isOnline || actionLoading === 'start-recording'}
                  sx={{
                    ...glassBtnSx,
                    '& .MuiButton-startIcon': { color: '#ef4444', mr: 0.5 },
                  }}
                >
                  {t.screen.startRecord}
                </Button>
              )}
              <Button
                variant="outlined"
                size="small"
                startIcon={<ScreenshotIcon sx={{ fontSize: 16 }} />}
                onClick={() => navigate('/screen')}
                sx={glassBtnSx}
              >
                屏幕镜像 & 遥控器
              </Button>
            </Box>
          </Paper>

          {/* 日志采集 */}
          <Paper sx={{ ...cardSx }}>
            <Box sx={sectionTitleSx}>
              <ArticleIcon />
              {t.logs.title}
            </Box>
            <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
              {logcatSession ? (
                <Button
                  variant="contained"
                  size="small"
                  startIcon={
                    actionLoading === 'stop-logcat' ? (
                      <CircularProgress size={12} color="inherit" />
                    ) : (
                      <StopIcon sx={{ fontSize: 16 }} />
                    )
                  }
                  onClick={handleStopLogcat}
                  disabled={actionLoading === 'stop-logcat'}
                  sx={activePrimaryBtnSx}
                >
                  {t.logs.stopCapture}
                </Button>
              ) : (
                <Button
                  variant="outlined"
                  size="small"
                  startIcon={
                    actionLoading === 'start-logcat' ? (
                      <CircularProgress size={12} />
                    ) : (
                      <PlayIcon sx={{ fontSize: 16 }} />
                    )
                  }
                  onClick={handleStartLogcat}
                  disabled={!isOnline || actionLoading === 'start-logcat'}
                  sx={glassBtnSx}
                >
                  {t.logs.realtimeLog}
                </Button>
              )}

              {diagnosticSession ? (
                <Button
                  variant="contained"
                  size="small"
                  startIcon={
                    actionLoading === 'stop-diag' ? (
                      <CircularProgress size={12} color="inherit" />
                    ) : (
                      <StopIcon sx={{ fontSize: 16 }} />
                    )
                  }
                  onClick={handleStopDiagnostic}
                  disabled={actionLoading === 'stop-diag'}
                  sx={activeDiagBtnSx}
                >
                  {t.logs.stopCapture} ({diagnosticElapsed}s)
                </Button>
              ) : (
                <Button
                  variant="outlined"
                  size="small"
                  startIcon={
                    actionLoading === 'start-diag' ? (
                      <CircularProgress size={12} />
                    ) : (
                      <DownloadIcon sx={{ fontSize: 16 }} />
                    )
                  }
                  onClick={handleStartDiagnostic}
                  disabled={!isOnline || actionLoading === 'start-diag'}
                  sx={glassBtnSx}
                >
                  {t.logs.captureDiagnosticPackage}
                </Button>
              )}

              {bootLogcatSession ? (
                <Button
                  variant="contained"
                  size="small"
                  startIcon={
                    actionLoading === 'stop-boot' ? (
                      <CircularProgress size={12} color="inherit" />
                    ) : (
                      <StopIcon sx={{ fontSize: 16 }} />
                    )
                  }
                  onClick={handleStopBootLogcat}
                  disabled={actionLoading === 'stop-boot'}
                  sx={activePrimaryBtnSx}
                >
                  {t.logs.stopCapture}
                  {` (${bootElapsed}s)`}
                </Button>
              ) : (
                <Button
                  variant="outlined"
                  size="small"
                  startIcon={
                    actionLoading === 'start-boot' ? (
                      <CircularProgress size={12} />
                    ) : (
                      <ArticleIcon sx={{ fontSize: 16 }} />
                    )
                  }
                  onClick={handleStartBootLogcat}
                  disabled={actionLoading === 'start-boot'}
                  sx={glassBtnSx}
                >
                  {t.logs.bootLogcat}
                </Button>
              )}

              <Button
                variant="outlined"
                size="small"
                startIcon={
                  actionLoading === 'clear-logcat' ? (
                    <CircularProgress size={12} />
                  ) : (
                    <ClearIcon sx={{ fontSize: 16 }} />
                  )
                }
                onClick={handleClearLogcat}
                disabled={!isOnline || actionLoading === 'clear-logcat'}
                sx={dangerGlassBtnSx}
              >
                {t.logs.clearDeviceLog}
              </Button>
            </Box>
          </Paper>

          {/* 其他操作 */}
          <Paper sx={{ ...cardSx }}>
            <Box sx={sectionTitleSx}>
              <ExtensionIcon />
              {t.devices.otherOperations}
            </Box>
            <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
              <Button
                variant="outlined"
                size="small"
                startIcon={<TouchAppIcon sx={{ fontSize: 16 }} />}
                onClick={() => setShowCustomButtonsPanel(true)}
                sx={glassBtnSx}
              >
                {t.customButtons.title}
              </Button>
              <Button
                variant="outlined"
                size="small"
                startIcon={<TuneIcon sx={{ fontSize: 16 }} />}
                onClick={() => setConfigDialogOpen(true)}
                disabled={!isOnline}
                sx={glassBtnSx}
              >
                {t.devices.modifyConfig}
              </Button>
            </Box>
          </Paper>

          {/* 应用管理 - 占据剩余空间 */}
          <Paper
            sx={{
              ...cardSx,
              flex: 1,
              minHeight: 0,
              overflow: 'hidden',
            }}
          >
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 1,
                mb: 1,
                flexWrap: 'wrap',
              }}
            >
              <Box sx={{ ...sectionTitleSx, mb: 0 }}>
                <AppsIcon />
                {t.apps.title}
              </Box>
              <FormControlLabel
                control={
                  <Switch
                    checked={includeSystem}
                    onChange={(e) => setIncludeSystem(e.target.checked)}
                    size="small"
                  />
                }
                label={
                  <Typography sx={{ fontSize: '0.88rem', color: '#475569' }}>
                    {t.apps.showSystemApps}
                  </Typography>
                }
                sx={{ m: 0 }}
              />
              <Tooltip title={t.apps.refreshApps}>
                <span>
                  <IconButton
                    size="small"
                    onClick={() => loadApps()}
                    disabled={appsLoading || !deviceId}
                    sx={{ cursor: 'pointer', color: '#64748b' }}
                  >
                    {appsLoading ? (
                      <CircularProgress size={14} />
                    ) : (
                      <RefreshIcon sx={{ fontSize: 16 }} />
                    )}
                  </IconButton>
                </span>
              </Tooltip>
            </Box>

            {/* 上传 / 当前应用 / 路径查询 */}
            <Box
              sx={{
                display: 'grid',
                gridTemplateColumns: { xs: '1fr', md: '160px auto 1fr' },
                gap: 0.75,
                mb: 1,
              }}
            >
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'stretch',
                  gap: 0,
                  borderRadius: '8px',
                  border: '1px solid rgba(226, 232, 240, 0.8)',
                  bgcolor: 'rgba(255, 255, 255, 0.6)',
                  backdropFilter: 'blur(8px)',
                  WebkitBackdropFilter: 'blur(8px)',
                  boxShadow: '0 1px 2px rgba(15, 23, 42, 0.03)',
                  overflow: 'hidden',
                  transition: 'all 0.15s',
                  '&:hover': {
                    borderColor: '#6366f1',
                    boxShadow: '0 4px 10px rgba(99, 102, 241, 0.12)',
                  },
                }}
              >
                <Button
                  size="small"
                  onClick={handleSelectApk}
                  disabled={!isOnline || actionLoading === 'install-apk'}
                  startIcon={
                    actionLoading === 'install-apk' ? (
                      <CircularProgress size={12} />
                    ) : (
                      <UploadIcon sx={{ fontSize: 16 }} />
                    )
                  }
                  sx={{
                    flex: 1,
                    py: 0.5,
                    px: 1,
                    fontSize: '0.85rem',
                    fontWeight: 500,
                    textTransform: 'none',
                    minHeight: 34,
                    color: '#475569',
                    bgcolor: 'transparent',
                    borderRadius: 0,
                    cursor: 'pointer',
                    '& .MuiButton-startIcon': { color: '#6366f1', mr: 0.5 },
                    '&:hover': {
                      bgcolor: 'rgba(238, 242, 255, 0.5)',
                      color: '#4f46e5',
                    },
                    '&:hover .MuiButton-startIcon': { color: '#4f46e5' },
                    '&.Mui-disabled': { color: '#cbd5e1' },
                  }}
                >
                  {t.apps.installApk}
                </Button>
                <Tooltip
                  title={
                    reinstallApk
                      ? `${t.apps.reinstall}（adb install -r）`
                      : '普通安装（adb install）'
                  }
                  placement="top"
                >
                  <Box
                    component="button"
                    type="button"
                    onClick={() => setReinstallApk((v) => !v)}
                    disabled={actionLoading === 'install-apk'}
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 0.4,
                      px: 1,
                      borderLeft: '1px solid rgba(226, 232, 240, 0.8)',
                      bgcolor: reinstallApk
                        ? 'rgba(99, 102, 241, 0.08)'
                        : 'transparent',
                      color: reinstallApk ? '#4f46e5' : '#94a3b8',
                      fontSize: '0.78rem',
                      fontWeight: 600,
                      border: 'none',
                      cursor:
                        actionLoading === 'install-apk' ? 'not-allowed' : 'pointer',
                      transition: 'all 0.15s',
                      whiteSpace: 'nowrap',
                      '&:hover': {
                        bgcolor: reinstallApk
                          ? 'rgba(99, 102, 241, 0.14)'
                          : 'rgba(248, 250, 252, 0.8)',
                      },
                    }}
                  >
                    {reinstallApk ? (
                      <CheckBoxIcon sx={{ fontSize: 14 }} />
                    ) : (
                      <CheckBoxOutlineBlankIcon sx={{ fontSize: 14 }} />
                    )}
                    覆盖
                  </Box>
                </Tooltip>
              </Box>
              <input
                ref={apkInputRef}
                type="file"
                accept=".apk"
                hidden
                onChange={handleApkChange}
              />
              <Button
                variant="outlined"
                size="small"
                startIcon={
                  actionLoading === 'current-app' ? (
                    <CircularProgress size={10} />
                  ) : (
                    <VisibilityIcon sx={{ fontSize: 13 }} />
                  )
                }
                onClick={handleGetCurrentApp}
                disabled={!isOnline || actionLoading === 'current-app'}
                sx={{
                  ...glassBtnSx,
                  py: 0.2,
                  px: 0.75,
                  fontSize: '0.72rem',
                  minHeight: 24,
                  '& .MuiButton-startIcon': { color: '#6366f1', mr: 0.3 },
                }}
              >
                {currentApp ? `${t.apps.getCurrentApp}: ${currentApp}` : t.apps.getCurrentApp}
              </Button>
              <Box sx={{ display: 'flex', gap: 0.5, maxWidth: 440 }}>
                <HistoryTextField
                  ref={pkgQueryHistoryRef}
                  historyKey={HK_PKG_QUERY}
                  value={queryPackage}
                  onChange={setQueryPackage}
                  placeholder={t.apps.enterPackageName}
                  disabled={!isOnline}
                  onEnter={handleGetAppPath}
                  inputSx={{
                    ...inputSx,
                    '& .MuiInputBase-input': { fontSize: '0.72rem', py: 0.35 },
                  }}
                />
                <Button
                  variant="outlined"
                  size="small"
                  onClick={handleGetAppPath}
                  disabled={!isOnline || !queryPackage.trim() || actionLoading === 'app-path'}
                  startIcon={
                    actionLoading === 'app-path' ? (
                      <CircularProgress size={10} />
                    ) : (
                      <FolderIcon sx={{ fontSize: 13 }} />
                    )
                  }
                  sx={{
                    ...glassBtnSx,
                    py: 0.2,
                    px: 0.75,
                    fontSize: '0.72rem',
                    minHeight: 24,
                    flexShrink: 0,
                    '& .MuiButton-startIcon': { color: '#6366f1', mr: 0.3 },
                  }}
                >
                  {t.apps.getAppPath}
                </Button>
              </Box>
            </Box>
            {appPath && (
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 0.5,
                  px: 0.75,
                  py: 0.5,
                  mb: 1,
                  bgcolor: '#f8fafc',
                  borderRadius: 1,
                  border: '1px solid #e2e8f0',
                }}
              >
                <Typography
                  sx={{
                    fontSize: '0.82rem',
                    fontFamily: 'ui-monospace, SFMono-Regular, monospace',
                    color: '#0f172a',
                    flex: 1,
                    wordBreak: 'break-all',
                  }}
                >
                  {appPath}
                </Typography>
                <IconButton
                  size="small"
                  onClick={() => handleCopyText(appPath)}
                  sx={{ cursor: 'pointer', p: 0.25, color: '#64748b' }}
                >
                  <CopyIcon sx={{ fontSize: 12 }} />
                </IconButton>
              </Box>
            )}

            {/* 已安装应用 */}
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 1,
                mb: 0.75,
              }}
            >
              <Typography sx={{ fontSize: '0.92rem', fontWeight: 600, color: '#0f172a' }}>
                {t.apps.installedApps}
              </Typography>
              <Typography sx={{ fontSize: '0.82rem', color: '#94a3b8' }}>
                ({filteredApps.length})
              </Typography>
              <HistoryTextField
                ref={appSearchHistoryRef}
                historyKey={HK_APP_SEARCH}
                value={appSearch}
                onChange={(v) => {
                  setAppSearch(v)
                  setAppPage(1)
                }}
                placeholder={t.apps.searchApps}
                size="small"
                startAdornment={
                  <SearchIcon sx={{ fontSize: 16, color: '#94a3b8' }} />
                }
                inputSx={{
                  ...inputSx,
                  '& .MuiInputBase-input': { fontSize: '0.88rem', py: 0.65 },
                }}
                onBlur={() => appSearchHistoryRef.current?.commit()}
                sx={{ width: 320 }}
              />
            </Box>

            <Box
              sx={{
                flex: 1,
                minHeight: 0,
                overflow: 'auto',
                border: '1px solid rgba(241, 245, 249, 0.9)',
                borderRadius: 1.5,
                bgcolor: 'rgba(255, 255, 255, 0.5)',
              }}
            >
              {appsLoading ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', py: 3 }}>
                  <CircularProgress size={20} />
                </Box>
              ) : currentPageApps.length === 0 ? (
                <Box sx={{ textAlign: 'center', py: 3 }}>
                  <Typography sx={{ fontSize: '0.8rem', color: '#94a3b8' }}>
                    {!deviceId ? t.devices.pleaseSelectDevice : t.apps.noApps}
                  </Typography>
                </Box>
              ) : (
                currentPageApps.map((app, idx) => {
                  const pkgLoading = appLoadingState[app.package_name] || {}
                  const anyLoading = Object.values(pkgLoading).some((v) => v)
                  const iconBtnSx = {
                    p: 0.5,
                    cursor: 'pointer',
                    borderRadius: 1,
                    transition: 'all 0.15s',
                  }
                  return (
                    <Box
                      key={app.package_name}
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 1,
                        px: 1,
                        py: 0.5,
                        borderBottom:
                          idx < currentPageApps.length - 1
                            ? '1px solid rgba(241, 245, 249, 0.9)'
                            : 'none',
                        '&:hover': { bgcolor: 'rgba(248, 250, 252, 0.7)' },
                      }}
                    >
                      <Box sx={{ display: 'flex', alignItems: 'center', flex: 0.5, minWidth: 0, overflow: 'hidden' }}>
                        <Tooltip title={t.apps.copyPackageName} placement="top">
                          <Typography
                            onClick={() => handleCopyText(app.package_name)}
                            sx={{
                              fontSize: '0.92rem',
                              fontWeight: 600,
                              color: '#0f172a',
                              fontFamily:
                                'ui-monospace, SFMono-Regular, monospace',
                              cursor: 'pointer',
                              minWidth: 0,
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap',
                              '&:hover': { color: '#4f46e5' },
                            }}
                          >
                            {app.package_name}
                          </Typography>
                        </Tooltip>
                        {app.version_name && app.version_code && (
                          <Tooltip title={t.apps.copyVersion} placement="top">
                            <Typography
                              onClick={() =>
                                handleCopyText(`${app.version_name} (${app.version_code})`)
                              }
                              component="span"
                              sx={{
                                fontSize: '0.78rem',
                                color: '#6366f1',
                                fontWeight: 500,
                                cursor: 'pointer',
                                whiteSpace: 'nowrap',
                                flexShrink: 0,
                                ml: 1,
                                '&:hover': { color: '#4f46e5' },
                              }}
                            >
                              v{app.version_name} ({app.version_code})
                            </Typography>
                          </Tooltip>
                        )}
                      </Box>
                      <Box sx={{ display: 'flex', gap: 0.25, flexShrink: 0 }}>
                        <Tooltip title={t.apps.downloadApk} placement="top">
                          <IconButton
                            size="small"
                            onClick={() => handleAppDownload(app.package_name)}
                            disabled={anyLoading}
                            sx={{
                              ...iconBtnSx,
                              color: '#6366f1',
                              '&:hover': { bgcolor: 'rgba(99, 102, 241, 0.1)' },
                            }}
                          >
                            {pkgLoading.download ? (
                              <CircularProgress size={16} />
                            ) : (
                              <DownloadIcon sx={{ fontSize: 18 }} />
                            )}
                          </IconButton>
                        </Tooltip>
                        <Tooltip title={t.apps.appVersion} placement="top">
                          <IconButton
                            size="small"
                            onClick={() => handleAppVersion(app.package_name)}
                            disabled={anyLoading}
                            sx={{
                              ...iconBtnSx,
                              color: '#64748b',
                              '&:hover': { bgcolor: 'rgba(100, 116, 139, 0.1)' },
                            }}
                          >
                            {pkgLoading.version ? (
                              <CircularProgress size={16} />
                            ) : (
                              <InfoIcon sx={{ fontSize: 18 }} />
                            )}
                          </IconButton>
                        </Tooltip>
                        <Tooltip title={t.apps.startApp} placement="top">
                          <IconButton
                            size="small"
                            onClick={() => handleAppStart(app.package_name)}
                            disabled={anyLoading}
                            sx={{
                              ...iconBtnSx,
                              color: '#10b981',
                              '&:hover': { bgcolor: 'rgba(16, 185, 129, 0.1)' },
                            }}
                          >
                            {pkgLoading.start ? (
                              <CircularProgress size={16} />
                            ) : (
                              <PlayIcon sx={{ fontSize: 18 }} />
                            )}
                          </IconButton>
                        </Tooltip>
                        <Tooltip title={t.apps.stopApp} placement="top">
                          <IconButton
                            size="small"
                            onClick={() => handleAppStop(app.package_name)}
                            disabled={anyLoading}
                            sx={{
                              ...iconBtnSx,
                              color: '#64748b',
                              '&:hover': { bgcolor: 'rgba(100, 116, 139, 0.1)' },
                            }}
                          >
                            {pkgLoading.stop ? (
                              <CircularProgress size={16} />
                            ) : (
                              <StopIcon sx={{ fontSize: 18 }} />
                            )}
                          </IconButton>
                        </Tooltip>
                        <Tooltip title={t.apps.clearData} placement="top">
                          <IconButton
                            size="small"
                            onClick={() => handleAppClearData(app.package_name)}
                            disabled={anyLoading}
                            sx={{
                              ...iconBtnSx,
                              color: '#f59e0b',
                              '&:hover': { bgcolor: 'rgba(245, 158, 11, 0.1)' },
                            }}
                          >
                            {pkgLoading.clear ? (
                              <CircularProgress size={16} />
                            ) : (
                              <CleaningServicesIcon sx={{ fontSize: 18 }} />
                            )}
                          </IconButton>
                        </Tooltip>
                        <Tooltip title={t.apps.uninstallApp} placement="top">
                          <IconButton
                            size="small"
                            onClick={() => {
                              if (confirm(t.apps.confirmUninstall + '\n' + app.package_name)) {
                                handleAppUninstall(app.package_name)
                              }
                            }}
                            disabled={anyLoading}
                            sx={{
                              ...iconBtnSx,
                              color: '#ef4444',
                              '&:hover': { bgcolor: 'rgba(239, 68, 68, 0.1)' },
                            }}
                          >
                            {pkgLoading.uninstall ? (
                              <CircularProgress size={16} />
                            ) : (
                              <DeleteIcon sx={{ fontSize: 18 }} />
                            )}
                          </IconButton>
                        </Tooltip>
                      </Box>
                    </Box>
                  )
                })
              )}
            </Box>

            {/* 分页 */}
            {filteredApps.length > PAGE_SIZE && (
              <Box
                sx={{
                  display: 'flex',
                  justifyContent: 'center',
                  pt: 0.5,
                  flexShrink: 0,
                }}
              >
                <Pagination
                  size="small"
                  count={totalPages}
                  page={appPage}
                  onChange={(_, p) => setAppPage(p)}
                  sx={{
                    '& .MuiPaginationItem-root': {
                      fontSize: '0.85rem',
                      minWidth: 30,
                      height: 30,
                    },
                  }}
                />
              </Box>
            )}

            {recordingSession && (
              <Alert
                severity="warning"
                icon={<RecordIcon sx={{ color: '#ef4444', fontSize: 16 }} />}
                sx={{
                  mt: 1,
                  py: 0.5,
                  px: 1,
                  fontSize: '0.72rem',
                  '& .MuiAlert-message': { py: 0.25, fontSize: '0.72rem' },
                  '& .MuiAlert-icon': { py: 0.25, mr: 1 },
                }}
              >
                {t.screen.recordingPersistent}
              </Alert>
            )}
          </Paper>
          </>
          )}
        </Box>
      </Box>

      {/* ==================== Snackbar ==================== */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={3000}
        onClose={() => setSnackbar((s) => ({ ...s, open: false }))}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert
          onClose={() => setSnackbar((s) => ({ ...s, open: false }))}
          severity={snackbar.severity}
          variant="filled"
          sx={{ fontSize: '0.85rem' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>

      {/* ==================== Confirm Dialog ==================== */}
      <Dialog
        open={confirmDialog.open}
        onClose={() => setConfirmDialog((s) => ({ ...s, open: false }))}
      >
        <DialogTitle sx={{ fontSize: '1rem', fontWeight: 600 }}>
          {confirmDialog.title}
        </DialogTitle>
        <DialogContent>
          <Typography sx={{ fontSize: '0.875rem', color: '#475569' }}>
            {confirmDialog.message}
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button
            onClick={() => setConfirmDialog((s) => ({ ...s, open: false }))}
            sx={{ cursor: 'pointer' }}
          >
            {t.common.cancel}
          </Button>
          <Button onClick={confirmDialog.action} variant="contained" sx={{ cursor: 'pointer' }}>
            {t.common.confirm}
          </Button>
        </DialogActions>
      </Dialog>

      {/* ==================== Modify Config Dialog ==================== */}
      <Dialog
        open={configDialogOpen}
        onClose={() => setConfigDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle sx={{ fontSize: '1rem', fontWeight: 600 }}>
          {t.devices.modifyConfigTitle}
        </DialogTitle>
        <DialogContent dividers>
          <Stack spacing={2} sx={{ pt: 1 }}>
            <HistoryTextField
              ref={configPathHistoryRef}
              historyKey={HK_CONFIG_PATH}
              value={configPath}
              onChange={setConfigPath}
              placeholder={t.devices.configPathPlaceholder}
              size="small"
              inputSx={inputSx}
            />
            <HistoryTextField
              ref={configKeyHistoryRef}
              historyKey={HK_CONFIG_KEY}
              value={configKey}
              onChange={setConfigKey}
              placeholder={t.devices.configKeyPlaceholder}
              size="small"
              inputSx={inputSx}
            />
            <HistoryTextField
              ref={configValueHistoryRef}
              historyKey={HK_CONFIG_VALUE}
              value={configValue}
              onChange={setConfigValue}
              placeholder={t.devices.configValuePlaceholder}
              size="small"
              inputSx={inputSx}
            />
            <Box
              sx={{
                p: 1.25,
                borderRadius: 1,
                bgcolor: '#eef2ff',
                border: '1px solid #c7d2fe',
              }}
            >
              <Typography
                sx={{ fontSize: '0.78rem', fontWeight: 600, color: '#4338ca', mb: 0.5 }}
              >
                {t.devices.configTips}
              </Typography>
              <Typography sx={{ fontSize: '0.75rem', color: '#4338ca' }}>
                • {t.devices.configTip1}
              </Typography>
              <Typography sx={{ fontSize: '0.75rem', color: '#4338ca' }}>
                • {t.devices.configTip2}
              </Typography>
              <Typography sx={{ fontSize: '0.75rem', color: '#4338ca' }}>
                • {t.devices.configTip3}
              </Typography>
            </Box>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfigDialogOpen(false)} sx={{ cursor: 'pointer' }}>
            {t.common.cancel}
          </Button>
          <Button
            onClick={handleModifyConfig}
            variant="contained"
            disabled={
              !configKey.trim() || !configValue.trim() || actionLoading === 'modify-config'
            }
            startIcon={
              actionLoading === 'modify-config' ? <CircularProgress size={14} /> : null
            }
            sx={{ cursor: 'pointer' }}
          >
            {t.common.confirm}
          </Button>
        </DialogActions>
      </Dialog>

      {/* ==================== Custom Button Exec Result Dialog ==================== */}
      <Dialog
        open={customExecResult.open}
        onClose={() => setCustomExecResult((s) => ({ ...s, open: false }))}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle sx={{ fontSize: '1rem', fontWeight: 600 }}>
          {customExecResult.name} · {t.customButtons.executionResult}
        </DialogTitle>
        <DialogContent dividers>
          <Stack spacing={1.5}>
            <Box>
              <Typography
                sx={{ fontSize: '0.78rem', fontWeight: 600, color: '#475569', mb: 0.5 }}
              >
                {t.customButtons.command}:
              </Typography>
              <Box
                sx={{
                  p: 1.25,
                  bgcolor: '#f8fafc',
                  borderRadius: 1,
                  fontFamily: 'ui-monospace, SFMono-Regular, monospace',
                  fontSize: '0.78rem',
                  border: '1px solid #e2e8f0',
                  wordBreak: 'break-all',
                }}
              >
                {customExecResult.command}
              </Box>
            </Box>
            <Typography sx={{ fontSize: '0.78rem', fontWeight: 600, color: '#475569' }}>
              {t.customButtons.returnCode}:
              <Typography
                component="span"
                sx={{
                  ml: 1,
                  color:
                    customExecResult.returnCode === 0 ? '#10b981' : '#ef4444',
                  fontWeight: 600,
                }}
              >
                {customExecResult.returnCode}
              </Typography>
            </Typography>
            <Box>
              <Typography
                sx={{ fontSize: '0.78rem', fontWeight: 600, color: '#475569', mb: 0.5 }}
              >
                {t.customButtons.commandOutput}:
              </Typography>
              <Box
                sx={{
                  p: 1.25,
                  bgcolor: '#1e1e1e',
                  color: '#d4d4d4',
                  borderRadius: 1,
                  fontFamily: 'ui-monospace, SFMono-Regular, monospace',
                  fontSize: '0.78rem',
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-all',
                  maxHeight: 360,
                  overflow: 'auto',
                }}
              >
                {customExecResult.output || `(${t.customButtons.noOutput})`}
              </Box>
            </Box>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button
            onClick={() =>
              setCustomExecResult((s) => ({ ...s, open: false }))
            }
            variant="contained"
            sx={{ cursor: 'pointer' }}
          >
            {t.common.close}
          </Button>
        </DialogActions>
      </Dialog>

      {/* ==================== Info Dialog ==================== */}
      <Dialog
        open={infoDialog.open}
        onClose={() => setInfoDialog((s) => ({ ...s, open: false }))}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle sx={{ fontSize: '1rem', fontWeight: 600 }}>{infoDialog.title}</DialogTitle>
        <DialogContent dividers>{infoDialog.content}</DialogContent>
        <DialogActions>
          <Button
            onClick={() => setInfoDialog((s) => ({ ...s, open: false }))}
            variant="contained"
            sx={{ cursor: 'pointer' }}
          >
            {t.common.close}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
