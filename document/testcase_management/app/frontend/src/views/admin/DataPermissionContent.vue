<template>
  <div class="data-permission-content">
    <!-- 工具栏 -->
    <div class="table-header">
      <div class="header-left">
        <div class="action-buttons">
          <el-button type="primary" :icon="Plus" @click="handleCreate">
            {{ $t('positionTag.createTag') }}
          </el-button>
        </div>
      </div>
      <div class="header-right">
        <el-input
          v-model="searchKeyword"
          :placeholder="$t('positionTag.searchPlaceholder')"
          style="width: 250px;"
          size="large"
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
          <el-table-column prop="name" :label="$t('positionTag.name')" min-width="180" align="center">
            <template #default="scope">
              <el-tooltip :content="scope.row.name" placement="top" :teleported="true" :show-after="500">
                <span class="cell-text">{{ scope.row.name }}</span>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column label="数据权限范围" min-width="300">
            <template #default="scope">
              <div class="permissions-display">
                <el-tooltip placement="top" :teleported="true" :show-after="500">
                  <template #content>
                    <div style="max-width: 350px;">{{ getPermissionDetail(scope.row) }}</div>
                  </template>
                  <div class="permissions-summary">
                    <el-icon><Checked /></el-icon>
                    <span>{{ getPermissionSummary(scope.row) }}</span>
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
          <el-table-column prop="created_at" :label="$t('common.createdAt')" min-width="170" align="center">
            <template #default="scope">
              <el-tooltip :content="formatDate(scope.row.created_at)" placement="top" :teleported="true" :show-after="500">
                <span class="cell-text">{{ formatDate(scope.row.created_at) }}</span>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column :label="$t('common.operation')" min-width="200" align="center" fixed="right">
            <template #default="scope">
              <el-button type="primary" size="default" :icon="Edit" @click="handleEdit(scope.row)">
                {{ $t('common.edit') }}
              </el-button>
              <el-button 
                v-if="!scope.row.is_system"
                type="danger" 
                size="default" 
                :icon="Delete" 
                @click="handleDelete(scope.row)"
              >
                {{ $t('common.delete') }}
              </el-button>
              <el-tooltip v-else content="系统默认数据权限不能删除" placement="top" :show-after="500">
                <el-button type="danger" size="default" :icon="Delete" disabled>
                  {{ $t('common.delete') }}
                </el-button>
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
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="700px" :close-on-click-modal="false">
      <el-form :model="form" ref="formRef" label-position="top">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item :label="$t('positionTag.name')" required>
              <el-input v-model="form.name" :placeholder="$t('positionTag.inputName')" maxlength="50" show-word-limit />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item :label="$t('common.description')">
              <el-input v-model="form.description" :placeholder="$t('positionTag.inputDescription')" maxlength="255" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="数据权限配置">
          <div class="permission-hint">
            <el-icon><InfoFilled /></el-icon>
            <span>所有权限均基于用户所属组织，不能超出组织范围</span>
          </div>
          <div class="permission-table-wrapper">
            <table class="permission-table">
              <thead>
                <tr>
                  <th class="col-module">数据模块</th>
                  <th class="col-scope">可见范围</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in permissionModules" :key="item.key" class="perm-row">
                  <td class="col-module">
                    <div class="module-info">
                      <el-icon :size="18"><component :is="item.icon" /></el-icon>
                      <span>{{ item.label }}</span>
                    </div>
                  </td>
                  <td class="col-scope">
                    <el-radio-group v-model="form.contentPermissions[item.key]" size="default">
                      <el-tooltip 
                        v-for="opt in scopeOptions" 
                        :key="opt.value"
                        :content="opt.desc"
                        placement="top"
                       :show-after="500">
                        <el-radio-button :value="opt.value">
                          <el-icon :size="14"><component :is="opt.icon" /></el-icon>
                          <span>{{ opt.label }}</span>
                        </el-radio-button>
                      </el-tooltip>
                    </el-radio-group>
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
import { positionTagApi } from '../../api/positionTag'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete, Search, Checked, Document, Tickets, Calendar, Bell, View, FolderOpened, User, InfoFilled } from '@element-plus/icons-vue'
import { useTableHeight } from '../../composables/useTableHeight'

const { t } = useI18n()
const { tableContainerRef, tableHeight, bindTableHeight, unbindTableHeight } = useTableHeight()
const tableRef = ref(null)

const tableData = ref([])
const page = ref(1)
const size = ref(10)
const total = ref(0)
const searchKeyword = ref('')
const dialogVisible = ref(false)
const dialogTitle = computed(() => form.id ? t('positionTag.editTag') : t('positionTag.createTag'))
const submitting = ref(false)
const formRef = ref(null)

const form = reactive({
  id: null,
  name: '',
  description: '',
  contentPermissions: { testcase: 'all', report: 'all', testplan: 'all', notification: 'all' }
})

// 权限模块配置
const permissionModules = [
  { key: 'testcase', label: '测试用例', icon: Document },
  { key: 'testplan', label: '测试计划', icon: Calendar },
  { key: 'report', label: '测试报告', icon: Tickets },
  { key: 'notification', label: '通知消息', icon: Bell }
]

// 可见范围选项
const scopeOptions = [
  { value: 'all', label: '组织可见', icon: View, desc: '所属组织下全部数据' },
  { value: 'project', label: '项目组可见', icon: FolderOpened, desc: '所属项目组下数据' },
  { value: 'personal', label: '仅个人', icon: User, desc: '个人创建/分配/授权的数据' }
]

const scopeLabels = { all: '组织', project: '项目组', personal: '个人' }

const getPermissionSummary = (row) => {
  if (!row.content_permissions || row.content_permissions.length === 0) {
    return '组织下全部数据可见'
  }
  const perms = {}
  row.content_permissions.forEach(p => {
    const [key, value] = p.split(':')
    perms[key] = value
  })
  const allCount = Object.values(perms).filter(v => v === 'all').length
  const projectCount = Object.values(perms).filter(v => v === 'project').length
  const personalCount = Object.values(perms).filter(v => v === 'personal').length
  
  const parts = []
  if (allCount > 0) parts.push(`${allCount}项组织可见`)
  if (projectCount > 0) parts.push(`${projectCount}项项目组可见`)
  if (personalCount > 0) parts.push(`${personalCount}项仅个人`)
  return parts.join('，') || '组织下全部数据可见'
}

const getPermissionDetail = (row) => {
  if (!row.content_permissions || row.content_permissions.length === 0) {
    return '所有数据模块均为组织范围可见'
  }
  const perms = {}
  row.content_permissions.forEach(p => {
    const [key, value] = p.split(':')
    perms[key] = value
  })
  const moduleLabels = { testcase: '测试用例', testplan: '测试计划', report: '测试报告', notification: '通知消息' }
  return Object.entries(perms).map(([key, value]) => `${moduleLabels[key] || key}: ${scopeLabels[value] || value}`).join('、')
}

const formatDate = (date) => {
  if (!date) return '-'
  return new Date(date).toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

const loadData = async () => {
  try {
    const res = await positionTagApi.getPositionTags()
    if (res.data && res.data.records) {
      tableData.value = res.data.records
      total.value = res.data.total || 0
    } else if (Array.isArray(res.data)) {
      tableData.value = res.data
      total.value = res.data.length
    } else {
      tableData.value = []
      total.value = 0
    }
  } catch (error) {
    tableData.value = []
    total.value = 0
    ElMessage.error('加载数据失败')
  }
}

const handleSearch = () => { page.value = 1; loadData() }

const handleCreate = () => {
  form.id = null
  form.name = ''
  form.description = ''
  form.contentPermissions = { testcase: 'all', report: 'all', testplan: 'all', notification: 'all' }
  dialogVisible.value = true
}

const handleEdit = (row) => {
  form.id = row.id
  form.name = row.name
  form.description = row.description
  if (row.content_permissions && Array.isArray(row.content_permissions)) {
    const permissions = { testcase: 'all', report: 'all', testplan: 'all', notification: 'all' }
    row.content_permissions.forEach(perm => {
      const [key, value] = perm.split(':')
      if (permissions.hasOwnProperty(key)) permissions[key] = value
    })
    form.contentPermissions = permissions
  } else {
    form.contentPermissions = { testcase: 'all', report: 'all', testplan: 'all', notification: 'all' }
  }
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!form.name || !form.name.trim()) {
    ElMessage.warning('请输入数据权限名称')
    return
  }
  submitting.value = true
  try {
    const payload = {
      name: form.name,
      description: form.description,
      content_permissions: Object.entries(form.contentPermissions).map(([key, value]) => `${key}:${value}`),
      notification_permissions: []
    }
    if (form.id) {
      await positionTagApi.updatePositionTag(form.id, payload)
      ElMessage.success('更新成功')
    } else {
      await positionTagApi.createPositionTag(payload)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadData()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '操作失败')
  } finally {
    submitting.value = false
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定删除该数据权限吗？此操作不可恢复。', '删除确认', {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await positionTagApi.deletePositionTag(row.id)
    ElMessage.success('删除成功')
    loadData()
  } catch (error) {
    if (error !== 'cancel') ElMessage.error(error.response?.data?.detail || '删除失败')
  }
}

onMounted(() => { loadData(); bindTableHeight() })
onBeforeUnmount(() => { unbindTableHeight() })
</script>

<style scoped>
/* ==================== */
/* 页面布局 */
/* ==================== */
.data-permission-content { display: flex; flex-direction: column; height: 100%; }

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

/* 固定列 */


/* ==================== */
/* 单元格内容 */
/* ==================== */
.permissions-display { display: flex; align-items: center; }
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
/* 权限提示 */
/* ==================== */
.permission-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 12px;
  margin-bottom: 12px;
  background: #eef2ff;
  border-radius: 8px;
  color: #4f46e5;
  font-size: 13px;
}

.permission-hint .el-icon {
  font-size: 16px;
}

/* ==================== */
/* 权限表格 */
/* ==================== */
.permission-table-wrapper {
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  overflow: hidden;
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
  padding: 12px 16px;
  height: 48px;
}

.permission-table .col-module {
  width: 160px;
  min-width: 160px;
  max-width: 160px;
  padding: 14px 16px;
}

.permission-table .col-scope {
  padding: 14px 16px;
}

.permission-table .perm-row td {
  background: #fff;
  height: 56px;
}

.permission-table .perm-row:last-child td {
  border-bottom: none;
}

.permission-table .perm-row:hover td {
  background: rgba(248, 250, 252, 0.8);
}

.permission-table .module-info {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #334155;
}

.permission-table .module-info .el-icon {
  color: #4f46e5;
}

.permission-table :deep(.el-radio-button__inner) {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 14px;
}

.permission-table :deep(.el-radio-group) {
  flex-wrap: nowrap;
}

.permission-table :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background-color: #4f46e5;
  border-color: #4f46e5;
  box-shadow: -1px 0 0 0 #4f46e5;
}

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
