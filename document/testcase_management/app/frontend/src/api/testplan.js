import request from './request'

export const getTestPlans = (params) => {
  return request({
    url: '/testplans',
    method: 'get',
    params
  })
}

export const createTestPlan = (data) => {
  return request({
    url: '/testplans',
    method: 'post',
    data
  })
}

export const getTestPlanDetail = (id, params = {}) => {
  return request({
    url: `/testplans/${id}`,
    method: 'get',
    params
  })
}

export const updateTestPlan = (id, data) => {
  return request({
    url: `/testplans/${id}`,
    method: 'put',
    data
  })
}

export const deleteTestPlan = (id) => {
  return request({
    url: `/testplans/${id}`,
    method: 'delete'
  })
}

export const startTestPlan = (id, data) => {
  return request({
    url: `/testplans/${id}/start`,
    method: 'post',
    data
  })
}

export const addTestCasesToPlan = (planId, data) => {
  return request({
    url: `/testplans/${planId}/testcases`,
    method: 'post',
    data
  })
}

export const removeTestCaseFromPlan = (planId, testcaseId) => {
  return request({
    url: `/testplans/${planId}/testcases/${testcaseId}`,
    method: 'delete'
  })
}

// 批量从测试计划中取消关联用例（单次事务）
export const batchRemoveTestCasesFromPlan = (planId, testcaseIds) => {
  return request({
    url: `/testplans/${planId}/testcases/batch-remove`,
    method: 'post',
    data: { testcase_ids: testcaseIds }
  })
}

export const submitTestPlanForReview = (planId, data) => {
  return request({
    url: `/testplans/${planId}/submit-review`,
    method: 'post',
    data,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

export const withdrawTestPlanReview = (planId) => {
  return request({
    url: `/testplans/${planId}/withdraw-review`,
    method: 'post'
  })
}

export const previewTestPlanReport = (planId) => {
  return request({
    url: `/testplans/${planId}/preview-report`,
    method: 'get'
  })
}

export const previewTestPlanReportWithData = (planId, data) => {
  return request({
    url: `/testplans/${planId}/preview-report`,
    method: 'post',
    data,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}
