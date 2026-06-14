<template>
  <div ref="analyticsPageRef" class="analytics-page">
    <!-- 筛选栏 -->
    <div class="filter-bar">
      <div class="filter-left">
        <el-select
          v-model="filters.plan_id"
          :placeholder="$t('analytics.selectPlan')"
          clearable
          filterable
          remote
          :remote-method="searchPlans"
          :loading="planLoading"
          style="width: 280px"
        >
          <el-option label="全部计划" :value="null" />
          <el-option v-for="p in filterOptions.plans" :key="p.id" :label="p.name" :value="p.id" />
        </el-select>
        <el-date-picker v-model="dateRange" type="daterange" :start-placeholder="$t('analytics.startDate')" :end-placeholder="$t('analytics.endDate')" format="YYYY-MM-DD" value-format="YYYY-MM-DD" style="width: 280px" />
        <el-radio-group v-model="filters.granularity" size="small">
          <el-radio-button value="day">当日数据</el-radio-button>
          <el-radio-button value="week">本周数据</el-radio-button>
          <el-radio-button value="month">本月数据</el-radio-button>
        </el-radio-group>
      </div>
      <div class="filter-right">
        <el-button @click="prCheckVisible = true">
          <el-icon><Document /></el-icon>PR 关联查询
        </el-button>
        <el-button type="primary" @click="loadAllData" :loading="loading">
          <el-icon><Refresh /></el-icon>{{ $t('analytics.refresh') }}
        </el-button>
      </div>
    </div>

    <!-- PR 关联查询对话框 -->
    <el-dialog
      v-model="prCheckVisible"
      title="PR 关联查询"
      width="1100px"
      top="4vh"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <div class="pr-check-dialog">
        <!-- 上传区域 -->
        <div v-if="!prCheckResult" class="pr-upload-area">
          <el-upload
            ref="prUploadRef"
            :auto-upload="false"
            :limit="1"
            accept=".xlsx,.xls"
            :on-change="onPrFileChange"
            :on-remove="onPrFileRemove"
            drag
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">拖拽 Excel 文件到此处，或 <em>点击上传</em></div>
            <template #tip>
              <div class="el-upload__tip">支持 .xlsx / .xls 格式；读取第一列（第3行起）的 PR 号，上限 2000 条</div>
            </template>
          </el-upload>
          <div style="margin-top: 16px; text-align: center">
            <el-button type="primary" :disabled="!prFile" :loading="prCheckLoading" @click="runPrCheck">
              {{ prCheckLoading ? '查询中，请耐心等待…' : '开始查询' }}
            </el-button>
          </div>
          <div v-if="prCheckLoading" class="pr-loading-hint">
            <el-icon class="is-loading"><Loading /></el-icon>
            正在逐条检索 PR，数量较多时可能需要 1~2 分钟，请勿关闭对话框
          </div>
        </div>

        <!-- 查询结果 -->
        <div v-else class="pr-check-result">
          <!-- 统计卡片 -->
          <div class="pr-stat-cards">
            <div class="pr-stat-card">
              <div class="pr-stat-num">{{ prCheckResult.total }}</div>
              <div class="pr-stat-label">总 PR 数</div>
            </div>
            <div class="pr-stat-card matched">
              <div class="pr-stat-num">{{ prCheckResult.matched_count }}</div>
              <div class="pr-stat-label">有关联记录</div>
            </div>
            <div class="pr-stat-card unmatched">
              <div class="pr-stat-num">{{ prCheckResult.unmatched_count }}</div>
              <div class="pr-stat-label">无关联记录</div>
            </div>
          </div>

          <!-- Tab 切换 -->
          <el-tabs v-model="prCheckTab" style="margin-top: 12px">

            <!-- 有关联 Tab：扁平化总表 + 分页 -->
            <el-tab-pane :label="`有关联 (${prCheckResult.matched_count})`" name="matched">
              <div v-if="prCheckResult.matched_count === 0" class="pr-empty">暂无有关联的 PR</div>
              <template v-else>
                <el-table
                  :data="pagedMatchedRows"
                  size="small"
                  border
                  style="width: 100%"
                  :max-height="prTableMaxHeight"
                  :row-class-name="prTableRowClass"
                >
                  <el-table-column prop="pr" label="PR 号" width="110" fixed>
                    <template #default="{ row }">
                      <span style="font-variant-numeric: tabular-nums; white-space: nowrap;">{{ row.pr }}</span>
                    </template>
                  </el-table-column>
                  <el-table-column prop="source" label="来源" width="110">
                    <template #default="{ row }">
                      <el-tooltip :content="row.source" placement="top" :show-after="300">
                        <div class="cell-ellipsis">{{ row.source || '-' }}</div>
                      </el-tooltip>
                    </template>
                  </el-table-column>
                  <el-table-column prop="case_number" label="用例编号" width="140">
                    <template #default="{ row }">
                      <el-tooltip :content="row.case_number" placement="top" :show-after="300" :disabled="!row.case_number">
                        <div class="cell-ellipsis">{{ row.case_number || '-' }}</div>
                      </el-tooltip>
                    </template>
                  </el-table-column>
                  <el-table-column label="用例名称" min-width="160">
                    <template #default="{ row }">
                      <el-tooltip :content="row.case_name" placement="top" :show-after="300" :disabled="!row.case_name">
                        <div class="cell-ellipsis">{{ row.case_name || '-' }}</div>
                      </el-tooltip>
                    </template>
                  </el-table-column>
                  <el-table-column label="测试计划" min-width="150">
                    <template #default="{ row }">
                      <el-tooltip :content="row.plan_name" placement="top" :show-after="300" :disabled="!row.plan_name">
                        <div class="cell-ellipsis">{{ row.plan_name || '-' }}</div>
                      </el-tooltip>
                    </template>
                  </el-table-column>
                  <el-table-column prop="result" label="结果" width="72">
                    <template #default="{ row }">
                      <el-tag v-if="row.result" :type="resultTagType(row.result)" size="small">{{ row.result }}</el-tag>
                      <span v-else>-</span>
                    </template>
                  </el-table-column>
                  <el-table-column label="项目" min-width="120">
                    <template #default="{ row }">
                      <el-tooltip :content="row.project" placement="top" :show-after="300" :disabled="!row.project">
                        <div class="cell-ellipsis">{{ row.project || '-' }}</div>
                      </el-tooltip>
                    </template>
                  </el-table-column>
                  <el-table-column label="匹配内容" min-width="180">
                    <template #default="{ row }">
                      <el-tooltip :content="row.matched_text" placement="top" :show-after="300" :disabled="!row.matched_text">
                        <div class="cell-ellipsis">{{ row.matched_text || '-' }}</div>
                      </el-tooltip>
                    </template>
                  </el-table-column>
                </el-table>
                <el-pagination
                  v-if="allMatchedRows.length > prPageSize"
                  :current-page="prCurrentPage"
                  :page-size="prPageSize"
                  :total="allMatchedRows.length"
                  :page-sizes="[20, 50, 100]"
                  layout="total, sizes, prev, pager, next"
                  style="margin-top: 10px; justify-content: flex-end;"
                  @current-change="prCurrentPage = $event"
                  @size-change="val => { prPageSize = val; prCurrentPage = 1 }"
                />
              </template>
            </el-tab-pane>

            <!-- 无关联 Tab -->
            <el-tab-pane :label="`无关联 (${prCheckResult.unmatched_count})`" name="unmatched">
              <div v-if="prCheckResult.unmatched_count === 0" class="pr-empty">所有 PR 均有关联记录</div>
              <div v-else class="pr-unmatched-list">
                <el-tag
                  v-for="item in unmatchedPrs"
                  :key="item.pr"
                  type="info"
                  style="margin: 4px"
                >{{ item.pr }}</el-tag>
              </div>
            </el-tab-pane>
          </el-tabs>

          <!-- 操作按钮 -->
          <div style="margin-top: 16px; display: flex; gap: 10px">
            <el-button @click="resetPrCheck">重新上传</el-button>
            <el-button type="primary" @click="exportPrCsv">
              <el-icon><Download /></el-icon>导出 CSV
            </el-button>
          </div>
        </div>
      </div>
    </el-dialog>

    <!-- 图表区域 -->
    <div class="charts-row">
      <!-- 用例执行数量 - 横向柱状图 -->
      <div class="chart-card-half">
        <div class="chart-title">{{ $t('analytics.caseExecutionCount') }} <span v-if="execTotalCount > 0" style="font-weight:400;font-size:13px;color:#909399">(总数量：{{ execTotalCount }})</span></div>
        <div ref="caseExecChartRef" class="chart-container-half" :style="{ height: chartHeight + 'px' }"></div>
      </div>
      <!-- 提交PR数量 - 横向柱状图 -->
      <div class="chart-card-half">
        <div class="chart-title">{{ $t('analytics.prCount') }} <span v-if="prTotalCount > 0" style="font-weight:400;font-size:13px;color:#909399">(总数量：{{ prTotalCount }})</span></div>
        <div ref="prCountChartRef" class="chart-container-half" :style="{ height: chartHeight + 'px' }"></div>
      </div>
    </div>

    <!-- ========== 个人用户分析 ========== -->
    <div class="section-divider">
      <div class="divider-line"></div>
      <span class="divider-text">{{ $t('analytics.personalSection') }}</span>
      <div class="divider-line"></div>
    </div>

    <div class="personal-filter">
      <el-select
        v-if="canViewAllUsers"
        v-model="selectedUserId"
        :placeholder="$t('analytics.selectUser')"
        filterable
        remote
        :remote-method="searchUsers"
        :loading="userLoading"
        @change="loadPersonalData"
        style="width: 220px"
      >
        <el-option v-for="u in userList" :key="u.id" :label="u.username" :value="u.id" />
      </el-select>
    </div>

    <!-- 个人图表 -->
    <div class="charts-grid" v-show="personalData">
      <div class="chart-card chart-wide" v-if="personalData?.exec_trend?.length">
        <div class="chart-title">{{ $t('analytics.personalExecTrend') }}</div>
        <div ref="personalTrendRef" class="chart-container"></div>
      </div>
      <div class="chart-card" v-if="personalData?.exec_by_result?.length">
        <div class="chart-title">{{ $t('analytics.personalExecResult') }}</div>
        <div ref="personalResultRef" class="chart-container"></div>
      </div>
      <div class="chart-card" v-if="personalData?.exec_by_hour?.length && canViewAllUsers">
        <div class="chart-title">{{ $t('analytics.personalHourDist') }}</div>
        <div ref="personalHourRef" class="chart-container"></div>
      </div>
      <div class="chart-card chart-wide" v-if="personalData?.plans_detail?.length">
        <div class="chart-title">{{ $t('analytics.personalPlans') }}</div>
        <el-table :data="paginatedPlans" stripe size="small" style="width:100%">
          <el-table-column prop="name" :label="$t('analytics.planName')" min-width="160" :show-overflow-tooltip="{ showAfter: 500 }" />
          <el-table-column :label="$t('common.status')" width="140">
            <template #default="{ row }">
              <el-tag :type="planStatusType(row.status)" size="small">{{ planStatusLabel(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="total_cases" :label="$t('analytics.totalCasesShort')" width="100" />
          <el-table-column prop="my_executed" :label="$t('analytics.myExecuted')" width="100" />
        </el-table>
        <el-pagination v-if="personalData.plans_detail.length > planPageSize" :current-page="planCurrentPage" :page-size="planPageSize" :total="personalData.plans_detail.length" layout="total, prev, pager, next" style="margin-top: 12px; justify-content: flex-end;" @current-change="planCurrentPage = $event" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { Refresh, Document, UploadFilled, Download, Loading } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import {
  getExecutionVelocity,
  getAnalyticsUserList, getPersonalAnalytics,
  getTestPlansForAnalytics,
  getPrCountByUser,
  checkPrInPlatform,
} from '../../api/analytics'
import { getUserRoleInTeam } from '../../api/team'
import { useUserRole } from '../../composables/useUserRole'
import { useTeam } from '../../composables/useTeam'
import { eventBus } from '../../utils/eventBus'

const { currentTeamId } = useTeam()

const { t } = useI18n()
const loading = ref(false)
const planLoading = ref(false)
const userLoading = ref(false)
const filters = ref({ plan_id: null, granularity: 'day' })
const dateRange = ref(null)
const filterOptions = ref({ plans: [] })
const planSearchQuery = ref('')
const selectedUserId = ref(null)
const userList = ref([])
const personalData = ref(null)
const personalLoading = ref(false)
const planCurrentPage = ref(1)
const planPageSize = 10
const currentUserRole = ref('member')
const analyticsPageRef = ref(null)
let debounceTimer = null

const { isSuperAdmin } = useUserRole()

const canViewAllUsers = computed(() => {
  if (isSuperAdmin.value) return true
  return currentUserRole.value === 'leader' || currentUserRole.value === 'org_manager'
})

const paginatedPlans = computed(() => {
  const list = personalData.value?.plans_detail || []
  const start = (planCurrentPage.value - 1) * planPageSize
  return list.slice(start, start + planPageSize)
})

const velResData = ref(null)
const prResData = ref(null)
const execTotalCount = ref(0)
const prTotalCount = ref(0)

const chartHeight = computed(() => {
  const userCount = velResData.value?.data?.by_user ? Object.keys(velResData.value.data.by_user).length : 0
  const baseHeight = 40
  const rowHeight = 32
  const minHeight = 200
  const calculatedHeight = minHeight + userCount * rowHeight
  return Math.min(calculatedHeight, 600)
})

const STATUS_MAP = {
  PENDING: { label: '待执行', type: 'info' },
  IN_PROGRESS: { label: '进行中', type: '' },
  COMPLETED: { label: '已完成', type: 'success' },
  IN_REVIEW: { label: '评审中', type: 'warning' },
  REJECTED: { label: '已驳回', type: 'danger' }
}

function planStatusLabel(status) { return STATUS_MAP[status]?.label || status }
function planStatusType(status) { return STATUS_MAP[status]?.type || 'info' }

// 图表 refs
const caseExecChartRef = ref(null)
const prCountChartRef = ref(null)
const personalTrendRef = ref(null)
const personalResultRef = ref(null)
const personalHourRef = ref(null)

const chartInstances = []
let chartResizeObserver = null
const observedChartEls = new Set()
const manualHoverCleanupMap = new WeakMap()
const COLORS = ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc', '#48b8d0']

function getDynamicGrid(isWide = false) {
  const width = window.innerWidth
  const isSmall = width < 768
  const isMedium = width < 1200
  if (isSmall) return { left: 50, right: 60, top: 30, bottom: 50, containLabel: true }
  if (isMedium) return { left: 45, right: 45, top: 30, bottom: 50, containLabel: true }
  return { left: isWide ? 60 : 50, right: 20, top: 30, bottom: 50, containLabel: true }
}

function getParams() {
  const p = {}
  if (filters.value.plan_id) {
    p.plan_id = filters.value.plan_id
  } else if (filterOptions.value.plans.length > 0) {
    p.plan_ids = filterOptions.value.plans.map(p => p.id).join(',')
  }
  if (dateRange.value?.length === 2) {
    p.start_date = dateRange.value[0]
    p.end_date = dateRange.value[1]
  } else if (filters.value.granularity) {
    p.granularity = filters.value.granularity
  }
  if (currentTeamId.value) p.team_id = currentTeamId.value
  return p
}

async function searchPlans(query) {
  planSearchQuery.value = query
  planLoading.value = true
  try {
    const params = { team_id: currentTeamId.value || undefined, page: 1, size: 100, search: query || undefined }
    const res = await getTestPlansForAnalytics(params)
    filterOptions.value.plans = res.data.records || []
  } catch {
    filterOptions.value.plans = []
  } finally {
    planLoading.value = false
  }
}

async function loadFilters() {
  await searchPlans('')
}

async function onGlobalTeamChange() {
  filters.value.plan_id = null
  selectedUserId.value = null
  personalData.value = null
  await loadFilters()
  await loadUserList()
  await loadUserRole()
  chartInstances.forEach(c => {
    if (!c || c.isDisposed()) return
    unbindManualAxisHover(c)
    c.dispose()
  })
  chartInstances.length = 0
  disposePersonalCharts()
  loadAllData()
}

function initChart(domRef) {
  if (!domRef) return null
  observeChartContainer(domRef)
  try {
    const existingInstance = echarts.getInstanceByDom(domRef)
    if (existingInstance) {
      unbindManualAxisHover(existingInstance)
      existingInstance.dispose()
    }
  } catch {}
  const size = getChartRenderSize(domRef)
  const instance = echarts.init(domRef, null, { renderer: 'svg', ...size })
  chartInstances.push(instance)
  return instance
}

function makePieOption(data) {
  const width = window.innerWidth
  const isSmall = width < 768
  const radius = isSmall ? ['30%', '55%'] : ['40%', '60%']
  const center = isSmall ? ['50%', '45%'] : ['50%', '42%']
  return {
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { bottom: 0, type: 'scroll' },
    color: COLORS,
    series: [{ type: 'pie', radius, center, label: { formatter: '{b}\n{d}%', fontSize: 11 }, emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.2)' } }, data }]
  }
}

function getChartRenderSize(domRef) {
  const rect = domRef.getBoundingClientRect()
  const width = Math.max(1, Math.floor(rect.width || domRef.clientWidth || 1))
  const height = Math.max(1, Math.floor(rect.height || domRef.clientHeight || 1))
  return { width, height }
}

function observeChartContainer(domRef) {
  if (!chartResizeObserver || !domRef || observedChartEls.has(domRef)) return
  chartResizeObserver.observe(domRef)
  observedChartEls.add(domRef)
}

function unobserveAllChartContainers() {
  if (!chartResizeObserver) return
  observedChartEls.forEach((el) => chartResizeObserver.unobserve(el))
  observedChartEls.clear()
}

function findNearestDataIndex(chart, x, length) {
  if (!chart || chart.isDisposed() || length <= 0) return -1
  const pixels = []
  for (let i = 0; i < length; i += 1) {
    const px = chart.convertToPixel({ xAxisIndex: 0 }, i)
    if (Number.isFinite(px)) pixels.push({ i, px })
  }
  if (!pixels.length) return -1
  let left = 0
  let right = pixels.length - 1
  while (left < right) {
    const mid = Math.floor((left + right) / 2)
    if (pixels[mid].px < x) left = mid + 1
    else right = mid
  }
  const curr = pixels[left]
  const prev = left > 0 ? pixels[left - 1] : curr
  return Math.abs(curr.px - x) < Math.abs(prev.px - x) ? curr.i : prev.i
}

function bindManualAxisHover(chart, getLength) {
  if (!chart || chart.isDisposed()) return
  const dom = chart.getDom()
  if (!dom || manualHoverCleanupMap.has(dom)) return
  let rafId = null
  let pendingEvent = null

  const processMove = () => {
    rafId = null
    const e = pendingEvent
    pendingEvent = null
    if (!e || !chart || chart.isDisposed()) return
    const rect = dom.getBoundingClientRect()
    if (!rect.width || !rect.height) return
    const scaleX = dom.clientWidth > 0 ? dom.clientWidth / rect.width : 1
    const scaleY = dom.clientHeight > 0 ? dom.clientHeight / rect.height : 1
    const x = (e.clientX - rect.left) * scaleX
    const y = (e.clientY - rect.top) * scaleY
    if (!chart.containPixel({ gridIndex: 0 }, [x, y])) return
    const idx = findNearestDataIndex(chart, x, getLength())
    if (idx < 0) return
    chart.dispatchAction({ type: 'updateAxisPointer', x, y })
    chart.dispatchAction({ type: 'showTip', seriesIndex: 0, dataIndex: idx })
  }

  const onMove = (e) => {
    pendingEvent = e
    if (!rafId) rafId = requestAnimationFrame(processMove)
  }
  const onLeave = () => {
    if (rafId) cancelAnimationFrame(rafId)
    rafId = null
    pendingEvent = null
    if (!chart || chart.isDisposed()) return
    chart.dispatchAction({ type: 'hideTip' })
  }

  dom.addEventListener('mousemove', onMove)
  dom.addEventListener('mouseleave', onLeave)
  manualHoverCleanupMap.set(dom, () => {
    if (rafId) cancelAnimationFrame(rafId)
    dom.removeEventListener('mousemove', onMove)
    dom.removeEventListener('mouseleave', onLeave)
  })
}

function unbindManualAxisHover(chart) {
  if (!chart || chart.isDisposed()) return
  const dom = chart.getDom()
  const cleanup = dom ? manualHoverCleanupMap.get(dom) : null
  if (cleanup) {
    cleanup()
    manualHoverCleanupMap.delete(dom)
  }
}

async function loadAllData() {
  loading.value = true
  const params = getParams()
  try {
    const [vRes, pRes] = await Promise.all([
      getExecutionVelocity(params),
      getPrCountByUser(params)
    ])
    velResData.value = vRes
    prResData.value = pRes

    if (vRes.data?.by_user) {
      const userData = vRes.data.by_user
      execTotalCount.value = Object.keys(userData).reduce((sum, u) => {
        const executions = userData[u]
        return sum + (Array.isArray(executions) ? executions.reduce((s, item) => s + (item.count || 0), 0) : 0)
      }, 0)
    } else {
      execTotalCount.value = 0
    }

    if (pRes.data?.by_user) {
      prTotalCount.value = Object.values(pRes.data.by_user).reduce((sum, count) => sum + (count || 0), 0)
    } else {
      prTotalCount.value = 0
    }

    await nextTick()

    // 用例执行数量 - 横向柱状图
    const caseExecChart = initChart(caseExecChartRef.value)
    if (caseExecChart && velResData.value?.data?.by_user) {
      const userData = velResData.value.data.by_user
      const users = Object.keys(userData)
      const totalCounts = users.map(u => {
        const executions = userData[u]
        return Array.isArray(executions) ? executions.reduce((sum, item) => sum + (item.count || 0), 0) : 0
      })

      const sortedIndices = totalCounts.map((c, i) => ({ count: c, index: i }))
        .sort((a, b) => b.count - a.count)
      const sortedUsers = sortedIndices.map(item => users[item.index]).reverse()
      const sortedCounts = sortedIndices.map(item => totalCounts[item.index]).reverse()

      const maxUsernameLen = Math.max(...sortedUsers.map(u => (u || '').length), 8)
      const leftPadding = Math.min(40, Math.max(10, maxUsernameLen * 3))
      const barColors = ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc', '#48b8d0']
      const execData = sortedCounts.map((count, idx) => ({
        value: count,
        itemStyle: {
          borderRadius: [0, 12, 12, 0],
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: barColors[idx % barColors.length] },
            { offset: 1, color: barColors[idx % barColors.length] + '99' }
          ])
        }
      }))
      caseExecChart.clear()
      caseExecChart.setOption({
        tooltip: {
          trigger: 'item',
          confine: true,
          appendToBody: true,
          backgroundColor: 'rgba(255,255,255,0.95)',
          borderColor: '#e8e8e8',
          borderWidth: 1,
          padding: [12, 16],
          textStyle: { color: '#303133', fontSize: 13 },
          extraCssText: 'box-shadow: 0 4px 12px rgba(0,0,0,0.12); border-radius: 8px;',
          formatter: (params) => `<div style="font-weight:600">${params.name}</div><div style="font-size:16px;margin-top:4px">${params.value}</div>`
        },
        grid: { left: leftPadding, right: 40, top: 10, bottom: 20, containLabel: true },
        xAxis: { type: 'value', show: false },
        yAxis: { type: 'category', data: sortedUsers, axisLine: { show: false }, axisTick: { show: false }, axisLabel: { fontSize: 13, color: '#606266', fontWeight: 500 } },
        series: [{
          type: 'bar',
          data: execData,
          barWidth: 24,
          label: { show: true, position: 'right', fontSize: 12, color: '#606266' },
          emphasis: { itemStyle: { opacity: 0.8 } },
          animationDuration: 1000,
          animationEasing: 'cubicOut'
        }]
      })
    }

    await nextTick()

    // PR数量 - 横向柱状图
    const prChart = initChart(prCountChartRef.value)
    if (prChart && prResData.value?.data?.by_user) {
      const userData = prResData.value.data.by_user
      const users = Object.keys(userData)
      const prCounts = users.map(u => userData[u] || 0)

      const sortedIndices = prCounts.map((c, i) => ({ count: c, index: i }))
        .sort((a, b) => b.count - a.count)
      const sortedUsers = sortedIndices.map(item => users[item.index]).reverse()
      const sortedCounts = sortedIndices.map(item => prCounts[item.index]).reverse()

      const maxPrUsernameLen = Math.max(...sortedUsers.map(u => (u || '').length), 8)
      const leftPaddingPr = Math.min(40, Math.max(10, maxPrUsernameLen * 3))
      const prBarColors = ['#91cc75', '#5470c6', '#fac858', '#ee6666', '#73c0de', '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc', '#48b8d0']
      const prData = sortedCounts.map((count, idx) => ({
        value: count,
        itemStyle: {
          borderRadius: [0, 12, 12, 0],
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: prBarColors[idx % prBarColors.length] },
            { offset: 1, color: prBarColors[idx % prBarColors.length] + '99' }
          ])
        }
      }))
      prChart.clear()
      prChart.setOption({
        tooltip: {
          trigger: 'item',
          confine: true,
          appendToBody: true,
          backgroundColor: 'rgba(255,255,255,0.95)',
          borderColor: '#e8e8e8',
          borderWidth: 1,
          padding: [12, 16],
          textStyle: { color: '#303133', fontSize: 13 },
          extraCssText: 'box-shadow: 0 4px 12px rgba(0,0,0,0.12); border-radius: 8px;',
          formatter: (params) => `<div style="font-weight:600">${params.name}</div><div style="font-size:16px;margin-top:4px">${params.value}</div>`
        },
        grid: { left: leftPaddingPr, right: 40, top: 10, bottom: 20, containLabel: true },
        xAxis: { type: 'value', show: false },
        yAxis: { type: 'category', data: sortedUsers, axisLine: { show: false }, axisTick: { show: false }, axisLabel: { fontSize: 13, color: '#606266', fontWeight: 500 } },
        series: [{
          type: 'bar',
          data: prData,
          barWidth: 24,
          label: { show: true, position: 'right', fontSize: 12, color: '#606266' },
          emphasis: { itemStyle: { opacity: 0.8 } },
          animationDuration: 1000,
          animationEasing: 'cubicOut'
        }]
      })
    }

    await nextTick()
    handleResize()
  } catch (e) {
    console.error('Analytics load error:', e)
  } finally {
    loading.value = false
  }
}

// 个人图表实例（单独管理，切换用户时需要销毁重建）
const personalChartInstances = []

function initPersonalChart(domRef) {
  if (!domRef) return null
  observeChartContainer(domRef)
  const size = getChartRenderSize(domRef)
  const instance = echarts.init(domRef, null, { renderer: 'svg', ...size })
  personalChartInstances.push(instance)
  return instance
}

function disposePersonalCharts() {
  personalChartInstances.forEach(c => {
    if (!c || c.isDisposed()) return
    unbindManualAxisHover(c)
    c.dispose()
  })
  personalChartInstances.length = 0
}

async function searchUsers(query) {
  userLoading.value = true
  try {
    const res = await getAnalyticsUserList({ team_id: currentTeamId.value || undefined, search: query || undefined })
    userList.value = res.data || []
  } catch { userList.value = [] }
  finally { userLoading.value = false }
}

async function loadUserList() {
  await searchUsers('')
}

async function loadUserRole() {
  if (!currentTeamId.value) {
    currentUserRole.value = 'member'
    return
  }
  try {
    const res = await getUserRoleInTeam(currentTeamId.value)
    currentUserRole.value = res.data?.role || 'member'
  } catch {
    currentUserRole.value = 'member'
  }
}

async function loadPersonalData() {
  if (!selectedUserId.value) { personalData.value = null; return }
  personalLoading.value = true
  planCurrentPage.value = 1
  disposePersonalCharts()
  personalData.value = null
  try {
    const params = { user_id: selectedUserId.value, ...getParams() }
    const res = await getPersonalAnalytics(params)
    personalData.value = res.data
    await nextTick()
    await nextTick()
    renderPersonalCharts()
  } catch (e) {
    console.error('Personal analytics error:', e)
    personalData.value = null
  } finally {
    personalLoading.value = false
  }
}

function renderPersonalCharts() {
  const d = personalData.value
  if (!d) return

  // 个人执行趋势（含团队平均对比）
  const ptChart = initPersonalChart(personalTrendRef.value)
  if (ptChart && d.exec_trend?.length) {
    const dateList = d.exec_trend.map(i => i.date)
    const series = [
      { name: t('analytics.personalTrend'), type: 'line', data: d.exec_trend.map(i => i.count), smooth: true, lineStyle: { width: 3 }, areaStyle: { opacity: 0.12 } }
    ]
    if (d.team_avg_trend?.length) {
      const avgDateMap = Object.fromEntries(d.team_avg_trend.map(i => [i.date, i.avg]))
      series.push({ name: t('analytics.teamAvg'), type: 'line', data: dateList.map(d => avgDateMap[d] ?? 0), smooth: true, lineStyle: { width: 2, type: 'dashed' }, itemStyle: { color: '#909399' } })
    }
    ptChart.setOption({
      tooltip: { trigger: 'axis', triggerOn: 'none', confine: true, appendToBody: true, axisPointer: { type: 'line', snap: true } }, legend: { bottom: 0 }, color: COLORS,
      grid: { ...getDynamicGrid(true), top: 20 },
      xAxis: { type: 'category', data: dateList }, yAxis: { type: 'value' },
      series
    })
    bindManualAxisHover(ptChart, () => dateList.length)
  }

  // 个人执行结果饼图
  const prChart = initPersonalChart(personalResultRef.value)
  if (prChart && d.exec_by_result?.length) prChart.setOption(makePieOption(d.exec_by_result))

  // 工作时段分布（0-23小时）
  const phChart = initPersonalChart(personalHourRef.value)
  if (phChart && d.exec_by_hour?.length) {
    const hourLabels = d.exec_by_hour.map(i => i.hour + ':00')
    phChart.setOption({
      tooltip: { trigger: 'axis', triggerOn: 'none', confine: true, appendToBody: true, axisPointer: { type: 'line', snap: true } }, color: ['#5470c6'],
      grid: { left: 40, right: 20, top: 10, bottom: 30 },
      xAxis: { type: 'category', data: hourLabels, axisLabel: { fontSize: 10 } },
      yAxis: { type: 'value' },
      series: [{ type: 'bar', data: d.exec_by_hour.map(i => i.count), barMaxWidth: 20, itemStyle: { borderRadius: [4, 4, 0, 0], color: (p) => p.data >= (Math.max(...d.exec_by_hour.map(i => i.count)) * 0.7) ? '#ee6666' : '#5470c6' } }]
    })
    bindManualAxisHover(phChart, () => hourLabels.length)
  }
}

function handleResize() {
  chartInstances.forEach(c => {
    if (c && !c.isDisposed()) {
      const size = getChartRenderSize(c.getDom())
      c.resize(size)
    }
  })
  personalChartInstances.forEach(c => {
    if (c && !c.isDisposed()) {
      const size = getChartRenderSize(c.getDom())
      c.resize(size)
    }
  })
}

function debounceResize() {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    handleResize()
  }, 200)
}

onMounted(async () => {
  if (window.ResizeObserver) {
    chartResizeObserver = new ResizeObserver(() => {
      chartInstances.forEach(c => c && !c.isDisposed() && c.resize(getChartRenderSize(c.getDom())))
      personalChartInstances.forEach(c => c && !c.isDisposed() && c.resize(getChartRenderSize(c.getDom())))
    })
  }
  await Promise.all([loadFilters(), loadUserList(), loadUserRole()])
  await loadAllData()

  if (!canViewAllUsers.value) {
    const currentUser = JSON.parse(localStorage.getItem('user') || '{}')
    if (currentUser.id) {
      selectedUserId.value = currentUser.id
      await loadPersonalData()
    }
  }

  window.addEventListener('resize', debounceResize)
  eventBus.on('teams-changed', onGlobalTeamChange)
})

onUnmounted(() => {
  if (debounceTimer) clearTimeout(debounceTimer)
  window.removeEventListener('resize', debounceResize)
  chartInstances.forEach(c => {
    if (!c || c.isDisposed()) return
    unbindManualAxisHover(c)
    c.dispose()
  })
  disposePersonalCharts()
  unobserveAllChartContainers()
  if (chartResizeObserver) {
    chartResizeObserver.disconnect()
    chartResizeObserver = null
  }
  eventBus.off('teams-changed', onGlobalTeamChange)
})

watch(() => filters.value.granularity, (newVal) => {
  if (newVal) {
    dateRange.value = null
  }
})

watch(() => dateRange.value, (newVal) => {
  if (newVal && newVal.length === 2) {
    filters.value.granularity = null
  }
})

watch(() => [filters.value.plan_id, dateRange.value, filters.value.granularity], () => {
  chartInstances.forEach(c => {
    if (!c || c.isDisposed()) return
    unbindManualAxisHover(c)
    c.dispose()
  })
  chartInstances.length = 0
  disposePersonalCharts()
  loadAllData()
  if (selectedUserId.value) loadPersonalData()
})

watch(currentTeamId, async (newVal, oldVal) => {
  if (newVal !== oldVal) {
    filters.value.plan_id = null
    await loadFilters()
    await loadAllData()
  }
})

// ── PR 关联查询 ────────────────────────────────────────────────────────────────
const prCheckVisible = ref(false)
const prFile = ref(null)
const prUploadRef = ref(null)
const prCheckLoading = ref(false)
const prCheckResult = ref(null)
const prCheckTab = ref('matched')
const prCurrentPage = ref(1)
const prPageSize = ref(20)

// 表格限高：对话框 top=4vh，标题栏≈55px，统计卡片≈90px，tabs≈44px，分页≈52px，底部按钮≈52px，留白 20px
// 视口高度 * 0.92 - 上述固定高度 = 表格可用高度
const prTableMaxHeight = computed(() => {
  const vh = typeof window !== 'undefined' ? window.innerHeight : 800
  return Math.max(200, Math.floor(vh * 0.92) - 55 - 90 - 44 - 52 - 52 - 20)
})

// 把所有有匹配的 PR 打平成行数组，方便统一分页
const allMatchedRows = computed(() => {
  const rows = []
  for (const item of (prCheckResult.value?.results || [])) {
    if (!item.matched) continue
    for (const h of item.hits) {
      rows.push({ pr: item.pr, ...h })
    }
  }
  return rows
})

const pagedMatchedRows = computed(() => {
  const start = (prCurrentPage.value - 1) * prPageSize.value
  return allMatchedRows.value.slice(start, start + prPageSize.value)
})

const unmatchedPrs = computed(() => (prCheckResult.value?.results || []).filter(r => !r.matched))

// 同一 PR 的行背景交替，方便区分
function prTableRowClass({ row, rowIndex }) {
  // 找到当前 PR 在 allMatchedRows 中出现的第一个索引，按 PR 分组奇偶交替
  const prList = [...new Set(allMatchedRows.value.map(r => r.pr))]
  const idx = prList.indexOf(row.pr)
  return idx % 2 === 0 ? '' : 'pr-row-alt'
}

function onPrFileChange(file) {
  prFile.value = file.raw
}
function onPrFileRemove() {
  prFile.value = null
}

async function runPrCheck() {
  if (!prFile.value) return
  prCheckLoading.value = true
  try {
    const fd = new FormData()
    fd.append('file', prFile.value)
    const res = await checkPrInPlatform(fd)
    if (res.code === 200) {
      prCheckResult.value = res.data
      prCurrentPage.value = 1
      prCheckTab.value = res.data.matched_count > 0 ? 'matched' : 'unmatched'
    } else {
      ElMessage.error(res.message || '查询失败')
    }
  } catch (e) {
    if (e?.code === 'ECONNABORTED' || String(e).includes('timeout')) {
      ElMessage.error('请求超时，PR 数量较多时建议分批上传（每批 ≤ 200 条）')
    } else {
      ElMessage.error('查询失败，请检查网络或稍后重试')
    }
  } finally {
    prCheckLoading.value = false
  }
}

function resetPrCheck() {
  prCheckResult.value = null
  prFile.value = null
  prCurrentPage.value = 1
  if (prUploadRef.value) prUploadRef.value.clearFiles()
}

function resultTagType(result) {
  const map = { PASS: 'success', Fail: 'danger', BLOCK: 'warning', NA: 'info', SKIP: 'info' }
  return map[result] || 'info'
}

function exportPrCsv() {
  if (!prCheckResult.value) return
  const BOM = '\uFEFF'
  const headers = ['PR号', '是否有关联', '来源', '用例编号', '用例名称', '测试计划', '执行结果', '执行时间', '项目', '执行人', '匹配内容']
  const rows = []
  for (const item of prCheckResult.value.results) {
    if (item.hits.length > 0) {
      for (const h of item.hits) {
        rows.push([item.pr, '有', h.source, h.case_number, h.case_name, h.plan_name, h.result, h.executed_at, h.project, h.executor, h.matched_text])
      }
    } else {
      rows.push([item.pr, '无', '', '', '', '', '', '', '', '', ''])
    }
  }
  const csvContent = BOM + [headers, ...rows].map(r => r.map(v => `"${String(v || '').replace(/"/g, '""')}"`).join(',')).join('\n')
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `PR关联查询_${new Date().toISOString().slice(0, 10)}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

</script>

<style scoped>
.analytics-page { padding: 0; }
.filter-bar { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 16px 20px; background: #fff; border-radius: 8px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
.filter-left { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.filter-right { display: flex; align-items: center; gap: 8px; }
.charts-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 14px; }
.charts-row { display: flex; gap: 14px; }
.chart-card { background: #fff; border-radius: 8px; padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
.chart-card-half { flex: 1; background: #fff; border-radius: 8px; padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); min-width: 0; }
.chart-card.chart-wide { grid-column: span 2; }
.chart-title { font-size: 14px; font-weight: 600; color: #1d2129; margin-bottom: 12px; padding-left: 8px; border-left: 3px solid #409eff; }
.chart-container { width: 100%; height: 380px; }
.chart-container-half { width: 100%; height: 320px; }
@media (max-width: 1200px) { .charts-grid { grid-template-columns: 1fr; } .charts-row { flex-direction: column; } .chart-card.chart-wide { grid-column: span 1; } }
@media (max-width: 768px) { .filter-bar { flex-direction: column; align-items: flex-start; } }
.section-divider { display: flex; align-items: center; gap: 16px; margin: 32px 0 16px; }
.divider-line { flex: 1; height: 1px; background: linear-gradient(to right, transparent, #dcdfe6, transparent); }
.divider-text { font-size: 16px; font-weight: 600; color: #303133; white-space: nowrap; }
.personal-filter { margin-bottom: 16px; padding: 12px 20px; background: #fff; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }

/* PR 关联查询对话框样式 */
.pr-check-dialog { min-height: 200px; }
.pr-upload-area { display: flex; flex-direction: column; align-items: center; }
.pr-upload-area :deep(.el-upload-dragger) { width: 500px; }
.pr-loading-hint { margin-top: 14px; display: flex; align-items: center; gap: 8px; font-size: 13px; color: #909399; }
.pr-stat-cards { display: flex; gap: 16px; margin-bottom: 8px; }
.pr-stat-card { flex: 1; background: #f5f7fa; border-radius: 8px; padding: 16px 20px; text-align: center; border: 1px solid #e4e7ed; }
.pr-stat-card.matched { background: #f0f9eb; border-color: #b3e19d; }
.pr-stat-card.unmatched { background: #fdf6ec; border-color: #f5dab1; }
.pr-stat-num { font-size: 28px; font-weight: 700; color: #303133; line-height: 1; }
.pr-stat-card.matched .pr-stat-num { color: #67c23a; }
.pr-stat-card.unmatched .pr-stat-num { color: #e6a23c; }
.pr-stat-label { font-size: 13px; color: #606266; margin-top: 6px; }
/* 单元格强制单行 + 省略号，tooltip 显示完整内容 */
.pr-check-result :deep(.el-table .cell) { white-space: nowrap; overflow: hidden; padding: 0 8px; }
.cell-ellipsis { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; display: block; }
/* 交替行背景 */
.pr-check-result :deep(.pr-row-alt td) { background: #f7f9ff !important; }
.pr-unmatched-list { padding: 8px 0; max-height: 400px; overflow-y: auto; }
.pr-empty { text-align: center; color: #909399; padding: 40px 0; font-size: 14px; }
</style>