import request from './request'

/** 总览统计 */
export function getAnalyticsOverview(params) {
  return request({ url: '/analytics/overview', method: 'get', params })
}

/** 用例统计 */
export function getTestcaseStats(params) {
  return request({ url: '/analytics/testcase-stats', method: 'get', params })
}

/** 执行统计 */
export function getExecutionStats(params) {
  return request({ url: '/analytics/execution-stats', method: 'get', params })
}

/** 趋势分析 */
export function getTrendData(params) {
  return request({ url: '/analytics/trend', method: 'get', params })
}

/** 测试计划统计 */
export function getPlanStats(params) {
  return request({ url: '/analytics/plan-stats', method: 'get', params })
}

/** 筛选选项 */
export function getFilterOptions(params) {
  return request({ url: '/analytics/filters', method: 'get', params })
}

/** 获取测试计划列表（用于下拉选择） */
export function getTestPlansForAnalytics(params) {
  return request({ url: '/analytics/testplans', method: 'get', params: { team_id: params?.team_id, page: params?.page || 1, size: params?.size || 100, search: params?.search } })
}


/** 缺陷密度 */
export function getDefectDensity(params) {
  return request({ url: '/analytics/defect-density', method: 'get', params })
}

/** 测试覆盖率 */
export function getTestCoverage(params) {
  return request({ url: '/analytics/coverage', method: 'get', params })
}

/** 执行效率 */
export function getExecutionVelocity(params) {
  return request({ url: '/analytics/velocity', method: 'get', params })
}

/** 用例老化 */
export function getCaseAge(params) {
  return request({ url: '/analytics/case-age', method: 'get', params })
}

/** 评审统计 */
export function getReviewStats(params) {
  return request({ url: '/analytics/review-stats', method: 'get', params })
}

/** 计划按时完成率 */
export function getPlanOntime(params) {
  return request({ url: '/analytics/plan-ontime', method: 'get', params })
}

/** 执行热力图 */
export function getExecutionHeatmap(params) {
  return request({ url: '/analytics/heatmap', method: 'get', params })
}


/** 用户列表 */
export function getAnalyticsUserList(params) {
  return request({ url: '/analytics/user-list', method: 'get', params })
}

/** 个人综合分析 */
export function getPersonalAnalytics(params) {
  return request({ url: '/analytics/personal', method: 'get', params })
}

/** PR数量统计 */
export function getPrCountByUser(params) {
  return request({ url: '/analytics/pr-count', method: 'get', params })
}

/** PR 关联查询 - 上传 Excel，检查 PR 在平台中的关联情况 */
export function checkPrInPlatform(formData) {
  return request({ url: '/analytics/pr-check', method: 'post', data: formData, timeout: 180000, skipErrorToast: true })
}
