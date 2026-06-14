import request from './request'

const BASE = '/aivoice'

// ===== 发版说明 =====
export const getReleaseNotes = (params) => request.get(`${BASE}/release-notes`, { params })
export const getReleaseNote = (id) => request.get(`${BASE}/release-notes/${id}`)
export const createReleaseNote = (data) => request.post(`${BASE}/release-notes`, data)
export const updateReleaseNote = (id, data) => request.put(`${BASE}/release-notes/${id}`, data)
export const deleteReleaseNote = (id) => request.delete(`${BASE}/release-notes/${id}`)
export const getParentVersions = (params) => request.get(`${BASE}/release-notes/parent-versions`, { params })
export const getEligibleForQa = (params) => request.get(`${BASE}/release-notes/eligible-for-qa`, { params })
export const getReleaseNoteStats = (params) => request.get(`${BASE}/release-notes/stats/summary`, { params })
export const getImpactTags = (params) => request.get(`${BASE}/release-notes/impact-tags`, { params })
export const updateImpactTags = (tags, params) => request.put(`${BASE}/release-notes/impact-tags`, tags, { params })

// ===== 版本记录 =====
export const getVersionRecords = (params) => request.get(`${BASE}/version-records`, { params })
export const getVersionRecord = (id) => request.get(`${BASE}/version-records/${id}`)
export const createVersionRecord = (data) => request.post(`${BASE}/version-records`, data)
export const updateVersionRecord = (id, data) => request.put(`${BASE}/version-records/${id}`, data)
export const deleteVersionRecord = (id) => request.delete(`${BASE}/version-records/${id}`)
export const transitionVersionStatus = (id, targetStatus) => request.post(`${BASE}/version-records/${id}/transition`, null, { params: { targetStatus } })
export const getStatusFlowOptions = () => request.get(`${BASE}/version-records/status-flow/options`)
export const getReleaseDecisions = () => request.get(`${BASE}/version-records/release-decisions/options`)

// ===== 问题跟踪 =====
export const getCustomerProblems = (params) => request.get(`${BASE}/customer-problems`, { params })
export const getCustomerProblem = (id) => request.get(`${BASE}/customer-problems/${id}`)
export const createCustomerProblem = (data) => request.post(`${BASE}/customer-problems`, data)
export const updateCustomerProblem = (id, data) => request.put(`${BASE}/customer-problems/${id}`, data)
export const deleteCustomerProblem = (id) => request.delete(`${BASE}/customer-problems/${id}`)

// ===== 版本问题 =====
export const getVersionIssues = (params) => request.get(`${BASE}/version-issues`, { params })
export const getVersionIssue = (id) => request.get(`${BASE}/version-issues/${id}`)
export const createVersionIssue = (data) => request.post(`${BASE}/version-issues`, data)
export const updateVersionIssue = (id, data) => request.put(`${BASE}/version-issues/${id}`, data)
export const deleteVersionIssue = (id) => request.delete(`${BASE}/version-issues/${id}`)

// ===== 知识库 =====
export const getAiVoiceTestCases = (params) => request.get(`${BASE}/knowledge-base`, { params })
export const getAiVoiceTestCase = (id) => request.get(`${BASE}/knowledge-base/${id}`)
export const createAiVoiceTestCase = (data) => request.post(`${BASE}/knowledge-base`, data)
export const updateAiVoiceTestCase = (id, data) => request.put(`${BASE}/knowledge-base/${id}`, data)
export const deleteAiVoiceTestCase = (id) => request.delete(`${BASE}/knowledge-base/${id}`)

// ===== APK管理 =====
export const uploadApk = (file) => {
  const formData = new FormData()
  formData.append('file', file)
  return request.post(`${BASE}/apk/upload`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}
export const listApkFiles = () => request.get(`${BASE}/apk/list`)
export const deleteApk = (fileName) => request.delete(`${BASE}/apk/${encodeURIComponent(fileName)}`)

// ===== 工作区管理 =====
export const getWorkspaces = () => request.get(`${BASE}/workspaces`)
export const createWorkspace = (data) => request.post(`${BASE}/workspaces`, data)
export const updateWorkspace = (id, data) => request.put(`${BASE}/workspaces/${id}`, data)
export const deleteWorkspace = (id) => request.delete(`${BASE}/workspaces/${id}`)
export const createGroup = (workspaceId, data) => request.post(`${BASE}/workspaces/${workspaceId}/groups`, data)
export const updateGroup = (groupId, data) => request.put(`${BASE}/workspaces/groups/${groupId}`, data)
export const deleteGroup = (groupId) => request.delete(`${BASE}/workspaces/groups/${groupId}`)

// ===== 设置 =====
export const getAiVoiceSetting = (key) => request.get(`${BASE}/settings/${key}`)
export const updateAiVoiceSetting = (key, value) => request.put(`${BASE}/settings/${key}`, { value })

// ===== AI用例推荐 =====
export const analyzeAndRecommend = (data) => request.post(`${BASE}/ai-recommend/analyze`, data)
export const getAnalyzeProgress = (historyId) => request.get(`${BASE}/ai-recommend/progress/${historyId}`)
export const getRunningTask = () => request.get(`${BASE}/ai-recommend/running-task`)
export const abortTask = (historyId) => request.post(`${BASE}/ai-recommend/abort/${historyId}`)
export const fetchPrInfo = (prNumbers) => request.post(`${BASE}/ai-recommend/fetch-pr-info`, { prNumbers })
export const getLatestAnalysis = () => request.get(`${BASE}/ai-recommend/latest`)
export const getRecommendHistory = (params) => request.get(`${BASE}/ai-recommend/history`, { params })
export const getRecommendHistoryDetail = (id) => request.get(`${BASE}/ai-recommend/history/${id}`)
export const deleteRecommendHistory = (id) => request.delete(`${BASE}/ai-recommend/history/${id}`)
export const updateRecommendHistorySuite = (historyId, data) => request.put(`${BASE}/ai-recommend/history/${historyId}/suite`, data)
export const generateSupplementCases = (data) => request.post(`${BASE}/ai-recommend/generate-supplement`, data)
export const getSupplementProgress = (historyId) => request.get(`${BASE}/ai-recommend/supplement-progress/${historyId}`)
export const exportRecommendExcel = (historyId) => {
  return request({
    url: `${BASE}/ai-recommend/export-excel`,
    method: 'post',
    data: { historyId },
    responseType: 'blob',
    timeout: 30000
  })
}

// ===== 任务队列 =====
export const getQueue = () => request.get(`${BASE}/ai-recommend/queue`)
export const reorderQueue = (historyIds) => request.post(`${BASE}/ai-recommend/queue/reorder`, { historyIds })
