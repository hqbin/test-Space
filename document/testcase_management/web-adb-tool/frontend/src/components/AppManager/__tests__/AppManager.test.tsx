/**
 * AppManager 组件测试
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { AppManager } from '../index'

// Mock store
vi.mock('@store/deviceStore', () => ({
  useDeviceStore: () => ({
    selectedDevice: null,
  }),
}))

describe('AppManager', () => {
  it('renders without crashing', () => {
    render(<AppManager />)
    expect(screen.getByText('安装应用')).toBeInTheDocument()
    expect(screen.getByText('已安装应用')).toBeInTheDocument()
  })

  it('shows device selection prompt when no device selected', () => {
    render(<AppManager />)
    expect(screen.getByText('请先选择一个设备')).toBeInTheDocument()
  })

  it('renders upload area', () => {
    render(<AppManager />)
    expect(screen.getByText(/拖放 APK 文件到此处/)).toBeInTheDocument()
  })
})
