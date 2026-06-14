/**
 * ScreenshotCapture 组件
 * 
 * 截图功能 - 点击后直接下载
 */

import React, { useState } from 'react'
import {
  Box,
  Paper,
  Typography,
  Button,
  CircularProgress,
} from '@mui/material'
import {
  CameraAlt as CameraIcon,
} from '@mui/icons-material'
import { downloadScreenshot } from '@services/localAgent'
import { useTranslation } from '@hooks/useTranslation'

interface ScreenshotCaptureProps {
  deviceId: string | null
  onSuccess?: (message: string) => void
  onError?: (error: string) => void
}

export const ScreenshotCapture: React.FC<ScreenshotCaptureProps> = ({
  deviceId,
  onSuccess,
  onError,
}) => {
  const { t } = useTranslation()
  const [isLoading, setIsLoading] = useState(false)

  const handleCapture = async () => {
    if (!deviceId) {
      onError?.(t.devices.pleaseSelectDevice)
      return
    }

    setIsLoading(true)
    try {
      // 使用本地代理下载截图
      const blob = await downloadScreenshot(deviceId)
      
      // 生成文件名（包含设备ID和时间戳）
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5)
      const filename = `screenshot_${deviceId}_${timestamp}.png`
      
      // 创建下载链接并自动下载
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      
      // 释放 URL 对象
      window.URL.revokeObjectURL(url)
      
      onSuccess?.(t.screen.captureSuccess)
    } catch (error: any) {
      onError?.(error.message || t.screen.captureFailed)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Paper sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">{t.screen.screenshot}</Typography>
        <Button
          variant="contained"
          startIcon={isLoading ? <CircularProgress size={20} color="inherit" /> : <CameraIcon />}
          onClick={handleCapture}
          disabled={!deviceId || isLoading}
        >
          {isLoading ? t.screen.capturing || '截图中...' : t.screen.capture}
        </Button>
      </Box>

      <Box sx={{ textAlign: 'center', py: 4 }}>
        <Typography color="text.secondary" variant="body2">
          {t.screen.screenshotTip || '点击"截图"按钮，截图将自动保存到浏览器的下载文件夹'}
        </Typography>
      </Box>
    </Paper>
  )
}
