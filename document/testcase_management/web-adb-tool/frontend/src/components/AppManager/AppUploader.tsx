/**
 * AppUploader 组件
 * 
 * APK 文件上传（支持拖放）
 */

import React, { useState } from 'react'
import {
  Box,
  Paper,
  Typography,
  Button,
  FormControlLabel,
  Checkbox,
  CircularProgress,
  LinearProgress,
  Divider,
  TextField,
  InputAdornment,
  IconButton,
} from '@mui/material'
import {
  CloudUpload as UploadIcon,
  CheckCircle as SuccessIcon,
  Visibility as VisibilityIcon,
  FolderOpen as FolderIcon,
  ContentCopy as CopyIcon,
} from '@mui/icons-material'
import { useDropzone } from 'react-dropzone'
import { uploadAndInstallApk, executeAdbCommand } from '@services/localAgent'
import { useTranslation } from '@hooks/useTranslation'
import { copyToClipboard } from '@utils/clipboard'

interface AppUploaderProps {
  deviceId: string | null
  onSuccess?: (message: string) => void
  onError?: (error: string) => void
  onAppInstalled?: () => void
}

export const AppUploader: React.FC<AppUploaderProps> = ({
  deviceId,
  onSuccess,
  onError,
  onAppInstalled,
}) => {
  const { t } = useTranslation()
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [reinstall, setReinstall] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [currentApp, setCurrentApp] = useState<string>('')
  const [appPath, setAppPath] = useState<string>('')
  const [queryPackage, setQueryPackage] = useState<string>('')
  const [isQuerying, setIsQuerying] = useState(false)

  const onDrop = (acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      const file = acceptedFiles[0]
      if (file.name.endsWith('.apk')) {
        setSelectedFile(file)
      } else {
        onError?.(t.apps.selectApkFile)
      }
    }
  }

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/vnd.android.package-archive': ['.apk'],
    },
    maxFiles: 1,
    // 移除大小限制，允许上传任意大小的 APK
  })

  const handleUpload = async () => {
    if (!deviceId) {
      onError?.(t.devices.pleaseSelectDevice)
      return
    }

    if (!selectedFile) {
      onError?.(t.apps.selectApkFile)
      return
    }

    setIsUploading(true)
    setUploadProgress(0)

    try {
      // 开始上传，显示进度
      setUploadProgress(10)
      
      // 使用本地代理上传并安装
      const response = await uploadAndInstallApk(deviceId, selectedFile)

      // 上传完成，显示安装中
      setUploadProgress(50)
      
      // 等待一下让用户看到进度
      await new Promise(resolve => setTimeout(resolve, 500))
      
      setUploadProgress(100)

      if (response.success) {
        onSuccess?.(t.apps.installSuccess)
        setSelectedFile(null)
        
        // 通知父组件刷新应用列表
        onAppInstalled?.()
        
        setTimeout(() => {
          setUploadProgress(0)
          setIsUploading(false)
        }, 1500)
      } else {
        onError?.(response.error || t.apps.installFailed)
        setIsUploading(false)
        setUploadProgress(0)
      }
    } catch (error: any) {
      console.error('Install error:', error)
      const errorMessage = error.message || t.apps.installFailed
      onError?.(errorMessage)
      setIsUploading(false)
      setUploadProgress(0)
    }
  }

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
  }

  const handleGetCurrentApp = async () => {
    if (!deviceId) {
      onError?.(t.devices.pleaseSelectDevice)
      return
    }

    setIsQuerying(true)
    try {
      // 使用 dumpsys window 获取当前前台应用
      const response = await executeAdbCommand(['-s', deviceId, 'shell', 'dumpsys', 'window', '|', 'grep', 'mCurrentFocus'])
      if (response.success && response.output) {
        // 解析包名
        const match = response.output.match(/\{.*\s+(\S+)\//)
        if (match && match[1]) {
          setCurrentApp(match[1])
          onSuccess?.(t.apps.currentAppIs.replace('{package}', match[1]))
        } else {
          onError?.(t.apps.getCurrentAppFailed)
        }
      } else {
        onError?.(t.apps.getCurrentAppFailed)
      }
    } catch (error: any) {
      onError?.(error.message || t.apps.getCurrentAppFailed)
    } finally {
      setIsQuerying(false)
    }
  }

  const handleGetAppPath = async () => {
    if (!deviceId) {
      onError?.(t.devices.pleaseSelectDevice)
      return
    }

    if (!queryPackage.trim()) {
      onError?.(t.apps.enterPackageNamePrompt)
      return
    }

    setIsQuerying(true)
    try {
      const response = await executeAdbCommand(['-s', deviceId, 'shell', 'pm', 'path', queryPackage])
      if (response.success && response.output) {
        // 解析路径
        const match = response.output.match(/package:(.+)/)
        if (match && match[1]) {
          const path = match[1].trim()
          setAppPath(path)
          onSuccess?.(t.apps.appPathIs.replace('{path}', path))
        } else {
          onError?.(t.apps.getAppPathFailed)
        }
      } else {
        onError?.(response.error || t.apps.getAppPathFailed)
      }
    } catch (error: any) {
      onError?.(error.message || t.apps.getAppPathFailed)
    } finally {
      setIsQuerying(false)
    }
  }

  const handleCopyToClipboard = async (text: string) => {
    const success = await copyToClipboard(text)
    if (success) {
      onSuccess?.(t.apps.copiedToClipboard)
    } else {
      onError?.('复制失败')
    }
  }

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        {t.apps.installApk}
      </Typography>

      <Box
        {...getRootProps()}
        sx={{
          border: 2,
          borderStyle: 'dashed',
          borderColor: isDragActive ? 'primary.main' : 'grey.300',
          borderRadius: 2,
          p: 4,
          textAlign: 'center',
          bgcolor: isDragActive ? 'action.hover' : 'background.paper',
          cursor: 'pointer',
          transition: 'all 0.3s',
          '&:hover': {
            borderColor: 'primary.main',
            bgcolor: 'action.hover',
          },
          mb: 2,
        }}
      >
        <input {...getInputProps()} />
        <UploadIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
        {selectedFile ? (
          <Box>
            <Typography variant="body1" gutterBottom>
              <SuccessIcon sx={{ verticalAlign: 'middle', mr: 1, color: 'success.main' }} />
              {selectedFile.name}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {formatFileSize(selectedFile.size)}
            </Typography>
          </Box>
        ) : (
          <Box>
            <Typography variant="body1" gutterBottom>
              {isDragActive ? (t.apps.releaseToUpload || '释放以上传文件') : t.apps.dragDrop}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {t.apps.orClickToSelect || '或点击选择文件'}
            </Typography>
          </Box>
        )}
      </Box>

      {uploadProgress > 0 && (
        <Box sx={{ mb: 2 }}>
          <LinearProgress 
            variant="determinate" 
            value={uploadProgress}
            sx={{
              height: 8,
              borderRadius: 1,
            }}
          />
          <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
            {uploadProgress < 50 ? t.apps.uploading : uploadProgress < 100 ? t.apps.installing : t.common.success} {uploadProgress}%
          </Typography>
        </Box>
      )}

      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, mb: 2 }}>
        <FormControlLabel
          control={
            <Checkbox
              checked={reinstall}
              onChange={(e) => setReinstall(e.target.checked)}
              disabled={isUploading}
            />
          }
          label={t.apps.reinstall || '重新安装（覆盖已有应用）'}
        />
      </Box>

      <Button
        variant="contained"
        startIcon={isUploading ? <CircularProgress size={20} /> : <UploadIcon />}
        onClick={handleUpload}
        disabled={!deviceId || !selectedFile || isUploading}
        fullWidth
      >
        {isUploading ? t.apps.installing : t.apps.installApk}
      </Button>

      {/* 分隔线 */}
      <Divider sx={{ my: 3 }} />

      {/* 查询当前前台应用 */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="subtitle2" gutterBottom>
          {t.apps.queryCurrentApp}
        </Typography>
        <Button
          variant="outlined"
          startIcon={isQuerying ? <CircularProgress size={20} /> : <VisibilityIcon />}
          onClick={handleGetCurrentApp}
          disabled={!deviceId || isQuerying}
          fullWidth
          sx={{ mb: 1 }}
        >
          {isQuerying ? t.apps.querying : t.apps.getCurrentApp}
        </Button>
        {currentApp && (
          <TextField
            fullWidth
            size="small"
            value={currentApp}
            InputProps={{
              readOnly: true,
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    size="small"
                    onClick={() => handleCopyToClipboard(currentApp)}
                  >
                    <CopyIcon fontSize="small" />
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />
        )}
      </Box>

      {/* 查询应用安装路径 */}
      <Box>
        <Typography variant="subtitle2" gutterBottom>
          {t.apps.queryAppPath}
        </Typography>
        <TextField
          fullWidth
          size="small"
          placeholder={t.apps.enterPackageName}
          value={queryPackage}
          onChange={(e) => setQueryPackage(e.target.value)}
          disabled={isQuerying}
          sx={{ mb: 1 }}
        />
        <Button
          variant="outlined"
          startIcon={isQuerying ? <CircularProgress size={20} /> : <FolderIcon />}
          onClick={handleGetAppPath}
          disabled={!deviceId || !queryPackage.trim() || isQuerying}
          fullWidth
          sx={{ mb: 1 }}
        >
          {isQuerying ? t.apps.querying : t.apps.getAppPath}
        </Button>
        {appPath && (
          <TextField
            fullWidth
            size="small"
            value={appPath}
            InputProps={{
              readOnly: true,
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    size="small"
                    onClick={() => handleCopyToClipboard(appPath)}
                  >
                    <CopyIcon fontSize="small" />
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />
        )}
      </Box>
    </Paper>
  )
}
