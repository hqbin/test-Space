import type { AiConfig } from '@/services/aiSettings'
import { type AiChatMessage, resolveSystemRole } from '@/services/noteAi'
import type { ApiCapturedRequest, ApiTestCase, ApiTestAssertion } from '@/types'
import * as db from '@/services/database'

let _tauriFetch: typeof fetch | null = null
async function getFetch(): Promise<typeof fetch> {
  if (_tauriFetch) return _tauriFetch
  try {
    const mod = await import('@tauri-apps/plugin-http')
    _tauriFetch = mod.fetch
  } catch {
    _tauriFetch = fetch
  }
  return _tauriFetch!
}

async function callApi(config: AiConfig, messages: AiChatMessage[]): Promise<any> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (config.authMode === 'api-key') {
    headers['api-key'] = config.apiKey.trim()
  } else {
    headers['Authorization'] = `Bearer ${config.apiKey.trim()}`
  }
  const body: Record<string, unknown> = { model: config.model.trim(), messages }
  const f = await getFetch()
  const res = await f(config.endpoint.trim(), {
    method: 'POST',
    headers,
    body: JSON.stringify(body),
  })
  const text = await res.text()
  let json: any
  try { json = JSON.parse(text) } catch {
    throw new Error(`API 返回非 JSON (HTTP ${res.status}): ${text.slice(0, 300)}`)
  }
  if (!res.ok) {
    const errMsg = json.error?.message || json.error?.code || json.error || json.message || `HTTP ${res.status}`
    throw new Error(typeof errMsg === 'string' ? errMsg : JSON.stringify(errMsg))
  }
  return json
}

interface GeneratedTestCase {
  name: string
  description: string
  type: 'positive' | 'negative'
  method: string
  url: string
  headers: Record<string, string>
  body: string | null
  expectedStatusCode: number
  assertions: { type: string; operator: string; target: string; expectedValue: string; description?: string }[]
}

interface MergedEndpoint {
  path: string
  method: string
  host: string
  allUrls: string[]
  allQueries: string[]
  allBodyFields: Set<string>
  allBodyValues: Record<string, string[]>
  sampleHeaders: string[][]
  sampleBody: string | null
  hasAuth: boolean
  authHeader: [string, string] | null
  contentType: string | null
  sourceIds: string[]
}

const BINARY_EXTENSIONS = new Set([
  '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.ico', '.svg',
  '.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.webm',
  '.mp3', '.wav', '.ogg', '.aac', '.flac', '.wma',
  '.woff', '.woff2', '.ttf', '.otf', '.eot',
  '.zip', '.rar', '.7z', '.tar', '.gz',
  '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
])

const BINARY_CONTENT_PREFIXES = [
  'image/', 'video/', 'audio/', 'font/', 'application/octet-stream',
  'application/pdf', 'application/zip', 'application/x-zip',
  'application/vnd.',
]

function isBinaryContent(req: ApiCapturedRequest): boolean {
  // Check URL extension
  const path = req.path.toLowerCase()
  for (const ext of BINARY_EXTENSIONS) {
    if (path.endsWith(ext)) return true
  }

  // Check response content-type
  if (req.response_headers) {
    for (const [k, v] of req.response_headers) {
      if (k.toLowerCase() === 'content-type') {
        const ct = v.toLowerCase()
        for (const prefix of BINARY_CONTENT_PREFIXES) {
          if (ct.startsWith(prefix)) return true
        }
      }
    }
  }

  // Check request content-type
  if (req.request_headers) {
    for (const [k, v] of req.request_headers) {
      if (k.toLowerCase() === 'content-type') {
        const ct = v.toLowerCase()
        if (ct.startsWith('multipart/form-data')) return false
        for (const prefix of BINARY_CONTENT_PREFIXES) {
          if (ct.startsWith(prefix)) return true
        }
      }
    }
  }

  // Body is base64 (binary)
  if (req.request_body_is_base64 || req.response_body_is_base64) return true

  return false
}

function mergeRequests(requests: ApiCapturedRequest[]): MergedEndpoint[] {
  const groups = new Map<string, MergedEndpoint>()

  for (const req of requests) {
    const key = `${req.method}:${req.path}`

    if (!groups.has(key)) {
      groups.set(key, {
        path: req.path,
        method: req.method,
        host: req.host,
        allUrls: [req.url],
        allQueries: req.query ? [req.query] : [],
        allBodyFields: new Set(),
        allBodyValues: {},
        sampleHeaders: req.request_headers,
        sampleBody: req.request_body,
        hasAuth: req.request_headers.some(([k]) => /authorization|token|api[_-]?key/i.test(k)),
        authHeader: req.request_headers.find(([k]) => /authorization|token|api[_-]?key/i.test(k)) as [string, string] | null || null,
        contentType: req.request_headers.find(([k]) => k.toLowerCase() === 'content-type')?.[1] || null,
        sourceIds: [req.id],
      })
    } else {
      const group = groups.get(key)!
      if (!group.allUrls.includes(req.url)) group.allUrls.push(req.url)
      if (req.query && !group.allQueries.includes(req.query)) group.allQueries.push(req.query)
      if (!group.sourceIds.includes(req.id)) group.sourceIds.push(req.id)
      if (!group.contentType) {
        group.contentType = req.request_headers.find(([k]) => k.toLowerCase() === 'content-type')?.[1] || null
      }
    }

    // Collect all unique body fields from JSON payloads
    const group = groups.get(key)!
    if (req.request_body && !req.request_body_is_base64) {
      try {
        const body = JSON.parse(req.request_body)
        collectFields(body, '', group.allBodyFields, group.allBodyValues)
      } catch {}
    }
  }

  return Array.from(groups.values())
}

function collectFields(obj: any, prefix: string, fields: Set<string>, values: Record<string, string[]>) {
  if (typeof obj !== 'object' || obj === null) return
  for (const [k, v] of Object.entries(obj)) {
    const path = prefix ? `${prefix}.${k}` : k
    fields.add(path)
    if (!values[path]) values[path] = []
    const sv = typeof v === 'object' && v !== null ? JSON.stringify(v) : String(v)
    if (!values[path].includes(sv)) values[path].push(sv)
    if (typeof v === 'object' && v !== null) {
      collectFields(v, path, fields, values)
    }
  }
}

function generateSmartTestCases(req: ApiCapturedRequest, merged?: MergedEndpoint): GeneratedTestCase[] {
  const cases: GeneratedTestCase[] = []
  const path = req.path
  const pathKey = path.split('/').filter(Boolean).join('_') || 'root'
  const endpoint = merged || mergeRequests([req])[0]

  // Use all observed query params from merged group
  const allQueryParams = new Map<string, Set<string>>()
  for (const q of endpoint.allQueries) {
    const sp = new URLSearchParams(q)
    sp.forEach((v, k) => {
      if (!allQueryParams.has(k)) allQueryParams.set(k, new Set())
      allQueryParams.get(k)!.add(v)
    })
  }

  // Build a comprehensive URL with all possible query params
  const baseUrl = endpoint.allUrls[0].split('?')[0]
  const queryParts: string[] = []
  allQueryParams.forEach((vals, k) => {
    const v = Array.from(vals)[0]
    queryParts.push(`${k}=${v}`)
  })
  const fullUrl = queryParts.length > 0 ? `${baseUrl}?${queryParts.join('&')}` : baseUrl

  // Parse body fields from merged data
  const bodyFields = Array.from(endpoint.allBodyFields).sort()
  let bodyJson: any = null
  if (req.request_body && !req.request_body_is_base64) {
    try { bodyJson = JSON.parse(req.request_body) } catch {}
  }

  const hasAuth = endpoint.hasAuth
  const authHeader = endpoint.authHeader
  const contentType = endpoint.contentType

  // ── Positive case (dedup: one positive per endpoint) ──
  const positiveAssertions: { type: string; operator: string; target: string; expectedValue: string; description?: string }[] = [
    { type: 'status_code', operator: 'equals', target: 'status_code', expectedValue: '200', description: '期望状态码 200' },
    { type: 'response_time', operator: 'less_than', target: 'duration_ms', expectedValue: '5000', description: '响应时间小于5秒' },
  ]
  // Add response body contains check for non-GET or when body is present
  if (req.response_body && !req.response_body_is_base64) {
    const resBody = tryParseJson(req.response_body)
    if (typeof resBody === 'object' && resBody !== null) {
      const keys = Object.keys(resBody)
      if (keys.length > 0) {
        positiveAssertions.push({
          type: 'json_path',
          operator: 'contains',
          target: keys[0],
          expectedValue: String(resBody[keys[0]]).slice(0, 100),
          description: `验证响应中包含字段 ${keys[0]}`,
        })
      }
    }
  }
  cases.push({
    name: `${pathKey}_positive`,
    description: `正向用例：正常请求 ${endpoint.method} ${path}`,
    type: 'positive',
    method: endpoint.method,
    url: fullUrl,
    headers: Object.fromEntries(endpoint.sampleHeaders.map(([k, v]) => [k, v])),
    body: endpoint.sampleBody,
    expectedStatusCode: 200,
    assertions: positiveAssertions,
  })

  // ── Negative: 无效/过期Token ──
  if (hasAuth && authHeader) {
    const [hdr, val] = authHeader
    const fakeVal = val.length > 8 ? val.slice(0, -4) + 'xxxx' : 'invalid_token_xxx'
    cases.push({
      name: `${pathKey}_negative_invalid_auth`,
      description: `反向用例：无效${hdr}认证`,
      type: 'negative',
      method: endpoint.method,
      url: fullUrl,
      headers: { ...Object.fromEntries(endpoint.sampleHeaders.map(([k, v]) => [k, v])), [hdr]: fakeVal },
      body: endpoint.sampleBody,
      expectedStatusCode: 401,
      assertions: [
        { type: 'status_code', operator: 'equals', target: 'status_code', expectedValue: '401', description: '期望状态码 401' },
      ],
    })
  }

  // ── Negative: 缺失Authorization ──
  if (hasAuth && authHeader) {
    const [hdr] = authHeader
    const filteredHeaders = Object.fromEntries(
      endpoint.sampleHeaders.filter(([k]) => k.toLowerCase() !== hdr.toLowerCase()).map(([k, v]) => [k, v])
    )
    cases.push({
      name: `${pathKey}_negative_missing_auth`,
      description: `反向用例：缺失${hdr}请求头`,
      type: 'negative',
      method: endpoint.method,
      url: fullUrl,
      headers: filteredHeaders,
      body: endpoint.sampleBody,
      expectedStatusCode: 401,
      assertions: [
        { type: 'status_code', operator: 'equals', target: 'status_code', expectedValue: '401', description: '期望状态码 401' },
      ],
    })
  }

  // ── Negative: 错误 Content-Type ──
  if (endpoint.method !== 'GET' && contentType) {
    cases.push({
      name: `${pathKey}_negative_wrong_content_type`,
      description: '反向用例：错误的Content-Type',
      type: 'negative',
      method: endpoint.method,
      url: fullUrl,
      headers: { ...Object.fromEntries(endpoint.sampleHeaders.map(([k, v]) => [k, v])), 'Content-Type': 'application/xml' },
      body: endpoint.sampleBody,
      expectedStatusCode: 415,
      assertions: [
        { type: 'status_code', operator: 'equals', target: 'status_code', expectedValue: '415', description: '期望状态码 415' },
      ],
    })
  }

  // ── Negative: 请求体为空 ──
  if (['POST', 'PUT', 'PATCH'].includes(endpoint.method) && endpoint.sampleBody) {
    cases.push({
      name: `${pathKey}_negative_empty_body`,
      description: '反向用例：请求体为空',
      type: 'negative',
      method: endpoint.method,
      url: fullUrl,
      headers: Object.fromEntries(endpoint.sampleHeaders.map(([k, v]) => [k, v])),
      body: null,
      expectedStatusCode: 400,
      assertions: [
        { type: 'status_code', operator: 'equals', target: 'status_code', expectedValue: '400', description: '期望状态码 400' },
      ],
    })
  }

  // ── Negative: 错误 Method ──
  const wrongMethods = endpoint.method === 'GET' ? ['POST', 'PUT', 'DELETE'] : ['GET']
  for (const wrongMethod of wrongMethods.slice(0, 2)) {
    cases.push({
      name: `${pathKey}_negative_wrong_method_${wrongMethod}`,
      description: `反向用例：使用${wrongMethod}方法请求`,
      type: 'negative',
      method: wrongMethod,
      url: fullUrl,
      headers: Object.fromEntries(endpoint.sampleHeaders.map(([k, v]) => [k, v])),
      body: ['POST', 'PUT', 'PATCH'].includes(wrongMethod) ? endpoint.sampleBody : null,
      expectedStatusCode: 405,
      assertions: [
        { type: 'status_code', operator: 'equals', target: 'status_code', expectedValue: '405', description: '期望状态码 405' },
      ],
    })
  }

  // ── Negative: 全部 query 缺失 ──
  if (allQueryParams.size > 0) {
    const noQueryUrl = baseUrl
    cases.push({
      name: `${pathKey}_negative_missing_all_queries`,
      description: `反向用例：缺失所有 query 参数`,
      type: 'negative',
      method: endpoint.method,
      url: noQueryUrl,
      headers: Object.fromEntries(endpoint.sampleHeaders.map(([k, v]) => [k, v])),
      body: endpoint.sampleBody,
      expectedStatusCode: 400,
      assertions: [
        { type: 'status_code', operator: 'equals', target: 'status_code', expectedValue: '400', description: '期望状态码 400' },
      ],
    })
  }

  // ── Negative: 逐个缺失 query 参数 ──
  if (allQueryParams.size >= 1) {
    const firstKey = Array.from(allQueryParams.keys())[0]
    const remainingParams = Array.from(allQueryParams.keys()).filter(k => k !== firstKey)
    const partialQuery = remainingParams.map(k => {
      const vals = Array.from(allQueryParams.get(k)!)
      return `${k}=${vals[0]}`
    }).join('&')
    const partialUrl = partialQuery ? `${baseUrl}?${partialQuery}` : baseUrl
    cases.push({
      name: `${pathKey}_negative_missing_query_${firstKey}`,
      description: `反向用例：缺少 query 参数 ${firstKey}`,
      type: 'negative',
      method: endpoint.method,
      url: partialUrl,
      headers: Object.fromEntries(endpoint.sampleHeaders.map(([k, v]) => [k, v])),
      body: endpoint.sampleBody,
      expectedStatusCode: 400,
      assertions: [
        { type: 'status_code', operator: 'equals', target: 'status_code', expectedValue: '400', description: '期望状态码 400' },
      ],
    })
  }

  // ── Negative: JSON body 字段逐个缺失 + 类型错误 (covering all observed fields) ──
  if (bodyFields.length > 0 && bodyJson && typeof bodyJson === 'object' && !Array.isArray(bodyJson)) {
    for (const field of bodyFields.slice(0, 3)) {
      const mutatedBody = { ...bodyJson }
      delete mutatedBody[field]
      cases.push({
        name: `${pathKey}_negative_missing_field_${field}`,
        description: `反向用例：缺少必填字段 ${field}`,
        type: 'negative',
        method: endpoint.method,
        url: fullUrl,
        headers: Object.fromEntries(endpoint.sampleHeaders.map(([k, v]) => [k, v])),
        body: JSON.stringify(mutatedBody),
        expectedStatusCode: 400,
        assertions: [
          { type: 'status_code', operator: 'equals', target: 'status_code', expectedValue: '400', description: '期望状态码 400' },
        ],
      })
    }

    // Type error for string fields
    const strFields = bodyFields.filter(f => {
      const parts = f.split('.')
      let val: any = bodyJson
      for (const p of parts) { val = val?.[p] }
      return typeof val === 'string'
    })
    for (const field of strFields.slice(0, 2)) {
      const mutatedBody = { ...bodyJson }
      setNestedField(mutatedBody, field, 12345)
      cases.push({
        name: `${pathKey}_negative_wrong_type_${field}`,
        description: `反向用例：字段 ${field} 类型错误（应为字符串，传数字）`,
        type: 'negative',
        method: endpoint.method,
        url: fullUrl,
        headers: Object.fromEntries(endpoint.sampleHeaders.map(([k, v]) => [k, v])),
        body: JSON.stringify(mutatedBody),
        expectedStatusCode: 400,
        assertions: [
          { type: 'status_code', operator: 'equals', target: 'status_code', expectedValue: '400', description: '期望状态码 400' },
        ],
      })
    }

    // Empty string for string fields
    for (const field of strFields.slice(0, 1)) {
      const mutatedBody = { ...bodyJson }
      setNestedField(mutatedBody, field, '')
      cases.push({
        name: `${pathKey}_negative_empty_field_${field}`,
        description: `反向用例：字段 ${field} 传空字符串`,
        type: 'negative',
        method: endpoint.method,
        url: fullUrl,
        headers: Object.fromEntries(endpoint.sampleHeaders.map(([k, v]) => [k, v])),
        body: JSON.stringify(mutatedBody),
        expectedStatusCode: 400,
        assertions: [
          { type: 'status_code', operator: 'equals', target: 'status_code', expectedValue: '400', description: '期望状态码 400' },
        ],
      })
    }
  }

  // ── Negative: 超长 query 参数值 ──
  if (allQueryParams.size > 0) {
    const firstKey = Array.from(allQueryParams.keys())[0]
    const overflowParams = Array.from(allQueryParams.keys()).map(k => {
      if (k === firstKey) return `${k}=${'a'.repeat(10000)}`
      const vals = Array.from(allQueryParams.get(k)!)
      return `${k}=${vals[0]}`
    }).join('&')
    const overflowUrl = `${baseUrl}?${overflowParams}`
    cases.push({
      name: `${pathKey}_negative_overflow_param`,
      description: `反向用例：参数 ${firstKey} 超长（10000字符）`,
      type: 'negative',
      method: endpoint.method,
      url: overflowUrl,
      headers: Object.fromEntries(endpoint.sampleHeaders.map(([k, v]) => [k, v])),
      body: endpoint.sampleBody,
      expectedStatusCode: 400,
      assertions: [
        { type: 'status_code', operator: 'equals', target: 'status_code', expectedValue: '400', description: '期望状态码 400' },
      ],
    })
  }

  return cases
}

function setNestedField(obj: any, path: string, value: any) {
  const parts = path.split('.')
  let current = obj
  for (let i = 0; i < parts.length - 1; i++) {
    if (current[parts[i]] === undefined) current[parts[i]] = {}
    current = current[parts[i]]
  }
  current[parts[parts.length - 1]] = value
}

export async function generateTestCasesWithAi(
  config: AiConfig,
  requests: ApiCapturedRequest[]
): Promise<GeneratedTestCase[]> {
  const mergedEndpoints = mergeRequests(requests)
  const requestSummaries = mergedEndpoints.map(e => ({
    method: e.method,
    path: e.path,
    host: e.host,
    urlCount: e.allUrls.length,
    allQueries: [...new Set(e.allQueries.flatMap(q => q.split('&').map(p => p.split('=')[0])))],
    bodyFields: Array.from(e.allBodyFields),
    sampleHeaders: Object.fromEntries(e.sampleHeaders),
    sampleBody: e.sampleBody,
    statusCodes: requests.filter(r => e.sourceIds.includes(r.id)).map(r => r.response_status_code).filter(Boolean),
  }))

  const messages: AiChatMessage[] = [
    {
      role: resolveSystemRole(config),
      content: `你是一个专业的 API 测试用例生成助手。

注意：已对重复接口（相同 Method + Path）进行了去重合并，以下每个条目代表一个独立接口。

每个接口需要生成：
1. **1个正向用例**：正常请求，验证正确响应
2. **多个反向用例**（尽可能覆盖）：
   - 无效/缺失认证（如 Authorization token 错误或缺失）
   - 错误 HTTP Method（GET/POST/PUT/DELETE 互换）
   - 缺少必填参数（query 参数逐个缺失）
   - 参数类型错误（如字符串传数字）
   - 参数边界值（超长、空值、特殊字符）
   - 错误 Content-Type
   - 请求体为空
   - 超长参数值 / XSS 注入

请以 JSON 格式返回，格式为：
{
  "testCases": [
    {
      "name": "用例名称（英文或拼音，唯一）",
      "description": "用例描述（中文）",
      "type": "positive" 或 "negative",
      "method": "GET/POST/PUT/DELETE等",
      "url": "完整请求URL",
      "headers": { "Header-Name": "value" },
      "body": "请求体字符串（可为null）",
      "expectedStatusCode": 200,
      "assertions": [
        { "type": "status_code", "operator": "equals", "target": "status_code", "expectedValue": "200", "description": "验证状态码" }
      ]
    }
  ]
}`,
    },
    {
      role: 'user',
      content: `请为以下 ${mergedEndpoints.length} 个已去重的接口生成全面的测试用例：\n${JSON.stringify(requestSummaries, null, 2)}`,
    },
  ]

  const json = await callApi(config, messages)
  const raw = json.choices?.[0]?.message?.content || json.choices?.[0]?.text || ''

  try {
    const parsed = JSON.parse(raw)
    if (parsed.testCases && Array.isArray(parsed.testCases)) {
      return parsed.testCases
    }
    if (Array.isArray(parsed)) return parsed
  } catch {}

  const jsonMatch = raw.match(/\{[\s\S]*"testCases"[\s\S]*\}/)
  if (jsonMatch) {
    try {
      const parsed = JSON.parse(jsonMatch[0])
      if (parsed.testCases && Array.isArray(parsed.testCases)) return parsed.testCases
    } catch {}
  }

  const arrMatch = raw.match(/\[[\s\S]*\]/)
  if (arrMatch) {
    try {
      const parsed = JSON.parse(arrMatch[0])
      if (Array.isArray(parsed)) return parsed
    } catch {}
  }

  throw new Error('AI 返回格式无法解析，请重试')
}

function tryParseJson(str: string): any {
  try { return JSON.parse(str) } catch { return str }
}

export function convertGeneratedToTestCases(
  generated: GeneratedTestCase[],
  groupId: string,
  sourceRequests: ApiCapturedRequest[]
): ApiTestCase[] {
  return generated.map((g, i) => {
    const sourceReq = sourceRequests.find(r => r.url === g.url && r.method === g.method)
    const now = new Date().toISOString()
    return {
      id: crypto.randomUUID(),
      groupId,
      name: g.name || `test_case_${i + 1}`,
      description: g.description || '',
      type: g.type,
      method: g.method,
      url: g.url,
      host: sourceReq?.host || '',
      path: sourceReq?.path || new URL(g.url).pathname,
      query: sourceReq?.query || null,
      headers: Object.entries(g.headers || {}).map(([k, v]) => [k, v]),
      body: g.body || null,
      bodyIsBase64: false,
      assertions: (g.assertions || []).map(a => ({
        id: crypto.randomUUID(),
        type: a.type as ApiTestAssertion['type'],
        operator: a.operator as ApiTestAssertion['operator'],
        target: a.target,
        expectedValue: a.expectedValue,
        description: a.description,
      })),
      sourceRequestId: sourceReq?.id || null,
      enabled: true,
      sortOrder: i,
      createdAt: now,
      updatedAt: now,
    }
  })
}

export async function autoGenerateFromRequests(
  requests: ApiCapturedRequest[],
  groupId: string
): Promise<{ cases: ApiTestCase[] }> {
  // Filter out binary content requests
  const newRequests = requests.filter(r => !isBinaryContent(r))
  if (newRequests.length === 0) return { cases: [] }

  // Merge requests to deduplicate
  const merged = mergeRequests(newRequests)

  // Generate test cases for each merged endpoint
  const allCases: ApiTestCase[] = []
  for (const endpoint of merged) {
    // Pick a representative request from this group
    const repReq = newRequests.find(r => `${r.method}:${r.path}` === `${endpoint.method}:${endpoint.path}`)
    if (!repReq) continue
    const generated = generateSmartTestCases(repReq, endpoint)
    const cases = convertGeneratedToTestCases(generated, groupId, [repReq])
    allCases.push(...cases)
  }

  // Save all cases to DB
  for (const tc of allCases) {
    await db.saveApiTestCase(tc)
  }

  return { cases: allCases }
}

export { generateSmartTestCases, mergeRequests, isBinaryContent as isBinaryRequest }
