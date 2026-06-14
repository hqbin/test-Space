import request from './request'
import { ElLoading } from 'element-plus'

export const getTestSuites = (params) => {
  return request({ url: '/test-suites', method: 'get', params })
}

export const createTestSuite = (data) => {
  return request({ url: '/test-suites', method: 'post', data })
}

export const getTestSuiteDetail = (id) => {
  return request({ url: `/test-suites/${id}`, method: 'get' })
}

export const updateTestSuite = (id, data) => {
  return request({ url: `/test-suites/${id}`, method: 'put', data })
}

export const deleteTestSuite = (id) => {
  return request({ url: `/test-suites/${id}`, method: 'delete' })
}

export const unlinkTestSuiteCase = (suiteId, caseId) => {
  return request({ url: `/test-suites/${suiteId}/cases/${caseId}`, method: 'delete' })
}

export const exportSuiteExcel = (suiteId, suiteName) => {
  const loading = ElLoading.service({
    lock: true,
    text: '正在导出套件，请耐心等待...',
    background: 'rgba(0, 0, 0, 0.5)'
  })
  return request({
    url: `/test-suites/${suiteId}/export/excel`,
    method: 'get',
    responseType: 'blob',
    timeout: 300000  // 大文件导出给5分钟超时
  }).then(response => {
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    let filename = suiteName ? `${suiteName}.xlsx` : 'suite.xlsx'
    const disposition = response.headers?.['content-disposition']
    if (!suiteName && disposition) {
      const match = disposition.match(/filename\*=UTF-8''(.+)/)
      if (match) filename = decodeURIComponent(match[1])
    }
    link.setAttribute('download', filename)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  }).finally(() => {
    loading.close()
  })
}
