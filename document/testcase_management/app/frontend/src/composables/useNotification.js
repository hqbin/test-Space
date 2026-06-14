/**
 * 通知状态管理 composable
 * 管理未读数、WebSocket集成、实时更新
 */
import { ref } from 'vue'
import { getUnreadCount } from '../api/notification'
import { useWebSocket } from './useWebSocket'
import { ElNotification } from 'element-plus'

const unreadCount = ref(0)
const latestNotification = ref(null)

// 通知类型标签映射
const typeLabels = {
  testcase: '测试用例',
  testplan: '测试计划',
  execution: '测试执行',
  report: '测试报告',
  system: '系统'
}

export function useNotification() {
  const { connected, connect, disconnect } = useWebSocket()

  async function fetchUnreadCount() {
    try {
      const res = await getUnreadCount()
      if (res.data && typeof res.data.count === 'number') {
        unreadCount.value = res.data.count
      }
    } catch (e) {
      // silent
    }
  }

  function handleWsMessage(msg) {
    if (msg.type === 'notification' && msg.data) {
      // 收到新通知，更新未读数
      unreadCount.value++
      latestNotification.value = msg.data

      // 桌面通知提示
      const typeLabel = typeLabels[msg.data.notification_type] || ''
      ElNotification({
        title: msg.data.title || '新通知',
        message: typeLabel ? `[${typeLabel}] ${msg.data.content?.substring(0, 80) || ''}` : (msg.data.content?.substring(0, 80) || ''),
        type: 'info',
        duration: 5000,
        position: 'top-right'
      })
    } else if (msg.type === 'unread_count' && typeof msg.count === 'number') {
      unreadCount.value = msg.count
    }
  }

  function startRealtime() {
    const token = localStorage.getItem('token')
    if (!token) return

    connect(token, handleWsMessage, fetchUnreadCount)
    // 初始加载未读数
    fetchUnreadCount()
  }

  function stopRealtime() {
    disconnect()
  }

  function decrementUnread(count = 1) {
    unreadCount.value = Math.max(0, unreadCount.value - count)
  }

  function resetUnread() {
    unreadCount.value = 0
  }

  return {
    unreadCount,
    latestNotification,
    connected,
    fetchUnreadCount,
    startRealtime,
    stopRealtime,
    decrementUnread,
    resetUnread
  }
}
