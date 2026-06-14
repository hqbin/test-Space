import request from './request'

/**
 * 获取工作台统计数据
 * @param {Object} params - 查询参数
 * @param {string} params.start_date - 开始日期
 * @param {string} params.end_date - 结束日期
 */
export function getDashboardStats(params) {
  return request({
    url: '/dashboard/stats',
    method: 'get',
    params
  })
}

// ========== Dashboard V2 APIs ==========

/** 卡片1: 用例库信息卡片 */
export function getProjectCards(params) {
  return request({ url: '/dashboard/v2/project-cards', method: 'get', params })
}

/** 卡片2: 用例关联PR数 */
export function getPrList(params) {
  return request({ url: '/dashboard/v2/pr-list', method: 'get', params })
}

/** 卡片3: 评审计划卡片 */
export function getReviewPlans(params) {
  return request({ url: '/dashboard/v2/review-plans', method: 'get', params })
}

/** 卡片4: 测试计划卡片 */
export function getTestPlans(params) {
  return request({ url: '/dashboard/v2/test-plans', method: 'get', params })
}

/** 卡片5: 用户任务统计 */
export function getUserTasks(params) {
  return request({ url: '/dashboard/v2/user-tasks', method: 'get', params })
}
