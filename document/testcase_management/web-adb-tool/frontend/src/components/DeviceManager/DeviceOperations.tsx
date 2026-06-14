/**
 * 设备操作组件
 * 
 * 提供设备的各种操作功能
 */

import React, { useState } from 'react'
import {
  Box,
  Paper,
  Typography,
  Button,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  CircularProgress,
  Grid,
} from '@mui/material'
import {
  Input as InputIcon,
  Refresh as RefreshIcon,
  RestartAlt as RestartIcon,
  Security as SecurityIcon,
  Info as InfoIcon,
  Memory as MemoryIcon,
} from '@mui/icons-material'
import { 
  inputText as sendText,
  restartAdb,
  rebootDevice as rebootDeviceCmd,
  rootDevice as rootDeviceCmd,
  remountDevice as remountDeviceCmd,
  getDeviceBasicInfo,
  getDeviceFirmwareInfo,
  getAospFirmwareInfo,
  checkDeviceKeys,
  modifyDeviceConfig,
} from '@services/localAgent'
import { useTranslation } from '@hooks/useTranslation'

interface DeviceOperationsProps {
  deviceId: string | null
  onSuccess?: (message: string) => void
  onError?: (error: string) => void
}

export const DeviceOperations: React.FC<DeviceOperationsProps> = ({
  deviceId,
  onSuccess,
  onError,
}) => {
  const { t } = useTranslation()
  const [isLoading, setIsLoading] = useState(false)
  const [inputText, setInputText] = useState('')
  const [infoDialogOpen, setInfoDialogOpen] = useState(false)
  const [whaleOSDialogOpen, setWhaleOSDialogOpen] = useState(false)
  const [aospFirmwareDialogOpen, setAospFirmwareDialogOpen] = useState(false)
  const [keysCheckDialogOpen, setKeysCheckDialogOpen] = useState(false)
  const [modifyConfigDialogOpen, setModifyConfigDialogOpen] = useState(false)
  const [configPath, setConfigPath] = useState('')
  const [configKey, setConfigKey] = useState('')
  const [configValue, setConfigValue] = useState('')
  const [deviceInfo, setDeviceInfo] = useState<any>(null)
  const [whaleOSInfo, setWhaleOSInfo] = useState<any>(null)
  const [aospFirmwareInfo, setAospFirmwareInfo] = useState<any>(null)
  const [keysCheckResults, setKeysCheckResults] = useState<any>(null)
  const [confirmDialog, setConfirmDialog] = useState<{
    open: boolean
    title: string
    message: string
    action: () => void
  }>({
    open: false,
    title: '',
    message: '',
    action: () => {},
  })

  const handleInputText = async () => {
    if (!deviceId || !inputText.trim()) {
      onError?.(t.devices.enterTextToSend)
      return
    }

    setIsLoading(true)
    try {
      const response = await sendText(deviceId, inputText)
      if (response.success) {
        onSuccess?.(t.devices.textSent)
        setInputText('')
      } else {
        onError?.(`${t.messages.operationFailed}: ${response.error}`)
      }
    } catch (error: any) {
      onError?.(`${t.messages.operationFailed}: ${error.message}`)
    } finally {
      setIsLoading(false)
    }
  }

  const handleRestartAdb = async () => {
    setIsLoading(true)
    try {
      const response = await restartAdb()
      if (response.success) {
        onSuccess?.(t.devices.adbRestarted || 'ADB 服务已重启')
      } else {
        onError?.(`${t.messages.operationFailed}: ${response.error}`)
      }
    } catch (error: any) {
      onError?.(`${t.messages.operationFailed}: ${error.message}`)
    } finally {
      setIsLoading(false)
    }
  }

  const handleRebootDevice = async () => {
    if (!deviceId) {
      onError?.(t.devices.pleaseSelectDevice)
      return
    }

    setConfirmDialog({
      open: true,
      title: t.devices.rebootConfirm || '确认重启设备',
      message: t.devices.rebootMessage || '确定要重启设备吗？设备将会断开连接。',
      action: async () => {
        setConfirmDialog(prev => ({ ...prev, open: false }))
        
        setIsLoading(true)
        try {
          const response = await rebootDeviceCmd(deviceId)
          if (response.success) {
            onSuccess?.(t.devices.rebootSuccess || '设备重启命令已发送')
          } else {
            onError?.(`${t.messages.operationFailed}: ${response.error}`)
          }
        } catch (error: any) {
          onError?.(`${t.messages.operationFailed}: ${error.message}`)
        } finally {
          setIsLoading(false)
        }
      },
    })
  }

  const handleRootDevice = async () => {
    if (!deviceId) {
      onError?.(t.devices.pleaseSelectDevice)
      return
    }

    setIsLoading(true)
    try {
      const response = await rootDeviceCmd(deviceId)
      if (response.success) {
        onSuccess?.(t.devices.rootSuccess || 'Root 成功')
      } else {
        onError?.(`${t.messages.operationFailed}: ${response.error}`)
      }
    } catch (error: any) {
      onError?.(`${t.messages.operationFailed}: ${error.message}`)
    } finally {
      setIsLoading(false)
    }
  }

  const handleRemountDevice = async () => {
    if (!deviceId) {
      onError?.(t.devices.pleaseSelectDevice)
      return
    }

    setConfirmDialog({
      open: true,
      title: t.devices.remountConfirm || '确认 Remount',
      message: t.devices.remountMessage || '此操作需要 root 权限。确定继续吗？',
      action: async () => {
        setConfirmDialog(prev => ({ ...prev, open: false }))
        
        setIsLoading(true)
        try {
          const response = await remountDeviceCmd(deviceId)
          if (response.success) {
            onSuccess?.(t.devices.remountSuccess || 'Remount 成功')
          } else {
            onError?.(`${t.messages.operationFailed}: ${response.error}`)
          }
        } catch (error: any) {
          onError?.(`${t.messages.operationFailed}: ${error.message}`)
        } finally {
          setIsLoading(false)
        }
      },
    })
  }

  const handleGetBasicInfo = async () => {
    if (!deviceId) {
      onError?.(t.devices.pleaseSelectDevice)
      return
    }

    setIsLoading(true)
    try {
      const response = await getDeviceBasicInfo(deviceId)
      if (response.success) {
        const data = JSON.parse(response.output)
        setDeviceInfo(data)
        setInfoDialogOpen(true)
      } else {
        onError?.(`${t.devices.getInfoFailed || '获取设备信息失败'}: ${response.error}`)
      }
    } catch (error: any) {
      onError?.(`${t.devices.getInfoFailed || '获取设备信息失败'}: ${error.message}`)
    } finally {
      setIsLoading(false)
    }
  }

  const handleGetWhaleOSInfo = async () => {
    if (!deviceId) {
      onError?.(t.devices.pleaseSelectDevice)
      return
    }

    setIsLoading(true)
    try {
      const response = await getDeviceFirmwareInfo(deviceId)
      if (response.success) {
        const data = JSON.parse(response.output)
        setWhaleOSInfo(data)
        setWhaleOSDialogOpen(true)
      } else {
        onError?.(`${t.devices.getWhaleOSInfoFailed}: ${response.error}`)
      }
    } catch (error: any) {
      onError?.(`${t.devices.getWhaleOSInfoFailed}: ${error.message}`)
    } finally {
      setIsLoading(false)
    }
  }

  const handleGetFirmwareInfo = async () => {
    if (!deviceId) {
      onError?.(t.devices.pleaseSelectDevice)
      return
    }

    setIsLoading(true)
    try {
      const response = await getAospFirmwareInfo(deviceId)
      if (response.success) {
        const data = JSON.parse(response.output)
        setAospFirmwareInfo(data)
        setAospFirmwareDialogOpen(true)
      } else {
        onError?.(`${t.devices.getAospInfoFailed}: ${response.error}`)
      }
    } catch (error: any) {
      onError?.(`${t.devices.getAospInfoFailed}: ${error.message}`)
    } finally {
      setIsLoading(false)
    }
  }

  const handleCheckKeys = async () => {
    if (!deviceId) {
      onError?.(t.devices.pleaseSelectDevice)
      return
    }

    setIsLoading(true)
    try {
      const response = await checkDeviceKeys(deviceId)
      if (response.success) {
        const data = JSON.parse(response.output)
        setKeysCheckResults(data)
        setKeysCheckDialogOpen(true)
      } else {
        onError?.(`${t.devices.checkKeysFailed}: ${response.error}`)
      }
    } catch (error: any) {
      onError?.(`${t.devices.checkKeysFailed}: ${error.message}`)
    } finally {
      setIsLoading(false)
    }
  }

  const handleModifyConfig = async () => {
    if (!deviceId) {
      onError?.(t.devices.pleaseSelectDevice)
      return
    }

    if (!configKey.trim() || !configValue.trim()) {
      onError?.(t.devices.enterConfigKeyValue)
      return
    }

    setIsLoading(true)
    setModifyConfigDialogOpen(false)
    
    try {
      const response = await modifyDeviceConfig(
        deviceId,
        configPath.trim(),
        configKey.trim(),
        configValue.trim()
      )
      
      if (response.success) {
        const data = JSON.parse(response.output)
        onSuccess?.(
          `${t.devices.modifyConfigSuccess}\n` +
          `${t.devices.configPathLabel}: ${data.config_path}\n` +
          `Key: ${data.config_key}\n` +
          `${t.devices.configValueLabel}: ${data.config_value}`
        )
        
        saveToHistory('configPaths', configPath.trim())
        saveToHistory('configKeys', configKey.trim())
        saveToHistory('configValues', configValue.trim())
        
        setConfigPath('')
        setConfigKey('')
        setConfigValue('')
      } else {
        onError?.(`${t.devices.modifyConfigFailed}: ${response.error}`)
      }
    } catch (error: any) {
      onError?.(`${t.devices.modifyConfigFailed}: ${error.message}`)
    } finally {
      setIsLoading(false)
    }
  }

  // 保存历史记录到localStorage
  const saveToHistory = (key: string, value: string) => {
    if (!value) return
    
    const history = JSON.parse(localStorage.getItem(key) || '[]')
    if (!history.includes(value)) {
      history.unshift(value)
      // 只保留最近10条
      if (history.length > 10) {
        history.pop()
      }
      localStorage.setItem(key, JSON.stringify(history))
    }
  }

  return (
    <Paper sx={{ p: 3, position: 'relative' }}>
      {/* Loading 遮罩层 */}
      {isLoading && (
        <Box
          sx={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            backgroundColor: 'rgba(255, 255, 255, 0.8)',
            zIndex: 1000,
            borderRadius: 1,
          }}
        >
          <CircularProgress size={60} />
        </Box>
      )}

      <Typography variant="h5" gutterBottom sx={{ fontWeight: 600, mb: 3 }}>
        {t.devices.deviceOperations}
      </Typography>

      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
        {/* 输入文本 */}
        <Box>
          <Typography variant="h6" gutterBottom sx={{ fontWeight: 500 }}>
            {t.devices.inputText}
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
            <TextField
              fullWidth
              size="small"
              placeholder={t.devices.enterTextToSend}
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              disabled={!deviceId || isLoading}
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  handleInputText()
                }
              }}
            />
            <Button
              variant="contained"
              startIcon={isLoading ? <CircularProgress size={20} /> : <InputIcon />}
              onClick={handleInputText}
              disabled={!deviceId || isLoading || !inputText.trim()}
              sx={{ minWidth: 120 }}
            >
              {t.devices.sendText || '发送'}
            </Button>
          </Box>
        </Box>

        {/* 设备控制 */}
        <Box>
          <Typography variant="h6" gutterBottom sx={{ fontWeight: 500 }}>
            {t.devices.deviceControl || '设备控制'}
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6} md={3}>
              <Button
                variant="outlined"
                fullWidth
                startIcon={<RefreshIcon />}
                onClick={handleRestartAdb}
                disabled={isLoading}
                sx={{ py: 1.5 }}
              >
                {t.devices.restartAdb}
              </Button>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Button
                variant="outlined"
                fullWidth
                startIcon={<RestartIcon />}
                onClick={handleRebootDevice}
                disabled={!deviceId || isLoading}
                sx={{ py: 1.5 }}
              >
                {t.devices.rebootDevice}
              </Button>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Button
                variant="outlined"
                fullWidth
                startIcon={<SecurityIcon />}
                onClick={handleRootDevice}
                disabled={!deviceId || isLoading}
                sx={{ py: 1.5 }}
              >
                Root
              </Button>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Button
                variant="outlined"
                fullWidth
                startIcon={<SecurityIcon />}
                onClick={handleRemountDevice}
                disabled={!deviceId || isLoading}
                sx={{ py: 1.5 }}
              >
                Remount
              </Button>
            </Grid>
          </Grid>
        </Box>

        {/* 设备信息 */}
        <Box>
          <Typography variant="h6" gutterBottom sx={{ fontWeight: 500 }}>
            {t.devices.deviceInfo}
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6} md={3}>
              <Button
                variant="outlined"
                fullWidth
                startIcon={<InfoIcon />}
                onClick={handleGetBasicInfo}
                disabled={!deviceId || isLoading}
                sx={{ py: 1.5 }}
              >
                {t.devices.basicInfo}
              </Button>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Button
                variant="outlined"
                fullWidth
                startIcon={<MemoryIcon />}
                onClick={handleGetWhaleOSInfo}
                disabled={!deviceId || isLoading}
                sx={{ py: 1.5 }}
              >
                {t.devices.whaleOSInfo}
              </Button>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Button
                variant="outlined"
                fullWidth
                startIcon={<MemoryIcon />}
                onClick={handleGetFirmwareInfo}
                disabled={!deviceId || isLoading}
                sx={{ py: 1.5 }}
              >
                {t.devices.aospInfo}
              </Button>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Button
                variant="outlined"
                fullWidth
                startIcon={<SecurityIcon />}
                onClick={handleCheckKeys}
                disabled={!deviceId || isLoading}
                sx={{ py: 1.5 }}
              >
                {t.devices.checkKeys}
              </Button>
            </Grid>
          </Grid>
        </Box>

        {/* 其他操作 */}
        <Box>
          <Typography variant="h6" gutterBottom sx={{ fontWeight: 500 }}>
            {t.devices.otherOperations || '其他操作'}
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6} md={4}>
              <Button
                variant="outlined"
                fullWidth
                startIcon={<InfoIcon />}
                onClick={() => setModifyConfigDialogOpen(true)}
                disabled={!deviceId || isLoading}
                sx={{ py: 1.5 }}
              >
                {t.devices.modifyConfig}
              </Button>
            </Grid>
          </Grid>
        </Box>
      </Box>

      {/* 设备基础信息对话框 */}
      <Dialog
        open={infoDialogOpen}
        onClose={() => setInfoDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>{t.devices.basicInfo}</DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2 }}>
            {deviceInfo && Array.isArray(deviceInfo) && deviceInfo.length > 0 && (
              <>
                {deviceInfo.map((item, index) => (
                  <Box key={index} sx={{ mb: 1, display: 'flex', gap: 2 }}>
                    <Typography variant="body2" sx={{ fontWeight: 600, minWidth: 150 }}>
                      {item.key}:
                    </Typography>
                    <Typography variant="body2" sx={{ wordBreak: 'break-all' }}>
                      {item.value}
                    </Typography>
                  </Box>
                ))}
              </>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setInfoDialogOpen(false)}>{t.common.close}</Button>
        </DialogActions>
      </Dialog>

      {/* WhaleOS固件信息对话框 */}
      <Dialog
        open={whaleOSDialogOpen}
        onClose={() => setWhaleOSDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>{t.devices.whaleOSInfo}</DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2 }}>
            {whaleOSInfo && Object.entries(whaleOSInfo).map(([key, value]) => (
              <Box key={key} sx={{ mb: 1, display: 'flex', gap: 2 }}>
                <Typography variant="body2" sx={{ fontWeight: 600, minWidth: 250 }}>
                  {key}:
                </Typography>
                <Typography variant="body2" sx={{ wordBreak: 'break-all' }}>
                  {String(value)}
                </Typography>
              </Box>
            ))}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setWhaleOSDialogOpen(false)}>{t.common.close}</Button>
        </DialogActions>
      </Dialog>

      {/* AOSP固件信息对话框 */}
      <Dialog
        open={aospFirmwareDialogOpen}
        onClose={() => setAospFirmwareDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>{t.devices.aospInfo}</DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2 }}>
            {aospFirmwareInfo && (
              <>
                {/* 固件信息 */}
                {aospFirmwareInfo.firmware && Object.keys(aospFirmwareInfo.firmware).length > 0 && (
                  <Box sx={{ mb: 3 }}>
                    <Typography variant="h6" sx={{ fontWeight: 600, mb: 2, color: 'primary.main' }}>
                      {t.devices.firmwareInfo}
                    </Typography>
                    {Object.entries(aospFirmwareInfo.firmware).map(([key, value]) => (
                      <Box key={key} sx={{ mb: 1, display: 'flex', gap: 2 }}>
                        <Typography variant="body2" sx={{ fontWeight: 600, minWidth: 250 }}>
                          {key}:
                        </Typography>
                        <Typography variant="body2" sx={{ wordBreak: 'break-all' }}>
                          {String(value)}
                        </Typography>
                      </Box>
                    ))}
                  </Box>
                )}

                {/* DP信息 */}
                {aospFirmwareInfo.dp && Object.keys(aospFirmwareInfo.dp).length > 0 && (
                  <Box sx={{ mb: 3 }}>
                    <Typography variant="h6" sx={{ fontWeight: 600, mb: 2, color: 'primary.main' }}>
                      {t.devices.dpInfo || 'DP信息'}
                    </Typography>
                    {Object.entries(aospFirmwareInfo.dp).map(([key, value]) => (
                      <Box key={key} sx={{ mb: 1, display: 'flex', gap: 2 }}>
                        <Typography variant="body2" sx={{ fontWeight: 600, minWidth: 250 }}>
                          {key}:
                        </Typography>
                        <Typography variant="body2" sx={{ wordBreak: 'break-all' }}>
                          {String(value)}
                        </Typography>
                      </Box>
                    ))}
                  </Box>
                )}

                {/* ADService信息 */}
                {aospFirmwareInfo.adservice && (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="h6" sx={{ fontWeight: 600, mb: 2, color: 'primary.main' }}>
                      {t.devices.adServiceInfo || 'ADService检测'}
                    </Typography>
                    {aospFirmwareInfo.adservice.status && (
                      <Box sx={{ mb: 1 }}>
                        <Typography variant="body2" sx={{ fontWeight: 600 }}>
                          {t.devices.status}:
                        </Typography>
                        <Typography variant="body2" sx={{ mt: 0.5, wordBreak: 'break-all' }}>
                          {aospFirmwareInfo.adservice.status}
                        </Typography>
                      </Box>
                    )}
                    {aospFirmwareInfo.adservice.version_info && (
                      <Box sx={{ mb: 1 }}>
                        <Typography variant="body2" sx={{ fontWeight: 600 }}>
                          {t.devices.versionInfo || '版本信息'}:
                        </Typography>
                        <Typography variant="body2" sx={{ mt: 0.5, wordBreak: 'break-all', fontFamily: 'monospace' }}>
                          {aospFirmwareInfo.adservice.version_info}
                        </Typography>
                      </Box>
                    )}
                  </Box>
                )}
              </>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAospFirmwareDialogOpen(false)}>{t.common.close}</Button>
        </DialogActions>
      </Dialog>

      {/* 确认对话框 */}
      <Dialog
        open={confirmDialog.open}
        onClose={() => setConfirmDialog({ ...confirmDialog, open: false })}
      >
        <DialogTitle>{confirmDialog.title}</DialogTitle>
        <DialogContent>
          <Typography>{confirmDialog.message}</Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmDialog({ ...confirmDialog, open: false })}>
            {t.common.cancel}
          </Button>
          <Button onClick={confirmDialog.action} variant="contained" color="primary">
            {t.common.confirm}
          </Button>
        </DialogActions>
      </Dialog>

      {/* 检查设备key烧写情况对话框 */}
      <Dialog
        open={keysCheckDialogOpen}
        onClose={() => setKeysCheckDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>{t.devices.keyCheckTitle}</DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2 }}>
            {keysCheckResults && Array.isArray(keysCheckResults) && keysCheckResults.map((result, index) => (
              <Box 
                key={index} 
                sx={{ 
                  mb: 3, 
                  p: 2, 
                  border: '1px solid',
                  borderColor: result.status === 'success' ? 'success.main' : result.status === 'error' ? 'error.main' : 'warning.main',
                  borderRadius: 1,
                  backgroundColor: result.status === 'success' ? 'success.light' : result.status === 'error' ? 'error.light' : 'warning.light',
                  opacity: 0.9
                }}
              >
                {/* Key名称 */}
                <Typography 
                  variant="h6" 
                  sx={{ 
                    fontWeight: 600, 
                    mb: 1,
                    color: result.status === 'success' ? 'success.dark' : result.status === 'error' ? 'error.dark' : 'warning.dark'
                  }}
                >
                  {result.name}
                </Typography>

                {/* 状态标签 */}
                <Box sx={{ mb: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    {t.devices.keyCheckStatus}:
                  </Typography>
                  <Typography 
                    variant="body2" 
                    sx={{ 
                      fontWeight: 600,
                      color: result.status === 'success' ? 'success.dark' : result.status === 'error' ? 'error.dark' : 'warning.dark'
                    }}
                  >
                    {result.status === 'success' ? t.devices.keyCheckSuccess : result.status === 'error' ? t.devices.keyCheckError : t.devices.keyCheckFailed}
                  </Typography>
                </Box>

                {/* 消息 */}
                <Typography variant="body2" sx={{ mb: 1 }}>
                  {result.message}
                </Typography>

                {/* 警告信息（失败或错误时显示） */}
                {result.warning && (
                  <Box 
                    sx={{ 
                      mt: 1, 
                      p: 1, 
                      backgroundColor: 'rgba(255, 255, 255, 0.7)',
                      borderRadius: 1,
                      border: '1px solid',
                      borderColor: 'warning.main'
                    }}
                  >
                    <Typography 
                      variant="body2" 
                      sx={{ 
                        color: 'warning.dark',
                        fontWeight: 500
                      }}
                    >
                      ⚠ {result.warning}
                    </Typography>
                  </Box>
                )}

                {/* 原始输出（可折叠） */}
                <Box sx={{ mt: 2 }}>
                  <details>
                    <summary style={{ cursor: 'pointer', fontWeight: 600, fontSize: '0.875rem' }}>
                      {t.devices.keyCheckViewOutput}
                    </summary>
                    <Box 
                      sx={{ 
                        mt: 1, 
                        p: 1, 
                        backgroundColor: 'rgba(0, 0, 0, 0.05)',
                        borderRadius: 1,
                        fontFamily: 'monospace',
                        fontSize: '0.75rem',
                        whiteSpace: 'pre-wrap',
                        wordBreak: 'break-all',
                        maxHeight: 200,
                        overflow: 'auto'
                      }}
                    >
                      {result.output || t.devices.keyCheckNoOutput}
                    </Box>
                  </details>
                </Box>
              </Box>
            ))}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setKeysCheckDialogOpen(false)}>{t.common.close}</Button>
        </DialogActions>
      </Dialog>

      {/* 修改设备配置表对话框 */}
      <Dialog
        open={modifyConfigDialogOpen}
        onClose={() => setModifyConfigDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>{t.devices.modifyConfigTitle}</DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              fullWidth
              label={t.devices.configPathLabel}
              placeholder={t.devices.configPathPlaceholder}
              value={configPath}
              onChange={(e) => setConfigPath(e.target.value)}
              helperText={t.devices.configPathHelper}
              size="small"
            />
            <TextField
              fullWidth
              label={t.devices.configKeyLabel}
              placeholder={t.devices.configKeyPlaceholder}
              value={configKey}
              onChange={(e) => setConfigKey(e.target.value)}
              required
              size="small"
            />
            <TextField
              fullWidth
              label={t.devices.configValueLabel}
              placeholder={t.devices.configValuePlaceholder}
              value={configValue}
              onChange={(e) => setConfigValue(e.target.value)}
              required
              size="small"
            />
            <Box sx={{ mt: 1, p: 2, backgroundColor: 'info.light', borderRadius: 1 }}>
              <Typography variant="body2" sx={{ fontSize: '0.875rem' }}>
                <strong>{t.devices.configTips}</strong>
              </Typography>
              <Typography variant="body2" sx={{ fontSize: '0.875rem', mt: 0.5 }}>
                • {t.devices.configTip1}
              </Typography>
              <Typography variant="body2" sx={{ fontSize: '0.875rem' }}>
                • {t.devices.configTip2}
              </Typography>
              <Typography variant="body2" sx={{ fontSize: '0.875rem' }}>
                • {t.devices.configTip3}
              </Typography>
            </Box>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setModifyConfigDialogOpen(false)}>{t.common.cancel}</Button>
          <Button 
            onClick={handleModifyConfig} 
            variant="contained" 
            disabled={!configKey.trim() || !configValue.trim()}
          >
            {t.common.confirm}
          </Button>
        </DialogActions>
      </Dialog>
    </Paper>
  )
}
