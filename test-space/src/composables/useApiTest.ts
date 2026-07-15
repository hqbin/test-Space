import { ref, computed } from 'vue'
import type { ApiTestCase, ApiTestGroup, ApiTestReport, ApiTestResult, ApiCapturedRequest } from '@/types'
import * as db from '@/services/database'
import { autoGenerateTestCases, runTestCases, runSingleTestCase, getOrCreateDefaultGroup, exportReport as serviceExportReport } from '@/services/apiTestService'

export function useApiTest() {
  const testCases = ref<ApiTestCase[]>([])
  const groups = ref<ApiTestGroup[]>([])
  const reports = ref<ApiTestReport[]>([])
  const currentReport = ref<ApiTestReport | null>(null)
  const currentResults = ref<ApiTestResult[]>([])
  const selectedGroupId = ref<string>('')
  const isGenerating = ref(false)
  const isRunning = ref(false)
  const runningCaseIds = ref<Set<string>>(new Set())
  const searchQuery = ref('')

  // Global auth headers — multiple pairs for endpoints that need different auth
  const globalAuthHeaders = ref<{ name: string; value: string }[]>([])

  // Domain keywords for filtering which requests to generate test cases for
  const domainKeywords = ref<string[]>(['zeasn', 'whaletv'])

  // Custom endpoint display names, keyed by "groupId:method:path"
  const endpointNames = ref<Record<string, string>>({})

  const filteredCases = computed(() => {
    let list = testCases.value
    if (selectedGroupId.value) {
      list = list.filter(c => c.groupId === selectedGroupId.value)
    }
    if (searchQuery.value) {
      const q = searchQuery.value.toLowerCase()
      list = list.filter(c =>
        c.name.toLowerCase().includes(q) ||
        c.url.toLowerCase().includes(q) ||
        c.path.toLowerCase().includes(q) ||
        c.description.toLowerCase().includes(q)
      )
    }
    return list
  })

  // Group cases by groupId (for group-based rendering)
  const groupedCases = computed(() => {
    const map = new Map<string, ApiTestCase[]>()
    for (const c of filteredCases.value) {
      const list = map.get(c.groupId) || []
      list.push(c)
      map.set(c.groupId, list)
    }
    return map
  })

  // Group cases by endpoint key (method:path) within a group
  function getEndpointCases(groupId: string): Map<string, ApiTestCase[]> {
    const map = new Map<string, ApiTestCase[]>()
    const cases = testCases.value.filter(c => c.groupId === groupId)
    const q = searchQuery.value.toLowerCase()
    for (const c of cases) {
      if (q && !c.name.toLowerCase().includes(q) && !c.url.toLowerCase().includes(q) && !c.path.toLowerCase().includes(q) && !c.description.toLowerCase().includes(q)) continue
      const normalizedPath = c.path.replace(/\/+$/, '')
      const key = `${c.method}:${normalizedPath}`
      const list = map.get(key) || []
      list.push(c)
      map.set(key, list)
    }
    return map
  }

  const selectedGroup = computed(() => groups.value.find(g => g.id === selectedGroupId.value))

  async function loadAll() {
    groups.value = await db.loadApiTestGroups()
    testCases.value = await db.loadApiTestCases()
    if (!selectedGroupId.value && groups.value.length > 0) {
      selectedGroupId.value = groups.value[0].id
    }
    await loadGlobalAuthHeader()
    await loadDomainKeywords()
    await loadEndpointNames()
  }

  async function loadReports() {
    reports.value = await db.loadApiTestReports()
  }

  async function loadGlobalAuthHeader() {
    const stored = await db.getSetting('api_test_global_auth')
    if (stored) {
      try {
        const parsed = JSON.parse(stored)
        if (Array.isArray(parsed)) {
          globalAuthHeaders.value = parsed
        } else if (parsed.name || parsed.value) {
          // Migrate old single-pair format
          globalAuthHeaders.value = [{ name: parsed.name || '', value: parsed.value || '' }]
        }
      } catch {}
    }
  }

  async function saveGlobalAuthHeader(hdrs: { name: string; value: string }[]) {
    globalAuthHeaders.value = hdrs.filter(h => h.name.trim())
    await db.setSetting('api_test_global_auth', JSON.stringify(globalAuthHeaders.value))
  }

  async function loadDomainKeywords() {
    const stored = await db.getSetting('api_test_domain_keywords')
    if (stored) {
      try {
        const parsed = JSON.parse(stored)
        if (Array.isArray(parsed) && parsed.length > 0) {
          domainKeywords.value = parsed
        }
      } catch {}
    }
  }

  async function saveDomainKeywords(keywords: string[]) {
    domainKeywords.value = keywords
    await db.setSetting('api_test_domain_keywords', JSON.stringify(keywords))
  }

  async function loadEndpointNames() {
    const stored = await db.getSetting('api_test_endpoint_names')
    if (stored) {
      try {
        const parsed = JSON.parse(stored)
        if (typeof parsed === 'object' && parsed !== null) {
          endpointNames.value = parsed
        }
      } catch {}
    }
  }

  async function setEndpointName(groupId: string, method: string, path: string, name: string) {
    const key = `${groupId}:${method}:${path.replace(/\/+$/, '')}`
    const map = { ...endpointNames.value }
    if (name.trim()) {
      map[key] = name.trim()
    } else {
      delete map[key]
    }
    endpointNames.value = map
    await db.setSetting('api_test_endpoint_names', JSON.stringify(map))
  }

  function getEndpointName(groupId: string, method: string, path: string): string {
    const key = `${groupId}:${method}:${path.replace(/\/+$/, '')}`
    return endpointNames.value[key] || ''
  }

  function applyGlobalAuth(cases: ApiTestCase[]): ApiTestCase[] {
    const hdrs = globalAuthHeaders.value.filter(h => h.name.trim() && h.value.trim())
    if (hdrs.length === 0) return cases
    return cases.map(tc => {
      let merged = [...tc.headers]
      let url = tc.url
      for (const h of hdrs) {
        // Overwrite matching headers
        const idx = merged.findIndex(([k]) => k.toLowerCase() === h.name.toLowerCase())
        if (idx !== -1) {
          merged[idx] = [h.name, h.value]
        }
        // Replace matching URL query parameter (e.g. ?token=old → ?token=new)
        try {
          const parsed = new URL(url)
          if (parsed.searchParams.has(h.name)) {
            parsed.searchParams.set(h.name, h.value)
            url = parsed.toString()
          }
        } catch {}
      }
      return { ...tc, headers: merged, url }
    })
  }

  function clearGlobalAuth() {
    globalAuthHeaders.value = []
    saveGlobalAuthHeader([])
  }

  // Helper: check if a header pair already exists in the list (case-insensitive name)
  function hasAuthHeader(name: string): boolean {
    return globalAuthHeaders.value.some(h => h.name.toLowerCase() === name.toLowerCase())
  }

  // Auto-detect auth headers from captured request data.
  // Scans request headers (what was actually sent) + response bodies + response headers.
  // Appends to existing global auth headers list (does not replace unless re-fetch clears first).
  function autoDetectToken(requests: ApiCapturedRequest[]): void {
    // Match any header whose name contains token/auth/key/bearer (case-insensitive)
    const authHeaderPattern = /token|auth|key|bearer/i

    // 1) Scan request headers — these are the actual auth headers the device sent
    for (const req of requests) {
      if (!req.request_headers) continue
      for (const [k, v] of req.request_headers) {
        if (authHeaderPattern.test(k) && v.trim()) {
          if (!hasAuthHeader(k)) {
            globalAuthHeaders.value.push({ name: k, value: v })
          }
        }
      }
    }

    // 2) Scan response bodies for token values (e.g. login responses)
    const tokenPatterns = [
      { field: 'token', header: 'Authorization', prefix: 'Bearer ' },
      { field: 'access_token', header: 'Authorization', prefix: 'Bearer ' },
      { field: 'refresh_token', header: 'Authorization', prefix: 'Bearer ' },
      { field: 'jwt', header: 'Authorization', prefix: 'Bearer ' },
      { field: 'id_token', header: 'Authorization', prefix: 'Bearer ' },
      { field: 'session_token', header: 'Authorization', prefix: 'Bearer ' },
      { field: 'auth_token', header: 'Authorization', prefix: 'Bearer ' },
      { field: 'usertoken', header: 'usertoken', prefix: '' },
      { field: 'user_token', header: 'user_token', prefix: '' },
      { field: 'api_key', header: 'X-API-Key', prefix: '' },
      { field: 'apikey', header: 'X-API-Key', prefix: '' },
      { field: 'data.token', header: 'Authorization', prefix: 'Bearer ' },
      { field: 'data.accessToken', header: 'Authorization', prefix: 'Bearer ' },
      { field: 'data.userToken', header: 'userToken', prefix: '' },
      { field: 'result.token', header: 'Authorization', prefix: 'Bearer ' },
      { field: 'result.accessToken', header: 'Authorization', prefix: 'Bearer ' },
    ]

    function findTokenStr(obj: any, depth = 0): { value: string; headerName: string; prefix: string } | null {
      if (depth > 3 || !obj || typeof obj !== 'object') return null
      for (const pattern of tokenPatterns) {
        const val = findNestedValue(obj, pattern.field)
        if (val && typeof val === 'string' && val.length > 8 && val.length < 4096) {
          return { value: val, headerName: pattern.header, prefix: pattern.prefix }
        }
      }
      for (const val of Object.values(obj)) {
        if (typeof val === 'object' && val !== null) {
          const found = findTokenStr(val, depth + 1)
          if (found) return found
        }
      }
      return null
    }

    for (const req of requests) {
      const resBody = req.response_body
      if (!resBody || req.response_body_is_base64) continue
      try {
        const body = JSON.parse(resBody)
        const result = findTokenStr(body)
        if (result && !hasAuthHeader(result.headerName)) {
          globalAuthHeaders.value.push({ name: result.headerName, value: `${result.prefix}${result.value}` })
        }
      } catch {}
    }

    // 4) Scan URL query parameters for auth patterns (e.g. ?token=xxx)
    const authQueryPattern = /token|auth|key|secret|session/i
    for (const req of requests) {
      try {
        const parsed = new URL(req.url || req.host || '')
        for (const [k, v] of parsed.searchParams.entries()) {
          if (authQueryPattern.test(k) && v.trim() && !hasAuthHeader(k)) {
            globalAuthHeaders.value.push({ name: k, value: v })
          }
        }
      } catch {}
    }

    // 3) Scan response headers for Set-Cookie / Authorization
    for (const req of requests) {
      const headers = req.response_headers
      if (!headers) continue
      for (const [k, v] of headers) {
        const lk = k.toLowerCase()
        if (lk === 'set-cookie' && v.includes('token=') && !hasAuthHeader('Authorization')) {
          const match = v.match(/token=([^;]+)/)
          if (match) {
            globalAuthHeaders.value.push({ name: 'Authorization', value: `Bearer ${match[1]}` })
          }
        }
        if (lk === 'authorization' && !hasAuthHeader('Authorization')) {
          globalAuthHeaders.value.push({ name: 'Authorization', value: v })
        }
      }
    }

    if (globalAuthHeaders.value.length > 0) {
      saveGlobalAuthHeader(globalAuthHeaders.value)
    }
  }

  // Filter requests by domain keywords (match against URL or host)
  function filterByDomainKeywords(requests: ApiCapturedRequest[]): ApiCapturedRequest[] {
    const keywords = domainKeywords.value
    if (!keywords || keywords.length === 0) return requests
    return requests.filter(r => {
      const url = (r.url || r.host || '').toLowerCase()
      return keywords.some(k => k && url.includes(k.toLowerCase()))
    })
  }

  async function deleteEndpointCases(groupId: string, method: string, path: string) {
    const toDelete = testCases.value.filter(c => c.groupId === groupId && c.method === method && c.path === path)
    for (const tc of toDelete) {
      await db.deleteApiTestCase(tc.id)
    }
    testCases.value = testCases.value.filter(c => !(c.groupId === groupId && c.method === method && c.path === path))
  }

  async function addGroup(name: string, color?: string) {
    const group: ApiTestGroup = {
      id: crypto.randomUUID(),
      name,
      description: '',
      color: color || '#6366f1',
      sortOrder: groups.value.length,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    }
    await db.saveApiTestGroup(group)
    groups.value.push(group)
    return group
  }

  async function updateGroup(group: ApiTestGroup) {
    await db.saveApiTestGroup(group)
    const idx = groups.value.findIndex(g => g.id === group.id)
    if (idx !== -1) groups.value[idx] = group
  }

  async function deleteGroup(id: string) {
    await db.deleteApiTestGroup(id)
    groups.value = groups.value.filter(g => g.id !== id)
    testCases.value = testCases.value.filter(c => c.groupId !== id)
    if (selectedGroupId.value === id) {
      selectedGroupId.value = groups.value[0]?.id || ''
    }
  }

  async function deleteCasesByGroup(groupId: string) {
    await db.deleteApiTestCasesByGroup(groupId)
    testCases.value = testCases.value.filter(c => c.groupId !== groupId)
  }

  async function generateCases(requests: ApiCapturedRequest[], useAi: boolean = false) {
    isGenerating.value = true
    try {
      // Auto-detect token from captured requests first
      autoDetectToken(requests)

      // Use the currently selected group, or fall back to default
      let groupId = selectedGroupId.value
      if (!groupId || !groups.value.find(g => g.id === groupId)) {
        const group = await getOrCreateDefaultGroup()
        if (!groups.value.find(g => g.id === group.id)) {
          groups.value.unshift(group)
        }
        groupId = group.id
        selectedGroupId.value = groupId
      }

      // Filter requests by domain keywords (zeasn, whaletv, etc.)
      const filtered = filterByDomainKeywords(requests)
      if (filtered.length === 0) {
        return []
      }

      const { cases } = await autoGenerateTestCases(
        filtered, groupId, useAi
      )
      // NOTE: Do NOT apply global auth here — token should only be injected at run time,
      // not baked into saved cases, otherwise cases become useless after token expiry.
      if (cases.length > 0) {
        for (const tc of cases) {
          await db.saveApiTestCase(tc)
        }
        testCases.value.push(...cases)
      }
      return cases
    } finally {
      isGenerating.value = false
    }
  }

  async function runAll(): Promise<{ report: ApiTestReport; results: ApiTestResult[] }> {
    isRunning.value = true
    try {
      const cases = applyGlobalAuth(testCases.value.filter(c => c.enabled))
      const { report, results } = await runTestCases(cases, `全部运行 ${new Date().toLocaleString()}`)
      currentReport.value = report
      currentResults.value = results
      await loadReports()
      return { report, results }
    } finally {
      isRunning.value = false
    }
  }

  async function runGroup(groupId: string, onProgress?: (idx: number) => void): Promise<{ report: ApiTestReport; results: ApiTestResult[] }> {
    isRunning.value = true
    try {
      const cases = applyGlobalAuth(testCases.value.filter(c => c.groupId === groupId && c.enabled))
      const group = groups.value.find(g => g.id === groupId)
      const { report, results } = await runTestCases(cases, `${group?.name || '分组'}运行 ${new Date().toLocaleString()}`, onProgress)
      currentReport.value = report
      currentResults.value = results
      await loadReports()
      return { report, results }
    } finally {
      isRunning.value = false
    }
  }

  async function runSingle(tc: ApiTestCase): Promise<ApiTestResult> {
    const set = new Set(runningCaseIds.value)
    set.add(tc.id)
    runningCaseIds.value = set
    try {
      const withAuth = applyGlobalAuth([tc])[0]
      const result = await runSingleTestCase(withAuth)
      const idx = currentResults.value.findIndex(r => r.caseId === tc.id)
      if (idx !== -1) {
        currentResults.value[idx] = result
      } else {
        currentResults.value.push(result)
      }
      return result
    } finally {
      const s = new Set(runningCaseIds.value)
      s.delete(tc.id)
      runningCaseIds.value = s
    }
  }

  async function loadReport(reportId: string) {
    const report = reports.value.find(r => r.id === reportId)
    if (report) {
      currentReport.value = report
      currentResults.value = await db.loadApiTestResults(reportId)
    }
  }

  async function deleteReport(reportId: string) {
    await db.deleteApiTestReport(reportId)
    reports.value = reports.value.filter(r => r.id !== reportId)
    if (currentReport.value?.id === reportId) {
      currentReport.value = null
      currentResults.value = []
    }
  }

  async function exportReport(reportId: string): Promise<void> {
    await serviceExportReport(reportId)
  }

  async function toggleCaseEnabled(tc: ApiTestCase) {
    tc.enabled = !tc.enabled
    await db.saveApiTestCase(tc)
  }

  async function updateTestCase(tc: ApiTestCase) {
    await db.saveApiTestCase(tc)
    const idx = testCases.value.findIndex(c => c.id === tc.id)
    if (idx !== -1) testCases.value[idx] = tc
  }

  async function deleteTestCase(id: string) {
    await db.deleteApiTestCase(id)
    testCases.value = testCases.value.filter(c => c.id !== id)
  }

  async function createManualTestCase(params: {
    groupId: string
    name: string
    method: string
    url: string
    headers?: string[][]
    body?: string | null
    type?: 'positive' | 'negative'
  }): Promise<ApiTestCase> {
    let host = ''
    let path = ''
    let query: string | null = null
    try {
      const parsed = new URL(params.url)
      host = parsed.host
      path = parsed.pathname.replace(/\/+$/, '') || '/'
      query = parsed.search ? parsed.search.slice(1) : null
    } catch {
      path = params.url.replace(/\/+$/, '') || '/'
    }
    const tc: ApiTestCase = {
      id: crypto.randomUUID(),
      groupId: params.groupId,
      name: params.name,
      description: '',
      type: params.type || 'positive',
      method: params.method.toUpperCase(),
      url: params.url,
      host,
      path,
      query,
      headers: params.headers || [],
      body: params.method.toUpperCase() !== 'GET' ? (params.body ?? null) : null,
      bodyIsBase64: false,
      assertions: [
        { id: crypto.randomUUID(), type: 'status_code', operator: 'equals', target: 'status_code', expectedValue: '200' },
      ],
      sourceRequestId: null,
      enabled: true,
      sortOrder: testCases.value.filter(c => c.groupId === params.groupId).length,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    }
    await db.saveApiTestCase(tc)
    testCases.value.push(tc)
    return tc
  }

  return {
    testCases, groups, reports, currentReport, currentResults,
    selectedGroupId, isGenerating, isRunning, runningCaseIds, searchQuery,
    globalAuthHeaders, domainKeywords,
    filteredCases, groupedCases, getEndpointCases, selectedGroup,
    loadAll, loadReports,
    addGroup, updateGroup, deleteGroup, deleteCasesByGroup,
    generateCases,
    runAll, runGroup, runSingle,
    loadReport, deleteReport, exportReport,
    toggleCaseEnabled, updateTestCase, deleteTestCase, deleteEndpointCases, createManualTestCase,
    saveGlobalAuthHeader, saveDomainKeywords, filterByDomainKeywords,
    autoDetectToken, clearGlobalAuth,
    endpointNames, setEndpointName, getEndpointName,
  }
}

function findNestedValue(obj: any, path: string): any {
  const parts = path.split('.')
  let current = obj
  for (const part of parts) {
    if (current == null || typeof current !== 'object') return undefined
    // Try the exact key, then case-insensitive
    if (part in current) {
      current = current[part]
    } else {
      const keys = Object.keys(current)
      const found = keys.find(k => k.toLowerCase() === part.toLowerCase())
      if (found) {
        current = current[found]
      } else {
        return undefined
      }
    }
  }
  return current
}
