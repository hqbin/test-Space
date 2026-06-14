import request from './request'
import { ElLoading } from 'element-plus'

export const getReports = (params) => {
  return request({
    url: '/reports',
    method: 'get',
    params
  })
}

export const generateReport = (data) => {
  return request({
    url: '/reports/generate',
    method: 'post',
    data,
    timeout: 300000
  })
}

export const exportReportPdf = (id, reportName) => {
  const loading = ElLoading.service({
    lock: true,
    text: '正在生成PDF文件，请耐心等待...',
    background: 'rgba(0, 0, 0, 0.5)'
  })
  return request({
    url: `/reports/${id}/export/pdf`,
    method: 'get',
    responseType: 'blob',
    timeout: 300000
  }).then(response => {
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    let filename = 'report.pdf'
    const disposition = response.headers?.['content-disposition']
    if (disposition) {
      const match = disposition.match(/filename\*=UTF-8''(.+)/)
      if (match) filename = decodeURIComponent(match[1])
    } else if (reportName) {
      filename = `${reportName}.pdf`
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

export const exportReportExcel = (id, reportName) => {
  const loading = ElLoading.service({
    lock: true,
    text: '正在生成Excel文件，请耐心等待...',
    background: 'rgba(0, 0, 0, 0.5)'
  })
  return request({
    url: `/reports/${id}/export/excel`,
    method: 'get',
    responseType: 'blob',
    timeout: 300000
  }).then(response => {
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    let filename = 'report.xlsx'
    const disposition = response.headers?.['content-disposition']
    if (disposition) {
      const match = disposition.match(/filename\*=UTF-8''(.+)/)
      if (match) filename = decodeURIComponent(match[1])
    } else if (reportName) {
      filename = `${reportName}.xlsx`
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

export const getReportDetail = (reportId) => {
  return request({
    url: `/reports/${reportId}`,
    method: 'get'
  })
}

export const approveReport = (reportId) => {
  return request({
    url: `/reports/${reportId}/approve`,
    method: 'post'
  })
}

export const rejectReport = (reportId, data) => {
  return request({
    url: `/reports/${reportId}/reject`,
    method: 'post',
    data
  })
}

// Mobile API aliases
export const getReportList = (params = {}) => {
  return request({
    url: '/reports',
    method: 'get',
    params
  })
}

export const archiveReport = (reportId) => {
  return request({
    url: `/reports/${reportId}/archive`,
    method: 'post'
  })
}

export const unarchiveReport = (reportId) => {
  return request({
    url: `/reports/${reportId}/unarchive`,
    method: 'post'
  })
}

export const withdrawReport = (reportId) => {
  return request({
    url: `/reports/${reportId}/withdraw`,
    method: 'post'
  })
}

// ==================== 异步导出（后台生成，避免大文件超时504） ====================

let _exportTaskId = null

export const startAsyncExport = async (reportId, format) => {
  const res = await request({
    url: `/reports/${reportId}/export/async/${format}`,
    method: 'post'
  })
  if (res.code === 200) {
    _exportTaskId = res.data.task_id
    return res.data.task_id
  }
  throw new Error(res.message || '启动导出失败')
}

export const pollExportStatus = async (taskId) => {
  const res = await request({
    url: `/reports/exports/tasks/${taskId}`,
    method: 'get'
  })
  if (res.code === 200) {
    return res.data
  }
  throw new Error(res.message || '查询导出状态失败')
}

export const downloadAsyncExport = async (taskId, reportName) => {
  try {
    const response = await fetch(`/api/reports/exports/tasks/${taskId}/download`)
    if (!response.ok) throw new Error('下载失败')
    const blob = await response.blob()
    const disposition = response.headers.get('content-disposition')
    let filename = 'report'
    if (disposition) {
      const match = disposition.match(/filename\*=UTF-8''(.+)/)
      if (match) filename = decodeURIComponent(match[1])
    } else if (reportName) {
      filename = reportName
    }
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', filename)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  } catch (e) {
    console.error('下载导出文件失败', e)
    throw e
  }
}

export const getPendingExportTaskId = () => _exportTaskId
