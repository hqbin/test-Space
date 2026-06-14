/**
 * 自定义按钮页面
 */

import React from 'react'
import { Container, Alert } from '@mui/material'
import CustomButtons from '../components/CustomButtons'
import { Info as InfoIcon } from '@mui/icons-material'
import { useTranslation } from '../hooks/useTranslation'

const CustomButtonsPage: React.FC = () => {
  const { t, locale } = useTranslation()

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Alert severity="info" icon={<InfoIcon />} sx={{ mb: 3 }}>
        <strong>{t.common.info}:</strong> {locale === 'zh-CN'
          ? '自定义按钮可以保存常用的 ADB 命令，一键执行。例如：查询设备信息、清除缓存、重启应用等。'
          : 'Custom buttons can save frequently used ADB commands for one-click execution. For example: query device info, clear cache, restart apps, etc.'}
      </Alert>

      <CustomButtons />
    </Container>
  )
}

export default CustomButtonsPage
