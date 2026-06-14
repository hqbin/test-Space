import request from './request'

// 获取项目成员列表
export function getProjectMembers(projectId) {
  return request({
    url: `/review-plans/projects/${projectId}/members`,
    method: 'get'
  })
}

// 创建评审计划
export function createReviewPlan(data) {
  return request({
    url: '/review-plans',
    method: 'post',
    data
  })
}

// 获取评审计划列表
export function getReviewPlanList(params) {
  return request({
    url: '/review-plans',
    method: 'get',
    params
  })
}

// 获取评审计划详情
export function getReviewPlanDetail(id) {
  return request({
    url: `/review-plans/${id}`,
    method: 'get'
  })
}

// 更新评审计划
export function updateReviewPlan(id, data) {
  return request({
    url: `/review-plans/${id}`,
    method: 'put',
    data
  })
}

// 删除评审计划
export function deleteReviewPlan(id) {
  return request({
    url: `/review-plans/${id}`,
    method: 'delete'
  })
}

// 添加用例到评审计划
export function addTestCasesToPlan(planId, data) {
  return request({
    url: `/review-plans/${planId}/testcases`,
    method: 'post',
    data
  })
}

// 获取评审计划的用例列表
export function getPlanTestCases(planId, params) {
  return request({
    url: `/review-plans/${planId}/testcases`,
    method: 'get',
    params
  })
}

// 从评审计划中移除用例
export function removeTestCaseFromPlan(planId, testcaseId) {
  return request({
    url: `/review-plans/${planId}/testcases/${testcaseId}`,
    method: 'delete'
  })
}

// 评审单个用例
export function reviewTestCase(planId, testcaseId, data) {
  return request({
    url: `/review-plans/${planId}/testcases/${testcaseId}/review`,
    method: 'post',
    data
  })
}

// 批量评审用例
export function batchReviewTestCases(planId, data) {
  return request({
    url: `/review-plans/${planId}/testcases/batch-review`,
    method: 'post',
    data
  })
}

// 提交评审计划
export function submitReviewPlan(planId) {
  return request({
    url: `/review-plans/${planId}/submit`,
    method: 'post'
  })
}

// 获取用例评审详情（用于详情页评审）
export function getTestCaseReviewDetail(planId, testcaseId) {
  return request({
    url: `/review-plans/${planId}/testcases/${testcaseId}/detail`,
    method: 'get'
  })
}
