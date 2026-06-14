<template>
  <div class="validation-result-step" ref="containerRef">
    <!-- 统计信息 -->
    <div class="statistics-bar">
      <div class="stat-item">
        <span class="label">总计:</span>
        <span class="value">{{ statistics.total }}</span>
      </div>
      <div class="stat-item success">
        <span class="label">通过:</span>
        <span class="value">{{ statistics.valid }}</span>
      </div>
      <div class="stat-item warning">
        <span class="label">警告:</span>
        <span class="value">{{ statistics.warning }}</span>
      </div>
      <div class="stat-item error">
        <span class="label">错误:</span>
        <span class="value">{{ statistics.error }}</span>
      </div>
    </div>

    <!-- 工具栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <el-button @click="$emit('back')">
          <el-icon><ArrowLeft /></el-icon>
          返回
        </el-button>
        <el-select v-model="filterType" style="width: 150px; margin-left: 12px">
          <el-option label="显示全部" value="all" />
          <el-option label="仅显示错误" value="error" />
          <el-option label="仅显示警告" value="warning" />
          <el-option label="仅显示问题" value="issues" />
        </el-select>
      </div>
      
      <div class="toolbar-actions">
        <el-button @click="$emit('reset')">
          <el-icon><RefreshLeft /></el-icon>
          重置
        </el-button>
        <el-button type="primary" @click="handleExport">
          <el-icon><Download /></el-icon>
          导出Excel
        </el-button>
      </div>
    </div>

    <!-- 数据表格 -->
    <div class="table-container">
      <el-table
        ref="tableRef"
        :data="paginatedRows"
        border
        :row-class-name="getRowClassName"
        :max-height="tableMaxHeight"
        v-loading="loading"
      >
        <el-table-column type="index" label="#" width="50" align="center">
          <template #default="{ $index }">
            {{ (currentPage - 1) * pageSize + $index + 1 }}
          </template>
        </el-table-column>
        
        <el-table-column
          v-for="header in displayHeaders"
          :key="header"
          :prop="header"
          :label="header"
          min-width="100"
          align="center"
          header-align="center"
        >
          <template #default="{ row }">
            <EditableCell
              :value="getCellValue(row, header)"
              :issues="getCellIssues(row, header)"
              :field-config="getFieldConfig(header)"
              @update="(val) => handleCellUpdate(row.row_index, header, val)"
            />
          </template>
        </el-table-column>

        <el-table-column label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="70" align="center">
          <template #default="{ row }">
            <el-button
              v-if="hasFixableIssues(row)"
              link
              type="primary"
              size="small"
              @click="handleRowFix(row)"
            >
              修复
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 分页器 -->
    <div class="pagination-container">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[20, 50, 100, 200]"
        :total="filteredRows.length"
        layout="total, sizes, prev, pager, next, jumper"
        background
        @size-change="handleSizeChange"
        @current-change="handlePageChange"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessageBox } from 'element-plus'
import { RefreshLeft, Download, ArrowLeft } from '@element-plus/icons-vue'
import EditableCell from './EditableCell.vue'

const props = defineProps({
  taskId: String,
  checkResult: {
    type: Object,
    default: () => ({})
  },
  loading: Boolean
})

const emit = defineEmits(['update-cell', 'apply-fix', 'reset', 'export', 'refresh', 'back'])

const filterType = ref('all')
const tableRef = ref(null)
const containerRef = ref(null)

// 分页相关
const currentPage = ref(1)
const pageSize = ref(50)

// 计算表格最大高度
const tableMaxHeight = ref(400)

// 计算实际高度
const calculateTableHeight = () => {
  nextTick(() => {
    if (containerRef.value) {
      const container = containerRef.value
      const rect = container.getBoundingClientRect()
      // 容器顶部到视口底部的距离 - 分页器高度(60) - 对话框底部按钮区(70) - 安全边距(20)
      const availableHeight = window.innerHeight - rect.top - 150
      tableMaxHeight.value = Math.max(availableHeight, 200)
    } else {
      // 备用计算
      const vh = window.innerHeight
      tableMaxHeight.value = Math.max(vh - 450, 200)
    }
  })
}

// 在组件挂载后计算实际高度
onMounted(() => {
  calculateTableHeight()
  window.addEventListener('resize', calculateTableHeight)
})

onUnmounted(() => {
  window.removeEventListener('resize', calculateTableHeight)
})

// 统计信息
const statistics = computed(() => props.checkResult.statistics || {
  total: 0,
  valid: 0,
  warning: 0,
  error: 0,
  fixable: 0
})

// 显示的表头（使用映射后的名称）
const displayHeaders = computed(() => {
  const headers = props.checkResult.headers || []
  const mapping = props.checkResult.field_mapping || {}
  // 返回映射后的表头名称
  return headers.map(h => mapping[h] || h)
})

// 原始表头到映射表头的对应关系
const headerMapping = computed(() => {
  const headers = props.checkResult.headers || []
  const mapping = props.checkResult.field_mapping || {}
  const result = {}
  headers.forEach(h => {
    result[mapping[h] || h] = h  // 映射后名称 -> 原始名称
  })
  return result
})

// 筛选后的行
const filteredRows = computed(() => {
  const rows = props.checkResult.rows || []
  if (filterType.value === 'all') return rows
  if (filterType.value === 'error') return rows.filter(r => r.status === 'error')
  if (filterType.value === 'warning') return rows.filter(r => r.status === 'warning')
  if (filterType.value === 'issues') return rows.filter(r => r.status !== 'valid')
  return rows
})

// 分页后的行
const paginatedRows = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredRows.value.slice(start, end)
})

// 分页变化时重置到第一页（如果当前页超出范围）
const handleSizeChange = () => {
  const maxPage = Math.ceil(filteredRows.value.length / pageSize.value)
  if (currentPage.value > maxPage) {
    currentPage.value = Math.max(1, maxPage)
  }
}

const handlePageChange = () => {
  // 页码变化时滚动到表格顶部
  if (tableRef.value) {
    tableRef.value.setScrollTop(0)
  }
}

// 获取单元格值（使用原始列名从数据中获取）
const getCellValue = (row, mappedHeader) => {
  // mappedHeader 是映射后的名称，需要找到原始列名
  const originalHeader = headerMapping.value[mappedHeader] || mappedHeader
  return row.data?.[originalHeader] || ''
}

// 获取单元格问题
const getCellIssues = (row, mappedHeader) => {
  // mappedHeader 已经是模板字段名
  return (row.issues || []).filter(issue => 
    issue.field === mappedHeader
  )
}

// 获取字段配置
const getFieldConfig = (mappedHeader) => {
  // mappedHeader 已经是模板字段名
  const fields = props.checkResult.template_fields || []
  return fields.find(f => f.name === mappedHeader) || {}
}

// 获取行样式类名
const getRowClassName = ({ row }) => {
  if (row.status === 'error') return 'row-error'
  if (row.status === 'warning') return 'row-warning'
  return ''
}

// 获取状态类型
const getStatusType = (status) => {
  if (status === 'valid') return 'success'
  if (status === 'warning') return 'warning'
  if (status === 'error') return 'danger'
  return 'info'
}

// 获取状态文本
const getStatusText = (status) => {
  if (status === 'valid') return '通过'
  if (status === 'warning') return '警告'
  if (status === 'error') return '错误'
  return '未知'
}

// 检查行是否有可修复问题
const hasFixableIssues = (row) => {
  return (row.issues || []).some(i => i.fixable)
}

// 处理单元格更新
const handleCellUpdate = (rowIndex, mappedHeader, value) => {
  // mappedHeader 已经是模板字段名，直接使用
  emit('update-cell', { rowIndex, field: mappedHeader, value })
}

// 处理单行修复
const handleRowFix = async (row) => {
  try {
    await ElMessageBox.confirm(
      '确定要修复该行的所有可修复问题吗？',
      '确认修复',
      { type: 'warning' }
    )
    emit('apply-fix', { rowIndices: [row.row_index], fixType: null })
  } catch {
    // 取消
  }
}

// 处理导出（带错误检查）
const handleExport = async () => {
  const errorCount = statistics.value.error || 0
  
  if (errorCount > 0) {
    try {
      await ElMessageBox.confirm(
        `当前还有 ${errorCount} 条错误数据未修复，确定要继续导出吗？`,
        '导出确认',
        { 
          type: 'warning',
          confirmButtonText: '继续导出',
          cancelButtonText: '取消'
        }
      )
      emit('export')
    } catch {
      // 取消导出
    }
  } else {
    emit('export')
  }
}
</script>

<style scoped>
.validation-result-step {
  padding: 10px;
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.statistics-bar {
  display: flex;
  gap: 20px;
  padding: 12px 16px;
  background: #f5f7fa;
  border-radius: 4px;
  margin-bottom: 12px;
  flex-shrink: 0;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.stat-item .label {
  color: #606266;
}

.stat-item .value {
  font-weight: 600;
  font-size: 16px;
}

.stat-item.success .value { color: #67C23A; }
.stat-item.warning .value { color: #E6A23C; }
.stat-item.error .value { color: #F56C6C; }
.stat-item.info .value { color: #409EFF; }

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  flex-shrink: 0;
}

.toolbar-left {
  display: flex;
  align-items: center;
}

.toolbar-actions {
  display: flex;
  gap: 8px;
}

.table-container {
  border: 1px solid #ebeef5;
  border-radius: 4px;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  padding: 12px 0 0;
  flex-shrink: 0;
  min-height: 44px;
}

:deep(.row-error) {
  background-color: #fef0f0 !important;
}

:deep(.row-warning) {
  background-color: #fdf6ec !important;
}

:deep(.el-table .cell) {
  padding: 8px 12px;
  line-height: 1.4;
}
</style>
