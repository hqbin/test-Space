<template>
  <div class="step-editor">
    <div class="step-header">
      <span class="header-label">{{ $t('testcase.stepNumber') }}</span>
      <span class="header-label step-col">{{ $t('testcase.stepContent') }}</span>
      <span class="header-label expected-col">{{ $t('testcase.stepExpected') }}</span>
      <span class="header-label action-col">{{ $t('testcase.stepOperation') }}</span>
    </div>
    
    <div 
      v-for="(step, index) in steps" 
      :key="index"
      class="step-row"
    >
      <span class="step-number">{{ index + 1 }}</span>
      <el-input
        v-model="step.step"
        type="textarea"
        :rows="4"
        :autosize="{ minRows: 4, maxRows: 10 }"
        :placeholder="$t('testcase.inputSteps')"
        class="step-input"
      />
      <el-input
        v-model="step.expected"
        type="textarea"
        :rows="4"
        :autosize="{ minRows: 4, maxRows: 10 }"
        :placeholder="$t('testcase.inputExpectedResult')"
        class="expected-input"
      />
      <div class="step-actions">
        <el-button
          type="primary"
          :icon="Plus"
          size="small"
          circle
          @click="addStep(index)"
          title="在下方插入"
        />
        <el-button
          v-if="steps.length > 1"
          type="danger"
          :icon="Delete"
          size="small"
          circle
          @click="removeStep(index)"
          title="删除"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { Plus, Delete } from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => [{ step: '', expected: '' }]
  }
})

const emit = defineEmits(['update:modelValue'])

const steps = ref([...props.modelValue])

// 标记是否是内部更新
let isInternalUpdate = false

// 监听外部变化
watch(() => props.modelValue, (newVal) => {
  if (!isInternalUpdate) {
    steps.value = [...newVal]
  }
  isInternalUpdate = false
}, { deep: true })

// 监听内部变化并通知父组件
watch(steps, (newVal) => {
  isInternalUpdate = true
  emit('update:modelValue', newVal)
}, { deep: true })

const addStep = (index) => {
  steps.value.splice(index + 1, 0, { step: '', expected: '' })
}

const removeStep = (index) => {
  if (steps.value.length > 1) {
    steps.value.splice(index, 1)
  }
}
</script>

<style scoped>
.step-editor {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  overflow: hidden;
  width: 100%;
}

.step-header {
  display: grid;
  grid-template-columns: 50px 1fr 1fr 90px;
  gap: 12px;
  padding: 12px 16px;
  background: #f5f7fa;
  border-bottom: 1px solid #dcdfe6;
  font-weight: 600;
  font-size: 14px;
  color: #606266;
}

.step-row {
  display: grid;
  grid-template-columns: 50px 1fr 1fr 90px;
  gap: 12px;
  padding: 16px;
  border-bottom: 1px solid #ebeef5;
  align-items: start;
}

.step-row:last-child {
  border-bottom: none;
}

.step-row:hover {
  background: #fafafa;
}

.step-number {
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 500;
  color: #909399;
  padding-top: 8px;
}

.step-input,
.expected-input {
  width: 100%;
  min-height: 100px;
}

.step-actions {
  display: flex;
  gap: 8px;
  align-items: center;
  justify-content: center;
  padding-top: 4px;
}

.header-label {
  text-align: center;
}

.step-col,
.expected-col {
  text-align: left;
}

:deep(.el-textarea__inner) {
  font-size: 14px;
  line-height: 1.6;
  min-height: 100px !important;
}
</style>
