/**
 * 全局靛蓝主题配色 - 匹配测试管理平台风格
 */

export const purpleGradient = {
  // 主色（纯色，不用渐变）
  primary: '#6366f1',
  primaryHover: '#4f46e5',
  
  // 浅色背景
  light: '#eef2ff',
  lightHover: '#e0e7ff',
  
  // 单色
  main: '#6366f1',
  dark: '#4f46e5',
  darker: '#4338ca',
  lightColor: '#818cf8',
  lighter: '#eef2ff',
  
  // 文字色
  text: '#4f46e5',
  textLight: '#6366f1',
  
  // 边框色
  border: '#a5b4fc',
  borderLight: '#c7d2fe',
}

// 按钮样式
export const purpleButtonStyles = {
  background: '#6366f1',
  '&:hover': {
    background: '#4f46e5',
    boxShadow: '0 2px 8px rgba(99, 102, 241, 0.3)',
  },
  '&:disabled': {
    background: '#e5e7eb',
    color: '#9ca3af',
  },
}

// 卡片样式
export const purpleCardStyles = {
  borderRadius: 2,
  boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
  transition: 'all 0.2s',
  '&:hover': {
    boxShadow: '0 4px 12px rgba(99, 102, 241, 0.15)',
  },
}

// Chip 样式
export const purpleChipStyles = {
  background: '#6366f1',
  color: '#fff',
  fontWeight: 500,
  '&:hover': {
    background: '#4f46e5',
  },
}

// 输入框聚焦样式
export const purpleInputStyles = {
  '& .MuiOutlinedInput-root': {
    '&:hover fieldset': {
      borderColor: '#6366f1',
    },
    '&.Mui-focused fieldset': {
      borderColor: '#6366f1',
      borderWidth: 2,
    },
  },
}
