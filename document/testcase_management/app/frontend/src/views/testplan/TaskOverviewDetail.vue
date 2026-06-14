<template>
  <div class="overview-detail-container">
    <div class="detail-header">
      <el-button @click="goBack">
        <el-icon><ArrowLeft /></el-icon>
        {{ $t('common.back') }}
      </el-button>
      <h2 style="margin: 0 0 0 20px;">{{ overview.name }}</h2>

      <div style="flex: 1"></div>
      <el-button
        v-if="canEdit"
        type="primary"
        @click="showEditDialog"
      >
        <el-icon><Edit /></el-icon>
        {{ $t('common.edit') }}
      </el-button>
    </div>

    <div class="info-section">
      <div class="section-title">{{ $t('taskOverview.basicInfo') }}</div>
      <div class="info-grid">
        <div class="info-item">
          <span class="info-label">{{ $t('taskOverview.name') }}:</span>
          <span class="info-value">{{ overview.name }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">{{ $t('common.status') }}:</span>
          <el-tag v-if="overview.status === 'PENDING'" type="info" size="small">{{ $t('taskOverview.statusPending') }}</el-tag>
          <el-tag v-else-if="overview.status === 'IN_PROGRESS'" type="warning" size="small">{{ $t('taskOverview.statusInProgress') }}</el-tag>
          <el-tag v-else-if="overview.status === 'COMPLETED'" type="success" size="small">{{ $t('taskOverview.statusCompleted') }}</el-tag>
        </div>
        <div class="info-item">
          <span class="info-label">{{ $t('taskOverview.creator') }}:</span>
          <span class="info-value">{{ overview.creator_name || '-' }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">{{ $t('taskOverview.viewers') }}:</span>
          <span class="info-value">{{ overview.viewer_names?.join(', ') || '-' }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">{{ $t('common.createdAt') }}:</span>
          <span class="info-value">{{ formatDate(overview.created_at) }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">{{ $t('common.updatedAt') }}:</span>
          <span class="info-value">{{ formatDate(overview.updated_at) }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">{{ $t('taskOverview.executionPeriod') }}:</span>
          <span class="info-value">
            <span v-if="overview.execution_period_start && overview.execution_period_end">
              {{ overview.execution_period_start }} ~ {{ overview.execution_period_end }}
            </span>
            <span v-else>-</span>
          </span>
        </div>
        <div class="info-item full-width">
          <span class="info-label">{{ $t('taskOverview.description') }}:</span>
          <span class="info-value">{{ overview.description || '-' }}</span>
        </div>
      </div>
    </div>

    <div class="stats-section">
      <div class="section-title">{{ $t('taskOverview.executionStats') }}</div>
      <div class="stats-cards">
        <div class="stat-card">
          <span class="stat-label">{{ $t('taskOverview.totalTestCases') }}</span>
          <span class="stat-value">{{ overview.total_testcases || 0 }}</span>
        </div>
        <div class="stat-card">
          <span class="stat-label">{{ $t('taskOverview.progress') }}</span>
          <span class="stat-value" :style="{ color: executionProgressColor }">
            {{ overview.total_testcases > 0 ? (overview.executed_pct || 0).toFixed(2) : '0.00' }}%
          </span>
        </div>
        <div class="stat-card">
          <span class="stat-label">{{ $t('taskOverview.passRate') }}</span>
          <span class="stat-value" :style="{ color: getPassRateColor }">
            {{ passRate }}%
          </span>
        </div>
        <div class="stat-card">
          <span class="stat-label">{{ $t('taskOverview.notExecuted') }}</span>
          <span class="stat-value" style="color: #909399;">{{ (overview.total_testcases || 0) - (overview.statistics?.executed || 0) }}</span>
        </div>
        <div class="stat-card">
          <span class="stat-label">{{ $t('taskOverview.executed') }}</span>
          <span class="stat-value" style="color: var(--primary-100);">{{ overview.statistics?.executed || 0 }}</span>
        </div>
        <div class="stat-card">
          <span class="stat-label">PASS</span>
          <span class="stat-value" style="color: #67c23a;">{{ overview.statistics?.passed || 0 }}</span>
        </div>
        <div class="stat-card">
          <span class="stat-label">FAIL</span>
          <span class="stat-value" style="color: var(--accent-100);">{{ overview.statistics?.failed || 0 }}</span>
        </div>
        <div class="stat-card">
          <span class="stat-label">BLOCK</span>
          <span class="stat-value" style="color: #e6a23c;">{{ overview.statistics?.blocked || 0 }}</span>
        </div>
        <div class="stat-card">
          <span class="stat-label">NA</span>
          <span class="stat-value" style="color: #909399;">{{ overview.statistics?.na || 0 }}</span>
        </div>
        <div class="stat-card">
          <span class="stat-label">NT</span>
          <span class="stat-value" style="color: #909399;">{{ overview.statistics?.nt || 0 }}</span>
        </div>
      </div>
    </div>

    <div class="plans-section">
      <div class="section-title-row">
        <span class="section-title">{{ $t('taskOverview.associatedPlans') }}</span>
      </div>
      <el-table :data="overview.plans || []" style="width: 100%"
        :header-cell-style="{ background: '#e6f5f5', color: 'var(--text-200)', fontWeight: '600' }">
        <el-table-column :label="$t('taskOverview.planName')" width="250" align="center">
          <template #default="{ row }">
            <el-tooltip :content="row.name" placement="top" :show-after="500">
              <el-link type="primary" :underline="false" class="clickable-name" @click="goToPlan(row)">
                {{ row.name }}
              </el-link>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column :label="$t('taskOverview.testCases')" width="80" align="center">
          <template #default="{ row }">
            {{ row.total_testcases || 0 }}
          </template>
        </el-table-column>
        <el-table-column :label="$t('testplan.progress')" width="100" align="center">
          <template #default="{ row }">
            <span style="font-size: 14px; font-weight: 500;">
              {{ row.total_testcases > 0 ? ((row.executed / row.total_testcases) * 100).toFixed(2) : '0.00' }}%
            </span>
          </template>
        </el-table-column>
        <el-table-column :label="$t('execution.passRate')" width="100" align="center">
          <template #default="{ row }">
            <span style="font-size: 14px; font-weight: 500;" :style="{ color: getPlanPassRateColor(row) }">
              {{ calculatePlanPassRate(row) }}%
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="status" :label="$t('common.status')" width="90" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.status === 'PENDING'" type="info" size="small">{{ $t('testplan.statusPending') }}</el-tag>
            <el-tag v-else-if="row.status === 'IN_PROGRESS'" type="warning" size="small">{{ $t('testplan.statusInProgress') }}</el-tag>
            <el-tag v-else-if="row.status === 'COMPLETED'" type="success" size="small">{{ $t('testplan.statusCompleted') }}</el-tag>
            <el-tag v-else type="info" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="$t('testplan.executionPeriod')" width="150" align="center">
          <template #default="{ row }">
            <el-tooltip
              :content="row.start_time && row.end_time ? row.start_time + ' ~ ' + row.end_time : '-'"
              placement="top" effect="dark" :show-after="500">
              <span style="display: block; text-align: center; width: 100%;">
                {{ getExecutionDays(row) }}
              </span>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column :label="$t('common.operation')" width="100" align="center" v-if="canEdit">
          <template #default="{ row }">
            <el-button link type="danger" size="small" @click="handleRemovePlan(row)">
              {{ $t('taskOverview.removePlan') }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog v-model="editDialogVisible" :title="$t('taskOverview.edit')"
      width="700px" :close-on-click-modal="false">
      <el-form :model="editForm" label-width="100px" label-position="top">
        <el-form-item :label="$t('taskOverview.name')" required>
          <el-input v-model="editForm.name" :placeholder="$t('taskOverview.inputName')" maxlength="255" />
        </el-form-item>
        <el-form-item :label="$t('taskOverview.description')">
          <el-input v-model="editForm.description" type="textarea" :rows="3" :placeholder="$t('taskOverview.inputDescription')" />
        </el-form-item>
        <el-form-item :label="$t('taskOverview.selectPlans')">
          <el-select
            v-model="editForm.planIds"
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
            v-model="editForm.viewerIds"
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
            {{ $t('taskOverview.viewersSelected', { count: editForm.viewerIds.length }) }}
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="submitEdit" :loading="submitting">
          {{ $t('common.confirm') }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useTeam } from '../../composables/useTeam'
import { getTaskOverviewDetail, updateTaskOverview, removePlanFromOverview, addPlansToOverview } from '../../api/taskOverview'
import { getTestPlans } from '../../api/testplan'
import { getAvailableMembersForSelection } from '../../api/team'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Edit } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const { t } = useI18n()
const { currentTeam } = useTeam()

const overview = ref({})
const loading = ref(false)
const editDialogVisible = ref(false)
const submitting = ref(false)
const planOptions = ref([])
const planSearchLoading = ref(false)
const viewerOptions = ref([])
const viewerSearchLoading = ref(false)
const viewerSelectRef = ref(null)


const editForm = reactive({
  name: '',
  description: '',
  planIds: [],
  viewerIds: []
})

const currentUser = computed(() => {
  const stored = localStorage.getItem('user')
  if (stored) {
    try { return JSON.parse(stored) } catch { return { id: null } }
  }
  return { id: null }
})

const canEdit = computed(() => {
  return overview.value.creator_id === currentUser.value.id
})

const passRate = computed(() => {
  const total = overview.value.total_testcases || 0
  const passed = overview.value.statistics?.passed || 0
  const na = overview.value.statistics?.na || 0
  const assist = overview.value.statistics?.assist || 0
  const valid = total - na - assist
  if (valid <= 0) return '0.00'
  return ((passed / valid) * 100).toFixed(2)
})

const getPassRateColor = computed(() => {
  const rate = parseFloat(passRate.value)
  if (rate >= 90) return '#67c23a'
  if (rate >= 70) return '#e6a23c'
  return '#f56c6c'
})

const executionProgressColor = computed(() => {
  const total = overview.value.total_testcases || 0
  if (total === 0) return '#909399'
  const pct = overview.value.executed_pct || 0
  if (pct >= 90) return '#67c23a'
  if (pct >= 50) return '#409eff'
  return '#e6a23c'
})

onMounted(() => {
  loadDetail()
})

const loadDetail = async () => {
  const id = route.params.id
  if (!id) return
  loading.value = true
  try {
    const res = await getTaskOverviewDetail(id)
    if (res.code === 200) {
      overview.value = res.data
    }
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const goBack = () => {
  router.push('/testplans')
}

const goToPlan = (plan) => {
  router.push(`/testplans/${plan.id}?from=task-overview`)
}

const formatDate = (date) => {
  if (!date) return '-'
  return new Date(date).toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' })
}

const showEditDialog = () => {
  editForm.name = overview.value.name
  editForm.description = overview.value.description || ''
  editForm.planIds = [...(overview.value.plan_ids || [])]
  editForm.viewerIds = [...(overview.value.viewer_ids || [])]
  loadPlanOptions()
  loadViewerOptions()
  editDialogVisible.value = true
}

const submitEdit = async () => {
  if (!editForm.name.trim()) {
    ElMessage.warning(t('taskOverview.inputName'))
    return
  }
  submitting.value = true
  try {
    const data = {
      name: editForm.name.trim(),
      description: editForm.description.trim() || undefined,
      plan_ids: editForm.planIds,
      viewer_ids: editForm.viewerIds
    }
    const res = await updateTaskOverview(route.params.id, data)
    if (res.code === 200) {
      ElMessage.success(t('taskOverview.updateSuccess'))
      editDialogVisible.value = false
      await loadDetail()
    }
  } catch (e) {
    console.error(e)
  } finally {
    submitting.value = false
  }
}

const calculatePlanPassRate = (row) => {
  const total = row.total_testcases || 0
  const passed = row.passed || 0
  const na = row.na || 0
  const valid = total - na
  if (valid <= 0) return '0.00'
  return ((passed / valid) * 100).toFixed(2)
}

const getPlanPassRateColor = (row) => {
  const rate = parseFloat(calculatePlanPassRate(row))
  if (rate >= 90) return '#67c23a'
  if (rate >= 70) return '#e6a23c'
  return '#f56c6c'
}

const getExecutionDays = (row) => {
  if (!row.start_time || !row.end_time) return '-'
  return `${row.start_time} ~ ${row.end_time}`
}

const handleRemovePlan = async (plan) => {
  try {
    await ElMessageBox.confirm(
      t('taskOverview.confirmRemovePlan', { name: plan.name }),
      t('common.confirm'),
      { type: 'warning', confirmButtonText: t('common.confirm'), cancelButtonText: t('common.cancel') }
    )
    const res = await removePlanFromOverview(route.params.id, plan.id)
    if (res.code === 200) {
      ElMessage.success(t('taskOverview.removePlanSuccess'))
      await loadDetail()
    }
  } catch (e) {
    if (e !== 'cancel') console.error(e)
  }
}

const loadPlanOptions = async () => {
  if (!currentTeam.value?.id) return
  planSearchLoading.value = true
  try {
    const res = await getTestPlans({ team_id: currentTeam.value.id, size: 200 })
    if (res.code === 200) {
      planOptions.value = res.data?.items || res.data?.records || []
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

const handleViewerChange = () => {
  if (viewerSelectRef.value) {
    viewerSelectRef.value.blur()
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
.overview-detail-container {
  padding: 20px;
}

.detail-header {
  display: flex;
  align-items: center;
  margin-bottom: 24px;
}

.info-section {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.section-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.info-item {
  display: flex;
  align-items: flex-start;
}

.info-item.full-width {
  grid-column: 1 / -1;
}

.info-label {
  font-size: 13px;
  color: #64748b;
  min-width: 100px;
  flex-shrink: 0;
}

.info-value {
  font-size: 13px;
  color: #1e293b;
}

.stats-section {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(10, 1fr);
  gap: 8px;
}

@media (max-width: 1400px) {
  .stats-cards {
    grid-template-columns: repeat(5, 1fr);
  }
}

@media (max-width: 900px) {
  .stats-cards {
    grid-template-columns: repeat(3, 1fr);
  }
}

.stat-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 10px 6px;
  background: #f8fafc;
  border-radius: 8px;
}

.stat-label {
  font-size: 11px;
  color: #64748b;
  margin-bottom: 6px;
  white-space: nowrap;
}

.stat-value {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
}

.plans-section {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
</style>
