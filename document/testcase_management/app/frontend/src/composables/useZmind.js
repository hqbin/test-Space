/**
 * Zmind集成组合式函数
 */
import { ref } from 'vue'
import * as api from '@/api/zmind'
import { ElMessage } from 'element-plus'

export function useZmind() {
  const loading = ref(false)
  const submitting = ref(false)
  
  /**
   * 创建Zmind问题单
   */
  const createIssue = async (executionId, issueData) => {
    submitting.value = true
    try {
      const res = await api.createZmindIssue({
        execution_id: executionId,
        ...issueData
      })
      
      ElMessage.success('问题单创建成功')
      return res.data
    } catch (error) {
      ElMessage.error('问题单创建失败')
      console.error('问题单创建失败:', error)
      return null
    } finally {
      submitting.value = false
    }
  }
  
  /**
   * 获取问题单状态
   */
  const getIssueStatus = async (issueId, apiKey) => {
    loading.value = true
    try {
      const res = await api.getZmindIssueStatus(issueId, apiKey)
      return res.data
    } catch (error) {
      ElMessage.error('获取问题单状态失败')
      console.error('获取问题单状态失败:', error)
      return null
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 同步问题单状态
   */
  const syncIssueStatus = async (executionId) => {
    try {
      await api.syncZmindIssueStatus(executionId)
      ElMessage.success('同步成功')
      return true
    } catch (error) {
      ElMessage.error('同步失败')
      console.error('同步失败:', error)
      return false
    }
  }
  
  /**
   * 验证问题单数据
   */
  const validateIssueData = (data) => {
    if (!data.project_id) {
      ElMessage.warning('请选择Zmind项目')
      return false
    }
    
    if (!data.title) {
      ElMessage.warning('请输入问题单标题')
      return false
    }
    
    return true
  }
  
  return {
    loading,
    submitting,
    createIssue,
    getIssueStatus,
    syncIssueStatus,
    validateIssueData
  }
}
