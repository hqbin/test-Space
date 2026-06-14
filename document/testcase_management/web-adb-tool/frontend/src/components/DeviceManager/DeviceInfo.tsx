/**
 * 设备信息组件
 * 
 * 显示选中设备的详细信息
 */

import {
  Box,
  Paper,
  Typography,
  Grid,
  Chip,
  Divider,
  Button,
} from '@mui/material'
import {
  Refresh as RefreshIcon,
  Info as InfoIcon,
} from '@mui/icons-material'
import type { DeviceInfo as DeviceInfoType } from '../../types/api'
import { useTranslation } from '../../hooks/useTranslation'

interface DeviceInfoProps {
  device: DeviceInfoType | null
  onRefresh?: () => void
  loading?: boolean
}

export function DeviceInfo({ device, onRefresh, loading = false }: DeviceInfoProps) {
  const { t } = useTranslation()

  if (!device) {
    return (
      <Paper sx={{ p: 3, textAlign: 'center' }}>
        <InfoIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
        <Typography variant="body1" color="text.secondary">
          {t.devices.pleaseSelectDevice}
        </Typography>
      </Paper>
    )
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
    <Paper sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">{t.devices.deviceInfo}</Typography>
        {onRefresh && (
          <Button
            startIcon={<RefreshIcon />}
            onClick={onRefresh}
            disabled={loading}
            size="small"
            variant="contained"
          >
            {t.common.refresh}
          </Button>
        )}
      </Box>

      <Divider sx={{ mb: 2 }} />

      <Grid container spacing={2}>
        <Grid item xs={12}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
            <Typography variant="subtitle2" color="text.secondary">
              {t.devices.status}:
            </Typography>
            <Chip
              label={getStatusText(device.status)}
              color={getStatusColor(device.status) as any}
              size="small"
            />
          </Box>
        </Grid>

        <Grid item xs={12}>
          <Typography variant="subtitle2" color="text.secondary">
            {t.devices.deviceId}
          </Typography>
          <Typography variant="body1" sx={{ mt: 0.5 }}>
            {device.device_id}
          </Typography>
        </Grid>

        {device.model && (
          <Grid item xs={12} sm={6}>
            <Typography variant="subtitle2" color="text.secondary">
              {t.devices.model}
            </Typography>
            <Typography variant="body1" sx={{ mt: 0.5 }}>
              {device.model}
            </Typography>
          </Grid>
        )}

        {device.android_version && (
          <Grid item xs={12} sm={6}>
            <Typography variant="subtitle2" color="text.secondary">
              {t.devices.androidVersion}
            </Typography>
            <Typography variant="body1" sx={{ mt: 0.5 }}>
              {device.android_version}
            </Typography>
          </Grid>
        )}

        {device.sdk_version && (
          <Grid item xs={12} sm={6}>
            <Typography variant="subtitle2" color="text.secondary">
              {t.devices.sdkVersion}
            </Typography>
            <Typography variant="body1" sx={{ mt: 0.5 }}>
              {device.sdk_version}
            </Typography>
          </Grid>
        )}

        {device.resolution && (
          <Grid item xs={12} sm={6}>
            <Typography variant="subtitle2" color="text.secondary">
              {t.screen.resolution}
            </Typography>
            <Typography variant="body1" sx={{ mt: 0.5 }}>
              {device.resolution}
            </Typography>
          </Grid>
        )}

        {device.density && (
          <Grid item xs={12} sm={6}>
            <Typography variant="subtitle2" color="text.secondary">
              {t.devices.density}
            </Typography>
            <Typography variant="body1" sx={{ mt: 0.5 }}>
              {device.density}
            </Typography>
          </Grid>
        )}

        {device.build_fingerprint && (
          <Grid item xs={12}>
            <Typography variant="subtitle2" color="text.secondary">
              {t.devices.buildFingerprint}
            </Typography>
            <Typography variant="body1" sx={{ mt: 0.5, wordBreak: 'break-word' }}>
              {device.build_fingerprint}
            </Typography>
          </Grid>
        )}
      </Grid>
    </Paper>
  )
}
