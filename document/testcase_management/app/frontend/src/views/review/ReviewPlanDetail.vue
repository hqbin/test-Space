<template>
  <div class="review-detail-container">
    <!-- 头部：返回按钮和标题 -->
    <div class="detail-header">
      <el-button @click="goBack">
        <el-icon><ArrowLeft /></el-icon>
        {{ $t('common.back') }}
      </el-button>
      <h2 style="margin: 0 0 0 20px;">{{ planDetail.name }}</h2>
      <div style="flex: 1"></div>
      <el-button 
        type="primary" 
        @click="showEditDialog" 
        v-if="canEdit && planDetail.status !== 'COMPLETED'"
      >
        <el-icon><Edit /></el-icon>
        {{ $t('common.edit') }}
      </el-button>
    </div>

    <!-- 基本信息 -->
    <div class="info-section">
      <div class="section-title">{{ $t('review.basicInfo') }}</div>
      <div class="info-grid">
        <div class="info-item">
          <span class="info-label">{{ $t('review.planName') }}:</span>
          <span class="info-value">{{ planDetail.name }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">{{ $t('review.planStatus') }}:</span>
          <el-tag :type="getStatusType(planDetail.status)" size="small">
            {{ getStatusText(planDetail.status) }}
          </el-tag>
        </div>
        <div class="info-item">
          <span class="info-label">{{ $t('review.reviewers') }}:</span>
          <span class="info-value">{{ planDetail.reviewer_names && planDetail.reviewer_names.length > 0 ? planDetail.reviewer_names.join(', ') : '-' }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">{{ $t('review.creator') }}:</span>
          <span class="info-value">{{ planDetail.creator_name }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">{{ $t('common.createdAt') }}:</span>
          <span class="info-value">{{ planDetail.created_at ? formatDate(planDetail.created_at) : '-' }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">{{ $t('review.reviewPeriod') }}:</span>
          <span class="info-value">
            <span v-if="planDetail.start_time && planDetail.end_time">
              {{ formatDate(planDetail.start_time) }} {{ $t('review.to') }} {{ formatDate(planDetail.end_time) }}
            </span>
            <span v-else>-</span>
          </span>
        </div>
        <div class="info-item full-width">
          <span class="info-label">{{ $t('review.description') }}:</span>
          <span class="info-value">{{ planDetail.description || '-' }}</span>
        </div>
      </div>
    </div>

    <!-- 评审进度统计 -->
    <div class="stats-section">
      <div class="section-title">{{ $t('review.statsTitle') }}</div>
      <div class="stats-cards">
        <div 
          class="stat-card clickable"
          :class="{ 'active': statusFilter === null }"
          @click="filterByStatus(null)"
        >
          <span class="stat-label">{{ $t('review.totalTestcases') }}</span>
          <span class="stat-value">{{ planDetail.total_testcases || 0 }}</span>
        </div>
        <div
          class="stat-card clickable"
          :class="{ 'active': statusFilter === 'PENDING' }"
          @click="filterByStatus('PENDING')"
        >
          <span class="stat-label">{{ $t('review.pendingReview') }}</span>
          <span class="stat-value" style="color: #909399;">{{ (planDetail.total_testcases || 0) - (planDetail.executed_testcases || 0) }}</span>
        </div>
        <div
          class="stat-card clickable"
          :class="{ 'active': statusFilter === 'REVIEWED' }"
          @click="filterByStatus('REVIEWED')"
        >
          <span class="stat-label">{{ $t('review.reviewed') }}</span>
          <span class="stat-value" style="color: #409eff;">{{ planDetail.executed_testcases || 0 }}</span>
        </div>
        <div
          class="stat-card clickable"
          :class="{ 'active': statusFilter === 'APPROVED' }"
          @click="filterByStatus('APPROVED')"
        >
          <span class="stat-label">{{ $t('review.passed') }}</span>
          <span class="stat-value" style="color: #67c23a;">{{ planDetail.executed_passed_testcases || 0 }}</span>
        </div>
        <div
          class="stat-card clickable"
          :class="{ 'active': statusFilter === 'REJECTED' }"
          @click="filterByStatus('REJECTED')"
        >
          <span class="stat-label">{{ $t('review.rejected') }}</span>
          <span class="stat-value" style="color: #f56c6c;">{{ planDetail.executed_rejected_testcases || 0 }}</span>
        </div>
        <div
          class="stat-card clickable"
          :class="{ 'active': statusFilter === 'DEPRECATED' }"
          @click="filterByStatus('DEPRECATED')"
        >
          <span class="stat-label">{{ $t('review.deprecated') }}</span>
          <span class="stat-value" style="color: #909399;">{{ planDetail.executed_deprecated_testcases || 0 }}</span>
        </div>
      </div>
    </div>

    <!-- 关联用例列表 -->
    <div class="testcase-list-section" style="margin-top: 20px">
      <div class="list-header sticky-toolbar">
        <el-button 
          v-if="canEdit && planDetail.status !== 'COMPLETED'" 
          type="primary" 
          @click="showAddTestCaseDialog"
        >
          <el-icon><Plus /></el-icon>
          {{ $t('review.addTestcase') }}
        </el-button>
        <div style="flex: 1"></div>
        <el-input
          v-model="searchKeyword"
          :placeholder="$t('review.searchCasePlaceholder')"
          clearable
          style="width: 300px;"
          @keyup.enter="loadTestCases"
        >
          <template #suffix>
            <el-icon class="el-input__icon" style="cursor: pointer;" @click="loadTestCases">
              <Search />
            </el-icon>
          </template>
        </el-input>
      </div>

      <div class="table-container" ref="tableWrapperRef">
        <el-table
          ref="tableRef"
          :data="filteredTestcaseList"
          style="width: 100%"
          border
          :header-cell-style="{ background: '#f8fafc', color: '#64748b', fontWeight: '500', fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.05em' }"
          class="sticky-header-table"
        >
<el-table-column :label="$t('review.operation')" width="60" align="center" v-if="canEdit && planDetail.status !== 'COMPLETED'">
              <template #default="{ row }">
                <el-icon 
                  v-if="row.review_status === 'PENDING'"
                  class="remove-icon"
                  :class="{ 'is-loading': removing }"
                  @click="removeTestCase(row)"
                >
                  <Close />
                </el-icon>
              </template>
            </el-table-column>
            <el-table-column prop="case_number" :label="$t('review.caseNumber')" width="230" align="center" resizable :show-overflow-tooltip="{ showAfter: 500 }">
              <template #default="{ row }">
                <span class="clickable-text" @click="viewTestCaseDetail(row)">{{ row.case_number }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="name" :label="$t('review.caseTitle')" min-width="200" align="left" resizable>
              <template #default="{ row }">
                <el-tooltip placement="top" :show-after="500" :disabled="!row.name">
                  <template #content>
                    <div style="max-width: 500px; white-space: pre-wrap; word-break: break-word;">{{ row.name }}</div>
                  </template>
                  <span class="clickable-text" @click="viewTestCaseDetail(row)">{{ row.name }}</span>
                </el-tooltip>
              </template>
            </el-table-column>
            <el-table-column prop="precondition" :label="$t('review.precondition')" min-width="200" align="left" resizable>
              <template #default="{ row }">
                <el-tooltip placement="top" :show-after="500" :disabled="!row.precondition">
                  <template #content>
                    <div style="max-width: 500px; white-space: pre-wrap; word-break: break-word;">{{ row.precondition }}</div>
                  </template>
                  <div class="single-line-ellipsis">{{ row.precondition || '-' }}</div>
                </el-tooltip>
              </template>
            </el-table-column>
            <el-table-column prop="steps" :label="$t('review.testSteps')" min-width="250" align="left" resizable>
              <template #default="{ row }">
                <el-tooltip placement="top" :show-after="500" raw-content>
                  <template #content>
                    <div style="max-width: 500px;">
                      <div v-for="(step, stepIndex) in parseSteps(row.steps)" :key="stepIndex" style="display: flex; padding: 4px 0; line-height: 1.6;">
                        <span style="color: #818cf8; font-weight: 500; min-width: 30px;">{{ stepIndex + 1 }}.</span>
                        <span style="word-break: break-word;">{{ step }}</span>
                      </div>
                    </div>
                  </template>
                  <div class="single-line-ellipsis">
                    {{ parseSteps(row.steps).map((s, i) => `${i + 1}. ${s}`).join(' ') || '-' }}
                  </div>
                </el-tooltip>
              </template>
            </el-table-column>
            <el-table-column :label="$t('review.expectedResult')" min-width="250" align="left" resizable>
              <template #default="{ row }">
                <el-tooltip placement="top" :show-after="500" raw-content>
                  <template #content>
                    <div style="max-width: 500px;">
                      <div v-for="(result, resultIndex) in parseExpected(row.expected_result)" :key="resultIndex" style="display: flex; padding: 4px 0; line-height: 1.6;">
                        <span style="color: #818cf8; font-weight: 500; min-width: 30px;">{{ resultIndex + 1 }}.</span>
                        <span style="word-break: break-word;">{{ result }}</span>
                      </div>
                    </div>
                  </template>
                  <div class="single-line-ellipsis">
                    {{ parseExpected(row.expected_result).map((r, i) => `${i + 1}. ${r}`).join(' ') || '-' }}
                  </div>
                </el-tooltip>
              </template>
            </el-table-column>
            <el-table-column prop="level" :label="$t('review.caseLevel')" width="140" align="center" resizable />
            <el-table-column :label="$t('review.reviewStatus')" width="170" align="center">
              <template #default="{ row }">
                <!-- 暂存与正式同时存在时一并展示 -->
                <template v-if="row.pending_review_result && row.review_result">
                  <el-tag
                    :type="getResultTagType(row.pending_review_result)"
                    effect="plain"
                    size="small"
                    style="border-style: dashed; margin-right: 4px;"
                  >
                    {{ getResultText(row.pending_review_result) }}
                  </el-tag>
                  <el-tag :type="getResultTagType(row.review_result)" size="small">
                    {{ getResultText(row.review_result) }}
                  </el-tag>
                </template>
                <!-- 仅暂存：虚线边框 -->
                <template v-else-if="row.pending_review_result">
                  <el-tag
                    :type="getResultTagType(row.pending_review_result)"
                    effect="plain"
                    size="small"
                    style="border-style: dashed;"
                  >
                    {{ getResultText(row.pending_review_result) }}
                  </el-tag>
                </template>
                <!-- 仅正式：按官方结果展示 -->
                <template v-else>
                  <el-tag v-if="row.review_result" :type="getResultTagType(row.review_result)" size="small">{{ getResultText(row.review_result) }}</el-tag>
                  <el-tag v-else type="warning" size="small">{{ $t('review.pendingReview') }}</el-tag>
                </template>
              </template>
            </el-table-column>
            <el-table-column :label="$t('review.reviewComment')" min-width="200" align="left" resizable :show-overflow-tooltip="{ showAfter: 500 }">
              <template #default="{ row }">
                {{ row.pending_review_comment || row.review_comment || '-' }}
              </template>
            </el-table-column>
          </el-table>
        </div>
        
        <!-- 分页器 -->
        <div class="pagination-container">
          <el-pagination
            v-model:current-page="pagination.page"
            v-model:page-size="pagination.size"
            :page-sizes="[10, 20, 50, 100]"
            :total="pagination.total"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleTestCasesPageChange"
            @current-change="handleTestCasesPageChange"
            background
          />
        </div>
    </div>

    <!-- 编辑评审计划对话框 -->
<el-dialog
      v-model="editDialogVisible"
      :title="$t('review.editPlan')"
      width="780px"
    >
      <el-form
        ref="editFormRef"
        :model="editForm"
        label-width="100px"
      >
        <el-form-item :label="$t('review.planName')" prop="name" :rules="[{ required: true, message: t('review.planNamePlaceholder'), trigger: 'blur' }]">
          <el-input v-model="editForm.name" :placeholder="t('review.planNamePlaceholder')" />
        </el-form-item>
        
        <el-form-item :label="$t('review.description')">
          <el-input
            v-model="editForm.description"
            type="textarea"
            :rows="3"
            :placeholder="t('review.descriptionPlaceholder')"
          />
        </el-form-item>
        
        <el-form-item :label="$t('review.reviewers')" prop="reviewer_ids">
          <el-select
            v-model="editForm.reviewer_ids"
            multiple
            :placeholder="t('review.selectReviewer')"
            style="width: 100%"
            filterable
          >
            <el-option
              v-for="member in projectMembers"
              :key="member.id"
              :label="member.username"
              :value="member.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item :label="$t('review.reviewPeriod')">
          <el-date-picker
            v-model="reviewTimeRange"
            type="datetimerange"
            :range-separator="t('review.to')"
            :start-placeholder="t('review.startDate')"
            :end-placeholder="t('review.endDate')"
            style="width: 100%"
            format="YYYY-MM-DD HH:mm"
            value-format="YYYY-MM-DD HH:mm:ss"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="editDialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="submitEdit" :loading="submitting">{{ $t('common.save') }}</el-button>
      </template>
    </el-dialog>

    <!-- 添加用例对话框 -->
<el-dialog
      v-model="addTestCaseDialogVisible"
      :title="$t('review.relatedCases')"
      width="95%"
      top="3vh"
      append-to-body
      :close-on-click-modal="false"
    >
      <div class="testcase-select-container">
        <!-- 左侧模块树 -->
        <div class="module-sidebar">
          <!-- 用例库选择器 -->
          <div class="project-filter-section">
            <div class="section-header">
              <span>{{ $t('common.caseLibrary') }}</span>
            </div>
            <div class="project-filter-content">
              <ProjectSelector
                v-model="selectedProjectIdList"
                :project-list="teamProjectList"
                @change="handleProjectSelectorChange"
              />
            </div>
          </div>
          
          <div class="module-header">
            <span>{{ $t('review.belongModule') }}</span>
          </div>
          <div class="module-list">
            <div 
              class="module-item" 
              :class="{ active: testcaseFilter.module === '' }"
              @click="handleModuleClick('')"
            >
              <span class="module-name">{{ $t('common.all') }}</span>
              <span class="module-count">{{ testcasePagination.total }}</span>
            </div>
            <div 
              v-for="item in flatModuleTree" 
              :key="item.path"
              class="module-item"
              :class="{ 
                'main-module': item.depth === 0,
                'sub-module': item.depth > 0,
                active: testcaseFilter.module === item.path
              }"
              :style="item.depth > 0 ? { paddingLeft: (12 + item.depth * 16) + 'px' } : {}"
            >
              <el-icon 
                v-if="item.children && item.children.length > 0"
                class="expand-icon"
                @click.stop="toggleModule(item.path)"
              >
                <ArrowRight v-if="!item.expanded" />
                <ArrowDown v-else />
              </el-icon>
              <div class="module-content" @click="handleModuleClick(item.path)">
                <span class="module-name">{{ item.name }}<span v-if="item.tag" style="color: #409eff; margin-left: 2px;">({{ item.tag }})</span></span>
                <span class="module-count" v-if="item.count">{{ item.count }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 右侧用例列表 -->
        <div class="testcase-content">
          <div class="testcase-filter">
            <el-input
              v-model="testcaseSearchKeyword"
              :placeholder="$t('review.searchCasePlaceholder')"
              clearable
              style="width: 300px;"
              @keyup.enter="loadAvailableTestCases"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
            <el-button type="primary" @click="loadAvailableTestCases">
              {{ $t('common.search') }}
            </el-button>
            
            <el-button 
              @click="selectAllCurrentModule"
              :disabled="availableTestCases.length === 0"
              :loading="selectingAll"
            >
              {{ $t('review.selectAllCurrentModule') }}
            </el-button>
            
            <div style="flex: 1"></div>
            
            <el-button 
              type="primary" 
              :disabled="selectedTestCases.length === 0"
              @click="confirmAddTestCases"
            >
              {{ $t('review.linkCases') }}（{{ selectedTestCases.length }}）
            </el-button>
          </div>
          
          <div class="table-wrapper">
            <el-table
              ref="testcaseTableRef"
              :data="availableTestCases"
              style="width: 100%"
              :height="dialogTableHeight"
              border
              :header-cell-style="{ background: '#f8fafc', color: '#64748b', fontWeight: '500', fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.05em' }"
              v-loading="testcaseLoading"
              :element-loading-text="$t('common.loading')"
              @selection-change="handleTestCaseSelectionChange"
            >
              <el-table-column type="selection" width="60" align="center" />
<el-table-column prop="case_number" :label="$t('review.caseNumber')" width="230" align="center" resizable>
                <template #default="scope">
                  <el-tooltip :content="scope.row.case_number" placement="top" :show-after="500">
                    <el-tag type="info" size="small" class="ellipsis-tag">{{ scope.row.case_number }}</el-tag>
                  </el-tooltip>
                </template>
              </el-table-column>
<el-table-column prop="name" :label="$t('review.caseTitle')" min-width="200" align="left" resizable>
                <template #default="scope">
                  <div class="single-line-ellipsis">{{ scope.row.name }}</div>
                </template>
              </el-table-column>
<el-table-column prop="precondition" :label="$t('review.precondition')" min-width="200" align="left" resizable>
                <template #default="scope">
                  <el-tooltip placement="top" :show-after="500" :disabled="!scope.row.precondition">
                    <template #content>
                      <div style="max-width: 500px; white-space: pre-wrap; word-break: break-word;">{{ scope.row.precondition }}</div>
                    </template>
                    <div class="single-line-ellipsis">{{ scope.row.precondition || '-' }}</div>
                  </el-tooltip>
                </template>
              </el-table-column>

<el-table-column prop="steps" :label="$t('review.testSteps')" min-width="250" align="left" resizable>
                <template #default="scope">
                  <el-tooltip placement="top" :show-after="500" raw-content>
                    <template #content>
                      <div style="max-width: 500px;">
                        <div v-for="(step, stepIndex) in parseSteps(scope.row.steps)" :key="stepIndex" style="display: flex; padding: 4px 0; line-height: 1.6;">
                          <span style="color: #818cf8; font-weight: 500; min-width: 30px;">{{ stepIndex + 1 }}.</span>
                          <span style="word-break: break-word;">{{ step }}</span>
                        </div>
                      </div>
                    </template>
                    <div class="single-line-ellipsis">
                      {{ parseSteps(scope.row.steps).map((s, i) => `${i + 1}. ${s}`).join(' ') || '-' }}
                    </div>
                  </el-tooltip>
                </template>
              </el-table-column>
<el-table-column :label="$t('review.expectedResult')" min-width="250" align="left" resizable>
                <template #default="scope">
                  <el-tooltip placement="top" :show-after="500" raw-content>
                    <template #content>
                      <div style="max-width: 500px;">
                        <div v-for="(result, resultIndex) in parseExpected(scope.row.expected_result)" :key="resultIndex" style="display: flex; padding: 4px 0; line-height: 1.6;">
                          <span style="color: #818cf8; font-weight: 500; min-width: 30px;">{{ resultIndex + 1 }}.</span>
                          <span style="word-break: break-word;">{{ result }}</span>
                        </div>
                      </div>
                    </template>
                    <div class="single-line-ellipsis">
                      {{ parseExpected(scope.row.expected_result).map((r, i) => `${i + 1}. ${r}`).join(' ') || '-' }}
                    </div>
                  </el-tooltip>
                </template>
              </el-table-column>
              <el-table-column prop="status" :label="$t('common.status')" width="140" align="center" resizable :show-overflow-tooltip="{ showAfter: 500 }">
                <template #default="scope">
                  <el-tag v-if="scope.row.status === 'REVIEWED'" type="success" size="small">{{ $t('review.reviewed') }}</el-tag>
                  <el-tag v-else-if="scope.row.status === 'PENDING'" type="warning" size="small">{{ $t('review.pendingReview') }}</el-tag>
                  <el-tag v-else-if="scope.row.status === 'REJECTED'" type="danger" size="small">{{ $t('review.rejected') }}</el-tag>
                  <el-tag v-else-if="scope.row.status === 'DEPRECATED'" type="info" size="small">{{ $t('review.deprecated') }}</el-tag>
                  <span v-else>-</span>
                </template>
              </el-table-column>
              <el-table-column prop="level" :label="$t('review.caseLevel')" width="140" align="center" resizable />
              <el-table-column :label="$t('review.creator')" width="120" align="center" resizable :show-overflow-tooltip="{ showAfter: 500 }">
                <template #default="scope">
                  {{ scope.row.creator_name || '-' }}
                </template>
              </el-table-column>
            </el-table>
          </div>
          
          <el-pagination
            v-model:current-page="testcasePagination.page"
            v-model:page-size="testcasePagination.size"
            :page-sizes="[10, 20, 50, 100]"
            :total="testcasePagination.total"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleAvailableTestCasesPageChange"
            @current-change="handleAvailableTestCasesPageChange"
            background
          />
        </div>
      </div>
    </el-dialog>
  </div>
</template>


<script setup>
import { ref, reactive, onMounted, onUnmounted, computed, nextTick, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useScrollToTop } from '../../composables/useScrollToTop'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Search, Edit, Plus, Delete, ArrowRight, ArrowDown, CircleClose, Loading } from '@element-plus/icons-vue'
import { 
  getReviewPlanDetail, 
  getPlanTestCases, 
  updateReviewPlan,
  removeTestCaseFromPlan,
  addTestCasesToPlan,
  getProjectMembers
} from '@/api/reviewPlan'
import { getTestCases, getAllTestCaseIds } from '@/api/testcase'
import { getModuleTree } from '@/api/module'
import { useUserRole } from '@/composables/useUserRole'
import { useTeam } from '@/composables/useTeam'
import ProjectSelector from '../../components/ProjectSelector.vue'
import { useLoadingStore } from '../../stores/loading'
import { useProjectPreference } from '../../composables/useProjectPreference'

const router = useRouter()
const route = useRoute()
const { t } = useI18n()
const { isAdmin } = useUserRole()
const { currentTeam, teamProjects } = useTeam()
const loadingStore = useLoadingStore()

// 用例库选择相关
const { selectedProjectIdList, applyPreference, updateSelection, resetPreference } = useProjectPreference()
const teamProjectList = computed(() => teamProjects.value || [])

// 计算当前选中的用例库ID列表
const currentProjectIds = computed(() => {
  return selectedProjectIdList.value.length > 0 
    ? selectedProjectIdList.value 
    : teamProjectList.value.map(p => p.id)
})

// 处理用例库选择器变化（防抖，防止快速切换导致数据错乱）
let _projectChangeTimer = null
const handleProjectSelectorChange = (ids) => {
  updateSelection(ids)
  testcaseFilter.module = ''
  testcaseFilter.subModule = ''
  testcasePagination.page = 1
  clearTimeout(_projectChangeTimer)
  _projectChangeTimer = setTimeout(() => {
    loadModuleTree()
    loadAvailableTestCases()
  }, 300)
}

const planDetail = ref({})
const testcaseList = ref([])
const loading = ref(false)
const searchKeyword = ref('')
const statusFilter = ref(null)

const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

// 表格容器引用
const tableWrapperRef = ref(null)
const tableRef = ref(null)
const { scrollToTop } = useScrollToTop(tableRef)

const handleTestCasesPageChange = async () => {
  await loadTestCases()
  await nextTick()
  scrollToTop()
}
const handleAvailableTestCasesPageChange = async () => {
  await loadAvailableTestCases()
  await nextTick()
  scrollToTop()
}

// 处理表格滚动同步
const handleTableScroll = (event) => {
  if (!tableWrapperRef.value) return
  
  const scrollLeft = event.target.scrollLeft
  
  // 同步表头和表体的滚动位置
  const headerWrapper = tableWrapperRef.value.querySelector('.el-table__header-wrapper')
  const bodyWrapper = tableWrapperRef.value.querySelector('.el-table__body-wrapper')
  
  if (headerWrapper) {
    headerWrapper.scrollLeft = scrollLeft
  }
  
  if (bodyWrapper) {
    bodyWrapper.scrollLeft = scrollLeft
  }
}

// 监听用例库列表变化，自动应用偏好
watch(teamProjectList, (list) => {
  if (list && list.length > 0) {
    applyPreference(list)
  }
})

onMounted(() => {
  loadPlanDetail()
  loadTestCases()
  
  // 添加滚动事件监听器
  if (tableWrapperRef.value) {
    tableWrapperRef.value.addEventListener('scroll', handleTableScroll)
  }
})

onUnmounted(() => {
  // 移除滚动事件监听器
  if (tableWrapperRef.value) {
    tableWrapperRef.value.removeEventListener('scroll', handleTableScroll)
  }
})

// 对话框中表格的高度
const dialogTableHeight = ref('calc(100vh - 350px)')

// 编辑相关
const editDialogVisible = ref(false)
const editFormRef = ref(null)
const editForm = reactive({
  name: '',
  description: '',
  reviewer_ids: [],
  start_time: null,
  end_time: null
})
const reviewTimeRange = ref(null)
const projectMembers = ref([])
const submitting = ref(false)

// 添加用例相关
const addTestCaseDialogVisible = ref(false)
const availableTestCases = ref([])
const selectedTestCases = ref([])
const isRestoringSelection = ref(false)
const testcaseSearchKeyword = ref('')
const testcaseLoading = ref(false)
const selectingAll = ref(false)
const testcaseTableRef = ref(null)
const moduleTree = ref([])
let _moduleTreeVer = 0
let _selectorVer = 0
const testcaseFilter = reactive({
  module: '',
  subModule: ''
})
const testcasePagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

const canEdit = computed(() => {
  if (isAdmin.value) return true
  const currentUserId = JSON.parse(localStorage.getItem('user')).id
  return planDetail.value.created_by === currentUserId
})

// 筛选后的用例列表（服务端已筛选，直接返回）
const filteredTestcaseList = computed(() => {
  return testcaseList.value
})

// 按状态筛选（服务端筛选）
const filterByStatus = (status) => {
  statusFilter.value = status
  pagination.page = 1
  loadTestCases()
  loadPlanDetail()  // 刷新统计数据
}

const loadPlanDetail = async () => {
  try {
    const res = await getReviewPlanDetail(route.params.id)
    if (res.code === 200) {
      planDetail.value = res.data
      // 存储计划名称供数据埋点使用
      if (res.data.name) {
        sessionStorage.setItem(`plan_name_${route.params.id}`, res.data.name)
      }
    }
  } catch (error) {
    ElMessage.error('加载评审计划详情失败')
  }
}

const loadTestCases = async () => {
  loadingStore.showLoading()
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      size: pagination.size,
      keyword: searchKeyword.value || undefined,
      review_status: statusFilter.value || undefined
    }
    const res = await getPlanTestCases(route.params.id, params)
    if (res.code === 200) {
      testcaseList.value = res.data.records
      pagination.total = res.data.total
    }
  } catch (error) {
    ElMessage.error('加载用例列表失败')
  } finally {
    loadingStore.hideLoading()
    loading.value = false
  }
}


const showEditDialog = async () => {
  // 加载项目成员
  try {
    const res = await getProjectMembers(planDetail.value.project_id)
    if (res.code === 200) {
      projectMembers.value = res.data
    }
  } catch (error) {
    console.error('加载项目成员失败', error)
  }
  
  // 填充表单
  editForm.name = planDetail.value.name
  editForm.description = planDetail.value.description
  editForm.reviewer_ids = planDetail.value.reviewer_ids || []
  editForm.start_time = planDetail.value.start_time
  editForm.end_time = planDetail.value.end_time
  
  if (planDetail.value.start_time && planDetail.value.end_time) {
    reviewTimeRange.value = [planDetail.value.start_time, planDetail.value.end_time]
  } else {
    reviewTimeRange.value = null
  }
  
  editDialogVisible.value = true
}

const submitEdit = async () => {
  if (!editFormRef.value) return
  
  await editFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    submitting.value = true
    try {
      // 处理时间范围
      if (reviewTimeRange.value && reviewTimeRange.value.length === 2) {
        editForm.start_time = reviewTimeRange.value[0]
        editForm.end_time = reviewTimeRange.value[1]
      }
      
      await updateReviewPlan(route.params.id, editForm)
      ElMessage.success('更新成功')
      editDialogVisible.value = false
      await loadPlanDetail()
    } catch (error) {
      ElMessage.error('更新失败')
    } finally {
      submitting.value = false
    }
  })
}

const showAddTestCaseDialog = async () => {
  addTestCaseDialogVisible.value = true
  testcaseSearchKeyword.value = ''
  testcaseFilter.module = ''
  testcaseFilter.subModule = ''
  testcasePagination.page = 1
  selectedTestCases.value = []
  
  // 加载模块树
  await loadModuleTree()
  
  // 加载用例列表
  loadAvailableTestCases()
}

const loadModuleTree = async () => {
  if (currentProjectIds.value.length === 0) return
  
  const ver = ++_moduleTreeVer
  try {
    const projectParam = currentProjectIds.value.join(',')
    const res = await getModuleTree(projectParam)
    if (ver !== _moduleTreeVer) return
    if (res.code === 200) {
      const addExpanded = (nodes) => nodes.map(n => ({
        ...n,
        expanded: false,
        children: n.children ? addExpanded(n.children) : []
      }))
      moduleTree.value = addExpanded(res.data || [])
    }
  } catch (error) {
    console.error('加载模块树失败', error)
  }
}

const flatModuleTree = computed(() => {
  const result = []
  const flatten = (nodes, depth) => {
    for (const node of nodes) {
      result.push({ ...node, depth })
      if (node.expanded && node.children && node.children.length > 0) {
        flatten(node.children, depth + 1)
      }
    }
  }
  flatten(moduleTree.value, 0)
  return result
})


const loadAvailableTestCases = async () => {
  if (currentProjectIds.value.length === 0) return
  
  const ver = ++_selectorVer
  testcaseLoading.value = true
  try {
    const params = {
      page: testcasePagination.page,
      size: testcasePagination.size,
      project_ids: currentProjectIds.value.join(','),
      keyword: testcaseSearchKeyword.value || undefined,
      status: 'PENDING',
      module: (testcaseFilter.subModule ? `${testcaseFilter.module}/${testcaseFilter.subModule}` : testcaseFilter.module) || undefined,
      exclude_in_review: true
    }
    
    const res = await getTestCases(params)
    if (ver !== _selectorVer) return
    if (res.code === 200) {
      isRestoringSelection.value = true
      availableTestCases.value = res.data.records
      testcasePagination.total = res.data.total
      
      // 先清除所有选中状态，防止 row-key 复用导致残留勾选
      await nextTick()
      if (testcaseTableRef.value) {
        testcaseTableRef.value.clearSelection()
      }
      // 恢复之前选中的用例
      if (testcaseTableRef.value && selectedTestCases.value.length > 0) {
        const selectedIds = new Set(selectedTestCases.value.map(tc => tc.id))
        availableTestCases.value.forEach(row => {
          if (selectedIds.has(row.id)) {
            testcaseTableRef.value.toggleRowSelection(row, true)
          }
        })
      }
      await nextTick()
      isRestoringSelection.value = false
    }
  } catch (error) {
    ElMessage.error('加载用例列表失败')
  } finally {
    testcaseLoading.value = false
  }
}

const toggleModule = (modulePath) => {
  const findAndToggle = (nodes) => {
    for (const n of nodes) {
      if (n.path === modulePath) { n.expanded = !n.expanded; return true }
      if (n.children && findAndToggle(n.children)) return true
    }
    return false
  }
  findAndToggle(moduleTree.value)
}

const handleModuleClick = (modulePath) => {
  testcaseFilter.module = modulePath
  testcaseFilter.subModule = ''
  testcasePagination.page = 1
  loadAvailableTestCases()
}

const handleTestCaseSelectionChange = (selection) => {
  // 恢复选中状态期间跳过，避免清空已选
  if (isRestoringSelection.value) return
  
  // 获取当前页面的所有用例ID
  const currentPageIds = new Set(availableTestCases.value.map(tc => tc.id))
  
  // 移除当前页面的所有用例（无论是否选中）
  const otherPagesSelected = selectedTestCases.value.filter(tc => !currentPageIds.has(tc.id))
  
  // 添加当前页面新选中的用例
  selectedTestCases.value = [...otherPagesSelected, ...selection]
}

// 全选当前模块
const selectAllCurrentModule = async () => {
  if (currentProjectIds.value.length === 0) {
    ElMessage.warning('请先选择用例库')
    return
  }
  
  selectingAll.value = true
  try {
    const params = {
      project_ids: currentProjectIds.value.join(','),
      keyword: testcaseSearchKeyword.value || undefined,
      module: (testcaseFilter.subModule ? `${testcaseFilter.module}/${testcaseFilter.subModule}` : testcaseFilter.module) || undefined,
      status_in: 'REVIEWED,PENDING'
    }
    
    const res = await getAllTestCaseIds(params)
    if (res.code === 200) {
      const allTestCases = res.data.records
      
      // 直接替换选择列表为所有用例（去重）
      const existingIds = new Set(selectedTestCases.value.map(tc => tc.id))
      const newTestCases = allTestCases.filter(tc => !existingIds.has(tc.id))
      selectedTestCases.value = [...selectedTestCases.value, ...newTestCases]
      
      // 同步表格的选中状态
      if (testcaseTableRef.value) {
        const selectedIds = new Set(selectedTestCases.value.map(tc => tc.id))
        availableTestCases.value.forEach(row => {
          const shouldSelect = selectedIds.has(row.id)
          testcaseTableRef.value.toggleRowSelection(row, shouldSelect)
        })
      }
      
      ElMessage.success(`已选择 ${allTestCases.length} 条用例`)
    }
  } catch (error) {
    console.error('全选失败', error)
    ElMessage.error('全选失败')
  } finally {
    selectingAll.value = false
  }
}


const confirmAddTestCases = async () => {
  if (selectedTestCases.value.length === 0) {
    ElMessage.warning('请先选择用例')
    return
  }
  
  try {
    const testcaseIds = selectedTestCases.value.map(tc => tc.id)
    await addTestCasesToPlan(route.params.id, { testcase_ids: testcaseIds })
    ElMessage.success(`成功添加 ${testcaseIds.length} 个用例`)
    addTestCaseDialogVisible.value = false
    await loadTestCases()
    await loadPlanDetail()
  } catch (error) {
    ElMessage.error('添加用例失败')
  }
}

const removing = ref(false)

const removeTestCase = async (row) => {
  if (removing.value) return
  removing.value = true
  try {
    await ElMessageBox.confirm(
      `确定要从评审计划中移除用例"${row.case_number}"吗？`,
      '确认移除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    await removeTestCaseFromPlan(route.params.id, row.id)
    ElMessage.success('移除成功')
    await loadTestCases()
    await loadPlanDetail()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('移除失败')
    }
  } finally {
    removing.value = false
  }
}

const goBack = () => {
  router.push('/review-plans')
}

const getStatusType = (status) => {
  const typeMap = {
    PENDING: 'info',
    IN_PROGRESS: 'warning',
    COMPLETED: 'success',
    CANCELLED: 'info'
  }
  return typeMap[status] || 'info'
}

const getStatusText = (status) => {
  const textMap = {
    PENDING: t('review.statusNotStarted'),
    IN_PROGRESS: t('review.statusInProgress'),
    COMPLETED: t('review.statusCompleted'),
    CANCELLED: t('review.statusCancelled')
  }
  return textMap[status] || status
}

const formatDate = (dateTime) => {
  if (!dateTime) return '-'
  return new Date(dateTime).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 评审结果 -> Element Plus tag 类型
const getResultTagType = (result) => {
  if (result === 'APPROVED') return 'success'
  if (result === 'REJECTED') return 'danger'
  if (result === 'DEPRECATED') return 'info'
  return 'warning'
}

// 评审结果 -> 文案
const getResultText = (result) => {
  if (result === 'APPROVED') return '已通过'
  if (result === 'REJECTED') return '未通过'
  if (result === 'DEPRECATED') return '已废弃'
  return '待评审'
}

// 取有效评审结果：暂存优先，否则官方
const getEffectiveResult = (row) => {
  if (!row) return null
  return row.pending_review_result || row.review_result || null
}


// 解析步骤文本（支持JSON格式和纯文本格式）
const parseSteps = (stepsText) => {
  if (!stepsText) return []
  
  // 如果已经是数组，直接处理
  if (Array.isArray(stepsText)) {
    return stepsText.map(item => {
      let text = ''
      if (typeof item === 'object' && item !== null) {
        text = String(item.step || '').trim()
      } else {
        text = String(item).trim()
      }
      
      // 移除序号前缀
      while (/^(\d+)(?:[。、]|\.)(?!\d)\s*/.test(text)) {
        text = text.replace(/^(\d+)(?:[。、]|\.)(?!\d)\s*/, '')
      }
      return text.trim()
    }).filter(text => text)
  }
  
  // 转换为字符串并去除首尾空格
  const textStr = String(stepsText).trim()
  if (!textStr) return []
  
  try {
    // 尝试解析JSON格式
    const parsed = JSON.parse(textStr)
    
    if (Array.isArray(parsed)) {
      return parsed.map(item => {
        let text = ''
        if (typeof item === 'object' && item !== null) {
          text = String(item.step || '').trim()
        } else {
          text = String(item).trim()
        }
        
        // 移除序号前缀
        while (/^(\d+)(?:[。、]|\.)(?!\d)\s*/.test(text)) {
          text = text.replace(/^(\d+)(?:[。、]|\.)(?!\d)\s*/, '')
        }
        return text.trim()
      }).filter(text => text)
    }
  } catch (e) {
    // JSON解析失败，按纯文本处理
  }
  
  // 纯文本处理：有序号（>=2行）按序号拆，无序号整体1条保留换行
  const lines = textStr.split('\n')
  // 序号行：以 数字+标点 开头即可，内容可以为空（如 "2. "）
  const numberedLines = lines.filter(l => /^\s*\d+\s*(?:[。、]|\.)(?!\d)/.test(l.trim()))
  if (numberedLines.length >= 2) {
    const items = []
    let current = null
    for (const line of lines) {
      const stripped = line.trim()
      if (/^\s*\d+\s*(?:[。、]|\.)(?!\d)\s*/.test(stripped)) {
        if (current !== null) items.push(current.trim())
        current = stripped.replace(/^\s*\d+\s*(?:[。、]|\.)(?!\d)\s*/, '')
      } else if (current !== null) {
        current += '\n' + line
      }
    }
    if (current !== null) items.push(current.trim())
    return items.filter(t => t)
  }
  // 整体1条，但去掉可能存在的序号前缀（避免前端自动编号导致双重序号）
  const stripped2 = textStr.replace(/^\s*\d+\s*(?:[。、]|\.)(?!\d)\s*/, '')
  return stripped2 ? [stripped2] : []
}


// 解析预期结果
const parseExpected = (expectedText) => {
  if (!expectedText) return []
  
  // 如果已经是数组，直接处理
  if (Array.isArray(expectedText)) {
    return expectedText.map(item => {
      let text = ''
      if (typeof item === 'object' && item !== null) {
        text = String(item.expected || '').trim()
      } else {
        text = String(item).trim()
      }
      
      // 移除序号前缀
      while (/^(\d+)(?:[。、]|\.)(?!\d)\s*/.test(text)) {
        text = text.replace(/^(\d+)(?:[。、]|\.)(?!\d)\s*/, '')
      }
      return text.trim()
    }).filter(text => text)
  }
  
  // 转换为字符串并去除首尾空格
  const textStr = String(expectedText).trim()
  if (!textStr) return []
  
  try {
    // 尝试解析JSON格式
    const parsed = JSON.parse(textStr)
    
    if (Array.isArray(parsed)) {
      return parsed.map(item => {
        let text = ''
        if (typeof item === 'object' && item !== null) {
          text = String(item.expected || '').trim()
        } else {
          text = String(item).trim()
        }
        
        // 移除序号前缀
        while (/^(\d+)(?:[。、]|\.)(?!\d)\s*/.test(text)) {
          text = text.replace(/^(\d+)(?:[。、]|\.)(?!\d)\s*/, '')
        }
        return text
      }).filter(text => text)
    }
  } catch (e) {
    // JSON解析失败，按纯文本处理
  }
  
  // 纯文本处理：有序号（>=2行）按序号拆，无序号整体1条保留换行
  const lines = textStr.split('\n')
  // 序号行：以 数字+标点 开头即可，内容可以为空（如 "2. "）
  const numberedLines = lines.filter(l => /^\s*\d+\s*(?:[。、]|\.)(?!\d)/.test(l.trim()))
  if (numberedLines.length >= 2) {
    const items = []
    let current = null
    for (const line of lines) {
      const stripped = line.trim()
      if (/^\s*\d+\s*(?:[。、]|\.)(?!\d)\s*/.test(stripped)) {
        if (current !== null) items.push(current.trim())
        current = stripped.replace(/^\s*\d+\s*(?:[。、]|\.)(?!\d)\s*/, '')
      } else if (current !== null) {
        current += '\n' + line
      }
    }
    if (current !== null) items.push(current.trim())
    return items.filter(t => t)
  }
  // 整体1条，但去掉可能存在的序号前缀（避免前端自动编号导致双重序号）
  const stripped2 = textStr.replace(/^\s*\d+\s*(?:[。、]|\.)(?!\d)\s*/, '')
  return stripped2 ? [stripped2] : []
}

onMounted(() => {
  loadPlanDetail()
  loadTestCases()
})
</script>


<style scoped>
.review-detail-container {
  padding: 10px 20px 20px 20px;
  min-height: 100%;
  background: var(--demo-bg);
}

.detail-header {
  display: flex;
  align-items: center;
  padding: 16px 20px;
  background: var(--demo-bg-card);
  border: 1px solid var(--demo-border);
  border-radius: 16px;
  margin-bottom: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.detail-header h2 {
  font-size: 20px;
  font-weight: 600;
  color: var(--demo-text-primary);
}

/* 按钮样式 - Demo主题 */
.detail-header :deep(.el-button) {
  border-radius: 8px;
  font-weight: 500;
  height: 40px;
  padding: 0 16px;
  font-size: 14px;
  transition: all 0.15s;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.detail-header :deep(.el-button--primary) {
  background: var(--demo-primary);
  border: none;
}

.detail-header :deep(.el-button--primary:hover) {
  background: var(--demo-primary-hover);
}

.detail-header :deep(.el-button--default) {
  background: #ffffff;
  border: 1px solid var(--demo-border);
  color: var(--demo-text-secondary);
}

.detail-header :deep(.el-button--default:hover) {
  background: var(--demo-bg);
  border-color: #cbd5e1;
}

/* 基本信息区域 */
.info-section {
  background: var(--demo-bg-card);
  border: 1px solid var(--demo-border);
  border-radius: 16px;
  padding: 24px;
  margin-top: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--demo-text-primary);
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--demo-border);
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
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
  color: var(--demo-text-muted);
  font-size: 14px;
  min-width: 100px;
  flex-shrink: 0;
}

.info-value {
  color: var(--demo-text-primary);
  font-size: 14px;
  flex: 1;
}


/* 统计区域 - Demo主题 */
.stats-section {
  background: var(--demo-bg-card);
  border: 1px solid var(--demo-border);
  border-radius: 16px;
  padding: 20px 24px;
  margin-top: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.stats-cards {
  display: flex;
  gap: 16px;
  margin-top: 12px;
  flex-wrap: wrap;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  background: var(--demo-bg);
  border-radius: 12px;
  min-width: 140px;
  transition: all 0.15s;
  border: 1px solid var(--demo-border);
}

.stat-card.clickable {
  cursor: pointer;
}

.stat-card.clickable:hover {
  background: var(--demo-border-light);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.stat-card.active {
  background: var(--demo-primary-light);
  border: 2px solid var(--demo-primary);
}

.stat-label {
  font-size: 14px;
  color: var(--demo-text-muted);
  white-space: nowrap;
}

.stat-value {
  font-size: 20px;
  font-weight: 600;
  color: var(--demo-text-primary);
}

/* 用例列表区域 */
.testcase-list-section {
  min-height: calc(100% - 200px);
  display: flex;
  flex-direction: column;
  background: var(--demo-bg-card);
  border: 1px solid var(--demo-border);
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

/* 列表头部样式 */
.list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0;
  padding: 12px 0;
}

/* 列表头部按钮样式 */
.list-header :deep(.el-button) {
  border-radius: 8px;
  font-weight: 500;
  height: 40px;
  padding: 0 16px;
  font-size: 14px;
  transition: all 0.15s;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.list-header :deep(.el-button--primary) {
  background: var(--demo-primary);
  border: none;
}

.list-header :deep(.el-button--primary:hover) {
  background: var(--demo-primary-hover);
}

/* 输入框样式 */
.list-header :deep(.el-input__wrapper) {
  border-radius: 8px;
  border: 1px solid var(--demo-border);
  box-shadow: none;
  height: 40px;
}

.list-header :deep(.el-input__wrapper:hover) {
  border-color: #cbd5e1;
}

.list-header :deep(.el-input__wrapper.is-focus) {
  border-color: var(--demo-primary);
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.1);
}

/* 固定工具栏 */
.sticky-toolbar {
  position: sticky;
  top: 0;
  z-index: 101;
  background: var(--demo-bg-card);
  padding: 12px 0;
  margin-bottom: 0 !important;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}


/* 表格容器 */
.table-container {
  width: 100%;
  position: relative;
  margin-bottom: 20px;
  margin-top: 0;
  overflow-x: auto;
  min-height: 600px;
  border: 1px solid var(--demo-border);
  border-radius: 12px;
  background: var(--demo-bg-card);
  scroll-behavior: smooth;
}

/* 表格表头固定 */
.sticky-header-table {
  position: relative;
  min-width: 1000px;
}

.sticky-header-table :deep(.el-table__header-wrapper) {
  position: sticky;
  top: 0;
  z-index: 100;
  background: var(--demo-bg-card) !important;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  overflow-x: hidden;
  border-bottom: 1px solid var(--demo-border);
}

.sticky-header-table :deep(.el-table__header-wrapper th) {
  background: #f8fafc !important;
  color: var(--demo-text-muted) !important;
  font-weight: 500 !important;
  font-size: 12px !important;
  text-transform: uppercase !important;
  letter-spacing: 0.05em !important;
  position: sticky;
  top: 0;
  z-index: 101;
  white-space: nowrap;
  border-right: 1px solid var(--demo-border);
}

/* 表格行悬停样式 */
.sticky-header-table :deep(.el-table__row:hover > td) {
  background: #f8fafc !important;
}

/* 固定列不透明背景 */
.sticky-header-table :deep(.el-table td.el-table__cell) {
  background: #fff;
}

/* 表格内容区域 */
.sticky-header-table :deep(.el-table__body-wrapper) {
  overflow-y: auto;
  overflow-x: hidden;
  max-height: calc(100vh - 220px);
}

/* 滚动条样式 */
.table-container::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

.table-container::-webkit-scrollbar-track {
  background: var(--demo-border-light);
  border-radius: 4px;
}

.table-container::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}

.table-container::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

/* Firefox滚动条 */
.table-container {
  scrollbar-width: thin;
  scrollbar-color: #cbd5e1 var(--demo-border-light);
}

/* 分页器固定在屏幕底部 */
.pagination-container {
  display: flex;
  justify-content: flex-end;
  padding: 12px 20px;
  background: var(--demo-bg-card);
  z-index: 999;
  box-shadow: 0 -2px 4px rgba(0, 0, 0, 0.05);
  height: 50px;
  align-items: center;
}

/* 分页器按钮样式 */
.pagination-container :deep(.el-pagination) {
  font-weight: normal;
}

.pagination-container :deep(.el-pagination button),
.pagination-container :deep(.el-pager li) {
  background: transparent !important;
  font-weight: normal;
}

.pagination-container :deep(.el-pager li) {
  border-radius: 6px;
  margin: 0 2px;
  transition: all 0.15s;
  min-width: 32px;
  height: 32px;
}

.pagination-container :deep(.el-pager li:hover) {
  color: var(--demo-primary);
  background: var(--demo-border-light);
}

.pagination-container :deep(.el-pager li.is-active) {
  background: var(--demo-primary-light);
  color: var(--demo-primary);
  font-weight: 600;
}


/* 单行省略号样式 */
.single-line-ellipsis {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  width: 100%;
}

/* 标签省略号样式 */
.ellipsis-tag {
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: inline-block;
}

/* Tooltip 样式 */
.steps-tooltip {
  max-width: 600px !important;
}

/* 移除图标样式 */
.remove-icon {
  font-size: 20px;
  color: #be123c;
  cursor: pointer;
  transition: all 0.15s;
}

.remove-icon:hover {
  color: #e11d48;
  transform: scale(1.1);
}

.remove-icon.is-loading {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 多选框样式优化 */
:deep(.el-table .el-checkbox) {
  transform: scale(1.3);
}

:deep(.el-table .el-checkbox__inner) {
  width: 16px;
  height: 16px;
  border-width: 2px;
  border-radius: 4px;
  border-color: #cbd5e1;
}

:deep(.el-table .el-checkbox__input.is-checked .el-checkbox__inner) {
  background: var(--demo-primary);
  border-color: var(--demo-primary);
}

:deep(.el-table .el-checkbox__inner::after) {
  width: 4px;
  height: 8px;
  border-width: 2px;
}

/* ==================== */
/* 关联用例对话框样式 - Demo主题 */
/* ==================== */

/* 对话框整体样式 */
:deep(.el-dialog) {
  border-radius: 16px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.12);
}

:deep(.el-dialog__header) {
  padding: 20px 24px 16px;
  border-bottom: 1px solid var(--demo-border);
  background: var(--demo-bg);
  border-radius: 16px 16px 0 0;
}

:deep(.el-dialog__title) {
  font-size: 18px;
  font-weight: 600;
  color: var(--demo-text-primary);
}

:deep(.el-dialog__body) {
  padding: 0;
}

/* 用例选择容器 */
.testcase-select-container {
  display: flex;
  height: calc(100vh - 180px);
  overflow: hidden;
}

/* 左侧模块侧边栏 - 与用例管理界面一致 */
.module-sidebar {
  width: 220px;
  background: #f8fafc;
  border-right: 1px solid var(--demo-border);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

/* 用例库选择器区域 */
.project-filter-section {
  padding: 16px;
  background: linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%);
  border-bottom: 1px solid var(--demo-border);
}

.project-filter-section .section-header {
  font-weight: 600;
  font-size: 12px;
  color: var(--demo-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.project-filter-section .section-header::before {
  content: '';
  width: 3px;
  height: 12px;
  background: var(--demo-primary);
  border-radius: 2px;
}

.project-filter-content {
  display: flex;
  flex-direction: column;
}

/* 模块头部 */
.module-header {
  padding: 14px 16px;
  font-weight: 600;
  font-size: 12px;
  color: var(--demo-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  background: #fff;
  border-bottom: 1px solid var(--demo-border-light);
  display: flex;
  align-items: center;
  gap: 6px;
}

.module-header::before {
  content: '';
  width: 3px;
  height: 12px;
  background: var(--demo-primary);
  border-radius: 2px;
}

/* 模块列表 */
.module-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
  background: #fff;
}

.module-list::-webkit-scrollbar {
  width: 6px;
}

.module-list::-webkit-scrollbar-track {
  background: transparent;
}

.module-list::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

.module-list::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

.module-group {
  margin-bottom: 2px;
}

.module-item {
  padding: 10px 12px;
  margin: 2px 0;
  cursor: pointer;
  display: flex;
  align-items: center;
  font-size: 14px;
  color: var(--demo-text-secondary);
  transition: all 0.15s ease;
  user-select: none;
  border-radius: 8px;
  border: 1px solid transparent;
}

.module-item:hover {
  background: var(--demo-bg);
  border-color: var(--demo-border-light);
}

.module-item.active {
  background: var(--demo-primary-light);
  color: var(--demo-primary);
  font-weight: 600;
  border-color: rgba(79, 70, 229, 0.2);
}

.module-item .expand-icon {
  margin-right: 8px;
  font-size: 12px;
  color: var(--demo-text-muted);
  flex-shrink: 0;
  transition: transform 0.2s;
}

.module-content {
  flex: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
  overflow: hidden;
  gap: 8px;
}

.module-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.module-count {
  font-size: 12px;
  color: var(--demo-text-muted);
  background: var(--demo-border-light);
  padding: 2px 8px;
  border-radius: 12px;
  font-weight: 500;
}

.module-item.active .module-count {
  background: rgba(79, 70, 229, 0.15);
  color: var(--demo-primary);
}

.sub-module-list {
  margin-left: 20px;
  border-left: 2px solid var(--demo-border-light);
  padding-left: 8px;
}

.sub-module {
  padding-left: 12px;
  font-size: 13px;
}

/* 右侧内容区域 */
.testcase-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--demo-bg);
  overflow: hidden;
}

/* 工具栏 */
.testcase-filter {
  display: flex;
  align-items: center;
  padding: 16px 20px;
  background: #fff;
  border-bottom: 1px solid var(--demo-border);
  gap: 12px;
  flex-shrink: 0;
}

/* 搜索框样式 */
.testcase-filter :deep(.el-input__wrapper) {
  border-radius: 8px;
  border: 1px solid var(--demo-border);
  box-shadow: none;
  height: 40px;
  transition: all 0.15s;
}

.testcase-filter :deep(.el-input__wrapper:hover) {
  border-color: #cbd5e1;
}

.testcase-filter :deep(.el-input__wrapper.is-focus) {
  border-color: var(--demo-primary);
  box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
}

/* 按钮样式 */
.testcase-filter :deep(.el-button) {
  border-radius: 8px;
  font-weight: 500;
  height: 40px;
  padding: 0 16px;
  font-size: 14px;
  transition: all 0.15s;
}

.testcase-filter :deep(.el-button--primary) {
  background: var(--demo-primary);
  border: none;
  box-shadow: 0 2px 4px rgba(79, 70, 229, 0.2);
}

.testcase-filter :deep(.el-button--primary:hover) {
  background: var(--demo-primary-hover);
  box-shadow: 0 4px 8px rgba(79, 70, 229, 0.3);
}

.testcase-filter :deep(.el-button--default) {
  background: #fff;
  border: 1px solid var(--demo-border);
  color: var(--demo-text-secondary);
}

.testcase-filter :deep(.el-button--default:hover) {
  background: var(--demo-bg);
  border-color: #cbd5e1;
  color: var(--demo-text-primary);
}

/* 表格容器 */
.testcase-content .table-wrapper {
  flex: 1;
  margin: 16px 20px;
  background: #fff;
  border-radius: 12px;
  border: 1px solid var(--demo-border);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* 表格样式 */
.testcase-content .table-wrapper :deep(.el-table) {
  width: 100%;
  border: none;
}

.testcase-content .table-wrapper :deep(.el-table__header-wrapper) {
  background: #f8fafc;
}

.testcase-content .table-wrapper :deep(.el-table th.el-table__cell) {
  background: #f8fafc !important;
  color: var(--demo-text-muted) !important;
  font-weight: 500 !important;
  font-size: 12px !important;
  text-transform: uppercase !important;
  letter-spacing: 0.05em !important;
  border-bottom: 1px solid var(--demo-border) !important;
}

.testcase-content .table-wrapper :deep(.el-table__row:hover > td) {
  background: #f8fafc !important;
}

.testcase-content .table-wrapper :deep(.el-table__body-wrapper) {
  overflow-x: auto !important;
  overflow-y: auto !important;
}

.testcase-content .table-wrapper :deep(.el-table__header),
.testcase-content .table-wrapper :deep(.el-table__body) {
  width: 100% !important;
  table-layout: fixed !important;
}

/* 表格单元格样式 */
.testcase-content .table-wrapper :deep(.el-table__cell) {
  padding: 0 12px !important;
  height: 52px !important;
}

/* 修复选择框列显示不完整的问题 */
.testcase-content .table-wrapper :deep(.el-table-column--selection) {
  overflow: visible !important;
}

.testcase-content .table-wrapper :deep(.el-table-column--selection .cell) {
  padding: 0 !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  overflow: visible !important;
}

.testcase-content .table-wrapper :deep(.el-checkbox) {
  margin: 0 !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
}

.testcase-content .table-wrapper :deep(.el-checkbox__inner) {
  width: 18px !important;
  height: 18px !important;
  border-radius: 4px !important;
  border: 2px solid #cbd5e1 !important;
}

.testcase-content .table-wrapper :deep(.el-checkbox__input.is-checked .el-checkbox__inner) {
  background: var(--demo-primary) !important;
  border-color: var(--demo-primary) !important;
}

.testcase-content .table-wrapper :deep(.el-checkbox__inner::after) {
  width: 4px !important;
  height: 8px !important;
  border-width: 2px !important;
  left: 5px !important;
  top: 1px !important;
}

/* 分页器样式 */
.testcase-content :deep(.el-pagination) {
  padding: 16px 20px;
  background: #fff;
  border-top: 1px solid var(--demo-border);
  justify-content: flex-end;
  margin: 0;
}

.testcase-content :deep(.el-pager li) {
  background: transparent;
  font-weight: 500;
  border-radius: 6px;
  min-width: 32px;
  height: 32px;
  transition: all 0.15s;
}

.testcase-content :deep(.el-pager li.is-active) {
  background: var(--demo-primary-light);
  color: var(--demo-primary);
  font-weight: 600;
}

.testcase-content :deep(.el-pager li:hover:not(.is-active)) {
  background: var(--demo-border-light);
}
</style>