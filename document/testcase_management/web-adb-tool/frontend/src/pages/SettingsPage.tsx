/**
 * 设置页面
 */

import React, { useState } from 'react'
import {
  Container,
  Typography,
  Box,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Button,
  Chip,
  Select,
  MenuItem,
  FormControl,
  Snackbar,
  Alert,
} from '@mui/material'
import {
  Download as DownloadIcon,
  Upload as UploadIcon,
  DeleteForever as DeleteIcon,
  ArrowBack as ArrowBackIcon,
} from '@mui/icons-material'
import {
  downloadDataAsFile,
  importDataFromFile,
  clearAllData,
  getCustomButtons,
  getIpHistory,
} from '@utils/localStorage'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from '../hooks/useTranslation'
import { localeNames, Locale } from '../i18n'

const SettingsPage: React.FC = () => {
  const navigate = useNavigate()
  const { locale, t, changeLocale } = useTranslation()
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false,
    message: '',
    severity: 'success',
  })
  const [mergeMode, setMergeMode] = useState(true)

  // 统计数据
  const buttonCount = getCustomButtons().length
  const historyCount = getIpHistory(100).length

  // 显示 Snackbar 消息
  const showSnackbar = (message: string, severity: 'success' | 'error') => {
    setSnackbar({ open: true, message, severity })
  }

  // 关闭 Snackbar
  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false })
  }

  // 切换语言
  const handleLanguageChange = (newLocale: Locale) => {
    changeLocale(newLocale)
    // 不显示提示消息，语言切换是即时的
  }

  // 导出数据
  const handleExportData = () => {
    try {
      downloadDataAsFile()
      showSnackbar(t.messages.dataExported, 'success')
    } catch (error) {
      showSnackbar(t.messages.operationFailed, 'error')
    }
  }

  // 导入数据
  const handleImportData = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    try {
      const success = await importDataFromFile(file, mergeMode)
      if (success) {
        showSnackbar(t.messages.dataImported, 'success')
        // 刷新页面以显示新数据
        setTimeout(() => window.location.reload(), 1500)
      } else {
        showSnackbar(t.messages.operationFailed, 'error')
      }
    } catch (error) {
      showSnackbar(t.messages.operationFailed, 'error')
    }

    // 清空 input
    event.target.value = ''
  }

  const handleClearCache = () => {
    if (confirm(t.settings.clearDataWarning + '\n\n' + t.settings.clearDataConfirm)) {
      clearAllData()
      showSnackbar(t.messages.dataCleared, 'success')
      setTimeout(() => window.location.reload(), 1000)
    }
  }

  return (
    <Box sx={{ flex: 1, minHeight: 0, overflow: 'auto' }}>
      <Container maxWidth="md" sx={{ py: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate('/')}
          sx={{ textTransform: 'none', color: '#475569', fontSize: '0.9rem' }}
        >
          {t.common.back}
        </Button>
      </Box>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          {t.settings.title}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {t.settings.general}
        </Typography>
      </Box>

      {/* 语言设置 */}
      <Paper sx={{ mb: 3, p: 3 }}>
        <Typography variant="h6" gutterBottom>
          {t.settings.language}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {t.settings.selectLanguage}
        </Typography>
        <FormControl fullWidth>
          <Select
            value={locale}
            onChange={(e) => handleLanguageChange(e.target.value as Locale)}
            sx={{ maxWidth: 300 }}
          >
            {Object.entries(localeNames).map(([key, name]) => (
              <MenuItem key={key} value={key}>
                {name}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </Paper>

      {/* 数据统计 */}
      <Paper sx={{ mb: 3, p: 3 }}>
        <Typography variant="h6" gutterBottom>
          {t.settings.statistics}
        </Typography>
        <Box sx={{ mt: 2 }}>
          <Typography variant="body2" gutterBottom>
            • {t.settings.totalButtons}：{buttonCount}
          </Typography>
          <Typography variant="body2" gutterBottom>
            • {t.settings.ipHistory}：{historyCount}
          </Typography>
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 2 }}>
            {t.settings.dataStorageNote}
          </Typography>
        </Box>
      </Paper>

      {/* 数据备份与恢复 */}
      <Paper sx={{ mb: 3, p: 3 }}>
        <Typography variant="h6" gutterBottom>
          {t.settings.backupRestore}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {locale === 'zh-CN'
            ? '导出数据可以备份您的自定义按钮和 IP 历史记录，方便在其他浏览器或电脑上使用。'
            : 'Export data to backup your custom buttons and IP history for use on other browsers or computers.'}
        </Typography>

        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mb: 2 }}>
          {/* 导入按钮 */}
          <Button
            variant="contained"
            component="label"
            startIcon={<DownloadIcon />}
          >
            {t.settings.importData}
            <input
              type="file"
              accept=".json"
              hidden
              onChange={handleImportData}
            />
          </Button>

          {/* 导出按钮 */}
          <Button
            variant="outlined"
            startIcon={<UploadIcon />}
            onClick={handleExportData}
          >
            {t.settings.exportData}
          </Button>
        </Box>

        {/* 导入模式选择 */}
        <Box sx={{ pl: 2, borderLeft: 2, borderColor: 'divider' }}>
          <ListItem sx={{ px: 0 }}>
            <ListItemText
              primary={t.settings.importMode}
              secondary={
                mergeMode 
                  ? t.settings.mergeModeDesc
                  : t.settings.overwriteModeDesc
              }
            />
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <Chip
                label={mergeMode ? t.settings.mergeMode : t.settings.overwriteMode}
                color={mergeMode ? 'primary' : 'warning'}
                size="small"
                onClick={() => setMergeMode(!mergeMode)}
                sx={{ cursor: 'pointer' }}
              />
            </Box>
          </ListItem>
        </Box>
      </Paper>

      {/* 存储设置 */}
      <Paper sx={{ mb: 3, border: '1px solid', borderColor: 'error.light' }}>
        <List>
          <ListItem>
            <ListItemIcon>
              <DeleteIcon color="error" />
            </ListItemIcon>
            <ListItemText
              primary={t.settings.clearAllData}
              secondary={locale === 'zh-CN' 
                ? '删除自定义按钮、IP历史记录等所有本地数据（不可恢复）'
                : 'Delete all local data including custom buttons and IP history (cannot be undone)'}
            />
            <Button
              variant="outlined"
              color="error"
              onClick={handleClearCache}
              startIcon={<DeleteIcon />}
            >
              {t.common.delete}
            </Button>
          </ListItem>
        </List>
      </Paper>

      {/* Snackbar 消息提示 */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={3000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
      >
        <Alert onClose={handleCloseSnackbar} severity={snackbar.severity} sx={{ width: '100%' }}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Container>
    </Box>
  )
}

export default SettingsPage
