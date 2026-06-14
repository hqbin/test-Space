<template>
  <el-card class="execution-card" :class="resultClass">
    <template #header>
      <div class="card-header">
        <span class="testcase-name">{{ testcase.name }}</span>
        <el-tag :type="resultTagType" size="large">
          {{ resultText }}
        </el-tag>
      </div>
    </template>
    
    <div class="card-content">
      <!-- 前置条件 -->
      <div v-if="testcase.precondition" class="section">
        <div class="section-title">{{ $t('testcase.precondition') }}</div>
        <div class="section-content">{{ testcase.precondition }}</div>
      </div>
      
      <!-- 测试步骤 -->
      <div class="section">
        <div class="section-title">{{ $t('testcase.steps') }}</div>
        <div class="section-content">{{ testcase.steps }}</div>
      </div>
      
      <!-- 预期结果 -->
      <div class="section">
        <div class="section-title">{{ $t('testcase.expectedResult') }}</div>
        <div class="section-content">{{ testcase.expected_result }}</div>
      </div>
      
      <!-- 实际结果（如果已执行） -->
      <div v-if="execution && execution.actual_result" class="section">
        <div class="section-title">{{ $t('testcase.actualResult') }}</div>
        <div class="section-content">{{ execution.actual_result }}</div>
      </div>
      
      <!-- 失败原因（如果失败） -->
      <div v-if="execution && execution.failure_reason" class="section">
        <div class="section-title">{{ $t('testcase.failureReason') }}</div>
        <div class="section-content error-text">{{ execution.failure_reason }}</div>
      </div>
      
      <!-- 备注 -->
      <div v-if="execution && execution.remarks" class="section">
        <div class="section-title">{{ $t('execution.remarks') }}</div>
        <div class="section-content" v-html="renderRemarkWithPR(execution.remarks)"></div>
      </div>
      
      <!-- Zmind问题单 -->
      <div v-if="execution && execution.zmind_issue_url" class="section">
        <div class="section-title">{{ $t('zmind.zmindIssue') }}</div>
        <div class="section-content">
          <el-link :href="execution.zmind_issue_url" target="_blank" type="primary">
            {{ execution.zmind_issue_id }}
          </el-link>
        </div>
      </div>
    </div>
    
    <template #footer>
      <div class="card-footer">
        <el-button-group>
          <el-button
            type="success"
            :icon="CircleCheck"
            @click="handleExecute('PASS')"
            :disabled="disabled"
          >
            PASS
          </el-button>
          <el-button
            type="danger"
            :icon="CircleClose"
            @click="handleExecute('FAIL')"
            :disabled="disabled"
          >
            FAIL
          </el-button>
          <el-button
            type="warning"
            :icon="WarningFilled"
            @click="handleExecute('BLOCK')"
            :disabled="disabled"
          >
            BLOCK
          </el-button>
          <el-button
            type="info"
            :icon="Remove"
            @click="handleExecute('NA')"
            :disabled="disabled"
          >
            NA
          </el-button>
        </el-button-group>
        
        <el-button
          v-if="execution"
          type="primary"
          :icon="Document"
          @click="handleViewHistory"
        >
          {{ $t('execution.viewHistory') }}
        </el-button>
      </div>
    </template>
  </el-card>
</template>

<script setup>
import { computed } from 'vue'
import { CircleCheck, CircleClose, WarningFilled, Remove, Document } from '@element-plus/icons-vue'
import { renderRemarkWithPR } from '@/composables/useRemarkPR'

const props = defineProps({
  testcase: {
    type: Object,
    required: true
  },
  execution: {
    type: Object,
    default: null
  },
  disabled: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['execute', 'view-history'])

const resultClass = computed(() => {
  if (!props.execution) return ''
  
  const resultMap = {
    'PASS': 'result-passed',
    'FAIL': 'result-failed',
    'BLOCK': 'result-blocked',
    'NA': 'result-skipped',
    'NT': 'result-skipped',
    '待确认': 'result-pending'
  }
  
  return resultMap[props.execution.result] || ''
})

const resultTagType = computed(() => {
  if (!props.execution) return 'info'
  
  const typeMap = {
    'PASS': 'success',
    'FAIL': 'danger',
    'BLOCK': 'warning',
    'NA': 'info',
    'NT': 'info',
    '待确认': 'warning'
  }
  
  return typeMap[props.execution.result] || 'info'
})

const resultText = computed(() => {
  if (!props.execution) return '未执行'
  
  const textMap = {
    'PASS': 'PASS',
    'FAIL': 'FAIL',
    'BLOCK': 'BLOCK',
    'NA': 'NA',
    'NT': 'NT',
    '待确认': '待确认'
  }
  
  return textMap[props.execution.result] || '未知'
})

const handleExecute = (result) => {
  emit('execute', { testcase: props.testcase, result })
}

const handleViewHistory = () => {
  emit('view-history', props.testcase)
}
</script>

<style scoped>
.execution-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.testcase-name {
  font-size: 16px;
  font-weight: bold;
}

.card-content {
  padding: 10px 0;
}

.section {
  margin-bottom: 15px;
}

.section:last-child {
  margin-bottom: 0;
}

.section-title {
  font-weight: bold;
  color: #606266;
  margin-bottom: 5px;
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

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.execution-card.result-passed {
  border-left: 4px solid #67C23A;
}

.execution-card.result-failed {
  border-left: 4px solid #F56C6C;
}

.execution-card.result-blocked {
  border-left: 4px solid #E6A23C;
}

.execution-card.result-skipped {
  border-left: 4px solid #909399;
}

.execution-card.result-pending {
  border-left: 4px solid #E6A23C;
}
</style>
