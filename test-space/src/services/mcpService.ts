import { getSetting, setSetting } from '@/services/database'
import type { McpServerConfig, McpTool, McpAuthType } from '@/types'
import { invoke } from '@tauri-apps/api/core'

const MCP_SERVERS_KEY = 'mcp_server_configs'

let tauriFetch: typeof fetch | null = null

async function getFetch(): Promise<typeof fetch> {
  if (tauriFetch) return tauriFetch
  try {
    const mod = await import('@tauri-apps/plugin-http')
    tauriFetch = mod.fetch
  } catch {
    tauriFetch = fetch
  }
  return tauriFetch
}

// ── Migration ──

function migrateServer(srv: any): McpServerConfig {
  if (srv.authType) return srv as McpServerConfig
  const old: any = srv
  const authHeader = (old.authHeader || 'Authorization').trim().toLowerCase()
  let authType: McpAuthType = 'bearer'
  let authValue = old.apiKey || ''
  if (!old.apiKey) {
    authType = 'none'
    authValue = ''
  } else if (authHeader === 'api-key') {
    authType = 'api-key'
    authValue = old.apiKey
  } else if (authHeader !== 'authorization' && authHeader !== '') {
    authType = 'custom'
    authValue = old.apiKey
  }
  return {
    id: old.id,
    name: old.name || '',
    endpoint: old.endpoint || '',
    authType,
    authValue: authValue || undefined,
    authHeader: authType === 'custom' ? (old.authHeader || 'Authorization') : undefined,
    enabled: old.enabled !== false,
    createdAt: old.createdAt || new Date().toISOString(),
  }
}

// ── CRUD ──

export async function loadMcpServers(): Promise<McpServerConfig[]> {
  const raw = await getSetting(MCP_SERVERS_KEY)
  if (!raw) return []
  try {
    const parsed = JSON.parse(raw)
    if (!Array.isArray(parsed)) return []
    const migrated = parsed.map(migrateServer)
    const needsMigration = parsed.some((s: any) => !s.authType)
    if (needsMigration) {
      await saveMcpServers(migrated)
    }
    return migrated
  } catch {
    return []
  }
}

export async function saveMcpServers(servers: McpServerConfig[]): Promise<void> {
  await setSetting(MCP_SERVERS_KEY, JSON.stringify(servers))
}

export async function addMcpServer(server: Omit<McpServerConfig, 'id' | 'createdAt'>): Promise<McpServerConfig> {
  const servers = await loadMcpServers()
  const newServer: McpServerConfig = {
    ...server,
    id: crypto.randomUUID(),
    createdAt: new Date().toISOString(),
  }
  servers.push(newServer)
  await saveMcpServers(servers)
  return newServer
}

export async function deleteMcpServer(id: string): Promise<void> {
  const servers = await loadMcpServers()
  await closeSse(id)
  await saveMcpServers(servers.filter(s => s.id !== id))
}

export async function updateMcpServer(id: string, updates: Partial<McpServerConfig>): Promise<void> {
  const servers = await loadMcpServers()
  const idx = servers.findIndex(s => s.id === id)
  if (idx < 0) return
  await closeSse(id)
  servers[idx] = { ...servers[idx], ...updates }
  await saveMcpServers(servers)
}

// ── SSE Transport (via Rust reqwest, bypasses CORS & HTTP plugin streaming issues) ──

const sseCache = new Map<string, { messageEndpoint: string; sessionId: string }>()

function isSseEndpoint(endpoint: string): boolean {
  const path = endpoint.replace(/https?:\/\/[^/]+/, '').split('?')[0].split('#')[0]
  return path.endsWith('/sse') || path.endsWith('/sse/')
}

function buildAuthHeaders(server: McpServerConfig): Record<string, string> {
  const headers: Record<string, string> = { 'Accept': 'text/event-stream', 'Cache-Control': 'no-cache' }
  if (server.authValue && server.authType !== 'none') {
    if (server.authType === 'bearer') headers['Authorization'] = `Bearer ${server.authValue}`
    else if (server.authType === 'api-key') headers['api-key'] = server.authValue
    else if (server.authType === 'custom') headers[server.authHeader || 'Authorization'] = server.authValue
  }
  return headers
}

async function sseJsonRpcCall(method: string, params: unknown, server: McpServerConfig): Promise<any> {
  // SSE endpoint detected — use Rust SSE transport directly
  return sseRustCall(method, params, server)
}

async function sseRustCall(method: string, params: unknown, server: McpServerConfig): Promise<any> {
  const cached = sseCache.get(server.id)
  if (!cached) {
    try {
      await initSseConnection(server)
    } catch (e: any) {
      throw new Error(`SSE init failed: ${e.message || e}`)
    }
  }
  const req: Record<string, any> = { jsonrpc: '2.0', id: Math.floor(Math.random() * 100000), method }
  if (params !== undefined && params !== null && Object.keys(params as any).length > 0) req.params = params
  const body = JSON.stringify(req)
  const result = await invoke<string>('mcp_sse_call', { serverId: server.id, body })
  const json = JSON.parse(result)
  if (json.error) throw new Error(`MCP 错误: ${json.error.message || JSON.stringify(json.error)}`)
  return json.result
}

async function initSseConnection(server: McpServerConfig): Promise<void> {
  console.log(`[MCP SSE] initSseConnection: ${server.name} (${server.endpoint})`)
  const authHeaders = buildAuthHeaders(server)
  try {
    const result = await invoke<{ session_id: string; message_endpoint: string }>('mcp_sse_init', {
      serverId: server.id,
      endpoint: server.endpoint,
      authHeaders,
    })
    sseCache.set(server.id, { messageEndpoint: result.message_endpoint, sessionId: result.session_id })
    console.log(`[MCP SSE] session_id=${result.session_id} endpoint=${result.message_endpoint}`)

    // MCP initialize handshake — required before any tool calls
    const initReq: Record<string, any> = {
      jsonrpc: '2.0',
      id: Math.floor(Math.random() * 100000),
      method: 'initialize',
      params: {
        protocolVersion: '2025-03-26',
        capabilities: {},
        clientInfo: { name: 'TestSpace', version: '1.6.9' },
      },
    }
    const initResp = await invoke<string>('mcp_sse_call', { serverId: server.id, body: JSON.stringify(initReq) })
    const initJson = JSON.parse(initResp)
    if (initJson.error) {
      console.warn(`[MCP SSE] Initialize failed: ${initJson.error.message}`)
    } else {
      console.log(`[MCP SSE] Initialize OK: server ${initJson.result?.serverInfo?.name || 'unknown'} v${initJson.result?.serverInfo?.version || '?'}`)
    }
  } catch (e: any) {
    throw new Error(`SSE init failed: ${e.message || e}`)
  }
}

async function closeSse(serverId: string): Promise<void> {
  sseCache.delete(serverId)
  try {
    await invoke('mcp_sse_close', { serverId })
  } catch {} // ignore close errors
}

// ── JSON-RPC call (auto-detects SSE vs HTTP) ──

async function jsonRpcCall(method: string, params: unknown, server: McpServerConfig): Promise<any> {
  if (isSseEndpoint(server.endpoint)) {
    return sseJsonRpcCall(method, params, server)
  }
  return httpJsonRpcCall(server.endpoint, method, params, server)
}

async function httpJsonRpcCall(endpoint: string, method: string, params?: unknown, server?: McpServerConfig): Promise<any> {
  const f = await getFetch()
  const body: Record<string, any> = { jsonrpc: '2.0', id: Math.floor(Math.random() * 100000), method }
  if (params !== undefined && params !== null && Object.keys(params as any).length > 0) body.params = params
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (server?.authValue && server.authType !== 'none') {
    if (server.authType === 'bearer') {
      headers['Authorization'] = `Bearer ${server.authValue}`
    } else if (server.authType === 'api-key') {
      headers['api-key'] = server.authValue
    } else if (server.authType === 'custom') {
      headers[server.authHeader || 'Authorization'] = server.authValue
    }
  }
  const res = await f(endpoint, {
    method: 'POST',
    headers,
    body: JSON.stringify(body),
  })
  return parseRpcResponse(res)
}

async function parseRpcResponse(res: Response): Promise<any> {
  const text = await res.text()
  let json: any
  try {
    json = JSON.parse(text)
  } catch {
    throw new Error(`MCP 返回非 JSON (HTTP ${res.status}): ${text.slice(0, 300)}`)
  }
  if (json.error) {
    throw new Error(`MCP 错误: ${json.error.message || JSON.stringify(json.error)}`)
  }
  return json.result
}

// ── Public API ──

export async function listTools(server: McpServerConfig): Promise<McpTool[]> {
  const result = await jsonRpcCall('tools/list', undefined, server)
  const tools: McpTool[] = (result?.tools || []).map((t: any) => ({
    name: t.name,
    description: t.description,
    inputSchema: t.inputSchema,
  }))
  return tools
}

export async function callTool(server: McpServerConfig, toolName: string, args: Record<string, unknown>): Promise<any> {
  const result = await jsonRpcCall('tools/call', { name: toolName, arguments: args }, server)
  return result
}

export async function getAllEnabledTools(): Promise<{ server: McpServerConfig; tools: McpTool[] }[]> {
  const servers = await loadMcpServers()
  const enabled = servers.filter(s => s.enabled)
  const results: { server: McpServerConfig; tools: McpTool[] }[] = []
  for (const server of enabled) {
    try {
      const tools = await listTools(server)
      results.push({ server, tools })
    } catch (e) {
      console.warn(`[MCP] Failed to list tools for ${server.name}:`, e)
    }
  }
  return results
}

export interface McpToolDescriptor {
  serverId: string
  serverName: string
  tool: McpTool
}

export async function getAllToolsFlat(): Promise<McpToolDescriptor[]> {
  const results = await getAllEnabledTools()
  return results.flatMap(r => {
    const disabled = r.server.disabledTools || []
    return r.tools
      .filter(t => !disabled.includes(t.name))
      .map(t => ({
        serverId: r.server.id,
        serverName: r.server.name,
        tool: t,
      }))
  })
}
