/**
 * Zmind API
 */
import request from './request'

// Zmind请求超时时间（5分钟）
const ZMIND_TIMEOUT = 5 * 60 * 1000 // 300000毫秒

// ─── 缓存工具 ────────────────────────────────────────────────
// 缓存策略：
//   - 每天第一次打开 PR 对话框时请求一次，当天后续使用缓存
//   - 选择/重新选择项目时强制刷新缓存
//   - 缓存 key 按项目 ID 区分，存在 localStorage

const CACHE_PREFIX = 'zmind_cache_'
const CACHE_TTL_MS = 24 * 60 * 60 * 1000 // 24小时

function getCacheKey(type, projectId) {
  return projectId ? `${CACHE_PREFIX}${type}_${projectId}` : `${CACHE_PREFIX}${type}`
}

function readCache(type, projectId) {
  try {
    const raw = localStorage.getItem(getCacheKey(type, projectId))
    if (!raw) return null
    const { data, ts } = JSON.parse(raw)
    if (Date.now() - ts > CACHE_TTL_MS) {
      localStorage.removeItem(getCacheKey(type, projectId))
      return null
    }
    return data
  } catch {
    return null
  }
}

function writeCache(type, projectId, data) {
  try {
    localStorage.setItem(getCacheKey(type, projectId), JSON.stringify({ data, ts: Date.now() }))
  } catch {
    // localStorage 满了或隐私模式，静默忽略
  }
}

/**
 * 清除指定项目的所有字段缓存（选择/重新选择项目时调用）
 */
export function clearZmindProjectCache(projectId) {
  const types = ['fields', 'required_fields', 'priorities', 'severities', 'phases', 'side_effects']
  types.forEach(type => {
    localStorage.removeItem(getCacheKey(type, projectId))
    localStorage.removeItem(getCacheKey(type, null))
  })
}

/**
 * 检查指定项目的所有 PR 字段缓存是否全部有效（用于跳过 loading）
 */
export function isZmindPRCacheReady(projectId) {
  const keys = [
    getCacheKey('priorities', null),
    getCacheKey('severities', null),
    getCacheKey('fields', projectId),
    getCacheKey('phases', null),
    getCacheKey('side_effects', null),
    getCacheKey('required_fields_t1', projectId)
  ]
  return keys.every(key => {
    try {
      const raw = localStorage.getItem(key)
      if (!raw) return false
      const { ts } = JSON.parse(raw)
      return Date.now() - ts < CACHE_TTL_MS
    } catch {
      return false
    }
  })
}



/**
 * 获取项目的可用字段（带缓存）
 */
export function getProjectFields(projectId, forceRefresh = false) {
  if (!forceRefresh) {
    const cached = readCache('fields', projectId)
    if (cached) return Promise.resolve({ code: 200, message: '获取成功（缓存）', data: cached })
  }
  return request({
    url: `/zmind/projects/${projectId}/fields`,
    method: 'get',
    timeout: ZMIND_TIMEOUT
  }).then(res => {
    if (res?.code === 200) writeCache('fields', projectId, res.data)
    return res
  })
}

/**
 * 获取项目的必填字段（带缓存）
 */
export function getProjectRequiredFields(projectId, trackerId = 1, forceRefresh = false) {
  const cacheKey = `required_fields_t${trackerId}`
  if (!forceRefresh) {
    const cached = readCache(cacheKey, projectId)
    if (cached) return Promise.resolve({ code: 200, message: '获取成功（缓存）', data: cached })
  }
  return request({
    url: `/zmind/projects/${projectId}/required-fields`,
    method: 'get',
    params: { tracker_id: trackerId },
    timeout: ZMIND_TIMEOUT
  }).then(res => {
    if (res?.code === 200) writeCache(cacheKey, projectId, res.data)
    return res
  })
}

/**
 * 获取优先级列表（带缓存，与项目无关）
 */
export function getPriorities(forceRefresh = false) {
  if (!forceRefresh) {
    const cached = readCache('priorities', null)
    if (cached) return Promise.resolve({ code: 200, message: '获取成功（缓存）', data: cached })
  }
  return request({
    url: '/zmind/priorities',
    method: 'get',
    timeout: ZMIND_TIMEOUT
  }).then(res => {
    if (res?.code === 200) writeCache('priorities', null, res.data)
    return res
  })
}

/**
 * 获取严重程度列表（带缓存，与项目无关）
 */
export function getSeverities(forceRefresh = false) {
  if (!forceRefresh) {
    const cached = readCache('severities', null)
    if (cached) return Promise.resolve({ code: 200, message: '获取成功（缓存）', data: cached })
  }
  return request({
    url: '/zmind/severities',
    method: 'get',
    timeout: ZMIND_TIMEOUT
  }).then(res => {
    if (res?.code === 200) writeCache('severities', null, res.data)
    return res
  })
}

/**
 * 获取Phase列表（带缓存，与项目无关）
 */
export function getPhases(forceRefresh = false) {
  if (!forceRefresh) {
    const cached = readCache('phases', null)
    if (cached) return Promise.resolve({ code: 200, message: '获取成功（缓存）', data: cached })
  }
  return request({
    url: '/zmind/phases',
    method: 'get',
    timeout: ZMIND_TIMEOUT
  }).then(res => {
    if (res?.code === 200) writeCache('phases', null, res.data)
    return res
  })
}

/**
 * 获取Side Effect列表（带缓存，与项目无关）
 */
export function getSideEffects(forceRefresh = false) {
  if (!forceRefresh) {
    const cached = readCache('side_effects', null)
    if (cached) return Promise.resolve({ code: 200, message: '获取成功（缓存）', data: cached })
  }
  return request({
    url: '/zmind/side-effects',
    method: 'get',
    timeout: ZMIND_TIMEOUT
  }).then(res => {
    if (res?.code === 200) writeCache('side_effects', null, res.data)
    return res
  })
}

/**
 * 更新用户的Zmind API Key
 */
export function updateUserApiKey(data) {
  return request({
    url: '/zmind/api-key',
    method: 'put',
    data,
    timeout: ZMIND_TIMEOUT
  })
}

/**
 * 获取用户的Zmind API Key
 */
export function getUserApiKey() {
  return request({
    url: '/zmind/api-key',
    method: 'get',
    timeout: ZMIND_TIMEOUT
  })
}

/**
 * 获取Zmind项目列表（带缓存，当天有效）
 */
export function getZmindProjects(signal, forceRefresh = false) {
  if (!forceRefresh) {
    const cached = readCache('projects', null)
    if (cached) return Promise.resolve({ code: 200, message: '获取成功（缓存）', data: cached })
  }
  return request({
    url: '/zmind/projects',
    method: 'get',
    timeout: ZMIND_TIMEOUT,
    signal
  }).then(res => {
    if (res?.code === 200) writeCache('projects', null, res.data)
    return res
  })
}

/**
 * 更新测试计划的Zmind项目
 */
export function updateTestPlanZmindProject(testPlanId, data) {
  return request({
    url: `/zmind/testplans/${testPlanId}/zmind-project`,
    method: 'put',
    data,
    timeout: ZMIND_TIMEOUT
  })
}

/**
 * 获取测试计划的Zmind项目
 */
export function getTestPlanZmindProject(testPlanId, signal) {
  return request({
    url: `/zmind/testplans/${testPlanId}/zmind-project`,
    method: 'get',
    timeout: ZMIND_TIMEOUT,
    signal
  })
}

/**
 * 获取版本列表
 */
export function getVersions() {
  return request({
    url: '/zmind/versions',
    method: 'get',
    timeout: ZMIND_TIMEOUT
  })
}

/**
 * 创建 Zmind Issue
 */
export function createZmindIssue(data) {
  return request({
    url: '/zmind/issues',
    method: 'post',
    data,
    timeout: ZMIND_TIMEOUT
  })
}

/**
 * 获取 Zmind Issue 详情
 */
export function getZmindIssue(issueId) {
  return request({
    url: `/zmind/issues/${issueId}`,
    method: 'get',
    timeout: ZMIND_TIMEOUT
  })
}

/**
 * 上传附件到 Zmind Issue
 */
export function uploadIssueAttachment(issueId, file) {
  const formData = new FormData()
  formData.append('file', file)
  
  return request({
    url: `/zmind/issues/${issueId}/attachments`,
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    },
    timeout: ZMIND_TIMEOUT
  })
}

/**
 * 根据PR号批量查询Zmind Issue
 * @param {string} prNumbers - 逗号分隔的PR号
 */
export function fetchIssuesByPrNumbers(prNumbers) {
  return request({
    url: '/zmind/fetch-issues-by-pr',
    method: 'post',
    data: { pr_numbers: prNumbers },
    timeout: ZMIND_TIMEOUT
  })
}
