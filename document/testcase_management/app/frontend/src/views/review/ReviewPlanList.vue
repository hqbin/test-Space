<template>
  <div class="review-plan-container">
    <!-- 搜索和操作栏 -->
    <div class="toolbar">
      <div class="left-actions">
        <el-button type="primary" @click="showCreateDialog">
          <el-icon><Plus /></el-icon>
          {{ $t('review.createPlan') }}
        </el-button>
      </div>
      
      <div class="search-bar">
        <el-select
          v-model="filterStatus"
          :placeholder="$t('review.statusFilter')"
          clearable
          style="width: 150px; margin-right: 10px"
          @change="handleSearch"
          @clear="handleSearch"
        >
          <el-option :label="$t('common.all')" value="ALL" />
          <el-option :label="$t('review.statusNotStarted')" value="PENDING" />
          <el-option :label="$t('review.statusInProgress')" value="IN_PROGRESS" />
          <el-option :label="$t('review.statusCompleted')" value="COMPLETED" />
          <el-option :label="$t('review.statusCancelled')" value="CANCELLED" />
        </el-select>
        
        <el-input
          v-model="searchKeyword"
          :placeholder="$t('review.searchPlaceholder')"
          clearable
          style="width: 250px; margin-right: 10px"
          @clear="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        
        <el-button type="primary" @click="handleSearch">
          <el-icon><Search /></el-icon>
          {{ $t('common.search') }}
        </el-button>
      </div>
    </div>

    <!-- 评审计划表格 -->
    <div class="table-wrapper">
      <div class="table-container" ref="tableContainerRef">
      <el-table
        ref="tableRef"
        :data="planList"
        style="width: 100%"
        border
        :height="tableHeight"
      >
          <el-table-column :label="$t('review.planName')" width="250" align="center">
            <template #default="{ row }">
              <el-tooltip :content="row.name" placement="top" :show-after="500" :teleported="false" :disabled="!row.name">
                <div class="ellipsis-text clickable-name" @click="viewDetail(row.id)">
                  {{ row.name }}
                </div>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column :label="$t('review.caseCount')" width="80" align="center">
            <template #default="{ row }">
              {{ row.total_testcases }}
            </template>
          </el-table-column>
          <el-table-column :label="$t('review.progress')" width="180" align="center">
            <template #default="{ row }">
              <div style="display: flex; align-items: center; justify-content: center;">
                <el-progress
                  :percentage="row.total_testcases > 0 ? Math.round(((row.executed_testcases || 0) / row.total_testcases) * 100) : 0"
                  :stroke-width="6"
                  style="flex: 1; margin-right: 8px"
                />
                <span style="font-size: 12px; color: #606266;">
                  {{ row.executed_testcases || 0 }}/{{ row.total_testcases }}
                </span>
              </div>
            </template>
          </el-table-column>
          <el-table-column :label="$t('review.passRate')" width="130" align="center">
            <template #default="{ row }">
              <span style="font-size: 14px; font-weight: 500;" :style="{ color: getPassRateColor(row) }">
                {{ row.total_testcases > 0 ? Math.round(((row.executed_passed_testcases || 0) / row.total_testcases) * 100) : 0 }}%
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="status" :label="$t('review.status')" width="90" align="center">
            <template #default="{ row }">
              <el-tag :type="getStatusType(row.status)" size="small">
                {{ getStatusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column :label="$t('review.reviewer')" width="120" align="center" :show-overflow-tooltip="{ showAfter: 500 }">
            <template #default="{ row }">
              <div style="text-align: center !important; width: 100% !important;">
                {{ row.reviewer_names && row.reviewer_names.length > 0 ? row.reviewer_names.join(', ') : '-' }}
              </div>
            </template>
          </el-table-column>
          <!-- 创建人列已隐藏 -->
          <el-table-column :label="$t('review.reviewPeriod')" width="150" align="center">
            <template #default="{ row }">
              <el-tooltip 
                :content="row.start_time && row.end_time ? `${formatDate(row.start_time)} ~ ${formatDate(row.end_time)}` : '-'" 
                placement="top"
                effect="dark"
                :show-after="500"
              >
                <span style="display: block; text-align: center; width: 100%;">
                  {{ row.end_time ? `~ ${formatDate(row.end_time)}` : '-' }}
                </span>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column :label="$t('review.operation')" width="320" align="center" fixed="right">
            <template #default="{ row }">
              <div style="display: flex; justify-content: center; align-items: center;">
                <el-button
                  v-if="(row.status === 'PENDING' || row.status === 'IN_PROGRESS') && canReviewPlan(row)"
                  link
                  type="primary"
                  @click="startReview(row)"
                >
                  {{ $t('review.execute') }}
                </el-button>
                
                <!-- 已完成状态：显示导出下拉菜单 -->
                <el-dropdown 
                  v-if="row.status === 'COMPLETED'" 
                  trigger="hover" 
                  @command="(cmd) => handleExportCommand(cmd, row)"
                >
                  <el-button 
                    type="info" 
                    size="small" 
                    link
                    :icon="MoreFilled"
                  />
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item command="excel">
                        <el-icon><Document /></el-icon>
                        <span>{{ $t('review.exportExcel') }}</span>
                      </el-dropdown-item>
                      <el-dropdown-item command="pdf">
                        <el-icon><Document /></el-icon>
                        <span>{{ $t('review.exportPdf') }}</span>
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
                
                <!-- 删除下拉菜单：超管可删除任意状态，普通用户只能删除PENDING状态自己的计划 -->
                <el-dropdown 
                  v-if="hasButton('testcases', 'deleteReviewPlan') && canDelete(row) && ((isSuperAdmin.value) || row.status === 'PENDING')" 
                  trigger="hover" 
                  @command="(cmd) => handleDropdownCommand(cmd, row)"
                >
                  <el-button 
                    type="info" 
                    size="small" 
                    link
                    :icon="MoreFilled"
                  />
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item command="delete">
                        <el-icon><Delete /></el-icon>
                        <span>{{ $t('review.delete') }}</span>
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </div>

        <!-- 分页 -->
        <div class="pagination-container">
          <el-pagination
            v-model:current-page="pagination.page"
            v-model:page-size="pagination.size"
            :page-sizes="[10, 20, 50, 100]"
            :total="pagination.total"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handlePageChange"
            background
          />
        </div>
      </div>

    <!-- 新建/编辑评审计划对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="780px"
      @close="handleDialogClose"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="100px"
      >
        <el-form-item :label="$t('review.planName')" prop="name">
          <el-input v-model="formData.name" :placeholder="$t('review.planNamePlaceholder')" />
        </el-form-item>
        
        <el-form-item :label="$t('review.description')">
          <el-input
            v-model="formData.description"
            type="textarea"
            :rows="3"
            :placeholder="$t('review.descriptionPlaceholder')"
          />
        </el-form-item>
        
        <el-form-item :label="$t('review.reviewer')" prop="reviewer_ids">
          <el-select
            ref="reviewerSelectRef"
            v-model="formData.reviewer_ids"
            multiple
            :placeholder="$t('review.selectReviewer')"
            style="width: 100%"
            filterable
            remote
            :remote-method="handleReviewerSearch"
            :loading="reviewerSearchLoading"
            :disabled="false"
            @focus="loadProjectMembers"
            @change="handleReviewerChange"
          >
            <el-option
              v-for="member in availableReviewers"
              :key="member.id"
              :label="member.username"
              :value="member.id"
            />
          </el-select>
        </el-form-item>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item :label="$t('review.startTime')">
              <el-date-picker
                v-model="formData.start_time"
                type="date"
                :placeholder="$t('review.selectStartTime')"
                style="width: 100%"
                value-format="YYYY-MM-DD 00:00:00"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item :label="$t('review.endTime')">
              <el-date-picker
                v-model="formData.end_time"
                type="date"
                :placeholder="$t('review.selectEndTime')"
                style="width: 100%"
                value-format="YYYY-MM-DD 00:00:00"
              />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      
      <!-- 关联用例部分 -->
      <div v-if="!isEdit" class="testcase-section">
        <div class="section-header">
          <span class="section-title">{{ $t('review.relatedCases') }}</span>
          <el-link type="primary" @click="showSelectTestCaseDialog">
            {{ $t('review.clickToSelect') }}
          </el-link>
        </div>
        
        <div v-if="selectedTestCases.length > 0" class="selected-count">
          {{ $t('review.selectedCases', { count: selectedTestCases.length }) }}
        </div>
      </div>
      
      <template #footer>
        <el-button @click="dialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitting">
          {{ isEdit ? $t('review.update') : $t('review.create') }}
        </el-button>
      </template>
    </el-dialog>
    
    <!-- 选择用例对话框 -->
    <el-dialog
      v-model="selectTestCaseDialogVisible"
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
              <span>{{ $t('menu.projects') }}</span>
            </div>
            <div class="project-filter-content">
              <ProjectSelector
                v-model="selectedProjectIdList"
                :project-list="teamProjectList"
                @change="handleProjectSelectorChange"
              />
            </div>
          </div>
          
          <el-divider style="margin: 12px 0;" />
          
          <div class="module-header">
            <span>{{ $t('review.belongModule') }}</span>
          </div>
          <div class="module-list">
            <div 
              class="module-item" 
              :class="{ active: testcaseFilter.module === '' }"
              @click="handleTestCaseModuleClick('')"
            >
              <span class="module-name">{{ $t('common.all') }}</span>
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
                @click.stop="toggleTestCaseModule(item.path)"
              >
                <ArrowRight v-if="!item.expanded" />
                <ArrowDown v-else />
              </el-icon>
              <div class="module-content" @click="handleTestCaseModuleClick(item.path)">
                <span class="module-name">{{ item.name }}<span v-if="item.tag" style="color: #409eff; margin-left: 2px;">({{ item.tag }})</span></span>
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
              style="width: 300px; margin-right: 10px"
              @keyup.enter="loadAvailableTestCases"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
            <el-button type="primary" @click="loadAvailableTestCases">
              <el-icon><Search /></el-icon>
              {{ $t('common.search') }}
            </el-button>
            
            <el-button 
              @click="selectAllTestCases"
              :disabled="availableTestCases.length === 0"
              style="margin-left: 10px"
              :loading="selectingAll"
            >
              {{ $t('review.selectAllCurrentModule') }}
            </el-button>
            
            <div style="flex: 1"></div>
            
            <el-button 
              type="primary" 
              :disabled="tempSelectedTestCases.length === 0"
              @click="confirmSelectTestCases"
            >
              {{ $t('review.relatedCasesCount', { count: tempSelectedTestCases.length }) }}
            </el-button>
          </div>
          
          <div class="table-wrapper">
            <el-table
              ref="testcaseTableRef"
              :data="availableTestCases"
              style="width: 100%"
              height="100%"
              border
              :header-cell-style="{ background: '#f8fafc', color: '#64748b', fontWeight: '500', fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.05em' }"
              v-loading="testcaseLoading"
              element-loading-text="加载中..."
              @selection-change="handleTestCaseSelectionChange"
            >
              <el-table-column type="selection" width="50" align="center" />
              <el-table-column prop="case_number" :label="$t('review.caseNumber')" width="230" align="center" resizable :show-overflow-tooltip="{ showAfter: 500 }">
                <template #default="scope">
                  <el-tooltip :content="scope.row.case_number" placement="top" :show-after="500">
                    <el-tag type="info" size="small" class="ellipsis-tag">{{ scope.row.case_number }}</el-tag>
                  </el-tooltip>
                </template>
              </el-table-column>
              <el-table-column prop="name" :label="$t('review.caseTitle')" min-width="200" align="left" resizable :show-overflow-tooltip="{ showAfter: 500 }">
                <template #default="scope">
                  <div class="single-line-ellipsis">{{ scope.row.name }}</div>
                </template>
              </el-table-column>
              <el-table-column prop="precondition" :label="$t('review.precondition')" min-width="200" align="left" resizable :show-overflow-tooltip="{ showAfter: 500 }">
                <template #default="scope">
                  <div class="single-line-ellipsis">{{ scope.row.precondition || '-' }}</div>
                </template>
              </el-table-column>
              <el-table-column prop="steps" :label="$t('review.testSteps')" min-width="250" align="left" resizable>
                <template #default="scope">
                  <el-tooltip 
                    placement="top" 
                    popper-class="steps-tooltip"
                    effect="dark"
                    :show-after="500"
                    raw-content
                  >
                    <template #content>
                      <div style="max-width: 500px; padding: 8px 0;">
                        <div 
                          v-for="(step, stepIndex) in parseSteps(scope.row.steps)" 
                          :key="stepIndex"
                          style="display: flex; padding: 6px 0; line-height: 1.6;"
                        >
                          <span style="color: #4f46e5; font-weight: 500; min-width: 30px;">{{ stepIndex + 1 }}.</span>
                          <span style="flex: 1; word-break: break-word;">{{ step }}</span>
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
                  <el-tooltip 
                    placement="top" 
                    popper-class="steps-tooltip"
                    effect="dark"
                    :show-after="500"
                    raw-content
                  >
                    <template #content>
                      <div style="max-width: 500px; padding: 8px 0;">
                        <div 
                          v-for="(result, resultIndex) in parseExpected(scope.row.expected_result)" 
                          :key="resultIndex"
                          style="display: flex; padding: 6px 0; line-height: 1.6;"
                        >
                          <span style="color: #4f46e5; font-weight: 500; min-width: 30px;">{{ resultIndex + 1 }}.</span>
                          <span style="flex: 1; word-break: break-word;">{{ result }}</span>
                        </div>
                      </div>
                    </template>
                    <div class="single-line-ellipsis">
                      {{ parseExpected(scope.row.expected_result).map((r, i) => `${i + 1}. ${r}`).join(' ') || '-' }}
                    </div>
                  </el-tooltip>
                </template>
              </el-table-column>
              <el-table-column prop="status" :label="$t('review.status')" width="140" align="center" resizable>
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
            @size-change="loadAvailableTestCases"
            @current-change="loadAvailableTestCases"
            style="margin-top: 20px; justify-content: flex-end"
          />
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
defineOptions({ name: 'ReviewPlanList' })
import { ref, reactive, onMounted, onActivated, onBeforeUnmount, computed, watch, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { useScrollToTop } from '../../composables/useScrollToTop'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus, ArrowLeft, ArrowRight, ArrowDown, MoreFilled, Delete, Document } from '@element-plus/icons-vue'
import {
  getReviewPlanList,
  createReviewPlan,
  updateReviewPlan,
  deleteReviewPlan,
  addTestCasesToPlan
} from '@/api/reviewPlan'
import { getProjects } from '@/api/project'
import { getTestCases, getAllTestCaseIds } from '@/api/testcase'
import { getModuleTree } from '@/api/module'
import { useUserRole } from '@/composables/useUserRole'
import { useTeam } from '@/composables/useTeam'
import { getAvailableMembersForSelection, getUserRoleInTeam } from '@/api/team'
import ProjectSelector from '../../components/ProjectSelector.vue'
import request from '@/api/request'
import { useLoadingStore } from '../../stores/loading'
import { eventBus } from '../../utils/eventBus'
import { useProjectPreference } from '../../composables/useProjectPreference'

const router = useRouter()
const { t } = useI18n()
const { isAdmin, isSuperAdmin, hasButton } = useUserRole()
const { currentTeam, teamProjects, loadTeamProjects } = useTeam()
const loadingStore = useLoadingStore()

// 当前用户角色类型：'member' | 'leader' | 'org_manager' | 'admin'
const currentUserRole = ref('member')

// 所有用户都可以选择其他评审人
const canSelectOtherReviewers = computed(() => {
  return true
})

// 可选评审人列表
const availableReviewersList = ref([])

// 用例库选择相关 - 新版本
const { selectedProjectIdList, applyPreference, updateSelection, resetPreference } = useProjectPreference()
const teamProjectList = computed(() => teamProjects.value || [])

// 当前项目组的所有用例库ID（评审计划列表用，不受用例库选择器影响）
const allTeamProjectIds = computed(() => {
  return teamProjectList.value.map(p => p.id)
})

// 计算当前选中的用例库ID列表（用例选择器对话框用）
const currentProjectIds = computed(() => {
  return selectedProjectIdList.value.length > 0 
    ? selectedProjectIdList.value 
    : teamProjectList.value.map(p => p.id)
})

// 兼容旧代码
const currentProject = computed(() => {
  if (currentProjectIds.value.length > 0) {
    const firstId = currentProjectIds.value[0]
    return teamProjectList.value.find(p => p.id === firstId) || null
  }
  return null
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

// 数据
const loading = ref(false)
const planList = ref([])
const projectList = ref([])
const projectMembers = ref([])
const searchKeyword = ref('')
const filterStatus = ref('')  // 空字符串表示默认状态（未开始+进行中）
const submitting = ref(false)
const tableRef = ref(null)

const pagination = reactive({
  page: 1,
  size: 10,
  total: 0
})

// 对话框
const dialogVisible = ref(false)
const dialogTitle = computed(() => isEdit.value ? t('review.editPlan') : t('review.createPlan'))
const formRef = ref(null)
const isEdit = ref(false)
const editId = ref(null)

const formData = reactive({
  name: '',
  description: '',
  project_id: null,
  team_id: null,
  reviewer_ids: [],
  start_time: null,
  end_time: null
})

const formRules = {
  name: [{ required: true, message: '请输入评审名称', trigger: 'blur' }],
  reviewer_ids: [
    { required: true, message: '请选择评审人', trigger: 'change', type: 'array' },
    { type: 'array', min: 1, message: '请至少选择一个评审人', trigger: 'change' }
  ]
}

// 选择用例相关
const selectTestCaseDialogVisible = ref(false)
const availableTestCases = ref([])
const selectedTestCases = ref([])
const tempSelectedTestCases = ref([])
const isRestoringSelection = ref(false)
const testcaseSearchKeyword = ref('')
const testcaseTableRef = ref(null)
const testcaseLoading = ref(false)
const selectingAll = ref(false)
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

// 方法
const loadPlanList = async () => {
  loadingStore.showLoading()
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      size: pagination.size,
      keyword: searchKeyword.value || undefined
    }
    
    // 使用当前项目组的所有用例库ID（不受选择器影响）
    if (allTeamProjectIds.value.length > 0) {
      params.project_ids = allTeamProjectIds.value.join(',')
    }
    
    // 按项目组过滤，确保项目组隔离
    if (currentTeam.value?.id) {
      params.team_id = currentTeam.value.id
    }
    
    // 状态筛选逻辑：
    // - filterStatus === '' (默认/未选择): 显示未开始和进行中
    // - filterStatus === 'ALL': 显示所有状态
    // - 其他值: 显示对应状态
    if (filterStatus.value === '') {
      // 默认显示未开始和进行中
      params.status = 'PENDING,IN_PROGRESS'
    } else if (filterStatus.value !== 'ALL') {
      // 显示特定状态
      params.status = filterStatus.value
    }
    // 如果是 'ALL'，不添加 status 参数
    
    const res = await getReviewPlanList(params)
    if (res.code === 200) {
      planList.value = res.data.records
      pagination.total = res.data.total
    }
  } catch (error) {
    ElMessage.error('加载评审计划列表失败')
  } finally {
    loadingStore.hideLoading()
    loading.value = false
  }
}

const loadProjectList = async () => {
  try {
    const res = await getProjects({ page: 1, size: 1000 })
    if (res.code === 200) {
      projectList.value = res.data.records
    }
  } catch (error) {
    console.error('加载项目列表失败', error)
  }
}

const loadProjectMembers = async () => {
  const teamId = currentTeam.value?.id
  if (!teamId) return
  
  try {
    // 评审计划的评审人选择规则与测试计划执行人相同
    const res = await getAvailableMembersForSelection(teamId, 'executor')
    if (res.code === 200) {
      availableReviewersList.value = res.data
    }
  } catch (error) {
    console.error('加载项目成员失败', error)
    ElMessage.error('加载项目成员失败')
  }
}

// 加载当前用户角色
const loadCurrentUserRole = async () => {
  const teamId = currentTeam.value?.id
  if (!teamId) return
  
  try {
    const res = await getUserRoleInTeam(teamId)
    if (res.code === 200) {
      currentUserRole.value = res.data.role
    }
  } catch (error) {
    console.error('加载用户角色失败', error)
    currentUserRole.value = 'member'
  }
}

// 获取可选的评审人列表
const availableReviewers = computed(() => {
  return availableReviewersList.value
})

// 搜索功能相关状态
const reviewerSearchLoading = ref(false)
const reviewerSelectRef = ref(null)

// 评审人远程搜索
const handleReviewerSearch = async (query) => {
  if (!query || !query.trim()) {
    await loadProjectMembers()
    return
  }
  reviewerSearchLoading.value = true
  try {
    const teamId = currentTeam.value?.id
    if (!teamId) return
    const res = await getAvailableMembersForSelection(teamId, 'executor', query.trim())
    if (res.code === 200) {
      availableReviewersList.value = res.data
    }
  } catch (error) {
    console.error('Search reviewers failed:', error)
  } finally {
    reviewerSearchLoading.value = false
  }
}

// 通用：选中后清空 el-select 的搜索输入框
const clearSelectSearch = (selectRef) => {
  nextTick(() => {
    const el = selectRef.value?.$el
    if (!el) return
    const input = el.querySelector('.el-select__input') || el.querySelector('.el-input__inner')
    if (input) {
      const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
        window.HTMLInputElement.prototype, 'value'
      ).set
      nativeInputValueSetter.call(input, '')
      input.dispatchEvent(new Event('input', { bubbles: true }))
    }
  })
}

// 选中后清空搜索框并刷新列表
const handleReviewerChange = () => clearSelectSearch(reviewerSelectRef)

const loadAvailableTestCases = async () => {
  if (currentProjectIds.value.length === 0) {
    availableTestCases.value = []
    return
  }
  
  const ver = ++_selectorVer
  testcaseLoading.value = true
  try {
    const params = {
      page: testcasePagination.page,
      size: testcasePagination.size,
      keyword: testcaseSearchKeyword.value || undefined,
      status: 'PENDING', // 只显示待评审的用例
      module: (testcaseFilter.subModule ? `${testcaseFilter.module}/${testcaseFilter.subModule}` : testcaseFilter.module) || undefined,
      exclude_in_review: true  // 排除已在评审计划中的用例
    }
    
    // 添加用例库ID参数
    if (currentProjectIds.value.length > 0) {
      params.project_ids = currentProjectIds.value.join(',')
    }
    
    const res = await getTestCases(params)
    if (ver !== _selectorVer) return
    
    if (res.code === 200) {
      // 数据赋值前设置标志位，防止 selection-change 清空已选
      isRestoringSelection.value = true
      availableTestCases.value = res.data.records
      testcasePagination.total = res.data.total
      
      // 恢复表格的选中状态
      await nextTick()
      // 先清除所有选中状态，防止 row-key 复用导致残留勾选
      if (testcaseTableRef.value) {
        testcaseTableRef.value.clearSelection()
      }
      if (testcaseTableRef.value && tempSelectedTestCases.value.length > 0) {
        const selectedIds = new Set(tempSelectedTestCases.value.map(tc => tc.id))
        availableTestCases.value.forEach(row => {
          const shouldSelect = selectedIds.has(row.id)
          testcaseTableRef.value.toggleRowSelection(row, shouldSelect)
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

const loadModuleTree = async () => {
  if (currentProjectIds.value.length === 0) return
  
  const ver = ++_moduleTreeVer
  try {
    const projectParam = currentProjectIds.value.join(',')
    if (!projectParam) return
    
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

const toggleTestCaseModule = (modulePath) => {
  const findAndToggle = (nodes) => {
    for (const n of nodes) {
      if (n.path === modulePath) { n.expanded = !n.expanded; return true }
      if (n.children && findAndToggle(n.children)) return true
    }
    return false
  }
  findAndToggle(moduleTree.value)
}

const handleTestCaseModuleClick = (modulePath) => {
  testcaseFilter.module = modulePath
  testcaseFilter.subModule = ''
  testcasePagination.page = 1
  loadAvailableTestCases()
}

const formatSteps = (stepsJson) => {
  try {
    const steps = JSON.parse(stepsJson)
    if (Array.isArray(steps) && steps.length > 0) {
      return steps.map(s => s.step).filter(Boolean).join('; ')
    }
  } catch (e) {
    // ignore
  }
  return '-'
}

const getTestCaseStatusType = (status) => {
  const typeMap = {
    PENDING: 'warning',
    REVIEWED: 'success',
    REJECTED: 'danger',
    DEPRECATED: 'info'
  }
  return typeMap[status] || ''
}

const getTestCaseStatusText = (status) => {
  const textMap = {
    PENDING: 'Pending',
    REVIEWED: 'Reviewed',
    REJECTED: 'Not Passed',
    DEPRECATED: 'Deprecated'
  }
  return textMap[status] || status
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

const handleSearch = () => {
  pagination.page = 1
  loadPlanList()
}

const goBack = () => {
  router.push('/testcases')
}

const { scrollToTop } = useScrollToTop(tableRef, null)
const handleSizeChange = async () => {
  await loadPlanList()
  await nextTick()
  scrollToTop()
}

const handlePageChange = async () => {
  await loadPlanList()
  await nextTick()
  scrollToTop()
}

const showCreateDialog = async () => {
  if (currentProjectIds.value.length === 0) {
    ElMessage.warning(t('review.selectModuleFirst'))
    return
  }
  
  isEdit.value = false
  editId.value = null
  
  // 加载当前用户角色
  await loadCurrentUserRole()
  
  // 加载项目成员
  await loadProjectMembers()
  
  // 获取当前用户ID
  const currentUserId = JSON.parse(localStorage.getItem('user') || '{}').id
  
  // 重置表单 - 普通成员默认选择自己，组长/经理可以不选
  Object.assign(formData, {
    name: '',
    description: '',
    project_id: currentProject.value?.id,
    team_id: currentTeam.value?.id,
    reviewer_ids: [],
    start_time: null,
    end_time: null
  })
  
  selectedTestCases.value = []
  
  dialogVisible.value = true
}

const editPlan = async (row) => {
  isEdit.value = true
  editId.value = row.id
  
  // 加载当前用户角色
  await loadCurrentUserRole()
  
  // 加载项目成员
  await loadProjectMembers()
  
  Object.assign(formData, {
    name: row.name,
    description: row.description,
    project_id: row.project_id,
    team_id: row.team_id || currentTeam.value?.id,
    reviewer_ids: row.reviewer_ids || [],
    start_time: row.start_time,
    end_time: row.end_time
  })
  
  if (row.start_time && row.end_time) {
    formData.start_time = row.start_time
    formData.end_time = row.end_time
  } else {
    formData.start_time = null
    formData.end_time = null
  }
  
  dialogVisible.value = true
}

const handleDialogClose = () => {
  if (formRef.value) {
    formRef.value.resetFields()
  }
  selectedTestCases.value = []
}

const showSelectTestCaseDialog = async () => {
  selectTestCaseDialogVisible.value = true
  testcaseSearchKeyword.value = ''
  testcaseFilter.module = ''
  testcaseFilter.subModule = ''
  testcasePagination.page = 1
  // 根据已选用例恢复勾选状态
  tempSelectedTestCases.value = [...selectedTestCases.value]
  
  // 确保 teamProjects 已加载
  if (teamProjects.value.length === 0 && currentTeam.value) {
    await loadTeamProjects()
  }
  
  // 等待 Vue 渲染完成
  await nextTick()
  
  // 加载模块树
  await loadModuleTree()
  
  // 加载用例列表
  await loadAvailableTestCases()
}

const handleTestCaseSelectionChange = (selection) => {
  // 恢复选中状态期间跳过，避免清空已选
  if (isRestoringSelection.value) return
  
  // 获取当前页面的所有用例ID
  const currentPageIds = new Set(availableTestCases.value.map(tc => tc.id))
  
  // 移除当前页面的所有用例（无论是否选中）
  const otherPagesSelected = tempSelectedTestCases.value.filter(tc => !currentPageIds.has(tc.id))
  
  // 添加当前页面新选中的用例
  tempSelectedTestCases.value = [...otherPagesSelected, ...selection]
}

const selectAllTestCases = async () => {
  if (currentProjectIds.value.length === 0) {
    ElMessage.warning('请先选择用例库')
    return
  }
  
  selectingAll.value = true
  try {
    // 使用 all-ids 接口，不受后端100条分页限制
    const params = {
      keyword: testcaseSearchKeyword.value || undefined,
      status: 'PENDING',
      module: (testcaseFilter.subModule ? `${testcaseFilter.module}/${testcaseFilter.subModule}` : testcaseFilter.module) || undefined,
      exclude_in_review: true  // 排除已在评审计划中的用例
    }
    
    if (currentProjectIds.value.length > 0) {
      params.project_ids = currentProjectIds.value.join(',')
    }
    
    const res = await getAllTestCaseIds(params)
    if (res.code === 200) {
      const allRecords = res.data.records || []
      
      // 直接替换临时选择列表为所有用例（去重）
      const existingIds = new Set(tempSelectedTestCases.value.map(tc => tc.id))
      const newRecords = allRecords.filter(tc => !existingIds.has(tc.id))
      tempSelectedTestCases.value = [...tempSelectedTestCases.value, ...newRecords]
      
      // 同步表格的选中状态
      if (testcaseTableRef.value) {
        isRestoringSelection.value = true
        const selectedIds = new Set(tempSelectedTestCases.value.map(tc => tc.id))
        availableTestCases.value.forEach(row => {
          const shouldSelect = selectedIds.has(row.id)
          testcaseTableRef.value.toggleRowSelection(row, shouldSelect)
        })
        await nextTick()
        isRestoringSelection.value = false
      }
      
      ElMessage.success(`已选择 ${allRecords.length} 条用例`)
    }
  } catch (error) {
    console.error('全选失败:', error)
    ElMessage.error('全选失败')
  } finally {
    selectingAll.value = false
  }
}

const confirmSelectTestCases = () => {
  // 直接用当前选择替换，支持取消勾选
  selectedTestCases.value = [...tempSelectedTestCases.value]
  
  selectTestCaseDialogVisible.value = false
  tempSelectedTestCases.value = []
}

const removeSelectedTestCase = (index) => {
  selectedTestCases.value.splice(index, 1)
}

const submitForm = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    if (!isEdit.value && selectedTestCases.value.length === 0) {
      ElMessage.warning('请至少选择一个用例')
      return
    }
    
    submitting.value = true
    try {
      if (isEdit.value) {
        await updateReviewPlan(editId.value, formData)
        ElMessage.success('更新成功')
      } else {
        // 创建评审计划
        const res = await createReviewPlan(formData)
        // 从响应中获取计划ID
        const planId = res.data.id
        
        // 添加用例到评审计划
        if (selectedTestCases.value.length > 0) {
          const testcaseIds = selectedTestCases.value.map(tc => tc.id)
          try {
            await addTestCasesToPlan(planId, { testcase_ids: testcaseIds })
          } catch (addError) {
            console.error('添加用例失败:', addError)
            ElMessage.warning('评审计划创建成功，但添加用例时出现问题')
          }
        }
        
        ElMessage.success('创建成功')
      }
      dialogVisible.value = false
      loadPlanList()
      eventBus.emit('reviewplans-changed')
    } catch (error) {
      console.error('操作失败:', error)
      ElMessage.error(isEdit.value ? '更新失败' : '创建失败')
    } finally {
      submitting.value = false
    }
  })
}

const startReview = async (row) => {
  router.push(`/review-plans/${row.id}/execution`)
}

const handleDropdownCommand = (command, row) => {
  if (command === 'delete') {
    deletePlan(row)
  }
}

const deletePlan = (row) => {
  ElMessageBox.confirm(
    `确定要删除评审计划"${row.name}"吗？此操作不可恢复。`,
    '确认删除',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      await deleteReviewPlan(row.id)
      ElMessage.success('删除成功')
      loadPlanList()
      eventBus.emit('reviewplans-changed')
    } catch (error) {
      const errorMsg = error?.response?.data?.detail || error?.message || '删除失败'
      ElMessage.error(errorMsg)
    }
  }).catch(() => {})
}

const viewDetail = (id) => {
  router.push(`/review-plans/${id}`)
}

const exportReport = async (row, format) => {
  try {
    ElMessage.info(`正在生成${format === 'excel' ? 'Excel' : 'PDF'}报告...`)
    
    // 使用 axios 调用 API，设置 responseType 为 blob
    const response = await request({
      url: `/review-plans/${row.id}/export`,
      method: 'get',
      params: { format },
      responseType: 'blob'
    })
    
    // 从响应头获取文件名
    let filename = `评审报告_${row.name}_${new Date().getTime()}.${format === 'excel' ? 'xlsx' : 'pdf'}`
    const contentDisposition = response.headers['content-disposition']
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename\*=UTF-8''(.+)/)
      if (filenameMatch && filenameMatch[1]) {
        filename = decodeURIComponent(filenameMatch[1])
      }
    }
    
    // 创建下载链接 - 注意：response.data 才是 blob 数据
    const url = window.URL.createObjectURL(response.data)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)
    
    ElMessage.success('导出成功')
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败，请稍后重试')
  }
}

const handleExportCommand = (command, row) => {
  exportReport(row, command)
}

const formatDateTime = (dateTime) => {
  if (!dateTime) return '-'
  return new Date(dateTime).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

const formatDate = (dateTime) => {
  if (!dateTime) return '-'
  return new Date(dateTime).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  }).replace(/\//g, '-')
}

// 判断当前用户是否可以执行评审（管理员、项目组/组织负责人、或评审人）
const canReviewPlan = (row) => {
  if (isSuperAdmin.value || isAdmin.value) return true
  // 项目组负责人或组织负责人可以执行任何评审
  if (currentUserRole.value === 'leader' || currentUserRole.value === 'org_manager') return true
  const currentUserId = JSON.parse(localStorage.getItem('user') || '{}').id
  return row.reviewer_ids && row.reviewer_ids.includes(currentUserId)
}

const canEdit = (row) => {
  // 管理员可以编辑所有计划
  if (isAdmin.value) return true
  
  // 创建人可以编辑自己的计划
  const currentUserId = JSON.parse(localStorage.getItem('user')).id
  return row.created_by === currentUserId
}

const canDelete = (row) => {
  // 超管可以删除所有计划
  if (isSuperAdmin.value) return true
  
  // 管理员可以删除所有计划
  if (isAdmin.value) return true
  
  // 创建人可以删除自己的计划
  const currentUserId = JSON.parse(localStorage.getItem('user')).id
  return row.created_by === currentUserId
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

const getPassRateColor = (row) => {
  if (!row.total_testcases || row.total_testcases === 0) return '#909399'
  const passRate = (row.executed_passed_testcases || 0) / row.total_testcases
  if (passRate >= 0.9) return '#67c23a' // 绿色：90%以上
  if (passRate >= 0.7) return '#e6a23c' // 橙色：70-90%
  return '#f56c6c' // 红色：70%以下
}

// 表格高度自适应
const tableContainerRef = ref(null)
const tableHeight = ref(400)
const updateTableHeight = () => {
  nextTick(() => {
    if (tableContainerRef.value && tableContainerRef.value.clientHeight > 0) {
      tableHeight.value = tableContainerRef.value.clientHeight
    }
  })
}
let resizeObserver = null

// 同步表头和表体的滚动
const syncTableScroll = () => {
  if (tableRef.value) {
    const bodyWrapper = tableRef.value.$el.querySelector('.el-table__body-wrapper')
    const headerWrapper = tableRef.value.$el.querySelector('.el-table__header-wrapper')
    
    if (bodyWrapper && headerWrapper) {
      // 当表体滚动时，同步表头的滚动位置
      bodyWrapper.addEventListener('scroll', (e) => {
        headerWrapper.scrollLeft = e.target.scrollLeft
      })
    }
  }
}

onMounted(() => {
  loadPlanList()
  loadProjectList()
  nextTick(() => {
    updateTableHeight()
    if (tableContainerRef.value && typeof ResizeObserver !== 'undefined') {
      resizeObserver = new ResizeObserver(updateTableHeight)
      resizeObserver.observe(tableContainerRef.value)
    }
    setTimeout(updateTableHeight, 150)
  })
  window.addEventListener('resize', updateTableHeight)
  setTimeout(syncTableScroll, 100)
})

// 从缓存恢复时刷新数据（如从评审执行页返回）
onActivated(() => {
  loadPlanList()
})

// 监听用例库列表变化，自动应用偏好
watch(teamProjectList, (list) => {
  if (list && list.length > 0) {
    applyPreference(list)
  }
})

// 监听项目组变化，重新加载数据
watch(currentTeam, async () => {
  if (currentTeam.value) {
    // 项目组变化时，重置用例库选择
    resetPreference()
    loadPlanList()
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', updateTableHeight)
  if (resizeObserver) resizeObserver.disconnect()
})
</script>

<style scoped>
.review-plan-container {
  padding: 24px;
  padding-bottom: 0;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--demo-bg);
}

/* 分页器在文档流中 */
.pagination-container {
  flex-shrink: 0;
  display: flex;
  justify-content: flex-end;
  align-items: center;
  padding: 16px 20px;
  background: var(--demo-bg-card);
  border-top: 1px solid var(--demo-border);
  border-radius: 0 0 16px 16px;
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

.review-plan-container :deep(.el-card__body) {
  padding-left: 0 !important;
}

/* 表格容器 */
.table-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
  margin-top: 20px;
  background: var(--demo-bg-card);
  border-radius: 16px;
  border: 1px solid var(--demo-border);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.table-container {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.table-wrapper :deep(.el-table) {
  width: 100%;
}

/* 表格头部样式 - Demo主题 */
.table-wrapper :deep(.el-table th.el-table__cell) {
  background: #f8fafc !important;
  color: var(--demo-text-muted) !important;
  font-weight: 500 !important;
  font-size: 12px !important;
  text-transform: uppercase !important;
  letter-spacing: 0.05em !important;
  text-align: center !important;
  vertical-align: middle !important;
}

.table-wrapper :deep(.el-table th.el-table__cell .cell) {
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  width: 100% !important;
  height: 100% !important;
}

/* 表格行悬停样式 */
.table-wrapper :deep(.el-table__row:hover > td) {
  background: #f8fafc !important;
}

/* 固定列不透明背景 */
.table-wrapper :deep(.el-table td.el-table__cell) {
  background: #fff;
}

/* 确保表格内容与表头对齐 - 全部居中 */
.table-wrapper :deep(.el-table td.el-table__cell) {
  text-align: center !important;
  vertical-align: middle !important;
}

.table-wrapper :deep(.el-table td.el-table__cell .cell) {
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  width: 100% !important;
  height: 100% !important;
  gap: 8px !important;
}

/* 操作列内容居中对齐 */
.table-wrapper :deep(.el-table td.el-table__cell:last-child) {
  text-align: center !important;
}

.table-wrapper :deep(.el-table td.el-table__cell:last-child .cell) {
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  width: 100% !important;
  height: 100% !important;
  gap: 8px !important;
  margin: 0 auto !important;
  max-width: 120px !important;
}

/* 操作列按钮间距调整 */
.table-wrapper :deep(.el-table td.el-table__cell:last-child .cell .el-button) {
  margin: 0 4px !important;
}

.table-wrapper :deep(.el-table td.el-table__cell:last-child .cell .el-dropdown) {
  margin: 0 4px !important;
}

/* 表格头部 */
.table-wrapper :deep(.el-table__header-wrapper) {
  overflow: hidden;
  position: sticky;
  top: 0;
  z-index: 900;
  background: var(--demo-bg-card);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

/* 表格主体 */
.table-wrapper :deep(.el-table__body-wrapper) {
  overflow: auto;
}

/* 确保表头和表体使用相同的布局 */
.table-wrapper :deep(.el-table) {
  table-layout: fixed;
}

/* 确保表头和表体使用相同的布局和宽度 */
.table-wrapper :deep(.el-table__header) {
  table-layout: fixed;
  width: 100%;
}

.table-wrapper :deep(.el-table__body) {
  table-layout: fixed;
  width: 100%;
}

/* 同步表头和表体的滚动 */
.table-wrapper :deep(.el-table__header-wrapper) {
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.table-wrapper :deep(.el-table__header-wrapper)::-webkit-scrollbar {
  display: none;
}

/* 自定义表格容器的滚动条样式 */
.table-wrapper :deep(.el-table__body-wrapper) {
  scrollbar-width: thin;
  scrollbar-color: #cbd5e1 var(--demo-border-light);
}

.table-wrapper :deep(.el-table__body-wrapper)::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

.table-wrapper :deep(.el-table__body-wrapper)::-webkit-scrollbar-track {
  background: var(--demo-border-light);
  border-radius: 4px;
}

.table-wrapper :deep(.el-table__body-wrapper)::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}

.table-wrapper :deep(.el-table__body-wrapper)::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

/* 响应式调整 */
@media (max-width: 1440px) {
  .table-wrapper :deep(.el-table th.el-table__cell),
  .table-wrapper :deep(.el-table td.el-table__cell) {
    padding: 8px 4px !important;
  }
  
  .table-wrapper :deep(.el-table th.el-table__cell .cell),
  .table-wrapper :deep(.el-table td.el-table__cell .cell) {
    padding: 0 4px !important;
  }
}

/* 省略号文本样式 */
.ellipsis-text {
  width: 100% !important;
  max-width: 230px !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
  white-space: nowrap !important;
  text-align: center !important;
  display: inline-block !important;
}

/* 特殊处理需要左对齐的列 */
.plan-table-wrapper :deep(.el-table td.el-table__cell .single-line-ellipsis) {
  justify-content: flex-start !important;
}

.plan-table-wrapper :deep(.el-table th.el-table__cell .single-line-ellipsis) {
  justify-content: flex-start !important;
}

/* 调整操作列按钮间距和对齐 */
.plan-table-wrapper :deep(.el-table td.el-table__cell .cell) {
  gap: 8px !important;
  justify-content: center !important;
  align-items: center !important;
}

.plan-table-wrapper :deep(.el-table td.el-table__cell .cell .el-button) {
  margin-right: 4px !important;
  margin-left: 4px !important;
}

.plan-table-wrapper :deep(.el-table td.el-table__cell .cell .el-dropdown) {
  margin-left: 4px !important;
  margin-right: 4px !important;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding: 16px 20px;
  background: var(--demo-bg-card);
  border-radius: 16px;
  border: 1px solid var(--demo-border);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.left-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* 按钮样式 - Demo主题 */
.toolbar :deep(.el-button) {
  border-radius: 8px;
  font-weight: 500;
  height: 40px;
  padding: 0 16px;
  font-size: 14px;
  transition: all 0.15s;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.toolbar :deep(.el-button--primary) {
  background: var(--demo-primary);
  border: none;
}

.toolbar :deep(.el-button--primary:hover) {
  background: var(--demo-primary-hover);
}

.toolbar :deep(.el-button--default) {
  background: #ffffff;
  border: 1px solid var(--demo-border);
  color: var(--demo-text-secondary);
}

.toolbar :deep(.el-button--default:hover) {
  background: var(--demo-bg);
  border-color: #cbd5e1;
}

.search-bar {
  display: flex;
  align-items: center;
}

/* 输入框样式 - Demo主题 */
.search-bar :deep(.el-input__wrapper) {
  border-radius: 8px;
  border: 1px solid var(--demo-border);
  box-shadow: none;
  height: 40px;
}

.search-bar :deep(.el-input__wrapper:hover) {
  border-color: #cbd5e1;
}

.search-bar :deep(.el-input__wrapper.is-focus) {
  border-color: var(--demo-primary);
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.1);
}

/* 选择器样式 - Demo主题 */
.search-bar :deep(.el-select__wrapper) {
  border-radius: 8px;
  border: 1px solid var(--demo-border);
  box-shadow: none;
  min-height: 40px;
}

.search-bar :deep(.el-select__wrapper:hover) {
  border-color: #cbd5e1;
}

.search-bar :deep(.el-select__wrapper.is-focus) {
  border-color: var(--demo-primary);
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.1);
}

.testcase-section {
  margin-top: 30px;
  padding-top: 20px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.section-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--demo-text-primary);
}

.selected-count {
  font-size: 13px;
  color: var(--demo-text-muted);
  padding: 10px 15px;
  background-color: var(--demo-border-light);
  border-radius: 8px;
  border: 1px solid var(--demo-border);
}

.testcase-filter {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

/* 进度条样式优化 */
:deep(.el-progress__text) {
  display: none;
}

:deep(.el-progress-bar) {
  padding-right: 0;
  margin-right: 0;
}

/* 用例选择对话框样式 */
.testcase-select-container {
  display: flex;
  height: calc(100vh - 200px);
  border: 1px solid var(--demo-border);
  border-radius: 12px;
  overflow: visible;
}

.module-sidebar {
  width: 220px;
  border-right: 1px solid var(--demo-border);
  background-color: var(--demo-bg-card);
  display: flex;
  flex-direction: column;
  overflow: visible;
}

.module-header {
  padding: 12px 16px;
  border-bottom: 1px solid var(--demo-border-light);
  font-weight: 600;
  font-size: 12px;
  color: var(--demo-text-light);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  background-color: var(--demo-bg);
}

.module-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
}

.module-group {
  margin-bottom: 0;
}

.module-item {
  padding: 8px 12px;
  margin: 2px 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  font-size: 14px;
  color: var(--demo-text-secondary);
  transition: all 0.15s;
  user-select: none;
  border-radius: 6px;
}

.module-item:hover {
  background-color: var(--demo-bg);
}

.module-item.active {
  background-color: var(--demo-primary-light);
  color: var(--demo-primary-hover);
  font-weight: 500;
}

.module-item .expand-icon {
  margin-right: 6px;
  font-size: 12px;
  color: var(--demo-text-muted);
  flex-shrink: 0;
}

.module-content {
  flex: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
  overflow: hidden;
}

.module-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sub-module-list {
  background-color: var(--demo-bg);
}

.sub-module {
  padding-left: 40px;
  font-size: 13px;
}

.testcase-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 16px;
  overflow: hidden;
  background-color: var(--demo-bg);
}

.testcase-content .testcase-filter {
  margin-bottom: 16px;
  flex-shrink: 0;
}

/* 终极方案：直接覆盖 Element Plus 的 .cell 样式 */
.table-wrapper :deep(.el-table .el-table__cell .cell) {
  padding-left: 0 !important;
  padding-right: 0 !important;
  text-align: center !important;
}

/* 确保所有内容都居中 */
.table-wrapper :deep(.el-table .el-table__cell .cell > *) {
  text-align: center !important;
  margin: 0 auto !important;
}

/* 可点击的评审名称样式 */
.clickable-name {
  color: var(--demo-primary);
  cursor: pointer;
  transition: all 0.15s;
  display: block;
  width: 100%;
  text-align: center;
}

.clickable-name:hover {
  color: var(--demo-primary-hover);
  text-decoration: underline;
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

/* 多选框列不影响其他列对齐 */
:deep(.el-table .el-table-column--selection .cell) {
  padding: 0 !important;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 调整操作列按钮对齐 */
.table-wrapper :deep(.el-table td.el-table__cell:last-child .cell) {
  gap: 4px !important;
  justify-content: flex-start !important;
  align-items: center !important;
  padding-left: 12px !important;
}

.table-wrapper :deep(.el-table td.el-table__cell:last-child .cell .el-button) {
  margin-right: 2px !important;
  margin-left: 2px !important;
}

.table-wrapper :deep(.el-table td.el-table__cell:last-child .cell .el-dropdown) {
  margin-left: 2px !important;
  margin-right: 2px !important;
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

/* 用例库选择器样式 */
.project-filter-section {
  padding: 12px 14px;
  background: var(--demo-primary-light);
  overflow: visible;
  position: relative;
  z-index: 100;
}

.project-filter-section .section-header {
  font-weight: 600;
  font-size: 12px;
  color: var(--demo-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 10px;
}

.project-filter-content {
  display: flex;
  flex-direction: column;
  overflow: visible;
  position: relative;
}

.project-filter-content :deep(.el-radio-group) {
  display: flex;
  width: 100%;
}

.project-filter-content :deep(.el-radio-button) {
  flex: 1;
}

.project-filter-content :deep(.el-radio-button__inner) {
  width: 100%;
  padding: 6px 0;
  font-size: 12px;
}

.project-filter-content :deep(.el-select) {
  width: 100%;
}

.project-filter-content :deep(.el-select .el-input__wrapper) {
  background-color: #fff;
}

/* 进度条样式 - Demo主题 */
:deep(.el-progress-bar__outer) {
  background: var(--demo-border-light);
}

:deep(.el-progress-bar__inner) {
  background: var(--demo-primary);
}

/* 对话框样式 - Demo主题 */
:deep(.el-dialog) {
  border-radius: 16px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.12);
}

:deep(.el-dialog__header) {
  padding: 20px 24px 16px;
  border-bottom: 1px solid var(--demo-border);
}

:deep(.el-dialog__title) {
  font-size: 18px;
  font-weight: 600;
  color: var(--demo-text-primary);
}

:deep(.el-dialog__body) {
  padding: 24px;
}
</style>
