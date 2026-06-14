import request from './request'

export const getExecutions = (params) => {
  return request({
    url: '/executions',
    method: 'get',
    params
  })
}

export const createExecution = (data) => {
  return request({
    url: '/executions',
    method: 'post',
    data
  })
}


/**
 * 增强的测试执行接口
 * @param {object} data - 执行数据
 * @param {number} data.test_plan_id - 测试计划ID
 * @param {number} data.test_case_id - 测试用例ID
 * @param {string} data.result - 执行结果 (PASSED/FAILED/BLOCKED/SKIPPED)
 * @param {string} data.remarks - 备注
 * @param {string} data.actual_result - 实际结果
 * @param {string} data.failure_reason - 失败原因
 */
export function createExecutionEnhanced(data) {
  return request({
    url: '/executions/enhanced',
    method: 'post',
    data
  })
}

/**
 * 批量标记执行结果
 * @param {object} data - 批量执行数据
 * @param {number} data.test_plan_id - 测试计划ID
 * @param {array} data.test_case_ids - 测试用例ID列表
 * @param {string} data.result - 执行结果 (PASSED/SKIPPED/BLOCKED)
 */
export function batchExecute(data) {
  return request({
    url: '/executions/batch',
    method: 'post',
    data
  })
}

/**
 * 获取执行记录详情
 * @param {number} executionId - 执行记录ID
 */
export function getExecutionDetail(executionId) {
  return request({
    url: `/executions/${executionId}/detail`,
    method: 'get'
  })
}

/**
 * 获取当前用户在指定测试计划中对指定用例的最新执行备注
 * @param {number} testPlanId - 测试计划ID
 * @param {number} testCaseId - 测试用例ID
 */
export function getLatestExecutionRemark(testPlanId, testCaseId) {
  return request({
    url: '/executions/latest-remark',
    method: 'get',
    params: {
      test_plan_id: testPlanId,
      test_case_id: testCaseId
    }
  })
}

/**
 * 获取指定测试计划中最近一次填写的版本信息（用于自动填充）
 * @param {number} testPlanId - 测试计划ID
 */
export function getLatestVersionInfo(testPlanId) {
  return request({
    url: '/executions/latest-version-info',
    method: 'get',
    params: {
      test_plan_id: testPlanId
    }
  })
}
