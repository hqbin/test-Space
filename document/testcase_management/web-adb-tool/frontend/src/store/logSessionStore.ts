/**
 * 日志会话状态管理
 * 
 * 用于在页面切换时保持日志采集会话的状态
 */

import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface LogcatSession {
  sessionId: string
  deviceId: string
  startTime: number
}

interface BootLogcatSession {
  sessionId: string
  mode: string
  deviceId?: string
  lineCount: number
  connected: boolean
  startTime: number
}

interface DiagnosticSession {
  sessionId: string
  deviceId: string
  startTime: number
}

interface LogSessionState {
  // Logcat 会话
  logcatSession: LogcatSession | null
  setLogcatSession: (session: LogcatSession | null) => void
  
  // Boot Logcat 会话
  bootLogcatSession: BootLogcatSession | null
  setBootLogcatSession: (session: BootLogcatSession | null) => void
  
  // Diagnostic 会话
  diagnosticSession: DiagnosticSession | null
  setDiagnosticSession: (session: DiagnosticSession | null) => void
  
  // 清除所有会话
  clearAllSessions: () => void
}

export const useLogSessionStore = create<LogSessionState>()(
  persist(
    (set) => ({
      logcatSession: null,
      setLogcatSession: (session) => set({ logcatSession: session }),
      
      bootLogcatSession: null,
      setBootLogcatSession: (session) => set({ bootLogcatSession: session }),
      
      diagnosticSession: null,
      setDiagnosticSession: (session) => set({ diagnosticSession: session }),
      
      clearAllSessions: () => set({
        logcatSession: null,
        bootLogcatSession: null,
        diagnosticSession: null,
      }),
    }),
    {
      name: 'log-session-storage',
    }
  )
)
