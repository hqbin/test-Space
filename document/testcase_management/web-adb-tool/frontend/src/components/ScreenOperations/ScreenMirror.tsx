/**
 * ScreenMirror 组件
 * 
 * 通过 WebSocket 实现网页内屏幕镜像
 * 支持参数配置并保存到 localStorage
 */

import React, { useState, useEffect, useRef } from 'react'
import {
  Box,
  Paper,
  Typography,
  Button,
  Alert,
  TextField,
  Grid,
  Collapse,
  IconButton,
} from '@mui/material'
import {
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  CheckCircle as CheckIcon,
  Settings as SettingsIcon,
  RestartAlt as ResetIcon,
} from '@mui/icons-material'
import { connectScreenMirror, type ScreenMirrorConnection } from '@services/localAgent'
import { useTranslation } from '@hooks/useTranslation'

interface ScreenMirrorProps {
  deviceId: string | null
  onSuccess?: (message: string) => void
  onError?: (error: string) => void
}

interface MirrorSettings {
  frameRate: number  // 帧率 (1-30 FPS)
  quality: number    // 质量 (1-100)
  maxSize: number    // 最大分辨率
}

const DEFAULT_SETTINGS: MirrorSettings = {
  frameRate: 10,
  quality: 80,
  maxSize: 1280,  // 降低到 720p 以提高性能
}

const SETTINGS_KEY = 'adb_tool_screen_mirror_settings'

export const ScreenMirror: React.FC<ScreenMirrorProps> = ({ deviceId, onSuccess, onError }) => {
  const { t } = useTranslation()
  const [isStreaming, setIsStreaming] = useState(false)
  const [frameCount, setFrameCount] = useState(0)
  const [showSettings, setShowSettings] = useState(false)
  const [settings, setSettings] = useState<MirrorSettings>(DEFAULT_SETTINGS)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const connectionRef = useRef<ScreenMirrorConnection | null>(null)

  // 加载设置
  useEffect(() => {
    const savedSettings = localStorage.getItem(SETTINGS_KEY)
    if (savedSettings) {
      try {
        setSettings(JSON.parse(savedSettings))
      } catch {
        setSettings(DEFAULT_SETTINGS)
      }
    }
  }, [])

  // 保存设置
  const saveSettings = (newSettings: MirrorSettings) => {
    setSettings(newSettings)
    localStorage.setItem(SETTINGS_KEY, JSON.stringify(newSettings))
  }

  // 重置设置
  const resetSettings = () => {
    setSettings(DEFAULT_SETTINGS)
    localStorage.setItem(SETTINGS_KEY, JSON.stringify(DEFAULT_SETTINGS))
    onSuccess?.(t.messages.settingsReset)
  }

  // 组件卸载时清理
  useEffect(() => {
    return () => {
      if (connectionRef.current) {
        connectionRef.current.close()
        connectionRef.current = null
      }
    }
  }, [])

  // 启动屏幕镜像
  const handleStart = async () => {
    if (!deviceId) {
      onError?.(t.devices.pleaseSelectDevice)
      return
    }

    try {
      console.log('[ScreenMirror] 启动屏幕镜像，设备ID:', deviceId)
      console.log('[ScreenMirror] 参数:', { fps: settings.frameRate, maxSize: settings.maxSize })
      
      // 连接 WebSocket 屏幕镜像，传递参数
      const connection = connectScreenMirror(
        deviceId,
        (blob) => {
          // 收到帧数据
          setFrameCount(prev => prev + 1)
          
          // 在 canvas 上绘制图像
          if (canvasRef.current) {
            const canvas = canvasRef.current
            const ctx = canvas.getContext('2d')
            if (ctx) {
              const img = new Image()
              img.onload = () => {
                // 调整 canvas 大小以匹配图像
                canvas.width = img.width
                canvas.height = img.height
                ctx.drawImage(img, 0, 0)
              }
              img.onerror = (e) => {
                console.error('[ScreenMirror] 图像加载失败:', e)
              }
              // 将 Blob 转换为 Data URL
              const reader = new FileReader()
              reader.onload = () => {
                img.src = reader.result as string
              }
              reader.readAsDataURL(blob)
            }
          }
        },
        (error) => {
          console.error('[ScreenMirror] WebSocket 错误:', error)
          onError?.(error.message || t.screen.mirrorFailed)
          setIsStreaming(false)
        },
        () => {
          console.log('[ScreenMirror] WebSocket 连接关闭')
          setIsStreaming(false)
        },
        {
          fps: settings.frameRate,
          maxSize: settings.maxSize,
        }
      )
      
      connectionRef.current = connection
      setIsStreaming(true)
      setFrameCount(0)
      
      console.log('[ScreenMirror] 屏幕镜像已启动')
      onSuccess?.(t.screen.mirrorStarted)
    } catch (error: any) {
      console.error('[ScreenMirror] 启动失败:', error)
      onError?.(error.message || t.screen.mirrorFailed)
    }
  }

  // 停止屏幕镜像
  const handleStop = async () => {
    try {
      console.log('[ScreenMirror] 停止屏幕镜像')
      
      if (connectionRef.current) {
        connectionRef.current.close()
        connectionRef.current = null
      }
      
      setIsStreaming(false)
      setFrameCount(0)
      
      // 清空 canvas
      if (canvasRef.current) {
        const canvas = canvasRef.current
        const ctx = canvas.getContext('2d')
        if (ctx) {
          ctx.clearRect(0, 0, canvas.width, canvas.height)
        }
      }
      
      onSuccess?.(t.screen.mirrorStopped)
    } catch (error: any) {
      console.error('[ScreenMirror] 停止失败:', error)
      onError?.(error.message || t.screen.mirrorFailed)
    }
  }

  return (
    <Paper sx={{ p: { xs: 1.5, md: 2, lg: 3 } }}>
      <Box sx={{ mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Typography variant="h6">
            {t.screen.screenMirror}
          </Typography>
          <IconButton
            onClick={() => setShowSettings(!showSettings)}
            size="small"
            sx={{ 
              transform: showSettings ? 'rotate(180deg)' : 'rotate(0deg)',
              transition: 'transform 0.3s'
            }}
          >
            <SettingsIcon />
          </IconButton>
        </Box>
      </Box>

      {/* 参数设置 */}
      <Collapse in={showSettings}>
        <Paper variant="outlined" sx={{ p: 2, mb: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
            <Typography variant="subtitle2">{t.screen.mirrorSettings}</Typography>
            <Button
              size="small"
              startIcon={<ResetIcon />}
              onClick={resetSettings}
            >
              {t.screen.reset}
            </Button>
          </Box>
          
          <Grid container spacing={2}>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label={t.screen.fps}
                type="number"
                value={settings.frameRate}
                onChange={(e) => saveSettings({ ...settings, frameRate: Math.max(1, Math.min(30, parseInt(e.target.value) || 10)) })}
                inputProps={{ min: 1, max: 30 }}
                helperText={t.screen.fpsRange}
                size="small"
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label={t.screen.imageQuality}
                type="number"
                value={settings.quality}
                onChange={(e) => saveSettings({ ...settings, quality: Math.max(1, Math.min(100, parseInt(e.target.value) || 80)) })}
                inputProps={{ min: 1, max: 100 }}
                helperText={t.screen.qualityRange}
                size="small"
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label={t.screen.maxResolution}
                type="number"
                value={settings.maxSize}
                onChange={(e) => saveSettings({ ...settings, maxSize: Math.max(480, Math.min(3840, parseInt(e.target.value) || 1920)) })}
                inputProps={{ min: 480, max: 3840, step: 120 }}
                helperText={t.screen.resolutionRange}
                size="small"
              />
            </Grid>
          </Grid>
        </Paper>
      </Collapse>

      {/* 控制按钮和画布 */}
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {/* 运行状态 */}
        {isStreaming && (
          <Alert severity="info" icon={<CheckIcon />}>
            <Typography variant="body2" gutterBottom>
              <strong>{t.screen.webMirrorRunning}</strong>
            </Typography>
            <Typography variant="body2" sx={{ mb: 1 }}>
              {t.screen.framesReceived} {frameCount} {t.screen.frames} • {t.screen.currentFps}: {settings.frameRate} FPS • {t.screen.currentResolution}: {settings.maxSize}p
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.875rem' }}>
              💡 {t.screen.mirrorTip} <a 
                href="https://github.com/Genymobile/scrcpy" 
                target="_blank" 
                rel="noopener noreferrer"
                style={{ color: '#6366f1', textDecoration: 'underline' }}
              >
                {t.screen.scrcpyTool}
              </a> {t.screen.independentTool}
            </Typography>
          </Alert>
        )}

        {/* 控制按钮 */}
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="contained"
            size="large"
            fullWidth
            startIcon={<PlayIcon />}
            onClick={handleStart}
            disabled={!deviceId || isStreaming}
            sx={{ py: 1.5 }}
          >
            {t.screen.startMirror}
          </Button>

          {isStreaming && (
            <Button
              variant="outlined"
              size="large"
              fullWidth
              startIcon={<StopIcon />}
              onClick={handleStop}
              sx={{ py: 1.5 }}
            >
              {t.screen.stopMirror}
            </Button>
          )}
        </Box>

        {/* 屏幕显示画布 */}
        <Box
          sx={{
            mt: 2,
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            bgcolor: 'black',
            borderRadius: 1,
            overflow: 'hidden',
            // 适配低分辨率：小屏减小最低高度
            minHeight: {
              xs: isStreaming ? 220 : 140,
              md: isStreaming ? 320 : 180,
              lg: isStreaming ? 400 : 200,
            },
            position: 'relative',
          }}
        >
          {!isStreaming && (
            <Typography variant="body2" color="grey.500">
              {t.screen.clickToStart}
            </Typography>
          )}
          <canvas
            ref={canvasRef}
            style={{
              maxWidth: '100%',
              maxHeight: '70vh',
              height: 'auto',
              objectFit: 'contain',
              display: isStreaming ? 'block' : 'none',
            }}
          />
        </Box>

        {/* 提示信息 */}
        {isStreaming && frameCount === 0 && (
          <Alert severity="info">
            <Typography variant="body2">
              {t.screen.waitingForData}
            </Typography>
          </Alert>
        )}
      </Box>
    </Paper>
  )
}
