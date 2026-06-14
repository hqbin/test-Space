<template>
  <div class="execution-detail-container">
    <!-- 头部 -->
    <div class="detail-header">
      <el-button @click="goBack">
        <el-icon><ArrowLeft /></el-icon>
        {{ $t('review.back') }}
      </el-button>
      <h2 style="margin: 0 0 0 20px;">{{ planDetail.name }} - {{ $t('review.caseReview') }}</h2>
    </div>

    <!-- 主内容区域 -->
    <div class="detail-content">
      <!-- 统计卡片 -->
      <div class="stats-section-top">
        <div class="stats-cards-horizontal">
          <div 
            class="stat-card-small"
            :class="{ 'active': statusFilter === null }"
            @click="filterByStatus(null)"
          >
            <span class="stat-label-small">{{ $t('review.totalCases') }}</span>
            <span class="stat-value-small">{{ allTestcases.length }}</span>
          </div>
          <div 
            class="stat-card-small"
            :class="{ 'active': statusFilter === 'PENDING' }"
            @click="filterByStatus('PENDING')"
          >
            <span class="stat-label-small">{{ $t('review.pendingReview') }}</span>
            <span class="stat-value-small" style="color: #909399;">{{ statistics.pending }}</span>
          </div>
          <div 
            class="stat-card-small"
            :class="{ 'active': statusFilter === 'REVIEWED' }"
            @click="filterByStatus('REVIEWED')"
          >
            <span class="stat-label-small">{{ $t('review.reviewed') }}</span>
            <span class="stat-value-small" style="color: #409eff;">{{ statistics.reviewed }}</span>
          </div>
          <div 
            class="stat-card-small"
            :class="{ 'active': statusFilter === 'APPROVED' }"
            @click="filterByStatus('APPROVED')"
          >
            <span class="stat-label-small">{{ $t('review.approved') }}</span>
            <span class="stat-value-small" style="color: #67c23a;">{{ statistics.approved }}</span>
          </div>
          <div 
            class="stat-card-small"
            :class="{ 'active': statusFilter === 'REJECTED' }"
            @click="filterByStatus('REJECTED')"
          >
            <span class="stat-label-small">{{ $t('review.rejected') }}</span>
            <span class="stat-value-small" style="color: #f56c6c;">{{ statistics.rejected }}</span>
          </div>
          <div 
            class="stat-card-small"
            :class="{ 'active': statusFilter === 'DEPRECATED' }"
            @click="filterByStatus('DEPRECATED')"
          >
            <span class="stat-label-small">{{ $t('review.deprecated') }}</span>
            <span class="stat-value-small" style="color: #909399;">{{ statistics.deprecated }}</span>
          </div>
        </div>
      </div>

      <!-- 内容区域包装器 -->
      <div class="content-wrapper">
        <!-- 左侧：模块选择和用例列表 -->
        <div class="left-sidebar">
          <div class="module-selector">
            <el-tree-select
              v-model="selectedModule"
              :data="moduleTreeOptions"
              :placeholder="$t('review.selectModule')"
              @change="handleModuleChange"
              style="width: 100%;"
              check-strictly
              :default-expand-all="false"
              clearable
            />
          </div>

          <div class="testcase-list">
            <div
              v-for="testcase in filteredTestcases"
              :key="testcase.id"
              class="testcase-item"
              :class="{ active: currentTestcaseId === testcase.id, 'has-draft': testcase.pending_review_result }"
              @click="selectTestcase(testcase.id)"
            >
              <div class="testcase-title">{{ testcase.name }}</div>
              <div class="testcase-meta">
                <!-- 暂存与正式同时存在时一并展示 -->
                <template v-if="testcase.pending_review_result && testcase.review_result">
                  <el-tag
                    :type="getResultTagType(testcase.pending_review_result)"
                    effect="plain"
                    size="small"
                    style="border-style: dashed;"
                  >
                    {{ getResultText(testcase.pending_review_result) }}
                  </el-tag>
                  <el-tag
                    :type="getResultTagType(testcase.review_result)"
                    size="small"
                  >
                    {{ getResultText(testcase.review_result) }}
                  </el-tag>
                </template>
                <!-- 仅暂存：虚线边框 -->
                <template v-else-if="testcase.pending_review_result">
                  <el-tag
                    :type="getResultTagType(testcase.pending_review_result)"
                    effect="plain"
                    size="small"
                    style="border-style: dashed;"
                  >
                    {{ getResultText(testcase.pending_review_result) }}
                  </el-tag>
                </template>
                <!-- 仅正式：按官方结果展示 -->
                <template v-else>
                  <el-tag v-if="testcase.review_result" :type="getResultTagType(testcase.review_result)" size="small">{{ getResultText(testcase.review_result) }}</el-tag>
                  <el-tag v-else type="warning" size="small">{{ $t('review.pendingReview') }}</el-tag>
                </template>
              </div>
            </div>
          </div>
        </div>

        <!-- 右侧：用例详情和评审 -->
        <div class="right-content" v-if="currentTestcaseId">
          <div class="content-scroll">
            <template v-if="testcaseData.id">
              <!-- 用例信息卡片 -->
              <el-card shadow="never" class="info-card">
                <template #header>
                  <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-weight: 600; font-size: 16px;">{{ $t('review.caseInfo') }}</span>
                    <div style="display: flex; align-items: center; gap: 12px;">
                      <el-tag :type="getLevelType(testcaseData.level)">{{ testcaseData.level }}</el-tag>
                      <el-button type="primary" link @click="handleEdit">
                        <el-icon><Edit /></el-icon>
                        {{ $t('common.edit') }}
                      </el-button>
                    </div>
                  </div>
                </template>
                <el-descriptions :column="1" border>
                  <el-descriptions-item :label="$t('review.caseNumber')">{{ testcaseData.case_number }}</el-descriptions-item>
                  <el-descriptions-item :label="$t('review.caseTitle')">{{ testcaseData.name }}</el-descriptions-item>
                  <el-descriptions-item :label="$t('review.belongModule')">
                    {{ testcaseData.module }}{{ testcaseData.sub_module ? ' / ' + testcaseData.sub_module : '' }}
                  </el-descriptions-item>
                  <el-descriptions-item :label="$t('review.precondition')">
                    <div style="white-space: pre-wrap;">{{ testcaseData.precondition || '-' }}</div>
                  </el-descriptions-item>
                  <el-descriptions-item :label="$t('review.testSteps')">
                    <div v-for="(step, index) in parseSteps(testcaseData.steps)" :key="index" style="margin-bottom: 8px; white-space: pre-line;">
                      <span style="color: #4f46e5; font-weight: 500;">{{ index + 1 }}.</span> {{ step }}
                    </div>
                    <span v-if="parseSteps(testcaseData.steps).length === 0">-</span>
                  </el-descriptions-item>
                  <el-descriptions-item :label="$t('review.expectedResult')">
                    <div v-for="(result, index) in parseExpected(testcaseData.expected_result)" :key="index" style="margin-bottom: 8px; white-space: pre-line;">
                      <span style="color: #4f46e5; font-weight: 500;">{{ index + 1 }}.</span> {{ result }}
                    </div>
                    <span v-if="parseExpected(testcaseData.expected_result).length === 0">-</span>
                  </el-descriptions-item>
                  <el-descriptions-item :label="$t('review.caseRemarks')">
                    {{ testcaseData.remarks || '-' }}
                  </el-descriptions-item>
                  <el-descriptions-item v-if="testcaseData.feedback" :label="$t('review.userFeedback')">
                    <div style="white-space: pre-wrap; color: #e6a23c;">{{ testcaseData.feedback }}</div>
                  </el-descriptions-item>
                </el-descriptions>
              </el-card>

              <!-- 评审表单 -->
              <el-card shadow="never" class="execution-card">
                <template #header>
                  <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                      <span style="font-weight: 600; font-size: 16px;">{{ $t('review.reviewOperation') }}</span>
                      <el-button link type="warning" @click="openCommentDialog" style="margin-left: 8px;">
                        <el-icon><ChatDotRound /></el-icon>
                        <span v-if="commentCount > 0">({{ commentCount }})</span>
                        <span v-else>评论</span>
                      </el-button>
                    </div>
                    <div style="display: flex; align-items: center; gap: 6px; flex-wrap: wrap; justify-content: flex-end;">
                      <!-- 暂存与正式同时存在时一并展示 -->
                      <template v-if="reviewData.pending_review_result && reviewData.review_result">
                        <el-tag
                          :type="getResultTagType(reviewData.pending_review_result)"
                          effect="plain"
                          style="border-style: dashed; font-weight: 500;"
                        >
                          {{ getResultText(reviewData.pending_review_result) }}
                        </el-tag>
                        <el-tag :type="getResultTagType(reviewData.review_result)">
                          {{ getResultText(reviewData.review_result) }}
                        </el-tag>
                      </template>
                      <!-- 仅暂存：虚线边框 -->
                      <template v-else-if="reviewData.pending_review_result">
                        <el-tag
                          :type="getResultTagType(reviewData.pending_review_result)"
                          effect="plain"
                          style="border-style: dashed; font-weight: 500;"
                        >
                          {{ getResultText(reviewData.pending_review_result) }}
                        </el-tag>
                        <span v-if="reviewData.pending_reviewed_at" style="color: #94a3b8; font-size: 12px;">
                          {{ formatDateTime(reviewData.pending_reviewed_at) }}
                        </span>
                      </template>
                      <!-- 仅正式：按官方结果展示 -->
                      <template v-else>
                        <el-tag v-if="reviewData.review_result" :type="getResultTagType(reviewData.review_result)">{{ getResultText(reviewData.review_result) }}</el-tag>
                        <el-tag v-else type="warning">{{ $t('review.pendingReview') }}</el-tag>
                        <span v-if="reviewData.reviewed_at" style="margin-left: 10px; color: #64748b; font-size: 12px;">
                          {{ formatDateTime(reviewData.reviewed_at) }}
                        </span>
                      </template>
                    </div>
                  </div>
                </template>
                <el-form :model="reviewForm" label-width="100px">
                  <el-form-item :label="$t('review.reviewComment')">
                    <el-input
                      v-model="reviewForm.review_comment"
                      type="textarea"
                      :rows="4"
                      :placeholder="$t('review.reviewCommentPlaceholder')"
                      maxlength="500"
                      show-word-limit
                    />
                  </el-form-item>
                  <el-form-item>
                    <el-button type="success" @click="submitReview('APPROVED')" :loading="submitting">
                      <el-icon><Select /></el-icon>
                      {{ $t('review.pass') }}
                    </el-button>
                    <el-button type="danger" @click="submitReview('REJECTED')" :loading="submitting">
                      <el-icon><CloseBold /></el-icon>
                      {{ $t('review.reject') }}
                    </el-button>
                    <el-button type="info" @click="submitReview('DEPRECATED')" :loading="submitting">
                      {{ $t('review.deprecate') }}
                    </el-button>
                    <el-button @click="goToPrevious" :disabled="!hasPrevious" style="margin-left: 12px;">
                      <el-icon><ArrowLeft /></el-icon>
                      {{ $t('review.previous') }}
                    </el-button>
                    <el-button @click="goToNext" :disabled="!hasNext">
                      {{ $t('review.next') }}
                      <el-icon><ArrowRight /></el-icon>
                    </el-button>
                  </el-form-item>
                </el-form>
              </el-card>
            </template>
          </div>
        </div>

        <!-- 右侧空状态 -->
        <div class="right-content empty-state" v-else>
          <el-empty :description="$t('review.selectCaseFromLeft')" />
        </div>
      </div>

      <!-- 编辑用例对话框 -->
      <el-dialog
        v-model="editDialogVisible"
        :title="$t('testcase.editCase')"
        width="900px"
        :close-on-click-modal="false"
        @closed="handleEditDialogClosed"
      >
        <el-form :model="editForm" label-width="130px" label-position="left">
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item :label="$t('testcase.caseLibrary')" required>
                <el-select
                  v-model="editForm.primary_project_id"
                  :placeholder="$t('testcase.selectProject')"
                  style="width: 100%"
                  filterable
                  @change="handleEditFormProjectChange"
                >
                  <el-option
                    v-for="project in teamProjectList"
                    :key="project.id"
                    :label="project.name"
                    :value="project.id"
                  />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item :label="$t('testcase.moduleBelongs')" required>
                <el-tree-select
                  v-model="editForm.module"
                  :data="editFormModuleTree"
                  :props="{ label: 'label', value: 'value', children: 'children' }"
                  :placeholder="$t('testcase.selectProject')"
                  filterable
                  :filter-node-method="filterModuleNode"
                  check-strictly
                  :render-after-expand="false"
                  style="width: 100%"
                  :disabled="!editForm.primary_project_id"
                  popper-class="module-tree-select-dropdown"
                />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item :label="$t('testcase.caseNumber')">
                <el-input
                  v-model="editForm.case_number"
                  :placeholder="$t('testcase.inputModule')"
                  :disabled="true"
                />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item :label="$t('testcase.type')" required>
                <el-select
                  v-model="editForm.case_type"
                  :placeholder="$t('testcase.allTypes')"
                  style="width: 100%"
                  popper-class="module-select-dropdown"
                  :fit-input-width="true"
                >
                  <el-option :label="$t('testcase.typeFunctional')" value="COMMON" />
                  <el-option :label="$t('testcase.typePerformance')" value="PERFORMANCE" />
                  <el-option :label="$t('testcase.typeSecurity')" value="SECURITY" />
                  <el-option :label="$t('testcase.typeInterface')" value="INTERFACE" />
                  <el-option :label="$t('testcase.typeInstall')" value="INSTALL" />
                  <el-option :label="$t('testcase.typeConfig')" value="CONFIG" />
                  <el-option :label="$t('testcase.typeOther')" value="OTHER" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>

          <el-form-item :label="$t('testcase.name')" required>
            <el-input
              v-model="editForm.name"
              :placeholder="$t('testcase.inputName')"
            />
          </el-form-item>

          <el-form-item :label="$t('testcase.precondition')">
            <el-input
              v-model="editForm.precondition"
              type="textarea"
              :rows="2"
              :placeholder="$t('testcase.inputPrecondition')"
            />
          </el-form-item>

          <el-form-item :label="$t('testcase.steps')" required>
            <StepEditor v-model="editForm.steps" />
          </el-form-item>

          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item :label="$t('testcase.level')" required>
                <el-select v-model="editForm.level" :placeholder="$t('testcase.selectLevel')" style="width: 100%;">
                  <el-option :label="'L1 - ' + $t('testcase.levelHighest')" value="L1">
                    <el-tag type="danger" size="small">L1</el-tag>
                    <span style="margin-left: 8px;">{{ $t('testcase.levelHighest') }}</span>
                  </el-option>
                  <el-option :label="'L2 - ' + $t('testcase.levelHigh')" value="L2">
                    <el-tag type="warning" size="small">L2</el-tag>
                    <span style="margin-left: 8px;">{{ $t('testcase.levelHigh') }}</span>
                  </el-option>
                  <el-option :label="'L3 - ' + $t('testcase.levelMedium')" value="L3">
                    <el-tag type="primary" size="small">L3</el-tag>
                    <span style="margin-left: 8px;">{{ $t('testcase.levelMedium') }}</span>
                  </el-option>
                  <el-option :label="'L4 - ' + $t('testcase.levelLow')" value="L4">
                    <el-tag type="info" size="small">L4</el-tag>
                    <span style="margin-left: 8px;">{{ $t('testcase.levelLow') }}</span>
                  </el-option>
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item :label="$t('testcase.automation')">
                <el-select v-model="editForm.automation" :placeholder="$t('testcase.selectAutomation')" clearable style="width: 100%;">
                  <el-option :label="$t('testcase.automationY')" value="Y" />
                  <el-option :label="$t('testcase.automationD')" value="D" />
                  <el-option :label="$t('testcase.automationNHwPhysical')" value="N-HW_PHYSICAL" />
                  <el-option :label="$t('testcase.automationNVisualJudge')" value="N-VISUAL_JUDGE" />
                  <el-option :label="$t('testcase.automationNBootProcess')" value="N-BOOT_PROCESS" />
                  <el-option :label="$t('testcase.automationNMediaPlay')" value="N-MEDIA_PLAY" />
                  <el-option :label="$t('testcase.automationNOtaUpgrade')" value="N-OTA_UPGRADE" />
                  <el-option :label="$t('testcase.automationNDataConfig')" value="N-DATA_CONFIG" />
                  <el-option :label="$t('testcase.automationNLogCheck')" value="N-LOG_CHECK" />
                  <el-option :label="$t('testcase.automationNBackendConfig')" value="N-BACKEND_CONFIG" />
                  <el-option :label="$t('testcase.automationNDataDynamic')" value="N-DATA_DYNAMIC" />
                  <el-option :label="$t('testcase.automationNSpecial')" value="N-OTHER_SPECIAL" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>

          <el-form-item :label="$t('testcase.remarks')">
            <el-input
              v-model="editForm.remarks"
              type="textarea"
              :rows="2"
              :placeholder="$t('testcase.inputRemarks')"
            />
          </el-form-item>
        </el-form>

        <template #footer>
          <el-button @click="editDialogVisible = false">{{ $t('common.cancel') }}</el-button>
          <el-button type="primary" @click="handleSubmit" :loading="editSubmitting">
            {{ $t('common.confirm') }}
          </el-button>
        </template>
      </el-dialog>

      <!-- 评论对话框 -->
      <el-dialog v-model="commentDialogVisible" :title="testcaseData.name + ' - 评论'" width="500px" destroy-on-close>
        <div class="comment-dialog-content">
          <div class="comment-input-section">
            <el-input v-model="newComment" type="textarea" :rows="3" placeholder="请输入评论内容" />
            <el-button type="primary" @click="submitComment" :loading="submittingComment" style="margin-top: 10px;">
              发表评论
            </el-button>
          </div>
          <div class="comment-list" v-loading="commentLoading">
            <div v-if="!testcaseComments.length" class="empty-comments">
              <el-empty description="暂无评论" :image-size="60" />
            </div>
            <div v-else v-for="comment in testcaseComments" :key="comment.id" class="comment-item">
              <div class="comment-header">
                <span class="comment-author">{{ comment.author_name }}</span>
                <span class="comment-time">{{ formatDateTime(comment.created_at) }}</span>
              </div>
              <div class="comment-content">{{ comment.content }}</div>
            </div>
          </div>
        </div>
        <template #footer>
          <el-button @click="commentDialogVisible = false">关闭</el-button>
        </template>
      </el-dialog>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, watch, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, ArrowRight, Select, CloseBold, ChatDotRound, Edit } from '@element-plus/icons-vue'
import { getTestCaseReviewDetail, reviewTestCase, getPlanTestCases, getReviewPlanDetail } from '@/api/reviewPlan'
import { updateTestCase } from '@/api/testcase'
import { getModuleTree } from '@/api/module'
import { getComments, createComment } from '@/api/comment.js'
import { useI18n } from 'vue-i18n'
import { useTeam } from '@/composables/useTeam'
import StepEditor from '@/components/StepEditor.vue'

const { t } = useI18n()
const router = useRouter()
const route = useRoute()
const { teamProjects, loadTeamProjects } = useTeam()

const planId = route.params.planId
const currentTestcaseId = ref(parseInt(route.params.testcaseId))

const planDetail = ref({})
const testcaseData = ref({ id: null })
const reviewData = ref({})
const submitting = ref(false)

// 编辑相关
const editDialogVisible = ref(false)
const editSubmitting = ref(false)
const editFormModuleTree = ref([])
const teamProjectList = computed(() => teamProjects.value || [])

const editForm = reactive({
  id: null,
  case_number: '',
  module: '',
  name: '',
  case_type: 'COMMON',
  precondition: '',
  steps: [{ step: '', expected: '' }],
  expected_result: '',
  level: 'L3',
  remarks: '',
  automation: null,
  status: 'PENDING',
  primary_project_id: null
})

// 评论相关
const testcaseComments = ref([])
const commentCount = ref(0)
const commentDialogVisible = ref(false)
const newComment = ref('')
const commentLoading = ref(false)
const submittingComment = ref(false)

const reviewForm = reactive({
  review_comment: ''
})

// 模块和用例列表
const selectedModule = ref(route.query.module || '')
const allTestcases = ref([])
const statusFilter = ref(null)

// 统计数据
const statistics = computed(() => {
  let testcases = allTestcases.value
  if (selectedModule.value) {
    const filterPath = selectedModule.value
    testcases = testcases.filter(tc => {
      const raw = tc.module || ''
      return raw === filterPath || raw.startsWith(filterPath + '/')
    })
  }
  let approved = 0, rejected = 0, deprecated = 0, executed = 0
  // 以"执行"为口径：有效结果 = 暂存结果（若有），否则官方结果
  const effective = (tc) => tc.pending_review_result || tc.review_result
  testcases.forEach(tc => {
    const r = effective(tc)
    if (r === 'APPROVED') approved++
    else if (r === 'REJECTED') rejected++
    else if (r === 'DEPRECATED') deprecated++
    if (tc.pending_review_result || tc.review_status !== 'PENDING') executed++
  })
  const pending = testcases.length - executed
  return {
    total: testcases.length,
    approved,
    rejected,
    deprecated,
    pending,
    executed,
    reviewed: executed
  }
})

// 模块树选项（用于 el-tree-select，支持任意深度）
const moduleTreeOptions = computed(() => {
  const options = [{ value: '', label: t('review.allModules'), children: [] }]
  
  const root = { children: new Map() }
  allTestcases.value.forEach(tc => {
    if (!tc.module) return
    const raw = tc.module
    const parts = raw.split('/').map(p => p.trim()).filter(Boolean)
    if (parts.length === 0) return
    
    let current = root
    let pathSoFar = ''
    for (const part of parts) {
      pathSoFar = pathSoFar ? pathSoFar + '/' + part : part
      if (!current.children.has(part)) {
        current.children.set(part, { name: part, path: pathSoFar, children: new Map() })
      }
      current = current.children.get(part)
    }
  })
  
  const toOptions = (map, isRoot) => {
    return Array.from(map.values())
      .sort((a, b) => a.name.localeCompare(b.name, 'zh-CN'))
      .map(node => {
        return {
          value: isRoot ? node.name : node.path,
          label: node.name,
          children: node.children.size > 0 ? toOptions(node.children, false) : []
        }
      })
  }
  
  if (root.children.size > 0) {
    options.push(...toOptions(root.children, true))
  }
  
  return options
})

// 筛选后的用例列表
const filteredTestcases = computed(() => {
  let list = allTestcases.value
  if (selectedModule.value) {
    const filterPath = selectedModule.value
    list = list.filter(tc => {
      const raw = tc.module || ''
      return raw === filterPath || raw.startsWith(filterPath + '/')
    })
  }
  if (statusFilter.value) {
    if (statusFilter.value === 'REVIEWED') {
      // 已执行：有暂存或已提交
      list = list.filter(tc => tc.pending_review_result || tc.review_status !== 'PENDING')
    } else if (statusFilter.value === 'PENDING') {
      // 未执行：既无暂存也未提交
      list = list.filter(tc => !tc.pending_review_result && tc.review_status === 'PENDING')
    } else {
      // 结果筛选：以"执行"为口径（暂存优先）
      const effective = (tc) => tc.pending_review_result || tc.review_result
      list = list.filter(tc => effective(tc) === statusFilter.value)
    }
  }
  return list
})

// 上一个/下一个导航
const currentIndex = computed(() => filteredTestcases.value.findIndex(tc => tc.id === currentTestcaseId.value))
const hasPrevious = computed(() => currentIndex.value > 0)
const hasNext = computed(() => currentIndex.value < filteredTestcases.value.length - 1)

const goToPrevious = () => {
  if (hasPrevious.value) {
    selectTestcase(filteredTestcases.value[currentIndex.value - 1].id)
  }
}
const goToNext = () => {
  if (hasNext.value) {
    selectTestcase(filteredTestcases.value[currentIndex.value + 1].id)
  }
}

const filterByStatus = (status) => {
  statusFilter.value = status
}

const handleModuleChange = () => {
  // 模块变化后，如果当前用例不在筛选结果中，选择第一个
  if (filteredTestcases.value.length > 0 && !filteredTestcases.value.find(tc => tc.id === currentTestcaseId.value)) {
    selectTestcase(filteredTestcases.value[0].id)
  }
}

const selectTestcase = async (testcaseId) => {
  currentTestcaseId.value = testcaseId
  // 静默更新URL，不触发Vue Router路由变化，避免组件重新渲染
  const newPath = `/review-plans/${planId}/testcases/${testcaseId}`
  const queryStr = new URLSearchParams(route.query).toString()
  window.history.replaceState({}, '', queryStr ? `${newPath}?${queryStr}` : newPath)
  await loadTestCaseDetail()
  
  // 加载评论数量
  await loadCommentCount(testcaseId)
  
  // 滚动到选中的用例
  await nextTick()
  scrollToSelectedTestcase()
}

// 滚动到选中的用例
const scrollToSelectedTestcase = async () => {
  await nextTick()
  const activeItem = document.querySelector('.testcase-item.active')
  
  if (activeItem) {
    // 使用 scrollIntoView 让元素可见，自动处理各种边界情况
    activeItem.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
  }
}

// 加载计划详情
const loadPlanDetail = async () => {
  try {
    const res = await getReviewPlanDetail(planId)
    if (res.code === 200) {
      planDetail.value = res.data
    }
  } catch (error) {
    console.error('加载评审计划详情失败', error)
  }
}

// 加载所有用例列表（用于侧边栏）
const loadAllTestcases = async () => {
  try {
    const res = await getPlanTestCases(planId, { page: 1, size: 10000 })
    if (res.code === 200) {
      // 保持后端返回的排序（module_sort + sort_order），不在前端重新排序
      allTestcases.value = res.data.records || []
    }
  } catch (error) {
    console.error('加载用例列表失败', error)
  }
}

// 加载用例详情
const loadTestCaseDetail = async () => {
  try {
    const res = await getTestCaseReviewDetail(planId, currentTestcaseId.value)
    if (res.code === 200) {
      // 直接替换整个对象，不先清空，避免骨架屏闪烁
      testcaseData.value = res.data.testcase
      reviewData.value = res.data.review
      // 暂存优先：表单回填时优先使用 pending_review_comment，未填时 fallback 到 review_comment
      reviewForm.review_comment = res.data.review.pending_review_comment
        || res.data.review.review_comment
        || ''
    }
  } catch (error) {
    ElMessage.error(t('review.loadCaseDetailFailed'))
    console.error(error)
  }
}

// 提交评审（写入暂存，不直接更新 testcase.status；待"提交评审计划"时统一落库）
const submitReview = async (result) => {
  submitting.value = true
  try {
    await reviewTestCase(planId, currentTestcaseId.value, {
      result: result,
      comment: reviewForm.review_comment
    })
    ElMessage.info('已记录，提交评审计划后生效')

    // 仅更新本地的暂存字段；不动 testcase.status 与正式 review_*
    reviewData.value.pending_review_result = result
    reviewData.value.pending_review_comment = reviewForm.review_comment
    reviewData.value.pending_reviewer_id = reviewData.value.pending_reviewer_id || null
    reviewData.value.pending_reviewed_at = new Date().toISOString()

    // 同步侧边栏的暂存字段
    const tc = allTestcases.value.find(t => t.id === currentTestcaseId.value)
    if (tc) {
      tc.pending_review_result = result
      tc.pending_review_comment = reviewForm.review_comment
      tc.pending_reviewer_id = tc.pending_reviewer_id || null
      tc.pending_reviewed_at = new Date().toISOString()
    }

    // 自动跳转到下一个
    if (hasNext.value) {
      goToNext()
    } else {
      // 重新加载当前用例详情以更新状态
      await loadTestCaseDetail()
    }
  } catch (error) {
    ElMessage.error(t('review.reviewFailed'))
    console.error(error)
  } finally {
    submitting.value = false
  }
}

const goBack = () => {
  const query = {}
  if (route.query.page) query.page = route.query.page
  router.push({ path: `/review-plans/${planId}/execution`, query })
}

const getLevelType = (level) => {
  if (!level) return 'info'
  const l = level.toUpperCase()
  if (l === 'P0' || l === 'HIGH') return 'danger'
  if (l === 'P1' || l === 'MEDIUM') return 'warning'
  return 'info'
}

// 取有效评审结果：暂存优先，否则官方
const getEffectiveResult = (item) => {
  if (!item) return null
  return item.pending_review_result || item.review_result || null
}

// 评审结果 -> Element Plus tag 类型
const getResultTagType = (result) => {
  if (result === 'APPROVED') return 'success'
  if (result === 'REJECTED') return 'danger'
  if (result === 'DEPRECATED') return 'info'
  return 'warning'
}

// 评审结果 -> 简短中文文案（用于暂存显示）
const getResultText = (result) => {
  if (result === 'APPROVED') return '已通过'
  if (result === 'REJECTED') return '未通过'
  if (result === 'DEPRECATED') return '已废弃'
  return '待评审'
}

const formatDateTime = (dateTime) => {
  if (!dateTime) return '-'
  return new Date(dateTime).toLocaleString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit'
  })
}

// 评论相关方法
const loadCommentCount = async (testcaseId) => {
  try {
    const res = await getComments('review_testcase', testcaseId, false)
    if (res.code === 200) {
      testcaseComments.value = res.data || []
      commentCount.value = (res.data || []).length
    }
  } catch (e) {
    commentCount.value = 0
  }
}

const openCommentDialog = async () => {
  if (!testcaseData.value.id) return
  commentDialogVisible.value = true
  newComment.value = ''
  await loadCommentCount(testcaseData.value.id)
}

const submitComment = async () => {
  if (!newComment.value.trim()) {
    ElMessage.warning('请输入评论内容')
    return
  }
  if (!testcaseData.value.id) return
  
  submittingComment.value = true
  try {
    await createComment({
      entity_type: 'review_testcase',
      entity_id: testcaseData.value.id,
      content: newComment.value.trim(),
      parent_id: null
    })
    ElMessage.success('评论成功')
    newComment.value = ''
    await loadCommentCount(testcaseData.value.id)
  } catch (error) {
    ElMessage.error('评论失败')
  } finally {
    submittingComment.value = false
  }
}

// 编辑相关函数
const handleEdit = async () => {
  if (!testcaseData.value.id) return

  // 确保 teamProjects 已加载
  if (teamProjectList.value.length === 0) {
    await loadTeamProjects()
  }

  const row = testcaseData.value
  editForm.id = row.id
  editForm.case_number = row.case_number || ''
  editForm.module = row.module || ''
  editForm.name = row.name
  editForm.case_type = row.case_type || 'COMMON'
  editForm.precondition = row.precondition || ''

  // 解析步骤数据
  try {
    const parsed = JSON.parse(row.steps)
    if (Array.isArray(parsed) && parsed.length > 0) {
      editForm.steps = parsed.map(item => {
        let stepText = String(item.step || '').trim()
        let expectedText = String(item.expected || '').trim()

        // 使用循环移除所有开头的序号
        while (/^(\d+)(?:[。、]|\.)(?!\d)\s*/.test(stepText)) {
          stepText = stepText.replace(/^(\d+)(?:[。、]|\.)(?!\d)\s*/, '')
        }
        while (/^(\d+)(?:[。、]|\.)(?!\d)\s*/.test(expectedText)) {
          expectedText = expectedText.replace(/^(\d+)(?:[。、]|\.)(?!\d)\s*/, '')
        }

        return {
          step: stepText,
          expected: expectedText
        }
      })
    } else {
      editForm.steps = [{ step: row.steps || '', expected: row.expected_result || '' }]
    }
  } catch (e) {
    editForm.steps = [{ step: row.steps || '', expected: row.expected_result || '' }]
  }

  editForm.expected_result = row.expected_result || ''
  editForm.level = row.level || 'L3'
  editForm.remarks = row.remarks || ''
  editForm.automation = row.automation || null
  editForm.status = row.status || 'PENDING'
  editForm.primary_project_id = row.primary_project_id || row.project_id

  // 加载该用例库的模块树
  loadEditFormModuleTree(editForm.primary_project_id)

  editDialogVisible.value = true
}

// 加载编辑表单的模块树
const loadEditFormModuleTree = async (projectId) => {
  if (!projectId) {
    editFormModuleTree.value = []
    return
  }
  try {
    const res = await getModuleTree(projectId)
    editFormModuleTree.value = buildFormTreeData(res.data || [])
  } catch (error) {
    console.error('加载表单模块树失败:', error)
    editFormModuleTree.value = []
  }
}

// 将后端模块树转换为 el-tree-select 需要的格式
const buildFormTreeData = (nodes, parentPath = '') => {
  return nodes.map(node => {
    const path = parentPath ? `${parentPath}/${node.name}` : node.name
    const item = {
      label: node.name,
      value: path,
      children: []
    }
    if (node.children && node.children.length > 0) {
      item.children = buildFormTreeData(node.children, path)
    }
    return item
  })
}

// 模块树搜索过滤
const filterModuleNode = (value, data) => {
  if (!value) return true
  return data.label.toLowerCase().includes(value.toLowerCase())
}

// 切换用例库时清空已选模块
const handleEditFormProjectChange = () => {
  editForm.module = ''
}

// 编辑对话框关闭
const handleEditDialogClosed = () => {
  editForm.id = null
  editForm.case_number = ''
  editForm.module = ''
  editForm.name = ''
  editForm.case_type = 'COMMON'
  editForm.precondition = ''
  editForm.steps = [{ step: '', expected: '' }]
  editForm.expected_result = ''
  editForm.level = 'L3'
  editForm.remarks = ''
  editForm.automation = null
  editForm.status = 'PENDING'
  editForm.primary_project_id = null
}

// 提交编辑
const handleSubmit = async () => {
  // 验证必填字段
  if (!editForm.module || !editForm.name || !editForm.level) {
    ElMessage.warning(t('testcase.fillRequiredFields'))
    return
  }

  // 验证步骤
  if (!editForm.steps || editForm.steps.length === 0) {
    ElMessage.warning(t('testcase.addStep'))
    return
  }

  // 检查步骤是否至少有一个字段填写了
  const hasEmptyStep = editForm.steps.some(s => !s.step && !s.expected)
  if (hasEmptyStep) {
    ElMessage.warning(t('testcase.stepContentRequired'))
    return
  }

  editSubmitting.value = true
  try {
    // 将步骤数组转换为JSON字符串
    const stepsJson = JSON.stringify(editForm.steps)

    // 生成纯文本格式的预期结果
    const expectedText = editForm.steps.map((s, i) => {
      let expected = String(s.expected || '').trim()
      expected = expected.replace(/^(\d+)(?:[。、]|\.)(?!\d)\s*/, '')
      return `${i + 1}. ${expected}`
    }).join('\n')

    // 只提交后端需要的字段，排除 id 等不必要的字段
    const submitData = {
      primary_project_id: editForm.primary_project_id,
      case_number: editForm.case_number,
      module: editForm.module,
      name: editForm.name,
      case_type: editForm.case_type || 'COMMON',
      precondition: editForm.precondition || '',
      steps: stepsJson,
      expected_result: expectedText,
      level: editForm.level,
      remarks: editForm.remarks || '',
      automation: editForm.automation || null,
      status: editForm.status || 'PENDING',
      tags: null,
      archive_source: ''
    }

    await updateTestCase(editForm.id, submitData)
    ElMessage.success(t('testcase.updateSuccess'))

    editDialogVisible.value = false

    // 重新加载用例详情
    await loadTestCaseDetail()

    // 更新侧边栏中当前用例的信息
    const tc = allTestcases.value.find(t => t.id === currentTestcaseId.value)
    if (tc) {
      tc.name = editForm.name
      tc.module = editForm.module
      // 编辑后：服务端会把"未完成评审"中的正式与暂存都重置为 PENDING
      tc.review_status = 'PENDING'
      tc.pending_review_result = null
      tc.pending_review_comment = null
      tc.pending_reviewer_id = null
      tc.pending_reviewed_at = null
    }
  } catch (error) {
    let errorMsg = t('testcase.operationFailed')
    if (error.response) {
      const detail = error.response.data?.detail
      if (detail) {
        errorMsg = typeof detail === 'string' ? detail : JSON.stringify(detail)
      }
    } else if (error.message) {
      errorMsg = error.message
    }
    ElMessage.error(errorMsg)
  } finally {
    editSubmitting.value = false
  }
}

// 解析步骤
const parseSteps = (stepsText) => {
  if (!stepsText) return []
  if (Array.isArray(stepsText)) {
    return stepsText.map(item => {
      let text = typeof item === 'object' && item !== null ? String(item.step || '').trim() : String(item).trim()
      while (/^(\d+)(?:[。、]|\.)(?!\d)\s*/.test(text)) text = text.replace(/^(\d+)(?:[。、]|\.)(?!\d)\s*/, '')
      return text.trim()
    }).filter(t => t)
  }
  const textStr = String(stepsText).trim()
  if (!textStr) return []
  try {
    const parsed = JSON.parse(textStr)
    if (Array.isArray(parsed)) {
      return parsed.map(item => {
        let text = typeof item === 'object' && item !== null ? String(item.step || '').trim() : String(item).trim()
        while (/^(\d+)(?:[。、]|\.)(?!\d)\s*/.test(text)) text = text.replace(/^(\d+)(?:[。、]|\.)(?!\d)\s*/, '')
        return text.trim()
      }).filter(t => t)
    }
  } catch (e) { /* ignore */ }
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
  if (Array.isArray(expectedText)) {
    return expectedText.map(item => {
      let text = typeof item === 'object' && item !== null ? String(item.expected || '').trim() : String(item).trim()
      while (/^(\d+)(?:[。、]|\.)(?!\d)\s*/.test(text)) text = text.replace(/^(\d+)(?:[。、]|\.)(?!\d)\s*/, '')
      return text.trim()
    }).filter(t => t)
  }
  const textStr = String(expectedText).trim()
  if (!textStr) return []
  try {
    const parsed = JSON.parse(textStr)
    if (Array.isArray(parsed)) {
      return parsed.map(item => {
        let text = typeof item === 'object' && item !== null ? String(item.expected || '').trim() : String(item).trim()
        while (/^(\d+)(?:[。、]|\.)(?!\d)\s*/.test(text)) text = text.replace(/^(\d+)(?:[。、]|\.)(?!\d)\s*/, '')
        return text.trim()
      }).filter(t => t)
    }
  } catch (e) { /* ignore */ }
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

onMounted(async () => {
  // 并行加载独立数据
  await Promise.all([loadPlanDetail(), loadAllTestcases()])
  await loadTestCaseDetail()
  // 加载评论数量
  await loadCommentCount(currentTestcaseId.value)
})
</script>

<style scoped>
.execution-detail-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--demo-bg);
  padding: 10px 20px 0 20px;
  overflow: hidden;
}

.detail-header {
  display: flex;
  align-items: center;
  padding: 12px 20px;
  background: var(--demo-bg-card);
  border: 1px solid var(--demo-border);
  border-radius: 12px;
  margin-bottom: 12px;
  flex-shrink: 0;
}

.detail-header h2 {
  font-size: 18px;
  font-weight: 600;
  color: var(--demo-text-primary);
}

.detail-header :deep(.el-button) {
  border-radius: 8px;
  font-weight: 500;
  height: 36px;
  padding: 0 14px;
  background: #fff;
  border: 1px solid var(--demo-border);
  color: var(--demo-text-secondary);
}

.detail-header :deep(.el-button:hover) {
  background: var(--demo-bg);
  border-color: #cbd5e1;
}

.detail-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 统计卡片 */
.stats-section-top {
  flex-shrink: 0;
  margin-bottom: 12px;
}

.stats-cards-horizontal {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.stat-card-small {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  background: var(--demo-bg-card);
  border: 1px solid var(--demo-border);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.15s;
}

.stat-card-small:hover {
  background: var(--demo-border-light);
  transform: translateY(-1px);
}

.stat-card-small.active {
  background: var(--demo-primary-light, rgba(79, 70, 229, 0.08));
  border-color: var(--demo-primary, #4f46e5);
}

.stat-label-small {
  font-size: 12px;
  color: var(--demo-text-muted);
  white-space: nowrap;
}

.stat-value-small {
  font-size: 16px;
  font-weight: 600;
  color: var(--demo-text-primary);
}

/* 内容区域 */
.content-wrapper {
  flex: 1;
  display: flex;
  gap: 12px;
  overflow: hidden;
}

/* 左侧侧边栏 */
.left-sidebar {
  width: 280px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: var(--demo-bg-card);
  border: 1px solid var(--demo-border);
  border-radius: 12px;
  overflow: hidden;
}

.module-selector {
  padding: 12px;
  border-bottom: 1px solid var(--demo-border);
  flex-shrink: 0;
}

.module-selector :deep(.el-tree-select) {
  width: 100%;
}

.module-selector :deep(.el-input__wrapper) {
  border-radius: 8px;
}

.testcase-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.testcase-list::-webkit-scrollbar {
  width: 6px;
}

.testcase-list::-webkit-scrollbar-track {
  background: transparent;
}

.testcase-list::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

.testcase-item {
  padding: 10px 12px;
  margin-bottom: 4px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s;
  border: 1px solid transparent;
}

.testcase-item:hover {
  background: var(--demo-bg);
  border-color: var(--demo-border-light);
}

.testcase-item.active {
  background: var(--demo-primary-light, rgba(79, 70, 229, 0.08));
  border-color: var(--demo-primary, #4f46e5);
}

.testcase-title {
  font-size: 13px;
  color: var(--demo-text-primary);
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  margin-bottom: 6px;
  transition: color 0.15s;
}

.testcase-item:hover .testcase-title,
.testcase-item.active .testcase-title {
  color: var(--demo-primary, #4f46e5);
}

.testcase-meta {
  display: flex;
  align-items: center;
  gap: 6px;
}

/* 右侧内容 */
.right-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--demo-bg-card);
  border: 1px solid var(--demo-border);
  border-radius: 12px;
}

.right-content.empty-state {
  justify-content: center;
  align-items: center;
}

.content-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.content-scroll::-webkit-scrollbar {
  width: 6px;
}

.content-scroll::-webkit-scrollbar-track {
  background: transparent;
}

.content-scroll::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

.info-card {
  margin-bottom: 16px;
}

.info-card :deep(.el-card__header) {
  padding: 14px 20px;
  border-bottom: 1px solid var(--demo-border);
}

.execution-card {
  margin-bottom: 16px;
}

.execution-card :deep(.el-card__header) {
  padding: 14px 20px;
  border-bottom: 1px solid var(--demo-border);
}

.execution-card :deep(.el-button) {
  border-radius: 8px;
  font-weight: 500;
}

.execution-card :deep(.el-button--success) {
  background: #047857;
  border: none;
}

.execution-card :deep(.el-button--success:hover) {
  background: #059669;
}

.execution-card :deep(.el-button--danger) {
  background: #be123c;
  border: none;
}

.execution-card :deep(.el-button--danger:hover) {
  background: #e11d48;
}

.loading-state {
  padding: 40px;
}

:deep(.el-card) {
  border-radius: 12px;
  border: 1px solid var(--demo-border);
  box-shadow: none;
}

:deep(.el-descriptions__label) {
  width: 100px;
  font-weight: 500;
  color: var(--demo-text-muted);
}

.comment-dialog-content {
  max-height: 500px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.comment-input-section {
  padding-bottom: 16px;
  border-bottom: 1px solid var(--demo-border);
}

.comment-list {
  flex: 1;
  overflow-y: auto;
  max-height: 300px;
}

.empty-comments {
  padding: 20px 0;
}

.comment-item {
  padding: 12px;
  background: var(--demo-bg);
  border-radius: 8px;
  margin-bottom: 10px;
}

.comment-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.comment-author {
  font-weight: 500;
  color: var(--demo-text-primary);
  font-size: 14px;
}

.comment-time {
  font-size: 12px;
  color: var(--demo-text-muted);
}

.comment-content {
  color: var(--demo-text-secondary);
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
