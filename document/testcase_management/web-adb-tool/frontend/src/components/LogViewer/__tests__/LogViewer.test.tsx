/**
 * LogViewer 组件测试
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { LogViewer } from '../index'

// Mock store
vi.mock('@store/deviceStore', () => ({
  useDeviceStore: () => ({
    selectedDevice: null,
  }),
}))

// Mock WebSocket
vi.mock('@services/websocket', () => ({
  websocketClient: {
    subscribeLogcat: vi.fn(),
    unsubscribeLogcat: vi.fn(),
    on: vi.fn(),
    off: vi.fn(),
  },
}))

describe('LogViewer', () => {
  it('renders without crashing', () => {
    render(<LogViewer />)
    expect(screen.getByText('日志查看器')).toBeInTheDocument()
    expect(screen.getByText('日志控制')).toBeInTheDocument()
  })

  it('shows device selection prompt when no device selected', () => {
    render(<LogViewer />)
    expect(screen.getByText('请先选择一个设备')).toBeInTheDocument()
  })

  it('renders filter panel', () => {
    render(<LogViewer />)
    expect(screen.getByText('日志过滤器')).toBeInTheDocument()
  })
})
