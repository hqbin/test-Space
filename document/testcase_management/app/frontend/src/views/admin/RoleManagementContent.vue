<template>
  <div class="role-management-content">
    <!-- 工具栏 -->
    <div class="table-header">
      <div class="header-left">
        <div class="action-buttons">
          <el-button v-if="hasButton('permissionManagement', 'createRole')" type="primary" :icon="Plus" @click="handleCreate">
            {{ $t('role.createRole') }}
          </el-button>
        </div>
      </div>
      <div class="header-right">
        <el-input
          v-model="searchKeyword"
          :placeholder="$t('role.searchPlaceholder')"
          size="large"
          style="width: 250px;"
          clearable
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
          <el-table-column prop="name" :label="$t('role.name')" min-width="160" align="center">
            <template #default="scope">
              <el-tooltip :content="scope.row.name" placement="top" :teleported="true" :show-after="500">
                <span class="cell-text" style="font-weight: 500; color: #0f172a;">{{ scope.row.name }}</span>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column :label="$t('role.permissions')" min-width="280">
            <template #default="scope">
              <div class="permissions-display">
                <div v-if="!scope.row.permissions || scope.row.permissions.length === 0" class="no-permissions">
                  <el-icon><WarningFilled /></el-icon>
                  <span>{{ $t('user.unassigned') }}</span>
                </div>
                <el-tooltip v-else placement="top" :teleported="true" :show-after="500">
                  <template #content>
                    <div style="max-width: 350px;">{{ scope.row.permissions.map(p => getPermissionName(p)).join('、') }}</div>
                  </template>
                  <div class="permissions-summary">
                    <el-icon><Checked /></el-icon>
                    <span>{{ getPermissionSummary(scope.row.permissions) }}</span>
                  </div>
                </el-tooltip>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="description" :label="$t('common.description')" min-width="200" align="center">
            <template #default="scope">
              <el-tooltip :content="scope.row.description || '-'" placement="top" :teleported="true" :show-after="500">
                <span class="cell-text">{{ scope.row.description || '-' }}</span>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" :label="$t('common.createdAt')" min-width="160" align="center">
            <template #default="scope">
              <el-tooltip :content="formatDate(scope.row.created_at)" placement="top" :teleported="true" :show-after="500">
                <span class="cell-text" style="color: #64748b;">{{ formatDate(scope.row.created_at) }}</span>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column :label="$t('common.operation')" width="240" align="center" fixed="right">
            <template #default="scope">
              <el-button v-if="hasButton('permissionManagement', 'editRole')" type="primary" size="default" :icon="Edit" @click="handleEdit(scope.row)">
                {{ $t('common.edit') }}
              </el-button>
              <el-button v-if="!scope.row.is_system && hasButton('permissionManagement', 'deleteRole')" type="danger" size="default" :icon="Delete" @click="handleDelete(scope.row)">
                {{ $t('common.delete') }}
              </el-button>
              <el-tooltip v-else-if="scope.row.is_system" :content="$t('role.systemRoleCannotDelete')" placement="top" :show-after="500">
                <el-button type="danger" size="default" :icon="Delete" disabled>{{ $t('common.delete') }}</el-button>
              </el-tooltip>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <!-- 分页 -->
    <div class="pagination-container">
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="size"
        :total="total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @current-change="loadData"
        @size-change="loadData"
      />
    </div>

    <!-- 创建/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="800px" :close-on-click-modal="false">
      <el-form :model="form" ref="formRef" label-position="top">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item :label="$t('role.name')" required>
              <el-input v-model="form.name" :placeholder="$t('role.inputName')" maxlength="50" show-word-limit />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item :label="$t('common.description')">
              <el-input v-model="form.description" :placeholder="$t('role.inputDescription')" maxlength="255" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item :label="$t('role.permissionConfig')">
          <div class="permission-table-wrapper">
            <table class="permission-table">
              <thead>
                <tr>
                  <th class="col-page">
                    <el-checkbox 
                      :indeterminate="isAllIndeterminate" 
                      :model-value="isAllChecked" 
                      @change="handleSelectAll"
                    >{{ $t('role.pagePermission') }}</el-checkbox>
                  </th>
                  <th class="col-buttons">{{ $t('role.featurePermission') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr class="group-row">
                  <td colspan="2">
                    <el-checkbox 
                      :indeterminate="isGroupIndeterminate('test')" 
                      :model-value="isGroupChecked('test')" 
                      @change="(val) => handleGroupSelect('test', val)"
                    >
                      <span class="group-label">{{ $t('role.mainFeatures') }}</span>
                    </el-checkbox>
                  </td>
                </tr>
                <tr v-for="perm in testPermissions" :key="perm.key" class="perm-row">
                  <td class="col-page">
                    <el-checkbox 
                      :model-value="form.permissions.includes(perm.key)" 
                      @change="(val) => handlePageChange(perm.key, val)"
                    >{{ $t(perm.nameKey) }}</el-checkbox>
                  </td>
                  <td class="col-buttons">
                    <div class="btn-list" v-if="getPageButtons(perm.key).length > 0">
                      <el-checkbox
                        v-for="btn in getPageButtons(perm.key)"
                        :key="btn.key"
                        :model-value="form.permissions.includes(btn.key)"
                        @change="(val) => handleButtonChange(btn.key, perm.key, val)"
                      >{{ btn.description }}</el-checkbox>
                    </div>
                    <span v-else class="no-buttons">-</span>
                  </td>
                </tr>
                <tr class="group-row">
                  <td colspan="2">
                    <el-checkbox 
                      :indeterminate="isGroupIndeterminate('admin')" 
                      :model-value="isGroupChecked('admin')" 
                      @change="(val) => handleGroupSelect('admin', val)"
                    >
                      <span class="group-label">{{ $t('role.adminFeatures') }}</span>
                    </el-checkbox>
                  </td>
                </tr>
                <tr v-for="perm in adminPermissions" :key="perm.key" class="perm-row">
                  <td class="col-page">
                    <el-checkbox 
                      :model-value="form.permissions.includes(perm.key)" 
                      @change="(val) => handlePageChange(perm.key, val)"
                    >{{ perm.group === 'aivoice' ? perm.nameKey : $t(perm.nameKey) }}</el-checkbox>
                  </td>
                  <td class="col-buttons">
                    <div class="btn-list" v-if="getPageButtons(perm.key).length > 0">
                      <el-checkbox
                        v-for="btn in getPageButtons(perm.key)"
                        :key="btn.key"
                        :model-value="form.permissions.includes(btn.key)"
                        @change="(val) => handleButtonChange(btn.key, perm.key, val)"
                      >{{ btn.description }}</el-checkbox>
                    </div>
                    <span v-else class="no-buttons">-</span>
                  </td>
                </tr>
                <tr v-if="featurePermissions.length > 0" class="group-row">
                  <td colspan="2">
                    <el-checkbox 
                      :indeterminate="isFeatureIndeterminate" 
                      :model-value="isFeatureChecked" 
                      @change="handleFeatureSelectAll"
                    >
                      <span class="group-label">{{ $t('role.independentFeatures') }}</span>
                    </el-checkbox>
                  </td>
                </tr>
                <tr v-for="perm in featurePermissions" :key="perm.key" class="perm-row">
                  <td class="col-page">
                    <el-checkbox 
                      :model-value="form.permissions.includes(perm.key)" 
                      @change="(val) => handleFeatureChange(perm.key, val)"
                    >{{ perm.description }}</el-checkbox>
                  </td>
                  <td class="col-buttons">
                    <span class="no-buttons">-</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
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
import { ref, reactive, computed, onMounted, onBeforeUnmount } from 'vue'
import { useI18n } from 'vue-i18n'
import { getRoles, createRole, updateRole, deleteRole } from '../../api/role'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete, Search, WarningFilled, Checked } from '@element-plus/icons-vue'
import { useTableHeight } from '../../composables/useTableHeight'
import { ALL_PERMISSIONS, BUTTON_PERMISSIONS, FEATURE_PERMISSIONS } from '../../config/permissions'
import { useUserRole } from '../../composables/useUserRole'

const { t } = useI18n()
const { hasButton } = useUserRole()
const { tableContainerRef, tableHeight, bindTableHeight, unbindTableHeight } = useTableHeight()
const tableRef = ref(null)

const tableData = ref([])
const page = ref(1)
const size = ref(10)
const total = ref(0)
const searchKeyword = ref('')
const dialogVisible = ref(false)
const dialogTitle = computed(() => form.id ? t('role.editRole') : t('role.createRole'))
const submitting = ref(false)
const formRef = ref(null)

const form = reactive({ id: null, name: '', description: '', permissions: [] })

const testPermissions = computed(() => ALL_PERMISSIONS.filter(p => p.group === 'test'))
const adminPermissions = computed(() => ALL_PERMISSIONS.filter(p => (p.group === 'admin' || (p.group === 'aivoice' && !p.parent) || p.group === 'standalone' || p.group === 'projects') && p.key !== 'behaviorTracker' && p.key !== 'versionRelease'))
const featurePermissions = computed(() => FEATURE_PERMISSIONS)

// 获取 aivoice 子入口列表
const getAivoiceSubPerms = () => ALL_PERMISSIONS.filter(p => p.parent === 'aivoice')

const getPageButtons = (pageKey) => {
  // aivoice 主入口：子入口来自 ALL_PERMISSIONS（parent === 'aivoice'）
  if (pageKey === 'aivoice') {
    return getAivoiceSubPerms().map(p => ({ key: p.key, description: p.nameKey }))
  }
  const buttons = BUTTON_PERMISSIONS[pageKey]
  return buttons ? Object.values(buttons) : []
}

const getPermissionSummary = (permissions) => {
  const featureKeys = FEATURE_PERMISSIONS.map(p => p.key)
  const pageCount = permissions.filter(p => !p.includes('.') && !featureKeys.includes(p)).length
  const buttonCount = permissions.filter(p => p.includes('.')).length
  const featureCount = permissions.filter(p => featureKeys.includes(p)).length
  const parts = []
  if (pageCount > 0) parts.push(t('role.pageCount', { count: pageCount }))
  if (buttonCount > 0) parts.push(t('role.featureCount', { count: buttonCount }))
  if (featureCount > 0) parts.push(t('role.independentCount', { count: featureCount }))
  return parts.join(' + ') || t('role.noPermission')
}

const getPermissionName = (perm) => {
  const pagePerm = ALL_PERMISSIONS.find(item => item.key === perm)
  if (pagePerm) return pagePerm.nameKey.startsWith('menu.') ? t(pagePerm.nameKey) : pagePerm.nameKey
  const featurePerm = FEATURE_PERMISSIONS.find(item => item.key === perm)
  if (featurePerm) return featurePerm.description
  const [page, action] = perm.split('.')
  const buttons = BUTTON_PERMISSIONS[page]
  if (buttons && buttons[action]) return buttons[action].description
  return perm
}

const formatDate = (date) => {
  if (!date) return '-'
  return new Date(date).toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

const loadData = async () => {
  try {
    const res = await getRoles({ page: page.value, size: size.value, search: searchKeyword.value })
    tableData.value = res.data.records || []
    total.value = res.data.total || 0
  } catch (error) {
    tableData.value = []; total.value = 0
    ElMessage.error(t('role.loadFailed'))
  }
}

const handleSearch = () => { page.value = 1; loadData() }

const handleCreate = () => {
  form.id = null; form.name = ''; form.description = ''; form.permissions = []
  dialogVisible.value = true
}

const handleEdit = (row) => {
  form.id = row.id; form.name = row.name; form.description = row.description
  form.permissions = row.permissions ? [...row.permissions] : []
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!form.name || !form.name.trim()) { ElMessage.warning(t('role.inputRoleName')); return }
  submitting.value = true
  try {
    const payload = { name: form.name, description: form.description, permissions: form.permissions }
    if (form.id) { await updateRole(form.id, payload); ElMessage.success(t('role.updateSuccess')) }
    else { await createRole(payload); ElMessage.success(t('role.createSuccess')) }
    dialogVisible.value = false; loadData()
  } catch (error) { ElMessage.error(error.response?.data?.detail || t('role.operationFailed')) } finally { submitting.value = false }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(t('role.confirmDeleteRole'), t('common.deleteConfirmTitle'), { confirmButtonText: t('role.confirmDeleteBtn'), cancelButtonText: t('common.cancel'), type: 'warning' })
    await deleteRole(row.id); ElMessage.success(t('role.deleteSuccess')); loadData()
  } catch (error) { if (error !== 'cancel') ElMessage.error(error.response?.data?.detail || t('role.deleteFailed')) }
}

const handlePageChange = (pageKey, val) => {
  if (val) {
    if (!form.permissions.includes(pageKey)) form.permissions.push(pageKey)
    // aivoice 主开关：自动勾选所有子入口
    if (pageKey === 'aivoice') {
      getAivoiceSubPerms().forEach(p => { if (!form.permissions.includes(p.key)) form.permissions.push(p.key) })
    }
  } else {
    let idx = form.permissions.indexOf(pageKey)
    if (idx > -1) form.permissions.splice(idx, 1)
    // aivoice 主开关：自动取消所有子入口
    if (pageKey === 'aivoice') {
      getAivoiceSubPerms().forEach(p => { const i = form.permissions.indexOf(p.key); if (i > -1) form.permissions.splice(i, 1) })
    } else {
      const buttons = BUTTON_PERMISSIONS[pageKey]
      if (buttons) Object.values(buttons).forEach(btn => { idx = form.permissions.indexOf(btn.key); if (idx > -1) form.permissions.splice(idx, 1) })
    }
  }
}

const handleButtonChange = (btnKey, pageKey, val) => {
  if (val) {
    if (!form.permissions.includes(pageKey)) form.permissions.push(pageKey)
    if (!form.permissions.includes(btnKey)) form.permissions.push(btnKey)
  } else { const idx = form.permissions.indexOf(btnKey); if (idx > -1) form.permissions.splice(idx, 1) }
}

const getGroupPerms = (group) => {
  if (group === 'test') return testPermissions.value
  if (group === 'admin') return adminPermissions.value
  return []
}

const isGroupChecked = (group) => {
  const perms = getGroupPerms(group)
  return perms.every(p => form.permissions.includes(p.key))
}

const isGroupIndeterminate = (group) => {
  const perms = getGroupPerms(group)
  const checked = perms.filter(p => form.permissions.includes(p.key)).length
  return checked > 0 && checked < perms.length
}

const handleGroupSelect = (group, val) => {
  const perms = getGroupPerms(group)
  perms.forEach(p => {
    handlePageChange(p.key, val)
    if (val) {
      if (p.key === 'aivoice') {
        // aivoice 子入口已在 handlePageChange 里处理
      } else {
        const buttons = BUTTON_PERMISSIONS[p.key]
        if (buttons) Object.values(buttons).forEach(btn => { if (!form.permissions.includes(btn.key)) form.permissions.push(btn.key) })
      }
    }
  })
}

const isFeatureChecked = computed(() => FEATURE_PERMISSIONS.every(p => form.permissions.includes(p.key)))
const isFeatureIndeterminate = computed(() => {
  const checked = FEATURE_PERMISSIONS.filter(p => form.permissions.includes(p.key)).length
  return checked > 0 && checked < FEATURE_PERMISSIONS.length
})

const handleFeatureSelectAll = (val) => { FEATURE_PERMISSIONS.forEach(p => { handleFeatureChange(p.key, val) }) }

const handleFeatureChange = (featureKey, val) => {
  if (val) { if (!form.permissions.includes(featureKey)) form.permissions.push(featureKey) }
  else { const idx = form.permissions.indexOf(featureKey); if (idx > -1) form.permissions.splice(idx, 1) }
}

const allPermKeys = computed(() => [
  ...ALL_PERMISSIONS.map(p => p.key),
  ...Object.values(BUTTON_PERMISSIONS).flatMap(page => Object.values(page).map(btn => btn.key)),
  ...FEATURE_PERMISSIONS.map(p => p.key)
])
const isAllChecked = computed(() => allPermKeys.value.every(k => form.permissions.includes(k)))
const isAllIndeterminate = computed(() => {
  const checked = allPermKeys.value.filter(k => form.permissions.includes(k)).length
  return checked > 0 && checked < allPermKeys.value.length
})

const handleSelectAll = (val) => {
  if (val) {
    form.permissions = []
    ALL_PERMISSIONS.forEach(p => {
      form.permissions.push(p.key)
      if (p.key === 'aivoice') {
        // aivoice 子入口已在 ALL_PERMISSIONS 里，会被直接 push（parent: 'aivoice' 的条目）
      } else {
        const buttons = BUTTON_PERMISSIONS[p.key]
        if (buttons) Object.values(buttons).forEach(btn => form.permissions.push(btn.key))
      }
    })
    FEATURE_PERMISSIONS.forEach(p => form.permissions.push(p.key))
  } else { form.permissions = [] }
}

onMounted(() => { loadData(); bindTableHeight() })
onBeforeUnmount(() => { unbindTableHeight() })
</script>

<style scoped>
/* ==================== */
/* 页面布局 */
/* ==================== */
.role-management-content {
  display: flex;
  flex-direction: column;
  height: 100%;
}

/* ==================== */
/* 工具栏 */
/* ==================== */
.table-header {
  padding: 16px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #e2e8f0;
  flex-shrink: 0;
  background-color: rgba(248, 250, 252, 0.5);
  border-radius: 16px 16px 0 0;
  gap: 12px;
}

.header-left {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-shrink: 0;
}

.header-right {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-shrink: 0;
  margin-left: auto;
}

.header-right :deep(.el-input__wrapper) {
  height: 40px !important;
  min-height: 40px !important;
  padding: 1px 11px !important;
  box-sizing: border-box !important;
  display: flex !important;
  align-items: center !important;
}

.header-right :deep(.el-input__inner) {
  height: 38px !important;
  line-height: 38px !important;
}

.action-buttons {
  display: flex;
  gap: 8px;
  align-items: center;
}

.action-buttons .el-button {
  border-radius: 8px !important;
  font-weight: 500 !important;
  height: 40px !important;
  padding: 0 18px !important;
  font-size: 14px !important;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05) !important;
}

.action-buttons .el-button--primary {
  background: #4f46e5 !important;
  border: none !important;
}

.action-buttons .el-button--primary:hover {
  background: #4338ca !important;
}

/* ==================== */
/* 表格容器 */
/* ==================== */
.table-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  width: 100%;
  overflow: hidden;
}

.table-wrapper .table-container {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.table-wrapper :deep(.el-table) {
  width: 100%;
  position: relative;
}

.table-wrapper :deep(.el-table td.el-table__cell),
.table-wrapper :deep(.el-table th.el-table__cell) {
  height: 48px !important;
  padding: 0 12px !important;
}

.table-wrapper :deep(.el-table td.el-table__cell .cell),
.table-wrapper :deep(.el-table th.el-table__cell .cell) {
  line-height: 48px;
  padding: 0;
}

.table-wrapper :deep(.el-table__body-wrapper) {
  overflow-y: auto !important;
  overflow-x: auto !important;
}

.table-wrapper :deep(.el-table__body-wrapper)::-webkit-scrollbar { height: 8px; width: 8px; }
.table-wrapper :deep(.el-table__body-wrapper)::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }
.table-wrapper :deep(.el-table__body-wrapper)::-webkit-scrollbar-thumb:hover { background: #94a3b8; }
.table-wrapper :deep(.el-table__body-wrapper)::-webkit-scrollbar-track { background: #f1f5f9; }

.table-wrapper :deep(.el-table__header-wrapper) { overflow: hidden !important; position: relative; z-index: 10 !important; }
.table-wrapper :deep(.el-table__body-wrapper) { position: relative; z-index: 5 !important; }



/* ==================== */
/* 单元格内容 */
/* ==================== */
.permissions-display { display: flex; align-items: center; }
.no-permissions { display: flex; align-items: center; gap: 4px; color: #94a3b8; font-size: 13px; }
.permissions-summary { display: flex; align-items: center; gap: 4px; color: #10b981; cursor: pointer; font-size: 13px; }

/* ==================== */
/* 分页 */
/* ==================== */
.pagination-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: #fff;
  flex-shrink: 0;
  border-top: 1px solid #e2e8f0;
  border-radius: 0 0 16px 16px;
  min-height: 56px;
}

.pagination-container :deep(.el-pager li) { background: transparent; font-weight: 500; border-radius: 6px; min-width: 32px; height: 32px; }
.pagination-container :deep(.el-pager li.is-active) { background: #eef2ff; color: #4f46e5; font-weight: 600; }
.pagination-container :deep(.el-pager li:hover:not(.is-active)) { background: #f1f5f9; }
.pagination-container :deep(.el-pagination__total) { font-size: 14px; color: #64748b; }

/* ==================== */
/* 按钮 */
/* ==================== */
:deep(.el-button) { border-radius: 8px; font-weight: 500; transition: all 0.15s; }
:deep(.el-button:hover) { transform: none; box-shadow: none; }
:deep(.el-button--primary) { background: #4f46e5; border: none; box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05); }
:deep(.el-button--primary:hover) { background: #4338ca; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1); }
:deep(.el-button--danger) { background: #ef4444; border: none; }
:deep(.el-button--danger:hover) { background: #dc2626; }

/* ==================== */
/* 对话框 */
/* ==================== */
:deep(.el-dialog) { border-radius: 16px; overflow: hidden; }
:deep(.el-dialog__header) { padding: 20px 24px 16px; border-bottom: 1px solid #e2e8f0; margin-right: 0; }
:deep(.el-dialog__title) { font-size: 18px; font-weight: 600; color: #0f172a; }
:deep(.el-dialog__body) { padding: 24px; }
:deep(.el-dialog__footer) { padding: 16px 24px; border-top: 1px solid #e2e8f0; }
:deep(.el-form-item__label) { font-weight: 500; color: #334155; font-size: 14px; }
:deep(.el-input__wrapper), :deep(.el-select) { border-radius: 8px; }

/* ==================== */
/* 权限表格 */
/* ==================== */
.permission-table-wrapper {
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  max-height: 400px;
  overflow-y: auto;
}

.permission-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
  table-layout: fixed;
}

.permission-table th,
.permission-table td {
  text-align: left;
  border-bottom: 1px solid #e2e8f0;
  vertical-align: middle;
  box-sizing: border-box;
}

.permission-table thead th {
  background: rgba(248, 250, 252, 0.8);
  font-weight: 500;
  color: #64748b;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  position: sticky;
  top: 0;
  z-index: 1;
  padding: 12px 16px;
  height: 48px;
}

.permission-table .col-page { width: 180px; min-width: 180px; max-width: 180px; padding: 12px 16px; }
.permission-table .col-buttons { padding: 12px 16px; }
.permission-table .col-buttons .btn-list { display: flex; flex-wrap: wrap; gap: 8px 24px; align-items: center; min-height: 22px; }

.permission-table .group-row td {
  background: #f8fafc;
  padding: 10px 16px;
  height: 44px;
}

.permission-table .group-label { font-weight: 600; color: #4f46e5; }

.permission-table .perm-row td { background: #fff; height: 48px; }
.permission-table .perm-row:hover td { background: rgba(248, 250, 252, 0.8); }
.permission-table .no-buttons { color: #cbd5e1; display: inline-block; min-height: 22px; line-height: 22px; }
.permission-table :deep(.el-checkbox) { height: 22px; line-height: 22px; margin-right: 0; }
.permission-table :deep(.el-checkbox__label) { color: #334155; }

/* ==================== */
/* 行悬停 */
/* ==================== */
.table-wrapper :deep(.el-table__row:hover > td) { background: #f8fafc !important; }

.cell-text {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  width: 100%;
}
</style>