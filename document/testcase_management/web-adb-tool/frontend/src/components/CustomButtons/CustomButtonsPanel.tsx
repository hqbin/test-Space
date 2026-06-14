/**
 * CustomButtonsPanel
 *
 * 用于在仪表板右栏内做"转场展开"的自定义按钮管理面板。
 * 包含：
 *  - 按钮列表（拖拽排序）
 *  - 添加 / 编辑 / 删除
 *  - 执行（含执行结果对话框）
 *  - 顶部"返回"按钮触发 onBack
 *
 * 与原 CustomButtons 组件保持相同的执行逻辑（ADB / shell 选择、设备 ID 注入等）。
 */

import React, { useEffect, useRef, useState } from 'react'
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  Paper,
  Snackbar,
  Stack,
  Tooltip,
  Typography,
} from '@mui/material'
import {
  Add as AddIcon,
  ArrowBack as ArrowBackIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  PlayArrow as PlayIcon,
  TouchApp as TouchAppIcon,
  DragIndicator as DragIcon,
} from '@mui/icons-material'
import { executeAdbCommand, executeShellCommand } from '@services/localAgent'
import {
  deleteCustomButton,
  getCustomButtons,
  saveCustomButton,
  updateCustomButton,
  type CustomButton,
} from '@utils/localStorage'
import { useDeviceStore } from '@store/deviceStore'
import { useTranslation } from '@hooks/useTranslation'
import ButtonDialog from './ButtonDialog'

interface CustomButtonsPanelProps {
  onBack: () => void
}

const cardSx = {
  p: 1.75,
  borderRadius: 2,
  border: '1px solid rgba(226, 232, 240, 0.9)',
  bgcolor: 'rgba(255, 255, 255, 0.85)',
  backdropFilter: 'blur(12px)',
  WebkitBackdropFilter: 'blur(12px)',
  boxShadow: '0 1px 3px rgba(15, 23, 42, 0.04)',
  display: 'flex',
  flexDirection: 'column',
  minHeight: 0,
}

const glassBtnSx = {
  py: 0.5,
  px: 1.25,
  fontSize: '0.78rem',
  fontWeight: 500,
  textTransform: 'none' as const,
  borderRadius: '8px',
  minHeight: 32,
  lineHeight: 1.3,
  whiteSpace: 'nowrap' as const,
  color: '#475569',
  bgcolor: 'rgba(255, 255, 255, 0.6)',
  border: '1px solid rgba(226, 232, 240, 0.8)',
  backdropFilter: 'blur(8px)',
  WebkitBackdropFilter: 'blur(8px)',
  boxShadow: '0 1px 2px rgba(15, 23, 42, 0.03)',
  transition: 'all 0.15s ease',
  cursor: 'pointer',
  '&:hover': {
    bgcolor: 'rgba(238, 242, 255, 0.85)',
    borderColor: '#6366f1',
    color: '#4f46e5',
    boxShadow: '0 4px 10px rgba(99, 102, 241, 0.12)',
  },
  '& .MuiButton-startIcon': {
    color: '#6366f1',
    mr: 0.5,
  },
  '&:hover .MuiButton-startIcon': { color: '#4f46e5' },
  '&.Mui-disabled': {
    color: '#cbd5e1',
    bgcolor: 'rgba(248, 250, 252, 0.6)',
    borderColor: 'rgba(226, 232, 240, 0.6)',
    boxShadow: 'none',
  },
}

export const CustomButtonsPanel: React.FC<CustomButtonsPanelProps> = ({ onBack }) => {
  const { t } = useTranslation()
  const { selectedDevice } = useDeviceStore()

  const [buttons, setButtons] = useState<CustomButton[]>([])
  const [draggedIndex, setDraggedIndex] = useState<number | null>(null)
  const isDraggingRef = useRef(false)

  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingButton, setEditingButton] = useState<CustomButton | null>(null)

  const [executing, setExecuting] = useState<string | null>(null)
  const [resultDialogOpen, setResultDialogOpen] = useState(false)
  const [executionResult, setExecutionResult] = useState<{
    command: string
    output: string
    returnCode: number
  } | null>(null)

  const [snackbar, setSnackbar] = useState<{
    open: boolean
    message: string
    severity: 'success' | 'error' | 'info'
  }>({ open: false, message: '', severity: 'info' })

  const showSnackbar = (
    message: string,
    severity: 'success' | 'error' | 'info' = 'info',
  ) => {
    setSnackbar({ open: true, message, severity })
  }

  const loadButtons = () => {
    try {
      setButtons(getCustomButtons())
    } catch (err) {
      showSnackbar(t.messages.operationFailed, 'error')
      console.error(err)
    }
  }

  useEffect(() => {
    loadButtons()
  }, [])

  const handleCreate = () => {
    setEditingButton(null)
    setDialogOpen(true)
  }

  const handleEdit = (button: CustomButton) => {
    setEditingButton(button)
    setDialogOpen(true)
  }

  const handleDelete = (buttonId: string) => {
    if (!confirm(t.customButtons.confirmDelete)) return
    try {
      const ok = deleteCustomButton(buttonId)
      if (ok) {
        showSnackbar(t.customButtons.deleteSuccess, 'success')
        loadButtons()
      } else {
        showSnackbar(t.customButtons.deleteFailed, 'error')
      }
    } catch (err) {
      showSnackbar(t.customButtons.deleteFailed, 'error')
      console.error(err)
    }
  }

  const handleExecute = async (button: CustomButton) => {
    try {
      setExecuting(button.id)
      const originalCommand = button.command.trim()
      let response: any

      if (originalCommand.includes('adb')) {
        const globalCmds = [
          'devices',
          'start-server',
          'kill-server',
          'version',
          'help',
          'connect',
          'disconnect',
        ]
        let isGlobalCmd = false
        for (const cmd of globalCmds) {
          if (originalCommand.includes(`adb ${cmd}`)) {
            isGlobalCmd = true
            break
          }
        }
        let adbArgs = originalCommand.replace(/^adb\s+/, '').trim()
        if (!isGlobalCmd && !adbArgs.startsWith('-s') && selectedDevice) {
          adbArgs = `-s ${selectedDevice.device_id} ${adbArgs}`
        }
        const args = adbArgs.match(/(?:[^\s"]+|"[^"]*")+/g) || []
        response = await executeAdbCommand(args)
      } else {
        response = await executeShellCommand(originalCommand)
      }

      if (response.success) {
        setExecutionResult({
          command: originalCommand,
          output: response.output || '',
          returnCode: 0,
        })
        setResultDialogOpen(true)
      } else {
        const errorMsg = response.error || t.messages.unknownError
        const outputMsg = response.output ? `\n输出: ${response.output}` : ''
        showSnackbar(`${t.customButtons.executeFailed}: ${errorMsg}${outputMsg}`, 'error')
        setExecutionResult({
          command: originalCommand,
          output: response.output || errorMsg,
          returnCode: 1,
        })
        setResultDialogOpen(true)
      }
    } catch (err: any) {
      showSnackbar(
        `${t.customButtons.executeFailed}: ${err.message || t.messages.unknownError}`,
        'error',
      )
      console.error(err)
    } finally {
      setExecuting(null)
    }
  }

  const handleSave = (
    buttonData: Omit<CustomButton, 'id' | 'created_at'>,
  ) => {
    try {
      if (editingButton) {
        const ok = updateCustomButton(editingButton.id, buttonData)
        if (!ok) {
          showSnackbar(t.customButtons.updateFailed, 'error')
          return
        }
        showSnackbar(t.customButtons.updateSuccess, 'success')
      } else {
        saveCustomButton(buttonData)
        showSnackbar(t.customButtons.createSuccess, 'success')
      }
      setDialogOpen(false)
      loadButtons()
    } catch (err) {
      showSnackbar(
        editingButton ? t.customButtons.updateFailed : t.customButtons.createFailed,
        'error',
      )
      console.error(err)
    }
  }

  const handleDragStart = (index: number) => {
    setDraggedIndex(index)
    isDraggingRef.current = true
  }

  const handleDragOver = (e: React.DragEvent, index: number) => {
    e.preventDefault()
    if (draggedIndex === null || draggedIndex === index) return
    const next = [...buttons]
    const dragged = next[draggedIndex]
    next.splice(draggedIndex, 1)
    next.splice(index, 0, dragged)
    setButtons(next)
    setDraggedIndex(index)
    try {
      localStorage.setItem('adb_tool_custom_buttons', JSON.stringify(next))
    } catch (err) {
      console.error(err)
    }
  }

  const handleDragEnd = () => {
    if (isDraggingRef.current) {
      showSnackbar(t.customButtons.orderSaved || '顺序已保存', 'success')
      isDraggingRef.current = false
    }
    setDraggedIndex(null)
  }

  return (
    <Paper sx={{ ...cardSx, flex: 1, minHeight: 0, overflow: 'hidden' }}>
      {/* 头部：返回 + 标题 + 添加 */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 1,
          mb: 1.25,
          flexShrink: 0,
        }}
      >
        <Tooltip title={t.common.back}>
          <IconButton
            size="small"
            onClick={onBack}
            sx={{
              color: '#475569',
              bgcolor: 'rgba(255,255,255,0.6)',
              border: '1px solid rgba(226, 232, 240, 0.8)',
              '&:hover': {
                bgcolor: 'rgba(238, 242, 255, 0.85)',
                color: '#4f46e5',
                borderColor: '#6366f1',
              },
            }}
          >
            <ArrowBackIcon sx={{ fontSize: 18 }} />
          </IconButton>
        </Tooltip>
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 0.75,
            fontSize: '0.95rem',
            fontWeight: 700,
            color: '#0f172a',
          }}
        >
          <TouchAppIcon sx={{ fontSize: 18, color: '#6366f1' }} />
          {t.customButtons.title}
          <Typography sx={{ fontSize: '0.72rem', color: '#94a3b8', ml: 0.5 }}>
            ({buttons.length})
          </Typography>
        </Box>
        <Box sx={{ flex: 1 }} />
        <Button
          variant="outlined"
          size="small"
          startIcon={<AddIcon sx={{ fontSize: 16 }} />}
          onClick={handleCreate}
          sx={glassBtnSx}
        >
          {t.customButtons.addButton}
        </Button>
      </Box>

      {/* 提示 */}
      {buttons.length > 0 && (
        <Typography
          sx={{
            fontSize: '0.72rem',
            color: '#94a3b8',
            mb: 0.75,
            flexShrink: 0,
          }}
        >
          💡 {t.customButtons.dragToReorder}
        </Typography>
      )}

      {/* 按钮列表 */}
      <Box
        sx={{
          flex: 1,
          minHeight: 0,
          overflow: 'auto',
          border: '1px solid rgba(241, 245, 249, 0.9)',
          borderRadius: 1.5,
          bgcolor: 'rgba(255, 255, 255, 0.5)',
          p: 1,
        }}
      >
        {buttons.length === 0 ? (
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <Typography sx={{ fontSize: '0.85rem', color: '#64748b', mb: 0.5 }}>
              {t.customButtons.noButtons}
            </Typography>
            <Typography sx={{ fontSize: '0.75rem', color: '#94a3b8' }}>
              {t.customButtons.createFirst}
            </Typography>
          </Box>
        ) : (
          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: {
                xs: '1fr',
                sm: 'repeat(2, minmax(0, 1fr))',
                md: 'repeat(3, minmax(0, 1fr))',
                lg: 'repeat(4, minmax(0, 1fr))',
              },
              gap: 1,
            }}
          >
            {buttons.map((button, index) => (
              <Box
                key={button.id}
                draggable
                onDragStart={() => handleDragStart(index)}
                onDragOver={(e) => handleDragOver(e, index)}
                onDragEnd={handleDragEnd}
                sx={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 0.5,
                  p: 1,
                  borderRadius: 1.5,
                  border: '1px solid rgba(226, 232, 240, 0.9)',
                  bgcolor: 'rgba(255, 255, 255, 0.85)',
                  backdropFilter: 'blur(8px)',
                  WebkitBackdropFilter: 'blur(8px)',
                  boxShadow: '0 1px 2px rgba(15, 23, 42, 0.04)',
                  opacity: draggedIndex === index ? 0.4 : 1,
                  cursor: 'move',
                  transition: 'all 0.15s',
                  minHeight: 0,
                  '&:hover': {
                    borderColor: '#6366f1',
                    boxShadow: '0 4px 10px rgba(99, 102, 241, 0.12)',
                    transform: 'translateY(-1px)',
                  },
                }}
              >
                {/* 标题行：拖拽 + 名称 + 操作 */}
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                  <DragIcon
                    sx={{ fontSize: 14, color: '#cbd5e1', cursor: 'grab', flexShrink: 0 }}
                  />
                  <Tooltip title={button.name} enterDelay={500}>
                    <Typography
                      sx={{
                        fontSize: '0.85rem',
                        fontWeight: 600,
                        color: '#0f172a',
                        flex: 1,
                        minWidth: 0,
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      {button.name}
                    </Typography>
                  </Tooltip>
                  <Tooltip title={t.customButtons.edit}>
                    <IconButton
                      size="small"
                      onClick={() => handleEdit(button)}
                      sx={{
                        p: 0.25,
                        color: '#94a3b8',
                        '&:hover': {
                          color: '#6366f1',
                          bgcolor: 'rgba(99, 102, 241, 0.08)',
                        },
                      }}
                    >
                      <EditIcon sx={{ fontSize: 14 }} />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title={t.customButtons.delete}>
                    <IconButton
                      size="small"
                      onClick={() => handleDelete(button.id)}
                      sx={{
                        p: 0.25,
                        color: '#cbd5e1',
                        '&:hover': {
                          color: '#ef4444',
                          bgcolor: 'rgba(239, 68, 68, 0.08)',
                        },
                      }}
                    >
                      <DeleteIcon sx={{ fontSize: 14 }} />
                    </IconButton>
                  </Tooltip>
                </Box>

                {/* 描述（可选） */}
                {button.description && (
                  <Tooltip title={button.description} enterDelay={500}>
                    <Typography
                      sx={{
                        fontSize: '0.7rem',
                        color: '#64748b',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      {button.description}
                    </Typography>
                  </Tooltip>
                )}

                {/* 命令预览 */}
                <Tooltip title={button.command} enterDelay={500}>
                  <Typography
                    sx={{
                      fontSize: '0.68rem',
                      fontFamily: 'ui-monospace, SFMono-Regular, monospace',
                      color: '#475569',
                      bgcolor: 'rgba(241, 245, 249, 0.8)',
                      px: 0.75,
                      py: 0.25,
                      borderRadius: 0.75,
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {button.command}
                  </Typography>
                </Tooltip>

                {/* 执行按钮 */}
                <Button
                  size="small"
                  variant="contained"
                  fullWidth
                  startIcon={
                    executing === button.id ? (
                      <CircularProgress size={12} color="inherit" />
                    ) : (
                      <PlayIcon sx={{ fontSize: 14 }} />
                    )
                  }
                  onClick={() => handleExecute(button)}
                  disabled={executing === button.id}
                  sx={{
                    fontSize: '0.75rem',
                    py: 0.5,
                    minHeight: 28,
                    textTransform: 'none',
                    cursor: 'pointer',
                    bgcolor: '#6366f1',
                    boxShadow: '0 2px 4px rgba(99, 102, 241, 0.2)',
                    '&:hover': {
                      bgcolor: '#4f46e5',
                      boxShadow: '0 4px 8px rgba(99, 102, 241, 0.3)',
                    },
                  }}
                >
                  {executing === button.id
                    ? t.customButtons.executing
                    : t.customButtons.execute}
                </Button>
              </Box>
            ))}
          </Box>
        )}
      </Box>

      {/* 创建/编辑 */}
      <ButtonDialog
        open={dialogOpen}
        button={editingButton}
        onClose={() => setDialogOpen(false)}
        onSave={handleSave}
      />

      {/* 执行结果 */}
      <Dialog
        open={resultDialogOpen}
        onClose={() => setResultDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle sx={{ fontSize: '1rem', fontWeight: 600 }}>
          {t.customButtons.executionResult}
        </DialogTitle>
        <DialogContent dividers>
          <Stack spacing={1.5}>
            <Box>
              <Typography sx={{ fontSize: '0.78rem', fontWeight: 600, color: '#475569', mb: 0.5 }}>
                {t.customButtons.command}:
              </Typography>
              <Box
                sx={{
                  p: 1.25,
                  bgcolor: '#f8fafc',
                  borderRadius: 1,
                  fontFamily: 'ui-monospace, SFMono-Regular, monospace',
                  fontSize: '0.78rem',
                  border: '1px solid #e2e8f0',
                  wordBreak: 'break-all',
                }}
              >
                {executionResult?.command}
              </Box>
            </Box>
            <Typography sx={{ fontSize: '0.78rem', fontWeight: 600, color: '#475569' }}>
              {t.customButtons.returnCode}:
              <Typography
                component="span"
                sx={{
                  ml: 1,
                  color:
                    executionResult?.returnCode === 0 ? '#10b981' : '#ef4444',
                  fontWeight: 600,
                }}
              >
                {executionResult?.returnCode}
              </Typography>
            </Typography>
            <Box>
              <Typography sx={{ fontSize: '0.78rem', fontWeight: 600, color: '#475569', mb: 0.5 }}>
                {t.customButtons.commandOutput}:
              </Typography>
              <Box
                sx={{
                  p: 1.25,
                  bgcolor: '#1e1e1e',
                  color: '#d4d4d4',
                  borderRadius: 1,
                  fontFamily: 'ui-monospace, SFMono-Regular, monospace',
                  fontSize: '0.78rem',
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-all',
                  maxHeight: 360,
                  overflow: 'auto',
                }}
              >
                {executionResult?.output || `(${t.customButtons.noOutput})`}
              </Box>
            </Box>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setResultDialogOpen(false)} variant="contained">
            {t.common.close}
          </Button>
        </DialogActions>
      </Dialog>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={3000}
        onClose={() => setSnackbar((s) => ({ ...s, open: false }))}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert
          onClose={() => setSnackbar((s) => ({ ...s, open: false }))}
          severity={snackbar.severity}
          variant="filled"
          sx={{ fontSize: '0.85rem' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Paper>
  )
}
