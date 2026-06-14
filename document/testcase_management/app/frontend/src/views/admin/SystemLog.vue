<template>
  <div class="log-page">
    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="filterForm" class="filter-form">
        <el-form-item :label="$t('systemLog.username')">
          <el-input v-model="filterForm.username" :placeholder="$t('systemLog.inputUsername')" clearable style="width: 150px;" />
        </el-form-item>
        <el-form-item :label="$t('systemLog.action')">
          <el-select v-model="filterForm.action" :placeholder="$t('systemLog.selectAction')" clearable style="width: 150px;">
            <el-option :label="$t('systemLog.all')" value="" />
            <el-option v-for="act in actions" :key="act" :label="getActionName(act)" :value="act" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('systemLog.startDate')">
          <el-date-picker
            v-model="filterForm.startDate"
            type="date"
            :placeholder="$t('systemLog.startDate')"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 150px;"
          />
        </el-form-item>
        <el-form-item :label="$t('systemLog.endDate')">
          <el-date-picker
            v-model="filterForm.endDate"
            type="date"
            :placeholder="$t('systemLog.endDate')"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 150px;"
          />
        </el-form-item>
        <el-form-item :label="$t('systemLog.keyword')">
          <el-input v-model="filterForm.keyword" :placeholder="$t('systemLog.searchKeyword')" clearable style="width: 200px;" />
        </el-form-item>
        <el-form-item class="filter-buttons">
          <div class="action-buttons">
            <el-button type="primary" size="large" :icon="Search" @click="handleSearch">{{ $t('systemLog.query') }}</el-button>
            <el-button size="large" :icon="Refresh" @click="handleReset">{{ $t('systemLog.reset') }}</el-button>
          </div>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 模块筛选标签组 -->
    <div class="module-filter-bar" v-if="modules.length > 0">
      <span class="module-filter-label">{{ $t('systemLog.module') }}</span>
      <div class="module-tags">
        <span
          class="module-tag"
          :class="{ active: filterForm.modules.length === 0 }"
          @click="selectAllModules"
        >{{ $t('systemLog.all') }}</span>
        <span
          v-for="mod in modules"
          :key="mod"
          class="module-tag"
          :class="{ active: filterForm.modules.includes(mod) }"
          @click="toggleModule(mod)"
        >{{ getModuleName(mod) }}</span>
      </div>
    </div>

    <el-card class="table-card" shadow="never">
      <div class="table-wrapper">
        <div class="table-container" ref="tableContainerRef">
          <el-table 
            ref="tableRef"
            :data="tableData" 
            style="width: 100%"
            :height="tableHeight"
            :header-cell-style="{ background: '#f8fafc', color: '#64748b', fontWeight: '500', fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.05em' }"
          >
            <el-table-column prop="username" :label="$t('systemLog.username')" min-width="120" />
            <el-table-column :label="$t('systemLog.module')" min-width="120">
              <template #default="{ row }">
                <el-tag :type="getModuleTagType(row.module)" size="small">
                  {{ getModuleName(row.module) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column :label="$t('systemLog.action')" min-width="100">
              <template #default="{ row }">
                <el-tag :type="getActionTagType(row.action)" size="small">
                  {{ getActionName(row.action) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="description" :label="$t('systemLog.operationDesc')" min-width="300">
              <template #default="{ row }">
                <el-tooltip :content="row.description" placement="top" :disabled="!row.description || row.description.length < 30" :show-after="500">
                  <span style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap; display: block;">{{ row.description }}</span>
                </el-tooltip>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" :label="$t('systemLog.operationTime')" min-width="180" />
            <el-table-column :label="$t('common.operation')" width="80" align="center" fixed="right">
              <template #default="{ row }">
                <el-button type="primary" link :icon="View" @click="handleViewDetail(row)">
                  {{ $t('systemLog.detail') }}
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>

      <div class="pagination-container">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="size"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @current-change="async () => { await loadData(); await nextTick(); scrollToTop(); }"
          @size-change="async () => { await loadData(); await nextTick(); scrollToTop(); }"
        />
      </div>
    </el-card>

    <!-- 详情对话框 -->
    <el-dialog v-model="detailVisible" :title="$t('systemLog.logDetail')" width="700px" @closed="handleDialogClosed">
      <el-descriptions :column="1" border>
        <el-descriptions-item label="ID">{{ currentLog.id }}</el-descriptions-item>
        <el-descriptions-item :label="$t('systemLog.username')">{{ currentLog.username }}</el-descriptions-item>
        <el-descriptions-item :label="$t('systemLog.module')">{{ getModuleName(currentLog.module) }}</el-descriptions-item>
        <el-descriptions-item :label="$t('systemLog.action')">{{ getActionName(currentLog.action) }}</el-descriptions-item>
        <el-descriptions-item :label="$t('systemLog.operationDesc')">{{ currentLog.description }}</el-descriptions-item>
        <el-descriptions-item :label="$t('systemLog.ipAddress')">{{ currentLog.ip_address }}</el-descriptions-item>
        <el-descriptions-item :label="$t('systemLog.requestMethod')">{{ currentLog.request_method }}</el-descriptions-item>
        <el-descriptions-item :label="$t('systemLog.requestPath')">{{ currentLog.request_path }}</el-descriptions-item>
        <el-descriptions-item :label="$t('systemLog.requestParams')">
          <pre style="margin: 0; white-space: pre-wrap; word-break: break-all;">{{ currentLog.request_params || $t('systemLog.none') }}</pre>
        </el-descriptions-item>
        <el-descriptions-item :label="$t('systemLog.responseStatus')">
          <el-tag :type="currentLog.response_status === 200 ? 'success' : 'danger'" size="small">
            {{ currentLog.response_status }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item :label="$t('systemLog.userAgent')">
          <div style="max-height: 100px; overflow-y: auto; word-break: break-all;">
            {{ currentLog.user_agent }}
          </div>
        </el-descriptions-item>
        <el-descriptions-item :label="$t('systemLog.operationTime')">{{ currentLog.created_at }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { getSystemLogs, getLogModules, getLogActions } from '../../api/systemLog'
import { ElMessage } from 'element-plus'
import { Search, Refresh, View } from '@element-plus/icons-vue'
import { usePagination } from '../../composables/usePagination'
import { useTableHeight } from '../../composables/useTableHeight'
import { useScrollToTop } from '../../composables/useScrollToTop'
import { useLoadingStore } from '../../stores/loading'

const { t } = useI18n()
const { tableContainerRef, tableHeight, bindTableHeight, unbindTableHeight } = useTableHeight()
const tableRef = ref(null)
const { scrollToTop } = useScrollToTop(tableRef)
const loadingStore = useLoadingStore()

const loading = ref(false)
const tableData = ref([])
const { page, size, total } = usePagination('systemLog', 20)
const modules = ref([])
const actions = ref([])
const detailVisible = ref(false)
const currentLog = ref({})

const MODULES_PREF_KEY = 'systemLog_module_preference'

const filterForm = reactive({
  username: '',
  modules: [],
  action: '',
  keyword: '',
  startDate: '',
  endDate: ''
})

// 模块名称映射
const getModuleNameMap = () => ({
  'testcases': t('systemLog.modules.testcases'),
  'testplans': t('systemLog.modules.testplans'),
  'executions': t('systemLog.modules.executions'),
  'reports': t('systemLog.modules.reports'),
  'zmind': t('systemLog.modules.zmind'),
  'validation': t('systemLog.modules.validation'),
  'users': t('systemLog.modules.users'),
  'projects': t('systemLog.modules.projects'),
  'roles': t('systemLog.modules.roles'),
  'database': t('systemLog.modules.database'),
  'auth': t('systemLog.modules.auth'),
  'user_projects': t('systemLog.modules.user_projects'),
  'system': t('systemLog.modules.system'),
  'review_plan': t('systemLog.modules.review_plan'),
  'organization': t('systemLog.modules.organization'),
  'position_tags': t('systemLog.modules.position_tags'),
  'teams': t('systemLog.modules.teams')
})

// 操作名称映射
const getActionNameMap = () => ({
  'create': t('systemLog.actions.create'),
  'update': t('systemLog.actions.update'),
  'delete': t('systemLog.actions.delete'),
  'import': t('systemLog.actions.import'),
  'export': t('systemLog.actions.export'),
  'login': t('systemLog.actions.login'),
  'logout': t('systemLog.actions.logout'),
  'view': t('systemLog.actions.view'),
  'search': t('systemLog.actions.search'),
  'execute': t('systemLog.actions.execute'),
  'generate': t('systemLog.actions.generate'),
  'assign': t('systemLog.actions.assign'),
  'sync': t('systemLog.actions.sync'),
  'remove': t('systemLog.actions.remove'),
  'download': t('systemLog.actions.download'),
  'upload': t('systemLog.actions.upload')
})

const getModuleName = (module) => {
  const moduleNames = getModuleNameMap()
  return moduleNames[module] || module
}

const getActionName = (action) => {
  const actionNames = getActionNameMap()
  return actionNames[action] || action
}

const getModuleTagType = (module) => {
  const adminModules = ['users', 'projects', 'roles', 'database', 'organization', 'position_tags', 'system', 'teams', 'user_projects']
  return adminModules.includes(module) ? 'danger' : 'primary'
}

const getActionTagType = (action) => {
  const typeMap = {
    'create': 'success',
    'update': 'warning',
    'delete': 'danger',
    'import': 'primary',
    'export': 'info',
    'login': 'success',
    'logout': 'info',
    'view': 'info',
    'search': 'info',
    'execute': 'primary',
    'generate': 'success',
    'assign': 'warning',
    'sync': 'primary'
  }
  return typeMap[action] || 'info'
}

const getMethodTagType = (method) => {
  const typeMap = {
    'GET': 'info',
    'POST': 'success',
    'PUT': 'warning',
    'DELETE': 'danger'
  }
  return typeMap[method] || 'info'
}

const loadData = async () => {
  loadingStore.showLoading()
  loading.value = true
  try {
    const params = {
      page: page.value,
      size: size.value,
      username: filterForm.username || undefined,
      modules: filterForm.modules.length > 0 ? filterForm.modules.join(',') : undefined,
      action: filterForm.action || undefined,
      keyword: filterForm.keyword || undefined,
      start_date: filterForm.startDate || undefined,
      end_date: filterForm.endDate || undefined
    }
    
    const res = await getSystemLogs(params)
    tableData.value = res.data.records
    total.value = res.data.total
  } catch (error) {
    ElMessage.error(t('systemLog.loadFailed'))
  } finally {
    loadingStore.hideLoading()
    loading.value = false
  }
}

const loadModules = async () => {
  try {
    const res = await getLogModules()
    modules.value = res.data
    // 加载用户偏好或设置默认值（排除 executions）
    const saved = localStorage.getItem(MODULES_PREF_KEY)
    if (saved) {
      try {
        const parsed = JSON.parse(saved)
        // 只保留当前存在的模块
        filterForm.modules = parsed.filter(m => modules.value.includes(m))
      } catch { filterForm.modules = [] }
    } else {
      // 默认勾选除 executions 外的所有模块
      filterForm.modules = modules.value.filter(m => m !== 'executions')
    }
    // 应用默认筛选重新加载数据
    loadData()
  } catch (error) {
    // 静默失败
  }
}

const saveModulePreference = () => {
  localStorage.setItem(MODULES_PREF_KEY, JSON.stringify(filterForm.modules))
}

const toggleModule = (mod) => {
  const idx = filterForm.modules.indexOf(mod)
  if (idx >= 0) {
    filterForm.modules.splice(idx, 1)
  } else {
    filterForm.modules.push(mod)
  }
  saveModulePreference()
  page.value = 1
  loadData()
}

const selectAllModules = () => {
  filterForm.modules = []
  saveModulePreference()
  page.value = 1
  loadData()
}

const loadActions = async () => {
  try {
    const res = await getLogActions()
    actions.value = res.data
  } catch (error) {
    // 静默失败
  }
}

const handleSearch = () => {
  page.value = 1
  loadData()
}

const handleReset = () => {
  filterForm.username = ''
  filterForm.modules = []
  filterForm.action = ''
  filterForm.keyword = ''
  filterForm.startDate = ''
  filterForm.endDate = ''
  page.value = 1
  localStorage.removeItem(MODULES_PREF_KEY)
  loadData()
}

const handleDialogClosed = () => {
  // 对话框关闭后,移除所有按钮的焦点
  if (document.activeElement instanceof HTMLElement) {
    document.activeElement.blur()
  }
}

const handleViewDetail = (row) => {
  currentLog.value = row
  detailVisible.value = true
}

onMounted(() => {
  loadModules()
  loadActions()
  bindTableHeight()
})
onBeforeUnmount(() => {
  unbindTableHeight()
})
</script>

<style scoped>
/* ==================== */
/* 页面布局 */
/* ==================== */
.log-page {
  height: 100%;
  background: #f8fafc;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  padding: 24px;
  gap: 16px;
}

.log-page::-webkit-scrollbar { width: 8px; }
.log-page::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }
.log-page::-webkit-scrollbar-thumb:hover { background: #94a3b8; }
.log-page::-webkit-scrollbar-track { background: #f1f5f9; }

/* ==================== */
/* 筛选卡片 */
/* ==================== */
.filter-card {
  border-radius: 16px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  flex-shrink: 0;
  background: #fff;
}

.filter-form {
  margin: 0;
}

.filter-form :deep(.el-form-item) {
  margin-bottom: 0;
  margin-right: 16px;
}

.filter-form :deep(.el-form-item__label) {
  font-weight: 500;
  color: #334155;
  font-size: 14px;
}

.filter-buttons {
  margin-right: 0 !important;
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
/* 模块筛选标签组 */
/* ==================== */
.module-filter-bar {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 20px;
  background: #fff;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  flex-shrink: 0;
}

.module-filter-label {
  font-size: 13px;
  font-weight: 500;
  color: #64748b;
  white-space: nowrap;
  line-height: 28px;
}

.module-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.module-tag {
  display: inline-block;
  padding: 4px 12px;
  font-size: 12px;
  color: #64748b;
  background: #f1f5f9;
  border-radius: 14px;
  cursor: pointer;
  transition: all 0.15s;
  user-select: none;
  line-height: 20px;
}

.module-tag:hover {
  background: #e2e8f0;
  color: #334155;
}

.module-tag.active {
  background: #eef2ff;
  color: #4f46e5;
  font-weight: 500;
}

/* ==================== */
/* 表格卡片 */
/* ==================== */
.table-card {
  border-radius: 16px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  background: #fff;
}

.table-card :deep(.el-card__body) {
  display: flex;
  flex-direction: column;
  padding: 0 !important;
  flex: 1;
  min-height: 0;
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

/* 表格单元格高度 */
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

/* 表格滚动 */
.table-wrapper :deep(.el-table__body-wrapper) {
  overflow-y: auto !important;
  overflow-x: auto !important;
}

.table-wrapper :deep(.el-table__body-wrapper)::-webkit-scrollbar {
  height: 8px;
  width: 8px;
}

.table-wrapper :deep(.el-table__body-wrapper)::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}

.table-wrapper :deep(.el-table__body-wrapper)::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

.table-wrapper :deep(.el-table__body-wrapper)::-webkit-scrollbar-track {
  background: #f1f5f9;
}

.table-wrapper :deep(.el-table__header-wrapper) {
  overflow: hidden !important;
  position: relative;
  z-index: 10 !important;
}

.table-wrapper :deep(.el-table__body-wrapper) {
  position: relative;
  z-index: 5 !important;
}



/* 行悬停效果 */
.table-wrapper :deep(.el-table__row:hover > td) {
  background: #f8fafc !important;
}

/* 固定列不透明背景 */
.table-wrapper :deep(.el-table td.el-table__cell) {
  background: #fff;
}

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

.pagination-container :deep(.el-pager li) {
  background: transparent;
  font-weight: 500;
  border-radius: 6px;
  min-width: 32px;
  height: 32px;
}

.pagination-container :deep(.el-pager li.is-active) {
  background: #eef2ff;
  color: #4f46e5;
  font-weight: 600;
}

.pagination-container :deep(.el-pager li:hover:not(.is-active)) {
  background: #f1f5f9;
}

.pagination-container :deep(.el-pagination__total) {
  font-size: 14px;
  color: #64748b;
}

/* ==================== */
/* 按钮 */
/* ==================== */
:deep(.el-button) {
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.15s;
}

:deep(.el-button:hover) {
  transform: none;
  box-shadow: none;
}

:deep(.el-button--primary) {
  background: #4f46e5;
  border: none;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

:deep(.el-button--primary:hover) {
  background: #4338ca;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

:deep(.el-button--danger) {
  background: #ef4444;
  border: none;
}

:deep(.el-button--danger:hover) {
  background: #dc2626;
}

/* ==================== */
/* 对话框 */
/* ==================== */
:deep(.el-dialog) {
  border-radius: 16px;
  overflow: hidden;
}

:deep(.el-dialog__header) {
  padding: 20px 24px 16px;
  border-bottom: 1px solid #e2e8f0;
  margin-right: 0;
}

:deep(.el-dialog__title) {
  font-size: 18px;
  font-weight: 600;
  color: #0f172a;
}

:deep(.el-dialog__body) {
  padding: 24px;
}

:deep(.el-dialog__footer) {
  padding: 16px 24px;
  border-top: 1px solid #e2e8f0;
}

:deep(.el-descriptions__label) {
  font-weight: 600;
  width: 120px;
  color: #334155;
}

:deep(.el-input__wrapper),
:deep(.el-select) {
  border-radius: 8px;
}
</style>
