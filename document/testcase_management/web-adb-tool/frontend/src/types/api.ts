/**
 * API 类型定义
 * 
 * 定义与后端 API 交互的所有数据类型
 */

// ==================== 通用类型 ====================

export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  error?: string
  message?: string
}

// ==================== 设备相关类型 ====================

export interface DeviceInfo {
  device_id: string
  status: 'device' | 'offline' | 'unauthorized'
  model?: string
  android_version?: string
  sdk_version?: string
  resolution?: string
  density?: string
  build_fingerprint?: string
}

export interface ConnectDeviceRequest {
  ip: string
  port?: number
}

export interface ConnectDeviceResponse {
  success: boolean
  message: string
  device_id?: string
}

// ==================== 应用管理类型 ====================

export interface InstallAppRequest {
  file: File
  reinstall?: boolean
  grant_permissions?: boolean
}

export interface AppVersionInfo {
  version_name: string
  version_code: string
  package_name: string
}

// ==================== 屏幕操作类型 ====================

export interface StartRecordingRequest {
  time_limit?: number
  bit_rate?: number
}

export interface RecordingSession {
  session_id: string
  device_id: string
  start_time: string
}

// ==================== 日志采集类型 ====================

export interface LogFilter {
  tag?: string
  priority?: 'V' | 'D' | 'I' | 'W' | 'E' | 'F'
  pid?: number
  message_pattern?: string
}

export interface StartLogcatRequest {
  tag?: string
  priority?: string
  pid?: number
  message_pattern?: string
}

export interface LogcatSession {
  session_id: string
  device_id: string
  start_time: string
  filters?: LogFilter
}

// ==================== 配置管理类型 ====================

export interface CustomButton {
  id: string
  name: string
  command: string
  description?: string
}

export interface IpHistoryEntry {
  ip: string
  port: number
  last_used: string
  use_count: number
}

// ==================== AI 助手类型 ====================

export interface GenerateCommandRequest {
  prompt: string
  device_id?: string
}

export interface AnalyzeErrorRequest {
  error_message: string
  device_id?: string
}

export interface AIResponse {
  response: string
  command?: string
}

export interface Message {
  role: 'user' | 'assistant' | 'system'
  content: string
  command?: string
  timestamp: string
}

export interface ConfigureAIRequest {
  api_key: string
  endpoint: string
  deployment: string
}

// ==================== WebSocket 消息类型 ====================

export interface WebSocketMessage {
  type: 'logcat' | 'screen_frame' | 'device_status' | 'error'
  timestamp: string
}

export interface LogcatMessage extends WebSocketMessage {
  type: 'logcat'
  device_id: string
  priority: string
  tag: string
  pid?: number
  message: string
}

export interface ScreenFrameMessage extends WebSocketMessage {
  type: 'screen_frame'
  device_id: string
  frame_data: string // base64 encoded image
}

export interface DeviceStatusMessage extends WebSocketMessage {
  type: 'device_status'
  device_id: string
  status: 'connected' | 'disconnected' | 'offline'
}

export interface ErrorMessage extends WebSocketMessage {
  type: 'error'
  code: string
  message: string
}
