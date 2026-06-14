<template>
  <div class="task-overview-container">
    <div class="table-header">
      <div class="header-left">
        <el-button v-if="hasButton('testplans', 'taskOverviewCreate')" type="primary" :icon="Plus" @click="handleCreate">
          {{ $t('taskOverview.create') }}
        </el-button>
      </div>
      <div class="header-right">
        <el-input
          v-model="searchKeyword"
          :placeholder="$t('taskOverview.searchPlaceholder')"
          style="width: 250px;"
          clearable
          @clear="handleSearch"
          @keyup.enter="handleSearch"
        >
          <template #suffix>
            <el-icon class="el-input__icon" style="cursor: pointer;" @click="handleSearch"><Search /></el-icon>
          </template>
        </el-input>
      </div>
    </div>

    <div class="stats-cards">
      <div class="stat-card" :class="{ active: statusFilter === null }" @click="filterByStatus(null)">
        <div class="stat-label">{{ $t('taskOverview.all') }}</div>
        <div class="stat-value">{{ statistics.total }}</div>
      </div>
      <div class="stat-card" :class="{ active: statusFilter === 'PENDING' }" @click="filterByStatus('PENDING')">
        <div class="stat-label">{{ $t('taskOverview.statusPending') }}</div>
        <div class="stat-value" style="color: var(--text-200);">{{ statistics.pending }}</div>
      </div>
      <div class="stat-card" :class="{ active: statusFilter === 'IN_PROGRESS' }" @click="filterByStatus('IN_PROGRESS')">
        <div class="stat-label">{{ $t('taskOverview.statusInProgress') }}</div>
        <div class="stat-value" style="color: var(--primary-200);">{{ statistics.inProgress }}</div>
      </div>
      <div class="stat-card" :class="{ active: statusFilter === 'COMPLETED' }" @click="filterByStatus('COMPLETED')">
        <div class="stat-label">{{ $t('taskOverview.statusCompleted') }}</div>
        <div class="stat-value" style="color: var(--primary-100);">{{ statistics.completed }}</div>
      </div>
    </div>

    <div class="table-wrapper">
      <div class="table-container">
      <el-table :data="tableData" style="width: 100%" v-loading="loading"
        :header-cell-style="{ background: '#e6f5f5', color: 'var(--text-200)', fontWeight: '600' }">
        <el-table-column :label="$t('taskOverview.name')" width="250" align="center">
          <template #default="{ row }">
            <el-tooltip :content="row.name" placement="top" :show-after="500" :teleported="false">
              <div class="ellipsis-text clickable-name" @click="goToDetail(row)">
                {{ row.name }}
              </div>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column :label="$t('taskOverview.testCases')" width="80" align="center">
          <template #default="{ row }">
            {{ row.total_testcases || 0 }}
          </template>
        </el-table-column>
        <el-table-column :label="$t('taskOverview.progress')" width="100" align="center">
          <template #default="{ row }">
            <span style="font-size: 14px; font-weight: 500;" :style="{ color: getProgressColor(row) }">
              {{ row.total_testcases > 0 ? (row.executed_pct || 0).toFixed(2) : '0.00' }}%
            </span>
          </template>
        </el-table-column>
        <el-table-column :label="$t('execution.passRate')" width="100" align="center">
          <template #default="{ row }">
            <span style="font-size: 14px; font-weight: 500;" :style="{ color: getPassRateColor(row) }">
              {{ row.pass_rate ? row.pass_rate.toFixed(2) : '0.00' }}%
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="status" :label="$t('common.status')" width="90" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.status === 'PENDING'" type="info" size="small">{{ $t('taskOverview.statusPending') }}</el-tag>
            <el-tag v-else-if="row.status === 'IN_PROGRESS'" type="warning" size="small">{{ $t('taskOverview.statusInProgress') }}</el-tag>
            <el-tag v-else-if="row.status === 'COMPLETED'" type="success" size="small">{{ $t('taskOverview.statusCompleted') }}</el-tag>
            <el-tag v-else type="info" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="$t('taskOverview.executionPeriod')" width="150" align="center">
          <template #default="{ row }">
            <el-tooltip
              :content="row.execution_period_start && row.execution_period_end ? row.execution_period_start + ' ~ ' + row.execution_period_end : '-'"
              placement="top" effect="dark" :show-after="500">
              <span style="display: block; text-align: center; width: 100%;">
                {{ row.execution_period_start && row.execution_period_end ? row.execution_period_start + ' ~ ' + row.execution_period_end : '-' }}
              </span>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column :label="$t('common.operation')" width="180" align="center" fixed="right">
          <template #default="{ row }">
            <div style="display: flex; align-items: center; justify-content: center; gap: 8px;">
              <el-button
                v-if="canEdit(row)"
                link
                type="primary"
                @click="handleEdit(row)"
              >
                {{ $t('common.edit') }}
              </el-button>
              <el-button
                v-if="canDelete(row)"
                link
                type="danger"
                @click="handleDelete(row)"
              >
                {{ $t('common.delete') }}
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
      </div>
    </div>

    <div class="pagination-container">
      <el-pagination v-model:current-page="page" v-model:page-size="size" :total="total"
        :page-sizes="[10, 20, 50]" layout="total, sizes, prev, pager, next, jumper"
        @current-change="loadData" @size-change="loadData" />
    </div>

    <el-dialog v-model="dialogVisible" :title="isEdit ? $t('taskOverview.edit') : $t('taskOverview.create')"
      width="700px" :close-on-click-modal="false" :before-close="handleDialogClose">
      <el-form :model="form" label-width="100px" label-position="top">
        <el-form-item :label="$t('taskOverview.name')" required>
          <el-input v-model="form.name" :placeholder="$t('taskOverview.inputName')" maxlength="255" />
        </el-form-item>
        <el-form-item :label="$t('taskOverview.description')">
          <el-input v-model="form.description" type="textarea" :rows="3" :placeholder="$t('taskOverview.inputDescription')" />
        </el-form-item>
        <el-form-item :label="$t('taskOverview.selectPlans')">
          <el-select
            v-model="form.planIds"
            :placeholder="$t('taskOverview.selectPlansPlaceholder')"
            multiple
            filterable
            remote
            :remote-method="handlePlanSearch"
            :loading="planSearchLoading"
            style="width: 100%"
            @focus="loadPlanOptions"
          >
            <el-option
              v-for="plan in planOptions"
              :key="plan.id"
              :label="plan.name"
              :value="plan.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('taskOverview.viewers')">
          <el-select
            ref="viewerSelectRef"
            v-model="form.viewerIds"
            :placeholder="$t('taskOverview.selectViewers')"
            multiple
            filterable
            remote
            :remote-method="handleViewerSearch"
            :loading="viewerSearchLoading"
            style="width: 100%"
            @focus="loadViewerOptions"
            @change="handleViewerChange"
          >
            <el-option
              v-for="member in viewerOptions"
              :key="member.id"
              :label="member.username"
              :value="member.id"
            />
          </el-select>
          <div style="margin-top: 8px; color: var(--text-200); font-size: 12px;">
            {{ $t('taskOverview.viewersSelected', { count: form.viewerIds.length }) }}
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          {{ $t('common.confirm') }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { useTeam } from '../../composables/useTeam'
import { useUserRole } from '../../composables/useUserRole'
import { getTaskOverviews, createTaskOverview, updateTaskOverview, deleteTaskOverview } from '../../api/taskOverview'
import { getTestPlans } from '../../api/testplan'
import { getAvailableMembersForSelection } from '../../api/team'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'

const { t } = useI18n()
const router = useRouter()
const { currentTeam } = useTeam()
const { hasButton } = useUserRole()

const tableData = ref([])
const loading = ref(false)
const page = ref(1)
const size = ref(20)
const total = ref(0)
const searchKeyword = ref('')
const statusFilter = ref(null)
const dialogVisible = ref(false)
const isEdit = ref(false)
const editId = ref(null)
const submitting = ref(false)

const form = reactive({
  name: '',
  description: '',
  planIds: [],
  viewerIds: []
})

const planOptions = ref([])
const planSearchLoading = ref(false)
const viewerOptions = ref([])
const viewerSearchLoading = ref(false)
const viewerSelectRef = ref(null)


const statistics = computed(() => {
  const items = allFetchedData.value
  const totalCount = items.length
  const pending = items.filter(r => r.status === 'PENDING').length
  const inProgress = items.filter(r => r.status === 'IN_PROGRESS').length
  const completed = items.filter(r => r.status === 'COMPLETED').length
  return { total: totalCount, pending, inProgress, completed }
})

const formatDate = (date) => {
  if (!date) return '-'
  return new Date(date).toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' })
}

const getProgressColor = (row) => {
  const pct = row.executed_pct || 0
  if (pct >= 90) return '#67c23a'
  if (pct >= 50) return '#409eff'
  return '#e6a23c'
}

const getPassRateColor = (row) => {
  const rate = row.pass_rate || 0
  if (rate >= 90) return '#67c23a'
  if (rate >= 70) return '#e6a23c'
  return '#f56c6c'
}

const currentUser = computed(() => {
  const stored = localStorage.getItem('user')
  if (stored) {
    try { return JSON.parse(stored) } catch { return { id: null } }
  }
  return { id: null }
})

const canEdit = (row) => {
  return row.creator_id === currentUser.value.id
}

const canDelete = (row) => {
  return row.creator_id === currentUser.value.id
}

watch(() => currentTeam.value?.id, () => {
  page.value = 1
  loadData()
})

onMounted(() => {
  if (currentTeam.value?.id) loadData()
})

const handleSearch = () => {
  page.value = 1
  loadData()
}

const filterByStatus = (status) => {
  statusFilter.value = status
  page.value = 1
  loadData()
}

const allFetchedData = ref([])

const loadData = async () => {
  if (!currentTeam.value?.id) return
  loading.value = true
  try {
    const params = { team_id: currentTeam.value.id }
    if (searchKeyword.value) params.search = searchKeyword.value
    if (statusFilter.value) {
      params.size = 1000
    } else {
      params.page = page.value
      params.size = size.value
    }
    const res = await getTaskOverviews(params)
    if (res.code === 200) {
      const allItems = res.data.items || []
      allFetchedData.value = allItems
      if (statusFilter.value) {
        const filtered = allItems.filter(r => r.status === statusFilter.value)
        total.value = filtered.length
        const start = (page.value - 1) * size.value
        tableData.value = filtered.slice(start, start + size.value)
      } else {
        tableData.value = allItems
        total.value = res.data.total || 0
      }
    }
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const resetForm = () => {
  form.name = ''
  form.description = ''
  form.planIds = []
  form.viewerIds = []
  planOptions.value = []
  viewerOptions.value = []
}

const handleCreate = () => {
  isEdit.value = false
  editId.value = null
  resetForm()
  loadPlanOptions()
  loadViewerOptions()
  dialogVisible.value = true
}

const handleEdit = async (row) => {
  isEdit.value = true
  editId.value = row.id
  form.name = row.name
  form.description = row.description || ''
  form.planIds = [...(row.plan_ids || [])]
  form.viewerIds = [...(row.viewer_ids || [])]

  if (row.plan_ids && row.plan_ids.length > 0) {
    const res = await getTestPlans({ team_id: currentTeam.value.id, size: 200 })
    if (res.code === 200) {
      const allPlans = res.data?.items || res.data?.records || []
      planOptions.value = allPlans.filter(p => row.plan_ids.includes(p.id))
    }
  }
  loadViewerOptions()
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!form.name.trim()) {
    ElMessage.warning(t('taskOverview.inputName'))
    return
  }

  submitting.value = true
  try {
    const data = {
      name: form.name.trim(),
      description: form.description.trim() || undefined,
      plan_ids: form.planIds,
      viewer_ids: form.viewerIds,
      team_id: currentTeam.value.id
    }
    if (isEdit.value) {
      const res = await updateTaskOverview(editId.value, data)
      if (res.code === 200) {
        ElMessage.success(t('taskOverview.updateSuccess'))
      }
    } else {
      const res = await createTaskOverview(data)
      if (res.code === 200) {
        ElMessage.success(t('taskOverview.createSuccess'))
      }
    }
    dialogVisible.value = false
    loadData()
  } catch (e) {
    console.error(e)
  } finally {
    submitting.value = false
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(t('taskOverview.deleteConfirm'), t('common.confirm'), {
      type: 'warning',
      confirmButtonText: t('common.confirm'),
      cancelButtonText: t('common.cancel')
    })
    const res = await deleteTaskOverview(row.id)
    if (res.code === 200) {
      ElMessage.success(t('taskOverview.deleteSuccess'))
      loadData()
    }
  } catch (e) {
    if (e !== 'cancel') console.error(e)
  }
}

const handleDialogClose = () => {
  dialogVisible.value = false
}

const goToDetail = (row) => {
  router.push(`/task-overviews/${row.id}`)
}

const loadPlanOptions = async () => {
  if (!currentTeam.value?.id) return
  planSearchLoading.value = true
  try {
    const res = await getTestPlans({ team_id: currentTeam.value.id, size: 200 })
    if (res.code === 200) {
      const plans = res.data?.items || res.data?.records || []
      if (!isEdit.value) {
        planOptions.value = plans
      }
    }
  } catch (e) {
    console.error(e)
  } finally {
    planSearchLoading.value = false
  }
}

const handlePlanSearch = async (query) => {
  if (!currentTeam.value?.id) return
  planSearchLoading.value = true
  try {
    const res = await getTestPlans({
      team_id: currentTeam.value.id,
      search: query || undefined,
      size: 200
    })
    if (res.code === 200) {
      planOptions.value = res.data?.items || res.data?.records || []
    }
  } catch (e) {
    console.error(e)
  } finally {
    planSearchLoading.value = false
  }
}

const loadViewerOptions = async () => {
  if (!currentTeam.value?.id) return
  viewerSearchLoading.value = true
  try {
    const res = await getAvailableMembersForSelection(currentTeam.value.id, 'viewer')
    if (res.code === 200) {
      viewerOptions.value = res.data || []
    }
  } catch (e) {
    console.error(e)
  } finally {
    viewerSearchLoading.value = false
  }
}

const handleViewerChange = () => {
  if (viewerSelectRef.value) {
    viewerSelectRef.value.blur()
  }
}

const handleViewerSearch = async (query) => {
  if (!currentTeam.value?.id) return
  if (!query || !query.trim()) {
    await loadViewerOptions()
    return
  }
  viewerSearchLoading.value = true
  try {
    const res = await getAvailableMembersForSelection(currentTeam.value.id, 'viewer', query.trim())
    if (res.code === 200) {
      viewerOptions.value = res.data || []
    }
  } catch (e) {
    console.error(e)
  } finally {
    viewerSearchLoading.value = false
  }
}
</script>

<style scoped>
.task-overview-container {
  padding: 0;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 20px;
  border-bottom: 1px solid #e2e8f0;
}

.header-left {
  display: flex;
  gap: 12px;
  align-items: center;
}

.header-right {
  display: flex;
  gap: 12px;
  align-items: center;
}

.header-right :deep(.el-input) {
  height: 32px;
}

.header-right :deep(.el-input__wrapper) {
  height: 32px;
  box-sizing: border-box;
}

.stats-cards {
  display: flex;
  gap: 10px;
  padding: 10px 20px;
  flex-wrap: wrap;
  background: var(--demo-bg-card, #ffffff);
  border-bottom: 1px solid var(--demo-border-light, #f1f5f9);
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: var(--demo-bg, #f8fafc);
  border-radius: 6px;
  min-width: 100px;
  transition: all 0.15s;
  cursor: pointer;
  border: 1px solid transparent;
}

.stat-card:hover {
  background: var(--demo-border-light, #f1f5f9);
  border-color: var(--demo-border, #e2e8f0);
}

.stat-card.active {
  border-color: var(--demo-primary, #4f46e5);
  background: var(--demo-primary-light, #eef2ff);
}

.stat-label {
  font-size: 12px;
  color: var(--demo-text-muted, #64748b);
  white-space: nowrap;
  font-weight: 500;
}

.stat-value {
  font-size: 15px;
  font-weight: 700;
  color: var(--demo-text-primary, #0f172a);
}

.table-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.table-container {
  flex: 1;
  overflow: auto;
}

.ellipsis-text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  text-align: center !important;
  width: 100% !important;
}

.clickable-name {
  cursor: pointer;
  font-weight: 500;
  color: var(--el-color-primary);
}

.clickable-name:hover {
  color: var(--el-color-primary);
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
  padding: 8px 0;
}
</style>
