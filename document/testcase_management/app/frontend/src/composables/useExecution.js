/**
 * 测试执行组合式函数
 */
import { ref } from 'vue'
import * as api from '@/api/execution'
import { ElMessage } from 'element-plus'

export function useExecution() {
  const loading = ref(false)
  const submitting = ref(false)
  
  /**
   * 执行测试用例（增强版）
   */
  const executeTestcase = async (data) => {
    submitting.value = true
    try {
      const res = await api.createExecutionEnhanced(data)
      ElMessage.success('执行成功')
      return res.data
    } catch (error) {
      ElMessage.error('执行失败')
      console.error('执行失败:', error)
      return null
    } finally {
      submitting.value = false
    }
  }
  
  /**
   * 批量标记执行结果
   */
  const batchExecute = async (testPlanId, testCaseIds, result) => {
    submitting.value = true
    try {
      const res = await api.batchExecute({
        test_plan_id: testPlanId,
        test_case_ids: testCaseIds,
        result
      })
      
      ElMessage.success(`成功标记${testCaseIds.length}个用例`)
      return res.data
    } catch (error) {
      ElMessage.error('批量标记失败')
      console.error('批量标记失败:', error)
      return null
    } finally {
      submitting.value = false
    }
  }
  
  /**
   * 获取执行记录详情
   */
  const getExecutionDetail = async (executionId) => {
    loading.value = true
    try {
      const res = await api.getExecutionDetail(executionId)
      return res.data
    } catch (error) {
      ElMessage.error('获取执行详情失败')
      console.error('获取执行详情失败:', error)
      return null
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 验证执行数据
   */
  const validateExecutionData = (data) => {
    if (!data.test_plan_id) {
      ElMessage.warning('缺少测试计划ID')
      return false
    }
    
    if (!data.test_case_id) {
      ElMessage.warning('缺少测试用例ID')
      return false
    }
    
    if (!data.result) {
      ElMessage.warning('请选择执行结果')
      return false
    }
    
    if (data.result === 'FAIL' && !data.failure_reason) {
      ElMessage.warning('执行失败时必须填写失败原因')
      return false
    }
    
    return true
  }
  
  return {
    loading,
    submitting,
    executeTestcase,
    batchExecute,
    getExecutionDetail,
    validateExecutionData
  }
}
