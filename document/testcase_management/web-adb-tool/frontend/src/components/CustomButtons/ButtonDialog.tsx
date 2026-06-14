/**
 * 按钮创建/编辑对话框
 */

import React, { useState, useEffect } from 'react'
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Box,
} from '@mui/material'
import type { CustomButton } from '../../types/api'
import { useTranslation } from '@hooks/useTranslation'

interface ButtonDialogProps {
  open: boolean
  button: CustomButton | null
  onClose: () => void
  onSave: (button: Omit<CustomButton, 'id'>) => void
}

const ButtonDialog: React.FC<ButtonDialogProps> = ({
  open,
  button,
  onClose,
  onSave,
}) => {
  const { t } = useTranslation()
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [command, setCommand] = useState('')
  const [errors, setErrors] = useState<Record<string, string>>({})

  // 当对话框打开或按钮改变时，更新表单
  useEffect(() => {
    if (open) {
      if (button) {
        setName(button.name)
        setDescription(button.description || '')
        setCommand(button.command)
      } else {
        setName('')
        setDescription('')
        setCommand('')
      }
      setErrors({})
    }
  }, [open, button])

  // 验证表单
  const validate = (): boolean => {
    const newErrors: Record<string, string> = {}

    if (!name.trim()) {
      newErrors.name = t.customButtons.nameRequired
    }

    if (!command.trim()) {
      newErrors.command = t.customButtons.commandRequired
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  // 处理保存
  const handleSave = () => {
    if (!validate()) {
      return
    }

    onSave({
      name: name.trim(),
      description: description.trim(),
      command: command.trim(),
    })
  }

  // 处理取消
  const handleCancel = () => {
    onClose()
  }

  return (
    <Dialog open={open} onClose={handleCancel} maxWidth="sm" fullWidth>
      <DialogTitle>
        {button ? t.customButtons.editButton : t.customButtons.addButton}
      </DialogTitle>

      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
          {/* 按钮名称 */}
          <TextField
            label={t.customButtons.buttonName}
            value={name}
            onChange={(e) => setName(e.target.value)}
            error={!!errors.name}
            helperText={errors.name || t.customButtons.buttonNameHelper || '显示在按钮上的名称'}
            fullWidth
            required
          />

          {/* 按钮描述 */}
          <TextField
            label={t.customButtons.buttonDescription || '按钮描述'}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            helperText={t.customButtons.buttonDescriptionHelper || '可选，描述按钮的功能'}
            fullWidth
            multiline
            rows={2}
          />

          {/* ADB 命令 */}
          <TextField
            label={t.customButtons.command}
            value={command}
            onChange={(e) => setCommand(e.target.value)}
            error={!!errors.command}
            helperText={errors.command || t.customButtons.commandPlaceholder}
            fullWidth
            required
            multiline
            rows={3}
            sx={{
              '& textarea': {
                fontFamily: 'monospace',
                fontSize: '0.9rem',
              },
            }}
          />
        </Box>
      </DialogContent>

      <DialogActions>
        <Button onClick={handleCancel}>{t.common.cancel}</Button>
        <Button onClick={handleSave} variant="contained">
          {t.common.save}
        </Button>
      </DialogActions>
    </Dialog>
  )
}

export default ButtonDialog
