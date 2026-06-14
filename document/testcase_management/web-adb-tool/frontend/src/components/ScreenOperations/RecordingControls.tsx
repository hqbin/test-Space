/**
 * RecordingControls 组件
 * 
 * 屏幕录制控制
 */

import React, { useState, useEffect } from 'react'
import {
  Box,
  Paper,
  Typography,
  Button,
  CircularProgress,
  Chip,
  Alert,
} from '@mui/material'
import {
  FiberManualRecord as RecordIcon,
  Stop as StopIcon,
  Info as InfoIcon,
} from '@mui/icons-material'
import { startRecordingSession, stopRecordingSession, getRecordingSessionStatus } from '@services/localAgent'
import { useTranslation } from '@hooks/useTranslation'
import { useRecordingSessionStore } from '@store/recordingSessionStore'

interface RecordingControlsProps {
  deviceId: string | null
  onSuccess?: (message: string) => void
  onError?: (error: string) => void
}

export const RecordingControls: React.FC<RecordingControlsProps> = ({
  deviceId,
  onSuccess,
  onError,
}) => {
  const { t } = useTranslation()
  const { recordingSession, setRecordingSession, clearRecordingSession } = useRecordingSessionStore()
  
  const [isRecording, setIsRecording] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [sessionId, setSessionId] = useState<string | null>(null)

  // 组件挂载时恢复录制状态
  useEffect(() => {
    if (recordingSession) {
      console.log('[RecordingControls] 恢复录制会话:', recordingSession)
      // 先检查 session 是否还存在
      getRecordingSessionStatus(recordingSession.sessionId)
        .then((status) => {
          if (status.running) {
            setSessionId(recordingSession.sessionId)
            setIsRecording(true)
          } else {
            // session 已失效，清理状态
            console.log('[RecordingControls] 会话已失效，清理状态')
            setIsRecording(false)
            setSessionId(null)
            clearRecordingSession()
          }
        })
        .catch(() => {
          // 请求失败（session 不存在），清理状态
          console.log('[RecordingControls] 会话不存在，清理状态')
          setIsRecording(false)
          setSessionId(null)
          clearRecordingSession()
        })
    }
  }, [recordingSession])

  const handleStartRecording = async () => {
    if (!deviceId) {
      onError?.(t.devices.pleaseSelectDevice)
      return
    }

    setIsLoading(true)
    try {
      // 生成文件名
      const filename = `recording_${Date.now()}.mp4`
      
      // 使用本地代理启动录屏会话
      const response = await startRecordingSession(deviceId, filename)

      if (response.success && response.session_id) {
        setSessionId(response.session_id)
        setIsRecording(true)
        
        // 保存会话到 store（移除 bitRate）
        setRecordingSession({
          sessionId: response.session_id,
          deviceId,
          startTime: Date.now(),
        })
        
        onSuccess?.(t.screen.recordingStarted)
      } else {
        onError?.(response.error || t.screen.recordingFailed)
      }
    } catch (error: any) {
      onError?.(error.message || t.screen.recordingFailed)
    } finally {
      setIsLoading(false)
    }
  }

  const handleStopRecording = async () => {
    if (!sessionId) return

    setIsLoading(true)
    try {
      // 停止录制并直接下载文件
      const blob = await stopRecordingSession(sessionId, deviceId || undefined)
      
      // 创建下载链接
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `recording_${deviceId || 'unknown'}_${Date.now()}.mp4`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      
      onSuccess?.(t.screen.recordingStopped)
    } catch (error: any) {
      onError?.(error.message || t.screen.recordingFailed)
    } finally {
      setIsRecording(false)
      setSessionId(null)
      clearRecordingSession()
      setIsLoading(false)
    }
  }

  // 组件卸载时清理（但不停止录制）
  useEffect(() => {
    return () => {
      // 不需要清理任何东西，录制会话会持久化
    }
  }, [])

  // 页面刷新或关闭时自动停止录制
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (isRecording && sessionId) {
        // 同步停止录制（注意：这里不会触发下载）
        stopRecordingSession(sessionId, deviceId || undefined).catch((error) => {
          console.error('页面关闭时停止录制失败:', error)
        })
        
        // 提示用户有正在进行的录制
        e.preventDefault()
        e.returnValue = t.screen.recordingInProgress || '正在录制屏幕，确定要离开吗？'
        return e.returnValue
      }
    }

    window.addEventListener('beforeunload', handleBeforeUnload)
    
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload)
    }
  }, [isRecording, sessionId, t])

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        {t.screen.screenRecord}
      </Typography>

      {/* 持久化会话提示 */}
      {isRecording && recordingSession && (
        <Alert severity="info" icon={<InfoIcon />} sx={{ mb: 2 }}>
          <Typography variant="body2">
            {t.screen.recordingPersistent || '录制会话已保存，切换页面不会中断录制'}
          </Typography>
        </Alert>
      )}

      {!isRecording ? (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <Button
            variant="contained"
            color="error"
            startIcon={isLoading ? <CircularProgress size={20} /> : <RecordIcon />}
            onClick={handleStartRecording}
            disabled={!deviceId || isLoading}
            fullWidth
          >
            {t.screen.startRecord}
          </Button>
        </Box>
      ) : (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1 }}>
            <Chip
              label={t.screen.recording}
              color="error"
              icon={<RecordIcon />}
            />
          </Box>

          <Button
            variant="contained"
            startIcon={isLoading ? <CircularProgress size={20} /> : <StopIcon />}
            onClick={handleStopRecording}
            disabled={isLoading}
            fullWidth
          >
            {t.screen.stopRecord}
          </Button>
        </Box>
      )}
    </Paper>
  )
}
