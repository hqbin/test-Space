/**
 * 进度统计API
 */
import request from './request'

/**
 * 获取测试计划进度统计
 * @param {number} testplanId - 测试计划ID
 */
export function getProgressStatistics(testplanId) {
  return request({
    url: `/progress/testplans/${testplanId}/statistics`,
    method: 'get'
  })
}

/**
 * 保存执行进度
 * @param {object} data - 进度数据
 * @param {number} data.testplan_id - 测试计划ID
 * @param {number} data.current_testcase_id - 当前测试用例ID
 * @param {number} data.current_index - 当前索引
 * @param {array} data.sort_order - 自定义排序
 */
export function saveExecutionProgress(data) {
  return request({
    url: '/progress/execution-progress',
    method: 'post',
    data
  })
}

/**
 * 获取执行进度
 * @param {number} testplanId - 测试计划ID
 */
export function getExecutionProgress(testplanId) {
  return request({
    url: `/progress/testplans/${testplanId}/execution-progress`,
    method: 'get'
  })
}

/**
 * 获取执行历史
 * @param {number} testplanId - 测试计划ID
 * @param {number} testcaseId - 测试用例ID
 * @param {number} limit - 返回数量限制
 */
export function getExecutionHistory(testplanId, testcaseId, limit = 10) {
  return request({
    url: `/progress/testplans/${testplanId}/testcases/${testcaseId}/history`,
    method: 'get',
    params: { limit }
  })
}
