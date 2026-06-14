/**
 * 附件管理组合式函数
 */
import { ref } from 'vue'
import * as api from '@/api/attachment'
import { ElMessage } from 'element-plus'

export function useAttachment(executionId) {
  const attachments = ref([])
  const loading = ref(false)
  const uploading = ref(false)
  const uploadProgress = ref(0)
  
  /**
   * 加载附件列表
   */
  const loadAttachments = async () => {
    loading.value = true
    try {
      const res = await api.getAttachments(executionId)
      attachments.value = res.data || []
    } catch (error) {
      ElMessage.error('加载附件失败')
      console.error('加载附件失败:', error)
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 上传附件
   */
  const uploadAttachment = async (file, description) => {
    uploading.value = true
    uploadProgress.value = 0
    
    try {
      await api.uploadAttachment(
        executionId,
        file,
        description,
        (progress) => {
          uploadProgress.value = progress
        }
      )
      
      ElMessage.success('上传成功')
      await loadAttachments()
    } catch (error) {
      ElMessage.error('上传失败')
      console.error('上传失败:', error)
    } finally {
      uploading.value = false
      uploadProgress.value = 0
    }
  }
  
  /**
   * 下载附件
   */
  const downloadAttachment = async (attachmentId, fileName) => {
    try {
      const response = await api.downloadAttachment(attachmentId)
      
      // api.downloadAttachment 使用 responseType: 'blob'，
      // axios 拦截器直接返回完整 response 对象，文件数据在 response.data
      const blob = response.data instanceof Blob
        ? response.data
        : new Blob([response.data], { type: 'application/octet-stream' })
      
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = fileName
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      
      ElMessage.success('下载成功')
    } catch (error) {
      ElMessage.error('下载失败')
      console.error('下载失败:', error)
    }
  }
  
  /**
   * 删除附件
   */
  const deleteAttachment = async (attachmentId) => {
    try {
      await api.deleteAttachment(attachmentId)
      ElMessage.success('删除成功')
      await loadAttachments()
    } catch (error) {
      ElMessage.error('删除失败')
      console.error('删除失败:', error)
    }
  }
  
  return {
    attachments,
    loading,
    uploading,
    uploadProgress,
    loadAttachments,
    uploadAttachment,
    downloadAttachment,
    deleteAttachment
  }
}
