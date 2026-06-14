/**
 * API 客户端
 * 
 * 封装所有与后端 REST API 的交互
 */

import axios, { AxiosInstance, AxiosError } from 'axios'
import type {
  ApiResponse,
  DeviceInfo,
  ConnectDeviceRequest,
  ConnectDeviceResponse,
  AppVersionInfo,
  StartRecordingRequest,
  RecordingSession,
  StartLogcatRequest,
  LogcatSession,
  CustomButton,
  IpHistoryEntry,
  GenerateCommandRequest,
  AnalyzeErrorRequest,
  AIResponse,
  Message,
  ConfigureAIRequest,
} from '../types/api'

// 本地代理客户端（用于直接调用本地 ADB 代理）
const localAgentClient = axios.create({
  baseURL: 'http://localhost:9527',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

class ApiClient {
  private client: AxiosInstance

  constructor(baseURL: string = import.meta.env.VITE_API_BASE_URL || 'http://localhost:2333') {
    this.client = axios.create({
      baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // 请求拦截器
    this.client.interceptors.request.use(
      (config) => {
        // 添加本地代理地址到请求头
        // 后端会使用这个地址来调用用户本地的 ADB 代理
        config.headers['X-Local-Agent-URL'] = 'http://localhost:9527'
        
        // 可以在这里添加认证 token
        return config
      },
      (error) => {
        return Promise.reject(error)
      }
    )

    // 响应拦截器
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        // 统一错误处理
        if (error.response) {
          console.error('API Error:', error.response.status, error.response.data)
        } else if (error.request) {
          console.error('Network Error:', error.message)
        } else {
          console.error('Error:', error.message)
        }
        return Promise.reject(error)
      }
    )
  }

  // ==================== 健康检查 ====================

  async healthCheck(): Promise<ApiResponse> {
    const response = await this.client.get('/health')
    return response.data
  }

  // ==================== 设备管理 ====================

  async listDevices(): Promise<ApiResponse<DeviceInfo[]>> {
    const response = await this.client.get('/api/devices')
    return response.data
  }

  async connectDevice(data: ConnectDeviceRequest): Promise<ApiResponse<ConnectDeviceResponse>> {
    const response = await this.client.post('/api/devices/connect', data)
    return response.data
  }

  async disconnectDevice(deviceId: string): Promise<ApiResponse> {
    const response = await this.client.delete(`/api/devices/${deviceId}`)
    return response.data
  }

  async getDeviceInfo(deviceId: string): Promise<ApiResponse<DeviceInfo>> {
    const response = await this.client.get(`/api/devices/${deviceId}/info`)
    return response.data
  }

  async inputText(deviceId: string, text: string): Promise<ApiResponse> {
    const response = await this.client.post(`/api/devices/${deviceId}/input-text`, { text })
    return response.data
  }

  async restartAdb(): Promise<ApiResponse> {
    const response = await this.client.post('/api/adb/restart')
    return response.data
  }

  async rebootDevice(deviceId: string): Promise<ApiResponse> {
    const response = await this.client.post(`/api/devices/${deviceId}/reboot`)
    return response.data
  }

  async rootAndRemount(deviceId: string): Promise<ApiResponse> {
    const response = await this.client.post(`/api/devices/${deviceId}/root-remount`)
    return response.data
  }

  async rootDevice(deviceId: string): Promise<ApiResponse> {
    const response = await this.client.post(`/api/devices/${deviceId}/root`)
    return response.data
  }

  async remountDevice(deviceId: string): Promise<ApiResponse> {
    const response = await this.client.post(`/api/devices/${deviceId}/remount`)
    return response.data
  }

  async getDeviceBasicInfo(deviceId: string): Promise<ApiResponse<any>> {
    const response = await this.client.get(`/api/devices/${deviceId}/basic-info`)
    return response.data
  }

  async getDeviceFirmwareInfo(deviceId: string, osaKeys?: string[]): Promise<ApiResponse<any>> {
    const params = osaKeys ? { osa_keys: osaKeys.join(',') } : {}
    const response = await this.client.get(`/api/devices/${deviceId}/firmware-info`, { params })
    return response.data
  }

  async getAospFirmwareInfo(deviceId: string): Promise<ApiResponse<any>> {
    const response = await this.client.get(`/api/devices/${deviceId}/aosp-firmware-info`)
    return response.data
  }

  async checkDeviceKeys(deviceId: string): Promise<ApiResponse<any>> {
    const response = await this.client.get(`/api/devices/${deviceId}/check-keys`)
    return response.data
  }

  async sendKeyevent(deviceId: string, keycode: number): Promise<ApiResponse> {
    const response = await this.client.post(`/api/devices/${deviceId}/keyevent`, {
      keycode,
    })
    return response.data
  }

  async modifyDeviceConfig(
    deviceId: string,
    configPath: string,
    configKey: string,
    configValue: string
  ): Promise<ApiResponse<any>> {
    const response = await this.client.post(`/api/devices/${deviceId}/modify-config`, {
      config_path: configPath,
      config_key: configKey,
      config_value: configValue,
    })
    return response.data
  }

  // ==================== 应用管理 ====================

  async listApps(deviceId: string, includeSystem: boolean = false): Promise<ApiResponse<string[]>> {
    const response = await this.client.get(`/api/devices/${deviceId}/apps`, {
      params: { include_system: includeSystem },
    })
    return response.data
  }

  async installApp(deviceId: string, file: File, options?: { reinstall?: boolean; grant_permissions?: boolean }): Promise<ApiResponse> {
    const formData = new FormData()
    formData.append('file', file)
    if (options?.reinstall) formData.append('reinstall', 'true')
    if (options?.grant_permissions) formData.append('grant_permissions', 'true')

    const response = await this.client.post(`/api/devices/${deviceId}/apps/install`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  }

  async uninstallApp(deviceId: string, packageName: string, keepData: boolean = false): Promise<ApiResponse> {
    const response = await this.client.delete(`/api/devices/${deviceId}/apps/${packageName}`, {
      params: { keep_data: keepData },
    })
    return response.data
  }

  async startApp(deviceId: string, packageName: string): Promise<ApiResponse> {
    const response = await this.client.post(`/api/devices/${deviceId}/apps/${packageName}/start`)
    return response.data
  }

  async stopApp(deviceId: string, packageName: string): Promise<ApiResponse> {
    const response = await this.client.post(`/api/devices/${deviceId}/apps/${packageName}/stop`)
    return response.data
  }

  async clearAppData(deviceId: string, packageName: string): Promise<ApiResponse> {
    const response = await this.client.post(`/api/devices/${deviceId}/apps/${packageName}/clear`)
    return response.data
  }

  async getAppVersion(deviceId: string, packageName: string): Promise<ApiResponse<AppVersionInfo>> {
    const response = await this.client.get(`/api/devices/${deviceId}/apps/${packageName}/version`)
    return response.data
  }

  async getCurrentApp(deviceId: string): Promise<ApiResponse<{ package_name: string; activity_name: string }>> {
    const response = await this.client.get(`/api/devices/${deviceId}/apps/current`)
    return response.data
  }

  async getAppPath(deviceId: string, packageName: string): Promise<ApiResponse<{ package_name: string; path: string }>> {
    const response = await this.client.get(`/api/devices/${deviceId}/apps/${packageName}/path`)
    return response.data
  }

  async pullApk(deviceId: string, packageName: string): Promise<Blob> {
    try {
      const response = await this.client.post(`/api/devices/${deviceId}/apps/${packageName}/pull`, null, {
        responseType: 'blob',
      })
      return response.data
    } catch (error: any) {
      // When responseType is 'blob', error responses are also blobs
      // We need to convert them to JSON to get the error message
      if (error.response && error.response.data instanceof Blob) {
        const text = await error.response.data.text()
        try {
          const errorData = JSON.parse(text)
          throw new Error(errorData.message || errorData.error || 'Failed to download APK')
        } catch {
          throw new Error('Failed to download APK')
        }
      }
      throw error
    }
  }

  async pushApkToAppPath(deviceId: string, packageName: string, file: File): Promise<ApiResponse> {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await this.client.post(`/api/devices/${deviceId}/apps/${packageName}/push`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  }

  // ==================== 屏幕操作 ====================

  async captureScreenshot(deviceId: string): Promise<Blob> {
    const response = await this.client.get(`/api/devices/${deviceId}/screenshot`, {
      responseType: 'blob',
    })
    return response.data
  }

  async startRecording(deviceId: string, options?: StartRecordingRequest): Promise<ApiResponse<RecordingSession>> {
    const response = await this.client.post(`/api/devices/${deviceId}/record/start`, options)
    return response.data
  }

  async stopRecording(deviceId: string, sessionId?: string): Promise<Blob> {
    const response = await this.client.post(`/api/devices/${deviceId}/record/stop`, 
      { session_id: sessionId },
      { responseType: 'blob' }
    )
    return response.data
  }

  async downloadRecording(deviceId: string, sessionId: string): Promise<Blob> {
    const response = await this.client.get(`/api/devices/${deviceId}/record/${sessionId}`, {
      responseType: 'blob',
    })
    return response.data
  }

  // ==================== 日志采集 ====================

  async startLogcat(deviceId: string, filters?: StartLogcatRequest & { buffer_size?: number; realtime?: boolean }): Promise<ApiResponse<LogcatSession>> {
    const response = await this.client.post(`/api/devices/${deviceId}/logcat/start`, filters)
    return response.data
  }

  async stopLogcat(deviceId: string, sessionId?: string): Promise<Blob> {
    const response = await this.client.post(`/api/devices/${deviceId}/logcat/stop`, 
      { session_id: sessionId },
      { responseType: 'blob' }
    )
    return response.data
  }

  async downloadLogcat(deviceId: string, sessionId: string): Promise<Blob> {
    const response = await this.client.get(`/api/devices/${deviceId}/logcat/download`, {
      params: { session_id: sessionId },
      responseType: 'blob',
    })
    return response.data
  }

  async generateBugreport(deviceId: string): Promise<Blob> {
    const response = await this.client.post(`/api/devices/${deviceId}/bugreport`, null, {
      responseType: 'blob',
      timeout: 300000, // 5 minutes for bugreport generation
    })
    return response.data
  }

  async startBugreport(deviceId: string): Promise<ApiResponse<{ session_id: string; device_id: string }>> {
    const response = await this.client.post(`/api/devices/${deviceId}/bugreport/start`)
    return response.data
  }

  async getBugreportStatus(sessionId: string): Promise<ApiResponse<{
    session_id: string
    device_id: string
    started_at: string
    completed: boolean
    success: boolean
    error?: string
    filename?: string
    size?: number
    progress?: number
    progress_message?: string
  }>> {
    const response = await this.client.get(`/api/bugreport/${sessionId}/status`)
    return response.data
  }

  async downloadBugreport(sessionId: string): Promise<Blob> {
    const response = await this.client.get(`/api/bugreport/${sessionId}/download`, {
      responseType: 'blob',
    })
    return response.data
  }

  async clearLogcat(deviceId: string): Promise<ApiResponse> {
    const response = await this.client.post(`/api/devices/${deviceId}/logcat/clear`)
    return response.data
  }

  async getLogcatBufferSize(deviceId: string): Promise<ApiResponse<any>> {
    const response = await this.client.get(`/api/devices/${deviceId}/logcat/buffer-size`)
    return response.data
  }

  async setLogcatBufferSize(deviceId: string, sizeMb: number): Promise<ApiResponse<any>> {
    const response = await this.client.post(`/api/devices/${deviceId}/logcat/buffer-size`, { size_mb: sizeMb })
    return response.data
  }

  async startBootLogcat(deviceId?: string, filters?: any): Promise<ApiResponse<{
    session_id: string
    mode: string
    device_id?: string
    message: string
  }>> {
    const response = await localAgentClient.post('/boot-logcat/start', {
      device_id: deviceId || '',
      filters
    })
    return response.data
  }

  async stopBootLogcat(sessionId: string): Promise<Blob> {
    const response = await localAgentClient.post(`/boot-logcat/stop?session_id=${sessionId}`, null, {
      responseType: 'blob',
    })
    return response.data
  }

  async getBootLogcatStatus(sessionId: string): Promise<ApiResponse<{
    session_id: string
    device_id?: string
    mode: string
    running: boolean
    connected: boolean
    line_count: number
    start_time: string
  }>> {
    const response = await localAgentClient.get(`/boot-logcat/status?session_id=${sessionId}`)
    return response.data
  }

  // ==================== 诊断日志包 ====================

  async startDiagnosticLog(deviceId: string): Promise<ApiResponse<{
    session_id: string
    device_id: string
    session_dir: string
  }>> {
    const response = await this.client.post(`/api/devices/${deviceId}/diagnostic/start`)
    return response.data
  }

  async stopDiagnosticLog(sessionId: string): Promise<Blob> {
    const response = await this.client.post(`/api/diagnostic/${sessionId}/stop`, null, {
      responseType: 'blob',
    })
    return response.data
  }

  // ==================== 文件传输 ====================

  async pushFile(deviceId: string, file: File, remotePath: string, onProgress?: (progress: number) => void): Promise<ApiResponse> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('remote_path', remotePath)

    const response = await this.client.post(`/api/devices/${deviceId}/files/push`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(progress)
        }
      },
    })
    return response.data
  }

  async pullFile(deviceId: string, remotePath: string): Promise<Blob> {
    const response = await this.client.post(`/api/devices/${deviceId}/files/pull`, 
      { remote_path: remotePath },
      {
        responseType: 'blob',
      }
    )
    return response.data
  }

  // ==================== 配置管理 ====================

  async getCustomButtons(): Promise<ApiResponse<CustomButton[]>> {
    const response = await this.client.get('/api/config/buttons')
    return response.data
  }

  async createCustomButton(button: Omit<CustomButton, 'id'>): Promise<ApiResponse> {
    const response = await this.client.post('/api/config/buttons', button)
    return response.data
  }

  async updateCustomButton(buttonId: string, button: Omit<CustomButton, 'id'>): Promise<ApiResponse> {
    const response = await this.client.put(`/api/config/buttons/${buttonId}`, button)
    return response.data
  }

  async deleteCustomButton(buttonId: string): Promise<ApiResponse> {
    const response = await this.client.delete(`/api/config/buttons/${buttonId}`)
    return response.data
  }

  async getIpHistory(limit: number = 20): Promise<ApiResponse<IpHistoryEntry[]>> {
    const response = await this.client.get('/api/config/ip-history', {
      params: { limit },
    })
    return response.data
  }

  // ==================== 通用命令执行 ====================

  async executeCustomCommand(deviceId: string, command: string): Promise<ApiResponse> {
    const response = await this.client.post(`/api/devices/${deviceId}/execute`, {
      command,
    })
    return response.data
  }

  // ==================== AI 助手 ====================

  async generateCommand(data: GenerateCommandRequest): Promise<ApiResponse<AIResponse>> {
    const response = await this.client.post('/api/ai/generate-command', data)
    return response.data
  }

  async analyzeError(data: AnalyzeErrorRequest): Promise<ApiResponse<AIResponse>> {
    const response = await this.client.post('/api/ai/analyze-error', data)
    return response.data
  }

  async getConversationHistory(sessionId: string): Promise<ApiResponse<Message[]>> {
    const response = await this.client.get(`/api/ai/conversation/${sessionId}`)
    return response.data
  }

  async clearConversationHistory(sessionId: string): Promise<ApiResponse> {
    const response = await this.client.delete(`/api/ai/conversation/${sessionId}`)
    return response.data
  }

  async configureAI(data: ConfigureAIRequest): Promise<ApiResponse> {
    const response = await this.client.post('/api/ai/config', data)
    return response.data
  }

  // ==================== Scrcpy 管理 ====================

  async checkScrcpyStatus(): Promise<ApiResponse<{
    installed: boolean
    version?: string
    path?: string
    download_url?: string
  }>> {
    const response = await this.client.get('/api/scrcpy/status')
    return response.data
  }

  async installScrcpy(): Promise<ApiResponse> {
    const response = await this.client.post('/api/scrcpy/install')
    return response.data
  }

  async startScrcpy(deviceId: string, options?: {
    max_size?: number
    max_fps?: number
    bit_rate?: number
    stay_awake?: boolean
    turn_screen_off?: boolean
  }): Promise<ApiResponse> {
    const response = await this.client.post('/api/scrcpy/start', {
      device_id: deviceId,
      options
    })
    return response.data
  }

  async stopScrcpy(deviceId: string): Promise<ApiResponse> {
    const response = await this.client.post('/api/scrcpy/stop', {
      device_id: deviceId
    })
    return response.data
  }

  async getRunningScrcpy(): Promise<ApiResponse<string[]>> {
    const response = await this.client.get('/api/scrcpy/running')
    return response.data
  }
}

// 导出单例实例
export const apiClient = new ApiClient()

// 导出常用方法
export const {
  listDevices,
  connectDevice,
  disconnectDevice,
  getDeviceInfo,
  listApps,
  installApp,
  uninstallApp,
  startApp,
  stopApp,
  clearAppData,
  getAppVersion,
  getCurrentApp,
  getAppPath,
  pullApk,
  pushApkToAppPath,
  captureScreenshot,
  startRecording,
  stopRecording,
  downloadRecording,
  startLogcat,
  stopLogcat,
  downloadLogcat,
  generateBugreport,
  startBugreport,
  getBugreportStatus,
  downloadBugreport,
  clearLogcat,
  startBootLogcat,
  stopBootLogcat,
  getBootLogcatStatus,
  startDiagnosticLog,
  stopDiagnosticLog,
  pushFile,
  pullFile,
  getCustomButtons,
  createCustomButton,
  updateCustomButton,
  deleteCustomButton,
  getIpHistory,
  executeCustomCommand,
  generateCommand,
  analyzeError,
  getConversationHistory,
  clearConversationHistory,
  configureAI,
  checkScrcpyStatus,
  installScrcpy,
  startScrcpy,
  stopScrcpy,
  getRunningScrcpy,
} = apiClient

export default apiClient
