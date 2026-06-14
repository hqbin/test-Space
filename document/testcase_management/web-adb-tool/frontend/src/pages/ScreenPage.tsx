/**
 * ScreenPage - 屏幕操作页面
 */

import React from 'react'
import { Box, Alert, Button } from '@mui/material'
import { ScreenOperations } from '@components/ScreenOperations'
import { useDeviceStore } from '../store/deviceStore'
import { Warning as WarningIcon, ArrowBack as ArrowBackIcon } from '@mui/icons-material'
import { useTranslation } from '../hooks/useTranslation'
import { useNavigate } from 'react-router-dom'

export const ScreenPage: React.FC = () => {
  const { t } = useTranslation()
  const { selectedDevice } = useDeviceStore()
  const navigate = useNavigate()

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', flex: 1, minHeight: 0 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2, flexShrink: 0 }}>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate('/')}
          sx={{ textTransform: 'none', color: '#475569', fontSize: '0.9rem' }}
        >
          {t.common.back || '返回'}
        </Button>
      </Box>

      {!selectedDevice && (
        <Alert severity="warning" icon={<WarningIcon />} sx={{ mb: 3, flexShrink: 0 }}>
          {t.messages.pleaseSelectDevice}
        </Alert>
      )}

      <Box sx={{ flex: 1, minHeight: 0 }}>
        <ScreenOperations />
      </Box>
    </Box>
  )
}
