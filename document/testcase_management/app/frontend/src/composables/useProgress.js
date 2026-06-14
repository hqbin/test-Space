/**
 * 进度统计组合式函数
 */
import { ref, computed } from 'vue'
import * as api from '@/api/progress'
import { ElMessage } from 'element-plus'

export function useProgress(testplanId) {
  const statistics = ref({
    total: 0,
    executed: 0,
    not_executed: 0,
    passed: 0,
    failed: 0,
    blocked: 0,
    skipped: 0,
    progress_percentage: 0
  })
  
  const loading = ref(false)
  
  /**
   * 计算进度百分比
   */
  const progressPercentage = computed(() => {
    return statistics.value.progress_percentage
  })
  
  /**
   * 计算通过率
   */
  const passRate = computed(() => {
    if (statistics.value.executed === 0) return 0
    return Math.round((statistics.value.passed / statistics.value.executed) * 100)
  })
  
  /**
   * 加载进度统计
   */
  const loadStatistics = async () => {
    loading.value = true
    try {
      const res = await api.getProgressStatistics(testplanId)
      statistics.value = res.data || statistics.value
    } catch (error) {
      ElMessage.error('加载进度统计失败')
      console.error('加载进度统计失败:', error)
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 刷新统计（静默刷新）
   */
  const refreshStatistics = async () => {
    try {
      const res = await api.getProgressStatistics(testplanId)
      statistics.value = res.data || statistics.value
    } catch (error) {
      console.error('刷新进度统计失败:', error)
    }
  }
  
  return {
    statistics,
    loading,
    progressPercentage,
    passRate,
    loadStatistics,
    refreshStatistics
  }
}

/**
 * 执行进度管理组合式函数
 */
export function useExecutionProgress(testplanId) {
  const progress = ref(null)
  const loading = ref(false)
  
  /**
   * 加载执行进度
   */
  const loadProgress = async () => {
    loading.value = true
    try {
      const res = await api.getExecutionProgress(testplanId)
      progress.value = res.data
      return progress.value
    } catch (error) {
      console.error('加载执行进度失败:', error)
      return null
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 保存执行进度
   */
  const saveProgress = async (currentTestcaseId, currentIndex, sortOrder = null) => {
    try {
      await api.saveExecutionProgress({
        testplan_id: testplanId,
        current_testcase_id: currentTestcaseId,
        current_index: currentIndex,
        sort_order: sortOrder
      })
    } catch (error) {
      console.error('保存执行进度失败:', error)
    }
  }
  
  return {
    progress,
    loading,
    loadProgress,
    saveProgress
  }
}

/**
 * 执行历史组合式函数
 */
export function useExecutionHistory(testplanId, testcaseId) {
  const history = ref([])
  const loading = ref(false)
  
  /**
   * 加载执行历史
   */
  const loadHistory = async (limit = 10) => {
    loading.value = true
    try {
      const res = await api.getExecutionHistory(testplanId, testcaseId, limit)
      history.value = res.data || []
    } catch (error) {
      ElMessage.error('加载执行历史失败')
      console.error('加载执行历史失败:', error)
    } finally {
      loading.value = false
    }
  }
  
  return {
    history,
    loading,
    loadHistory
  }
}
