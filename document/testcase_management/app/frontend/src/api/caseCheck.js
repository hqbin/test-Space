import request from './request'

/**
 * 解析Excel文件的所有Sheet (V1.3新增)
 */
export function parseSheets(projectId, file) {
  const formData = new FormData()
  formData.append('file', file)
  return request({
    url: `/projects/${projectId}/case/check/parse-sheets`,
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

/**
 * 开始校对任务 (V1.3扩展：支持file_id、sheet_name、header_row)
 */
export function startCheck(projectId, templateId, file, options = {}) {
  const formData = new FormData()
  formData.append('template_id', templateId)
  
  // V1.3: 支持从缓存获取文件或直接上传
  if (options.fileId) {
    formData.append('file_id', options.fileId)
  } else if (file) {
    formData.append('file', file)
  }
  
  // V1.3: 支持指定Sheet和表头行
  if (options.sheetName) {
    formData.append('sheet_name', options.sheetName)
  }
  if (options.headerRow) {
    formData.append('header_row', options.headerRow)
  }
  
  return request({
    url: `/projects/${projectId}/case/check`,
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

/**
 * 获取校对结果
 */
export function getCheckResult(taskId) {
  return request({
    url: `/case/check/${taskId}`,
    method: 'get'
  })
}

/**
 * 确认字段映射
 */
export function confirmMapping(taskId, mapping) {
  return request({
    url: `/case/check/${taskId}/mapping`,
    method: 'post',
    data: { mapping }
  })
}

/**
 * 更新单元格
 */
export function updateCell(taskId, rowIndex, field, value) {
  return request({
    url: `/case/check/${taskId}/update`,
    method: 'post',
    data: {
      row_index: rowIndex,
      field,
      value
    }
  })
}

/**
 * 应用修复
 */
export function applyFix(taskId, rowIndices, fixType = null) {
  return request({
    url: `/case/check/${taskId}/fix`,
    method: 'post',
    data: {
      row_indices: rowIndices,
      fix_type: fixType
    }
  })
}

/**
 * 重置到原始数据
 */
export function resetToOriginal(taskId) {
  return request({
    url: `/case/check/${taskId}/reset`,
    method: 'post'
  })
}

/**
 * 导出修正后的Excel
 */
export function exportResult(taskId) {
  return request({
    url: `/case/check/${taskId}/export`,
    method: 'get',
    responseType: 'blob'
  })
}
