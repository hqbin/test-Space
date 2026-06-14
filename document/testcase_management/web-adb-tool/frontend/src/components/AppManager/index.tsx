/**
 * AppManager 主组件
 * 
 * 整合应用上传和列表功能
 */

import React, { useState } from 'react'
import {
  Box,
  Grid,
  Snackbar,
  Alert,
} from '@mui/material'
import { useDeviceStore } from '@store/deviceStore'
import { AppUploader } from './AppUploader'
import { AppList } from './AppList'

export const AppManager: React.FC = () => {
  const { selectedDevice } = useDeviceStore()
  const [snackbar, setSnackbar] = useState<{
    open: boolean
    message: string
    severity: 'success' | 'error'
  }>({
    open: false,
    message: '',
    severity: 'success',
  })
  const [refreshTrigger, setRefreshTrigger] = useState(0)

  const handleSuccess = (message: string) => {
    setSnackbar({
      open: true,
      message,
      severity: 'success',
    })
  }

  const handleError = (message: string) => {
    setSnackbar({
      open: true,
      message,
      severity: 'error',
    })
  }

  const handleCloseSnackbar = () => {
    setSnackbar((prev) => ({ ...prev, open: false }))
  }

  const handleAppInstalled = () => {
    // 触发应用列表刷新
    setRefreshTrigger(prev => prev + 1)
  }

  return (
    <Box>
      <Grid container spacing={3}>
        {/* 左侧 - 应用上传 */}
        <Grid item xs={12} md={4}>
          <AppUploader
            deviceId={selectedDevice?.device_id || null}
            onSuccess={handleSuccess}
            onError={handleError}
            onAppInstalled={handleAppInstalled}
          />
        </Grid>

        {/* 右侧 - 应用列表 */}
        <Grid item xs={12} md={8}>
          <AppList
            deviceId={selectedDevice?.device_id || null}
            onSuccess={handleSuccess}
            onError={handleError}
            refreshTrigger={refreshTrigger}
          />
        </Grid>
      </Grid>

      {/* 提示消息 */}
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
