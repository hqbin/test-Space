/**
 * 设备列表组件
 * 
 * 显示已连接的设备列表，支持选择和断开设备
 */

import {
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  IconButton,
  Chip,
  Box,
  Typography,
  Paper,
  Tooltip,
} from '@mui/material'
import {
  Smartphone as SmartphoneIcon,
  Close as CloseIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material'
import type { DeviceInfo } from '../../types/api'
import { useTranslation } from '../../hooks/useTranslation'

interface DeviceListProps {
  devices: DeviceInfo[]
  selectedDevice: DeviceInfo | null
  onSelectDevice: (device: DeviceInfo) => void
  onDisconnectDevice: (deviceId: string) => void
  onRefresh?: () => void
  loading?: boolean
}

export function DeviceList({
  devices,
  selectedDevice,
  onSelectDevice,
  onDisconnectDevice,
  onRefresh,
  loading = false,
}: DeviceListProps) {
  const { t } = useTranslation()

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'device':
        return <SmartphoneIcon sx={{ color: '#666' }} />
      case 'offline':
        return <ErrorIcon color="error" />
      case 'unauthorized':
        return <WarningIcon color="warning" />
      default:
        return <SmartphoneIcon />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'device':
        return 'primary' // 浅紫色主题
      case 'offline':
        return 'error'
      case 'unauthorized':
        return 'warning'
      default:
        return 'default'
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'device':
        return t.devices.online
      case 'offline':
        return t.devices.offline
      case 'unauthorized':
        return t.devices.unauthorized
      default:
        return status
    }
  }

  return (
    <Paper>
      {/* 标题栏和刷新按钮 */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', p: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Typography variant="h6">
          {t.devices.deviceList} {devices.length > 0 && `(${devices.length})`}
        </Typography>
        {onRefresh && (
          <Tooltip title={t.devices.refreshDevices}>
            <span>
              <IconButton onClick={onRefresh} disabled={loading} size="small">
                <RefreshIcon />
              </IconButton>
            </span>
          </Tooltip>
        )}
      </Box>

      {devices.length === 0 ? (
        <Box sx={{ p: 3, textAlign: 'center' }}>
          <Typography variant="body1" color="text.secondary">
            {t.devices.noDevices}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            {t.devices.pleaseSelectDevice}
          </Typography>
        </Box>
      ) : (
        <List>
        {devices.map((device) => {
          const isSelected = selectedDevice?.device_id === device.device_id
          
          return (
            <ListItem
              key={device.device_id}
              disablePadding
              secondaryAction={
                <IconButton
                  edge="end"
                  aria-label="disconnect"
                  onClick={() => onDisconnectDevice(device.device_id)}
                  size="small"
                >
                  <CloseIcon />
                </IconButton>
              }
              sx={{
                // 选中设备的背景色
                bgcolor: isSelected ? 'rgba(99, 102, 241, 0.1)' : 'transparent',
                borderLeft: isSelected ? '4px solid #6366f1' : '4px solid transparent',
                transition: 'all 0.2s ease',
              }}
            >
              <ListItemButton
                selected={isSelected}
                onClick={() => onSelectDevice(device)}
                sx={{
                  '&.Mui-selected': {
                    bgcolor: 'transparent',
                    '&:hover': {
                      bgcolor: 'rgba(99, 102, 241, 0.08)',
                    },
                  },
                  '&:hover': {
                    bgcolor: isSelected ? 'rgba(99, 102, 241, 0.08)' : 'rgba(0, 0, 0, 0.04)',
                  },
                }}
              >
                <ListItemIcon>
                  {isSelected ? (
                    <CheckCircleIcon sx={{ color: '#6366f1' }} />
                  ) : (
                    getStatusIcon(device.status)
                  )}
                </ListItemIcon>
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography 
                        variant="body1"
                        sx={{ 
                          fontWeight: isSelected ? 600 : 400,
                          color: isSelected ? '#6366f1' : 'inherit',
                        }}
                      >
                        {device.device_id}
                      </Typography>
                      <Chip
                        label={getStatusText(device.status)}
                        size="small"
                        color={getStatusColor(device.status) as any}
                        sx={{
                          fontWeight: isSelected ? 600 : 400,
                        }}
                      />
                    </Box>
                  }
                />
              </ListItemButton>
            </ListItem>
          )
        })}
        </List>
      )}
    </Paper>
  )
}
