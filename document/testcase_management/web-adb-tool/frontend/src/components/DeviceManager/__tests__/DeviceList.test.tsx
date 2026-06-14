/**
 * DeviceList 组件测试
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { DeviceList } from '../DeviceList'
import type { DeviceInfo } from '@types/api'

describe('DeviceList', () => {
  const mockDevices: DeviceInfo[] = [
    {
      device_id: '192.168.1.100:5555',
      status: 'device',
      model: 'Test Device',
      android_version: '10',
    },
  ]

  it('should render device list', () => {
    render(
      <DeviceList
        devices={mockDevices}
        selectedDevice={null}
        onSelectDevice={vi.fn()}
        onDisconnectDevice={vi.fn()}
      />
    )

    expect(screen.getByText('192.168.1.100:5555')).toBeInTheDocument()
    expect(screen.getByText('Test Device')).toBeInTheDocument()
  })

  it('should show empty state when no devices', () => {
    render(
      <DeviceList
        devices={[]}
        selectedDevice={null}
        onSelectDevice={vi.fn()}
        onDisconnectDevice={vi.fn()}
      />
    )

    expect(screen.getByText('暂无已连接的设备')).toBeInTheDocument()
  })
})
