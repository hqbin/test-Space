<template>
  <div class="report-page">
    <el-card class="table-card" shadow="never">
      <div class="table-header">
        <div class="header-left">
          <!-- 状态统计卡片 -->
          <div class="stats-cards">
            <div 
              class="stat-card" 
              :class="{ 'active': statusFilter === null }"
              @click="filterByStatus(null)"
            >
              <div class="stat-label">{{ $t('report.statusAll') }}</div>
              <div class="stat-value">{{ statistics.total }}</div>
            </div>
            <div 
              class="stat-card"
              :class="{ 'active': statusFilter === 'PENDING_REVIEW' }"
              @click="filterByStatus('PENDING_REVIEW')"
            >
              <div class="stat-label">{{ $t('report.statusPendingReview') }}</div>
              <div class="stat-value" style="color: #f59e0b;">{{ statistics.pendingReview }}</div>
            </div>
            <div 
              class="stat-card"
              :class="{ 'active': statusFilter === 'APPROVED' }"
              @click="filterByStatus('APPROVED')"
            >
              <div class="stat-label">{{ $t('report.statusApproved') }}</div>
              <div class="stat-value" style="color: #22c55e;">{{ statistics.approved }}</div>
            </div>
            <div 
              class="stat-card"
              :class="{ 'active': statusFilter === 'ARCHIVED' }"
              @click="filterByStatus('ARCHIVED')"
            >
              <div class="stat-label">已归档</div>
              <div class="stat-value" style="color: #6b7280;">{{ statistics.archived }}</div>
            </div>
          </div>
        </div>
        <div class="header-right">
          <el-select
            v-model="executorFilter"
            :placeholder="$t('report.executor')"
            size="large"
            style="width: 150px;"
            clearable
            filterable
            @change="handleSearch"
          >
            <el-option
              v-for="name in executorOptions"
              :key="name"
              :label="name"
              :value="name"
            />
          </el-select>
          <el-date-picker
            v-model="cycleStartFilter"
            type="date"
            :placeholder="$t('testplan.startTime')"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            size="large"
            style="width: 150px;"
            clearable
            @change="handleSearch"
          />
          <el-date-picker
            v-model="cycleEndFilter"
            type="date"
            :placeholder="$t('testplan.endTime')"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            size="large"
            style="width: 150px;"
            clearable
            @change="handleSearch"
          />
          <el-input
            v-model="searchKeyword"
            :placeholder="$t('report.searchPlaceholder')"
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
      
      <div class="table-wrapper">
        <div class="table-container" ref="tableContainerRef">
          <el-table 
            ref="tableRef"
            :data="tableData" 
            style="width: 100%;"
            :height="tableHeight"
            :header-cell-style="{ background: '#f8fafc', color: '#64748b', fontWeight: '500', fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.05em' }"
          >
            <el-table-column prop="name" :label="$t('report.name')" min-width="280">
              <template #default="{ row }">
                <span class="clickable-name report-name-cell" @click="handleReview(row)">{{ getDisplayName(row) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="pass_rate" :label="$t('report.passRate')" min-width="110">
              <template #default="{ row }">
                <span :style="{ color: getPassRateColor(row.pass_rate), fontWeight: '600' }">{{ row.pass_rate }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="executors" :label="$t('report.executor')" min-width="180">
              <template #default="{ row }">
                <el-tooltip :content="row.executors || '-'" placement="top" :disabled="!row.executors" :show-after="500">
                  <span style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap; display: block;">{{ row.executors || '-' }}</span>
                </el-tooltip>
              </template>
            </el-table-column>
            <el-table-column prop="test_cycle" :label="$t('report.executionPeriod')" min-width="120">
              <template #default="{ row }">
                <el-tooltip :content="row.test_cycle || '-'" placement="top" :disabled="!row.test_cycle || row.test_cycle === '-'" :show-after="500">
                  <span style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap; display: block;">{{ getCycleDays(row.test_cycle) }}</span>
                </el-tooltip>
              </template>
            </el-table-column>
            <el-table-column prop="status" :label="$t('common.status')" min-width="100">
              <template #default="{ row }">
                <el-tag v-if="row.status === 'PENDING_REVIEW'" type="warning" size="small">{{ $t('report.statusPendingReview') }}</el-tag>
                <el-tag v-else-if="row.status === 'APPROVED' && row.is_archived === 1" type="info" size="small">已归档</el-tag>
                <el-tag v-else-if="row.status === 'APPROVED'" type="success" size="small">{{ $t('report.statusApproved') }}</el-tag>
                <el-tag v-else-if="row.status === 'IN_PROGRESS'" type="warning" size="small">{{ $t('testplan.statusInProgress') }}</el-tag>
                <el-tag v-else type="info" size="small">{{ $t('report.unknown') }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="reviewer_name" :label="$t('report.reviewer')" min-width="120">
              <template #default="{ row }">
                <span>{{ row.reviewer_name || '-' }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" :label="$t('common.createdAt')" min-width="170">
              <template #default="{ row }">
                <span>{{ formatDate(row.created_at) }}</span>
              </template>
            </el-table-column>
            <el-table-column :label="$t('common.operation')" width="180" align="center" fixed="right">
              <template #default="scope">
                <el-button 
                  v-if="scope.row.status === 'PENDING_REVIEW'"
                  type="primary" 
                  size="small" 
                  link
                  @click="handleReview(scope.row)"
                >
                  {{ $t('report.review') }}
                </el-button>
                <template v-else-if="scope.row.status === 'APPROVED'">
                  <!-- 已归档的报告：跟已完成状态一样的导出权限 -->
                  <template v-if="scope.row.is_archived === 1">
                    <el-dropdown v-if="hasButton('reports', 'exportPdf') || hasButton('reports', 'exportExcel')" trigger="hover" @command="(cmd) => handleExportCommand(cmd, scope.row)">
                      <el-button 
                        type="primary" 
                        size="small" 
                        link
                      >
                        {{ $t('report.export') }}
                        <el-icon class="el-icon--right"><ArrowDown /></el-icon>
                      </el-button>
                      <template #dropdown>
                        <el-dropdown-menu>
                          <el-dropdown-item v-if="hasButton('reports', 'exportPdf')" command="pdf">
                            <span>{{ $t('report.exportPdf') }}</span>
                          </el-dropdown-item>
                          <el-dropdown-item v-if="hasButton('reports', 'exportExcel')" command="excel">
                            <span>{{ $t('report.exportExcelBtn') }}</span>
                          </el-dropdown-item>
                        </el-dropdown-menu>
                      </template>
                    </el-dropdown>
                    <el-dropdown v-if="isSuperAdmin" trigger="hover" @command="(cmd) => handleArchiveCommand(cmd, scope.row)">
                      <el-button 
                        size="small" 
                        link
                      >
                        <el-icon><MoreFilled /></el-icon>
                      </el-button>
                      <template #dropdown>
                        <el-dropdown-menu>
                          <el-dropdown-item command="unarchive">
                            <span>撤回归档</span>
                          </el-dropdown-item>
                        </el-dropdown-menu>
                      </template>
                    </el-dropdown>
                  </template>
                  <!-- 未归档的报告：审核人和超管可以看到归档按钮 -->
                  <template v-else>
                    <el-dropdown v-if="hasButton('reports', 'exportPdf') || hasButton('reports', 'exportExcel')" trigger="hover" @command="(cmd) => handleExportCommand(cmd, scope.row)">
                      <el-button 
                        type="primary" 
                        size="small" 
                        link
                      >
                        {{ $t('report.export') }}
                        <el-icon class="el-icon--right"><ArrowDown /></el-icon>
                      </el-button>
                      <template #dropdown>
                        <el-dropdown-menu>
                          <el-dropdown-item v-if="hasButton('reports', 'exportPdf')" command="pdf">
                            <span>{{ $t('report.exportPdf') }}</span>
                          </el-dropdown-item>
                          <el-dropdown-item v-if="hasButton('reports', 'exportExcel')" command="excel">
                            <span>{{ $t('report.exportExcelBtn') }}</span>
                          </el-dropdown-item>
                        </el-dropdown-menu>
                      </template>
                    </el-dropdown>
                    <el-dropdown v-if="isReviewer(scope.row) || isSuperAdmin" trigger="hover" @command="(cmd) => handleArchiveCommand(cmd, scope.row)">
                      <el-button 
                        size="small" 
                        link
                      >
                        <el-icon><MoreFilled /></el-icon>
                      </el-button>
                      <template #dropdown>
                        <el-dropdown-menu>
                          <el-dropdown-item command="archive">
                            <span>归档</span>
                          </el-dropdown-item>
                          <el-dropdown-item command="withdraw">
                            <span>撤回</span>
                          </el-dropdown-item>
                        </el-dropdown-menu>
                      </template>
                    </el-dropdown>
                  </template>
                </template>
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
          @current-change="async () => { applyFilter(); await nextTick(); scrollToTop(); }"
          @size-change="async () => { applyFilter(); await nextTick(); scrollToTop(); }"
        />
      </div>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="$t('report.generateReport')" width="500px" @closed="handleDialogClosed">
      <el-form :model="form" label-width="100px">
        <el-form-item :label="$t('report.name')">
          <el-input v-model="form.name" :placeholder="$t('report.inputName')" />
        </el-form-item>
        <el-form-item :label="$t('report.testPlan')">
          <el-select v-model="form.testPlanId" :placeholder="$t('report.selectTestPlan')" clearable style="width: 100%">
            <el-option
              v-for="plan in testPlans"
              :key="plan.id"
              :label="plan.name"
              :value="plan.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleSubmit">{{ $t('common.confirm') }}</el-button>
      </template>
    </el-dialog>
    
    <!-- 导出进度对话框 -->
    <el-dialog v-model="exportDialogVisible" title="正在导出" :close-on-click-modal="false" :show-close="false" width="420px">
      <div style="text-align: center; padding: 20px 0;">
        <el-progress :percentage="exportProgress" :stroke-width="16" :text-inside="true" />
        <p style="margin-top: 16px; color: #909399; font-size: 14px;">{{ exportMessage }}</p>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
defineOptions({ name: 'ReportList' })
import { ref, reactive, onMounted, onBeforeUnmount, onActivated, onDeactivated, watch, nextTick, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter, useRoute } from 'vue-router'
import { getReports, generateReport, archiveReport, unarchiveReport, withdrawReport, startAsyncExport, pollExportStatus, downloadAsyncExport } from '../../api/report'
import { getTestPlans } from '../../api/testplan'
import { ElMessage } from 'element-plus'
import { Search, ArrowDown, MoreFilled } from '@element-plus/icons-vue'
import { useTeam } from '../../composables/useTeam'
import { useProjectPreference } from '../../composables/useProjectPreference'
import { usePagination } from '../../composables/usePagination'
import { useTableHeight } from '../../composables/useTableHeight'
import { useScrollToTop } from '../../composables/useScrollToTop'
import { useLoadingStore } from '../../stores/loading'
import { useUserRole } from '../../composables/useUserRole'
import { getWorkDaysInRange } from '../../utils/chineseHoliday'

const { t } = useI18n()
const router = useRouter()
const route = useRoute()
const { currentTeam, teamProjects, loadTeamProjects } = useTeam()
const { selectedProjectIdList } = useProjectPreference()
const { hasButton, isSuperAdmin } = useUserRole()

// 导出进度
const exportDialogVisible = ref(false)
const exportProgress = ref(0)
const exportMessage = ref('')

// 当前用户ID
const currentUserId = computed(() => {
  const user = JSON.parse(localStorage.getItem('user') || '{}')
  return user.id
})

// 判断是否是审核人
const isReviewer = (row) => {
  return row.reviewer_id === currentUserId.value
}

// 当前项目组的所有用例库ID（报告列表用，不受用例库选择器影响）
const allTeamProjectIds = computed(() => {
  const teamProjectList = teamProjects.value || []
  return teamProjectList.map(p => p.id)
})

// 计算当前选中的用例库ID列表（保留兼容）
const currentProjectIds = computed(() => {
  const teamProjectList = teamProjects.value || []
  return selectedProjectIdList.value.length > 0
    ? selectedProjectIdList.value
    : teamProjectList.map(p => p.id)
})

const { tableContainerRef, tableHeight, bindTableHeight, unbindTableHeight } = useTableHeight()
const tableRef = ref(null)
const { scrollToTop } = useScrollToTop(tableRef)
const loadingStore = useLoadingStore()

const tableData = ref([])
const allTableData = ref([])
const testPlans = ref([])
const { page, size, total } = usePagination('reportList', 10)
const containerLoading = ref(false)
const dialogVisible = ref(false)
const searchKeyword = ref('')
const executorFilter = ref(null)
const cycleStartFilter = ref(null)
const cycleEndFilter = ref(null)
// 从sessionStorage恢复筛选状态，排除已废弃的REJECTED状态
const savedFilter = sessionStorage.getItem('reportListStatusFilter')
const statusFilter = ref(savedFilter === 'REJECTED' ? null : savedFilter)
const form = reactive({
  name: '',
  testPlanId: null,
  templateId: 1,
  projectId: null
})

// 统计数据
const statistics = computed(() => {
  const data = allTableData.value.filter(r => r.status !== 'REJECTED')
  let total = data.length
  let pendingReview = 0
  let approved = 0
  let archived = 0
  
  data.forEach(report => {
    if (report.status === 'PENDING_REVIEW') {
      pendingReview++
    } else if (report.status === 'APPROVED') {
      if (report.is_archived === 1) {
        archived++
      } else {
        approved++
      }
    }
  })
  
  return { total, pendingReview, approved, archived }
})

// 执行人选项列表（从数据中提取去重）
const executorOptions = computed(() => {
  const names = new Set()
  allTableData.value.forEach(report => {
    if (report.executors) {
      report.executors.split(',').forEach(name => {
        const trimmed = name.trim()
        if (trimmed) names.add(trimmed)
      })
    }
  })
  return [...names].sort()
})

// 状态筛选
const filterByStatus = (status) => {
  statusFilter.value = status
  // 保存筛选状态到sessionStorage
  if (status) {
    sessionStorage.setItem('reportListStatusFilter', status)
  } else {
    sessionStorage.removeItem('reportListStatusFilter')
  }
  page.value = 1
  applyFilter()
}

// 应用筛选
const applyFilter = () => {
  let filtered = allTableData.value
  
  // 状态筛选
  if (statusFilter.value) {
    if (statusFilter.value === 'ARCHIVED') {
      // 已归档筛选
      filtered = filtered.filter(report => report.status === 'APPROVED' && report.is_archived === 1)
    } else if (statusFilter.value === 'APPROVED') {
      // 已通过筛选：排除已归档的报告（已归档有自己独立的tab）
      filtered = filtered.filter(report => report.status === 'APPROVED' && report.is_archived !== 1)
    } else {
      // 选择了特定状态
      filtered = filtered.filter(report => report.status === statusFilter.value)
    }
  } else {
    // 选择"全部"时，隐藏已拒绝状态
    filtered = filtered.filter(report => report.status !== 'REJECTED')
  }
  
  // 搜索筛选（支持报告名称、项目名称和测试计划名称，忽略多余空格）
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.trim().toLowerCase().replace(/\s+/g, ' ')
    filtered = filtered.filter(report => {
      const name = (report.name || '').toLowerCase().replace(/\s+/g, ' ')
      const projectName = (report.project_name || '').toLowerCase().replace(/\s+/g, ' ')
      const planName = (report.test_plan_name || '').toLowerCase().replace(/\s+/g, ' ')
      return name.includes(keyword) || projectName.includes(keyword) || planName.includes(keyword)
    })
  }
  
  // 执行人筛选
  if (executorFilter.value) {
    filtered = filtered.filter(report => {
      if (!report.executors) return false
      return report.executors.split(',').map(s => s.trim()).includes(executorFilter.value)
    })
  }
  
  // 测试周期筛选（日期范围交集匹配）
  if (cycleStartFilter.value || cycleEndFilter.value) {
    const filterStart = cycleStartFilter.value ? new Date(cycleStartFilter.value) : null
    const filterEnd = cycleEndFilter.value ? new Date(cycleEndFilter.value) : null
    if (filterStart) filterStart.setHours(0, 0, 0, 0)
    if (filterEnd) filterEnd.setHours(23, 59, 59, 999)
    filtered = filtered.filter(report => {
      if (!report.test_cycle || report.test_cycle === '-') return false
      const parts = report.test_cycle.split('~').map(s => s.trim())
      if (parts.length !== 2) return false
      const cycleStart = new Date(parts[0])
      const cycleEnd = new Date(parts[1])
      if (isNaN(cycleStart) || isNaN(cycleEnd)) return false
      // 日期范围有交集（支持只选开始或只选结束）
      if (filterStart && filterEnd) {
        return cycleStart <= filterEnd && cycleEnd >= filterStart
      } else if (filterStart) {
        return cycleEnd >= filterStart
      } else {
        return cycleStart <= filterEnd
      }
    })
  }
  
  // 排序：待审核 → 已完成 → 已归档（在最后）
  const statusOrder = {
    'PENDING_REVIEW': 1,
    'APPROVED': 2
  }
  filtered.sort((a, b) => {
    // 已归档的报告排在最后
    const aArchived = a.is_archived === 1 ? 1 : 0
    const bArchived = b.is_archived === 1 ? 1 : 0
    if (aArchived !== bArchived) {
      return aArchived - bArchived
    }
    const orderA = statusOrder[a.status] || 999
    const orderB = statusOrder[b.status] || 999
    if (orderA !== orderB) {
      return orderA - orderB
    }
    // 同状态按创建时间降序
    return new Date(b.created_at) - new Date(a.created_at)
  })
  
  // 更新总数
  total.value = filtered.length
  
  // 分页
  const start = (page.value - 1) * size.value
  const end = start + size.value
  tableData.value = filtered.slice(start, end)
  
  // 强制el-table重新布局（修复固定高度下数据变化后渲染异常）
  nextTick(() => {
    tableRef.value?.doLayout()
    // 行高自适应后DOM可能还未完全更新，延迟再次doLayout
    setTimeout(() => {
      tableRef.value?.doLayout()
    }, 50)
  })
}

const handleSearch = () => {
  page.value = 1
  applyFilter()
}

const loadData = async () => {
  if (allTeamProjectIds.value.length === 0) {
    allTableData.value = []
    tableData.value = []
    total.value = 0
    return
  }
  
  // 避免重复加载
  if (containerLoading.value) return
  
  containerLoading.value = true
  loadingStore.showLoading(t('report.title') + '...')
  try {
    // 加载所有数据用于统计和筛选（按项目组过滤）
    const params = { 
      page: 1, 
      size: 10000  // 获取所有数据
    }
    if (currentTeam.value?.id) {
      params.team_id = currentTeam.value.id
    }
    if (allTeamProjectIds.value.length > 0) {
      params.project_ids = allTeamProjectIds.value.join(',')
    }
    // 加载所有报告（已归档+未归档），由前端筛选展示
    const res = await getReports(params)
    allTableData.value = res.data.records
    
    // 应用筛选和分页
    applyFilter()
  } catch (error) {
    ElMessage.error(t('common.failed'))
  } finally {
    containerLoading.value = false
    loadingStore.hideLoading()
  }
}

const loadTestPlans = async () => {
  try {
    const params = { page: 1, size: 100 }
    if (currentTeam.value?.id) {
      params.team_id = currentTeam.value.id
    }
    if (allTeamProjectIds.value.length > 0) {
      params.project_ids = allTeamProjectIds.value.join(',')
    }
    const res = await getTestPlans(params)
    testPlans.value = res.data.records
  } catch (error) {
    // 静默失败
  }
}

const handleGenerate = () => {
  form.name = ''
  form.testPlanId = null
  form.projectId = null
  dialogVisible.value = true
  loadTestPlans()
}

const handleSubmit = async () => {
  if (!form.name) {
    ElMessage.warning(t('report.inputName'))
    return
  }
  
  if (!form.projectId) {
    ElMessage.warning(t('common.failed'))
    return
  }
  
  try {
    await generateReport(form)
    ElMessage.success(t('report.generateSuccess'))
    dialogVisible.value = false
    loadData()
  } catch (error) {
    ElMessage.error(t('common.failed'))
  }
}

const _asyncExport = async (row, format) => {
  const formatLabel = format === 'pdf' ? 'PDF' : 'Excel'
  exportProgress.value = 0
  exportMessage.value = `正在启动${formatLabel}导出...`
  exportDialogVisible.value = true
  try {
    const taskId = await startAsyncExport(row.id, format)
    let retries = 0
    while (retries < 600) {
      const status = await pollExportStatus(taskId)
      if (status.status === 'completed') {
        exportProgress.value = 100
        exportMessage.value = '正在下载文件...'
        await downloadAsyncExport(taskId, getDisplayName(row))
        ElMessage.success(t('report.exportSuccess'))
        return
      }
      if (status.status === 'failed') {
        throw new Error(status.error || '导出失败')
      }
      if (status.progress !== undefined) {
        exportProgress.value = status.progress
      }
      if (status.status_message) {
        exportMessage.value = status.status_message
      }
      await new Promise(resolve => setTimeout(resolve, 2000))
      retries++
    }
    throw new Error('导出超时')
  } catch (error) {
    ElMessage.error(error.message || t('common.failed'))
  } finally {
    exportDialogVisible.value = false
  }
}

const handleExportPdf = (row) => _asyncExport(row, 'pdf')

const handleExportCommand = async (command, row) => {
  if (command === 'pdf') {
    await handleExportPdf(row)
  } else if (command === 'excel') {
    await handleExportExcel(row)
  }
}

const handleArchiveCommand = async (command, row) => {
  if (command === 'archive') {
    try {
      await archiveReport(row.id)
      ElMessage.success('归档成功')
      loadData()
    } catch (error) {
      ElMessage.error('归档失败')
    }
  } else if (command === 'withdraw') {
    try {
      await withdrawReport(row.id)
      ElMessage.success('撤回成功，报告已变为进行中')
      loadData()
    } catch (error) {
      ElMessage.error('撤回失败')
    }
  } else if (command === 'unarchive') {
    try {
      await unarchiveReport(row.id)
      ElMessage.success('撤回归档成功')
      // 撤回归档后，如果当前在已归档筛选，切换到已完成筛选
      if (statusFilter.value === 'ARCHIVED') {
        statusFilter.value = 'APPROVED'
        sessionStorage.setItem('reportListStatusFilter', 'APPROVED')
      }
      loadData()
    } catch (error) {
      ElMessage.error('撤回归档失败')
    }
  }
}

const handleDialogClosed = () => {
  // 对话框关闭后,移除所有按钮的焦点
  if (document.activeElement instanceof HTMLElement) {
    document.activeElement.blur()
  }
}

const handleExportExcel = (row) => _asyncExport(row, 'excel')

// 获取报告显示名称：优先使用project_name，去掉" - 测试报告"后缀
const getDisplayName = (row) => {
  const name = row.project_name || row.name || ''
  return name.replace(/\s*-\s*测试报告$/, '')
}

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// 将 "2026-03-05 ~ 2026-03-09" 格式的周期转为工作日数显示
const getCycleDays = (cycle) => {
  if (!cycle || cycle === '-') return '-'
  const parts = cycle.split('~').map(s => s.trim())
  if (parts.length !== 2) return cycle
  const workDays = getWorkDaysInRange(parts[0], parts[1])
  return `${workDays} ${t('testplan.days')}`
}

// 通过率颜色
const getPassRateColor = (passRate) => {
  if (!passRate || passRate === '-') return '#909399'
  const rate = parseFloat(passRate)
  if (rate >= 95) return '#67c23a'  // 绿色
  if (rate >= 80) return '#e6a23c'  // 橙色
  return '#f56c6c'  // 红色
}

// 处理审核/查看详情
const handleReview = (row) => {
  // 跳转到审核/查看页面
  router.push(`/reports/review/${row.id}`)
}

// 页面是否处于激活状态
const isActive = ref(false)
let watchTimeout = null

watch(allTeamProjectIds, () => {
  // 只在页面激活且不在加载中时才刷新，添加防抖避免重复
  if (!isActive.value) return
  if (containerLoading.value) return
  if (watchTimeout) clearTimeout(watchTimeout)
  watchTimeout = setTimeout(() => {
    if (!isActive.value) return
    if (containerLoading.value) return
    page.value = 1
    loadData()
  }, 100)
})

onMounted(async () => {
  // 页面初始化时标记为激活状态
  isActive.value = true
  // 刷新页面时 teamProjects 可能还没加载完，需要等待
  if (allTeamProjectIds.value.length === 0 && currentTeam.value) {
    await loadTeamProjects()
  }
  loadData()
  bindTableHeight()
})
onActivated(() => {
  isActive.value = true
  // 从审核页面返回时刷新数据，确保状态实时更新
  loadData()
})
onDeactivated(() => {
  isActive.value = false
})
onBeforeUnmount(() => {
  unbindTableHeight()
})
</script>

<style scoped>
/* ==================== */
/* 页面布局 */
/* ==================== */
.report-page {
  height: 100%;
  background: #f8fafc;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  padding: 24px;
}

.report-page::-webkit-scrollbar { width: 8px; }
.report-page::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }
.report-page::-webkit-scrollbar-thumb:hover { background: #94a3b8; }
.report-page::-webkit-scrollbar-track { background: #f1f5f9; }

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

/* ==================== */
/* 统计卡片 */
/* ==================== */
.stats-cards {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 14px;
  background: #f8fafc;
  border-radius: 8px;
  cursor: pointer;
  border: 1.5px solid transparent;
  transition: all 0.15s;
}

.stat-card:hover {
  background: #f1f5f9;
}

.stat-card.active {
  border-color: #4f46e5;
  background: #eef2ff;
}

.stat-label {
  font-size: 13px;
  color: #64748b;
  white-space: nowrap;
}

.stat-value {
  font-size: 18px;
  font-weight: 600;
  color: #0f172a;
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

/* 表头单元格固定高度 */
.table-wrapper :deep(.el-table th.el-table__cell) {
  height: 48px !important;
  padding: 0 12px !important;
}

.table-wrapper :deep(.el-table th.el-table__cell .cell) {
  line-height: 48px;
  padding: 0;
}

/* 数据行单元格自适应高度 */
.table-wrapper :deep(.el-table td.el-table__cell) {
  padding: 12px 12px !important;
}

.table-wrapper :deep(.el-table td.el-table__cell .cell) {
  line-height: 22px;
  padding: 0;
  overflow: visible !important;
}

/* 报告名称换行显示 */
.report-name-cell {
  display: block;
  white-space: normal;
  word-break: break-all;
  line-height: 1.4;
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
/* 可点击名称 */
/* ==================== */
.clickable-name {
  color: #4f46e5;
  cursor: pointer;
  transition: color 0.15s;
}

.clickable-name:hover {
  color: #4338ca;
  text-decoration: underline;
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

:deep(.el-form-item__label) {
  font-weight: 500;
  color: #334155;
  font-size: 14px;
}

:deep(.el-input__wrapper),
:deep(.el-select) {
  border-radius: 8px;
}
</style>
