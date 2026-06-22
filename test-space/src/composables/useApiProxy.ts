import { ref, computed } from "vue"
import { invoke } from "@tauri-apps/api/core"
import { listen } from "@tauri-apps/api/event"
import type { ApiCapturedRequest, ApiRewriteRule, ApiProxyStatus } from "@/types"
import * as db from "@/services/database"

export interface BreakpointEvent {
  type: "request" | "response"
  data: ApiCapturedRequest
}

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
  const debugLogs = ref<string[]>([])
  const breakpointEvent = ref<BreakpointEvent | null>(null)
  const pendingBreakpoints = ref<Set<string>>(new Set())

  let unlistens: (() => void)[] = []

  async function syncRulesToDb() {
    try {
      await db.saveProxyRules(rewriteRules.value)
    } catch { /* ok */ }
  }

  async function loadRules() {
    try {
      const rules = await invoke<ApiRewriteRule[]>("proxy_get_rewrite_rules")
      rewriteRules.value = rules
      if (rules.length > 0) {
        await syncRulesToDb()
      } else {
        // Fall back to DB if Rust backend has no rules
        const dbRules = await db.loadProxyRules()
        if (dbRules.length > 0) {
          rewriteRules.value = dbRules
          // Push DB rules to Rust backend
          for (const rule of dbRules) {
            try { await invoke("proxy_add_rewrite_rule", { rule }) } catch {}
          }
        }
      }
    } catch {
      // Rust backend unavailable, load from DB
      const dbRules = await db.loadProxyRules()
      rewriteRules.value = dbRules
    }
  }

  async function init() {
    try {
      const s = await invoke<ApiProxyStatus>("proxy_get_status")
      status.value = s
    } catch { /* ok */ }
    await loadRules()

    unlistens.push(await listen<ApiCapturedRequest>("proxy:request", (e) => {
      capturedRequests.value.unshift(e.payload)
    }))

    unlistens.push(await listen<ApiCapturedRequest>("proxy:response", (e) => {
      const idx = capturedRequests.value.findIndex(r => r.id === e.payload.id)
      if (idx !== -1) {
        capturedRequests.value[idx] = e.payload
      }
      if (selectedRequest.value?.id === e.payload.id) {
        selectedRequest.value = e.payload
      }
    }))

    unlistens.push(await listen<ApiCapturedRequest>("proxy:breakpoint:request", (e) => {
      const set = new Set(pendingBreakpoints.value)
      set.add(e.payload.id)
      pendingBreakpoints.value = set
      if (selectedRequest.value?.id === e.payload.id) {
        selectedRequest.value = e.payload
      }
      breakpointEvent.value = { type: "request", data: e.payload }
    }))

    unlistens.push(await listen<ApiCapturedRequest>("proxy:breakpoint:response", (e) => {
      const set = new Set(pendingBreakpoints.value)
      const respId = `${e.payload.id}_resp`
      set.add(respId)
      pendingBreakpoints.value = set
      if (selectedRequest.value?.id === e.payload.id) {
        selectedRequest.value = e.payload
      }
      breakpointEvent.value = { type: "response", data: e.payload }
    }))

    unlistens.push(await listen<string>("proxy:error", (e) => {
      console.error("Proxy error:", e.payload)
      debugLogs.value.push(`[ERROR] ${e.payload}`)
    }))

    unlistens.push(await listen<string>("proxy:debug", (e) => {
      debugLogs.value.push(e.payload)
    }))
  }

  function markBreakpointResolved(requestId: string) {
    const set = new Set(pendingBreakpoints.value)
    set.delete(requestId)
    set.delete(`${requestId}_resp`)
    pendingBreakpoints.value = set
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
    if (!enabled) {
      pendingBreakpoints.value = new Set()
    }
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
    await syncRulesToDb()
  }

  async function removeRule(ruleId: string) {
    await invoke("proxy_remove_rewrite_rule", { ruleId })
    rewriteRules.value = rewriteRules.value.filter(r => r.id !== ruleId)
    await syncRulesToDb()
  }

  async function updateRule(rule: ApiRewriteRule) {
    await invoke("proxy_update_rewrite_rule", { rule })
    const idx = rewriteRules.value.findIndex(r => r.id === rule.id)
    if (idx !== -1) rewriteRules.value[idx] = rule
    await syncRulesToDb()
  }

  async function clearRules() {
    await invoke("proxy_clear_rewrite_rules")
    rewriteRules.value = []
    await syncRulesToDb()
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

  const pendingCount = computed(() => pendingBreakpoints.value.size)

  return {
    status, capturedRequests, selectedRequest, rewriteRules,
    isStarting, isStopping, isReplaying, debugLogs,
    running, breakpointEnabled, currentPort, breakpointEvent,
    pendingBreakpoints, pendingCount, markBreakpointResolved,
    init, cleanup,
    startProxy, stopProxy, toggleBreakpoint, continueRequest,
    getCaptured, clearCaptured,
    addRule, removeRule, updateRule, clearRules,
    replay, loadRules,
  }
}
