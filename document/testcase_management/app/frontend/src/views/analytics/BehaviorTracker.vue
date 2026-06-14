<template>
  <div class="behavior-tracker-page">
    <div class="filter-bar">
      <div class="filter-left">
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
          style="width: 240px"
        />
        <el-select v-model="filterDimension" placeholder="统计维度" style="width: 120px" @change="handleDimensionChange">
          <el-option label="全部概览" value="overview" />
          <el-option label="按页面" value="page" />
          <el-option label="按用户" value="user" />
          <el-option label="按日期" value="date" />
        </el-select>
        <div v-if="filterDimension === 'page'" class="search-box">
          <el-input
            v-model="searchPage"
            placeholder="搜索页面"
            clearable
            @keyup.enter="loadData"
            @clear="loadData"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
        <div v-if="filterDimension === 'user'" class="search-box">
          <el-input
            v-model="searchUsername"
            placeholder="搜索用户"
            clearable
            @keyup.enter="loadData"
            @clear="loadData"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
        <div v-if="filterDimension === 'action'" class="search-box">
          <el-input
            v-model="searchAction"
            placeholder="搜索功能"
            clearable
            @keyup.enter="loadData"
            @clear="loadData"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
      </div>
      <div class="filter-right">
        <el-button type="primary" @click="loadData" :loading="loading">
          <el-icon><Refresh /></el-icon>刷新
        </el-button>
      </div>
    </div>

    <div v-if="filterDimension === 'overview'" class="overview-section">
      <div class="stats-cards">
        <div class="stat-card stat-primary">
          <div class="stat-icon"><el-icon :size="32"><DataAnalysis /></el-icon></div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.total_count }}</div>
            <div class="stat-label">总行为次数</div>
          </div>
        </div>
        <div class="stat-card stat-success">
          <div class="stat-icon"><el-icon :size="32"><View /></el-icon></div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.page_views }}</div>
            <div class="stat-label">页面访问次数</div>
          </div>
        </div>
        <div class="stat-card stat-warning">
          <div class="stat-icon"><el-icon :size="32"><Pointer /></el-icon></div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.clicks }}</div>
            <div class="stat-label">点击次数</div>
          </div>
        </div>
        <div class="stat-card stat-danger">
          <div class="stat-icon"><el-icon :size="32"><User /></el-icon></div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.unique_users }}</div>
            <div class="stat-label">活跃用户数</div>
          </div>
        </div>
      </div>

      <div class="tables-section">
        <div class="table-card">
          <div class="table-title">页面访问排行 TOP 20</div>
          <el-table :data="pageStats.slice(0, 20)" stripe size="small" max-height="300">
            <el-table-column prop="page_name" label="页面名称" min-width="180">
              <template #default="{ row }">
                <el-tooltip :content="row.page_name" placement="top" :show-after="500">
                  <div class="cell-ellipsis">{{ row.page_name }}</div>
                </el-tooltip>
              </template>
            </el-table-column>
            <el-table-column prop="page_path" label="页面路径" min-width="200">
              <template #default="{ row }">
                <el-tooltip :content="row.page_path" placement="top" :show-after="500">
                  <div class="cell-ellipsis">{{ row.page_path }}</div>
                </el-tooltip>
              </template>
            </el-table-column>
            <el-table-column prop="total_count" label="总次数" width="100" />
            <el-table-column prop="page_views" label="访问" width="80" />
            <el-table-column prop="unique_users" label="用户数" width="80" />
          </el-table>
        </div>
        <div class="table-card">
          <div class="table-title">用户访问页面明细 TOP 20</div>
          <el-table :data="userStats.slice(0, 20)" stripe size="small" max-height="300">
            <el-table-column prop="username" label="用户名" width="150" />
            <el-table-column prop="page_name" label="页面" min-width="150">
              <template #default="{ row }">
                <el-tooltip :content="row.page_name" placement="top" :show-after="500">
                  <div class="cell-ellipsis">{{ row.page_name }}</div>
                </el-tooltip>
              </template>
            </el-table-column>
            <el-table-column prop="visit_count" label="访问次数" width="100" />
            <el-table-column prop="page_path" label="页面路径" min-width="200">
              <template #default="{ row }">
                <el-tooltip :content="row.page_path" placement="top" :show-after="500">
                  <div class="cell-ellipsis">{{ row.page_path }}</div>
                </el-tooltip>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </div>

    <div v-if="filterDimension === 'page'" class="page-section">
      <div class="table-card">
        <div class="table-title">页面访问统计</div>
        <el-table ref="pageTableRef" :data="pageStats" stripe size="small" max-height="400">
          <el-table-column prop="page_name" label="页面名称" min-width="180">
            <template #default="{ row }">
              <el-tooltip :content="row.page_name" placement="top" :show-after="500">
                <div class="cell-ellipsis">{{ row.page_name }}</div>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column prop="page_path" label="页面路径" min-width="250">
            <template #default="{ row }">
              <el-tooltip :content="row.page_path" placement="top" :show-after="500">
                <div class="cell-ellipsis">{{ row.page_path }}</div>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column prop="total_count" label="总次数" width="100" />
          <el-table-column prop="page_views" label="访问次数" width="100" />
          <el-table-column prop="unique_users" label="用户数" width="100" />
        </el-table>
        <el-pagination
          v-if="pageStatsTotal > 0"
          v-model:current-page="pageStatsPage"
          v-model:page-size="pageStatsPageSize"
          :total="pageStatsTotal"
          :page-sizes="[20, 50, 100]"
          layout="total, sizes, prev, pager, next"
          @size-change="async () => { await loadPageStats(false); await nextTick(); scrollToTopPage(); }"
          @current-change="async () => { await loadPageStats(false); await nextTick(); scrollToTopPage(); }"
          style="margin-top: 16px; justify-content: flex-end;"
        />
      </div>
    </div>

    <div v-if="filterDimension === 'user'" class="user-section">
      <div class="table-card">
        <div class="table-title">用户访问页面明细</div>
        <el-table ref="userTableRef" :data="userStats" stripe size="small" max-height="400">
          <el-table-column prop="username" label="用户名" width="150" />
          <el-table-column prop="page_name" label="页面" min-width="150">
            <template #default="{ row }">
              <el-tooltip :content="row.page_name" placement="top" :show-after="500">
                <div class="cell-ellipsis">{{ row.page_name }}</div>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column prop="visit_count" label="访问次数" width="100" />
          <el-table-column prop="page_path" label="页面路径" min-width="200">
            <template #default="{ row }">
              <el-tooltip :content="row.page_path" placement="top" :show-after="500">
                <div class="cell-ellipsis">{{ row.page_path }}</div>
              </el-tooltip>
            </template>
          </el-table-column>
        </el-table>
        <el-pagination
          v-if="userStatsTotal > 0"
          v-model:current-page="userStatsPage"
          v-model:page-size="userStatsPageSize"
          :total="userStatsTotal"
          :page-sizes="[20, 50, 100]"
          layout="total, sizes, prev, pager, next"
          @size-change="async () => { await loadUserStats(false); await nextTick(); scrollToTopUser(); }"
          @current-change="async () => { await loadUserStats(false); await nextTick(); scrollToTopUser(); }"
          style="margin-top: 16px; justify-content: flex-end;"
        />
      </div>
    </div>

    <div v-if="filterDimension === 'action'" class="action-section">
      <div class="table-card">
        <div class="table-title">功能操作统计</div>
        <el-table :data="actionStats" stripe size="small" max-height="500">
          <el-table-column prop="action_name" label="功能名称" min-width="180">
            <template #default="{ row }">
              <el-tooltip :content="row.action_name" placement="top" :show-after="500">
                <div class="cell-ellipsis">{{ row.action_name }}</div>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column prop="action_type" label="操作类型" width="120" />
          <el-table-column prop="page_path" label="所属页面" min-width="250">
            <template #default="{ row }">
              <el-tooltip :content="row.page_path" placement="top" :show-after="500">
                <div class="cell-ellipsis">{{ row.page_path }}</div>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column prop="total_count" label="执行次数" width="120" />
          <el-table-column prop="unique_users" label="用户数" width="120" />
        </el-table>
      </div>
    </div>

    <div v-if="filterDimension === 'date'" class="date-section">
      <div class="charts-section">
        <div class="chart-card">
          <div class="chart-title">每日行为趋势</div>
          <div ref="dateTrendChartRef" class="chart-container"></div>
        </div>
      </div>
      <div class="table-card">
        <div class="table-title">每日统计明细</div>
        <el-table :data="dateStats" stripe size="small" max-height="400">
          <el-table-column prop="date" label="日期" width="120" />
          <el-table-column prop="total_count" label="总次数" width="100" />
          <el-table-column prop="page_views" label="访问次数" width="100" />
          <el-table-column prop="clicks" label="点击次数" width="100" />
          <el-table-column prop="actions" label="操作次数" width="100" />
        </el-table>
      </div>
    </div>

    <div class="records-section">
      <div class="section-header">
        <div class="section-title">行为记录明细</div>
      </div>
      <div class="records-filters">
        <el-select v-model="recordBehaviorType" placeholder="行为类型" clearable style="width: 120px" @change="loadRecords">
          <el-option label="全部" value="" />
          <el-option label="页面访问" value="page_view" />
          <el-option label="点击" value="click" />
        </el-select>
        <div class="search-box">
          <el-input
            v-model="recordUsername"
            placeholder="搜索用户"
            clearable
            @keyup.enter="loadRecords"
            @clear="loadRecords"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
        <div class="search-box">
          <el-input
            v-model="recordPagePath"
            placeholder="搜索页面"
            clearable
            @keyup.enter="loadRecords"
            @clear="loadRecords"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
        <el-button type="primary" @click="loadRecords">
          <el-icon><Search /></el-icon>查询
        </el-button>
      </div>
      <div class="records-table-wrapper">
        <el-table ref="recordsTableRef" :data="records" stripe size="small">
        <el-table-column prop="created_at" label="时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="username" label="用户" width="150" />
        <el-table-column prop="behavior_type" label="类型" width="80">
          <template #default="{ row }">
            <el-tag :type="getBehaviorTypeTag(row.behavior_type)" size="small">
              {{ getBehaviorTypeLabel(row.behavior_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="page_name" label="页面" min-width="200">
          <template #default="{ row }">
            <el-tooltip :content="row.page_name" placement="top" :show-after="500">
              <div class="cell-ellipsis">{{ row.page_name }}</div>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column prop="page_path" label="页面路径" min-width="250">
          <template #default="{ row }">
            <el-tooltip :content="row.page_path" placement="top" :show-after="500">
              <div class="cell-ellipsis">{{ row.page_path }}</div>
            </el-tooltip>
          </template>
        </el-table-column>
      </el-table>
      </div>
      <el-pagination
        v-if="recordTotal > 0"
        v-model:current-page="recordPage"
        v-model:page-size="recordPageSize"
        :total="recordTotal"
        :page-sizes="[20, 50, 100]"
        layout="total, sizes, prev, pager, next"
        @size-change="async () => { await loadRecords(false); await nextTick(); scrollToTopRecords(); }"
        @current-change="async () => { await loadRecords(false); await nextTick(); scrollToTopRecords(); }"
        style="margin-top: 16px; justify-content: flex-end;"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { DataAnalysis, View, Pointer, Operation, User, Refresh, Search } from '@element-plus/icons-vue'
import axios from 'axios'
import * as echarts from 'echarts'
import { useScrollToTop } from '@/composables/useScrollToTop'

const API_BASE = '/api/behavior-tracker'

const getAuthHeaders = () => {
  const token = localStorage.getItem('token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

const loading = ref(false)
const dateRange = ref([])
const filterDimension = ref('overview')
const searchPage = ref('')
const searchUsername = ref('')
const searchAction = ref('')

const stats = ref({
  total_count: 0,
  page_views: 0,
  clicks: 0,
  actions: 0,
  unique_users: 0
})

const pageStats = ref([])
const pageStatsTotal = ref(0)
const pageStatsPage = ref(1)
const pageStatsPageSize = ref(50)
const userStats = ref([])
const userStatsTotal = ref(0)
const userStatsPage = ref(1)
const userStatsPageSize = ref(50)
const actionStats = ref([])
const dateStats = ref([])
const records = ref([])
const recordPage = ref(1)
const recordPageSize = ref(50)
const recordTotal = ref(0)
const recordBehaviorType = ref('')
const recordUsername = ref('')
const recordPagePath = ref('')

const trendChartRef = ref(null)
const dateTrendChartRef = ref(null)
let trendChart = null
let dateTrendChart = null

const pageTableRef = ref(null)
const userTableRef = ref(null)
const recordsTableRef = ref(null)

const { scrollToTop: scrollToTopPage } = useScrollToTop(pageTableRef)
const { scrollToTop: scrollToTopUser } = useScrollToTop(userTableRef)
const { scrollToTop: scrollToTopRecords } = useScrollToTop(recordsTableRef)

const getDateParams = () => {
  return {
    date_from: dateRange.value?.[0] || null,
    date_to: dateRange.value?.[1] || null
  }
}

const loadStats = async () => {
  try {
    const params = getDateParams()
    const res = await axios.get(`${API_BASE}/stats/overview`, { params, headers: getAuthHeaders() })
    stats.value = res.data
  } catch (e) {
    console.error('Failed to load stats:', e)
  }
}

const loadPageStats = async (resetPage = true) => {
  try {
    if (resetPage) {
      pageStatsPage.value = 1
    }
    const params = {
      ...getDateParams(),
      search: searchPage.value || undefined,
      page: pageStatsPage.value,
      page_size: pageStatsPageSize.value
    }
    const res = await axios.get(`${API_BASE}/stats/by-page`, { params, headers: getAuthHeaders() })
    pageStats.value = res.data.items || []
    pageStatsTotal.value = res.data.total || 0
  } catch (e) {
    console.error('Failed to load page stats:', e)
  }
}

const loadUserStats = async (resetPage = true) => {
  try {
    if (resetPage) {
      userStatsPage.value = 1
    }
    const params = {
      ...getDateParams(),
      search: searchUsername.value || undefined,
      page: userStatsPage.value,
      page_size: userStatsPageSize.value
    }
    const res = await axios.get(`${API_BASE}/stats/by-user`, { params, headers: getAuthHeaders() })
    userStats.value = res.data.items || []
    userStatsTotal.value = res.data.total || 0
  } catch (e) {
    console.error('Failed to load user stats:', e)
  }
}

const loadActionStats = async () => {
  try {
    const params = { ...getDateParams(), limit: 30, search: searchAction.value || undefined }
    const res = await axios.get(`${API_BASE}/stats/by-action`, { params, headers: getAuthHeaders() })
    actionStats.value = res.data
  } catch (e) {
    console.error('Failed to load action stats:', e)
  }
}

const loadDateStats = async () => {
  try {
    const params = getDateParams()
    const res = await axios.get(`${API_BASE}/stats/by-date`, { params, headers: getAuthHeaders() })
    dateStats.value = res.data
    nextTick(() => {
      renderDateTrendChart()
    })
  } catch (e) {
    console.error('Failed to load date stats:', e)
  }
}

const loadRecords = async (resetPage = true) => {
  try {
    if (resetPage) {
      recordPage.value = 1
    }
    const params = {
      ...getDateParams(),
      page: recordPage.value,
      page_size: recordPageSize.value,
      behavior_type: recordBehaviorType.value || undefined,
      username: recordUsername.value || undefined,
      page_path: recordPagePath.value || undefined
    }
    const res = await axios.get(`${API_BASE}/records`, { params, headers: getAuthHeaders() })
    records.value = res.data.items
    recordTotal.value = res.data.total
  } catch (e) {
    console.error('Failed to load records:', e)
  }
}

const loadData = async () => {
  loading.value = true
  try {
    await Promise.all([
      loadStats(),
      loadPageStats(),
      loadUserStats(),
      loadActionStats(),
      loadRecords()
    ])
    if (filterDimension.value === 'date') {
      await loadDateStats()
    }
    nextTick(() => {
      renderTrendChart()
    })
  } finally {
    loading.value = false
  }
}

const handleDimensionChange = () => {
  if (filterDimension.value === 'date') {
    loadDateStats()
  } else if (filterDimension.value === 'page') {
    loadPageStats()
  } else if (filterDimension.value === 'user') {
    loadUserStats()
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

const getBehaviorTypeTag = (type) => {
  const map = {
    'page_view': 'primary',
    'click': 'warning',
    'action': 'success'
  }
  return map[type] || 'info'
}

const getBehaviorTypeLabel = (type) => {
  const map = {
    'page_view': '访问',
    'click': '点击',
    'action': '操作'
  }
  return map[type] || type
}

const renderTrendChart = () => {
  if (!trendChartRef.value) return
  if (trendChart) {
    trendChart.dispose()
  }

  const data = dateStats.value.length > 0 ? dateStats.value : []

  trendChart = echarts.init(trendChartRef.value)
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' }
    },
    legend: {
      data: ['总次数', '页面访问', '点击', '功能操作']
    },
    xAxis: {
      type: 'category',
      data: data.map(d => d.date?.slice(5, 10) || ''),
      axisLabel: { rotate: 45 }
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '总次数',
        type: 'line',
        data: data.map(d => d.total_count),
        smooth: true,
        areaStyle: { opacity: 0.3 }
      },
      {
        name: '页面访问',
        type: 'line',
        data: data.map(d => d.page_views),
        smooth: true
      },
      {
        name: '点击',
        type: 'line',
        data: data.map(d => d.clicks),
        smooth: true
      },
      {
        name: '功能操作',
        type: 'line',
        data: data.map(d => d.actions),
        smooth: true
      }
    ],
    grid: {
      left: 60,
      right: 40,
      top: 60,
      bottom: 40
    }
  }
  trendChart.setOption(option)
}

const renderDateTrendChart = () => {
  if (!dateTrendChartRef.value) return
  if (dateTrendChart) {
    dateTrendChart.dispose()
  }

  const data = dateStats.value

  dateTrendChart = echarts.init(dateTrendChartRef.value)
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' }
    },
    legend: {
      data: ['总次数', '页面访问', '点击', '功能操作']
    },
    xAxis: {
      type: 'category',
      data: data.map(d => d.date?.slice(5, 10) || ''),
      axisLabel: { rotate: 45 }
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '总次数',
        type: 'bar',
        data: data.map(d => d.total_count),
        itemStyle: { color: '#6366f1' }
      },
      {
        name: '页面访问',
        type: 'line',
        data: data.map(d => d.page_views),
        smooth: true,
        itemStyle: { color: '#22c55e' }
      },
      {
        name: '点击',
        type: 'line',
        data: data.map(d => d.clicks),
        smooth: true,
        itemStyle: { color: '#f59e0b' }
      },
      {
        name: '功能操作',
        type: 'line',
        data: data.map(d => d.actions),
        smooth: true,
        itemStyle: { color: '#3b82f6' }
      }
    ],
    grid: {
      left: 60,
      right: 40,
      top: 60,
      bottom: 40
    }
  }
  dateTrendChart.setOption(option)
}

onMounted(() => {
  const now = new Date()
  const thirtyDaysAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)
  dateRange.value = [
    thirtyDaysAgo.toISOString().slice(0, 10),
    now.toISOString().slice(0, 10)
  ]
  loadData()
})

watch(dateRange, () => {
  if (filterDimension.value === 'overview') {
    loadData()
  }
})

watch(filterDimension, () => {
  recordUsername.value = ''
  recordPagePath.value = ''
  loadRecords()
})
</script>

<style scoped>
.behavior-tracker-page {
  padding: 20px;
  background: #f8fafc;
  min-height: 100%;
}

.filter-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 16px 20px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.filter-left {
  display: flex;
  gap: 12px;
  align-items: center;
}

.filter-right {
  display: flex;
  gap: 12px;
}

.search-box {
  width: 180px;
}

.search-box :deep(.el-input__wrapper) {
  border-radius: 8px;
  box-shadow: 0 0 0 1px #dcdfe6 inset;
}

.search-box :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #c0c4cc inset;
}

.search-box :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px #409eff inset;
}

.search-box :deep(.el-input__inner) {
  height: 28px;
  line-height: 28px;
}

.records-filters {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
  align-items: center;
}

.records-filters > .el-select {
  width: 120px;
}

.records-filters .search-box {
  width: 150px;
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
  padding: 20px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  transition: transform 0.2s, box-shadow 0.2s;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16px;
}

.stat-primary .stat-icon { background: linear-gradient(135deg, #6366f1, #8b5cf6); color: #fff; }
.stat-success .stat-icon { background: linear-gradient(135deg, #22c55e, #10b981); color: #fff; }
.stat-warning .stat-icon { background: linear-gradient(135deg, #f59e0b, #f97316); color: #fff; }
.stat-info .stat-icon { background: linear-gradient(135deg, #3b82f6, #0ea5e9); color: #fff; }
.stat-danger .stat-icon { background: linear-gradient(135deg, #ef4444, #dc2626); color: #fff; }

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #1e293b;
  line-height: 1.2;
}

.stat-label {
  font-size: 13px;
  color: #64748b;
  margin-top: 4px;
}

.charts-section {
  margin-bottom: 20px;
}

.chart-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.chart-title {
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 16px;
}

.chart-container {
  height: 300px;
}

.tables-section {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 20px;
}

.table-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.table-wide {
  grid-column: span 2;
}

.table-title {
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 16px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
}

.records-section {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  margin-top: 20px;
  min-height: calc(100vh - 200px);
}

.records-table-wrapper {
  height: calc(100vh - 320px);
  margin-top: 16px;
}

.records-table-wrapper :deep(.el-table) {
  height: 100%;
}

.records-table-wrapper :deep(.el-table__header-wrapper) {
  position: sticky;
  top: 0;
  z-index: 100;
}

.records-table-wrapper :deep(.el-table__body-wrapper) {
  overflow-y: auto;
}

.page-section, .user-section, .action-section, .date-section {
  margin-bottom: 20px;
}

.cell-ellipsis {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (max-width: 1400px) {
  .stats-cards {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 1000px) {
  .stats-cards {
    grid-template-columns: repeat(2, 1fr);
  }
  .tables-section {
    grid-template-columns: 1fr;
  }
  .table-wide {
    grid-column: span 1;
  }
}
</style>