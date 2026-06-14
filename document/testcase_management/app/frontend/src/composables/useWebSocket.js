/**
 * WebSocket连接管理 composable
 * 支持自动重连、心跳检测、降级轮询
 */
import { ref, onUnmounted } from 'vue'

const MAX_RETRIES = 5
const HEARTBEAT_INTERVAL = 30000 // 30秒
const RECONNECT_BASE_DELAY = 2000
const FALLBACK_POLL_INTERVAL = 60000 // 60秒降级轮询

export function useWebSocket() {
  const connected = ref(false)
  const retryCount = ref(0)

  let ws = null
  let heartbeatTimer = null
  let reconnectTimer = null
  let fallbackTimer = null
  let messageHandler = null
  let fallbackFn = null

  function _getWsUrl(token) {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    return `${protocol}//${host}/ws/notifications?token=${encodeURIComponent(token)}`
  }

  function _startHeartbeat() {
    _stopHeartbeat()
    heartbeatTimer = setInterval(() => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'ping' }))
      }
    }, HEARTBEAT_INTERVAL)
  }

  function _stopHeartbeat() {
    if (heartbeatTimer) {
      clearInterval(heartbeatTimer)
      heartbeatTimer = null
    }
  }

  function _startFallbackPolling() {
    _stopFallbackPolling()
    if (fallbackFn) {
      fallbackTimer = setInterval(fallbackFn, FALLBACK_POLL_INTERVAL)
    }
  }

  function _stopFallbackPolling() {
    if (fallbackTimer) {
      clearInterval(fallbackTimer)
      fallbackTimer = null
    }
  }

  function connect(token, onMessage, onFallback) {
    messageHandler = onMessage
    fallbackFn = onFallback

    if (ws) {
      ws.close()
      ws = null
    }

    const url = _getWsUrl(token)
    ws = new WebSocket(url)

    ws.onopen = () => {
      connected.value = true
      retryCount.value = 0
      _startHeartbeat()
      _stopFallbackPolling()
    }

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        if (msg.type === 'pong' || msg.type === 'ping') return
        if (messageHandler) messageHandler(msg)
      } catch (e) {
        // ignore parse errors
      }
    }

    ws.onclose = (event) => {
      connected.value = false
      _stopHeartbeat()

      // 4003 = unauthorized, don't retry
      if (event.code === 4003) return

      if (retryCount.value < MAX_RETRIES) {
        const delay = RECONNECT_BASE_DELAY * Math.pow(2, retryCount.value)
        retryCount.value++
        reconnectTimer = setTimeout(() => connect(token, onMessage, onFallback), delay)
      } else {
        // 降级到轮询
        _startFallbackPolling()
      }
    }

    ws.onerror = () => {
      // onclose will handle reconnection
    }
  }

  function disconnect() {
    _stopHeartbeat()
    _stopFallbackPolling()
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
    if (ws) {
      ws.close()
      ws = null
    }
    connected.value = false
    retryCount.value = 0
  }

  onUnmounted(() => {
    disconnect()
  })

  return {
    connected,
    retryCount,
    connect,
    disconnect
  }
}
