<template>
  <div class="zmind-container" v-loading="loadingProjects && zmindProjects.length === 0" :element-loading-text="$t('zmind.loadingProjects')">
    <div class="config-section">
      <el-form :model="configForm" label-width="120px" label-position="top">
        <el-form-item :label="$t('zmind.projectName')">
          <el-select
            v-model="configForm.projectIdentifier"
            :placeholder="$t('zmind.selectProject')"
            filterable
            :loading="loadingProjects"
            style="width: 100%"
          >
            <el-option
              v-for="project in zmindProjects"
              :key="project.identifier"
              :label="project.name"
              :value="project.identifier"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button 
            type="primary" 
            @click="handleSearch" 
            :disabled="!configForm.projectIdentifier || !hasButton('zmind', 'query')"
            :loading="loadingTestcases"
          >
            {{ $t('zmind.searchCases') }}
          </el-button>
        </el-form-item>
      </el-form>
    </div>

    <div class="table-section" v-loading="loadingTestcases">
      <div class="search-bar">
        <div class="search-actions">
          <el-button 
            @click="selectAll" 
            :icon="CircleCheck" 
            :disabled="totalTestcases === 0 || !hasButton('zmind', 'import')"
          >
            {{ $t('zmind.selectAll') }} ({{ totalTestcases }})
          </el-button>
          <el-button 
            @click="clearSelection" 
            :icon="Close"
            :disabled="!hasButton('zmind', 'import')"
          >
            {{ $t('zmind.clearSelection') }}
          </el-button>
          <el-button 
            type="primary" 
            @click="handleImport" 
            :disabled="selectedRows.length === 0 || !hasButton('zmind', 'import')"
            :loading="importing"
            :icon="Download"
          >
            {{ $t('zmind.importSelected') }} ({{ selectedRows.length }})
          </el-button>
        </div>
        <el-input
          v-model="keyword"
          :placeholder="$t('zmind.searchPlaceholder')"
          style="width: 300px;"
          @input="handleKeywordChange"
          clearable
        >
          <template #append>
            <el-button @click="handleSearch" :icon="Search" />
          </template>
        </el-input>
      </div>

      <div class="table-wrapper">
      <el-table
        ref="tableRef"
        :data="tableData"
        style="width: 100%; margin-top: 20px;"
        height="100%"
        :header-cell-style="{ background: '#f0f1fb', color: '#606266', fontWeight: '600' }"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column :label="$t('zmind.zmindId')" width="100">
          <template #default="{ row }">
            <a 
              :href="`https://zmind.whaletv.com/issues/${row.zmindId}`" 
              target="_blank" 
              class="zmind-link"
            >
              {{ row.zmindId }}
            </a>
          </template>
        </el-table-column>
        <el-table-column prop="name" :label="$t('zmind.caseName')" min-width="250" :show-overflow-tooltip="{ showAfter: 500 }" />
        <el-table-column prop="status" :label="$t('zmind.status')" width="100" />
        <el-table-column prop="priority" :label="$t('zmind.priority')" width="100" />
        <el-table-column prop="author" :label="$t('zmind.author')" width="120" />
        <el-table-column prop="steps" :label="$t('zmind.description')" min-width="300" :show-overflow-tooltip="{ showAfter: 500 }" />
      </el-table>
      </div>

      <!-- 分页 -->
      <div class="pagination-container" v-if="totalTestcases > 0">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="totalTestcases"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
defineOptions({ name: 'ZmindIntegration' })
import { ref, reactive, onMounted, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { getZmindProjects } from '../../api/zmind'
import { ElMessage } from 'element-plus'
import { Connection, Key, Search, Download, Folder, CircleCheck, Close } from '@element-plus/icons-vue'
import { useProject } from '../../composables/useProject'
import { useUserRole } from '../../composables/useUserRole'
import { usePagination } from '../../composables/usePagination'
import { useScrollToTop } from '../../composables/useScrollToTop'
import { useLoadingStore } from '../../stores/loading'

const { t } = useI18n()
const { currentProjectId } = useProject()
const { hasButton } = useUserRole()
const loadingStore = useLoadingStore()

// API Key从后端配置获取
let ZMIND_API_KEY = '51be09c67413a5c7c253d96ed1b09550e56ec1a7'  // 默认值

const configForm = reactive({
  projectIdentifier: '',  // 项目标识符（用于API调用）
  apiKey: ZMIND_API_KEY
})

const keyword = ref('')
const tableData = ref([])
const selectedRows = ref([])
const zmindProjects = ref([])
const loadingProjects = ref(false)
const loadingTestcases = ref(false)  // 查询测试用例的loading
const importing = ref(false)  // 导入的loading
const projectsLoaded = ref(false)  // 标记项目是否已加载

// 分页相关
const allTestcases = ref([])  // 存储所有测试用例（原始数据）
const filteredTestcases = ref([])  // 存储过滤后的测试用例
const { page: currentPage, size: pageSize, total: totalTestcases } = usePagination('zmindIntegration', 20)

// 加载Zmind配置并预加载项目列表
const loadZmindConfig = async () => {
  try {
    const res = await getZmindConfig()
    ZMIND_API_KEY = res.data.apiKey
    configForm.apiKey = ZMIND_API_KEY
    
    // 立即加载配置的项目及子项目
    await loadProjects()
  } catch (error) {
    ElMessage.error(t('zmind.loadConfigFailed') + ': ' + (error.message || t('zmind.unknownError')))
  }
}

// 加载项目列表（配置的项目及其子项目）
const loadProjects = async () => {
  loadingStore.showLoading()
  // 如果已经加载过，直接返回
  if (projectsLoaded.value && zmindProjects.value.length > 0) {
    loadingStore.hideLoading()
    return
  }
  
  loadingProjects.value = true
  try {
    const res = await getZmindProjects({ apiKey: ZMIND_API_KEY })
    zmindProjects.value = res.data
    projectsLoaded.value = true  // 标记为已加载
  } catch (error) {
    ElMessage.error(t('zmind.loadProjectsFailed') + ': ' + (error.response?.data?.detail || error.message || t('zmind.unknownError')))
  } finally {
    loadingStore.hideLoading()
    loadingProjects.value = false
  }
}

// 移除搜索项目功能

const handleSaveConfig = async () => {
  if (!configForm.projectName || !configForm.projectName.trim()) {
    ElMessage.warning(t('zmind.configWarningProject'))
    return
  }
  if (!configForm.apiKey || !configForm.apiKey.trim()) {
    ElMessage.warning(t('zmind.configWarningKey'))
    return
  }
  try {
    await configZmindApi(configForm)
    ElMessage.success(t('zmind.configSuccess'))
  } catch (error) {
    ElMessage.error(t('zmind.configFailed'))
  }
}

const handleSearch = async () => {
  if (!configForm.projectIdentifier) {
    ElMessage.warning(t('zmind.selectProjectWarning'))
    return
  }
  
  // 点击"查询用例"按钮，清空现有数据并从后端获取最新数据
  loadingTestcases.value = true
  
  // 清空现有数据
  allTestcases.value = []
  filteredTestcases.value = []
  tableData.value = []
  totalTestcases.value = 0
  selectedRows.value = []
  currentPage.value = 1
  
  try {
    const res = await getZmindTestCases({ 
      projectName: configForm.projectIdentifier,
      apiKey: ZMIND_API_KEY,
      keyword: ''  // 不传关键词，获取所有数据
    })
    
    // 存储所有测试用例
    allTestcases.value = res.data
    
    // 如果有关键词，进行过滤
    if (keyword.value.trim()) {
      filterTestcases()
    } else {
      filteredTestcases.value = res.data
      totalTestcases.value = res.data.length
      // 更新当前页数据
      updatePageData()
    }
    
    if (res.data.length === 0) {
      ElMessage.info(t('zmind.searchNoResults'))
    } else {
      ElMessage.success(t('zmind.searchSuccessCount', { count: res.data.length }))
    }
  } catch (error) {
    const errorMsg = error.response?.data?.detail || error.message || t('common.failed')
    
    // 如果是超时错误，给出更友好的提示
    if (errorMsg.includes('timeout') || errorMsg.includes('超时')) {
      ElMessage.warning(t('zmind.queryTimeout'))
    } else {
      ElMessage.error(`${t('common.failed')}: ${errorMsg}`)
    }
  } finally {
    loadingTestcases.value = false
  }
}

// 前端过滤测试用例
const filterTestcases = () => {
  const kw = keyword.value.trim().toLowerCase()
  if (!kw) {
    filteredTestcases.value = allTestcases.value
  } else {
    filteredTestcases.value = allTestcases.value.filter(item => {
      return (
        item.name?.toLowerCase().includes(kw) ||
        item.zmindId?.toString().includes(kw) ||
        item.steps?.toLowerCase().includes(kw) ||
        item.status?.toLowerCase().includes(kw) ||
        item.priority?.toLowerCase().includes(kw) ||
        item.author?.toLowerCase().includes(kw)
      )
    })
  }
  
  totalTestcases.value = filteredTestcases.value.length
  currentPage.value = 1
  updatePageData()
}

// 处理关键词变化（实时过滤）
const handleKeywordChange = () => {
  // 只有在已经查询过数据的情况下才进行前端过滤
  if (allTestcases.value.length > 0) {
    filterTestcases()
  }
}

// 更新当前页数据
const updatePageData = () => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  tableData.value = filteredTestcases.value.slice(start, end)
  
  // 如果已经选择了全部，需要同步当前页的勾选状态
  if (selectedRows.value.length === filteredTestcases.value.length && tableRef.value) {
    isSelectingAll.value = true
    setTimeout(() => {
      tableData.value.forEach(row => {
        tableRef.value.toggleRowSelection(row, true)
      })
      isSelectingAll.value = false
    }, 0)
  }
}

const tableRef = ref(null)
const { scrollToTop } = useScrollToTop(tableRef)
// 页码改变
const handlePageChange = async (page) => {
  currentPage.value = page
  updatePageData()
  await nextTick()
  scrollToTop()
}

// 每页数量改变
const handleSizeChange = async (size) => {
  pageSize.value = size
  currentPage.value = 1
  updatePageData()
  await nextTick()
  scrollToTop()
}

// 选择全部用例
const selectAll = () => {
  isSelectingAll.value = true
  
  // 将所有过滤后的用例添加到选中列表
  selectedRows.value = [...filteredTestcases.value]
  
  // 同步表格中当前页的勾选状态
  if (tableRef.value) {
    setTimeout(() => {
      tableData.value.forEach(row => {
        tableRef.value.toggleRowSelection(row, true)
      })
      isSelectingAll.value = false
    }, 0)
  } else {
    isSelectingAll.value = false
  }
  
  ElMessage.success(t('zmind.selectAll') + ` ${filteredTestcases.value.length}`)
}

// 清空选择
const clearSelection = () => {
  isSelectingAll.value = false
  if (tableRef.value) {
    tableRef.value.clearSelection()
  }
  selectedRows.value = []
}

// tableRef 已在上面声明，这里删除重复声明

const handleSync = () => {
  handleSearch()
}

const handleSelectionChange = (selection) => {
  // 如果不是"选择全部"操作，才更新selectedRows
  if (!isSelectingAll.value) {
    selectedRows.value = selection
  }
}

const isSelectingAll = ref(false)  // 标记是否正在执行"选择全部"操作

const handleImport = async () => {
  if (!currentProjectId.value) {
    ElMessage.warning(t('zmind.importWarningProject'))
    return
  }
  
  if (selectedRows.value.length === 0) {
    ElMessage.warning(t('zmind.importWarningSelection'))
    return
  }
  
  importing.value = true
  try {
    const zmindIds = selectedRows.value.map(row => row.zmindId)
    
    const res = await syncZmindTestCases({
      zmindIds,
      projectId: currentProjectId.value,
      projectName: configForm.projectIdentifier,
      apiKey: ZMIND_API_KEY
    })
    
    ElMessage.success(res.message || t('zmind.importSuccess'))
    selectedRows.value = []
  } catch (error) {
    const errorMsg = error.response?.data?.detail || error.message || t('zmind.importFailed')
    ElMessage.error(`${t('zmind.importFailed')}: ${errorMsg}`)
  } finally {
    importing.value = false
  }
}

// 页面加载时获取配置
onMounted(() => {
  loadZmindConfig()
})
</script>

<style scoped>
.zmind-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 20px;
  min-height: 100%;
}

.config-section {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.table-section {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  height: calc(100% - 180px);
}

/* 表格容器 */
.table-wrapper {
  flex: 1;
  width: 100%;
  overflow: visible;
  position: relative;
  min-height: 400px;
  max-height: calc(100% - 320px);
}

.table-wrapper :deep(.el-table) {
  width: 100%;
  height: 100%;
  position: relative;
}

/* 表格内部垂直和水平滚动 */
.table-wrapper :deep(.el-table__body-wrapper) {
  overflow-y: auto !important;
  overflow-x: auto !important;
}

/* 表格内部滚动条样式 */
.table-wrapper :deep(.el-table__body-wrapper)::-webkit-scrollbar {
  height: 8px;
  width: 8px;
}

.table-wrapper :deep(.el-table__body-wrapper)::-webkit-scrollbar-thumb {
  background: rgba(139, 154, 238, 0.3);
  border-radius: 4px;
}

.table-wrapper :deep(.el-table__body-wrapper)::-webkit-scrollbar-thumb:hover {
  background: rgba(139, 154, 238, 0.5);
}

.table-wrapper :deep(.el-table__body-wrapper)::-webkit-scrollbar-track {
  background: rgba(139, 154, 238, 0.05);
}

.search-bar {
  margin-bottom: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-actions {
  display: flex;
  gap: 12px;
}

.pagination-container {
  margin-top: 0;
  display: flex;
  justify-content: center;
  padding: 6px 20px;
  background: #fff;
  flex-shrink: 0;
}

.pagination-container :deep(.el-pager li) {
  background: transparent;
  font-weight: 500;
}

.pagination-container :deep(.el-pager li.is-active) {
  color: #8b9aee;
  font-weight: 600;
}

.el-button {
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.3s;
}

.el-button:hover {
  transform: translateY(-2px);
}

.el-button:active {
  transform: translateY(0);
}

.el-button.is-disabled {
  background-color: rgba(139, 154, 238, 0.5);
  border-color: rgba(139, 154, 238, 0.5);
  color: #ffffff;
}

.el-button--primary.is-disabled {
  background-color: rgba(139, 154, 238, 0.5);
  border-color: rgba(139, 154, 238, 0.5);
}

:deep(.el-input__wrapper) {
  border-radius: 8px;
}

:deep(.el-form-item__label) {
  font-weight: 500;
  color: #606266;
}

.zmind-link {
  color: #409eff;
  text-decoration: none;
  font-weight: 500;
  transition: all 0.3s;
}

.zmind-link:hover {
  color: #66b1ff;
  text-decoration: underline;
}

.zmind-link:active {
  color: #3a8ee6;
}
</style>
