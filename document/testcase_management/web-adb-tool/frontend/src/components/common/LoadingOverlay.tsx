/**
 * 加载遮罩组件
 * 
 * 显示加载指示器和可选的消息
 */

import { Box, CircularProgress, Typography, Backdrop } from '@mui/material'

interface LoadingOverlayProps {
  open: boolean
  message?: string
}

export function LoadingOverlay({ open, message }: LoadingOverlayProps) {
  return (
    <Backdrop
      sx={{ color: '#fff', zIndex: (theme) => theme.zIndex.drawer + 1 }}
      open={open}
    >
      <Box sx={{ textAlign: 'center' }}>
        <CircularProgress color="inherit" />
        {message && (
          <Typography variant="body1" sx={{ mt: 2 }}>
            {message}
          </Typography>
        )}
      </Box>
    </Backdrop>
  )
}
