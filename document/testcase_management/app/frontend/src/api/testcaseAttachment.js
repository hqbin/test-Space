import request from './request'

/**
 * 上传测试用例附件
 */
export function uploadAttachment(testCaseId, formData) {
  return request({
    url: `/testcase-attachments/${testCaseId}/attachments`,
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

/**
 * 获取测试用例附件列表
 */
export function getAttachments(testCaseId) {
  return request({
    url: `/testcase-attachments/${testCaseId}/attachments`,
    method: 'get'
  })
}

/**
 * 下载附件
 */
export function downloadAttachment(attachmentId) {
  return request({
    url: `/testcase-attachments/attachments/${attachmentId}/download`,
    method: 'get',
    responseType: 'blob'
  })
}

/**
 * 获取附件预览URL（内联显示）
 */
export function getAttachmentPreviewUrl(attachmentId) {
  const token = localStorage.getItem('token')
  return `/api/testcase-attachments/attachments/${attachmentId}/preview?token=${token}`
}

/**
 * 删除附件
 */
export function deleteAttachment(attachmentId) {
  return request({
    url: `/testcase-attachments/attachments/${attachmentId}`,
    method: 'delete'
  })
}
