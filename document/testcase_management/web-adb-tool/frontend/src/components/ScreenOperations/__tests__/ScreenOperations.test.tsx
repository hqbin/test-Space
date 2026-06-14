/**
 * ScreenOperations 组件测试
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ScreenOperations } from '../index'

// Mock store
vi.mock('@store/deviceStore', () => ({
  useDeviceStore: () => ({
    selectedDevice: null,
  }),
}))

// Mock WebSocket
vi.mock('@services/websocket', () => ({
  websocketClient: {
    subscribeScreenMirror: vi.fn(),
    unsubscribeScreenMirror: vi.fn(),
    on: vi.fn(),
    off: vi.fn(),
  },
}))

describe('ScreenOperations', () => {
  it('renders without crashing', () => {
    render(<ScreenOperations />)
    expect(screen.getByText('屏幕镜像')).toBeInTheDocument()
    expect(screen.getByText('屏幕录制')).toBeInTheDocument()
    expect(screen.getByText('截图')).toBeInTheDocument()
  })

  it('shows device selection prompt when no device selected', () => {
    render(<ScreenOperations />)
    expect(screen.getByText('请先选择一个设备')).toBeInTheDocument()
  })
})
