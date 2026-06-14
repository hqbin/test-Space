/**
 * 连接设备表单组件
 * 
 * 提供 IP 地址和端口输入，支持从历史记录快速选择
 */

import { useState, useEffect } from 'react'
import {
  Box,
  TextField,
  Button,
  Paper,
  Typography,
  MenuItem,
  Grid,
  CircularProgress,
} from '@mui/material'
import { Add as AddIcon } from '@mui/icons-material'
import { getIpHistory, addIpToHistory, type IpHistoryEntry } from '@utils/localStorage'
import { useTranslation } from '../../hooks/useTranslation'

interface ConnectDeviceFormProps {
  onConnect: (ip: string, port: number) => Promise<void>
  loading?: boolean
}

export function ConnectDeviceForm({
  onConnect,
  loading = false,
}: ConnectDeviceFormProps) {
  const { t } = useTranslation()
  const [ip, setIp] = useState('')
  const [port, setPort] = useState('5555')
  const [error, setError] = useState('')
  const [ipHistory, setIpHistory] = useState<IpHistoryEntry[]>([])

  // 加载 IP 历史记录
  useEffect(() => {
    setIpHistory(getIpHistory(10))
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    // 验证 IP 地址
    const ipPattern = /^(\d{1,3}\.){3}\d{1,3}$/
    if (!ipPattern.test(ip)) {
      setError(t.devices.enterIpAddress)
      return
    }

    // 验证端口
    const portNum = parseInt(port, 10)
    if (isNaN(portNum) || portNum < 1 || portNum > 65535) {
      setError(t.devices.enterPort)
      return
    }

    try {
      await onConnect(ip, portNum)
      
      // 连接成功后添加到历史记录
      addIpToHistory(ip, portNum)
      setIpHistory(getIpHistory(10))
      
      // 清空表单
      setIp('')
      setPort('5555')
    } catch (err) {
      setError((err as Error).message || t.messages.connectFailed)
    }
  }

  const handleSelectHistory = (historyIp: string, historyPort: number) => {
    setIp(historyIp)
    setPort(historyPort.toString())
  }

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        {t.devices.connectDevice}
      </Typography>

      <Box component="form" onSubmit={handleSubmit}>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={8}>
            <TextField
              fullWidth
              label={t.devices.ipAddress}
              value={ip}
              onChange={(e) => setIp(e.target.value)}
              placeholder="192.168.1.100"
              disabled={loading}
              error={!!error}
              helperText={error}
              required
            />
          </Grid>
          <Grid item xs={12} sm={4}>
            <TextField
              fullWidth
              label={t.devices.port}
              value={port}
              onChange={(e) => setPort(e.target.value)}
              placeholder="5555"
              disabled={loading}
              required
            />
          </Grid>

          {ipHistory.length > 0 && (
            <Grid item xs={12}>
              <TextField
                fullWidth
                select
                label="从历史记录选择"
                value=""
                onChange={(e) => {
                  const [historyIp, historyPort] = e.target.value.split(':')
                  handleSelectHistory(historyIp, parseInt(historyPort, 10))
                }}
                disabled={loading}
              >
                {ipHistory.map((item) => (
                  <MenuItem key={`${item.ip}:${item.port}`} value={`${item.ip}:${item.port}`}>
                    {item.ip}:{item.port}
                  </MenuItem>
                ))}
              </TextField>
            </Grid>
          )}

          <Grid item xs={12}>
            <Button
              type="submit"
              variant="contained"
              startIcon={loading ? <CircularProgress size={20} /> : <AddIcon />}
              disabled={loading || !ip || !port}
              fullWidth
            >
              {loading ? t.devices.connecting : t.devices.connect}
            </Button>
          </Grid>
        </Grid>
      </Box>
    </Paper>
  )
}
