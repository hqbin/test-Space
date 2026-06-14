/**
 * 主布局组件
 * 
 * 嵌入平台时隐藏侧边栏和顶栏，由平台导航控制页面切换
 * 独立运行时显示完整布局
 */

import { useState, useEffect, useRef } from 'react'
import {
  Box,
  AppBar,
  Toolbar,
  Typography,
  Select,
  MenuItem,
  FormControl,
  Chip,
} from '@mui/material'
import {
  PhoneAndroid as PhoneAndroidIcon,
} from '@mui/icons-material'
import { useNavigate } from 'react-router-dom'
import { useDeviceStore } from '../../store/deviceStore'
import { useRecordingSessionStore } from '../../store/recordingSessionStore'
import { useLogSessionStore } from '../../store/logSessionStore'
import { stopRecordingSession, stopLogcatSession, stopDiagnosticLog } from '../../services/localAgent'
import { useTranslation } from '../../hooks/useTranslation'

interface MainLayoutProps {
  children: React.ReactNode
}

// 检测是否在嵌入模式
// embedded.html 在 JS 加载前通过内联 <script> 设置 window.__ADB_EMBEDDED__ = true
// 这是最可靠的方式，不依赖 URL 参数、postMessage 或 window.name
function isEmbedded(): boolean {
  return !!(window as any).__ADB_EMBEDDED__
}

export function MainLayout({ children }: MainLayoutProps) {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [embedded, setEmbedded] = useState(isEmbedded())
  
  const { devices, selectedDevice, selectDevice, fetchDevices } = useDeviceStore()

  useEffect(() => {
    fetchDevices()
  }, [fetchDevices])

  useEffect(() => {
    const interval = setInterval(() => {
      fetchDevices()
    }, 5000)
    return () => clearInterval(interval)
  }, [fetchDevices])

  const prevDeviceIdsRef = useRef<string[]>([])

  useEffect(() => {
    const currentIds = devices.map(d => d.device_id)
    const prevIds = prevDeviceIdsRef.current

    if (prevIds.length > 0) {
      const disconnectedIds = prevIds.filter(id => !currentIds.includes(id))
      for (const deviceId of disconnectedIds) {
        stopSessionsForDisconnectedDevice(deviceId)
      }
    }

    prevDeviceIdsRef.current = currentIds
  }, [devices])

  function stopSessionsForDisconnectedDevice(deviceId: string) {
    const recordingSession = useRecordingSessionStore.getState().recordingSession
    const { logcatSession, diagnosticSession, setLogcatSession, setDiagnosticSession } = useLogSessionStore.getState()
    const { clearRecordingSession } = useRecordingSessionStore.getState()

    if (recordingSession && recordingSession.deviceId === deviceId) {
      stopRecordingSession(recordingSession.sessionId, deviceId)
        .catch(() => {})
        .finally(() => clearRecordingSession())
    }

    if (logcatSession && logcatSession.deviceId === deviceId) {
      stopLogcatSession(logcatSession.sessionId)
        .then(blob => {
          const url = window.URL.createObjectURL(blob)
          const a = document.createElement('a')
          a.href = url
          a.download = `logcat_${deviceId}_${Date.now()}.txt`
          document.body.appendChild(a)
          a.click()
          window.URL.revokeObjectURL(url)
          document.body.removeChild(a)
        })
        .catch(() => {})
        .finally(() => setLogcatSession(null))
    }

    if (diagnosticSession && diagnosticSession.deviceId === deviceId) {
      stopDiagnosticLog(diagnosticSession.sessionId)
        .then(blob => {
          const url = window.URL.createObjectURL(blob)
          const a = document.createElement('a')
          a.href = url
          a.download = `diagnostic_${deviceId}_${Date.now()}.zip`
          document.body.appendChild(a)
          a.click()
          window.URL.revokeObjectURL(url)
          document.body.removeChild(a)
        })
        .catch(() => {})
        .finally(() => setDiagnosticSession(null))
    }
  }

  // 监听来自父窗口的消息（导航 + 嵌入模式激活）
  // 始终监听，因为 activate-embedded 可能在非嵌入模式下到达
  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      if (event.data?.type === 'navigate' && event.data?.path) {
        navigate(event.data.path)
      } else if (event.data?.type === 'activate-embedded') {
        ;(window as any).__ADB_EMBEDDED__ = true
        setEmbedded(true)
        if (event.data?.path) {
          navigate(event.data.path)
        }
      }
    }
    window.addEventListener('message', handleMessage)
    return () => window.removeEventListener('message', handleMessage)
  }, [navigate])

  // 嵌入模式：路由变化时通知父窗口
  useEffect(() => {
    if (!embedded) return
    window.parent.postMessage({
      type: 'adb-route-change',
      path: window.location.pathname,
    }, '*')
  }, [embedded])

  const handleDeviceChange = (deviceId: string) => {
    const device = devices.find(d => d.device_id === deviceId)
    selectDevice(device || null)
  }

  // ========== 嵌入模式：只显示设备选择器 + 内容 ==========
  if (embedded) {
    return (
      <Box sx={{
        width: 'calc(100vw / var(--zoom-factor, 1))',
        height: 'calc(100vh / var(--zoom-factor, 1))',
        transformOrigin: 'top left',
        transform: 'scale(var(--zoom-factor, 1))',
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: '#f8fafc',
      }}>
        {/* 顶部设备选择器条 */}
        <Box sx={{
          bgcolor: '#fff',
          borderBottom: '1px solid #e2e8f0',
          px: 3,
          py: 1.5,
          display: 'flex',
          alignItems: 'center',
          gap: 2,
        }}>
          <PhoneAndroidIcon sx={{ color: '#6366f1', fontSize: 20 }} />
          <FormControl size="small" sx={{ minWidth: 280 }}>
            <Select
              value={selectedDevice?.device_id || ''}
              onChange={(e) => handleDeviceChange(e.target.value)}
              displayEmpty
              sx={{
                bgcolor: '#f9fafb',
                fontSize: '0.875rem',
                borderRadius: '8px',
                '& .MuiOutlinedInput-notchedOutline': { borderColor: '#e2e8f0' },
                '&:hover .MuiOutlinedInput-notchedOutline': { borderColor: '#6366f1' },
                '&.Mui-focused .MuiOutlinedInput-notchedOutline': { borderColor: '#6366f1', borderWidth: 1 },
              }}
            >
              <MenuItem value="" disabled>
                <Typography variant="body2" color="text.secondary">
                  {t.devices.selectDevice}
                </Typography>
              </MenuItem>
              {devices.map((device) => (
                <MenuItem key={device.device_id} value={device.device_id}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, width: '100%' }}>
                    <Typography variant="body2" sx={{ flex: 1 }}>
                      {device.model || device.device_id}
                    </Typography>
                    <Chip 
                      label={device.status} 
                      size="small" 
                      color={device.status === 'device' ? 'primary' : 'default'}
                      sx={{ height: 20, fontSize: '0.7rem', fontWeight: 500 }}
                    />
                  </Box>
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          
          {selectedDevice && (
            <Box sx={{ 
              display: 'flex', alignItems: 'center', gap: 1,
              px: 2, py: 0.5, bgcolor: '#eef2ff', borderRadius: '8px',
            }}>
              <Typography variant="body2" sx={{ color: '#4f46e5', fontSize: '0.8rem', fontWeight: 500 }}>
                {selectedDevice.model || selectedDevice.device_id}
              </Typography>
              <Typography variant="body2" sx={{ color: '#6366f1', fontSize: '0.75rem' }}>
                Android {selectedDevice.android_version || 'N/A'}
              </Typography>
            </Box>
          )}
        </Box>

        {/* 内容区域 */}
        <Box sx={{
          px: 2, pt: 1.5, pb: 1,
          flex: 1,
          minHeight: 0,
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          boxSizing: 'border-box',
        }}>
          {children}
        </Box>
      </Box>
    )
  }

  // ========== 独立模式：仅顶栏 + 内容 ==========
  return (
    <Box sx={{
      width: 'calc(100vw / var(--zoom-factor, 1))',
      height: 'calc(100vh / var(--zoom-factor, 1))',
      transformOrigin: 'top left',
      transform: 'scale(var(--zoom-factor, 1))',
      display: 'flex',
      flexDirection: 'column',
      backgroundColor: '#f8fafc',
    }}>
      <AppBar position="static" elevation={0} sx={{ bgcolor: '#fff', borderBottom: '1px solid #e2e8f0' }}>
        <Toolbar sx={{ minHeight: 56, height: 56, px: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <PhoneAndroidIcon sx={{ color: '#6366f1', fontSize: 20 }} />
            <FormControl size="small" sx={{ minWidth: 280 }}>
              <Select
                value={selectedDevice?.device_id || ''}
                onChange={(e) => handleDeviceChange(e.target.value)}
                displayEmpty
                sx={{
                  bgcolor: '#f9fafb', fontSize: '0.875rem', borderRadius: '8px',
                  '& .MuiOutlinedInput-notchedOutline': { borderColor: '#e2e8f0' },
                  '&:hover .MuiOutlinedInput-notchedOutline': { borderColor: '#6366f1' },
                  '&.Mui-focused .MuiOutlinedInput-notchedOutline': { borderColor: '#6366f1', borderWidth: 1 },
                }}
              >
                <MenuItem value="" disabled>
                  <Typography variant="body2" color="text.secondary">{t.devices.selectDevice}</Typography>
                </MenuItem>
                {devices.map((device) => (
                  <MenuItem key={device.device_id} value={device.device_id}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, width: '100%' }}>
                      <Typography variant="body2" sx={{ flex: 1 }}>{device.model || device.device_id}</Typography>
                      <Chip label={device.status} size="small" 
                        color={device.status === 'device' ? 'primary' : 'default'}
                        sx={{ height: 20, fontSize: '0.7rem', fontWeight: 500 }}
                      />
                    </Box>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            
            {selectedDevice && (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, px: 2, py: 0.5, bgcolor: '#eef2ff', borderRadius: '8px' }}>
                <Typography variant="body2" sx={{ color: '#4f46e5', fontSize: '0.8rem', fontWeight: 500 }}>
                  {selectedDevice.model || selectedDevice.device_id}
                </Typography>
                <Typography variant="body2" sx={{ color: '#6366f1', fontSize: '0.75rem' }}>
                  Android {selectedDevice.android_version || 'N/A'}
                </Typography>
              </Box>
            )}
          </Box>
        </Toolbar>
      </AppBar>

      <Box component="main" sx={{
        flex: 1,
        minHeight: 0,
        px: 2,
        pt: 2,
        pb: 1,
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        boxSizing: 'border-box',
      }}>
        {children}
      </Box>
    </Box>
  )
}
