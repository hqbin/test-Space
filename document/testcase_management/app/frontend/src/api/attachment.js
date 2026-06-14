/**
 * 附件管理API
 */
import request from './request'

/**
 * 上传附件
 * @param {number} executionId - 执行记录ID
 * @param {File} file - 文件对象
 * @param {string} description - 附件描述
 * @param {function} onProgress - 上传进度回调
 */
export function uploadAttachment(executionId, file, description, onProgress) {
  const formData = new FormData()
  formData.append('file', file)
  if (description) {
    formData.append('description', description)
  }
  
  return request({
    url: `/attachments/executions/${executionId}/upload`,
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    },
    onUploadProgress: (progressEvent) => {
      if (onProgress) {
        const percentCompleted = Math.round(
          (progressEvent.loaded * 100) / progressEvent.total
        )
        onProgress(percentCompleted)
      }
    }
  })
}

/**
 * 获取附件列表
 * @param {number} executionId - 执行记录ID
 */
export function getAttachments(executionId) {
  return request({
    url: `/attachments/executions/${executionId}`,
    method: 'get'
  })
}

/**
 * 下载附件
 * @param {number} attachmentId - 附件ID
 */
export function downloadAttachment(attachmentId) {
  return request({
    url: `/attachments/${attachmentId}/download`,
    method: 'get',
    responseType: 'blob'
  })
}

/**
 * 删除附件
 * @param {number} attachmentId - 附件ID
 */
export function deleteAttachment(attachmentId) {
  return request({
    url: `/attachments/${attachmentId}`,
    method: 'delete'
  })
}
