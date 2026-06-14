<template>
  <div class="dashboard-page">
    <!-- 卡片1: 用例库信息卡片 -->
    <div v-if="hasButton('dashboard', 'projectCards')" class="card-section">
      <div class="section-title-bar">
        <svg class="section-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"/></svg>
        <span>{{ $t('dashboard.caseLibraryInfo') }}</span>
        <el-tooltip :content="$t('common.refreshData')" placement="bottom" :show-after="500">
          <el-button :icon="Refresh" :loading="refreshing" circle size="small" @click="handleRefreshAll" style="margin-left: auto;" />
        </el-tooltip>
      </div>
      <div v-loading="loading.projectCards" class="kpi-cards-row">
        <div v-if="projectCards.length === 0 && !loading.projectCards" class="empty-hint">
          <el-empty :description="$t('dashboard.noCaseLibrary')" :image-size="64" />
        </div>
        <div
          v-for="card in projectCards"
          :key="card.project_id"
          class="summary-card clickable"
          @click="goToTestcases(card.project_id)"
        >
          <div class="card-header-row">
            <div class="card-icon-box blue">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
            </div>
            <h3 class="card-title" :title="card.project_name">{{ card.project_name }}</h3>
          </div>
          <div class="card-main-number">{{ card.total.toLocaleString() }}</div>
          <div class="card-stats-row">
            <div class="stat-item"><div class="stat-dot dark"></div><span class="stat-label">L1</span><span class="stat-value">{{ card.l1 }}</span></div>
            <div class="stat-item"><div class="stat-dot medium"></div><span class="stat-label">L2</span><span class="stat-value">{{ card.l2 }}</span></div>
            <div class="stat-item"><div class="stat-dot light"></div><span class="stat-label">L3</span><span class="stat-value">{{ card.l3 }}</span></div>
            <div class="stat-item"><div class="stat-dot lighter"></div><span class="stat-label">L4</span><span class="stat-value">{{ card.l4 }}</span></div>
          </div>
          <div class="card-stats-row mt-12">
            <div class="stat-item"><div class="stat-dot emerald"></div><span class="stat-label">{{ $t('testcase.automationCompleted') }}</span><span class="stat-value">{{ card.auto_done }}</span></div>
            <div class="stat-item"><div class="stat-dot rose"></div><span class="stat-label">{{ $t('testcase.automationNA') }}</span><span class="stat-value">{{ card.auto_na }}</span></div>
            <div class="stat-item"><div class="stat-dot slate"></div><span class="stat-label">{{ $t('testcase.automationPending') }}</span><span class="stat-value">{{ card.auto_pending }}</span></div>
          </div>
          <div class="card-stats-row mt-12">
            <div class="stat-item"><div class="stat-dot amber"></div><span class="stat-label">{{ $t('dashboard.pendingReview') }}</span><span class="stat-value">{{ card.review_pending }}</span></div>
            <div class="stat-item"><div class="stat-dot rose"></div><span class="stat-label">{{ $t('dashboard.reviewRejected') }}</span><span class="stat-value">{{ card.review_rejected }}</span></div>
          </div>
        </div>
      </div>
    </div>

    <!-- 卡片2: 用例关联PR数 -->
    <div v-if="hasButton('dashboard', 'prList')" class="card-section">
      <div class="section-title-bar">
        <svg class="section-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="18" cy="18" r="3"/><circle cx="6" cy="6" r="3"/><path d="M13 6h3a2 2 0 012 2v7"/><path d="M6 9v12"/></svg>
        <span>{{ $t('dashboard.caseLinkedPR') }}</span>
      </div>
      <div v-loading="loading.prList" class="summary-card table-card">
        <el-table
          :data="prList"
          style="width: 100%"
          border
          stripe
          :header-cell-style="{ textAlign: 'center', background: '#f8fafc', color: '#0f172a', fontWeight: 600 }"
          :cell-style="{ verticalAlign: 'middle' }"
        >
          <el-table-column :label="$t('testcase.caseNumber')" width="300" align="center">
            <template #default="{ row }">
              <el-tooltip :content="row.case_number" placement="top" :disabled="!row.case_number" :show-after="500">
                <div style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{{ row.case_number || '-' }}</div>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column :label="$t('testcase.caseLibrary')" width="140" align="center">
            <template #default="{ row }">
              <el-tooltip :content="row.project_name" placement="top" :disabled="!row.project_name" :show-after="500">
                <div style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{{ row.project_name || '-' }}</div>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column :label="$t('testcase.moduleBelongs')" width="140" align="center">
            <template #default="{ row }">
              <el-tooltip :content="row.module" placement="top" :disabled="!row.module" :show-after="500">
                <div style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{{ row.module || '-' }}</div>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column :label="$t('testcase.name')" min-width="180">
            <template #default="{ row }">
              <el-tooltip :content="row.case_name" placement="top" :disabled="!row.case_name" :show-after="500">
                <div style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{{ row.case_name }}</div>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column :label="$t('testcase.steps')" min-width="200">
            <template #default="{ row }">
              <el-tooltip placement="top" :disabled="!formatSteps(row.steps)" :show-after="500">
                <template #content>
                  <div style="max-width: 400px; white-space: pre-wrap;">{{ formatSteps(row.steps) }}</div>
                </template>
                <div style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{{ formatSteps(row.steps) || '-' }}</div>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column :label="$t('testcase.expectedResult')" min-width="200">
            <template #default="{ row }">
              <el-tooltip placement="top" :disabled="!formatExpected(row.steps, row.expected_result)" :show-after="500">
                <template #content>
                  <div style="max-width: 400px; white-space: pre-wrap;">{{ formatExpected(row.steps, row.expected_result) }}</div>
                </template>
                <div style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{{ formatExpected(row.steps, row.expected_result) || '-' }}</div>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column prop="level" :label="$t('testcase.level')" width="100" align="center" />
          <el-table-column :label="$t('testcase.prCount')" width="110" align="center">
            <template #default="{ row }">
              <span class="pr-count-link" @click="openPrDialog(row)">{{ row.pr_count != null ? row.pr_count : 0 }}</span>
            </template>
          </el-table-column>
        </el-table>
        <div class="table-pagination">
          <el-pagination
            v-model:current-page="prPage"
            v-model:page-size="prSize"
            :total="prTotal"
            :page-sizes="[10, 20, 50]"
            layout="total, sizes, prev, pager, next"
            @size-change="loadPrList"
            @current-change="loadPrList"
          />
        </div>
      </div>
    </div>

    <!-- 卡片3 & 4: 评审计划 + 测试计划 并排 -->
    <div class="two-col-row">
      <!-- 卡片3: 测试计划 -->
      <div v-if="hasButton('dashboard', 'testPlans')" class="card-section col-half">
        <div class="section-title-bar">
          <svg class="section-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
          <span>{{ $t('dashboard.testPlans') }}</span>
        </div>
        <div v-loading="loading.testPlans" class="plan-list">
          <el-empty v-if="testPlans.length === 0 && !loading.testPlans" :description="$t('dashboard.noTestPlans')" :image-size="48" />
          <div v-for="plan in paginatedTestPlans" :key="plan.id" class="summary-card plan-card">
            <div class="plan-card-header">
              <span class="plan-name" :title="plan.name">{{ plan.name }}</span>
              <el-tag :type="testPlanStatusType(plan.status)" size="small">
                {{ testPlanStatusLabel(plan.status) }}
              </el-tag>
            </div>
            <div class="plan-meta">
              <span>{{ $t('user.team') }}: {{ plan.team_name }}</span>
              <span>{{ $t('testcase.creator') }}: {{ plan.creator }}</span>
            </div>
            <div class="plan-meta">
              <span>{{ $t('testplan.executors') }}: {{ plan.executors.join(', ') || '-' }}</span>
              <span v-if="plan.reviewer">{{ $t('testplan.reviewer') }}: {{ plan.reviewer }}</span>
            </div>
            <el-progress :percentage="plan.progress" :stroke-width="6" :format="() => plan.executed_cases + '/' + plan.total_cases" />
          </div>
          <div v-if="testPlans.length > planPageSize" class="plan-pager">
            <span class="pager-info">{{ (testPlanPage - 1) * planPageSize + 1 }}-{{ Math.min(testPlanPage * planPageSize, testPlans.length) }} / {{ testPlans.length }}</span>
            <div class="pager-btns">
              <button class="pager-btn" :disabled="testPlanPage <= 1" @click="testPlanPage--">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14"><polyline points="15 18 9 12 15 6"/></svg>
              </button>
              <button class="pager-btn" :disabled="testPlanPage >= Math.ceil(testPlans.length / planPageSize)" @click="testPlanPage++">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14"><polyline points="9 18 15 12 9 6"/></svg>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 卡片4: 评审计划 -->
      <div v-if="hasButton('dashboard', 'reviewPlans')" class="card-section col-half">
        <div class="section-title-bar">
          <svg class="section-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/></svg>
          <span>{{ $t('dashboard.reviewPlans') }}</span>
        </div>
        <div v-loading="loading.reviewPlans" class="plan-list">
          <el-empty v-if="reviewPlans.length === 0 && !loading.reviewPlans" :description="$t('dashboard.noReviewPlans')" :image-size="48" />
          <div v-for="plan in paginatedReviewPlans" :key="plan.id" class="summary-card plan-card">
            <div class="plan-card-header">
              <span class="plan-name" :title="plan.name">{{ plan.name }}</span>
              <el-tag :type="plan.status === 'IN_PROGRESS' ? 'warning' : 'info'" size="small">
                {{ plan.status === 'IN_PROGRESS' ? $t('dashboard.inProgress') : $t('dashboard.pendingReview') }}
              </el-tag>
            </div>
            <div class="plan-meta">
              <span>{{ $t('testcase.caseLibrary') }}: {{ plan.project_name }}</span>
              <span>{{ $t('testcase.creator') }}: {{ plan.creator }}</span>
            </div>
            <div class="plan-meta">
              <span>{{ $t('testplan.reviewer') }}: {{ plan.reviewers.join(', ') || '-' }}</span>
            </div>
            <el-progress :percentage="plan.progress" :stroke-width="6" :format="() => plan.reviewed_cases + '/' + plan.total_cases" />
          </div>
          <div v-if="reviewPlans.length > planPageSize" class="plan-pager">
            <span class="pager-info">{{ (reviewPlanPage - 1) * planPageSize + 1 }}-{{ Math.min(reviewPlanPage * planPageSize, reviewPlans.length) }} / {{ reviewPlans.length }}</span>
            <div class="pager-btns">
              <button class="pager-btn" :disabled="reviewPlanPage <= 1" @click="reviewPlanPage--">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14"><polyline points="15 18 9 12 15 6"/></svg>
              </button>
              <button class="pager-btn" :disabled="reviewPlanPage >= Math.ceil(reviewPlans.length / planPageSize)" @click="reviewPlanPage++">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14"><polyline points="9 18 15 12 9 6"/></svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 卡片5: 用户任务统计 -->
    <div v-if="hasButton('dashboard', 'userTasks')" class="card-section">
      <div class="section-title-bar">
        <svg class="section-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87"/><path d="M16 3.13a4 4 0 010 7.75"/></svg>
        <span>{{ $t('dashboard.userTaskStats') }}</span>
      </div>
      <div v-loading="loading.userTasks" class="summary-card table-card">
        <el-table
          :data="userTasks"
          style="width: 100%"
          border
          stripe
          :header-cell-style="{ textAlign: 'center', background: '#f8fafc', color: '#0f172a', fontWeight: 600 }"
          :cell-style="{ verticalAlign: 'middle' }"
        >
          <el-table-column :label="$t('common.user')" min-width="240" align="center">
            <template #default="{ row }">
              <div style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{{ row.username || '-' }}</div>
            </template>
          </el-table-column>
          <el-table-column :label="$t('user.department')" min-width="320" align="center">
            <template #default="{ row }">
              <el-tooltip :content="row.department_names.join(', ')" placement="top" :disabled="row.department_names.length === 0" :show-after="500">
                <div style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{{ row.department_names.join(', ') || '-' }}</div>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column :label="$t('user.team')" min-width="320" align="center">
            <template #default="{ row }">
              <el-tooltip :content="row.team_names.join(', ')" placement="top" :disabled="row.team_names.length === 0" :show-after="500">
                <div style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{{ row.team_names.join(', ') || '-' }}</div>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column prop="task_count" :label="$t('dashboard.assignedCases')" width="280" align="center" />
        </el-table>
      </div>
    </div>

    <!-- PR详情对话框 -->
    <el-dialog v-model="prDialogVisible" :title="$t('dashboard.linkedPRList')" width="900px" :close-on-click-modal="false" append-to-body>
      <div v-if="prDialogCase" style="margin-bottom: 12px; color: #64748b; font-size: 13px;">
        {{ $t('testcase.name') }}: <span style="color: #0f172a; font-weight: 500;">{{ prDialogCase.case_number }} - {{ prDialogCase.case_name }}</span>
      </div>
      <el-table
        v-loading="prDialogLoading"
        :data="prDialogLinks"
        style="width: 100%"
        border
        stripe
        :header-cell-style="{ textAlign: 'center', background: '#f8fafc', color: '#0f172a', fontWeight: 600 }"
        :cell-style="{ verticalAlign: 'middle' }"
        :empty-text="$t('dashboard.noPRData')"
      >
        <el-table-column label="PR ID" width="100" align="center">
          <template #default="{ row }">
            <a
              :href="'https://zmind.whaletv.com/issues/' + row.zmind_issue_id"
              target="_blank"
              rel="noopener noreferrer"
              style="color: #409EFF; text-decoration: underline;"
            >{{ row.zmind_issue_id }}</a>
          </template>
        </el-table-column>
        <el-table-column :label="$t('testcase.linkDialog.prTitle')" min-width="240">
          <template #default="{ row }">
            <el-tooltip :content="row.zmind_issue_subject" placement="top" :disabled="!row.zmind_issue_subject" :show-after="500">
              <div style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{{ row.zmind_issue_subject || '-' }}</div>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column :label="$t('testcase.linkDialog.prSeverity')" width="120" align="center">
          <template #default="{ row }">{{ row.zmind_issue_severity || '-' }}</template>
        </el-table-column>
        <el-table-column :label="$t('common.status')" width="120" align="center">
          <template #default="{ row }">{{ row.zmind_issue_status || '-' }}</template>
        </el-table-column>
        <el-table-column :label="$t('testcase.creator')" width="120" align="center">
          <template #default="{ row }">{{ row.created_by_name || '-' }}</template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
defineOptions({ name: 'Dashboard' })
import { ref, reactive, onMounted, onActivated, computed, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useUserRole } from '@/composables/useUserRole'
import { useTeam } from '@/composables/useTeam'
import { getProjectCards, getPrList, getReviewPlans, getTestPlans, getUserTasks } from '@/api/dashboard'
import { getZmindLinks } from '@/api/testcase'
import { eventBus } from '@/utils/eventBus'

import { useI18n } from 'vue-i18n'

const router = useRouter()
const { hasButton } = useUserRole()
const { currentTeam } = useTeam()
const { t } = useI18n()

// loading 状态
const refreshing = ref(false)
const loading = reactive({
  projectCards: false,
  prList: false,
  reviewPlans: false,
  testPlans: false,
  userTasks: false
})

// 数据
const projectCards = ref([])
const prList = ref([])
const prPage = ref(1)
const prSize = ref(10)
const prTotal = ref(0)
const reviewPlans = ref([])
const testPlans = ref([])
const reviewPlanPage = ref(1)
const testPlanPage = ref(1)
const planPageSize = 5
const userTasks = ref([])

// 分页计算
const paginatedReviewPlans = computed(() => {
  const start = (reviewPlanPage.value - 1) * planPageSize
  return reviewPlans.value.slice(start, start + planPageSize)
})
const paginatedTestPlans = computed(() => {
  const start = (testPlanPage.value - 1) * planPageSize
  return testPlans.value.slice(start, start + planPageSize)
})

// PR详情对话框
const prDialogVisible = ref(false)
const prDialogLoading = ref(false)
const prDialogCase = ref(null)
const prDialogLinks = ref([])

// ========== 数据加载 ==========
async function loadProjectCards() {
  loading.projectCards = true
  try {
    const res = await getProjectCards({ team_id: currentTeam.value?.id || undefined })
    projectCards.value = res.data || []
  } catch (e) {
    console.error('loadProjectCards', e)
  } finally {
    loading.projectCards = false
  }
}

async function loadPrList() {
  loading.prList = true
  try {
    const res = await getPrList({ page: prPage.value, size: prSize.value, team_id: currentTeam.value?.id || undefined })
    const d = res.data || {}
    prList.value = d.records || []
    prTotal.value = d.total || 0
  } catch (e) {
    console.error('loadPrList', e)
  } finally {
    loading.prList = false
  }
}

async function loadReviewPlans() {
  loading.reviewPlans = true
  try {
    const res = await getReviewPlans({ team_id: currentTeam.value?.id || undefined })
    reviewPlans.value = res.data || []
    reviewPlanPage.value = 1
  } catch (e) {
    console.error('loadReviewPlans', e)
  } finally {
    loading.reviewPlans = false
  }
}

async function loadTestPlans() {
  loading.testPlans = true
  try {
    const res = await getTestPlans({ team_id: currentTeam.value?.id || undefined })
    testPlans.value = res.data || []
    testPlanPage.value = 1
  } catch (e) {
    console.error('loadTestPlans', e)
  } finally {
    loading.testPlans = false
  }
}

async function loadUserTasks() {
  loading.userTasks = true
  try {
    const res = await getUserTasks({ team_id: currentTeam.value?.id || undefined })
    userTasks.value = res.data || []
  } catch (e) {
    console.error('loadUserTasks', e)
  } finally {
    loading.userTasks = false
  }
}

async function handleRefreshAll() {
  refreshing.value = true
  try {
    await Promise.all([
      loadProjectCards(),
      loadPrList(),
      loadReviewPlans(),
      loadTestPlans(),
      loadUserTasks()
    ])
    ElMessage.success(t('common.dataRefreshed'))
  } finally {
    refreshing.value = false
  }
}

// ========== 格式化 ==========
function formatSteps(steps) {
  if (!steps) return ''
  try {
    const arr = typeof steps === 'string' ? JSON.parse(steps) : steps
    if (!Array.isArray(arr) || arr.length === 0) return typeof steps === 'string' ? steps : ''
    return arr.map(item => {
      if (typeof item === 'string') return item
      if (item && typeof item === 'object') return item.step || item.action || ''
      return String(item || '')
    }).filter(Boolean).join('\n')
  } catch {
    return String(steps)
  }
}

function formatExpected(steps, expectedResult) {
  // 优先从steps JSON数组中提取expected字段
  if (steps) {
    try {
      const arr = typeof steps === 'string' ? JSON.parse(steps) : steps
      if (Array.isArray(arr) && arr.length > 0 && arr[0].expected !== undefined) {
        return arr.map(item => item.expected || '').filter(Boolean).join('\n')
      }
    } catch {
      // fallback
    }
  }
  return expectedResult || ''
}

// ========== 测试计划状态 ==========
function testPlanStatusType(status) {
  const map = { PENDING: 'info', IN_PROGRESS: 'warning', IN_REVIEW: '' }
  return map[status] || 'info'
}

function testPlanStatusLabel(status) {
  const map = { PENDING: t('testplan.statusPending'), IN_PROGRESS: t('testplan.statusInProgress'), IN_REVIEW: t('dashboard.pendingReview') }
  return map[status] || status
}

// ========== PR对话框 ==========
async function openPrDialog(row) {
  prDialogCase.value = row
  prDialogLinks.value = []
  prDialogVisible.value = true
  prDialogLoading.value = true
  try {
    const res = await getZmindLinks(row.testcase_id)
    prDialogLinks.value = res.data || []
  } catch (e) {
    ElMessage.error(t('dashboard.getPRListFailed'))
    console.error('openPrDialog', e)
  } finally {
    prDialogLoading.value = false
  }
}

// ========== 导航 ==========
function goToTestcases(projectId) {
  router.push({ path: '/testcases', query: { project_id: projectId } })
}

// ========== 初始化 ==========
let lastLoadTime = 0
const REFRESH_INTERVAL = 30000 // 30秒内切回不重复请求

function loadAll() {
  lastLoadTime = Date.now()
  loadProjectCards()
  loadPrList()
  loadReviewPlans()
  loadTestPlans()
  loadUserTasks()
}

onMounted(() => {
  loadAll()
})

// 监听数据变化事件，自动刷新仪表盘
const handleDataChanged = () => {
  lastLoadTime = 0 // 重置时间，确保下次 activated 也会刷新
  loadAll()
}
eventBus.on('projects-changed', handleDataChanged)
eventBus.on('teams-changed', handleDataChanged)
eventBus.on('testcases-changed', handleDataChanged)
eventBus.on('testplans-changed', handleDataChanged)

onUnmounted(() => {
  eventBus.off('projects-changed', handleDataChanged)
  eventBus.off('teams-changed', handleDataChanged)
  eventBus.off('testcases-changed', handleDataChanged)
  eventBus.off('testplans-changed', handleDataChanged)
})

onActivated(() => {
  // 超过30秒才重新加载
  if (Date.now() - lastLoadTime > REFRESH_INTERVAL) {
    loadAll()
  }
})
</script>

<style scoped>
.dashboard-page {
  padding: 16px 24px;
  background: #f1f5f9;
  min-height: 100%;
}

/* 区块标题 */
.card-section {
  margin-bottom: 20px;
}
.section-title-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #0f172a;
  margin-bottom: 12px;
}
.section-icon {
  width: 20px;
  height: 20px;
  color: #3b82f6;
}

/* 卡片网格 */
.kpi-cards-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}
.empty-hint {
  grid-column: 1 / -1;
  text-align: center;
  padding: 32px 0;
}

/* summary-card 风格 */
.summary-card {
  background: #ffffff;
  border-radius: 12px;
  padding: 14px 18px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  transition: box-shadow 0.2s ease;
}
.summary-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}
.summary-card.clickable {
  cursor: pointer;
}
.summary-card.table-card {
  padding: 16px;
}

/* 卡片头部 */
.card-header-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}
.card-icon-box {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.card-icon-box.blue { background: #eff6ff; color: #3b82f6; }
.card-icon-box.green { background: #ecfdf5; color: #10b981; }
.card-icon-box.amber { background: #fffbeb; color: #f59e0b; }

.card-title {
  font-size: 15px;
  font-weight: 600;
  color: #0f172a;
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.card-main-number {
  font-size: 22px;
  font-weight: 700;
  color: #0f172a;
  line-height: 1;
  margin-bottom: 10px;
}

/* 统计行 */
.card-stats-row {
  display: flex;
  gap: 20px;
}
.card-stats-row.mt-12 {
  margin-top: 8px;
}
.stat-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.stat-item .stat-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #64748b;
  font-weight: 500;
}
.stat-item .stat-value {
  font-size: 14px;
  font-weight: 600;
  color: #0f172a;
}
.stat-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.stat-dot.dark { background: #1e293b; }
.stat-dot.medium { background: #475569; }
.stat-dot.light { background: #94a3b8; }
.stat-dot.lighter { background: #cbd5e1; }
.stat-dot.emerald { background: #10b981; }
.stat-dot.rose { background: #f43f5e; }
.stat-dot.slate { background: #e2e8f0; }
.stat-dot.amber { background: #f59e0b; }

/* 表格单元格省略 — 必须用 width:0 技巧让 ellipsis 在 table cell 内生效 */
.cell-ellipsis {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  width: 0;
  min-width: 100%;
}

/* 分页 */
.table-pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
}

/* 两列布局 */
.two-col-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-bottom: 24px;
}
.col-half {
  min-width: 0;
}

/* 计划列表 */
.plan-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.plan-card {
  padding: 20px;
}
.plan-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.plan-name {
  font-size: 15px;
  font-weight: 600;
  color: #0f172a;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  margin-right: 8px;
}
.plan-meta {
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: #64748b;
  margin-bottom: 8px;
  flex-wrap: wrap;
}
.plan-pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 4px;
}

/* 自定义轻量分页器 */
.plan-pager {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 4px;
  padding-top: 8px;
}
.pager-info {
  font-size: 13px;
  color: #94a3b8;
  font-weight: 500;
  font-variant-numeric: tabular-nums;
}
.pager-btns {
  display: flex;
  gap: 4px;
}
.pager-btn {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #475569;
  transition: all 0.15s ease;
}
.pager-btn:hover:not(:disabled) {
  background: #f1f5f9;
  border-color: #cbd5e1;
  color: #0f172a;
}
.pager-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

/* PR数量链接 */
.pr-count-link {
  color: #409EFF;
  cursor: pointer;
  font-weight: 600;
  text-decoration: underline;
}
.pr-count-link:hover {
  color: #337ecc;
}

/* el-table cell 省略号样式 */
.table-card :deep(.el-table .cell) {
  padding: 0 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
/* tooltip 内的 div 也需要继承省略 */
.table-card :deep(.el-table .cell .el-tooltip) {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: block;
  max-width: 100%;
}
.table-card :deep(.el-table .cell .el-tooltip > div) {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
