import { ref, computed } from "vue"
import { invoke } from "@tauri-apps/api/core"
import { listen } from "@tauri-apps/api/event"
import type { ApiCapturedRequest, ApiRewriteRule, ApiProxyStatus } from "@/types"

export function useApiProxy() {
  const status = ref<ApiProxyStatus>({
    running: false,
    port: null,
    breakpoint_enabled: false,
    captured_count: 0,
  })
  const capturedRequests = ref<ApiCapturedRequest[]>([])
  const selectedRequest = ref<ApiCapturedRequest | null>(null)
  const rewriteRules = ref<ApiRewriteRule[]>([])
  const isStarting = ref(false)
  const isStopping = ref(false)
  const isReplaying = ref(false)

  let unlistens: (() => void)[] = []

  async function init() {
    try {
      const s = await invoke<ApiProxyStatus>("proxy_get_status")
      status.value = s
    } catch { /* ok */ }

    unlistens.push(await listen<ApiCapturedRequest>("proxy:request", (e) => {
      capturedRequests.value.unshift(e.payload)
    }))

    unlistens.push(await listen<ApiCapturedRequest>("proxy:response", (e) => {
      const idx = capturedRequests.value.findIndex(r => r.id === e.payload.id)
      if (idx !== -1) {
        capturedRequests.value[idx] = e.payload
      }
    }))

    unlistens.push(await listen<ApiCapturedRequest>("proxy:breakpoint:request", (e) => {
      selectedRequest.value = e.payload
    }))

    unlistens.push(await listen<ApiCapturedRequest>("proxy:breakpoint:response", (e) => {
      selectedRequest.value = e.payload
    }))

    unlistens.push(await listen<string>("proxy:error", (e) => {
      console.error("Proxy error:", e.payload)
    }))
  }

  function cleanup() {
    unlistens.forEach(fn => fn())
    unlistens = []
  }

  async function startProxy(deviceSerial?: string) {
    isStarting.value = true
    try {
      const msg = await invoke<string>("proxy_start", { deviceSerial: deviceSerial || null })
      const s = await invoke<ApiProxyStatus>("proxy_get_status")
      status.value = s
      return msg
    } finally {
      isStarting.value = false
    }
  }

  async function stopProxy(deviceSerial?: string) {
    isStopping.value = true
    try {
      const msg = await invoke<string>("proxy_stop", { deviceSerial: deviceSerial || null })
      status.value = { ...status.value, running: false, port: null }
      return msg
    } finally {
      isStopping.value = false
    }
  }

  async function toggleBreakpoint(enabled: boolean, urlPattern?: string) {
    await invoke("proxy_set_breakpoint", { enabled, urlPattern: urlPattern || null })
    status.value = { ...status.value, breakpoint_enabled: enabled }
  }

  async function continueRequest(requestId: string, action: Record<string, any>) {
    await invoke("proxy_continue", { requestId, action })
  }

  async function getCaptured(clear = false): Promise<ApiCapturedRequest[]> {
    const data = await invoke<ApiCapturedRequest[]>("proxy_get_captured", { clear })
    capturedRequests.value = data
    return data
  }

  async function clearCaptured() {
    await getCaptured(true)
    selectedRequest.value = null
  }

  async function addRule(rule: ApiRewriteRule) {
    await invoke("proxy_add_rewrite_rule", { rule })
    rewriteRules.value.push(rule)
  }

  async function removeRule(ruleId: string) {
    await invoke("proxy_remove_rewrite_rule", { ruleId })
    rewriteRules.value = rewriteRules.value.filter(r => r.id !== ruleId)
  }

  async function updateRule(rule: ApiRewriteRule) {
    await invoke("proxy_update_rewrite_rule", { rule })
    const idx = rewriteRules.value.findIndex(r => r.id === rule.id)
    if (idx !== -1) rewriteRules.value[idx] = rule
  }

  async function clearRules() {
    await invoke("proxy_clear_rewrite_rules")
    rewriteRules.value = []
  }

  async function replay(captured: ApiCapturedRequest): Promise<ApiCapturedRequest> {
    isReplaying.value = true
    try {
      const result = await invoke<ApiCapturedRequest>("proxy_replay", { captured })
      return result
    } finally {
      isReplaying.value = false
    }
  }

  const running = computed(() => status.value.running)
  const breakpointEnabled = computed(() => status.value.breakpoint_enabled)
  const currentPort = computed(() => status.value.port)

  return {
    status, capturedRequests, selectedRequest, rewriteRules,
    isStarting, isStopping, isReplaying,
    running, breakpointEnabled, currentPort,
    init, cleanup,
    startProxy, stopProxy, toggleBreakpoint, continueRequest,
    getCaptured, clearCaptured,
    addRule, removeRule, updateRule, clearRules,
    replay,
  }
}
