/**
 * WebSocket 客户端
 * 
 * 封装 Socket.IO 客户端，处理实时通信
 */

import { io, Socket } from 'socket.io-client'
import type {
  WebSocketMessage,
  LogcatMessage,
  ScreenFrameMessage,
  DeviceStatusMessage,
  ErrorMessage,
} from '../types/api'

type MessageHandler = (message: WebSocketMessage) => void
type LogcatHandler = (message: LogcatMessage) => void
type ScreenFrameHandler = (message: ScreenFrameMessage) => void
type DeviceStatusHandler = (message: DeviceStatusMessage) => void
type ErrorHandler = (message: ErrorMessage) => void

class WebSocketClient {
  private socket: Socket | null = null
  private url: string
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000
  private messageHandlers: Map<string, MessageHandler[]> = new Map()

  constructor(url: string = import.meta.env.VITE_WS_URL || 'http://localhost:2333') {
    this.url = url
  }

  /**
   * 连接到 WebSocket 服务器
   */
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.socket?.connected) {
        resolve()
        return
      }

      this.socket = io(this.url, {
        transports: ['websocket', 'polling'],
        reconnection: true,
        reconnectionAttempts: this.maxReconnectAttempts,
        reconnectionDelay: this.reconnectDelay,
      })

      // 连接成功
      this.socket.on('connect', () => {
        this.reconnectAttempts = 0
        resolve()
      })

      // 连接错误
      this.socket.on('connect_error', (error) => {
        console.error('WebSocket connection error:', error)
        this.reconnectAttempts++
        
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
          reject(new Error('Failed to connect after maximum attempts'))
        }
      })

      // 断开连接
      this.socket.on('disconnect', (reason) => {
        if (reason === 'io server disconnect') {
          // 服务器主动断开，需要手动重连
          this.socket?.connect()
        }
      })

      // 重连尝试
      this.socket.on('reconnect_attempt', () => {
        // 静默重连
      })

      // 重连成功
      this.socket.on('reconnect', () => {
        this.reconnectAttempts = 0
      })

      // 重连失败
      this.socket.on('reconnect_failed', () => {
        console.error('WebSocket reconnection failed')
      })

      // 监听消息
      this.setupMessageListeners()
    })
  }

  /**
   * 断开连接
   */
  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect()
      this.socket = null
    }
    this.messageHandlers.clear()
  }

  /**
   * 检查连接状态
   */
  isConnected(): boolean {
    return this.socket?.connected || false
  }

  /**
   * 设置消息监听器
   */
  private setupMessageListeners(): void {
    if (!this.socket) return

    // Logcat 消息
    this.socket.on('logcat', (data: any) => {
      const message: LogcatMessage = {
        type: 'logcat',
        device_id: data.device_id,
        priority: data.priority,
        tag: data.tag,
        pid: data.pid,
        message: data.message,
        timestamp: data.timestamp || new Date().toISOString(),
      }
      
      this.notifyHandlers('logcat', message)
    })

    // 屏幕帧消息
    this.socket.on('screen_frame', (data: any) => {
      const message: ScreenFrameMessage = {
        type: 'screen_frame',
        device_id: data.device_id || data.deviceId,
        frame_data: data.frame_data || data.image,
        timestamp: data.timestamp || new Date().toISOString(),
      }
      
      this.notifyHandlers('screen_frame', message)
    })

    // 设备状态消息
    this.socket.on('device_status', (data: any) => {
      const message: DeviceStatusMessage = {
        type: 'device_status',
        device_id: data.deviceId,
        status: data.status,
        timestamp: data.timestamp || new Date().toISOString(),
      }
      this.notifyHandlers('device_status', message)
    })

    // 错误消息
    this.socket.on('error', (data: any) => {
      const message: ErrorMessage = {
        type: 'error',
        code: data.code,
        message: data.message,
        timestamp: new Date().toISOString(),
      }
      this.notifyHandlers('error', message)
    })

    // 订阅确认
    this.socket.on('subscribed', () => {
      // 静默处理
    })

    // 取消订阅确认
    this.socket.on('unsubscribed', () => {
      // 静默处理
    })
  }

  /**
   * 通知所有注册的处理器
   */
  private notifyHandlers(type: string, message: WebSocketMessage): void {
    const handlers = this.messageHandlers.get(type)
    if (handlers) {
      handlers.forEach((handler) => handler(message))
    }
  }

  /**
   * 订阅消息类型
   */
  on(type: 'logcat', handler: LogcatHandler): void
  on(type: 'screen_frame', handler: ScreenFrameHandler): void
  on(type: 'device_status', handler: DeviceStatusHandler): void
  on(type: 'error', handler: ErrorHandler): void
  on(type: string, handler: MessageHandler | LogcatHandler | ScreenFrameHandler | DeviceStatusHandler | ErrorHandler): void {
    if (!this.messageHandlers.has(type)) {
      this.messageHandlers.set(type, [])
    }
    this.messageHandlers.get(type)!.push(handler as MessageHandler)
  }

  /**
   * 取消订阅消息类型
   */
  off(type: string, handler: MessageHandler): void {
    const handlers = this.messageHandlers.get(type)
    if (handlers) {
      const index = handlers.indexOf(handler)
      if (index > -1) {
        handlers.splice(index, 1)
      }
    }
  }

  /**
   * 订阅 logcat 流
   */
  subscribeLogcat(deviceId: string): void {
    if (!this.socket) {
      throw new Error('WebSocket not connected')
    }
    this.socket.emit('subscribe', {
      stream: 'logcat',
      deviceId: deviceId,
    })
  }

  /**
   * 取消订阅 logcat 流
   */
  unsubscribeLogcat(_deviceId: string): void {
    if (!this.socket) return
    this.socket.emit('unsubscribe', {
      stream: 'logcat',
    })
  }

  /**
   * 订阅屏幕镜像流
   */
  subscribeScreenMirror(deviceId: string): void {
    if (!this.socket) {
      throw new Error('WebSocket not connected')
    }
    this.socket.emit('subscribe', {
      stream: 'screen_mirror',
      deviceId: deviceId,
    })
  }

  /**
   * 取消订阅屏幕镜像流
   */
  unsubscribeScreenMirror(_deviceId: string): void {
    if (!this.socket) return
    this.socket.emit('unsubscribe', {
      stream: 'screen_mirror',
    })
  }

  /**
   * 发送自定义消息
   */
  emit(event: string, data: any): void {
    if (!this.socket) {
      throw new Error('WebSocket not connected')
    }
    this.socket.emit(event, data)
  }
}

// 导出单例实例
export const wsClient = new WebSocketClient()
export default wsClient
