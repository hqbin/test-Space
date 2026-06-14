<template>
  <div class="notification-template-content">
    <!-- 工具栏 -->
    <div class="table-header">
      <div class="header-left">
        <div class="action-buttons">
          <el-button v-if="hasButton('notificationManagement', 'createTemplate')" type="primary" @click="handleCreate">
            <el-icon><Plus /></el-icon>
            {{ $t('notificationTemplate.createTemplate') }}
          </el-button>
        </div>
      </div>
      <div class="header-right">
        <el-select
          v-model="filterType"
          :placeholder="$t('notificationTemplate.filterByType')"
          clearable
          style="width: 150px"
          @change="handleSearch"
        >
          <el-option :label="$t('notificationTemplate.allTypes')" value="" />
          <el-option :label="$t('notification.types.testcase')" value="testcase" />
          <el-option :label="$t('notification.types.testplan')" value="testplan" />
          <el-option :label="$t('notification.types.report')" value="report" />
          <el-option label="系统通知" value="system" />
        </el-select>
        <el-input
          v-model="searchText"
          :placeholder="$t('notificationTemplate.searchPlaceholder')"
          clearable
          style="width: 250px"
          size="large"
          @clear="handleSearch"
          @keyup.enter="handleSearch"
        >
          <template #suffix>
            <el-icon class="el-input__icon" style="cursor: pointer;" @click="handleSearch">
              <Search />
            </el-icon>
          </template>
        </el-input>
      </div>
    </div>

    <!-- 表格 -->
    <div class="table-wrapper">
      <div class="table-container" ref="tableContainerRef">
        <el-table
          ref="tableRef"
          :data="tableData"
          style="width: 100%"
          :height="tableHeight"
          :header-cell-style="{ background: '#f8fafc', color: '#64748b', fontWeight: '500', fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.05em' }"
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
          <el-table-column :label="$t('common.operation')" width="180">
            <template #default="{ row }">
              <el-button link type="primary" @click="handleView(row)">
                <el-icon><View /></el-icon>
              </el-button>
              <el-button v-if="hasButton('notificationManagement', 'editTemplate')" link type="primary" @click="handleEdit(row)">
                <el-icon><Edit /></el-icon>
              </el-button>
              <el-button v-if="!row.is_system && hasButton('notificationManagement', 'deleteTemplate')" link type="danger" @click="handleDelete(row)">
                <el-icon><Delete /></el-icon>
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <!-- 分页 -->
    <div class="pagination-container">
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

    <!-- 创建/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="800px" :close-on-click-modal="false">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="120px">
        <el-form-item :label="$t('notificationTemplate.templateName')" prop="name">
          <el-input v-model="form.name" :placeholder="$t('notificationTemplate.inputTemplateName')" />
        </el-form-item>
        <el-form-item :label="$t('notificationTemplate.notificationType')" prop="notification_type">
          <el-select v-model="form.notification_type" :placeholder="$t('notificationTemplate.selectNotificationType')" style="width: 100%" @change="handleTypeChange">
            <el-option :label="$t('notification.types.testcase')" value="testcase" />
            <el-option :label="$t('notification.types.testplan')" value="testplan" />
            <el-option :label="$t('notification.types.report')" value="report" />
            <el-option label="系统通知" value="system" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('notificationTemplate.titleTemplate')" prop="title_template">
          <el-input v-model="form.title_template" :placeholder="$t('notificationTemplate.inputTitleTemplate')" @focus="lastFocusedInput = 'title'" />
          <div class="template-hint">{{ $t('notificationTemplate.titleTemplateHint') }}</div>
        </el-form-item>
        <el-form-item :label="$t('notificationTemplate.contentTemplate')" prop="content_template">
          <el-input v-model="form.content_template" type="textarea" :rows="8" :placeholder="$t('notificationTemplate.inputContentTemplate')" @focus="lastFocusedInput = 'content'" />
          <div class="template-hint">{{ $t('notificationTemplate.contentTemplateHint') }}</div>
        </el-form-item>
        <el-form-item :label="$t('notificationTemplate.availableVariables')">
          <div class="variables-container">
            <div v-for="variable in availableVariables" :key="variable.name" class="variable-item" @click="insertVariable(variable.name)">
              <el-tag size="small" class="variable-tag">{{ variable.name }}</el-tag>
              <span class="variable-desc">{{ variable.description }}</span>
            </div>
          </div>
          <div class="variable-hint">
            <el-icon><InfoFilled /></el-icon>
            <span>点击变量可插入到光标位置</span>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">{{ $t('common.confirm') }}</el-button>
      </template>
    </el-dialog>

    <!-- 查看对话框 -->
    <el-dialog v-model="viewDialogVisible" :title="$t('notificationTemplate.templateDetail')" width="800px">
      <div v-if="currentTemplate" class="template-detail">
        <div class="detail-item">
          <div class="detail-label">{{ $t('notificationTemplate.templateName') }}:</div>
          <div class="detail-value">{{ currentTemplate.name }}</div>
        </div>
        <div class="detail-item">
          <div class="detail-label">{{ $t('notificationTemplate.notificationType') }}:</div>
          <div class="detail-value">
            <el-tag :type="getTypeTagColor(currentTemplate.notification_type)" size="small">{{ getTypeLabel(currentTemplate.notification_type) }}</el-tag>
          </div>
        </div>
        <div class="detail-item">
          <div class="detail-label">{{ $t('notificationTemplate.titleTemplate') }}:</div>
          <div class="detail-value template-code">{{ currentTemplate.title_template }}</div>
        </div>
        <div class="detail-item">
          <div class="detail-label">{{ $t('notificationTemplate.contentTemplate') }}:</div>
          <div class="detail-value template-code"><pre>{{ currentTemplate.content_template }}</pre></div>
        </div>
      </div>
      <template #footer>
        <el-button @click="viewDialogVisible = false">{{ $t('common.close') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Edit, Delete, View, InfoFilled } from '@element-plus/icons-vue'
import { getNotificationTemplates, createNotificationTemplate, updateNotificationTemplate, deleteNotificationTemplate } from '@/api/notification'
import { useTableHeight } from '@/composables/useTableHeight'
import { useUserRole } from '../../composables/useUserRole'

const { t } = useI18n()
const { hasButton } = useUserRole()
const { tableContainerRef, tableHeight, bindTableHeight, unbindTableHeight } = useTableHeight()
const tableRef = ref(null)

const tableData = ref([])
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const searchText = ref('')
const filterType = ref('')

const dialogVisible = ref(false)
const dialogTitle = ref('')
const isEdit = ref(false)
const submitting = ref(false)
const formRef = ref(null)

const viewDialogVisible = ref(false)
const currentTemplate = ref(null)
const lastFocusedInput = ref('title')
const availableVariables = ref([])

const variablesByType = {
  testcase: [
    { name: '{case_id}', description: '用例ID' }, { name: '{case_name}', description: '用例名称' }, { name: '{action}', description: '操作类型' },
    { name: '{operator}', description: '操作人姓名' }, { name: '{old_status}', description: '原状态' }, { name: '{new_status}', description: '新状态' },
    { name: '{changes}', description: '变更内容描述' }, { name: '{time}', description: '操作时间' }
  ],
  testplan: [
    { name: '{plan_name}', description: '测试计划名称' }, { name: '{action}', description: '操作类型' }, { name: '{start_time}', description: '开始时间' },
    { name: '{end_time}', description: '结束时间' }, { name: '{executors}', description: '执行人列表' }, { name: '{reviewer}', description: '审核人' },
    { name: '{operator}', description: '操作人姓名' }
  ],
  execution: [
    { name: '{case_name}', description: '用例名称' }, { name: '{result}', description: '执行结果' }, { name: '{remarks}', description: '执行备注' },
    { name: '{executor}', description: '执行人姓名' }, { name: '{time}', description: '执行时间' }
  ],
  report: [
    { name: '{report_name}', description: '报告名称' }, { name: '{total_cases}', description: '总用例数' }, { name: '{passed}', description: '通过数量' },
    { name: '{failed}', description: '失败数量' }, { name: '{pass_rate}', description: '通过率' }, { name: '{fail_rate}', description: '失败率' },
    { name: '{operator}', description: '操作人姓名' }, { name: '{time}', description: '生成时间' }
  ],
  system: [
    { name: '{title}', description: '通知标题' }, { name: '{content}', description: '通知内容' }, { name: '{start_time}', description: '开始时间' },
    { name: '{end_time}', description: '结束时间' }, { name: '{version}', description: '版本号' }
  ]
}

const form = reactive({ id: null, name: '', notification_type: '', title_template: '', content_template: '' })

const rules = {
  name: [{ required: true, message: t('notificationTemplate.templateNameRequired'), trigger: 'blur' }],
  notification_type: [{ required: true, message: t('notificationTemplate.notificationTypeRequired'), trigger: 'change' }],
  title_template: [{ required: true, message: t('notificationTemplate.titleTemplateRequired'), trigger: 'blur' }],
  content_template: [{ required: true, message: t('notificationTemplate.contentTemplateRequired'), trigger: 'blur' }]
}

const getTypeTagColor = (type) => ({ 'testcase': 'primary', 'testplan': 'success', 'execution': 'warning', 'report': 'danger', 'system': 'info' }[type] || 'info')
const getTypeLabel = (type) => ({ 'testcase': t('notification.types.testcase'), 'testplan': t('notification.types.testplan'), 'execution': t('notification.types.execution'), 'report': t('notification.types.report'), 'system': '系统通知' }[type] || type)
const formatDate = (dateString) => dateString ? new Date(dateString).toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }) : '-'

const loadData = async () => {
  try {
    const response = await getNotificationTemplates({ page: currentPage.value, size: pageSize.value, search: searchText.value, notification_type: filterType.value })
    tableData.value = response.data.records
    total.value = response.data.total
  } catch (error) { ElMessage.error(t('notificationTemplate.loadFailed')) }
}

const handleSearch = () => { currentPage.value = 1; loadData() }
const handleSizeChange = () => { currentPage.value = 1; loadData() }
const handleCurrentChange = () => { loadData() }

const handleCreate = () => {
  isEdit.value = false
  dialogTitle.value = t('notificationTemplate.createTemplate')
  Object.assign(form, { id: null, name: '', notification_type: '', title_template: '', content_template: '' })
  availableVariables.value = []
  dialogVisible.value = true
}

const handleEdit = (row) => {
  isEdit.value = true
  dialogTitle.value = t('notificationTemplate.editTemplate')
  Object.assign(form, { id: row.id, name: row.name, notification_type: row.notification_type, title_template: row.title_template, content_template: row.content_template })
  updateAvailableVariables(row.notification_type)
  dialogVisible.value = true
}

const handleTypeChange = (type) => { updateAvailableVariables(type) }
const updateAvailableVariables = (type) => { availableVariables.value = type && variablesByType[type] ? variablesByType[type] : [] }
const insertVariable = (variableName) => { if (lastFocusedInput.value === 'title') form.title_template += variableName; else form.content_template += variableName }
const handleView = (row) => { currentTemplate.value = row; viewDialogVisible.value = true }

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        const data = { name: form.name, notification_type: form.notification_type, title_template: form.title_template, content_template: form.content_template, is_system: false }
        if (isEdit.value) { await updateNotificationTemplate(form.id, data); ElMessage.success(t('notificationTemplate.updateSuccess')) }
        else { await createNotificationTemplate(data); ElMessage.success(t('notificationTemplate.createSuccess')) }
        dialogVisible.value = false
        loadData()
      } catch (error) { ElMessage.error(error.response?.data?.detail || t('notificationTemplate.operationFailed')) }
      finally { submitting.value = false }
    }
  })
}

const handleDelete = (row) => {
  ElMessageBox.confirm(t('notificationTemplate.deleteConfirm', { name: row.name }), t('common.warning'), { confirmButtonText: t('common.confirm'), cancelButtonText: t('common.cancel'), type: 'warning' })
    .then(async () => { await deleteNotificationTemplate(row.id); ElMessage.success(t('notificationTemplate.deleteSuccess')); loadData() })
    .catch(() => {})
}

onMounted(() => { loadData(); bindTableHeight() })
onBeforeUnmount(() => { unbindTableHeight() })
</script>

<style scoped>
.notification-template-content { display: flex; flex-direction: column; height: 100%; }

/* 工具栏 */
.table-header {
  padding: 16px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #e2e8f0;
  flex-shrink: 0;
  background-color: rgba(248, 250, 252, 0.5);
  gap: 12px;
}
.header-left { display: flex; gap: 12px; align-items: center; flex-shrink: 0; }
.header-right { display: flex; gap: 12px; align-items: center; flex-shrink: 0; margin-left: auto; }
.header-right :deep(.el-input__wrapper) { height: 40px !important; min-height: 40px !important; padding: 1px 11px !important; box-sizing: border-box !important; display: flex !important; align-items: center !important; }
.header-right :deep(.el-input__inner) { height: 38px !important; line-height: 38px !important; }
.action-buttons { display: flex; gap: 8px; align-items: center; }
.action-buttons .el-button { border-radius: 8px !important; font-weight: 500 !important; height: 40px !important; padding: 0 18px !important; font-size: 14px !important; box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05) !important; }
.action-buttons .el-button--primary { background: #4f46e5 !important; border: none !important; }
.action-buttons .el-button--primary:hover { background: #4338ca !important; }

/* 表格 */
.table-wrapper { flex: 1; display: flex; flex-direction: column; min-height: 0; width: 100%; overflow: hidden; }
.table-wrapper .table-container { flex: 1; min-height: 0; overflow: hidden; }
.table-wrapper :deep(.el-table) { width: 100%; position: relative; }
.table-wrapper :deep(.el-table td.el-table__cell), .table-wrapper :deep(.el-table th.el-table__cell) { height: 48px !important; padding: 0 12px !important; }
.table-wrapper :deep(.el-table td.el-table__cell .cell), .table-wrapper :deep(.el-table th.el-table__cell .cell) { line-height: 48px; padding: 0; }
.table-wrapper :deep(.el-table__body-wrapper) { overflow-y: auto !important; overflow-x: auto !important; }
.table-wrapper :deep(.el-table__body-wrapper)::-webkit-scrollbar { height: 8px; width: 8px; }
.table-wrapper :deep(.el-table__body-wrapper)::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }
.table-wrapper :deep(.el-table__body-wrapper)::-webkit-scrollbar-track { background: #f1f5f9; }
.table-wrapper :deep(.el-table__header-wrapper) { overflow: hidden !important; position: relative; z-index: 10 !important; }

.table-wrapper :deep(.el-table__row:hover > td) { background: #f8fafc !important; }

/* 分页 */
.pagination-container { display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; background: #fff; flex-shrink: 0; border-top: 1px solid #e2e8f0; min-height: 56px; }
.pagination-container :deep(.el-pager li) { background: transparent; font-weight: 500; border-radius: 6px; min-width: 32px; height: 32px; }
.pagination-container :deep(.el-pager li.is-active) { background: #eef2ff; color: #4f46e5; font-weight: 600; }
.pagination-container :deep(.el-pager li:hover:not(.is-active)) { background: #f1f5f9; }
.pagination-container :deep(.el-pagination__total) { font-size: 14px; color: #64748b; }

/* 按钮 */
:deep(.el-button) { border-radius: 8px; font-weight: 500; transition: all 0.15s; }
:deep(.el-button:hover) { transform: none; box-shadow: none; }
:deep(.el-button--primary) { background: #4f46e5; border: none; box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05); }
:deep(.el-button--primary:hover) { background: #4338ca; }
:deep(.el-button--danger) { background: #ef4444; border: none; }
:deep(.el-button--danger:hover) { background: #dc2626; }

/* 对话框 */
:deep(.el-dialog) { border-radius: 16px; overflow: hidden; }
:deep(.el-dialog__header) { padding: 20px 24px 16px; border-bottom: 1px solid #e2e8f0; margin-right: 0; }
:deep(.el-dialog__title) { font-size: 18px; font-weight: 600; color: #0f172a; }
:deep(.el-dialog__body) { padding: 24px; }
:deep(.el-dialog__footer) { padding: 16px 24px; border-top: 1px solid #e2e8f0; }
:deep(.el-form-item__label) { font-weight: 500; color: #334155; font-size: 14px; }
:deep(.el-input__wrapper), :deep(.el-select) { border-radius: 8px; }

/* 模板相关 */
.template-hint { font-size: 12px; color: #94a3b8; margin-top: 4px; }
.template-detail { padding: 10px 0; }
.detail-item { margin-bottom: 20px; }
.detail-label { font-weight: 600; color: #334155; margin-bottom: 8px; }
.detail-value { color: #0f172a; }
.template-code { background: rgba(248, 250, 252, 0.8); border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; font-family: 'Courier New', monospace; font-size: 13px; }
.template-code pre { margin: 0; white-space: pre-wrap; word-wrap: break-word; }
.variables-container { max-height: 200px; overflow-y: auto; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; background: #f8fafc; }
.variable-item { display: flex; align-items: center; margin-bottom: 8px; padding: 6px 8px; background: white; border-radius: 6px; cursor: pointer; transition: all 0.2s; border: 1px solid #e2e8f0; }
.variable-item:hover { background: #eef2ff; border-color: #c7d2fe; }
.variable-item:last-child { margin-bottom: 0; }
.variable-tag { min-width: 120px; font-family: 'Courier New', monospace; margin-right: 12px; }
.variable-desc { color: #64748b; font-size: 13px; }
.variable-hint { display: flex; align-items: center; gap: 6px; margin-top: 8px; padding: 8px 12px; background: #eef2ff; border-radius: 8px; color: #4f46e5; font-size: 12px; }
</style>
