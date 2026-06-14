/**
 * 共享按钮样式
 * 
 * iOS 风格的按钮样式定义，用于整个应用
 */

import { SxProps, Theme } from '@mui/material'

/**
 * iOS 风格的白色按钮样式
 */
export const iosWhiteButtonStyle: SxProps<Theme> = {
  bgcolor: 'white',
  color: '#333',
  borderRadius: 3,
  border: '1px solid #d1d1d6',
  boxShadow: '0 2px 8px rgba(0, 0, 0, 0.08)',
  textTransform: 'none',
  fontSize: '15px',
  fontWeight: 500,
  padding: '10px 20px',
  transition: 'all 0.2s ease',
  '&:hover': {
    bgcolor: '#f9f9f9',
    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.12)',
    transform: 'translateY(-1px)',
  },
  '&:active': {
    transform: 'translateY(0)',
    boxShadow: '0 2px 6px rgba(0, 0, 0, 0.1)',
  },
  '&:disabled': {
    bgcolor: '#f5f5f5',
    color: '#999',
    border: '1px solid #e5e5e5',
  },
}

/**
 * iOS 风格的红色按钮样式（用于电源键等）
 */
export const iosRedButtonStyle: SxProps<Theme> = {
  bgcolor: '#ff3b30',
  color: 'white',
  borderRadius: 3,
  border: 'none',
  boxShadow: '0 2px 8px rgba(255, 59, 48, 0.3)',
  textTransform: 'none',
  fontSize: '15px',
  fontWeight: 500,
  padding: '10px 20px',
  transition: 'all 0.2s ease',
  '&:hover': {
    bgcolor: '#ff2d21',
    boxShadow: '0 4px 12px rgba(255, 59, 48, 0.4)',
    transform: 'translateY(-1px)',
  },
  '&:active': {
    transform: 'translateY(0)',
    boxShadow: '0 2px 6px rgba(255, 59, 48, 0.3)',
  },
  '&:disabled': {
    bgcolor: '#ffb3b0',
    color: 'white',
  },
}

/**
 * iOS 风格的蓝色按钮样式（用于确认键等）
 */
export const iosBlueButtonStyle: SxProps<Theme> = {
  bgcolor: '#007aff',
  color: 'white',
  borderRadius: 3,
  border: 'none',
  boxShadow: '0 2px 8px rgba(0, 122, 255, 0.3)',
  textTransform: 'none',
  fontSize: '15px',
  fontWeight: 500,
  padding: '10px 20px',
  transition: 'all 0.2s ease',
  '&:hover': {
    bgcolor: '#0051d5',
    boxShadow: '0 4px 12px rgba(0, 122, 255, 0.4)',
    transform: 'translateY(-1px)',
  },
  '&:active': {
    transform: 'translateY(0)',
    boxShadow: '0 2px 6px rgba(0, 122, 255, 0.3)',
  },
  '&:disabled': {
    bgcolor: '#80bdff',
    color: 'white',
  },
}

/**
 * iOS 风格的圆形按钮样式（用于方向键等）
 */
export const iosCircleButtonStyle: SxProps<Theme> = {
  bgcolor: 'white',
  color: '#333',
  borderRadius: '50%',
  border: '1px solid #d1d1d6',
  boxShadow: '0 2px 8px rgba(0, 0, 0, 0.08)',
  width: 56,
  height: 56,
  minWidth: 56,
  transition: 'all 0.2s ease',
  '&:hover': {
    bgcolor: '#f9f9f9',
    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.12)',
    transform: 'translateY(-1px)',
  },
  '&:active': {
    transform: 'translateY(0)',
    boxShadow: '0 2px 6px rgba(0, 0, 0, 0.1)',
  },
  '&:disabled': {
    bgcolor: '#f5f5f5',
    color: '#999',
    border: '1px solid #e5e5e5',
  },
}

/**
 * iOS 风格的小型按钮样式
 */
export const iosSmallButtonStyle: SxProps<Theme> = {
  ...iosWhiteButtonStyle,
  fontSize: '13px',
  padding: '6px 12px',
  minWidth: 'auto',
}

/**
 * iOS 风格的主要操作按钮样式
 */
export const iosPrimaryButtonStyle: SxProps<Theme> = {
  ...iosBlueButtonStyle,
  fontSize: '16px',
  fontWeight: 600,
  padding: '12px 24px',
}

/**
 * iOS 风格的次要操作按钮样式
 */
export const iosSecondaryButtonStyle: SxProps<Theme> = {
  ...iosWhiteButtonStyle,
  color: '#007aff',
  '&:hover': {
    bgcolor: '#f0f7ff',
    boxShadow: '0 4px 12px rgba(0, 122, 255, 0.15)',
    transform: 'translateY(-1px)',
  },
}

/**
 * iOS 风格的危险操作按钮样式
 */
export const iosDangerButtonStyle: SxProps<Theme> = {
  ...iosRedButtonStyle,
}

/**
 * iOS 风格的图标按钮样式
 */
export const iosIconButtonStyle: SxProps<Theme> = {
  bgcolor: 'white',
  color: '#333',
  borderRadius: 2,
  border: '1px solid #d1d1d6',
  boxShadow: '0 2px 8px rgba(0, 0, 0, 0.08)',
  transition: 'all 0.2s ease',
  '&:hover': {
    bgcolor: '#f9f9f9',
    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.12)',
  },
  '&:active': {
    boxShadow: '0 2px 6px rgba(0, 0, 0, 0.1)',
  },
}

/**
 * iOS 风格的卡片样式
 */
export const iosCardStyle: SxProps<Theme> = {
  bgcolor: 'white',
  borderRadius: 3,
  border: '1px solid #d1d1d6',
  boxShadow: '0 2px 8px rgba(0, 0, 0, 0.08)',
  overflow: 'hidden',
}

/**
 * iOS 风格的输入框样式
 */
export const iosInputStyle: SxProps<Theme> = {
  '& .MuiOutlinedInput-root': {
    bgcolor: 'white',
    borderRadius: 2,
    '& fieldset': {
      borderColor: '#d1d1d6',
    },
    '&:hover fieldset': {
      borderColor: '#a1a1a6',
    },
    '&.Mui-focused fieldset': {
      borderColor: '#007aff',
      borderWidth: 2,
    },
  },
}
