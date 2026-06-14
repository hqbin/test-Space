/**
 * ScreenOperations 主组件
 *
 * 整合遥控器、屏幕镜像、录制和截图功能
 * 适配低分辨率（1366×768）：
 * - 在 md 断点以下纵向堆叠
 * - 中分辨率下使用更紧凑的两列布局（屏幕镜像 + 遥控控制条）
 * - 大屏使用三列布局
 */

import React, { useState } from 'react'
import { Box, Snackbar, Alert, useMediaQuery } from '@mui/material'
import { useDeviceStore } from '@store/deviceStore'
import { RemoteControl } from './RemoteControl'
import { ScreenMirror } from './ScreenMirror'
import { RecordingControls } from './RecordingControls'
import { ScreenshotCapture } from './ScreenshotCapture'

export const ScreenOperations: React.FC = () => {
  const { selectedDevice } = useDeviceStore()
  // 考虑 zoom 缩放后的实际断点：
  // 1366px × 0.9 zoom → 逻辑宽度约 1518px，但 useMediaQuery 读真实像素
  // 所以这里用真实像素判断
  const isSmall = useMediaQuery('(max-width: 1279px)')
  const isMedium = useMediaQuery('(min-width: 1280px) and (max-width: 1599px)')

  const [snackbar, setSnackbar] = useState<{
    open: boolean
    message: string
    severity: 'success' | 'error'
  }>({
    open: false,
    message: '',
    severity: 'success',
  })

  const handleSuccess = (message: string) => {
    setSnackbar({ open: true, message, severity: 'success' })
  }

  const handleError = (message: string) => {
    setSnackbar({ open: true, message, severity: 'error' })
  }

  const handleCloseSnackbar = () => {
    setSnackbar((prev) => ({ ...prev, open: false }))
  }

  const deviceId = selectedDevice?.device_id || null

  // 列布局：
  // 小屏 (< 1280px)：1 列纵向
  // 中屏 (1280-1599)：屏幕镜像 + (遥控器 / 控制) 两列
  // 大屏 (>= 1600)：遥控器 / 屏幕镜像 / 控制 三列
  let gridTemplateColumns: string
  if (isSmall) {
    gridTemplateColumns = '1fr'
  } else if (isMedium) {
    gridTemplateColumns = 'minmax(0, 1fr) 280px'
  } else {
    gridTemplateColumns = '260px minmax(0, 1fr) 280px'
  }

  return (
    <Box>
      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns,
          gap: 1.5,
          alignItems: 'stretch',
        }}
      >
        {/* 大屏：遥控器单独一列；中/小屏：与镜像并排或堆叠 */}
        {!isSmall && !isMedium && (
          <Box sx={{ minWidth: 0 }}>
            <RemoteControl deviceId={deviceId} />
          </Box>
        )}

        {/* 屏幕镜像 - 永远在主区域 */}
        <Box sx={{ minWidth: 0 }}>
          <ScreenMirror deviceId={deviceId} onError={handleError} />
        </Box>

        {/* 控制面板：录制 + 截图，中屏/大屏放右侧；小屏放下方 */}
        {!isSmall && (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5, minWidth: 0 }}>
            {/* 中屏：把遥控器折叠进右侧 */}
            {isMedium && (
              <RemoteControl deviceId={deviceId} compact />
            )}
            <RecordingControls
              deviceId={deviceId}
              onSuccess={handleSuccess}
              onError={handleError}
            />
            <ScreenshotCapture
              deviceId={deviceId}
              onSuccess={handleSuccess}
              onError={handleError}
            />
          </Box>
        )}

        {/* 小屏：遥控器和控制堆叠在镜像下方 */}
        {isSmall && (
          <>
            <Box sx={{ minWidth: 0 }}>
              <RemoteControl deviceId={deviceId} compact />
            </Box>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
              <RecordingControls
                deviceId={deviceId}
                onSuccess={handleSuccess}
                onError={handleError}
              />
              <ScreenshotCapture
                deviceId={deviceId}
                onSuccess={handleSuccess}
                onError={handleError}
              />
            </Box>
          </>
        )}
      </Box>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={4000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert
          onClose={handleCloseSnackbar}
          severity={snackbar.severity}
          variant="filled"
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  )
}
