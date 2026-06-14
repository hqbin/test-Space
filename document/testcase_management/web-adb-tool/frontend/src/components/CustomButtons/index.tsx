/**
 * 自定义按钮组件
 * 
 * 功能：
 * - 显示自定义按钮列表
 * - 创建、编辑、删除自定义按钮
 * - 执行自定义 ADB 命令
 * 
 * 数据存储：使用浏览器 localStorage
 */

import React, { useState, useEffect, useRef } from 'react'
import {
  Box,
  Button,
  Card,
  CardContent,
  Grid,
  IconButton,
  Typography,
  CircularProgress,
  Snackbar,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material'
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  PlayArrow as PlayIcon,
} from '@mui/icons-material'
import { executeAdbCommand, executeShellCommand } from '@services/localAgent'
import {
  getCustomButtons,
  saveCustomButton,
  updateCustomButton,
  deleteCustomButton,
  type CustomButton,
} from '@utils/localStorage'
import ButtonDialog from './ButtonDialog'
import { useDeviceStore } from '../../store/deviceStore'
import { useTranslation } from '@hooks/useTranslation'

const CustomButtons: React.FC = () => {
  const { t } = useTranslation()
  const [buttons, setButtons] = useState<CustomButton[]>([])
  const [draggedIndex, setDraggedIndex] = useState<number | null>(null)
  const isDraggingRef = useRef(false)
  const [snackbar, setSnackbar] = useState<{
    open: boolean
    message: string
    severity: 'success' | 'error' | 'info'
  }>({
    open: false,
    message: '',
    severity: 'info',
  })
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingButton, setEditingButton] = useState<CustomButton | null>(null)
  const [executing, setExecuting] = useState<string | null>(null)
  const [resultDialogOpen, setResultDialogOpen] = useState(false)
  const [executionResult, setExecutionResult] = useState<{
    command: string
    output: string
    returnCode: number
  } | null>(null)

  const { selectedDevice } = useDeviceStore()

  // 加载自定义按钮列表
  const loadButtons = () => {
    try {
      const loadedButtons = getCustomButtons()
      setButtons(loadedButtons)
    } catch (err) {
      showSnackbar(t.messages.operationFailed, 'error')
      console.error('Load buttons error:', err)
    }
  }

  useEffect(() => {
    loadButtons()
  }, [])

  // 显示Snackbar
  const showSnackbar = (message: string, severity: 'success' | 'error' | 'info') => {
    setSnackbar({ open: true, message, severity })
  }

  // 关闭Snackbar
  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false })
  }

  // 打开创建对话框
  const handleCreate = () => {
    setEditingButton(null)
    setDialogOpen(true)
  }

  // 打开编辑对话框
  const handleEdit = (button: CustomButton) => {
    setEditingButton(button)
    setDialogOpen(true)
  }

  // 删除按钮
  const handleDelete = (buttonId: string) => {
    if (!confirm(t.customButtons.confirmDelete)) {
      return
    }

    try {
      const success = deleteCustomButton(buttonId)
      if (success) {
        showSnackbar(t.customButtons.deleteSuccess, 'success')
        loadButtons()
      } else {
        showSnackbar(t.customButtons.deleteFailed, 'error')
      }
    } catch (err) {
      showSnackbar(t.customButtons.deleteFailed, 'error')
      console.error('Delete button error:', err)
    }
  }

  // 执行按钮命令
  const handleExecute = async (button: CustomButton) => {
    try {
      setExecuting(button.id)

      const originalCommand = button.command.trim()
      let response: any
      
      // 判断是否是 ADB 命令
      if (originalCommand.includes('adb')) {
        // 检查是否是全局命令（不需要设备 ID）
        const globalCmds = ['devices', 'start-server', 'kill-server', 'version', 'help', 'connect', 'disconnect']
        
        let isGlobalCmd = false
        for (const cmd of globalCmds) {
          if (originalCommand.includes(`adb ${cmd}`)) {
            isGlobalCmd = true
            break
          }
        }
        
        // 提取 adb 后面的参数
        let adbArgs = originalCommand.replace(/^adb\s+/, '').trim()
        
        // 如果不是全局命令且没有 -s 参数，且有选中的设备，则注入设备 ID
        if (!isGlobalCmd && !adbArgs.startsWith('-s') && selectedDevice) {
          adbArgs = `-s ${selectedDevice.device_id} ${adbArgs}`
        }
        
        // 拆分参数
        const args = adbArgs.match(/(?:[^\s"]+|"[^"]*")+/g) || []
        
        // 通过 ADB 接口执行（不会弹黑框）
        response = await executeAdbCommand(args)
      } else {
        // 非 ADB 命令：通过 shell 接口执行（会弹黑框）
        response = await executeShellCommand(originalCommand)
      }

      if (response.success) {
        // 显示执行结果对话框
        setExecutionResult({
          command: originalCommand,
          output: response.output || '',
          returnCode: 0,
        })
        setResultDialogOpen(true)
      } else {
        // 显示详细的错误信息
        const errorMsg = response.error || t.messages.unknownError
        const outputMsg = response.output ? `\n输出: ${response.output}` : ''
        showSnackbar(`${t.customButtons.executeFailed}: ${errorMsg}${outputMsg}`, 'error')
        
        // 同时在结果对话框中显示错误
        setExecutionResult({
          command: originalCommand,
          output: response.output || errorMsg,
          returnCode: 1,
        })
        setResultDialogOpen(true)
      }
    } catch (err: any) {
      showSnackbar(`${t.customButtons.executeFailed}: ${err.message || t.messages.unknownError}`, 'error')
      console.error('Execute command error:', err)
    } finally {
      setExecuting(null)
    }
  }

  // 保存按钮（创建或更新）
  const handleSave = (buttonData: Omit<CustomButton, 'id' | 'created_at'>) => {
    try {
      if (editingButton) {
        // 更新现有按钮
        const success = updateCustomButton(editingButton.id, buttonData)
        if (!success) {
          showSnackbar(t.customButtons.updateFailed, 'error')
          return
        }
        showSnackbar(t.customButtons.updateSuccess, 'success')
      } else {
        // 创建新按钮
        saveCustomButton(buttonData)
        showSnackbar(t.customButtons.createSuccess, 'success')
      }

      setDialogOpen(false)
      loadButtons()
    } catch (err) {
      showSnackbar(editingButton ? t.customButtons.updateFailed : t.customButtons.createFailed, 'error')
      console.error('Save button error:', err)
    }
  }

  // 拖拽开始
  const handleDragStart = (index: number) => {
    setDraggedIndex(index)
    isDraggingRef.current = true
  }

  // 拖拽经过
  const handleDragOver = (e: React.DragEvent, index: number) => {
    e.preventDefault()
    
    if (draggedIndex === null || draggedIndex === index) {
      return
    }

    // 重新排列按钮
    const newButtons = [...buttons]
    const draggedButton = newButtons[draggedIndex]
    newButtons.splice(draggedIndex, 1)
    newButtons.splice(index, 0, draggedButton)
    
    setButtons(newButtons)
    setDraggedIndex(index)
    
    // 立即保存到 localStorage（使用正确的 key）
    try {
      localStorage.setItem('adb_tool_custom_buttons', JSON.stringify(newButtons))
    } catch (err) {
      console.error('Save order error:', err)
    }
  }

  // 拖拽结束
  const handleDragEnd = () => {
    if (isDraggingRef.current) {
      showSnackbar(t.customButtons.orderSaved || '顺序已保存', 'success')
      isDraggingRef.current = false
    }
    setDraggedIndex(null)
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* 标题和创建按钮 */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h5">{t.customButtons.title}</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleCreate}
        >
          {t.customButtons.addButton}
        </Button>
      </Box>

      {/* 按钮列表 */}
      {buttons.length === 0 && (
        <Alert severity="info">
          {t.customButtons.noButtons}
        </Alert>
      )}

      {buttons.length > 0 && (
        <>
          <Alert severity="info" sx={{ mb: 2 }}>
            💡 {t.customButtons.dragToReorder}
          </Alert>
          <Grid container spacing={2}>
            {buttons.map((button, index) => (
              <Grid item xs={12} sm={6} md={4} key={button.id}>
              <Card
                draggable
                onDragStart={() => handleDragStart(index)}
                onDragOver={(e) => handleDragOver(e, index)}
                onDragEnd={handleDragEnd}
                sx={{
                  cursor: 'move',
                  opacity: draggedIndex === index ? 0.5 : 1,
                  transition: 'opacity 0.2s',
                  '&:hover': {
                    boxShadow: 3,
                  },
                }}
              >
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="h6" noWrap sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Box
                        component="span"
                        sx={{
                          display: 'inline-block',
                          width: 4,
                          height: 20,
                          bgcolor: 'primary.main',
                          borderRadius: 1,
                          cursor: 'grab',
                          '&:active': {
                            cursor: 'grabbing',
                          },
                        }}
                      />
                      {button.name}
                    </Typography>
                    <Box>
                      <IconButton
                        size="small"
                        onClick={() => handleEdit(button)}
                        title={t.customButtons.edit}
                      >
                        <EditIcon fontSize="small" />
                      </IconButton>
                      <IconButton
                        size="small"
                        onClick={() => handleDelete(button.id)}
                        title={t.customButtons.delete}
                        color="error"
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </Box>
                  </Box>

                  {button.description && (
                    <Typography
                      variant="body2"
                      color="text.secondary"
                      sx={{ mb: 2 }}
                    >
                      {button.description}
                    </Typography>
                  )}

                  <Typography
                    variant="caption"
                    sx={{
                      display: 'block',
                      mb: 2,
                      p: 1,
                      bgcolor: 'grey.100',
                      borderRadius: 1,
                      fontFamily: 'monospace',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                    }}
                  >
                    {button.command}
                  </Typography>

                  <Button
                    variant="contained"
                    startIcon={
                      executing === button.id ? (
                        <CircularProgress size={16} color="inherit" />
                      ) : (
                        <PlayIcon />
                      )
                    }
                    onClick={() => handleExecute(button)}
                    disabled={executing === button.id}
                    fullWidth
                  >
                    {executing === button.id ? t.customButtons.executing : t.customButtons.execute}
                  </Button>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
        </>
      )}

      {/* 创建/编辑对话框 */}
      <ButtonDialog
        open={dialogOpen}
        button={editingButton}
        onClose={() => setDialogOpen(false)}
        onSave={handleSave}
      />

      {/* 执行结果对话框 */}
      <Dialog
        open={resultDialogOpen}
        onClose={() => setResultDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>{t.customButtons.executionResult}</DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2 }}>
            {/* 命令 */}
            <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
              {t.customButtons.command}:
            </Typography>
            <Box
              sx={{
                p: 1.5,
                mb: 2,
                bgcolor: 'grey.100',
                borderRadius: 1,
                fontFamily: 'monospace',
                fontSize: '0.875rem',
                wordBreak: 'break-all',
              }}
            >
              {executionResult?.command}
            </Box>

            {/* 返回码 */}
            <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
              {t.customButtons.returnCode}:
              <Typography
                component="span"
                sx={{
                  ml: 1,
                  color: executionResult?.returnCode === 0 ? 'success.main' : 'error.main',
                  fontWeight: 600,
                }}
              >
                {executionResult?.returnCode}
              </Typography>
            </Typography>

            {/* 输出 */}
            <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1, mt: 2 }}>
              {t.customButtons.commandOutput}:
            </Typography>
            <Box
              sx={{
                p: 1.5,
                bgcolor: '#1e1e1e',
                color: '#d4d4d4',
                borderRadius: 1,
                fontFamily: 'monospace',
                fontSize: '0.875rem',
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-all',
                maxHeight: 400,
                overflow: 'auto',
              }}
            >
              {executionResult?.output || `(${t.customButtons.noOutput})`}
            </Box>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setResultDialogOpen(false)}>{t.common.close}</Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar通知 */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={3000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert
          onClose={handleCloseSnackbar}
          severity={snackbar.severity}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  )
}

export default CustomButtons
