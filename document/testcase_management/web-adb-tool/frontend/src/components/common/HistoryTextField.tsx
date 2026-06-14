/**
 * HistoryTextField
 *
 * 带历史记录下拉的输入框：
 * - 通过 historyKey 区分不同输入位置
 * - 每个 key 最多保留 15 条历史，最新替换最旧
 * - 调用 commit() 后才会写入历史；外部在执行操作成功时调用即可
 */

import React, { useEffect, useImperativeHandle, useState, forwardRef, useRef, useCallback } from 'react'
import {
  Autocomplete,
  TextField,
  TextFieldProps,
  IconButton,
  Tooltip,
  CircularProgress,
  Popper,
} from '@mui/material'
import { History as HistoryIcon, Close as CloseIcon } from '@mui/icons-material'
import {
  addInputHistory,
  clearInputHistory,
  getInputHistory,
} from '@utils/localStorage'

export interface HistoryTextFieldHandle {
  commit: () => void
}

interface HistoryTextFieldProps {
  historyKey: string
  value: string
  onChange: (value: string) => void
  placeholder?: string
  disabled?: boolean
  size?: TextFieldProps['size']
  fullWidth?: boolean
  startAdornment?: React.ReactNode
  endAdornment?: React.ReactNode
  loading?: boolean
  onEnter?: () => void
  onBlur?: () => void
  sx?: TextFieldProps['sx']
  inputSx?: object
}

export const HistoryTextField = forwardRef<HistoryTextFieldHandle, HistoryTextFieldProps>(
  function HistoryTextField(
    {
      historyKey,
      value,
      onChange,
      placeholder,
      disabled,
      size = 'small',
      fullWidth = true,
      startAdornment,
      endAdornment,
      loading,
      onEnter,
      onBlur,
      sx,
      inputSx,
    },
    ref,
  ) {
    const [options, setOptions] = useState<string[]>([])
    const rootRef = useRef<HTMLDivElement>(null)
    const [popupWidth, setPopupWidth] = useState<number>(0)

    // 用 getBoundingClientRect 获取输入框视觉宽度（受 transform scale 影响），
    // 覆盖 MUI 内部用 clientWidth 计算的宽度，使下拉框与输入框等宽
    const updateWidth = useCallback(() => {
      if (rootRef.current) {
        const inputEl = rootRef.current.querySelector('.MuiOutlinedInput-root') as HTMLElement
        if (inputEl) {
          setPopupWidth(Math.round(inputEl.getBoundingClientRect().width))
        }
      }
    }, [])

    useEffect(() => {
      setOptions(getInputHistory(historyKey))
    }, [historyKey])

    useEffect(() => {
      updateWidth()
      window.addEventListener('resize', updateWidth)
      return () => window.removeEventListener('resize', updateWidth)
    }, [updateWidth])

    useImperativeHandle(ref, () => ({
      commit: () => {
        if (value.trim()) {
          addInputHistory(historyKey, value.trim())
          setOptions(getInputHistory(historyKey))
        }
      },
    }))

    const CustomPopper = useCallback(
      (popperProps: any) => (
        <Popper
          {...popperProps}
          style={{ ...popperProps.style, minWidth: popupWidth || undefined, width: undefined }}
        />
      ),
      [popupWidth],
    )

    return (
      <Autocomplete
        freeSolo
        disableClearable
        size={size}
        fullWidth={fullWidth}
        disabled={disabled}
        options={options}
        value={value}
        inputValue={value}
        onInputChange={(_, newValue) => onChange(newValue)}
        onChange={(_, newValue) => {
          if (typeof newValue === 'string') onChange(newValue)
        }}
        forcePopupIcon={false}
        sx={sx}
        ref={rootRef}
        onOpen={updateWidth}
        PopperComponent={CustomPopper}
        slotProps={{
          paper: {
            sx: {
              fontSize: '0.78rem',
              border: '1px solid #e2e8f0',
              boxShadow: '0 4px 16px rgba(15, 23, 42, 0.08)',
              borderRadius: 1.5,
              '& .MuiAutocomplete-option': {
                fontSize: '0.78rem',
                py: 0.5,
                px: 1,
                fontFamily: 'ui-monospace, SFMono-Regular, monospace',
              },
            },
          },
        }}
        renderOption={(props, option) => (
          <li
            {...props}
            key={option}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: 8,
            }}
          >
            <span
              style={{
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
                flex: 1,
              }}
            >
              {option}
            </span>
            <IconButton
              size="small"
              onMouseDown={(e) => e.preventDefault()}
              onClick={(e) => {
                e.stopPropagation()
                const next = options.filter((o) => o !== option)
                // rewrite history: clear then re-add in order
                clearInputHistory(historyKey)
                ;[...next].reverse().forEach((v) => addInputHistory(historyKey, v))
                setOptions(next)
              }}
              sx={{ p: 0.25, color: '#cbd5e1', '&:hover': { color: '#ef4444' } }}
            >
              <CloseIcon sx={{ fontSize: 12 }} />
            </IconButton>
          </li>
        )}
        renderInput={(params) => (
          <TextField
            {...params}
            placeholder={placeholder}
            size={size}
            onBlur={onBlur}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                onEnter?.()
              }
            }}
            InputProps={{
              ...params.InputProps,
              startAdornment: startAdornment ?? params.InputProps.startAdornment,
              endAdornment: (
                <>
                  {loading && (
                    <CircularProgress size={14} sx={{ mr: 0.5, color: '#94a3b8' }} />
                  )}
                  {options.length > 0 && (
                    <Tooltip title={`${options.length} 条历史`}>
                      <HistoryIcon
                        sx={{
                          fontSize: 14,
                          color: '#94a3b8',
                          mr: 0.25,
                          opacity: 0.7,
                        }}
                      />
                    </Tooltip>
                  )}
                  {endAdornment}
                </>
              ),
              sx: inputSx,
            }}
          />
        )}
      />
    )
  },
)
