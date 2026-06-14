<template>
  <div class="sheet-selection-step">
    <div class="step-header">
      <el-alert
        title="请选择包含用例数据的Sheet"
        type="info"
        :closable="false"
        show-icon
      >
        <template #default>
          系统已自动识别可能包含用例的Sheet，您可以预览并确认选择。
        </template>
      </el-alert>
    </div>

    <div class="sheet-content" v-loading="loading">
      <div class="sheet-list">
        <div class="list-header">Sheet列表 ({{ sheets.length }})</div>
        <el-scrollbar class="sheet-scrollbar">
          <div
            v-for="sheet in sheets"
            :key="sheet.name"
            :class="['sheet-item', { active: selectedSheet === sheet.name }]"
            @click="selectSheet(sheet.name)"
          >
            <div class="sheet-info">
              <div class="sheet-name">
                <el-icon v-if="sheet.auto_recommend" class="recommend-icon">
                  <Star />
                </el-icon>
                {{ sheet.name }}
                <el-tag v-if="sheet.auto_recommend" size="small" type="warning">
                  推荐
                </el-tag>
                <el-tag v-else-if="sheet.row_count === 0" size="small" type="info">
                  空
                </el-tag>
              </div>
              <div class="sheet-meta">
                <template v-if="sheet.row_count > 0">
                  {{ sheet.row_count }} 行 · {{ sheet.column_count }} 列
                </template>
                <template v-else>
                  <span class="empty-hint">无数据</span>
                </template>
              </div>
              <div v-if="sheet.recommend_reason" class="sheet-reason">
                <el-tooltip :content="sheet.recommend_reason" placement="top" :show-after="500">
                  <span class="reason-text">{{ sheet.recommend_reason }}</span>
                </el-tooltip>
              </div>
            </div>
            <el-icon class="check-icon" v-if="selectedSheet === sheet.name">
              <Check />
            </el-icon>
          </div>
        </el-scrollbar>
      </div>

      <div class="sheet-preview">
        <div class="preview-header">
          <span>预览: {{ selectedSheet || '请选择Sheet' }}</span>
          <span v-if="currentSheetData" class="preview-info">
            显示前 {{ currentSheetData.preview_rows?.length || 0 }} 行
          </span>
        </div>
        <div class="preview-content">
          <el-table
            v-if="currentSheetData?.preview_rows?.length"
            :data="previewTableData"
            border
            size="small"
            :max-height="400"
            style="width: 100%"
          >
            <el-table-column
              v-for="(col, index) in previewColumns"
              :key="index"
              :prop="'col_' + index"
              :label="col"
              min-width="120"
              :show-overflow-tooltip="{ showAfter: 500 }"
            />
          </el-table>
          <el-empty v-else description="暂无预览数据" />
        </div>
      </div>
    </div>

    <div class="step-actions">
      <el-button @click="handleBack">
        <el-icon><ArrowLeft /></el-icon>
        上一步
      </el-button>
      <el-button
        type="primary"
        :disabled="!selectedSheet"
        @click="handleConfirm"
      >
        下一步
        <el-icon><ArrowRight /></el-icon>
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { Star, Check, ArrowLeft, ArrowRight } from '@element-plus/icons-vue'

const props = defineProps({
  sheets: {
    type: Array,
    default: () => []
  },
  recommendedSheet: {
    type: String,
    default: ''
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['select', 'confirm', 'back'])

const selectedSheet = ref('')

// 当前选中的Sheet数据
const currentSheetData = computed(() => {
  return props.sheets.find(s => s.name === selectedSheet.value)
})

// 预览表格的列（第一行作为表头）
const previewColumns = computed(() => {
  const data = currentSheetData.value?.preview_rows
  if (!data || data.length === 0) return []
  // 使用第一行作为列标题
  return data[0].map((cell, index) => cell || `列${index + 1}`)
})

// 预览表格的数据（从第二行开始）
const previewTableData = computed(() => {
  const data = currentSheetData.value?.preview_rows
  if (!data || data.length <= 1) return []
  
  return data.slice(1).map((row, rowIndex) => {
    const rowData = { _index: rowIndex }
    row.forEach((cell, colIndex) => {
      rowData['col_' + colIndex] = cell
    })
    return rowData
  })
})

// 初始化选中推荐的Sheet
watch(() => props.recommendedSheet, (newVal) => {
  if (newVal && !selectedSheet.value) {
    selectedSheet.value = newVal
  }
}, { immediate: true })

// 当sheets变化时，如果有推荐则选中
watch(() => props.sheets, (newSheets) => {
  if (newSheets.length > 0 && !selectedSheet.value) {
    const recommended = newSheets.find(s => s.auto_recommend)
    if (recommended) {
      selectedSheet.value = recommended.name
    } else {
      selectedSheet.value = newSheets[0].name
    }
  }
}, { immediate: true })

const selectSheet = (name) => {
  selectedSheet.value = name
  emit('select', name)
}

const handleConfirm = () => {
  if (selectedSheet.value) {
    const sheetData = currentSheetData.value
    emit('confirm', {
      sheetName: selectedSheet.value,
      detectedHeaderRow: sheetData?.detected_header_row || 1
    })
  }
}

const handleBack = () => {
  emit('back')
}
</script>

<style scoped>
.sheet-selection-step {
  padding: 16px;
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.step-header {
  margin-bottom: 16px;
  flex-shrink: 0;
}

.sheet-content {
  display: flex;
  gap: 16px;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.sheet-list {
  width: 280px;
  flex-shrink: 0;
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.list-header {
  padding: 12px 16px;
  background: var(--el-fill-color-light);
  border-bottom: 1px solid var(--el-border-color);
  font-weight: 500;
  flex-shrink: 0;
}

.sheet-scrollbar {
  flex: 1;
  min-height: 0;
}

.sheet-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  cursor: pointer;
  border-bottom: 1px solid var(--el-border-color-lighter);
  transition: background-color 0.2s;
}

.sheet-item:hover {
  background: var(--el-fill-color-light);
}

.sheet-item.active {
  background: var(--el-color-primary-light-9);
  border-left: 3px solid var(--el-color-primary);
}

.sheet-info {
  flex: 1;
  min-width: 0;
}

.sheet-name {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 500;
  margin-bottom: 4px;
}

.recommend-icon {
  color: var(--el-color-warning);
}

.sheet-meta {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.sheet-meta .empty-hint {
  color: var(--el-text-color-placeholder);
  font-style: italic;
}

.sheet-reason {
  margin-top: 4px;
}

.reason-text {
  font-size: 11px;
  color: var(--el-text-color-placeholder);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: block;
  max-width: 180px;
}

.check-icon {
  color: var(--el-color-primary);
  font-size: 18px;
}

.sheet-preview {
  flex: 1;
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: var(--el-fill-color-light);
  border-bottom: 1px solid var(--el-border-color);
  font-weight: 500;
  flex-shrink: 0;
}

.preview-info {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  font-weight: normal;
}

.preview-content {
  flex: 1;
  padding: 12px;
  overflow: auto;
  min-height: 0;
}

.step-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  padding-top: 16px;
  flex-shrink: 0;
}
</style>
