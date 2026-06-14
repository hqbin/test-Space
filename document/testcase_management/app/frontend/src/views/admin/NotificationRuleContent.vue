<template>
  <div class="notification-rule-content">
    <!-- 工具栏 -->
    <div class="table-header">
      <div class="header-left">
        <div class="action-buttons">
          <el-button v-if="hasButton('notificationManagement', 'createRule')" type="primary" @click="handleCreate">
            <el-icon><Plus /></el-icon>
            {{ $t('notificationRule.createRule') }}
          </el-button>
        </div>
      </div>
      <div class="header-right">
        <el-select
          v-model="filterType"
          :placeholder="$t('notificationRule.filterByType')"
          clearable
          style="width: 150px"
          @change="handleSearch"
        >
          <el-option :label="$t('notificationRule.allTypes')" value="" />
          <el-option :label="$t('notification.types.testcase')" value="testcase" />
          <el-option :label="$t('notification.types.testplan')" value="testplan" />
          <el-option :label="$t('notification.types.execution')" value="execution" />
          <el-option :label="$t('notification.types.report')" value="report" />
          <el-option label="系统通知" value="system" />
        </el-select>
        <el-input
          v-model="searchText"
          :placeholder="$t('notificationRule.searchPlaceholder')"
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
          <el-table-column prop="name" :label="$t('notificationRule.ruleName')" min-width="180" />
          <el-table-column prop="notification_type" :label="$t('notificationRule.notificationType')" width="120" align="center">
            <template #default="{ row }">
              <el-tag :type="getTypeTagColor(row.notification_type)" size="small">
                {{ getTypeLabel(row.notification_type) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="event_type" :label="$t('notificationRule.eventType')" width="120" align="center">
            <template #default="{ row }">
              <el-tag size="small" effect="light">
                {{ getEventLabel(row.event_type) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="recipient_type" :label="$t('notificationRule.recipientType')" width="120" align="center">
            <template #default="{ row }">
              <el-tag :type="getRecipientTypeTag(row.recipient_type)" size="small">
                {{ getRecipientTypeLabel(row.recipient_type) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="notification_method" label="通知方式" width="130" align="center">
            <template #default="{ row }">
              <el-tag :type="getMethodTagColor(row.notification_method)" size="small">
                {{ getMethodLabel(row.notification_method) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="template_id" label="通知模板" width="150" align="center">
            <template #default="{ row }">
              <span v-if="row.template_id">{{ getTemplateName(row.template_id) }}</span>
              <span v-else style="color: #94a3b8;">系统默认</span>
            </template>
          </el-table-column>
          <el-table-column prop="description" :label="$t('common.description')" min-width="200" :show-overflow-tooltip="{ showAfter: 500 }" />
          <el-table-column prop="is_active" :label="$t('common.status')" width="100" align="center">
            <template #default="{ row }">
              <el-switch v-model="row.is_active" @change="handleStatusChange(row)" />
            </template>
          </el-table-column>
          <el-table-column prop="created_at" :label="$t('common.createdAt')" width="180">
            <template #default="{ row }">
              {{ formatDate(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column :label="$t('common.operation')" width="150">
            <template #default="{ row }">
              <el-button v-if="hasButton('notificationManagement', 'editRule')" link type="primary" @click="handleEdit(row)">
                <el-icon><Edit /></el-icon>
              </el-button>
              <el-button v-if="hasButton('notificationManagement', 'deleteRule')" link type="danger" @click="handleDelete(row)">
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
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="700px" :close-on-click-modal="false">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="120px">
        <el-form-item :label="$t('notificationRule.ruleName')" prop="name">
          <el-input v-model="form.name" :placeholder="$t('notificationRule.inputRuleName')" />
        </el-form-item>
        <el-form-item :label="$t('common.description')" prop="description">
          <el-input v-model="form.description" type="textarea" :rows="3" :placeholder="$t('notificationRule.inputDescription')" />
        </el-form-item>
        <el-form-item :label="$t('notificationRule.notificationType')" prop="notification_type">
          <el-select v-model="form.notification_type" :placeholder="$t('notificationRule.selectNotificationType')" style="width: 100%">
            <el-option :label="$t('notification.types.testcase')" value="testcase" />
            <el-option :label="$t('notification.types.testplan')" value="testplan" />
            <el-option :label="$t('notification.types.execution')" value="execution" />
            <el-option :label="$t('notification.types.report')" value="report" />
            <el-option label="系统通知" value="system" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="form.notification_type === 'testcase'" label="用例库" prop="watch_project_id">
          <el-tree-select
            v-model="form.watch_project_id"
            :data="allProjects"
            :props="{ label: 'name', children: 'children', value: 'id' }"
            placeholder="请选择用例库"
            check-strictly
            filterable
            style="width: 100%"
          />
          <div style="color: #909399; font-size: 12px; margin-top: 4px;">选择后仅该用例库下的用例变更会触发通知</div>
        </el-form-item>
        <el-form-item :label="$t('notificationRule.eventType')" prop="event_type">
          <el-select v-model="form.event_type" :placeholder="$t('notificationRule.selectEventType')" style="width: 100%">
            <template v-if="form.notification_type === 'system'">
              <el-option label="系统维护" value="maintenance" />
              <el-option label="新功能上线" value="feature_release" />
              <el-option label="密码过期提醒" value="password_expiry" />
              <el-option label="权限变更" value="permission_changed" />
              <el-option label="数据备份完成" value="backup_completed" />
              <el-option label="版本更新" value="version_update" />
              <el-option label="每日任务提醒" value="daily_reminder" />
            </template>
            <template v-else-if="form.notification_type === 'testcase'">
              <el-option :label="$t('notification.events.created')" value="created" />
              <el-option :label="$t('notification.events.updated')" value="updated" />
              <el-option :label="$t('notification.events.deleted')" value="deleted" />
              <el-option :label="$t('notification.events.statusChanged')" value="status_changed" />
              <el-option label="评审邀请" value="review_invitation" />
              <el-option label="提交评审" value="review_submitted" />
              <el-option label="评审通过" value="review_approved" />
              <el-option label="评审拒绝" value="review_rejected" />
              <el-option label="评审意见" value="review_commented" />
            </template>
            <template v-else-if="form.notification_type === 'testplan'">
              <el-option :label="$t('notification.events.created')" value="created" />
              <el-option :label="$t('notification.events.updated')" value="updated" />
              <el-option label="提交审核" value="submitted_for_review" />
              <el-option label="撤回审核" value="review_withdrawn" />
            </template>
            <template v-else-if="form.notification_type === 'report'">
              <el-option :label="$t('notification.events.generated')" value="generated" />
              <el-option :label="$t('notification.events.alert')" value="alert" />
              <el-option label="审核通过" value="approved" />
              <el-option label="审核拒绝" value="rejected" />
            </template>
            <template v-else-if="form.notification_type === 'execution'">
              <el-option label="执行结果更新" value="result_updated" />
            </template>
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('notificationRule.recipientType')" prop="recipient_type">
          <el-select v-model="form.recipient_type" :placeholder="$t('notificationRule.selectRecipientType')" style="width: 100%">
            <el-option :label="$t('notificationRule.recipientTypes.role')" value="role" />
            <el-option :label="$t('notificationRule.recipientTypes.user')" value="user" />
            <el-option :label="$t('notificationRule.recipientTypes.mixed')" value="mixed" />
          </el-select>
        </el-form-item>
        <el-form-item label="通知模板">
          <el-select v-model="form.template_id" placeholder="选择通知模板（可选）" style="width: 100%" clearable>
            <el-option v-for="tpl in filteredTemplates" :key="tpl.id" :label="tpl.name" :value="tpl.id" />
          </el-select>
          <div style="font-size: 12px; color: #94a3b8; margin-top: 4px;">选择模板后，通知内容将按模板格式发送；不选则使用系统默认内容</div>
        </el-form-item>
        <el-form-item label="通知方式" prop="notification_method">
          <el-radio-group v-model="form.notification_method">
            <el-radio value="internal">仅平台内</el-radio>
            <el-radio value="dingtalk">仅钉钉</el-radio>
            <el-radio value="both">平台内+钉钉</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="form.recipient_type === 'role' || form.recipient_type === 'mixed'" :label="$t('notificationRule.recipientRoles')">
          <el-select v-model="form.recipient_roles" multiple :placeholder="$t('notificationRule.selectRoles')" style="width: 100%">
            <el-option v-for="role in allRoles" :key="role.id" :label="role.name" :value="role.id" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="form.recipient_type === 'user' || form.recipient_type === 'mixed'" :label="$t('notificationRule.recipientUsers')">
          <el-select v-model="form.recipient_users" multiple :placeholder="$t('notificationRule.selectUsers')" style="width: 100%" filterable>
            <el-option v-for="user in allUsers" :key="user.id" :label="user.username" :value="user.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('common.status')" prop="is_active">
          <el-radio-group v-model="form.is_active">
            <el-radio :label="true">{{ $t('common.enabled') }}</el-radio>
            <el-radio :label="false">{{ $t('common.disabled') }}</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">{{ $t('common.confirm') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Edit, Delete } from '@element-plus/icons-vue'
import { getNotificationRules, createNotificationRule, updateNotificationRule, deleteNotificationRule, getNotificationTemplates } from '@/api/notification'
import { getRoles } from '@/api/role'
import { getUsers } from '@/api/user'
import { getProjectTree } from '@/api/project'
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

const allRoles = ref([])
const allUsers = ref([])
const allTemplates = ref([])
const allProjects = ref([])

const form = reactive({
  id: null,
  name: '',
  description: '',
  notification_type: '',
  event_type: '',
  recipient_type: '',
  recipient_roles: [],
  recipient_users: [],
  notification_method: 'internal',
  template_id: null,
  watch_project_id: null,
  is_active: true
})

const rules = {
  name: [{ required: true, message: t('notificationRule.ruleNameRequired'), trigger: 'blur' }],
  notification_type: [{ required: true, message: t('notificationRule.notificationTypeRequired'), trigger: 'change' }],
  event_type: [{ required: true, message: t('notificationRule.eventTypeRequired'), trigger: 'change' }],
  recipient_type: [{ required: true, message: t('notificationRule.recipientTypeRequired'), trigger: 'change' }],
  watch_project_id: [{ required: true, validator: (rule, value, callback) => { if (form.notification_type === 'testcase' && !value) { callback(new Error('请选择用例库')) } else { callback() } }, trigger: 'change' }]
}

const getTypeTagColor = (type) => {
  const colorMap = { 'testcase': 'primary', 'testplan': 'success', 'execution': 'warning', 'report': 'danger', 'system': 'info' }
  return colorMap[type] || 'info'
}

const getTypeLabel = (type) => {
  const labelMap = { 'testcase': t('notification.types.testcase'), 'testplan': t('notification.types.testplan'), 'execution': t('notification.types.execution'), 'report': t('notification.types.report'), 'system': '系统通知' }
  return labelMap[type] || type
}

const getEventLabel = (event) => {
  const systemEvents = { 'maintenance': '系统维护', 'feature_release': '新功能上线', 'password_expiry': '密码过期提醒', 'permission_changed': '权限变更', 'backup_completed': '数据备份完成', 'version_update': '版本更新', 'daily_reminder': '每日任务提醒', 'user_registration': '用户注册审核' }
  const labelMap = { 'created': t('notification.events.created'), 'updated': t('notification.events.updated'), 'deleted': t('notification.events.deleted'), 'status_changed': t('notification.events.statusChanged'), 'result_updated': t('notification.events.resultUpdated'), 'generated': t('notification.events.generated'), 'alert': t('notification.events.alert'), 'submitted_for_review': '提交审核', 'review_withdrawn': '撤回审核', 'approved': '审核通过', 'rejected': '审核拒绝', 'review_invitation': '评审邀请', 'review_submitted': '提交评审', 'review_approved': '评审通过', 'review_rejected': '评审拒绝', 'review_commented': '评审意见' }
  return systemEvents[event] || labelMap[event] || event
}

const getRecipientTypeTag = (type) => {
  const tagMap = { 'role': 'success', 'user': 'warning', 'mixed': 'primary' }
  return tagMap[type] || 'info'
}

const getRecipientTypeLabel = (type) => {
  const labelMap = { 'role': t('notificationRule.recipientTypes.role'), 'user': t('notificationRule.recipientTypes.user'), 'mixed': t('notificationRule.recipientTypes.mixed') }
  return labelMap[type] || type
}

const getMethodTagColor = (method) => {
  const colorMap = { 'internal': '', 'dingtalk': 'warning', 'both': 'success' }
  return colorMap[method] || 'info'
}

const getMethodLabel = (method) => {
  const labelMap = { 'internal': '仅平台内', 'dingtalk': '仅钉钉', 'both': '平台内+钉钉' }
  return labelMap[method] || '仅平台内'
}

const filteredTemplates = computed(() => {
  if (!form.notification_type) return allTemplates.value
  return allTemplates.value.filter(t => t.notification_type === form.notification_type)
})

const getTemplateName = (templateId) => {
  const tpl = allTemplates.value.find(t => t.id === templateId)
  return tpl ? tpl.name : `模板#${templateId}`
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

const loadData = async () => {
  try {
    const response = await getNotificationRules({ page: currentPage.value, size: pageSize.value, search: searchText.value, notification_type: filterType.value })
    tableData.value = response.data.records
    total.value = response.data.total
  } catch (error) {
    ElMessage.error(t('notificationRule.loadFailed'))
  }
}

const handleSearch = () => { currentPage.value = 1; loadData() }
const handleSizeChange = () => { currentPage.value = 1; loadData() }
const handleCurrentChange = () => { loadData() }

const handleCreate = () => {
  isEdit.value = false
  dialogTitle.value = t('notificationRule.createRule')
  Object.assign(form, { id: null, name: '', description: '', notification_type: '', event_type: '', recipient_type: '', recipient_roles: [], recipient_users: [], notification_method: 'internal', template_id: null, watch_project_id: null, is_active: true })
  dialogVisible.value = true
}

const handleEdit = (row) => {
  isEdit.value = true
  dialogTitle.value = t('notificationRule.editRule')
  Object.assign(form, { id: row.id, name: row.name, description: row.description, notification_type: row.notification_type, event_type: row.event_type, recipient_type: row.recipient_type, recipient_roles: row.recipient_roles ? JSON.parse(row.recipient_roles) : [], recipient_users: row.recipient_users ? JSON.parse(row.recipient_users) : [], notification_method: row.notification_method || 'internal', template_id: row.template_id || null, watch_project_id: null, is_active: row.is_active })
  // 从 trigger_condition 中恢复 watch_project_id
  if (row.trigger_condition) {
    try { const cond = JSON.parse(row.trigger_condition); form.watch_project_id = cond.project_id || null } catch { form.watch_project_id = null }
  }
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        const data = { name: form.name, description: form.description, notification_type: form.notification_type, event_type: form.event_type, recipient_type: form.recipient_type, recipient_roles: JSON.stringify(form.recipient_roles), recipient_users: JSON.stringify(form.recipient_users), notification_method: form.notification_method, template_id: form.template_id || null, is_active: form.is_active, trigger_condition: form.notification_type === 'testcase' && form.watch_project_id ? JSON.stringify({ project_id: form.watch_project_id }) : null }
        if (isEdit.value) { await updateNotificationRule(form.id, data); ElMessage.success(t('notificationRule.updateSuccess')) }
        else { await createNotificationRule(data); ElMessage.success(t('notificationRule.createSuccess')) }
        dialogVisible.value = false
        loadData()
      } catch (error) { ElMessage.error(error.response?.data?.detail || t('notificationRule.operationFailed')) }
      finally { submitting.value = false }
    }
  })
}

const handleStatusChange = async (row) => {
  try { await updateNotificationRule(row.id, { is_active: row.is_active }); ElMessage.success(t('notificationRule.statusUpdateSuccess')) }
  catch (error) { row.is_active = !row.is_active; ElMessage.error(error.response?.data?.detail || t('notificationRule.statusUpdateFailed')) }
}

const handleDelete = (row) => {
  ElMessageBox.confirm(t('notificationRule.deleteConfirm', { name: row.name }), t('common.warning'), { confirmButtonText: t('common.confirm'), cancelButtonText: t('common.cancel'), type: 'warning' })
    .then(async () => { await deleteNotificationRule(row.id); ElMessage.success(t('notificationRule.deleteSuccess')); loadData() })
    .catch(() => {})
}

const loadRoles = async () => { try { const response = await getRoles({ page: 1, size: 1000 }); allRoles.value = response.data.records || [] } catch (error) { console.error('加载角色列表失败:', error) } }
const loadUsers = async () => { try { const response = await getUsers({ page: 1, size: 1000 }); allUsers.value = response.data.records || [] } catch (error) { console.error('加载用户列表失败:', error) } }
const loadTemplates = async () => { try { const response = await getNotificationTemplates({ page: 1, size: 1000 }); allTemplates.value = response.data.records || [] } catch (error) { console.error('加载模板列表失败:', error) } }
const loadProjects = async () => { try { const response = await getProjectTree(); allProjects.value = response.data || [] } catch (error) { console.error('加载项目列表失败:', error) } }

watch(() => form.notification_type, (newType, oldType) => { if (newType !== oldType && !isEdit.value) { form.event_type = ''; form.template_id = null; if (newType !== 'testcase') form.watch_project_id = null } })

onMounted(() => { loadData(); loadRoles(); loadUsers(); loadTemplates(); loadProjects(); bindTableHeight() })
onBeforeUnmount(() => { unbindTableHeight() })
</script>

<style scoped>
.notification-rule-content { display: flex; flex-direction: column; height: 100%; }

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

/* Switch */
:deep(.el-switch) { --el-switch-on-color: #4f46e5; --el-switch-off-color: #cbd5e1; }

/* 对话框 */
:deep(.el-dialog) { border-radius: 16px; overflow: hidden; }
:deep(.el-dialog__header) { padding: 20px 24px 16px; border-bottom: 1px solid #e2e8f0; margin-right: 0; }
:deep(.el-dialog__title) { font-size: 18px; font-weight: 600; color: #0f172a; }
:deep(.el-dialog__body) { padding: 24px; }
:deep(.el-dialog__footer) { padding: 16px 24px; border-top: 1px solid #e2e8f0; }
:deep(.el-form-item__label) { font-weight: 500; color: #334155; font-size: 14px; }
:deep(.el-input__wrapper), :deep(.el-select) { border-radius: 8px; }
</style>
