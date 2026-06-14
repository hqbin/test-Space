<template>
  <div class="version-release-page">
    <!-- 主内容区 -->
    <div class="main-card glass-card">
      <div class="table-header">
        <div class="header-left">
          <el-button type="primary" round @click="handleCreate">
            <el-icon><Plus /></el-icon>
            <span>新建版本</span>
          </el-button>
          <el-button round @click="openGroupDialog">
            <el-icon><UserFilled /></el-icon>
            <span>用户组管理</span>
          </el-button>
        </div>
        <div class="header-right">
          <el-input v-model="searchKeyword" placeholder="搜索版本号 / 标题" clearable class="search-input" @keyup.enter="loadData" @clear="loadData">
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
        </div>
      </div>

      <el-table :data="tableData" v-loading="loading" class="modern-table" stripe>
        <el-table-column prop="version_number" label="版本号" width="130">
          <template #default="{ row }">
            <span class="version-num">{{ row.version_number }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="版本标题" min-width="180" show-overflow-tooltip />
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 'published' ? 'success' : 'info'" effect="plain" round size="small">
              {{ row.status === 'published' ? '已发布' : '草稿' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="通知" width="80" align="center">
          <template #default="{ row }">
            <el-icon v-if="row.notify_enabled" color="#e6a23c"><Bell /></el-icon>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column label="发布时间" width="170">
          <template #default="{ row }">
            <span class="time-text">{{ formatTime(row.published_at) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="条目" width="70" align="center">
          <template #default="{ row }">
            <el-badge :value="row.items?.length || 0" type="info" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button type="primary" link @click="handleEdit(row)">
                <el-icon><Edit /></el-icon> 编辑
              </el-button>
              <el-button v-if="row.status === 'draft'" type="success" link @click="handlePublish(row)">
                <el-icon><Promotion /></el-icon> 发布
              </el-button>
              <el-button v-if="row.status === 'published'" type="warning" link @click="handleUnpublish(row)">
                <el-icon><RefreshLeft /></el-icon> 撤回
              </el-button>
              <el-button type="danger" link @click="handleDelete(row)">
                <el-icon><Delete /></el-icon> 删除
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          background
          @size-change="loadData"
          @current-change="loadData"
        />
      </div>
    </div>

    <!-- 新建/编辑版本弹窗 -->
    <el-dialog v-model="editDialogVisible" :title="isEdit ? '编辑版本' : '新建版本'" width="720px" class="modern-dialog" :close-on-click-modal="false" destroy-on-close>
      <el-form :model="editForm" label-width="80px" class="edit-form">
        <div class="form-row">
          <el-form-item label="版本号" required class="form-half">
            <el-input v-model="editForm.version_number" placeholder="如 v1.0.0" />
          </el-form-item>
          <el-form-item label="标题" required class="form-half">
            <el-input v-model="editForm.title" placeholder="版本标题" />
          </el-form-item>
        </div>
        <el-form-item label="更新内容">
          <div class="items-editor">
            <TransitionGroup name="list">
              <div v-for="(item, idx) in editForm.items" :key="idx" class="item-row">
                <el-select v-model="item.item_type" class="item-type-select" size="default">
                  <el-option label="新增" value="new" />
                  <el-option label="修复" value="fix" />
                  <el-option label="优化" value="improve" />
                  <el-option label="删除" value="delete" />
                  <el-option label="其他" value="other" />
                </el-select>
                <el-input v-model="item.content" placeholder="更新内容描述" class="item-content-input" size="default" />
                <el-button type="danger" :icon="Delete" circle size="small" @click="editForm.items.splice(idx, 1)" />
              </div>
            </TransitionGroup>
            <el-button class="add-item-btn" text @click="editForm.items.push({ item_type: 'new', content: '', sort_order: editForm.items.length })">
              <el-icon><Plus /></el-icon> 添加更新条目
            </el-button>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveDraft" :loading="saving">保存草稿</el-button>
      </template>
    </el-dialog>

    <!-- 发布弹窗 -->
    <el-dialog v-model="publishDialogVisible" title="发布版本" width="620px" class="modern-dialog" :close-on-click-modal="false" destroy-on-close>
      <div class="publish-form">
        <div class="publish-info glass-card-inner">
          <div class="info-row">
            <span class="info-label">版本号</span>
            <span class="info-value version-num">{{ publishTarget?.version_number }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">标题</span>
            <span class="info-value">{{ publishTarget?.title }}</span>
          </div>
        </div>
        <el-divider />
        <el-checkbox v-model="publishNotifyEnabled" class="notify-checkbox">
          <span class="notify-label">发送站内通知</span>
        </el-checkbox>
        <Transition name="fade">
          <div v-if="publishNotifyEnabled" class="notify-targets glass-card-inner">
            <div class="targets-header">
              <span>选择通知目标</span>
              <el-button type="primary" text size="small" @click="selectAllTargets">全选所有</el-button>
            </div>
            <div class="targets-tree">
              <div v-for="group in notifyGroups" :key="group.id" class="group-node">
                <div class="group-row">
                  <el-checkbox
                    :model-value="isGroupSelected(group)"
                    :indeterminate="isGroupIndeterminate(group)"
                    @change="toggleGroup(group, $event)"
                  />
                  <span class="group-expand-icon" @click="toggleGroupExpand(group.id)">
                    <el-icon :class="{ 'is-expanded': expandedGroups.has(group.id) }"><ArrowRight /></el-icon>
                  </span>
                  <span class="group-name" @click="toggleGroupExpand(group.id)">{{ group.name }}</span>
                  <el-tag size="small" type="info" class="group-count-tag">{{ group.members?.length || 0 }}人</el-tag>
                </div>
                <div v-if="expandedGroups.has(group.id) && group.members?.length" class="member-list">
                  <el-checkbox
                    v-for="member in group.members"
                    :key="member.user_id"
                    :model-value="selectedUserIds.has(member.user_id)"
                    @change="toggleUser(member.user_id, $event)"
                    class="member-item"
                  >
                    {{ member.username }}{{ member.full_name ? ` (${member.full_name})` : '' }}
                  </el-checkbox>
                </div>
              </div>
              <el-empty v-if="!notifyGroups.length" description="暂无用户组" :image-size="48" />
            </div>
          </div>
        </Transition>
      </div>
      <template #footer>
        <el-button @click="publishDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleConfirmPublish" :loading="publishing">
          <el-icon><Promotion /></el-icon> 确认发布
        </el-button>
      </template>
    </el-dialog>

    <!-- 用户组管理弹窗 -->
    <el-dialog v-model="showGroupDialog" title="版本通知用户组" width="860px" class="modern-dialog" :close-on-click-modal="false" destroy-on-close>
      <div class="group-management">
        <div class="group-header">
          <el-button type="primary" round size="default" @click="handleCreateGroup">
            <el-icon><Plus /></el-icon> 新建用户组
          </el-button>
        </div>
        <el-table :data="groupList" class="modern-table" stripe>
          <el-table-column prop="name" label="组名称" min-width="140" />
          <el-table-column prop="description" label="描述" min-width="180" show-overflow-tooltip />
          <el-table-column prop="member_count" label="成员" width="80" align="center">
            <template #default="{ row }">
              <el-tag round size="small">{{ row.member_count }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="160" align="center">
            <template #default="{ row }">
              <div class="action-buttons">
                <el-button type="primary" link @click="handleEditGroup(row)">
                  <el-icon><Edit /></el-icon> 编辑
                </el-button>
                <el-button type="danger" link @click="handleDeleteGroup(row)">
                  <el-icon><Delete /></el-icon> 删除
                </el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-dialog>

    <!-- 用户组编辑弹窗 -->
    <el-dialog v-model="groupEditVisible" :title="isEditGroup ? '编辑用户组' : '新建用户组'" width="600px" class="modern-dialog" :close-on-click-modal="false" destroy-on-close>
      <el-form :model="groupForm" label-width="80px">
        <el-form-item label="组名称" required>
          <el-input v-model="groupForm.name" placeholder="输入用户组名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="groupForm.description" type="textarea" :rows="2" placeholder="用户组描述（可选）" />
        </el-form-item>
        <el-form-item label="选择用户">
          <PaginatedUserSelector v-model="groupForm.user_ids" :exclude-user-ids="excludeUserIds" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="groupEditVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveGroup" :loading="savingGroup">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Delete, Search, UserFilled, Edit, Promotion, RefreshLeft, Bell, ArrowRight } from '@element-plus/icons-vue'
import { getVersionReleases, createVersionRelease, updateVersionRelease, deleteVersionRelease, publishVersion, unpublishVersion } from '@/api/versionRelease'
import { getVersionNotifyGroups, getAllVersionNotifyGroups, getVersionNotifyGroup, createVersionNotifyGroup, updateVersionNotifyGroup, deleteVersionNotifyGroup } from '@/api/versionNotifyGroup'
import PaginatedUserSelector from '@/components/PaginatedUserSelector.vue'

const loading = ref(false)
const tableData = ref([])
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const searchKeyword = ref('')

const editDialogVisible = ref(false)
const isEdit = ref(false)
const editId = ref(null)
const editForm = reactive({ version_number: '', title: '', items: [] })
const saving = ref(false)

const publishDialogVisible = ref(false)
const publishTarget = ref(null)
const publishNotifyEnabled = ref(false)
const selectedUserIds = ref(new Set())
const selectedGroupIds = ref(new Set())
const expandedGroups = ref(new Set())
const publishing = ref(false)

const showGroupDialog = ref(false)
const groupList = ref([])
const groupEditVisible = ref(false)
const isEditGroup = ref(false)
const editGroupId = ref(null)
const groupForm = reactive({ name: '', description: '', user_ids: [] })
const savingGroup = ref(false)

const excludeUserIds = computed(() => {
  const ids = new Set()
  for (const g of groupList.value) {
    if (isEditGroup.value && g.id === editGroupId.value) continue
    if (g.members) {
      g.members.forEach(m => ids.add(m.user_id))
    }
  }
  return Array.from(ids)
})

const notifyGroups = ref([])

const formatTime = (t) => {
  if (!t) return '-'
  return t.replace('T', ' ').replace(/\.\d+$/, '').substring(0, 19)
}

const loadData = async () => {
  loading.value = true
  try {
    const res = await getVersionReleases({ page: page.value, size: pageSize.value, keyword: searchKeyword.value || undefined })
    tableData.value = res.data.records
    total.value = res.data.total
  } catch {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

const loadGroups = async () => {
  try {
    const res = await getAllVersionNotifyGroups()
    groupList.value = res.data || []
  } catch {}
}

const loadAllGroups = async () => {
  try {
    const res = await getAllVersionNotifyGroups()
    notifyGroups.value = res.data
  } catch {}
}

const openGroupDialog = async () => {
  await loadGroups()
  showGroupDialog.value = true
}

const handleCreate = () => {
  isEdit.value = false
  editId.value = null
  editForm.version_number = ''
  editForm.title = ''
  editForm.items = []
  editDialogVisible.value = true
}

const handleEdit = async (row) => {
  isEdit.value = true
  editId.value = row.id
  editForm.version_number = row.version_number
  editForm.title = row.title
  editForm.items = (row.items || []).map(i => ({ item_type: i.item_type, content: i.content, sort_order: i.sort_order }))
  editDialogVisible.value = true
}

const handleSaveDraft = async () => {
  if (!editForm.version_number.trim()) return ElMessage.warning('请输入版本号')
  if (!editForm.title.trim()) return ElMessage.warning('请输入版本标题')
  saving.value = true
  try {
    const data = { ...editForm, items: editForm.items.filter(i => i.content.trim()) }
    if (isEdit.value) {
      await updateVersionRelease(editId.value, data)
      ElMessage.success('更新成功')
    } else {
      await createVersionRelease(data)
      ElMessage.success('创建成功')
    }
    editDialogVisible.value = false
    loadData()
  } catch {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定删除版本 ${row.version_number} 吗？`, '确认删除', { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' })
    await deleteVersionRelease(row.id)
    ElMessage.success('删除成功')
    loadData()
  } catch {}
}

const handlePublish = async (row) => {
  publishTarget.value = row
  publishNotifyEnabled.value = false
  selectedUserIds.value = new Set()
  selectedGroupIds.value = new Set()
  await loadAllGroups()
  publishDialogVisible.value = true
}

const handleUnpublish = async (row) => {
  try {
    await ElMessageBox.confirm(`确定撤回版本 ${row.version_number} 的发布吗？`, '撤回发布', { type: 'warning', confirmButtonText: '撤回', cancelButtonText: '取消' })
    await unpublishVersion(row.id)
    ElMessage.success('已撤回')
    loadData()
  } catch {}
}

const isGroupSelected = (group) => {
  const members = group.members || []
  return members.length > 0 && members.every(m => selectedUserIds.value.has(m.user_id))
}

const isGroupIndeterminate = (group) => {
  const members = group.members || []
  const selected = members.filter(m => selectedUserIds.value.has(m.user_id))
  return selected.length > 0 && selected.length < members.length
}

const toggleGroup = (group, checked) => {
  const newSet = new Set(selectedUserIds.value)
  if (checked) {
    (group.members || []).forEach(m => newSet.add(m.user_id))
    selectedGroupIds.value.add(group.id)
  } else {
    (group.members || []).forEach(m => newSet.delete(m.user_id))
    selectedGroupIds.value.delete(group.id)
  }
  selectedUserIds.value = newSet
}

const toggleUser = (userId, checked) => {
  const newSet = new Set(selectedUserIds.value)
  if (checked) newSet.add(userId)
  else newSet.delete(userId)
  selectedUserIds.value = newSet
}

const toggleGroupExpand = (groupId) => {
  const newSet = new Set(expandedGroups.value)
  if (newSet.has(groupId)) newSet.delete(groupId)
  else newSet.add(groupId)
  expandedGroups.value = newSet
}

const selectAllTargets = () => {
  const newSet = new Set()
  notifyGroups.value.forEach(g => {
    (g.members || []).forEach(m => newSet.add(m.user_id))
    selectedGroupIds.value.add(g.id)
  })
  selectedUserIds.value = newSet
}

const handleConfirmPublish = async () => {
  publishing.value = true
  try {
    const targets = []
    if (publishNotifyEnabled.value) {
      const groupTargetIds = new Set()
      notifyGroups.value.forEach(g => {
        const members = g.members || []
        if (members.length > 0 && members.every(m => selectedUserIds.value.has(m.user_id))) {
          groupTargetIds.add(g.id)
        }
      })
      groupTargetIds.forEach(gid => targets.push({ type: 'group', id: gid }))
      const groupMemberIds = new Set()
      notifyGroups.value.forEach(g => {
        if (groupTargetIds.has(g.id)) {
          (g.members || []).forEach(m => groupMemberIds.add(m.user_id))
        }
      })
      selectedUserIds.value.forEach(uid => {
        if (!groupMemberIds.has(uid)) {
          targets.push({ type: 'user', id: uid })
        }
      })
    }
    await publishVersion(publishTarget.value.id, { notify_enabled: publishNotifyEnabled.value, targets })
    ElMessage.success('发布成功')
    publishDialogVisible.value = false
    loadData()
  } catch {
    ElMessage.error('发布失败')
  } finally {
    publishing.value = false
  }
}

const handleCreateGroup = async () => {
  isEditGroup.value = false
  editGroupId.value = null
  groupForm.name = ''
  groupForm.description = ''
  groupForm.user_ids = []
  await loadGroups()
  groupEditVisible.value = true
}

const handleEditGroup = async (row) => {
  isEditGroup.value = true
  editGroupId.value = row.id
  groupForm.name = row.name
  groupForm.description = row.description || ''
  try {
    await loadGroups()
    const res = await getVersionNotifyGroup(row.id)
    groupForm.user_ids = (res.data?.members || []).map(m => m.user_id)
  } catch {
    groupForm.user_ids = []
  }
  groupEditVisible.value = true
}

const handleSaveGroup = async () => {
  if (!groupForm.name.trim()) return ElMessage.warning('请输入组名称')
  savingGroup.value = true
  try {
    if (isEditGroup.value) {
      await updateVersionNotifyGroup(editGroupId.value, { name: groupForm.name, description: groupForm.description, user_ids: groupForm.user_ids })
      ElMessage.success('更新成功')
    } else {
      await createVersionNotifyGroup(groupForm)
      ElMessage.success('创建成功')
    }
    groupEditVisible.value = false
    loadGroups()
  } catch {
    ElMessage.error('保存失败')
  } finally {
    savingGroup.value = false
  }
}

const handleDeleteGroup = async (row) => {
  try {
    await ElMessageBox.confirm(`确定删除用户组「${row.name}」吗？`, '确认删除', { type: 'warning' })
    await deleteVersionNotifyGroup(row.id)
    ElMessage.success('删除成功')
    loadGroups()
  } catch {}
}

onMounted(() => {
  loadData()
  loadGroups()
})
</script>

<style scoped>
.version-release-page {
  padding: 20px;
  height: 100%;
  overflow: auto;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e7ed 100%);
}

/* 毛玻璃主卡片 */
.glass-card {
  background: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.85);
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06);
}
.glass-card-inner {
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.7);
  border-radius: 10px;
  padding: 16px;
}

/* 表头 */
.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 12px;
}
.header-left {
  display: flex;
  gap: 10px;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}
.search-input {
  width: 220px;
}

/* 版本号 */
.version-num {
  font-size: 13px;
  font-weight: 600;
  color: var(--el-color-primary);
  font-family: monospace;
}

/* 时间 */
.time-text {
  font-size: 13px;
  color: #606266;
  font-variant-numeric: tabular-nums;
}

/* 操作按钮 */
.action-buttons {
  display: flex;
  gap: 4px;
  flex-wrap: nowrap;
}

/* 分页 */
.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

/* 弹窗内表单 */
.form-row {
  display: flex;
  gap: 16px;
}
.form-half {
  flex: 1;
}

/* 更新条目编辑器 */
.items-editor {
  width: 100%;
}
.item-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}
.item-row .el-select,
.item-row .el-input {
  --el-component-size: 32px;
}
.item-type-select {
  width: 100px;
}
.item-content-input {
  flex: 1;
}
.add-item-btn {
  color: var(--el-color-primary);
}
.add-item-btn:hover {
  background: transparent;
}

/* 发布弹窗 */
.publish-info {
  margin-bottom: 12px;
}
.info-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}
.info-row:last-child {
  margin-bottom: 0;
}
.info-label {
  font-size: 13px;
  color: #909399;
  min-width: 50px;
}
.info-value {
  font-size: 14px;
  color: #303133;
}
.notify-checkbox {
  margin: 8px 0;
}
.notify-label {
  font-weight: 500;
}

/* 通知目标 */
.notify-targets {
  margin-top: 12px;
}
.targets-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  font-weight: 600;
  font-size: 14px;
}
.targets-tree {
  max-height: 280px;
  overflow-y: auto;
}
.group-node {
  margin-bottom: 10px;
}
.group-row {
  display: flex;
  align-items: center;
  gap: 6px;
}
.group-expand-icon {
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  transition: transform 0.2s;
  color: #909399;
}
.group-expand-icon .is-expanded {
  transform: rotate(90deg);
}
.group-name {
  font-weight: 500;
  cursor: pointer;
}
.group-name:hover {
  color: var(--el-color-primary);
}
.group-count-tag {
  margin-left: 6px;
}
.member-list {
  padding-left: 28px;
  margin-top: 6px;
}
.member-item {
  display: block;
  margin-bottom: 4px;
}

/* 用户组管理 */
.group-management {
  min-height: 200px;
}
.group-header {
  margin-bottom: 16px;
}

/* 文本 */
.text-muted {
  color: #c0c4cc;
}

/* 动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
.list-enter-active,
.list-leave-active {
  transition: all 0.3s ease;
}
.list-enter-from {
  opacity: 0;
  transform: translateX(-20px);
}
.list-leave-to {
  opacity: 0;
  transform: translateX(20px);
}
.expand-enter-active,
.expand-leave-active {
  transition: all 0.2s ease;
}
.expand-enter-from,
.expand-leave-to {
  opacity: 0;
  max-height: 0;
  overflow: hidden;
}

/* 深度样式 */
:deep(.el-dialog) {
  border-radius: 16px;
  overflow: hidden;
}
:deep(.el-dialog__header) {
  background: linear-gradient(135deg, #f5f7fa 0%, var(--el-color-primary-light-9) 100%);
  padding: 16px 24px;
  margin: 0;
  border-bottom: 1px solid #e4e7ed;
}
:deep(.el-dialog__title) {
  font-weight: 600;
}
:deep(.el-dialog__body) {
  padding: 24px;
}
:deep(.el-dialog__footer) {
  padding: 12px 24px;
  border-top: 1px solid #ebeef5;
}
:deep(.el-table) {
  border-radius: 10px;
  overflow: hidden;
}
:deep(.el-table th.el-table__cell) {
  background: #f5f7fa;
  font-weight: 600;
}
:deep(.el-segmented) {
  --el-segmented-bg-color: rgba(255, 255, 255, 0.5);
  --el-segmented-item-selected-bg-color: #409eff;
  --el-segmented-item-selected-color: #fff;
}
:deep(.el-tabs__header) {
  margin-bottom: 16px;
}
</style>
