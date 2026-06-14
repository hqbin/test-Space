<template>
  <div class="notification-template-management table-layout">
    <el-card class="table-layout" shadow="never">
      <template #header>
        <div class="card-header">
          <span class="title">{{ $t('notificationTemplate.title') }}</span>
          <el-button v-if="hasButton('notificationManagement', 'createTemplate')" type="primary" @click="handleCreate">
            <el-icon><Plus /></el-icon>
            {{ $t('notificationTemplate.createTemplate') }}
          </el-button>
        </div>
      </template>

      <!-- 搜索栏 -->
      <div class="search-bar">
        <el-input
          v-model="searchText"
          :placeholder="$t('notificationTemplate.searchPlaceholder')"
          clearable
          style="width: 300px"
          @clear="handleSearch"
          @keyup.enter="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-select
          v-model="filterType"
          :placeholder="$t('notificationTemplate.filterByType')"
          clearable
          style="width: 180px"
          @change="handleSearch"
        >
          <el-option :label="$t('notificationTemplate.allTypes')" value="" />
          <el-option :label="$t('notification.types.testcase')" value="testcase" />
          <el-option :label="$t('notification.types.testplan')" value="testplan" />
          <el-option :label="$t('notification.types.execution')" value="execution" />
          <el-option :label="$t('notification.types.report')" value="report" />
          <el-option label="系统通知" value="system" />
        </el-select>
        <el-button type="primary" @click="handleSearch">
          <el-icon><Search /></el-icon>
          {{ $t('common.search') }}
        </el-button>
      </div>

      <!-- 表格 -->
      <div class="table-wrapper">
        <div class="table-container" ref="tableContainerRef">
      <el-table
        ref="tableRef"
        :data="tableData"
        style="width: 100%"
        :height="tableHeight"
        border
        :header-cell-style="{ background: '#f0f1fb', color: '#606266', fontWeight: '600' }"
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" :label="$t('notificationTemplate.templateName')" min-width="180" />
        <el-table-column prop="notification_type" :label="$t('notificationTemplate.notificationType')" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="getTypeTagColor(row.notification_type)" size="small">
              {{ getTypeLabel(row.notification_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="title_template" :label="$t('notificationTemplate.titleTemplate')" min-width="200" :show-overflow-tooltip="{ showAfter: 500 }" />
        <el-table-column prop="is_system" :label="$t('notificationTemplate.templateType')" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_system ? 'info' : 'success'" size="small">
              {{ row.is_system ? $t('notificationTemplate.systemTemplate') : $t('notificationTemplate.customTemplate') }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" :label="$t('common.createdAt')" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column :label="$t('common.operation')" width="200">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleView(row)">
              <el-icon><View /></el-icon>
              {{ $t('notificationTemplate.view') }}
            </el-button>
            <el-button v-if="hasButton('notificationManagement', 'editTemplate')" link type="primary" @click="handleEdit(row)">
              <el-icon><Edit /></el-icon>
              {{ $t('common.edit') }}
            </el-button>
            <el-button v-if="!row.is_system && hasButton('notificationManagement', 'deleteTemplate')" link type="danger" @click="handleDelete(row)">
              <el-icon><Delete /></el-icon>
              {{ $t('common.delete') }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
        </div>
      </div>

      <!-- 分页 -->
      <div class="pagination pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="800px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="120px"
      >
        <el-form-item :label="$t('notificationTemplate.templateName')" prop="name">
          <el-input v-model="form.name" :placeholder="$t('notificationTemplate.inputTemplateName')" />
        </el-form-item>
        <el-form-item :label="$t('notificationTemplate.notificationType')" prop="notification_type">
          <el-select v-model="form.notification_type" :placeholder="$t('notificationTemplate.selectNotificationType')" style="width: 100%" @change="handleTypeChange">
            <el-option :label="$t('notification.types.testcase')" value="testcase" />
            <el-option :label="$t('notification.types.testplan')" value="testplan" />
            <el-option :label="$t('notification.types.execution')" value="execution" />
            <el-option :label="$t('notification.types.report')" value="report" />
            <el-option label="系统通知" value="system" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('notificationTemplate.titleTemplate')" prop="title_template">
          <el-input 
            v-model="form.title_template" 
            :placeholder="$t('notificationTemplate.inputTitleTemplate')"
            @focus="lastFocusedInput = 'title'"
          />
          <div class="template-hint">
            {{ $t('notificationTemplate.titleTemplateHint') }}
          </div>
        </el-form-item>
        <el-form-item :label="$t('notificationTemplate.contentTemplate')" prop="content_template">
          <el-input
            v-model="form.content_template"
            type="textarea"
            :rows="8"
            :placeholder="$t('notificationTemplate.inputContentTemplate')"
            @focus="lastFocusedInput = 'content'"
          />
          <div class="template-hint">
            {{ $t('notificationTemplate.contentTemplateHint') }}
          </div>
        </el-form-item>
        <el-form-item :label="$t('notificationTemplate.availableVariables')">
          <!-- 变量列表：类型变量 + 通用变量 -->
          <div class="variables-container">
            <div 
              v-for="variable in currentVariables" 
              :key="variable.name" 
              class="variable-item"
              @click="insertVariable(variable.name)"
            >
              <el-tag size="small" class="variable-tag">{{ variable.name }}</el-tag>
              <span class="variable-desc">{{ variable.description }}</span>
            </div>
          </div>
          <div class="variable-hint">
            <el-icon><InfoFilled /></el-icon>
            <span>点击变量可插入到光标位置（选择通知类型后显示对应变量）</span>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          {{ $t('common.confirm') }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 查看对话框 -->
    <el-dialog
      v-model="viewDialogVisible"
      :title="$t('notificationTemplate.templateDetail')"
      width="800px"
    >
      <div v-if="currentTemplate" class="template-detail">
        <div class="detail-item">
          <div class="detail-label">{{ $t('notificationTemplate.templateName') }}:</div>
          <div class="detail-value">{{ currentTemplate.name }}</div>
        </div>
        <div class="detail-item">
          <div class="detail-label">{{ $t('notificationTemplate.notificationType') }}:</div>
          <div class="detail-value">
            <el-tag :type="getTypeTagColor(currentTemplate.notification_type)" size="small">
              {{ getTypeLabel(currentTemplate.notification_type) }}
            </el-tag>
          </div>
        </div>
        <div class="detail-item">
          <div class="detail-label">{{ $t('notificationTemplate.titleTemplate') }}:</div>
          <div class="detail-value template-code">{{ currentTemplate.title_template }}</div>
        </div>
        <div class="detail-item">
          <div class="detail-label">{{ $t('notificationTemplate.contentTemplate') }}:</div>
          <div class="detail-value template-code">
            <pre>{{ currentTemplate.content_template }}</pre>
          </div>
        </div>
        <div class="detail-item">
          <div class="detail-label">{{ $t('notificationTemplate.availableVariables') }}:</div>
          <div class="detail-value">
            <div class="variables-container">
              <div v-for="variable in getTemplateVariables(currentTemplate.notification_type)" :key="variable.name" class="variable-item">
                <el-tag size="small" class="variable-tag">{{ variable.name }}</el-tag>
                <span class="variable-desc">{{ variable.description }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="viewDialogVisible = false">{{ $t('common.close') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Edit, Delete, View, InfoFilled } from '@element-plus/icons-vue'
import { getNotificationTemplates, createNotificationTemplate, updateNotificationTemplate, deleteNotificationTemplate } from '@/api/notification'
import { usePagination } from '@/composables/usePagination'
import { useTableHeight } from '@/composables/useTableHeight'
import { useScrollToTop } from '@/composables/useScrollToTop'
import { useLoadingStore } from '../../stores/loading'
import { useUserRole } from '../../composables/useUserRole'

const { t } = useI18n()
const { hasButton } = useUserRole()
const { tableContainerRef, tableHeight, bindTableHeight, unbindTableHeight } = useTableHeight()
const tableRef = ref(null)
const { scrollToTop } = useScrollToTop(tableRef)
const loadingStore = useLoadingStore()

const loading = ref(false)
const tableData = ref([])
const { page: currentPage, size: pageSize, total } = usePagination('notificationTemplateManagement', 10)
const searchText = ref('')
const filterType = ref('')

const dialogVisible = ref(false)
const dialogTitle = ref('')
const isEdit = ref(false)
const submitting = ref(false)
const formRef = ref(null)

const viewDialogVisible = ref(false)
const currentTemplate = ref(null)

// 用于跟踪当前聚焦的输入框
const lastFocusedInput = ref('title') // 'title' 或 'content'
const titleInputRef = ref(null)
const contentInputRef = ref(null)

// 定义各类型的可用变量
const variablesByType = {
  testcase: [
    { name: '{case_id}', description: '用例ID' },
    { name: '{case_name}', description: '用例名称' },
    { name: '{testcase_name}', description: '用例名称（别名）' },
    { name: '{action}', description: '操作类型' },
    { name: '{operator}', description: '操作人' },
    { name: '{operator_name}', description: '操作人（别名）' },
    { name: '{changes}', description: '变更内容' },
    { name: '{old_status}', description: '旧状态' },
    { name: '{new_status}', description: '新状态' },
    { name: '{time}', description: '操作时间' },
    { name: '{reviewer}', description: '审核人/评审人' },
    { name: '{review_status}', description: '审核状态' },
    { name: '{review_comment}', description: '审核意见' },
    { name: '{review_time}', description: '审核时间' }
  ],
  testplan: [
    { name: '{plan_name}', description: '计划名称' },
    { name: '{testplan_name}', description: '计划名称（别名）' },
    { name: '{action}', description: '操作类型' },
    { name: '{start_time}', description: '开始时间' },
    { name: '{end_time}', description: '结束时间' },
    { name: '{executors}', description: '执行人列表' },
    { name: '{operator}', description: '操作人' },
    { name: '{operator_name}', description: '操作人（别名）' },
    { name: '{reviewer}', description: '审核人' },
    { name: '{report_id}', description: '报告ID' }
  ],
  execution: [
    { name: '{case_name}', description: '用例名称' },
    { name: '{testcase_name}', description: '用例名称（别名）' },
    { name: '{result}', description: '执行结果' },
    { name: '{remarks}', description: '执行备注' },
    { name: '{executor}', description: '执行人' },
    { name: '{operator_name}', description: '执行人（别名）' },
    { name: '{time}', description: '执行时间' }
  ],
  report: [
    { name: '{report_name}', description: '报告名称' },
    { name: '{total_cases}', description: '总用例数' },
    { name: '{passed}', description: '通过数量' },
    { name: '{failed}', description: '失败数量' },
    { name: '{pass_rate}', description: '通过率' },
    { name: '{fail_rate}', description: '失败率' },
    { name: '{time}', description: '生成时间' },
    { name: '{operator}', description: '操作人' },
    { name: '{reviewer}', description: '审核人' },
    { name: '{review_time}', description: '审核时间' },
    { name: '{review_comment}', description: '审核意见' }
  ],
  system: [
    { name: '{title}', description: '通知标题' },
    { name: '{content}', description: '通知内容' },
    { name: '{start_time}', description: '开始时间' },
    { name: '{end_time}', description: '结束时间' },
    { name: '{reason}', description: '原因' },
    { name: '{feature_name}', description: '功能名称' },
    { name: '{description}', description: '功能描述' },
    { name: '{version}', description: '版本号' },
    { name: '{changelog}', description: '更新日志' },
    { name: '{backup_time}', description: '备份时间' },
    { name: '{status}', description: '状态' },
    { name: '{days_remaining}', description: '剩余天数' },
    { name: '{permission_name}', description: '权限名称' }
  ]
}

// 通用变量 - 始终显示
const commonVariables = [
  { name: '{plan_name}', description: '计划名称' },
  { name: '{operator}', description: '操作人' },
  { name: '{operator_name}', description: '操作人' },
  { name: '{start_time}', description: '开始时间' },
  { name: '{end_time}', description: '结束时间' },
  { name: '{executors}', description: '执行人列表' },
  { name: '{reviewer}', description: '审核人' },
  { name: '{report_name}', description: '报告名称' },
  { name: '{case_name}', description: '用例名称' },
  { name: '{action}', description: '操作类型' },
  { name: '{result}', description: '执行结果' },
  { name: '{time}', description: '时间' }
]

const form = reactive({
  id: null,
  name: '',
  notification_type: '',
  title_template: '',
  content_template: ''
})

const rules = {
  name: [
    { required: true, message: t('notificationTemplate.templateNameRequired'), trigger: 'blur' }
  ],
  notification_type: [
    { required: true, message: t('notificationTemplate.notificationTypeRequired'), trigger: 'change' }
  ],
  title_template: [
    { required: true, message: t('notificationTemplate.titleTemplateRequired'), trigger: 'blur' }
  ],
  content_template: [
    { required: true, message: t('notificationTemplate.contentTemplateRequired'), trigger: 'blur' }
  ]
}

// 当前显示的变量：类型变量 + 通用变量
const currentVariables = computed(() => {
  const typeVars = availableVariables.value || []
  const common = commonVariables || []
  // 合并并去重（按name）
  const merged = [...typeVars]
  for (const v of common) {
    if (!merged.some(m => m.name === v.name)) {
      merged.push(v)
    }
  }
  return merged
})

const getTypeTagColor = (type) => {
  const colorMap = {
    'testcase': 'primary',
    'testplan': 'success',
    'execution': 'warning',
    'report': 'danger',
    'system': 'info'
  }
  return colorMap[type] || 'info'
}

const getTypeLabel = (type) => {
  const labelMap = {
    'testcase': t('notification.types.testcase'),
    'testplan': t('notification.types.testplan'),
    'execution': t('notification.types.execution'),
    'report': t('notification.types.report'),
    'system': '系统通知'
  }
  return labelMap[type] || type
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const parseVariables = (variablesStr) => {
  if (!variablesStr) return []
  try {
    return JSON.parse(variablesStr)
  } catch {
    return []
  }
}

const loadData = async () => {
  loadingStore.showLoading()
  loading.value = true
  try {
    const response = await getNotificationTemplates({
      page: currentPage.value,
      size: pageSize.value,
      search: searchText.value,
      notification_type: filterType.value
    })
    tableData.value = response.data.records
    total.value = response.data.total
  } catch (error) {
    ElMessage.error(t('notificationTemplate.loadFailed'))
  } finally {
    loadingStore.hideLoading()
    loading.value = false
  }
}

const handleSearch = () => {
  currentPage.value = 1
  loadData()
}

const handleSizeChange = async () => {
  currentPage.value = 1
  await loadData()
  await nextTick()
  scrollToTop()
}

const handleCurrentChange = async () => {
  await loadData()
  await nextTick()
  scrollToTop()
}

const handleCreate = () => {
  isEdit.value = false
  dialogTitle.value = t('notificationTemplate.createTemplate')
  form.id = null
  form.name = ''
  form.notification_type = ''
  form.title_template = ''
  form.content_template = ''
  availableVariables.value = []
  dialogVisible.value = true
  lastFocusedInput.value = 'title'
  // 自动聚焦到类型选择框
  nextTick(() => {
    const typeSelect = document.querySelector('.el-form-item__content .el-select input')
    if (typeSelect) typeSelect.focus()
  })
}

const handleEdit = (row) => {
  isEdit.value = true
  dialogTitle.value = t('notificationTemplate.editTemplate')
  form.id = row.id
  form.name = row.name
  form.notification_type = row.notification_type
  form.title_template = row.title_template
  form.content_template = row.content_template
  lastFocusedInput.value = 'title'
  dialogVisible.value = true
  // 根据类型显示变量
  updateAvailableVariables(row.notification_type)
}

const handleTypeChange = (type) => {
  updateAvailableVariables(type)
}

const updateAvailableVariables = (type) => {
  if (type && variablesByType[type]) {
    availableVariables.value = variablesByType[type]
  } else {
    availableVariables.value = []
  }
}

const getTemplateVariables = (type) => {
  return variablesByType[type] || []
}

// 插入变量到输入框
const insertVariable = (variableName) => {
  if (lastFocusedInput.value === 'title') {
    // 插入到标题模板
    form.title_template += variableName
  } else {
    // 插入到内容模板
    form.content_template += variableName
  }
}

const handleView = (row) => {
  currentTemplate.value = row
  viewDialogVisible.value = true
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        const data = {
          name: form.name,
          notification_type: form.notification_type,
          title_template: form.title_template,
          content_template: form.content_template,
          is_system: false
        }
        
        if (isEdit.value) {
          await updateNotificationTemplate(form.id, data)
          ElMessage.success(t('notificationTemplate.updateSuccess'))
        } else {
          await createNotificationTemplate(data)
          ElMessage.success(t('notificationTemplate.createSuccess'))
        }
        
        dialogVisible.value = false
        loadData()
      } catch (error) {
        const errorMsg = error.response?.data?.detail || t('notificationTemplate.operationFailed')
        ElMessage.error(errorMsg)
      } finally {
        submitting.value = false
      }
    }
  })
}

const handleDelete = (row) => {
  ElMessageBox.confirm(
    t('notificationTemplate.deleteConfirm', { name: row.name }),
    t('common.warning'),
    {
      confirmButtonText: t('common.confirm'),
      cancelButtonText: t('common.cancel'),
      type: 'warning'
    }
  ).then(async () => {
    try {
      await deleteNotificationTemplate(row.id)
      ElMessage.success(t('notificationTemplate.deleteSuccess'))
      loadData()
    } catch (error) {
      const errorMsg = error.response?.data?.detail || t('notificationTemplate.deleteFailed')
      ElMessage.error(errorMsg)
    }
  }).catch(() => {})
}

onMounted(() => {
  loadData()
  bindTableHeight()
})
onBeforeUnmount(() => {
  unbindTableHeight()
})
</script>

<style scoped>
.notification-template-management {
  padding: 20px;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.notification-template-management :deep(.el-card__body) {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title {
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
}

.search-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  flex-shrink: 0;
}

.pagination {
  flex-shrink: 0;
  display: flex;
  justify-content: flex-end;
}

.template-hint {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.template-detail {
  padding: 10px 0;
}

.detail-item {
  margin-bottom: 20px;
}

.detail-label {
  font-weight: 600;
  color: #606266;
  margin-bottom: 8px;
}

.detail-value {
  color: #303133;
}

.template-code {
  background: rgba(139, 154, 238, 0.04);
  border-radius: 4px;
  padding: 12px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.6;
}

.template-code pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.variables-container {
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 12px;
  background: #f5f7fa;
}

.variable-item {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  padding: 6px 8px;
  background: white;
  border-radius: 4px;
  transition: all 0.2s;
  cursor: pointer;
}

.variable-item:hover {
  background: #ecf5ff;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  transform: translateX(2px);
}

.variable-item:last-child {
  margin-bottom: 0;
}

.variable-tag {
  min-width: 150px;
  font-family: 'Courier New', monospace;
  font-weight: 600;
  margin-right: 12px;
}

.variable-desc {
  color: #606266;
  font-size: 13px;
  flex: 1;
}

.variable-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
  padding: 8px 12px;
  background: #e6f7ff;
  border-radius: 4px;
  color: #1890ff;
  font-size: 12px;
}

.variable-hint .el-icon {
  font-size: 14px;
}
</style>
