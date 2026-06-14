/**
 * LogControls 组件
 * 
 * 日志采集控制
 */

import React, { useState, useEffect, useRef } from 'react'
import {
  Box,
  Paper,
  Typography,
  Button,
  CircularProgress,
  Chip,
} from '@mui/material'
import {
  PlayArrow as StartIcon,
  Stop as StopIcon,
  DeleteSweep as ClearIcon,
} from '@mui/icons-material'
import { apiClient } from '@services/api' // Note: boot logcat still uses backend
import { 
  clearLogcat as clearLogcatLocal, 
  startLogcatSession, 
  stopLogcatSession,
  startDiagnosticLog,
  stopDiagnosticLog
} from '@services/localAgent'
import { useTranslation } from '@hooks/useTranslation'
import { useLogSessionStore } from '../../store/logSessionStore'

interface LogControlsProps {
  deviceId: string | null
  onSuccess?: (message: string) => void
  onError?: (error: string) => void
}

export const LogControls: React.FC<LogControlsProps> = ({
  deviceId,
  onSuccess,
  onError,
}) => {
  const { t } = useTranslation()
  const [isLoading, setIsLoading] = useState(false)
  
  // 使用全局状态管理会话
  const {
    logcatSession,
    setLogcatSession,
    bootLogcatSession,
    setBootLogcatSession,
    diagnosticSession,
    setDiagnosticSession,
  } = useLogSessionStore()
  
  const isCollecting = !!logcatSession
  const sessionId = logcatSession?.sessionId || null
  
  // Boot logcat polling
  const bootPollIntervalRef = useRef<number | null>(null)
  
  // Diagnostic log elapsed time
  const [diagnosticElapsed, setDiagnosticElapsed] = useState<number>(0)
  
  // Update diagnostic elapsed time
  useEffect(() => {
    if (!diagnosticSession) {
      setDiagnosticElapsed(0)
      return
    }
    
    const interval = window.setInterval(() => {
      const elapsed = Math.floor((new Date().getTime() - diagnosticSession.startTime) / 1000)
      setDiagnosticElapsed(elapsed)
    }, 1000)
    
    return () => clearInterval(interval)
  }, [diagnosticSession])

  // 恢复 boot logcat 轮询（如果有活动会话）
  useEffect(() => {
    if (bootLogcatSession) {
      startBootLogcatPolling(bootLogcatSession.sessionId)
    }
    
    // 注意：不要在 unmount 时清理轮询，让它继续运行
    // 只在会话真正结束时清理
  }, [bootLogcatSession?.sessionId])

  const handleStartLogcat = async () => {
    if (!deviceId) {
      onError?.(t.devices.pleaseSelectDevice)
      return
    }

    setIsLoading(true)
    try {
      // 使用本地代理启动 logcat 会话
      const response = await startLogcatSession(deviceId)

      if (response.success && response.session_id) {
        setLogcatSession({
          sessionId: response.session_id,
          deviceId: deviceId,
          startTime: Date.now(),
        })
        onSuccess?.(t.logs.startCaptureLog)
      } else {
        onError?.(response.error || t.logs.startCaptureFailed)
      }
    } catch (error: any) {
      onError?.(error.message || t.logs.startCaptureFailed)
    } finally {
      setIsLoading(false)
    }
  }

  const handleStopLogcat = async () => {
    if (!sessionId) return

    setIsLoading(true)
    try {
      // 停止采集并直接获取文件
      const blob = await stopLogcatSession(sessionId)
      
      onSuccess?.(t.logs.stopCaptureDownloading)
      
      // 下载文件
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      // 使用更友好的文件名
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5)
      a.download = `logcat_${deviceId?.replace(/:/g, '_')}_${timestamp}.txt`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      onSuccess?.(t.logs.logDownloaded)
    } catch (error: any) {
      onError?.(error.message || t.logs.stopCaptureFailed)
    } finally {
      setLogcatSession(null)
      setIsLoading(false)
    }
  }

  const handleClearLogcat = async () => {
    if (!deviceId) {
      onError?.(t.devices.pleaseSelectDevice)
      return
    }

    setIsLoading(true)
    try {
      const response = await clearLogcatLocal(deviceId)
      if (response.success) {
        onSuccess?.(t.logs.deviceLogCleared)
      } else {
        onError?.(`${response.error || t.logs.clearDeviceLogFailed}`)
      }
    } catch (error: any) {
      onError?.(error.message || t.logs.clearDeviceLogFailed)
    } finally {
      setIsLoading(false)
    }
  }

  const handleStartBootLogcat = async () => {
    setIsLoading(true)
    try {
      // Start boot logcat with or without device
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
        
        if (mode === 'reboot') {
          onSuccess?.(t.devices.rebootSuccess)
        } else {
          onSuccess?.(t.logs.capturing)
        }
        
        // Start polling for status
        startBootLogcatPolling(session_id)
      }
    } catch (error: any) {
      onError?.(error.response?.data?.message || t.logs.startBootLogcatFailed)
    } finally {
      setIsLoading(false)
    }
  }

  const stopBootLogcatPolling = () => {
    if (bootPollIntervalRef.current) {
      clearInterval(bootPollIntervalRef.current)
      bootPollIntervalRef.current = null
    }
  }

  const startBootLogcatPolling = (sessionId: string) => {
    stopBootLogcatPolling()
    let errorCount = 0
    
    bootPollIntervalRef.current = window.setInterval(async () => {
      try {
        const statusResponse = await apiClient.getBootLogcatStatus(sessionId)
        errorCount = 0 // 重置错误计数
        
        if (statusResponse.success && statusResponse.data) {
          const status = statusResponse.data
          
          // 更新会话状态
          const currentSession = useLogSessionStore.getState().bootLogcatSession
          if (currentSession) {
            setBootLogcatSession({
              ...currentSession,
              lineCount: status.line_count,
              connected: status.connected
            })
          }
        }
      } catch (error: any) {
        errorCount++
        console.error('Failed to get boot logcat status:', error)
        // 连续 3 次错误或 404 认为会话已失效，停止轮询并清理
        if (errorCount >= 3 || error?.response?.status === 404) {
          console.error('Boot logcat session lost, stopping polling')
          stopBootLogcatPolling()
          setBootLogcatSession(null)
        }
      }
    }, 2000) // Poll every 2 seconds
  }

  const handleStopBootLogcat = async () => {
    if (!bootLogcatSession) return

    setIsLoading(true)
    try {
      // Stop and download
      const blob = await apiClient.stopBootLogcat(bootLogcatSession.sessionId)
      
      // Download file
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5)
      const devicePart = bootLogcatSession.deviceId?.replace(/:/g, '_') || 'unknown'
      a.download = `boot_logcat_${devicePart}_${timestamp}.txt`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      
      onSuccess?.(t.logs.logDownloaded)
    } catch (error: any) {
      onError?.(error.response?.data?.message || t.logs.startBootLogcatFailed)
    } finally {
      // 无论成功失败都清理轮询和会话，避免前端卡死
      stopBootLogcatPolling()
      setBootLogcatSession(null)
      setIsLoading(false)
    }
  }

  const handleStartDiagnosticLog = async () => {
    if (!deviceId) {
      onError?.(t.devices.pleaseSelectDevice)
      return
    }

    setIsLoading(true)
    try {
      // 使用本地代理启动完整诊断日志采集
      const response = await startDiagnosticLog(deviceId)
      
      if (response.success && response.session_id) {
        setDiagnosticSession({
          sessionId: response.session_id,
          deviceId: deviceId,
          startTime: Date.now()
        })
        onSuccess?.(t.logs.captureStarted)
      } else {
        onError?.(response.error || t.logs.captureFailed)
      }
    } catch (error: any) {
      onError?.(error.message || t.logs.captureFailed)
    } finally {
      setIsLoading(false)
    }
  }

  const handleStopDiagnosticLog = async () => {
    if (!diagnosticSession) return

    setIsLoading(true)
    try {
      // 停止并下载
      const blob = await stopDiagnosticLog(diagnosticSession.sessionId)
      
      // Download file
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5)
      const devicePart = diagnosticSession.deviceId.replace(/:/g, '_')
      a.download = `diagnostic_${devicePart}_${timestamp}.zip`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      
      const duration = Math.floor((Date.now() - diagnosticSession.startTime) / 1000)
      onSuccess?.(t.logs.logDownloaded + ` (${duration} ${t.screen.seconds})`)
    } catch (error: any) {
      onError?.(error.message || t.logs.captureFailed)
    } finally {
      setDiagnosticSession(null)
      setIsLoading(false)
    }
  }

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h5" gutterBottom sx={{ fontWeight: 600, mb: 3 }}>
        {t.logs.realtimeLog}
      </Typography>

      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
        {!isCollecting ? (
          <Button
            variant="contained"
            size="large"
            startIcon={isLoading ? <CircularProgress size={24} /> : <StartIcon />}
            onClick={handleStartLogcat}
            disabled={!deviceId || isLoading}
            sx={{ py: 1.5, fontSize: '1.1rem', maxWidth: 400, mx: 'auto', width: '100%' }}
          >
            {t.logs.startCapture}
          </Button>
        ) : (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, maxWidth: 400, mx: 'auto', width: '100%' }}>
            <Chip
              label={t.logs.capturing}
              color="primary"
              icon={<StartIcon />}
              sx={{ fontSize: '1rem', py: 2.5 }}
            />
            
            <Button
              variant="contained"
              size="large"
              startIcon={isLoading ? <CircularProgress size={24} /> : <StopIcon />}
              onClick={handleStopLogcat}
              disabled={isLoading}
              fullWidth
              sx={{ py: 1.5, fontSize: '1.1rem' }}
            >
              {t.logs.stopCapture}
            </Button>
          </Box>
        )}

        <Box sx={{ mt: 3, pt: 3, borderTop: 2, borderColor: 'divider' }}>
          <Typography variant="h6" gutterBottom sx={{ fontWeight: 500, mb: 2 }}>
            {t.logs.bootLogcat}
          </Typography>
          
          {!bootLogcatSession ? (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, maxWidth: 400, mx: 'auto' }}>
              {deviceId ? (
                <>
                  <Button
                    variant="contained"
                    size="large"
                    color="secondary"
                    startIcon={isLoading ? <CircularProgress size={24} /> : <StartIcon />}
                    onClick={handleStartBootLogcat}
                    disabled={isLoading || isCollecting}
                    fullWidth
                    sx={{ py: 1.5, fontSize: '1.1rem' }}
                  >
                    {t.logs.captureBootLog}
                  </Button>
                  <Typography variant="body2" color="text.secondary">
                    {t.logs.bootLogcatDesc}
                  </Typography>
                </>
              ) : (
                <>
                  <Button
                    variant="contained"
                    size="large"
                    color="secondary"
                    startIcon={isLoading ? <CircularProgress size={24} /> : <StartIcon />}
                    onClick={handleStartBootLogcat}
                    disabled={isLoading || isCollecting}
                    fullWidth
                    sx={{ py: 1.5, fontSize: '1.1rem' }}
                  >
                    {t.logs.captureBootLog}
                  </Button>
                  <Typography variant="body2" color="text.secondary">
                    {t.logs.bootLogcatDesc}
                  </Typography>
                </>
              )}
            </Box>
          ) : (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, maxWidth: 400, mx: 'auto' }}>
              <Chip
                label={
                  bootLogcatSession.connected
                    ? t.logs.capturing
                    : t.common.loading
                }
                color="secondary"
                icon={<CircularProgress size={16} />}
                sx={{ fontSize: '1rem', py: 2.5 }}
              />
              <Button
                variant="contained"
                size="large"
                startIcon={isLoading ? <CircularProgress size={24} /> : <StopIcon />}
                onClick={handleStopBootLogcat}
                disabled={isLoading}
                fullWidth
                sx={{ py: 1.5, fontSize: '1.1rem' }}
              >
                {t.logs.stopCapture}
              </Button>
            </Box>
          )}
        </Box>

        <Box sx={{ mt: 3, pt: 3, borderTop: 2, borderColor: 'divider' }}>
          <Typography variant="h6" gutterBottom sx={{ fontWeight: 500, mb: 2 }}>
            {t.logs.advancedFeatures}
          </Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, maxWidth: 400, mx: 'auto' }}>
            <Button
              variant="outlined"
              size="large"
              color="error"
              startIcon={isLoading ? <CircularProgress size={24} /> : <ClearIcon />}
              onClick={handleClearLogcat}
              disabled={!deviceId || isLoading}
              fullWidth
              sx={{ py: 1.5, fontSize: '1.05rem' }}
            >
              {t.logs.clearDeviceLog}
            </Button>
            
            {/* 完整诊断日志包 */}
            {!diagnosticSession ? (
              <Button
                variant="outlined"
                size="large"
                color="info"
                startIcon={isLoading ? <CircularProgress size={24} /> : <StartIcon />}
                onClick={handleStartDiagnosticLog}
                disabled={!deviceId || isLoading || isCollecting}
                fullWidth
                sx={{ py: 1.5, fontSize: '1.05rem' }}
              >
                {t.logs.captureDiagnosticPackage}
              </Button>
            ) : (
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Chip
                  label={`${t.logs.capturing} (${diagnosticElapsed} ${t.screen.seconds})`}
                  color="info"
                  icon={<CircularProgress size={16} />}
                  sx={{ fontSize: '1rem', py: 2.5 }}
                />
                <Button
                  variant="contained"
                  size="large"
                  color="info"
                  startIcon={isLoading ? <CircularProgress size={24} /> : <StopIcon />}
                  onClick={handleStopDiagnosticLog}
                  disabled={isLoading}
                  fullWidth
                  sx={{ py: 1.5, fontSize: '1.05rem' }}
                >
                  {t.logs.stopCapture}
                </Button>
              </Box>
            )}
          </Box>
        </Box>
      </Box>
    </Paper>
  )
}
