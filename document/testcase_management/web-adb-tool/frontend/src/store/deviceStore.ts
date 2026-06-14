/**
 * 设备状态管理
 * 
 * 使用 Zustand 管理设备列表和当前选中的设备
 */

import { create } from 'zustand'
import type { DeviceInfo } from '../types/api'
import { getDevices, connectDevice as connectDeviceAPI, disconnectDevice as disconnectDeviceAPI, getDeviceInfo } from '../services/localAgent'

interface DeviceState {
  devices: DeviceInfo[]
  selectedDevice: DeviceInfo | null
  fetchingDevices: boolean  // 刷新设备列表的 loading 状态（不影响用户操作）
  connecting: boolean        // 连接/断开设备的 loading 状态（会禁用输入框）
  error: string | null
  
  // Bugreport generation state
  bugreportSession: {
    sessionId: string
    deviceId: string
    startedAt: string
    progress: string
  } | null
  
  // Actions
  fetchDevices: () => Promise<void>
  selectDevice: (device: DeviceInfo | null) => Promise<void>
  connectDevice: (ip: string, port?: number) => Promise<boolean>
  disconnectDevice: (deviceId: string) => Promise<void>
  refreshDeviceInfo: (deviceId: string) => Promise<void>
  clearError: () => void
  setBugreportSession: (session: { sessionId: string; deviceId: string; startedAt: string; progress: string } | null) => void
  updateBugreportProgress: (progress: string) => void
}

export const useDeviceStore = create<DeviceState>((set, get) => ({
  devices: [],
  selectedDevice: null,
  fetchingDevices: false,
  connecting: false,
  error: null,
  bugreportSession: null,

  fetchDevices: async () => {
    set({ fetchingDevices: true, error: null })
    try {
      const response = await getDevices()
      if (response.success) {
        // 解析 adb devices 输出
        const lines = response.output.split('\n')
        const deviceList: DeviceInfo[] = []
        
        for (const line of lines) {
          const trimmed = line.trim()
          // 跳过空行和标题行
          if (!trimmed || trimmed.includes('List of devices')) continue
          
          // 解析设备行：device_id\tstatus
          const parts = trimmed.split(/\s+/)
          if (parts.length >= 2) {
            deviceList.push({
              device_id: parts[0],
              status: parts[1] === 'device' ? 'device' : (parts[1] === 'offline' ? 'offline' : 'unauthorized'),
            })
          }
        }
        
        const { selectedDevice } = get()
        
        // 智能设备选择逻辑
        let newSelectedDevice = selectedDevice
        let hasChanged = false
        
        if (selectedDevice) {
          // 如果已有选择的设备，检查它是否还在设备列表中
          const stillExists = deviceList.find(d => d.device_id === selectedDevice.device_id)
          if (stillExists) {
            // 设备仍然存在，保留原来的完整信息（包括型号、版本等）
            // 只在状态发生变化时才更新引用，避免不必要的重渲染
            if (selectedDevice.status !== stillExists.status) {
              newSelectedDevice = {
                ...selectedDevice,
                status: stillExists.status
              }
              hasChanged = true
            }
            // 同时更新设备列表中的这个设备，保留完整信息
            const deviceIndex = deviceList.findIndex(d => d.device_id === selectedDevice.device_id)
            if (deviceIndex !== -1) {
              deviceList[deviceIndex] = newSelectedDevice as DeviceInfo
            }
          } else {
            // 设备已断开，清除选择
            newSelectedDevice = null
            hasChanged = true
          }
        } else if (deviceList.length > 0) {
          // 首次加载或没有选择设备时，自动选择第一个设备
          newSelectedDevice = deviceList[0]
          hasChanged = true
        }
        
        // 如果设备列表内容没有变化，避免触发引用更新
        const prevDevices = get().devices
        const devicesChanged =
          prevDevices.length !== deviceList.length ||
          prevDevices.some((d, i) => {
            const newD = deviceList[i]
            return !newD || newD.device_id !== d.device_id || newD.status !== d.status
          })
        
        if (devicesChanged || hasChanged) {
          set({ 
            devices: devicesChanged ? deviceList : prevDevices, 
            selectedDevice: hasChanged ? newSelectedDevice : selectedDevice,
            fetchingDevices: false 
          })
        } else {
          set({ fetchingDevices: false })
        }
        
        // 如果自动选择了新设备，获取完整的设备信息
        if (hasChanged && newSelectedDevice && !selectedDevice) {
          // 这是首次自动选择，需要获取完整信息
          get().refreshDeviceInfo(newSelectedDevice.device_id)
        }
      } else {
        set({ error: response.error || 'Failed to fetch devices', fetchingDevices: false })
      }
    } catch (error) {
      set({ error: (error as Error).message, fetchingDevices: false })
    }
  },

  selectDevice: async (device) => {
    set({ selectedDevice: device })
    // 自动获取设备详细信息
    if (device) {
      await get().refreshDeviceInfo(device.device_id)
    }
  },

  connectDevice: async (ip, port = 5555) => {
    set({ connecting: true, error: null })
    try {
      const response = await connectDeviceAPI(ip, port)
      if (response.success) {
        const { selectedDevice } = get()
        
        // 重新获取设备列表
        await get().fetchDevices()
        
        // 只有在没有选择设备时，才自动选择新连接的设备
        if (!selectedDevice) {
          const { devices } = get()
          const newDevice = devices.find(d => d.device_id.includes(ip))
          if (newDevice) {
            set({ selectedDevice: newDevice })
          }
        }
        
        set({ connecting: false })
        return true // 返回成功标志
      } else {
        set({ error: response.error || 'Failed to connect device', connecting: false })
        return false // 返回失败标志
      }
    } catch (error) {
      set({ error: (error as Error).message, connecting: false })
      return false // 返回失败标志
    }
  },

  disconnectDevice: async (deviceId) => {
    set({ connecting: true, error: null })
    try {
      const response = await disconnectDeviceAPI(deviceId)
      if (response.success) {
        // 如果断开的是当前选中的设备，清除选中状态
        const { selectedDevice } = get()
        if (selectedDevice?.device_id === deviceId) {
          set({ selectedDevice: null })
        }
        // 重新获取设备列表
        await get().fetchDevices()
        set({ connecting: false })
      } else {
        set({ error: response.error || 'Failed to disconnect device', connecting: false })
      }
    } catch (error) {
      set({ error: (error as Error).message, connecting: false })
    }
  },

  refreshDeviceInfo: async (deviceId: string) => {
    console.log('[deviceStore] refreshDeviceInfo called for:', deviceId);
    try {
      const response = await getDeviceInfo(deviceId);
      console.log('[deviceStore] getDeviceInfo response:', response);
      
      if (response.success) {
        const deviceInfo = JSON.parse(response.output);
        console.log('[deviceStore] Parsed device info:', deviceInfo);
        
        const { devices, selectedDevice } = get();
        
        // 更新设备列表中的设备信息
        const updatedDevices = devices.map((device) =>
          device.device_id === deviceId ? deviceInfo : device
        );
        
        // 如果当前选中的设备就是要刷新的设备，也更新 selectedDevice
        const newSelectedDevice = selectedDevice?.device_id === deviceId 
          ? deviceInfo 
          : selectedDevice;
        
        console.log('[deviceStore] Updating store with:', { updatedDevices, newSelectedDevice });
        
        set({ 
          devices: updatedDevices, 
          selectedDevice: newSelectedDevice 
        });
      } else {
        console.error('[deviceStore] getDeviceInfo failed:', response.error);
      }
    } catch (error) {
      console.error('[deviceStore] Failed to refresh device info:', error);
    }
  },

  clearError: () => {
    set({ error: null })
  },

  setBugreportSession: (session) => {
    set({ bugreportSession: session })
  },

  updateBugreportProgress: (progress) => {
    const { bugreportSession } = get()
    if (bugreportSession) {
      set({ 
        bugreportSession: { 
          ...bugreportSession, 
          progress 
        } 
      })
    }
  },
}))
