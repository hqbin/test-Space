<template>
  <el-dialog
    v-model="visible"
    :title="$t('execution.executionHistory')"
    width="800px"
    @close="handleClose"
  >
    <div v-loading="loading">
      <el-timeline v-if="history.length > 0">
        <el-timeline-item
          v-for="item in history"
          :key="item.id"
          :timestamp="formatDateTime(item.executed_at)"
          placement="top"
        >
          <el-card>
            <div class="history-item">
              <div class="history-header">
                <el-tag :type="getResultType(item.result)" size="large">
                  {{ getResultText(item.result) }}
                </el-tag>
                <span class="executor">{{ $t('execution.executor') }}: {{ getExecutorName(item.executor_id) }}</span>
              </div>
              
              <div v-if="item.actual_result" class="history-section">
                <div class="section-title">{{ $t('execution.actualResult') }}</div>
                <div class="section-content">{{ item.actual_result }}</div>
              </div>
              
              <div v-if="item.failure_reason" class="history-section">
                <div class="section-title">{{ $t('execution.failureReason') }}</div>
                <div class="section-content error-text">{{ item.failure_reason }}</div>
              </div>
              
              <div v-if="item.remarks" class="history-section">
                <div class="section-title">{{ $t('execution.remarks') }}</div>
                <div class="section-content" v-html="renderRemarkWithPR(item.remarks)"></div>
              </div>
            </div>
          </el-card>
        </el-timeline-item>
      </el-timeline>
      
      <el-empty v-else :description="$t('testcase.noExecutionHistory')" />
    </div>
    
    <template #footer>
      <el-button @click="handleClose">{{ $t('common.close') }}</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useExecutionHistory } from '@/composables/useProgress'
import { renderRemarkWithPR } from '@/composables/useRemarkPR'

const { t } = useI18n()

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  testplanId: {
    type: [Number, null],
    default: null
  },
  testcaseId: {
    type: [Number, null],
    default: null
  },
  limit: {
    type: Number,
    default: 10
  }
})

const emit = defineEmits(['update:modelValue'])

const visible = ref(props.modelValue)

const { history, loading, loadHistory } = useExecutionHistory(
  props.testplanId,
  props.testcaseId
)

watch(() => props.modelValue, (val) => {
  visible.value = val
  if (val) {
    loadHistory(props.limit)
  }
})

watch(visible, (val) => {
  emit('update:modelValue', val)
})

const getResultType = (result) => {
  const typeMap = {
    'PASSED': 'success',
    'FAILED': 'danger',
    'BLOCKED': 'warning',
    'SKIPPED': 'info'
  }
  return typeMap[result] || 'info'
}

const getResultText = (result) => {
  const textMap = {
    'PASSED': t('execution.passed'),
    'FAILED': t('execution.failed'),
    'BLOCKED': t('execution.blocked'),
    'SKIPPED': t('execution.skipped')
  }
  return textMap[result] || t('execution.unknown')
}

const getExecutorName = (executorId) => {
  return t('execution.userPrefix') + executorId
}

const formatDateTime = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

const handleClose = () => {
  visible.value = false
}
</script>

<style scoped>
.history-item {
  padding: 10px;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.executor {
  color: #606266;
  font-size: 14px;
}

.history-section {
  margin-bottom: 10px;
}

.history-section:last-child {
  margin-bottom: 0;
}

.section-title {
  font-weight: bold;
  color: #606266;
  margin-bottom: 5px;
  font-size: 14px;
}

.section-content {
  color: #303133;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

.error-text {
  color: #F56C6C;
}
</style>
