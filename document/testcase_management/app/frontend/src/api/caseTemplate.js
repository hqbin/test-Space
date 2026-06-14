import request from './request'

/**
 * 获取项目组下的所有模板
 */
export function getTemplates(teamId) {
  return request({
    url: `/teams/${teamId}/templates`,
    method: 'get'
  })
}

/**
 * 上传并创建模板
 */
export function createTemplate(teamId, file, name = null) {
  const formData = new FormData()
  formData.append('file', file)
  if (name) {
    formData.append('name', name)
  }
  return request({
    url: `/teams/${teamId}/templates`,
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

/**
 * 获取模板详情
 */
export function getTemplate(templateId) {
  return request({
    url: `/templates/${templateId}`,
    method: 'get'
  })
}

/**
 * 更新模板
 */
export function updateTemplate(templateId, data) {
  return request({
    url: `/templates/${templateId}`,
    method: 'put',
    data
  })
}

/**
 * 删除模板
 */
export function deleteTemplate(templateId) {
  return request({
    url: `/templates/${templateId}`,
    method: 'delete'
  })
}

/**
 * 设为默认模板
 */
export function setDefaultTemplate(templateId) {
  return request({
    url: `/templates/${templateId}/default`,
    method: 'put'
  })
}

/**
 * 下载模板文件
 */
export function downloadTemplate(templateId) {
  return request({
    url: `/templates/${templateId}/download`,
    method: 'get',
    responseType: 'blob'
  })
}

/**
 * 获取项目组的默认模板
 */
export function getDefaultTemplate(teamId) {
  return request({
    url: `/teams/${teamId}/templates/default`,
    method: 'get'
  })
}
