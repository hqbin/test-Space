import type { ApiCapturedRequest, ApiTestCase, ApiTestResult, ApiTestReport, ApiTestGroup } from '@/types'
import { autoGenerateFromRequests, generateTestCasesWithAi, convertGeneratedToTestCases, isBinaryRequest } from '@/services/apiTestAi'
import * as db from '@/services/database'
import type { AiConfig } from '@/services/aiSettings'
import { loadAiConfig, isAiConfigured } from '@/services/aiSettings'
import { invoke } from '@tauri-apps/api/core'

export async function autoGenerateTestCases(
  requests: ApiCapturedRequest[],
  groupId: string,
  useAi: boolean = false
): Promise<{ cases: ApiTestCase[] }> {
  if (useAi) {
    try {
      const config = await loadAiConfig()
      if (isAiConfigured(config)) {
        const newRequests = requests.filter(r => !isBinaryRequest(r))
        if (newRequests.length === 0) return { cases: [] }
        const generated = await generateTestCasesWithAi(config, newRequests)
        const cases = convertGeneratedToTestCases(generated, groupId, newRequests)
        for (const tc of cases) {
          await db.saveApiTestCase(tc)
        }
        return { cases }
      }
    } catch (e) {
      console.warn('AI 生成失败，回退到智能生成:', e)
    }
  }

  return autoGenerateFromRequests(requests, groupId)
}

interface TestRunResult {
  status_code: number
  status_text: string
  headers: string[][]
  body: string
  body_is_base64: boolean
  duration_ms: number
  error: string | null
}

export async function runSingleTestCase(testCase: ApiTestCase): Promise<ApiTestResult> {
  const resultId = crypto.randomUUID()
  const now = new Date().toISOString()
  const result: ApiTestResult = {
    id: resultId,
    caseId: testCase.id,
    reportId: '',
    passed: false,
    statusCode: null,
    responseBody: null,
    responseHeaders: null,
    duration: null,
    errorMessage: null,
    assertionResults: [],
    startedAt: now,
    completedAt: null,
  }

  try {
    const res = await invoke<TestRunResult>('proxy_run_test', {
      method: testCase.method,
      url: testCase.url,
      headers: testCase.headers.filter(([k]) => {
        const lk = k.toLowerCase()
        return lk !== 'content-length'
      }),
      body: (testCase.body && !testCase.bodyIsBase64 && !['GET', 'HEAD'].includes(testCase.method))
        ? testCase.body : null,
      timeoutSecs: 30,
    })

    if (res.error) {
      result.errorMessage = res.error
      result.passed = false
      result.completedAt = new Date().toISOString()
      return result
    }

    result.statusCode = res.status_code
    result.duration = res.duration_ms
    result.responseHeaders = res.headers
    result.responseBody = res.body

    const responseText = res.body

    // Run assertions
    const assertionResults: { assertionId: string; passed: boolean; actual: string; expected: string }[] = []
    for (const assertion of testCase.assertions) {
      let passed = false
      let actual = ''

      switch (assertion.type) {
        case 'status_code': {
          actual = String(res.status_code)
          switch (assertion.operator) {
            case 'equals': passed = actual === assertion.expectedValue; break
            case 'not_equals': passed = actual !== assertion.expectedValue; break
            default: passed = actual === assertion.expectedValue; break
          }
          break
        }
        case 'body_contains': {
          actual = responseText.includes(assertion.target) ? `包含"${assertion.target}"` : `不包含"${assertion.target}"`
          switch (assertion.operator) {
            case 'contains': passed = responseText.includes(assertion.target); break
            case 'not_contains': passed = !responseText.includes(assertion.target); break
            default: passed = responseText.includes(assertion.target); break
          }
          break
        }
        case 'json_path': {
          try {
            const body = JSON.parse(responseText)
            const segments = assertion.target.split('.')
            let val: any = body
            for (const seg of segments) {
              if (val == null) break
              const bracketMatch = seg.match(/^([^\[]*)\[(\d+)\]$/)
              if (bracketMatch) {
                if (bracketMatch[1]) val = val[bracketMatch[1]]
                val = val?.[Number(bracketMatch[2])]
              } else {
                val = val[seg]
              }
            }
            const isComplex = val !== null && typeof val === 'object'
            actual = isComplex ? JSON.stringify(val) : val !== undefined ? String(val) : 'undefined'
            const expected = assertion.expectedValue
            switch (assertion.operator) {
              case 'equals': passed = isComplex ? JSON.stringify(val) === expected : String(val) === expected; break
              case 'not_equals': passed = isComplex ? JSON.stringify(val) !== expected : String(val) !== expected; break
              case 'contains': passed = isComplex ? JSON.stringify(val).includes(expected) : String(val).includes(expected); break
              case 'exists': passed = val !== undefined; break
              case 'not_exists': passed = val === undefined; break
              default: passed = isComplex ? JSON.stringify(val) === expected : String(val) === expected; break
            }
          } catch {
            actual = '无法解析JSON响应体'
            passed = false
          }
          break
        }
        case 'header': {
          const headerVal = res.headers.find(([k]) => k.toLowerCase() === assertion.target.toLowerCase())
          actual = headerVal ? headerVal[1] : 'undefined'
          switch (assertion.operator) {
            case 'equals': passed = actual === assertion.expectedValue; break
            case 'contains': passed = actual.includes(assertion.expectedValue); break
            case 'exists': passed = headerVal !== undefined; break
            case 'not_exists': passed = headerVal === undefined; break
            default: passed = actual === assertion.expectedValue; break
          }
          break
        }
        case 'response_time': {
          actual = `${res.duration_ms.toFixed(1)}ms`
          switch (assertion.operator) {
            case 'less_than': passed = res.duration_ms < Number(assertion.expectedValue); break
            case 'greater_than': passed = res.duration_ms > Number(assertion.expectedValue); break
            default: passed = res.duration_ms < Number(assertion.expectedValue); break
          }
          break
        }
        case 'json_schema': {
          try {
            const body = JSON.parse(responseText)
            const schema = JSON.parse(assertion.expectedValue)
            passed = validateJsonSchema(body, schema)
            actual = passed ? '符合Schema' : '不符合Schema'
          } catch {
            actual = 'Schema验证异常'
            passed = false
          }
          break
        }
        default: {
          passed = false
          actual = '未知断言类型'
          break
        }
      }

      assertionResults.push({
        assertionId: assertion.id,
        passed,
        actual,
        expected: assertion.type === 'body_contains'
          ? (assertion.operator === 'not_contains' ? `不包含"${assertion.target}"` : `包含"${assertion.target}"`)
          : assertion.type === 'response_time'
            ? `${assertion.operator === 'greater_than' ? '>' : '<'} ${assertion.expectedValue}ms`
            : assertion.expectedValue,
      })
    }

    result.assertionResults = assertionResults
    result.passed = assertionResults.every(a => a.passed)
  } catch (e: any) {
    result.errorMessage = e.message || String(e)
    result.passed = false
  }

  result.completedAt = new Date().toISOString()
  return result
}

function validateJsonSchema(data: any, schema: any): boolean {
  if (!schema || typeof schema !== 'object') return true
  if (schema.type) {
    const typeMap: Record<string, string> = {
      string: 'string', number: 'number', integer: 'number',
      boolean: 'boolean', array: 'object', object: 'object',
    }
    if (schema.type === 'array' && !Array.isArray(data)) return false
    if (schema.type === 'object' && (typeof data !== 'object' || Array.isArray(data))) return false
    if (['string', 'number', 'integer', 'boolean'].includes(schema.type) && typeof data !== typeMap[schema.type]) return false
  }
  if (schema.required && Array.isArray(schema.required)) {
    for (const field of schema.required) {
      if (data[field] === undefined) return false
    }
  }
  if (schema.properties && typeof data === 'object') {
    for (const [key, propSchema] of Object.entries(schema.properties)) {
      if (data[key] !== undefined) {
        if (!validateJsonSchema(data[key], propSchema)) return false
      }
    }
  }
  if (schema.items && Array.isArray(data)) {
    for (const item of data) {
      if (!validateJsonSchema(item, schema.items)) return false
    }
  }
  return true
}

export async function runTestCases(
  testCases: ApiTestCase[],
  reportName: string = 'API Test Run',
  onProgress?: (current: number) => void
): Promise<{ report: ApiTestReport; results: ApiTestResult[] }> {
  const reportId = crypto.randomUUID()
  const now = new Date().toISOString()

  const report: ApiTestReport = {
    id: reportId,
    name: reportName,
    description: `${testCases.length} 个用例`,
    totalCases: testCases.length,
    passedCases: 0,
    failedCases: 0,
    totalDuration: 0,
    startedAt: now,
    completedAt: null,
    status: 'running',
    createdAt: now,
  }

  await db.saveApiTestReport(report)

  const results: ApiTestResult[] = []
  let totalDuration = 0
  let passedCount = 0

  let completedCount = 0
  // Run with concurrency: process in batches of 5
  const concurrency = 5
  for (let i = 0; i < testCases.length; i += concurrency) {
    const batch = testCases.slice(i, i + concurrency).filter(tc => tc.enabled)
    if (batch.length === 0) continue
    const batchResults = await Promise.all(batch.map(async tc => {
      const result = await runSingleTestCase(tc)
      result.reportId = reportId
      result.caseId = tc.id
      if (result.passed) passedCount++
      if (result.duration) totalDuration += result.duration
      await db.saveApiTestResult(result)
      completedCount++
      onProgress?.(completedCount)
      return result
    }))
    results.push(...batchResults)
  }
  report.passedCases = passedCount
  report.failedCases = results.length - passedCount
  report.totalDuration = totalDuration
  report.completedAt = new Date().toISOString()
  report.status = 'completed'
  await db.saveApiTestReport(report)

  return { report, results }
}

export async function getOrCreateDefaultGroup(): Promise<ApiTestGroup> {
  const groups = await db.loadApiTestGroups()
  if (groups.length > 0) return groups[0]

  const group: ApiTestGroup = {
    id: crypto.randomUUID(),
    name: '默认分组',
    description: '自动生成的测试用例',
    color: '#6366f1',
    sortOrder: 0,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  }
  await db.saveApiTestGroup(group)
  return group
}

export async function exportReport(reportId: string): Promise<void> {
  const report = (await db.loadApiTestReports()).find(r => r.id === reportId)
  if (!report) throw new Error('报告不存在')
  const results = await db.loadApiTestResults(reportId)
  const allCases = await db.loadApiTestCases()
  const allGroups = await db.loadApiTestGroups()

  // Join case details into results
  const resultsWithCase = results.map(r => {
    const tc = allCases.find(c => c.id === r.caseId)
    return { ...r, caseName: tc?.name || r.caseId.slice(0, 8), method: tc?.method || '', path: tc?.path || '', url: tc?.url || '', groupId: tc?.groupId || '' }
  })

  const exportData = {
    version: '1.1',
    exportedAt: new Date().toISOString(),
    report: {
      name: report.name,
      description: report.description,
      totalCases: report.totalCases,
      passedCases: report.passedCases,
      failedCases: report.failedCases,
      totalDuration: report.totalDuration,
      startedAt: report.startedAt,
      completedAt: report.completedAt,
      status: report.status,
      passRate: report.totalCases > 0 ? ((report.passedCases / report.totalCases) * 100).toFixed(1) + '%' : 'N/A',
    },
    results: resultsWithCase.map(r => ({
      passed: r.passed,
      statusCode: r.statusCode,
      duration: r.duration,
      errorMessage: r.errorMessage,
      assertionResults: r.assertionResults,
      caseId: r.caseId,
      caseName: r.caseName,
      method: r.method,
      path: r.path,
      url: r.url,
      groupId: r.groupId,
      responseBody: r.responseBody,
      responseHeaders: r.responseHeaders,
    })),
  }

  const jsonStr = JSON.stringify(exportData, null, 2)
  const htmlContent = generateReportHtml(report, resultsWithCase, allGroups, allCases)

  try {
    const { save } = await import('@tauri-apps/plugin-dialog')
    const { writeTextFile } = await import('@tauri-apps/plugin-fs')
    const path = await save({
      defaultPath: `api-report-${report.name.replace(/[\\/:*?"<>|]/g, '_')}.html`,
      filters: [
        { name: 'HTML 报告', extensions: ['html'] },
        { name: 'JSON 数据', extensions: ['json'] },
      ],
    })
    if (!path) return
    if (path.endsWith('.json')) {
      await writeTextFile(path, jsonStr)
    } else {
      await writeTextFile(path, htmlContent)
    }
  } catch {
    // Fallback: download via Blob
    const blob = new Blob([htmlContent], { type: 'text/html' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `api-report-${report.name.replace(/[\\/:*?"<>|]/g, '_')}.html`
    a.click()
    URL.revokeObjectURL(url)
  }
}

function generateReportHtml(report: ApiTestReport, results: any[], allGroups: ApiTestGroup[], allCases: ApiTestCase[]): string {
  const passRate = report.totalCases > 0 ? ((report.passedCases / report.totalCases) * 100).toFixed(1) : 'N/A'
  const duration = report.totalDuration ? (report.totalDuration / 1000).toFixed(2) + 's' : 'N/A'

  function methodColor(m: string): string {
    const colors: Record<string, string> = { GET: '#2563eb', POST: '#059669', PUT: '#ea580c', DELETE: '#dc2626', PATCH: '#7c3aed' }
    return colors[m] || '#6b7280'
  }

  const rows = results.map((r, i) => {
    const detailId = `detail-${i}`
    const assertionRows = (r.assertionResults || []).map((a: any) =>
      `<tr><td style="padding:4px 8px;font-size:13px;"><span style="color:${a.passed ? '#34c759' : '#ff3b30'}">${a.passed ? '✓' : '✗'}</span></td><td style="padding:4px 8px;font-size:13px;">${escapeHtml(a.expected)}</td><td style="padding:4px 8px;font-size:13px;color:#86868b;">${escapeHtml(a.actual)}</td></tr>`
    ).join('')
    const methodTag = `<span style="display:inline-block;padding:1px 8px;border-radius:6px;font-size:11px;font-weight:600;background:${methodColor(r.method)}15;color:${methodColor(r.method)}">${escapeHtml(r.method)}</span>`

    return `<tr style="cursor:pointer" onclick="toggleDetail('${detailId}')">
      <td style="padding:10px 12px;"><span class="tag ${r.passed ? 'tag-pass' : 'tag-fail'}">${r.passed ? '通过' : '失败'}</span></td>
      <td style="padding:10px 12px;font-size:13px;">${methodTag} <span style="font-family:monospace;font-size:13px;margin-left:4px;">${escapeHtml(r.path || r.url || '')}</span></td>
      <td style="padding:10px 12px;font-size:13px;">${escapeHtml(r.caseName || '')}</td>
      <td style="padding:10px 12px;font-family:monospace;font-size:13px;">${r.statusCode || '-'}</td>
      <td style="padding:10px 12px;font-size:13px;color:#86868b;">${r.duration ? r.duration.toFixed(1) + 'ms' : '-'}</td>
      <td style="padding:10px 12px;">${(r.assertionResults || []).map((a: any) => `<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:${a.passed ? '#34c759' : '#ff3b30'};margin:0 1px;"></span>`).join('')}</td>
    </tr>
    <tr id="${detailId}" style="display:none;">
      <td colspan="6" style="padding:12px 16px;background:#fafafa;border-top:1px solid #f0f0f2;">
        <div style="font-size:13px;line-height:1.6;">
          <div style="margin-bottom:8px;"><strong>URL:</strong> <span style="font-family:monospace;word-break:break-all;">${escapeHtml(r.url || '')}</span></div>
          ${r.errorMessage ? `<div style="margin-bottom:8px;color:#ff3b30;"><strong>错误:</strong> ${escapeHtml(r.errorMessage)}</div>` : ''}
          ${r.responseHeaders ? `<div style="margin-bottom:8px;"><strong>响应头:</strong><pre style="background:#f0f0f2;padding:8px;border-radius:8px;font-size:12px;margin-top:4px;overflow-x:auto;white-space:pre-wrap;">${escapeHtml(JSON.stringify(r.responseHeaders, null, 2))}</pre></div>` : ''}
          ${r.responseBody ? `<div style="margin-bottom:8px;"><strong>响应体:</strong><pre style="background:#f0f0f2;padding:8px;border-radius:8px;font-size:12px;margin-top:4px;overflow-x:auto;white-space:pre-wrap;max-height:300px;">${escapeHtml(formatJson(r.responseBody))}</pre></div>` : ''}
          ${assertionRows ? `<div><strong>断言详情:</strong><table style="width:100%;border-collapse:collapse;margin-top:4px;"><thead><tr><th style="padding:4px 8px;font-size:12px;text-align:left;color:#86868b;width:30px;">结果</th><th style="padding:4px 8px;font-size:12px;text-align:left;color:#86868b;">期望</th><th style="padding:4px 8px;font-size:12px;text-align:left;color:#86868b;">实际</th></tr></thead><tbody>${assertionRows}</tbody></table></div>` : ''}
        </div>
      </td>
    </tr>`
  }).join('')

  function formatJson(str: string): string {
    try { return JSON.stringify(JSON.parse(str), null, 2) } catch { return str }
  }

  return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>API 测试报告 - ${escapeHtml(report.name)}</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f7; color: #1d1d1f; padding: 40px 20px; }
.container { max-width: 1100px; margin: 0 auto; }
h1 { font-size: 28px; font-weight: 700; margin-bottom: 8px; }
.subtitle { color: #86868b; font-size: 14px; margin-bottom: 32px; }
.summary { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 32px; }
.card { background: #fff; border-radius: 16px; padding: 20px; text-align: center; box-shadow: 0 2px 12px rgba(0,0,0,0.06); }
.card-value { font-size: 32px; font-weight: 700; margin-bottom: 4px; }
.card-label { font-size: 13px; color: #86868b; }
.passed { color: #34c759; }
.failed { color: #ff3b30; }
.table { width: 100%; border-collapse: collapse; background: #fff; border-radius: 16px; overflow: hidden; box-shadow: 0 2px 12px rgba(0,0,0,0.06); }
.table th { background: #f5f5f7; padding: 10px 12px; text-align: left; font-size: 12px; font-weight: 600; color: #86868b; white-space: nowrap; }
.table td { border-top: 1px solid #f0f0f2; }
.table tr:hover td { background: #fafbfc; }
.tag { display: inline-block; padding: 2px 10px; border-radius: 12px; font-size: 12px; font-weight: 600; white-space: nowrap; }
.tag-pass { background: #e8f8ee; color: #34c759; }
.tag-fail { background: #ffe8e7; color: #ff3b30; }
@media (max-width: 640px) { .summary { grid-template-columns: repeat(2, 1fr); } .table th:nth-child(3),.table td:nth-child(3) { display:none; } }
</style>
</head>
<body>
<div class="container">
  <h1>${escapeHtml(report.name)}</h1>
  <p class="subtitle">${escapeHtml(report.description)} | 开始: ${new Date(report.startedAt).toLocaleString()} | 完成: ${report.completedAt ? new Date(report.completedAt).toLocaleString() : 'N/A'}</p>

  <div class="summary">
    <div class="card"><div class="card-value">${report.totalCases}</div><div class="card-label">总用例</div></div>
    <div class="card"><div class="card-value passed">${report.passedCases}</div><div class="card-label">通过</div></div>
    <div class="card"><div class="card-value failed">${report.failedCases}</div><div class="card-label">失败</div></div>
    <div class="card"><div class="card-value">${passRate}%</div><div class="card-label">通过率</div></div>
  </div>

  <p style="margin-bottom:16px;font-size:13px;color:#86868b;">总耗时: ${duration} | 点击行展开详情</p>

  <table class="table">
    <thead><tr><th style="width:80px;">状态</th><th>接口</th><th>用例名称</th><th style="width:60px;">状态码</th><th style="width:80px;">耗时</th><th style="width:80px;">断言</th></tr></thead>
    <tbody>
      ${rows}
    </tbody>
  </table>
</div>
<script>
function toggleDetail(id) { var el = document.getElementById(id); if (el) el.style.display = el.style.display === 'none' ? 'table-row' : 'none'; }
</script>
</body>
</html>`
}

function escapeHtml(s: string): string {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')
}
