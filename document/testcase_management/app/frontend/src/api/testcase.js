import request from './request'
import { ElLoading } from 'element-plus'

export const getTestCases = (params) => {
  return request({
    url: '/testcases',
    method: 'get',
    params
  })
}

// 获取当前筛选条件下所有用例的ID列表（用于全选，不受分页限制）
export const getAllTestCaseIds = (params) => {
  return request({
    url: '/testcases/all-ids',
    method: 'get',
    params,
    timeout: 30000  // 全选 ID 查询给 30 秒，只查 id 列，通常很快
  })
}

export const getTestCaseDetail = (id) => {
  return request({
    url: `/testcases/${id}`,
    method: 'get'
  })
}

export const createTestCase = (data) => {
  return request({
    url: '/testcases',
    method: 'post',
    data
  })
}

export const updateTestCase = (id, data) => {
  return request({
    url: `/testcases/${id}`,
    method: 'put',
    data
  })
}

export const deleteTestCase = (id) => {
  return request({
    url: `/testcases/${id}`,
    method: 'delete'
  })
}

export const batchDeleteTestCases = (ids) => {
  return request({
    url: '/testcases/batch-delete',
    method: 'post',
    data: { ids }
  })
}

export const getDeleteProgress = (taskId) => {
  return request({
    url: `/testcases/batch-delete/${taskId}/progress`,
    method: 'get'
  })
}

export const getFilterOptions = (params) => {
  return request({
    url: '/testcases/filter-options',
    method: 'get',
    params
  })
}


export const exportTestCases = (projectId, params = {}) => {
  const loading = ElLoading.service({
    lock: true,
    text: '正在导出用例，请耐心等待...',
    background: 'rgba(0, 0, 0, 0.5)'
  })
  return request({
    url: '/testcases/export',
    method: 'get',
    params: { project_id: projectId, ...params },
    responseType: 'blob',
    timeout: 300000  // 大文件导出给5分钟超时
  }).then(response => {
    let filename = 'testcases.xlsx'
    const contentDisposition = response.headers['content-disposition']
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename\*=UTF-8''(.+)/)
      if (filenameMatch && filenameMatch[1]) {
        filename = decodeURIComponent(filenameMatch[1])
      } else {
        const simpleMatch = contentDisposition.match(/filename="?(.+?)"?$/)
        if (simpleMatch && simpleMatch[1]) {
          filename = simpleMatch[1]
        }
      }
    }
    
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', filename)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  }).finally(() => {
    loading.close()
  })
}

// 批量移动测试用例到指定用例库的模块（跨用例库移动）
export const batchMoveTestCases = (data) => {
  return request({
    url: '/testcases/batch-move',
    method: 'post',
    data,
    timeout: 120000
  })
}

// 批量创建测试用例
export const batchCreateTestCases = (data) => {
  return request({
    url: '/testcases/batch-create',
    method: 'post',
    data,
    timeout: 120000
  })
}

// 批量更新测试用例
export const batchUpdateTestCases = (data) => {
  return request({
    url: '/testcases/batch-update',
    method: 'post',
    data,
    timeout: 120000  // 批量操作给120秒超时
  })
}

// 按ID导出测试用例
export const exportTestCasesByIds = (projectId, ids) => {
  const loading = ElLoading.service({
    lock: true,
    text: `正在导出 ${ids.length} 条用例，请耐心等待...`,
    background: 'rgba(0, 0, 0, 0.5)'
  })
  return request({
    url: '/testcases/export-by-ids',
    method: 'post',
    data: { project_id: projectId, ids },
    responseType: 'blob',
    timeout: 300000  // 大文件导出给5分钟超时
  }).then(response => {
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', 'testcases_selected.xlsx')
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  }).finally(() => {
    loading.close()
  })
}

// Zmind PR关联相关API
export const linkZmindIssue = (testcaseId, data) => {
  return request({
    url: `/testcases/${testcaseId}/zmind-links`,
    method: 'post',
    data
  })
}

export const getZmindLinks = (testcaseId) => {
  return request({
    url: `/testcases/${testcaseId}/zmind-links`,
    method: 'get'
  })
}

export const unlinkZmindIssue = (testcaseId, linkId) => {
  return request({
    url: `/testcases/${testcaseId}/zmind-links/${linkId}`,
    method: 'delete'
  })
}

export const updateZmindLink = (testcaseId, linkId, data) => {
  return request({
    url: `/testcases/${testcaseId}/zmind-links/${linkId}`,
    method: 'put',
    data
  })
}

export const getZmindLinkStatistics = (projectId) => {
  return request({
    url: '/testcases/statistics/zmind-links',
    method: 'get',
    params: { project_id: projectId }
  })
}

// 获取测试用例历史记录
export const getTestCaseHistory = (id) => {
  return request({
    url: `/testcases/${id}/history`,
    method: 'get'
  })
}

// 获取测试用例执行历史
export const getTestCaseExecutionHistory = (id) => {
  return request({
    url: `/testcases/${id}/execution-history`,
    method: 'get'
  })
}


// 拖拽调整用例顺序
export const reorderTestCase = (data) => {
  return request({
    url: '/testcases/reorder',
    method: 'post',
    data
  })
}


// 批量刷新所有PR状态
export const refreshAllPRStatus = (projectId) => {
  return request({
    url: '/testcases/refresh-all-pr-status',
    method: 'post',
    params: { project_id: projectId },
    timeout: 5 * 60 * 1000 // 5分钟超时，Zmind API响应慢
  })
}

// 刷新单个测试用例的PR状态
export const refreshTestcasePRStatus = (testcaseId) => {
  return request({
    url: `/testcases/${testcaseId}/refresh-pr-status`,
    method: 'post',
    timeout: 5 * 60 * 1000
  })
}

// 获取测试用例统计信息
export const getTestCaseStatistics = (params) => {
  return request({
    url: '/testcases/statistics',
    method: 'get',
    params
  })
}

// 提交用例问题反馈
export const submitTestCaseFeedback = (testcaseId, data) => {
  return request({
    url: `/testcases/${testcaseId}/feedback`,
    method: 'post',
    data
  })
}

// 清除用例反馈信息
export const clearTestCaseFeedback = (testcaseId) => {
  return request({
    url: `/testcases/${testcaseId}/feedback`,
    method: 'delete'
  })
}
