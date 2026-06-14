/**
 * 设备管理器主组件
 * 
 * 整合设备列表、连接表单和设备信息
 */

import { useEffect, useState } from 'react'
import { Box, Grid, Alert, Snackbar } from '@mui/material'
import { useDeviceStore } from '@store/deviceStore'
import { DeviceList } from './DeviceList'
import { ConnectDeviceForm } from './ConnectDeviceForm'
import { DeviceInfo } from './DeviceInfo'
import { useTranslation } from '../../hooks/useTranslation'

export function DeviceManager() {
  const { t } = useTranslation()
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
    refreshDeviceInfo,
    clearError,
  } = useDeviceStore()

  const [successMessage, setSuccessMessage] = useState('')

  // 初始加载
  useEffect(() => {
    fetchDevices()
  }, [])

  // 连接设备
  const handleConnect = async (ip: string, port: number) => {
    const result = await connectDevice(ip, port)
    // 只在真正连接成功时才显示成功消息
    // 失败消息会由 store 的 error 状态处理
    if (result) {
      // connectDevice 返回 true 表示连接成功
      setSuccessMessage(`${t.messages.connectSuccess}: ${ip}:${port}`)
    }
    // 如果返回 false，错误消息已经设置到 store.error 中了
  }

  // 断开设备
  const handleDisconnect = async (deviceId: string) => {
    await disconnectDevice(deviceId)
    setSuccessMessage(`${t.messages.disconnectSuccess}: ${deviceId}`)
  }

  // 刷新设备信息
  const handleRefreshInfo = () => {
    if (selectedDevice) {
      refreshDeviceInfo(selectedDevice.device_id)
    }
  }

  return (
    <Box>
      <Grid container spacing={3}>
        {/* 左侧：连接表单和设备列表 */}
        <Grid item xs={12} md={6}>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            <ConnectDeviceForm
              onConnect={handleConnect}
              loading={connecting}
            />
            <DeviceList
              devices={devices}
              selectedDevice={selectedDevice}
              onSelectDevice={selectDevice}
              onDisconnectDevice={handleDisconnect}
              onRefresh={fetchDevices}
              loading={fetchingDevices}
            />
          </Box>
        </Grid>

        {/* 右侧：设备信息 */}
        <Grid item xs={12} md={6}>
          <DeviceInfo
            device={selectedDevice}
            onRefresh={handleRefreshInfo}
            loading={fetchingDevices}
          />
        </Grid>
      </Grid>

      {/* 错误提示 */}
      <Snackbar
        open={!!error}
        autoHideDuration={6000}
        onClose={clearError}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={clearError} severity="error" sx={{ width: '100%' }}>
          {error}
        </Alert>
      </Snackbar>

      {/* 成功提示 */}
      <Snackbar
        open={!!successMessage}
        autoHideDuration={3000}
        onClose={() => setSuccessMessage('')}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={() => setSuccessMessage('')} severity="success" sx={{ width: '100%' }}>
          {successMessage}
        </Alert>
      </Snackbar>
    </Box>
  )
}
