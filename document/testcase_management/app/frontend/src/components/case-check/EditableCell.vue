<template>
  <div class="editable-cell" :class="cellClass" @click="startEdit">
    <!-- 显示模式 -->
    <div v-if="!editing" class="cell-display">
      <el-tooltip
        :content="fullValue"
        placement="top"
        :disabled="!shouldShowTooltip"
        :show-after="500"
        effect="dark"
      >
        <span class="cell-value">{{ displayValue }}</span>
      </el-tooltip>
      
      <!-- 问题图标 -->
      <el-tooltip
        v-if="issues.length > 0"
        :content="issueTooltip"
        placement="top"
        effect="dark"
       :show-after="500">
        <el-icon class="issue-icon" :class="issueIconClass">
          <WarningFilled v-if="hasError" />
          <Warning v-else />
        </el-icon>
      </el-tooltip>
      
      <!-- 编辑提示图标 -->
      <el-icon class="edit-hint" v-if="issues.length > 0">
        <Edit />
      </el-icon>
    </div>

    <!-- 编辑模式 -->
    <div v-else class="cell-edit" @click.stop>
      <!-- 枚举类型使用下拉框 -->
      <el-select
        v-if="fieldConfig.field_type === 'enum'"
        v-model="editValue"
        size="small"
        @change="finishEdit"
        @blur="finishEdit"
        ref="inputRef"
      >
        <el-option
          v-for="opt in fieldConfig.enum_values || []"
          :key="opt"
          :label="opt"
          :value="opt"
        />
      </el-select>
      
      <!-- 其他类型使用输入框 -->
      <el-input
        v-else
        v-model="editValue"
        size="small"
        @keyup.enter="finishEdit"
        @blur="finishEdit"
        ref="inputRef"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, watch } from 'vue'
import { WarningFilled, Warning, Edit } from '@element-plus/icons-vue'

const props = defineProps({
  value: {
    type: [String, Number],
    default: ''
  },
  issues: {
    type: Array,
    default: () => []
  },
  fieldConfig: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update'])

const editing = ref(false)
const editValue = ref('')
const inputRef = ref(null)

// 完整值（用于tooltip显示）
const fullValue = computed(() => {
  const val = props.value
  if (val === null || val === undefined || val === '') {
    return '(空)'
  }
  return String(val)
})

// 是否需要显示tooltip（内容非空时都显示）
const shouldShowTooltip = computed(() => {
  const val = props.value
  if (val === null || val === undefined || val === '') {
    return false
  }
  return true
})

// 显示值
const displayValue = computed(() => {
  const val = props.value
  if (val === null || val === undefined || val === '') {
    return '-'
  }
  // 截断长文本
  const str = String(val)
  return str.length > 20 ? str.substring(0, 20) + '...' : str
})

// 是否有错误
const hasError = computed(() => {
  return props.issues.some(i => i.issue_type === 'required')
})

// 单元格样式类
const cellClass = computed(() => {
  if (props.issues.length === 0) return ''
  if (hasError.value) return 'has-error'
  return 'has-warning'
})

// 问题图标样式类
const issueIconClass = computed(() => {
  if (hasError.value) return 'error'
  return 'warning'
})

// 问题提示
const issueTooltip = computed(() => {
  return props.issues.map(i => i.message).join('\n')
})

// 开始编辑
const startEdit = () => {
  editing.value = true
  editValue.value = props.value || ''
  nextTick(() => {
    inputRef.value?.focus?.()
  })
}

// 完成编辑
const finishEdit = () => {
  editing.value = false
  if (editValue.value !== props.value) {
    emit('update', editValue.value)
  }
}

// 监听值变化
watch(() => props.value, (val) => {
  if (!editing.value) {
    editValue.value = val || ''
  }
})
</script>

<style scoped>
.editable-cell {
  min-height: 32px;
  padding: 4px 8px;
  border-radius: 4px;
  cursor: pointer;
  position: relative;
}

.editable-cell.has-error {
  background-color: #fef0f0;
  border: 1px solid #F56C6C;
}

.editable-cell.has-warning {
  background-color: #fdf6ec;
  border: 1px solid #E6A23C;
}

.cell-display {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 24px;
}

.cell-value {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.issue-icon {
  margin-left: 4px;
  flex-shrink: 0;
}

.issue-icon.error {
  color: #F56C6C;
}

.issue-icon.warning {
  color: #E6A23C;
}

.edit-hint {
  margin-left: 4px;
  color: #409EFF;
  opacity: 0;
  transition: opacity 0.2s;
}

.editable-cell:hover .edit-hint {
  opacity: 1;
}

.editable-cell.has-error .edit-hint,
.editable-cell.has-warning .edit-hint {
  opacity: 0.6;
}

.editable-cell.has-error:hover .edit-hint,
.editable-cell.has-warning:hover .edit-hint {
  opacity: 1;
}

.cell-edit {
  width: 100%;
}

.cell-edit :deep(.el-input),
.cell-edit :deep(.el-select) {
  width: 100%;
}
</style>
