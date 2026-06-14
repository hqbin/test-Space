/**
 * 屏幕录制会话状态管理
 * 
 * 用于在页面切换时保持屏幕录制会话的状态
 */

import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface RecordingSession {
  sessionId: string
  deviceId: string
  startTime: number
}

interface RecordingSessionState {
  // 录制会话
  recordingSession: RecordingSession | null
  setRecordingSession: (session: RecordingSession | null) => void
  
  // 清除会话
  clearRecordingSession: () => void
}

export const useRecordingSessionStore = create<RecordingSessionState>()(
  persist(
    (set) => ({
      recordingSession: null,
      setRecordingSession: (session) => set({ recordingSession: session }),
      
      clearRecordingSession: () => set({ recordingSession: null }),
    }),
    {
      name: 'recording-session-storage',
    }
  )
)
