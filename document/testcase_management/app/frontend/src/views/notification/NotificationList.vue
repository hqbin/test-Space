<template>
  <div :class="isDrawer ? '' : 'notification-page'">
    <el-card class="table-card" shadow="never" :class="{ 'drawer-mode': isDrawer }">
      <!-- 页面标题栏 -->
      <div v-if="!isDrawer" class="table-header">
        <div class="header-left">
          <h3 class="page-title">{{ $t('notification.title') }}</h3>
        </div>
        <div class="header-right">
          <el-select v-model="filterType" :placeholder="$t('notification.filterByType')" style="width: 160px;" clearable @change="handleSearch">
            <el-option :label="$t('notification.allTypes')" value="" />
            <el-option :label="$t('notification.types.testcase')" value="testcase" />
            <el-option :label="$t('notification.types.testplan')" value="testplan" />
            <el-option :label="$t('notification.types.execution')" value="execution" />
            <el-option :label="$t('notification.types.report')" value="report" />
            <el-option :label="$t('notification.types.system')" value="system" />
          </el-select>
          <el-select v-model="filterRead" :placeholder="$t('notification.filterByStatus')" style="width: 130px;" clearable @change="handleSearch">
            <el-option :label="$t('notification.allStatus')" value="" />
            <el-option :label="$t('notification.unread')" :value="false" />
            <el-option :label="$t('notification.read')" :value="true" />
          </el-select>
          <el-button type="primary" :icon="Check" @click="handleMarkAllAsRead" :disabled="unreadCount === 0">
            {{ $t('notification.markAllAsRead') }}
          </el-button>
          <el-button :icon="Setting" @click="handleOpenSettings" circle :title="$t('notification.notificationSettings')" />
        </div>
      </div>

      <!-- 抽屉模式标题栏 -->
      <div v-if="isDrawer" class="table-header drawer-header">
        <div style="display: flex; gap: 8px; flex: 1; min-width: 0;">
          <el-select v-model="filterType" :placeholder="$t('notification.filterByType')" clearable @change="handleSearch" style="flex: 1; min-width: 120px;">
            <el-option :label="$t('notification.allTypes')" value="" />
            <el-option :label="$t('notification.types.testcase')" value="testcase" />
            <el-option :label="$t('notification.types.testplan')" value="testplan" />
            <el-option :label="$t('notification.types.execution')" value="execution" />
            <el-option :label="$t('notification.types.report')" value="report" />
            <el-option :label="$t('notification.types.system')" value="system" />
          </el-select>
          <el-select v-model="filterRead" :placeholder="$t('notification.filterByStatus')" clearable @change="handleSearch" style="flex: 1; min-width: 120px;">
            <el-option :label="$t('notification.allStatus')" value="" />
            <el-option :label="$t('notification.unread')" :value="false" />
            <el-option :label="$t('notification.read')" :value="true" />
          </el-select>
        </div>
        <div style="display: flex; gap: 8px; flex-shrink: 0;">
          <el-button type="primary" :icon="Check" @click="handleMarkAllAsRead" :disabled="unreadCount === 0">
            {{ $t('notification.markAllAsRead') }}
          </el-button>
          <el-button :icon="Setting" @click="handleOpenSettings" circle :title="$t('notification.notificationSettings')" />
        </div>
      </div>

      <!-- 表格 -->
      <div class="table-wrapper">
        <el-table
          ref="tableRef"
          :data="tableData"
          style="width: 100%"
          :header-cell-style="{ background: '#f8fafc', color: '#64748b', fontWeight: '500', fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.05em' }"
          :row-style="{ height: '48px' }"
        >
          <el-table-column :label="$t('notification.notificationType')" min-width="100" align="center">
            <template #default="scope">
              <el-tag :type="getTypeTagColor(scope.row.notification_type)" size="small" effect="plain">
                {{ getTypeLabel(scope.row.notification_type) }}
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column :label="$t('notification.notificationContent')" min-width="300">
            <template #default="scope">
              <div class="notification-content-cell" @click="handleViewDetail(scope.row)">
                <span :class="{ 'unread-title': !scope.row.is_read }">{{ scope.row.title }}</span>
                <el-badge v-if="!scope.row.is_read" is-dot style="margin-left: 8px;" />
              </div>
            </template>
          </el-table-column>

          <el-table-column :label="$t('notification.sendTime')" min-width="140" align="center">
            <template #default="scope">
              <span style="font-size: 13px; color: #64748b;">{{ formatDate(scope.row.created_at) }}</span>
            </template>
          </el-table-column>

          <el-table-column :label="$t('notification.status')" min-width="80" align="center">
            <template #default="scope">
              <el-tag :type="scope.row.is_read ? 'info' : 'success'" size="small" effect="light">
                {{ scope.row.is_read ? $t('notification.read') : $t('notification.unread') }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="size"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          background
          @current-change="async () => { await loadData(); await nextTick(); scrollToTop(); }"
          @size-change="async () => { await loadData(); await nextTick(); scrollToTop(); }"
        />
      </div>
    </el-card>

    <!-- 通知详情对话框 -->
    <el-dialog v-model="detailDialogVisible" :title="$t('notification.detail')" width="700px" :close-on-click-modal="false" :append-to-body="true">
      <div v-if="currentNotification" class="notification-detail">
        <div class="detail-header">
          <el-tag :type="getTypeTagColor(currentNotification.notification_type)" size="large" effect="plain">
            {{ getTypeLabel(currentNotification.notification_type) }}
          </el-tag>
          <el-tag size="large" effect="light" style="margin-left: 12px;">
            {{ getEventLabel(currentNotification.event_type) }}
          </el-tag>
        </div>
        <h3 class="detail-title">{{ currentNotification.title }}</h3>
        <div class="detail-content">
          <pre>{{ currentNotification.content }}</pre>
        </div>
        <div class="detail-footer">
          <div class="detail-time">
            <el-icon><Clock /></el-icon>
            <span>{{ formatDate(currentNotification.created_at) }}</span>
          </div>
          <el-tag :type="currentNotification.is_read ? 'info' : 'success'" size="small">
            {{ currentNotification.is_read ? $t('notification.read') : $t('notification.unread') }}
          </el-tag>
        </div>
      </div>
      <template #footer>
        <el-button @click="detailDialogVisible = false">{{ $t('common.close') }}</el-button>
        <el-button v-if="currentNotification && !currentNotification.is_read" type="primary" @click="handleMarkAsReadInDialog">
          {{ $t('notification.markAsRead') }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 通知偏好设置对话框 -->
    <el-dialog v-model="settingsDialogVisible" :title="$t('notification.notificationSettings')" width="700px" :close-on-click-modal="false" :append-to-body="true">
      <div class="notification-settings" style="max-height: 60vh; overflow-y: auto;">
        <p class="settings-description">{{ $t('notification.settingsDescription') }}</p>
        <el-collapse v-model="activeCollapseItems" class="settings-collapse">
          <el-collapse-item v-for="typePref in preferences" :key="typePref.notification_type" :name="typePref.notification_type">
            <template #title>
              <div class="collapse-title">
                <el-tag :type="getTypeTagColor(typePref.notification_type)" size="large" effect="plain">
                  {{ typePref.label }}
                </el-tag>
                <div class="collapse-title-right">
                  <span class="event-count">{{ $t('notification.eventCount', { count: typePref.events.length }) }}</span>
                  <el-switch
                    :model-value="isAllEventsEnabled(typePref)"
                    @change="(val) => toggleAllEvents(typePref, val)"
                    @click.stop
                    size="large"
                    style="--el-switch-on-color: #4f46e5; --el-switch-off-color: #cbd5e1;"
                  />
                </div>
              </div>
            </template>
            <div class="events-list">
              <div v-for="event in typePref.events" :key="event.event_type" class="event-item">
                <span class="event-label">{{ event.label }}</span>
                <el-switch v-model="event.is_enabled" size="default" style="--el-switch-on-color: #4f46e5; --el-switch-off-color: #cbd5e1;" />
              </div>
            </div>
          </el-collapse-item>
        </el-collapse>
      </div>
      <template #footer>
        <el-button @click="settingsDialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleSaveSettings" :loading="savingSettings">{{ $t('notification.saveSettings') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, defineProps, defineEmits, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { getNotifications, markAsRead, markAllAsRead, getNotificationDetail, getNotificationPreferences, updateNotificationPreferences } from '../../api/notification'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Check, View, Clock, Setting } from '@element-plus/icons-vue'
import { usePagination } from '../../composables/usePagination'
import { useScrollToTop } from '../../composables/useScrollToTop'
import { useLoadingStore } from '../../stores/loading'

const { t } = useI18n()

const props = defineProps({
  isDrawer: { type: Boolean, default: false }
})

const emit = defineEmits(['update-count'])

const tableData = ref([])
const tableRef = ref(null)
const { page, size, total } = usePagination('notificationList', 10)
const { scrollToTop } = useScrollToTop(tableRef)
const loadingStore = useLoadingStore()
const filterType = ref('')
const filterRead = ref('')
const unreadCount = ref(0)
const detailDialogVisible = ref(false)
const currentNotification = ref(null)
const settingsDialogVisible = ref(false)
const preferences = ref([])
const savingSettings = ref(false)
const activeCollapseItems = ref([])

const getTypeTagColor = (type) => {
  const colorMap = { 'testcase': 'primary', 'testplan': 'success', 'execution': 'warning', 'report': 'danger', 'system': 'info' }
  return colorMap[type] || 'info'
}

const getTypeLabel = (type) => {
  const labelMap = { 'testcase': t('notification.types.testcase'), 'testplan': t('notification.types.testplan'), 'execution': t('notification.types.execution'), 'report': t('notification.types.report'), 'system': t('notification.types.system') }
  return labelMap[type] || type
}

const getEventLabel = (event) => {
  const labelMap = {
    'created': t('notification.events.created'), 'updated': t('notification.events.updated'), 'deleted': t('notification.events.deleted'),
    'status_changed': t('notification.events.statusChanged'), 'completed': t('notification.events.completed'), 'started': t('notification.events.started'),
    'cancelled': t('notification.events.cancelled'), 'result_updated': t('notification.events.resultUpdated'), 'generated': t('notification.events.generated'),
    'alert': t('notification.events.alert'), 'review_submitted': t('notification.events.reviewSubmitted'), 'review_approved': t('notification.events.reviewApproved'), 'review_rejected': t('notification.events.reviewRejected'),
    'review_commented': t('notification.events.reviewCommented'), 'review_invitation': '评审邀请', 'assigned': '任务分配', 'maintenance': t('notification.events.maintenance'), 'feature_release': t('notification.events.featureRelease'), 'password_expiry': t('notification.events.passwordExpiry'),
    'permission_changed': t('notification.events.permissionChanged'), 'backup_completed': t('notification.events.backupCompleted'), 'version_update': t('notification.events.versionUpdate'), 'daily_reminder': t('notification.events.dailyReminder'),
    'user_registration': '用户注册审核'
  }
  return labelMap[event] || event
}

const formatDate = (date) => {
  if (!date) return '-'
  const d = new Date(date)
  return d.toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

const handleSearch = () => { page.value = 1; loadData() }

const loadData = async () => {
  loadingStore.showLoading()
  try {
    const params = { page: page.value, size: size.value }
    if (filterType.value) params.notification_type = filterType.value
    if (filterRead.value !== '') params.is_read = filterRead.value
    const res = await getNotifications(params)
    if (res.data && res.data.records) {
      tableData.value = res.data.records
      total.value = res.data.total || 0
      unreadCount.value = tableData.value.filter(n => !n.is_read).length
    }
  } catch (error) {
    console.error('Load notifications error:', error)
    ElMessage.error(t('notification.loadFailed'))
  } finally {
    loadingStore.hideLoading()
  }
}

const handleViewDetail = async (row) => {
  try {
    const res = await getNotificationDetail(row.id)
    if (res.data) {
      currentNotification.value = res.data
      detailDialogVisible.value = true
      if (!row.is_read) { row.is_read = true; unreadCount.value = Math.max(0, unreadCount.value - 1); if (props.isDrawer) emit('update-count') }
    }
  } catch (error) { console.error('Load notification detail error:', error); ElMessage.error(t('notification.loadDetailFailed')) }
}

const handleMarkAsRead = async (row) => {
  try {
    await markAsRead(row.id); row.is_read = true; unreadCount.value = Math.max(0, unreadCount.value - 1)
    ElMessage.success(t('notification.markSuccess'))
    if (props.isDrawer) emit('update-count')
  } catch (error) { console.error('Mark read failed:', error); ElMessage.error(t('notification.markFailed')) }
}

const handleMarkAsReadInDialog = async () => {
  if (!currentNotification.value) return
  try {
    await markAsRead(currentNotification.value.id); currentNotification.value.is_read = true
    const item = tableData.value.find(n => n.id === currentNotification.value.id)
    if (item) item.is_read = true
    unreadCount.value = Math.max(0, unreadCount.value - 1)
    ElMessage.success(t('notification.markSuccess'))
    if (props.isDrawer) emit('update-count')
  } catch (error) { console.error('Mark read error:', error); ElMessage.error(t('notification.markFailed')) }
}

const handleMarkAllAsRead = async () => {
  try {
    await ElMessageBox.confirm(t('notification.markAllConfirm'), t('notification.markAllTitle'), { confirmButtonText: t('common.confirm'), cancelButtonText: t('common.cancel'), type: 'info' })
    const res = await markAllAsRead()
    ElMessage.success(t('notification.markAllSuccess', { count: res.data.count }))
    loadData()
    if (props.isDrawer) emit('update-count')
  } catch (error) { if (error !== 'cancel') { console.error('Mark all read failed:', error); ElMessage.error(t('notification.markAllFailed')) } }
}

const handleOpenSettings = async () => {
  try {
    const res = await getNotificationPreferences()
    if (res.data) { preferences.value = res.data; activeCollapseItems.value = []; settingsDialogVisible.value = true }
  } catch (error) { console.error('Load notification preferences failed:', error); ElMessage.error(t('notification.loadSettingsFailed')) }
}

const isAllEventsEnabled = (typePref) => typePref.events.every(event => event.is_enabled)
const toggleAllEvents = (typePref, enabled) => { typePref.events.forEach(event => { event.is_enabled = enabled }) }

const handleSaveSettings = async () => {
  try {
    savingSettings.value = true
    await updateNotificationPreferences({ preferences: preferences.value })
    ElMessage.success(t('notification.settingsSaved')); settingsDialogVisible.value = false
  } catch (error) { console.error('Save settings failed:', error); ElMessage.error(t('notification.settingsFailed')) }
  finally { savingSettings.value = false }
}

onMounted(() => { loadData() })

defineExpose({ loadData })
</script>

<style scoped>
/* ==================== 页面容器 ==================== */
.notification-page {
  height: 100%;
  padding: 24px;
  background: #f8fafc;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}

/* ==================== 卡片 ==================== */
.table-card {
  border-radius: 16px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  flex: 1;
  display: flex;
  flex-direction: column;
}

.table-card :deep(.el-card__body) {
  padding: 0;
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
}

/* ==================== 表头 ==================== */
.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #e2e8f0;
  background: #fff;
  border-radius: 16px 16px 0 0;
}

.page-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #0f172a;
}

.header-right {
  display: flex;
  gap: 12px;
  align-items: center;
}

/* ==================== 表格 ==================== */
.table-wrapper {
  flex: 1;
  overflow: auto;
  padding: 0 24px;
}

.notification-content-cell {
  display: flex;
  align-items: center;
  cursor: pointer;
}

.notification-content-cell:hover {
  color: #4f46e5;
}

.unread-title {
  font-weight: 600;
  color: #0f172a;
}

/* ==================== 分页 ==================== */
.pagination-container {
  display: flex;
  justify-content: flex-end;
  padding: 16px 24px;
  border-top: 1px solid #e2e8f0;
  flex-shrink: 0;
}

.pagination-container :deep(.el-pagination.is-background .el-pager li:not(.is-disabled).is-active) {
  background: #eef2ff;
  color: #4f46e5;
}

/* ==================== 详情对话框 ==================== */
.notification-detail { padding: 8px 0; }

.detail-header { margin-bottom: 16px; }

.detail-title {
  font-size: 18px;
  font-weight: 600;
  color: #0f172a;
  margin: 16px 0;
  line-height: 1.5;
}

.detail-content {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 20px;
  margin: 16px 0;
}

.detail-content pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: inherit;
  font-size: 14px;
  line-height: 1.8;
  color: #475569;
}

.detail-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 16px;
  border-top: 1px solid #e2e8f0;
}

.detail-time {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #64748b;
  font-size: 13px;
}

/* ==================== 设置对话框 ==================== */
.notification-settings { padding: 4px 0; }

.settings-description {
  color: #64748b;
  font-size: 14px;
  margin-bottom: 20px;
}

.settings-collapse :deep(.el-collapse-item) {
  margin-bottom: 12px;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  overflow: hidden;
}

.settings-collapse :deep(.el-collapse-item__header) {
  background: #f8fafc;
  border: none;
  padding: 14px 20px;
  height: auto;
  line-height: 1.5;
}

.settings-collapse :deep(.el-collapse-item__header:hover) {
  background: #f1f5f9;
}

.settings-collapse :deep(.el-collapse-item__wrap) {
  border: none;
}

.settings-collapse :deep(.el-collapse-item__content) {
  padding: 0;
}

.collapse-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding-right: 12px;
}

.collapse-title-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.event-count {
  font-size: 13px;
  color: #64748b;
}

.events-list {
  padding: 8px 20px;
}

.event-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px dashed #e2e8f0;
}

.event-item:last-child {
  border-bottom: none;
}

.event-label {
  font-size: 14px;
  color: #475569;
}

/* ==================== 抽屉模式 ==================== */
.drawer-mode {
  border-radius: 0;
  box-shadow: none;
  border: none;
  height: 100%;
}

.drawer-mode .table-header {
  border-radius: 0;
  padding: 16px;
}

.drawer-header {
  flex-wrap: wrap;
  gap: 12px;
}

.drawer-mode :deep(.el-card__body) {
  height: 100%;
}

.drawer-mode .table-wrapper {
  padding: 0 16px;
}

.drawer-mode .pagination-container {
  padding: 12px 16px;
}

.drawer-mode :deep(.el-table) {
  font-size: 12px;
}

.drawer-mode :deep(.el-tag) {
  font-size: 11px;
  padding: 0 6px;
  height: 22px;
  line-height: 22px;
}
</style>
