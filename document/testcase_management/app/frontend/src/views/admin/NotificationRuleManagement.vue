<template>
  <div class="notification-rule-management table-layout">
    <el-card class="table-layout" shadow="never">
      <template #header>
        <div class="card-header">
          <span class="title">{{ $t('notificationRule.title') }}</span>
          <el-button v-if="hasButton('notificationManagement', 'createRule')" type="primary" @click="handleCreate">
            <el-icon><Plus /></el-icon>
            {{ $t('notificationRule.createRule') }}
          </el-button>
        </div>
      </template>

      <!-- 搜索栏 -->
      <div class="search-bar">
        <el-input
          v-model="searchText"
          :placeholder="$t('notificationRule.searchPlaceholder')"
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
          :placeholder="$t('notificationRule.filterByType')"
          clearable
          style="width: 180px"
          @change="handleSearch"
        >
          <el-option :label="$t('notificationRule.allTypes')" value="" />
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
        <el-table-column prop="description" :label="$t('common.description')" min-width="200" :show-overflow-tooltip="{ showAfter: 500 }" />
        <el-table-column prop="is_active" :label="$t('common.status')" width="100" align="center">
          <template #default="{ row }">
            <el-switch
              v-model="row.is_active"
              @change="handleStatusChange(row)"
            />
          </template>
        </el-table-column>
        <el-table-column prop="created_at" :label="$t('common.createdAt')" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column :label="$t('common.operation')" width="200">
          <template #default="{ row }">
            <el-button v-if="hasButton('notificationManagement', 'editRule')" link type="primary" @click="handleEdit(row)">
              <el-icon><Edit /></el-icon>
              {{ $t('common.edit') }}
            </el-button>
            <el-button v-if="hasButton('notificationManagement', 'deleteRule')" link type="danger" @click="handleDelete(row)">
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
      width="700px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="120px"
      >
        <el-form-item :label="$t('notificationRule.ruleName')" prop="name">
          <el-input v-model="form.name" :placeholder="$t('notificationRule.inputRuleName')" />
        </el-form-item>
        <el-form-item :label="$t('common.description')" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            :placeholder="$t('notificationRule.inputDescription')"
          />
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
            <template v-else>
              <el-option :label="$t('notification.events.created')" value="created" />
              <el-option :label="$t('notification.events.updated')" value="updated" />
              <el-option :label="$t('notification.events.deleted')" value="deleted" />
              <el-option :label="$t('notification.events.statusChanged')" value="status_changed" />
              <el-option :label="$t('notification.events.resultUpdated')" value="result_updated" />
              <el-option :label="$t('notification.events.generated')" value="generated" />
              <el-option :label="$t('notification.events.alert')" value="alert" />
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
        <el-form-item v-if="form.recipient_type === 'role' || form.recipient_type === 'mixed'" :label="$t('notificationRule.recipientRoles')">
          <el-select v-model="form.recipient_roles" multiple :placeholder="$t('notificationRule.selectRoles')" style="width: 100%">
            <el-option
              v-for="role in allRoles"
              :key="role.id"
              :label="role.name"
              :value="role.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item v-if="form.recipient_type === 'user' || form.recipient_type === 'mixed'" :label="$t('notificationRule.recipientUsers')">
          <el-select v-model="form.recipient_users" multiple :placeholder="$t('notificationRule.selectUsers')" style="width: 100%" filterable>
            <el-option
              v-for="user in allUsers"
              :key="user.id"
              :label="user.username"
              :value="user.id"
            />
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
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          {{ $t('common.confirm') }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Edit, Delete } from '@element-plus/icons-vue'
import { getNotificationRules, createNotificationRule, updateNotificationRule, deleteNotificationRule } from '@/api/notification'
import { getRoles } from '@/api/role'
import { getUsers } from '@/api/user'
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
const { page: currentPage, size: pageSize, total } = usePagination('notificationRuleManagement', 10)
const searchText = ref('')
const filterType = ref('')

const dialogVisible = ref(false)
const dialogTitle = ref('')
const isEdit = ref(false)
const submitting = ref(false)
const formRef = ref(null)

const allRoles = ref([])
const allUsers = ref([])

const form = reactive({
  id: null,
  name: '',
  description: '',
  notification_type: '',
  event_type: '',
  recipient_type: '',
  recipient_roles: [],
  recipient_users: [],
  is_active: true
})

const rules = {
  name: [
    { required: true, message: t('notificationRule.ruleNameRequired'), trigger: 'blur' }
  ],
  notification_type: [
    { required: true, message: t('notificationRule.notificationTypeRequired'), trigger: 'change' }
  ],
  event_type: [
    { required: true, message: t('notificationRule.eventTypeRequired'), trigger: 'change' }
  ],
  recipient_type: [
    { required: true, message: t('notificationRule.recipientTypeRequired'), trigger: 'change' }
  ]
}

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

const getEventLabel = (event) => {
  // 系统通知事件类型
  const systemEvents = {
    'maintenance': '系统维护',
    'feature_release': '新功能上线',
    'password_expiry': '密码过期提醒',
    'permission_changed': '权限变更',
    'backup_completed': '数据备份完成',
    'version_update': '版本更新',
    'daily_reminder': '每日任务提醒',
    'user_registration': '用户注册审核'
  }
  
  // 评审相关事件类型
  const reviewEvents = {
    'review_submitted': '提交评审',
    'review_approved': '评审通过',
    'review_rejected': '评审拒绝',
    'review_commented': '评审意见'
  }
  
  // 其他通知事件类型
  const labelMap = {
    'created': t('notification.events.created'),
    'updated': t('notification.events.updated'),
    'deleted': t('notification.events.deleted'),
    'status_changed': t('notification.events.statusChanged'),
    'result_updated': t('notification.events.resultUpdated'),
    'generated': t('notification.events.generated'),
    'alert': t('notification.events.alert')
  }
  
  return systemEvents[event] || reviewEvents[event] || labelMap[event] || event
}

const getRecipientTypeTag = (type) => {
  const tagMap = {
    'role': 'success',
    'user': 'warning',
    'mixed': 'primary'
  }
  return tagMap[type] || 'info'
}

const getRecipientTypeLabel = (type) => {
  const labelMap = {
    'role': t('notificationRule.recipientTypes.role'),
    'user': t('notificationRule.recipientTypes.user'),
    'mixed': t('notificationRule.recipientTypes.mixed')
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

const loadData = async () => {
  loadingStore.showLoading()
  loading.value = true
  try {
    const response = await getNotificationRules({
      page: currentPage.value,
      size: pageSize.value,
      search: searchText.value,
      notification_type: filterType.value
    })
    tableData.value = response.data.records
    total.value = response.data.total
  } catch (error) {
    ElMessage.error(t('notificationRule.loadFailed'))
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
  dialogTitle.value = t('notificationRule.createRule')
  form.id = null
  form.name = ''
  form.description = ''
  form.notification_type = ''
  form.event_type = ''
  form.recipient_type = ''
  form.recipient_roles = []
  form.recipient_users = []
  form.is_active = true
  dialogVisible.value = true
}

const handleEdit = (row) => {
  isEdit.value = true
  dialogTitle.value = t('notificationRule.editRule')
  form.id = row.id
  form.name = row.name
  form.description = row.description
  form.notification_type = row.notification_type
  form.event_type = row.event_type
  form.recipient_type = row.recipient_type
  form.recipient_roles = row.recipient_roles ? JSON.parse(row.recipient_roles) : []
  form.recipient_users = row.recipient_users ? JSON.parse(row.recipient_users) : []
  form.is_active = row.is_active
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        const data = {
          name: form.name,
          description: form.description,
          notification_type: form.notification_type,
          event_type: form.event_type,
          recipient_type: form.recipient_type,
          recipient_roles: JSON.stringify(form.recipient_roles),
          recipient_users: JSON.stringify(form.recipient_users),
          is_active: form.is_active
        }
        
        if (isEdit.value) {
          await updateNotificationRule(form.id, data)
          ElMessage.success(t('notificationRule.updateSuccess'))
        } else {
          await createNotificationRule(data)
          ElMessage.success(t('notificationRule.createSuccess'))
        }
        
        dialogVisible.value = false
        loadData()
      } catch (error) {
        const errorMsg = error.response?.data?.detail || t('notificationRule.operationFailed')
        ElMessage.error(errorMsg)
      } finally {
        submitting.value = false
      }
    }
  })
}

const handleStatusChange = async (row) => {
  try {
    await updateNotificationRule(row.id, { is_active: row.is_active })
    ElMessage.success(t('notificationRule.statusUpdateSuccess'))
  } catch (error) {
    row.is_active = !row.is_active
    const errorMsg = error.response?.data?.detail || t('notificationRule.statusUpdateFailed')
    ElMessage.error(errorMsg)
  }
}

const handleDelete = (row) => {
  ElMessageBox.confirm(
    t('notificationRule.deleteConfirm', { name: row.name }),
    t('common.warning'),
    {
      confirmButtonText: t('common.confirm'),
      cancelButtonText: t('common.cancel'),
      type: 'warning'
    }
  ).then(async () => {
    try {
      await deleteNotificationRule(row.id)
      ElMessage.success(t('notificationRule.deleteSuccess'))
      loadData()
    } catch (error) {
      const errorMsg = error.response?.data?.detail || t('notificationRule.deleteFailed')
      ElMessage.error(errorMsg)
    }
  }).catch(() => {})
}

const loadRoles = async () => {
  try {
    const response = await getRoles({ page: 1, size: 1000 })
    allRoles.value = response.data.records || []
  } catch (error) {
    console.error('加载角色列表失败:', error)
  }
}

const loadUsers = async () => {
  try {
    const response = await getUsers({ page: 1, size: 1000 })
    allUsers.value = response.data.records || []
  } catch (error) {
    console.error('加载用户列表失败:', error)
  }
}

// 监听通知类型变化，清空事件类型
watch(() => form.notification_type, (newType, oldType) => {
  if (newType !== oldType) {
    form.event_type = ''
  }
})

onMounted(() => {
  loadData()
  loadRoles()
  loadUsers()
  bindTableHeight()
})
onBeforeUnmount(() => {
  unbindTableHeight()
})
</script>

<style scoped>
.notification-rule-management {
  padding: 20px;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.notification-rule-management :deep(.el-card__body) {
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
</style>
