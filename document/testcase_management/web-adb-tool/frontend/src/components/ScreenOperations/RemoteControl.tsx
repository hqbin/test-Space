/**
 * RemoteControl 组件
 * 
 * 虚拟遥控器界面（iOS 风格设计）
 */

import React, { useState } from 'react'
import {
  Box,
  IconButton,
  Paper,
  Snackbar,
  Alert,
} from '@mui/material'
import {
  PowerSettingsNew as PowerIcon,
  Menu as MenuIcon,
  Settings as SettingsIcon,
  KeyboardArrowUp as UpIcon,
  KeyboardArrowDown as DownIcon,
  KeyboardArrowLeft as LeftIcon,
  KeyboardArrowRight as RightIcon,
  FiberManualRecord as OkIcon,
  ArrowBack as BackIcon,
  Home as HomeIcon,
  VolumeUp as VolumeUpIcon,
  VolumeDown as VolumeDownIcon,
  VolumeOff as MuteIcon,
} from '@mui/icons-material'
import { sendKeyevent } from '../../services/localAgent'
import { useTranslation } from '../../hooks/useTranslation'

interface RemoteControlProps {
  deviceId: string | null
  compact?: boolean
}

export const RemoteControl: React.FC<RemoteControlProps> = ({ deviceId, compact = false }) => {
  const { t } = useTranslation()
  const [snackbar, setSnackbar] = useState<{
    open: boolean
    message: string
    severity: 'success' | 'error' | 'info'
  }>({
    open: false,
    message: '',
    severity: 'info',
  })

  const showSnackbar = (message: string, severity: 'success' | 'error' | 'info') => {
    setSnackbar({ open: true, message, severity })
  }

  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false })
  }

  const sendKey = async (keycode: number, _keyName: string) => {
    if (!deviceId) {
      showSnackbar(t.messages.pleaseSelectDevice, 'error')
      return
    }

    try {
      const response = await sendKeyevent(deviceId, keycode)
      if (!response.success) {
        showSnackbar(`${t.remote.sendKeyFailed}: ${response.error}`, 'error')
      }
    } catch (err: any) {
      showSnackbar(`${t.remote.sendKeyFailed}: ${err.message}`, 'error')
    }
  }

  const keys = {
    power: { code: 26, name: t.remote.power },
    menu: { code: 82, name: t.remote.menu },
    settings: { code: 176, name: t.remote.settings },
    up: { code: 19, name: t.remote.up },
    down: { code: 20, name: t.remote.down },
    left: { code: 21, name: t.remote.left },
    right: { code: 22, name: t.remote.right },
    ok: { code: 23, name: t.remote.ok },
    back: { code: 4, name: t.remote.back },
    home: { code: 3, name: t.remote.home },
    volumeUp: { code: 24, name: t.remote.volumeUp },
    volumeDown: { code: 25, name: t.remote.volumeDown },
    mute: { code: 164, name: t.remote.mute },
    num0: { code: 7, name: '0' },
    num1: { code: 8, name: '1' },
    num2: { code: 9, name: '2' },
    num3: { code: 10, name: '3' },
    num4: { code: 11, name: '4' },
    num5: { code: 12, name: '5' },
    num6: { code: 13, name: '6' },
    num7: { code: 14, name: '7' },
    num8: { code: 15, name: '8' },
    num9: { code: 16, name: '9' },
    netflix: { code: 132, name: 'Netflix' },
    youtube: { code: 131, name: 'Youtube' },
    primeVideo: { code: 134, name: 'Prime' },
    disneyPlus: { code: 317, name: 'Disney+' },
  }

  return (
    <>
      <Paper
        elevation={0}
        sx={{
          p: compact ? 1.5 : 3.5,
          bgcolor: '#f5f5f7',
          borderRadius: compact ? 2 : 4,
          border: '1px solid #e0e0e0',
        }}
      >
        {/* 顶部按钮 */}
        <Box sx={{ display: 'flex', gap: 2, mb: 2.5 }}>
          <IconButton
            onClick={() => sendKey(keys.power.code, keys.power.name)}
            disabled={!deviceId}
            sx={{
              flex: 1,
              height: 56,
              bgcolor: '#ff3b30',
              color: 'white',
              borderRadius: 2.5,
              boxShadow: '0 2px 8px rgba(255, 59, 48, 0.3)',
              '&:hover': { bgcolor: '#ff2d20', boxShadow: '0 4px 12px rgba(255, 59, 48, 0.4)' },
              '&:active': { transform: 'scale(0.95)' },
              '&:disabled': { bgcolor: '#e0e0e0', color: '#9e9e9e', boxShadow: 'none' },
              transition: 'all 0.2s ease',
            }}
          >
            <PowerIcon sx={{ fontSize: 26 }} />
          </IconButton>
          <IconButton
            onClick={() => sendKey(keys.menu.code, keys.menu.name)}
            disabled={!deviceId}
            sx={{
              flex: 1,
              height: 52,
              bgcolor: 'white',
              color: '#333',
              borderRadius: 2.5,
              border: '1px solid #d1d1d6',
              boxShadow: '0 2px 8px rgba(0, 0, 0, 0.08)',
              '&:hover': { bgcolor: '#f9f9f9', boxShadow: '0 4px 12px rgba(0, 0, 0, 0.12)' },
              '&:active': { transform: 'scale(0.95)' },
              '&:disabled': { bgcolor: '#e0e0e0', color: '#9e9e9e', border: 'none', boxShadow: 'none' },
              transition: 'all 0.2s ease',
            }}
          >
            <MenuIcon sx={{ fontSize: 26 }} />
          </IconButton>
        </Box>

        {/* 数字键 - 紧凑模式下隐藏以节省空间 */}
        {!compact && (
        <Box sx={{ mb: 2.5 }}>
          <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 1.5 }}>
            {[1, 2, 3, 4, 5, 6, 7, 8, 9].map((num) => {
              const key = keys[`num${num}` as keyof typeof keys] as { code: number; name: string }
              return (
                <IconButton
                  key={num}
                  onClick={() => sendKey(key.code, key.name)}
                  disabled={!deviceId}
                  sx={{
                    height: 50,
                    bgcolor: 'white',
                    color: '#333',
                    borderRadius: 2,
                    border: '1px solid #d1d1d6',
                    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.08)',
                    fontSize: '1.1rem',
                    fontWeight: 600,
                    '&:hover': {
                      bgcolor: '#f9f9f9',
                      boxShadow: '0 4px 12px rgba(0, 0, 0, 0.12)',
                    },
                    '&:active': {
                      transform: 'scale(0.95)',
                    },
                    '&:disabled': {
                      bgcolor: '#e0e0e0',
                      color: '#9e9e9e',
                      border: 'none',
                      boxShadow: 'none',
                    },
                    transition: 'all 0.2s ease',
                  }}
                >
                  {num}
                </IconButton>
              )
            })}
            <Box />
            <IconButton
              onClick={() => sendKey(keys.num0.code, keys.num0.name)}
              disabled={!deviceId}
              sx={{
                height: 50,
                bgcolor: 'white',
                color: '#333',
                borderRadius: 2,
                border: '1px solid #d1d1d6',
                boxShadow: '0 2px 8px rgba(0, 0, 0, 0.08)',
                fontSize: '1.1rem',
                fontWeight: 600,
                '&:hover': {
                  bgcolor: '#f9f9f9',
                  boxShadow: '0 4px 12px rgba(0, 0, 0, 0.12)',
                },
                '&:active': {
                  transform: 'scale(0.95)',
                },
                '&:disabled': {
                  bgcolor: '#e0e0e0',
                  color: '#9e9e9e',
                  border: 'none',
                  boxShadow: 'none',
                },
                transition: 'all 0.2s ease',
              }}
            >
              0
            </IconButton>
            <Box />
          </Box>
        </Box>
        )}

        {/* 方向键 */}
        <Box
          sx={{
            position: 'relative',
            width: '100%',
            aspectRatio: '1',
            mb: 2.5,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Box
            sx={{
              position: 'absolute',
              width: '85%',
              height: '85%',
              borderRadius: '50%',
              bgcolor: 'white',
              border: '1px solid #d1d1d6',
              boxShadow: '0 2px 12px rgba(0, 0, 0, 0.08)',
            }}
          />
          <IconButton
            onClick={() => sendKey(keys.up.code, keys.up.name)}
            disabled={!deviceId}
            sx={{
              position: 'absolute',
              top: '5%',
              left: '50%',
              transform: 'translateX(-50%)',
              width: 64,
              height: 64,
              bgcolor: 'transparent',
              color: '#333',
              '&:hover': {
                bgcolor: 'rgba(0, 0, 0, 0.04)',
              },
              '&:active': {
                bgcolor: 'rgba(0, 0, 0, 0.08)',
              },
              '&:disabled': {
                color: '#9e9e9e',
              },
              transition: 'all 0.15s ease',
            }}
          >
            <UpIcon sx={{ fontSize: 40 }} />
          </IconButton>
          <IconButton
            onClick={() => sendKey(keys.left.code, keys.left.name)}
            disabled={!deviceId}
            sx={{
              position: 'absolute',
              top: '50%',
              left: '5%',
              transform: 'translateY(-50%)',
              width: 64,
              height: 64,
              bgcolor: 'transparent',
              color: '#333',
              '&:hover': {
                bgcolor: 'rgba(0, 0, 0, 0.04)',
              },
              '&:active': {
                bgcolor: 'rgba(0, 0, 0, 0.08)',
              },
              '&:disabled': {
                color: '#9e9e9e',
              },
              transition: 'all 0.15s ease',
            }}
          >
            <LeftIcon sx={{ fontSize: 40 }} />
          </IconButton>
          <IconButton
            onClick={() => sendKey(keys.ok.code, keys.ok.name)}
            disabled={!deviceId}
            sx={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              width: 80,
              height: 80,
              bgcolor: '#007aff',
              color: 'white',
              borderRadius: '50%',
              boxShadow: '0 4px 16px rgba(0, 122, 255, 0.4)',
              '&:hover': {
                bgcolor: '#0051d5',
                boxShadow: '0 6px 20px rgba(0, 122, 255, 0.5)',
              },
              '&:active': {
                transform: 'translate(-50%, -50%) scale(0.92)',
              },
              '&:disabled': {
                bgcolor: '#e0e0e0',
                color: '#9e9e9e',
                boxShadow: 'none',
              },
              transition: 'all 0.2s ease',
            }}
          >
            <OkIcon sx={{ fontSize: 24 }} />
          </IconButton>
          <IconButton
            onClick={() => sendKey(keys.right.code, keys.right.name)}
            disabled={!deviceId}
            sx={{
              position: 'absolute',
              top: '50%',
              right: '5%',
              transform: 'translateY(-50%)',
              width: 64,
              height: 64,
              bgcolor: 'transparent',
              color: '#333',
              '&:hover': {
                bgcolor: 'rgba(0, 0, 0, 0.04)',
              },
              '&:active': {
                bgcolor: 'rgba(0, 0, 0, 0.08)',
              },
              '&:disabled': {
                color: '#9e9e9e',
              },
              transition: 'all 0.15s ease',
            }}
          >
            <RightIcon sx={{ fontSize: 40 }} />
          </IconButton>
          <IconButton
            onClick={() => sendKey(keys.down.code, keys.down.name)}
            disabled={!deviceId}
            sx={{
              position: 'absolute',
              bottom: '5%',
              left: '50%',
              transform: 'translateX(-50%)',
              width: 64,
              height: 64,
              bgcolor: 'transparent',
              color: '#333',
              '&:hover': {
                bgcolor: 'rgba(0, 0, 0, 0.04)',
              },
              '&:active': {
                bgcolor: 'rgba(0, 0, 0, 0.08)',
              },
              '&:disabled': {
                color: '#9e9e9e',
              },
              transition: 'all 0.15s ease',
            }}
          >
            <DownIcon sx={{ fontSize: 40 }} />
          </IconButton>
        </Box>

        {/* 返回和Home */}
        <Box sx={{ display: 'flex', gap: 1.5, mb: 2.5 }}>
          <IconButton
            onClick={() => sendKey(keys.back.code, keys.back.name)}
            disabled={!deviceId}
            sx={{
              flex: 1,
              height: 52,
              bgcolor: 'white',
              color: '#333',
              borderRadius: 2.5,
              border: '1px solid #d1d1d6',
              boxShadow: '0 2px 8px rgba(0, 0, 0, 0.08)',
              '&:hover': {
                bgcolor: '#f9f9f9',
                boxShadow: '0 4px 12px rgba(0, 0, 0, 0.12)',
              },
              '&:active': {
                transform: 'scale(0.95)',
              },
              '&:disabled': {
                bgcolor: '#e0e0e0',
                color: '#9e9e9e',
                border: 'none',
                boxShadow: 'none',
              },
              transition: 'all 0.2s ease',
            }}
          >
            <BackIcon sx={{ fontSize: 26 }} />
          </IconButton>
          <IconButton
            onClick={() => sendKey(keys.home.code, keys.home.name)}
            disabled={!deviceId}
            sx={{
              flex: 1,
              height: 52,
              bgcolor: 'white',
              color: '#333',
              borderRadius: 2.5,
              border: '1px solid #d1d1d6',
              boxShadow: '0 2px 8px rgba(0, 0, 0, 0.08)',
              '&:hover': {
                bgcolor: '#f9f9f9',
                boxShadow: '0 4px 12px rgba(0, 0, 0, 0.12)',
              },
              '&:active': {
                transform: 'scale(0.95)',
              },
              '&:disabled': {
                bgcolor: '#e0e0e0',
                color: '#9e9e9e',
                border: 'none',
                boxShadow: 'none',
              },
              transition: 'all 0.2s ease',
            }}
          >
            <HomeIcon sx={{ fontSize: 26 }} />
          </IconButton>
        </Box>

        {/* 音量控制 */}
        <Box sx={{ display: 'flex', gap: 1.5, mb: 2.5 }}>
          <IconButton
            onClick={() => sendKey(keys.volumeDown.code, keys.volumeDown.name)}
            disabled={!deviceId}
            sx={{
              flex: 1,
              height: 52,
              bgcolor: 'white',
              color: '#333',
              borderRadius: 2.5,
              border: '1px solid #d1d1d6',
              boxShadow: '0 2px 8px rgba(0, 0, 0, 0.08)',
              '&:hover': {
                bgcolor: '#f9f9f9',
                boxShadow: '0 4px 12px rgba(0, 0, 0, 0.12)',
              },
              '&:active': {
                transform: 'scale(0.95)',
              },
              '&:disabled': {
                bgcolor: '#e0e0e0',
                color: '#9e9e9e',
                border: 'none',
                boxShadow: 'none',
              },
              transition: 'all 0.2s ease',
            }}
          >
            <VolumeDownIcon sx={{ fontSize: 26 }} />
          </IconButton>
          <IconButton
            onClick={() => sendKey(keys.mute.code, keys.mute.name)}
            disabled={!deviceId}
            sx={{
              flex: 1,
              height: 52,
              bgcolor: 'white',
              color: '#333',
              borderRadius: 2.5,
              border: '1px solid #d1d1d6',
              boxShadow: '0 2px 8px rgba(0, 0, 0, 0.08)',
              '&:hover': {
                bgcolor: '#f9f9f9',
                boxShadow: '0 4px 12px rgba(0, 0, 0, 0.12)',
              },
              '&:active': {
                transform: 'scale(0.95)',
              },
              '&:disabled': {
                bgcolor: '#e0e0e0',
                color: '#9e9e9e',
                border: 'none',
                boxShadow: 'none',
              },
              transition: 'all 0.2s ease',
            }}
          >
            <MuteIcon sx={{ fontSize: 26 }} />
          </IconButton>
          <IconButton
            onClick={() => sendKey(keys.volumeUp.code, keys.volumeUp.name)}
            disabled={!deviceId}
            sx={{
              flex: 1,
              height: 52,
              bgcolor: 'white',
              color: '#333',
              borderRadius: 2.5,
              border: '1px solid #d1d1d6',
              boxShadow: '0 2px 8px rgba(0, 0, 0, 0.08)',
              '&:hover': {
                bgcolor: '#f9f9f9',
                boxShadow: '0 4px 12px rgba(0, 0, 0, 0.12)',
              },
              '&:active': {
                transform: 'scale(0.95)',
              },
              '&:disabled': {
                bgcolor: '#e0e0e0',
                color: '#9e9e9e',
                border: 'none',
                boxShadow: 'none',
              },
              transition: 'all 0.2s ease',
            }}
          >
            <VolumeUpIcon sx={{ fontSize: 26 }} />
          </IconButton>
        </Box>

        {/* 设置键 */}
        <Box sx={{ mb: 2.5 }}>
          <IconButton
            onClick={() => sendKey(keys.settings.code, keys.settings.name)}
            disabled={!deviceId}
            sx={{
              width: '100%',
              height: 52,
              bgcolor: 'white',
              color: '#333',
              borderRadius: 2.5,
              border: '1px solid #d1d1d6',
              boxShadow: '0 2px 8px rgba(0, 0, 0, 0.08)',
              '&:hover': {
                bgcolor: '#f9f9f9',
                boxShadow: '0 4px 12px rgba(0, 0, 0, 0.12)',
              },
              '&:active': {
                transform: 'scale(0.95)',
              },
              '&:disabled': {
                bgcolor: '#e0e0e0',
                color: '#9e9e9e',
                border: 'none',
                boxShadow: 'none',
              },
              transition: 'all 0.2s ease',
            }}
          >
            <SettingsIcon sx={{ fontSize: 26 }} />
          </IconButton>
        </Box>

        {/* 应用热键 - 紧凑模式下隐藏 */}
        {!compact && (
        <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 1.5 }}>
          {[
            { key: 'netflix', label: 'Netflix' },
            { key: 'youtube', label: 'Youtube' },
            { key: 'primeVideo', label: 'Prime' },
            { key: 'disneyPlus', label: 'Disney+' },
          ].map((app) => {
            const key = keys[app.key as keyof typeof keys] as { code: number; name: string }
            return (
              <IconButton
                key={app.key}
                onClick={() => sendKey(key.code, key.name)}
                disabled={!deviceId}
                sx={{
                  height: 52,
                  bgcolor: 'white',
                  color: '#333',
                  borderRadius: 2.5,
                  border: '1px solid #d1d1d6',
                  boxShadow: '0 2px 8px rgba(0, 0, 0, 0.08)',
                  fontSize: '0.9rem',
                  fontWeight: 600,
                  '&:hover': {
                    bgcolor: '#f9f9f9',
                    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.12)',
                  },
                  '&:active': {
                    transform: 'scale(0.95)',
                  },
                  '&:disabled': {
                    bgcolor: '#e0e0e0',
                    color: '#9e9e9e',
                    border: 'none',
                    boxShadow: 'none',
                  },
                  transition: 'all 0.2s ease',
                }}
              >
                {app.label}
              </IconButton>
            )
          })}
        </Box>
        )}
      </Paper>

      <Snackbar open={snackbar.open} autoHideDuration={2000} onClose={handleCloseSnackbar} anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}>
        <Alert onClose={handleCloseSnackbar} severity={snackbar.severity} sx={{ width: '100%' }}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </>
  )
}
