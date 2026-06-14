<template>
  <div class="review-execution-page">
    <!-- 头部：返回按钮和标题 -->
    <div class="execution-header">
      <el-button size="small" @click="goBack">
        <el-icon><ArrowLeft /></el-icon>
        {{ $t('common.back') }}
      </el-button>
      <h2 style="margin: 0 0 0 16px;">{{ planDetail.name }} - {{ $t('review.reviewExecution') }}</h2>
    </div>

    <div class="main-content">
      <!-- 统计卡片和提交按钮 - 固定区域 -->
      <div class="stats-submit-wrapper" ref="statsWrapperRef">
        <div class="stats-submit-container">
          <!-- 进度统计 -->
          <div class="stats-cards">
            <div
              class="stat-card"
              :class="{ 'active': statusFilter === null }"
              @click="filterByStatus(null)"
              style="cursor: pointer;"
            >
              <span class="stat-label">{{ $t('review.totalTestcases') }}</span>
              <span class="stat-value">{{ planDetail.total_testcases || 0 }}</span>
            </div>
            <div
              class="stat-card"
              :class="{ 'active': statusFilter === 'REVIEWED' }"
              @click="filterByStatus('REVIEWED')"
              style="cursor: pointer;"
            >
              <span class="stat-label">{{ $t('review.reviewed') }}</span>
              <span class="stat-value" style="color: #409eff;">{{ statistics.executed || 0 }}</span>
            </div>
            <div
              class="stat-card"
              :class="{ 'active': statusFilter === 'PENDING' }"
              @click="filterByStatus('PENDING')"
              style="cursor: pointer;"
            >
              <span class="stat-label">{{ $t('review.pendingReview') }}</span>
              <span class="stat-value" style="color: #64748b;">{{ statistics.pending || 0 }}</span>
            </div>
            <div
              class="stat-card"
              :class="{ 'active': statusFilter === 'APPROVED' }"
              @click="filterByStatus('APPROVED')"
              style="cursor: pointer;"
            >
              <span class="stat-label">{{ $t('review.passed') }}</span>
              <span class="stat-value" style="color: #047857;">{{ statistics.approved || 0 }}</span>
            </div>
            <div
              class="stat-card"
              :class="{ 'active': statusFilter === 'REJECTED' }"
              @click="filterByStatus('REJECTED')"
              style="cursor: pointer;"
            >
              <span class="stat-label">{{ $t('review.rejected') }}</span>
              <span class="stat-value" style="color: #be123c;">{{ statistics.rejected || 0 }}</span>
            </div>
          </div>
          
          <!-- 提交评审按钮 -->
          <div class="submit-action" v-if="isReviewer && (planDetail.status === 'PENDING' || planDetail.status === 'IN_PROGRESS')">
            <el-button
              type="primary"
              @click="submitReviewPlan"
              :disabled="!canSubmit"
            >
              <el-icon><Check /></el-icon>
              {{ $t('review.submitReview') }}
            </el-button>
            <div v-if="!canSubmit" class="submit-tip">
              还有 {{ pendingDraftCount }} 个用例未完成评审
            </div>
          </div>
        </div>
      </div>

      <div class="table-section">
        <!-- 批量操作栏 -->
        <div class="batch-actions" v-if="isReviewer && selectedTestCases.length > 0">
          <span style="margin-right: 10px;">{{ $t('review.selected') }} {{ selectedTestCases.length }} {{ $t('review.caseCount') }}</span>
          <el-button type="success" @click="showBatchReviewDialog('APPROVED')">
            <el-icon><Select /></el-icon>
            {{ $t('review.batchPass') }}
          </el-button>
          <el-button type="danger" @click="showBatchReviewDialog('REJECTED')">
            <el-icon><CloseBold /></el-icon>
            {{ $t('review.batchReject') }}
          </el-button>
          <el-button type="info" @click="showBatchReviewDialog('DEPRECATED')">
            <el-icon><Delete /></el-icon>
            {{ $t('review.batchDeprecate') }}
          </el-button>
        </div>

        <!-- 用例列表 -->
        <div class="table-container" ref="tableContainerRef">
          <el-table
            ref="tableRef"
            :data="testcaseList"
            style="width: 100%"
            border
            :header-cell-style="{ background: '#f8fafc', color: '#64748b', fontWeight: '500', fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.05em' }"
            :cell-style="tableCellStyle"
            @selection-change="handleSelectionChange"
            row-key="id"
            :height="tableHeight"
          >
            <el-table-column v-if="isReviewer" type="selection" width="50" align="center" :selectable="isSelectable" />
            <el-table-column :label="$t('review.caseTitle')" min-width="250" align="left">
              <template #default="{ row }">
                <div
                  class="clickable-title multi-line-cell"
                  @click.stop="goToReviewDetail(row.id)"
                >
                  {{ row.name }}
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="module" :label="$t('review.belongModule')" min-width="200" align="left">
              <template #default="{ row }">
                <div class="multi-line-cell">{{ row.module }}{{ row.sub_module ? ' / ' + row.sub_module : '' }}</div>
              </template>
            </el-table-column>
            <el-table-column prop="precondition" :label="$t('review.precondition')" min-width="200" align="left">
              <template #default="{ row }">
                <div class="multi-line-cell">{{ row.precondition || '-' }}</div>
              </template>
            </el-table-column>
            <el-table-column prop="steps" :label="$t('review.testSteps')" min-width="300" align="left">
              <template #default="{ row }">
                <div class="multi-line-cell">
                  <div v-for="(step, stepIndex) in parseSteps(row.steps)" :key="stepIndex" class="step-item">
                    <span class="step-number">{{ stepIndex + 1 }}.</span>
                    <span class="step-text">{{ step }}</span>
                  </div>
                  <span v-if="!row.steps || parseSteps(row.steps).length === 0">-</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column :label="$t('review.expectedResult')" min-width="300" align="left">
              <template #default="{ row }">
                <div class="multi-line-cell">
                  <div v-for="(result, resultIndex) in parseExpected(row.expected_result)" :key="resultIndex" class="step-item">
                    <span class="step-number">{{ resultIndex + 1 }}.</span>
                    <span class="step-text">{{ result }}</span>
                  </div>
                  <span v-if="!row.expected_result || parseExpected(row.expected_result).length === 0">-</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="level" :label="$t('review.caseLevel')" width="120" align="center" />
            <el-table-column :label="$t('review.reviewStatus')" width="140" align="center">
              <template #default="{ row }">
                <!-- 暂存状态：虚线边框 -->
                <template v-if="row.pending_review_result">
                  <el-tag
                    :type="getResultTagType(row.pending_review_result)"
                    effect="plain"
                    size="small"
                    style="border-style: dashed;"
                  >
                    {{ getResultText(row.pending_review_result) }}
                  </el-tag>
                </template>
                <template v-else>
                  <el-tag v-if="row.review_status === 'PENDING'" type="warning" size="small">{{ $t('review.pendingReview') }}</el-tag>
                  <el-tag v-else-if="row.review_status === 'APPROVED'" type="success" size="small">{{ $t('review.approved') }}</el-tag>
                  <el-tag v-else-if="row.review_status === 'REJECTED'" type="danger" size="small">{{ $t('review.rejected') }}</el-tag>
                  <el-tag v-else-if="row.review_status === 'DEPRECATED'" type="info" size="small">{{ $t('review.deprecated') }}</el-tag>
                  <span v-else>-</span>
                </template>
              </template>
            </el-table-column>
            <el-table-column :label="$t('review.reviewComment')" min-width="200" align="left">
              <template #default="{ row }">
                <div class="multi-line-cell">{{ (row.pending_review_comment || row.review_comment) || '-' }}</div>
              </template>
            </el-table-column>
            <el-table-column v-if="isReviewer" :label="$t('review.operation')" width="260" align="center" fixed="right">
              <template #default="{ row }">
                <div style="display: flex; align-items: center; justify-content: center; flex-wrap: wrap; gap: 2px;">
                  <template v-if="row.review_status === 'PENDING'">
                    <el-button link type="success" @click="reviewTestCase(row, 'APPROVED')">{{ $t('review.pass') }}</el-button>
                    <el-button link type="danger" @click="reviewTestCase(row, 'REJECTED')">{{ $t('review.notPass') }}</el-button>
                    <el-button link type="info" @click="reviewTestCase(row, 'DEPRECATED')">{{ $t('review.deprecate') }}</el-button>
                  </template>
                  <template v-else>
                    <el-button link type="primary" @click="viewReviewDetail(row)">{{ $t('review.view') }}</el-button>
                  </template>
                  <el-button link type="warning" @click="openCommentDialog(row)">
                    <el-icon><ChatDotRound /></el-icon>
                    <span v-if="testcaseCommentCounts[row.id]">({{ testcaseCommentCounts[row.id] }})</span>
                    <span v-else>{{ $t('review.comment') }}</span>
                  </el-button>
                </div>
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
            @size-change="async () => { await applyFilter(); await nextTick(); scrollToTop(); }"
            @current-change="async () => { await applyFilter(); await nextTick(); scrollToTop(); }"
            background
          />
        </div>
      </div>
    </div>

    <!-- 评审对话框 -->
    <el-dialog
      v-model="reviewDialogVisible"
      :title="reviewDialogTitle"
      width="600px"
    >
      <el-form :model="reviewForm" label-width="100px">
        <el-form-item :label="$t('review.reviewResult')">
          <el-tag 
            v-if="reviewForm.result === 'APPROVED'" 
            type="success" 
            size="large"
          >
            {{ $t('review.pass') }}
          </el-tag>
          <el-tag 
            v-else-if="reviewForm.result === 'REJECTED'" 
            type="danger" 
            size="large"
          >
            {{ $t('review.reject') }}
          </el-tag>
          <el-tag 
            v-else-if="reviewForm.result === 'DEPRECATED'" 
            type="info" 
            size="large"
          >
            {{ $t('review.deprecate') }}
          </el-tag>
        </el-form-item>
        <el-form-item :label="$t('review.reviewComment')">
          <el-input
            v-model="reviewForm.comment"
            type="textarea"
            :rows="4"
            :placeholder="$t('review.reviewCommentPlaceholder')"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="reviewDialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="submitReview" :loading="submitting">{{ $t('common.confirm') }}</el-button>
      </template>
    </el-dialog>

<!-- 查看评审详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      :title="$t('review.reviewDetailTitle')"
      width="600px"
    >
      <el-descriptions :column="1" border>
        <el-descriptions-item :label="$t('review.caseNumber')">{{ currentTestCase.case_number }}</el-descriptions-item>
        <el-descriptions-item :label="$t('review.caseTitle')">{{ currentTestCase.name }}</el-descriptions-item>
        <el-descriptions-item :label="$t('review.reviewResult')">
          <el-tag 
            v-if="currentTestCase.review_result === 'APPROVED'"
            type="success" 
            size="small"
          >{{ $t('review.pass') }}</el-tag>
          <el-tag 
            v-else-if="currentTestCase.review_result === 'REJECTED'"
            type="danger" 
            size="small"
          >{{ $t('review.reject') }}</el-tag>
          <el-tag 
            v-else-if="currentTestCase.review_result === 'DEPRECATED'"
            type="info" 
            size="small"
          >{{ $t('review.deprecate') }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item :label="$t('review.reviewer')">{{ currentTestCase.reviewer_name || '-' }}</el-descriptions-item>
        <el-descriptions-item :label="$t('review.reviewTime')">
          {{ currentTestCase.reviewed_at ? formatDateTime(currentTestCase.reviewed_at) : '-' }}
        </el-descriptions-item>
        <el-descriptions-item :label="$t('review.reviewComment')">{{ currentTestCase.review_comment || '-' }}</el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button type="primary" @click="detailDialogVisible = false">{{ $t('common.close') }}</el-button>
      </template>
    </el-dialog>

    <!-- 评论对话框 -->
    <el-dialog
      v-model="commentDialogVisible"
      :title="(currentCommentTestcase?.name || $t('review.caseTitle')) + ' - ' + $t('review.comment')"
      width="600px"
      destroy-on-close
    >
      <div class="comment-dialog-content">
        <div class="comment-input-section">
          <el-input
            v-model="newComment"
            type="textarea"
            :rows="3"
            :placeholder="$t('review.commentPlaceholder')"
          />
          <el-button 
            type="primary" 
            @click="submitComment" 
            :loading="submittingComment"
            style="margin-top: 10px;"
          >
            {{ $t('review.publishComment') }}
          </el-button>
        </div>
        
        <div class="comment-list" v-loading="commentLoading">
          <div v-if="!testcaseComments[currentCommentTestcase?.id]?.length" class="empty-comments">
            <el-empty :description="$t('review.noComments')" :image-size="60" />
          </div>
          <div 
            v-else 
            v-for="comment in testcaseComments[currentCommentTestcase?.id]" 
            :key="comment.id"
            class="comment-item"
          >
            <div class="comment-header">
              <span class="comment-author">{{ comment.author_name }}</span>
              <span class="comment-time">{{ formatDateTime(comment.created_at) }}</span>
            </div>
            <div class="comment-content">{{ comment.content }}</div>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="commentDialogVisible = false">{{ $t('common.close') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, onBeforeUnmount, nextTick, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useScrollToTop } from '../../composables/useScrollToTop'
import { useRouter, useRoute, onBeforeRouteLeave } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Select, CloseBold, Check, Delete, ChatDotRound } from '@element-plus/icons-vue'
import { 
  getReviewPlanDetail, 
  getPlanTestCases, 
  reviewTestCase as reviewTestCaseApi, 
  batchReviewTestCases,
  submitReviewPlan as submitReviewPlanApi
} from '@/api/reviewPlan'
import { getComments, createComment, getCommentCounts } from '@/api/comment.js'
import { useLoadingStore } from '../../stores/loading'
import { useUserRole } from '../../composables/useUserRole'
import { useTeam } from '../../composables/useTeam'
import { getUserRoleInTeam } from '../../api/team'

const { t } = useI18n()

const router = useRouter()
const route = useRoute()
const loadingStore = useLoadingStore()
const { isSuperAdmin, isAdmin } = useUserRole()
const { currentTeam } = useTeam()
const currentUserRole = ref('member')

const planDetail = ref({})
const testcaseList = ref([])
const allTestcases = ref([])  // 保存所有用例数据
const loading = ref(false)
const selectedTestCases = ref([])
const tableRef = ref(null)
const { scrollToTop } = useScrollToTop(tableRef)
const isStatsFixed = ref(false)
const statsWrapperRef = ref(null)

const pagination = reactive({
  page: parseInt(route.query.page) || 1,
  size: 20,
  total: 0
})

// 统计：基于 allTestcases 实时计算，暂存或官方结果变化立即刷新
const statistics = computed(() => {
  const cases = allTestcases.value || []
  const effective = (tc) => tc.pending_review_result || tc.review_result
  let approved = 0, rejected = 0, deprecated = 0, executed = 0
  cases.forEach(tc => {
    const r = effective(tc)
    if (r === 'APPROVED') approved++
    else if (r === 'REJECTED') rejected++
    else if (r === 'DEPRECATED') deprecated++
    if (tc.pending_review_result || tc.review_status !== 'PENDING') executed++
  })
  return {
    total: cases.length,
    approved,
    rejected,
    deprecated,
    executed,
    pending: cases.length - executed
  }
})

// 状态筛选
const statusFilter = ref(null)

// 评审对话框
const reviewDialogVisible = ref(false)
const reviewDialogTitle = ref('')
const submitting = ref(false)
const isLeavingAfterSubmit = ref(false)  // 提交成功后主动跳转，跳过离开守卫
const reviewForm = reactive({
  result: '',
  comment: '',
  testcaseIds: [],
  isBatch: false
})

// 详情对话框
const detailDialogVisible = ref(false)
const currentTestCase = ref({})

// 评论相关
const testcaseComments = ref({})
const testcaseCommentCounts = ref({})
const commentDialogVisible = ref(false)
const currentCommentTestcase = ref(null)
const newComment = ref('')
const commentLoading = ref(false)
const submittingComment = ref(false)

const loadPlanDetail = async () => {
  try {
    const res = await getReviewPlanDetail(route.params.id)
    if (res.code === 200) {
      planDetail.value = res.data
      // statistics 改用 computed 后会基于 allTestcases 自动重新计算
    }
  } catch (error) {
    ElMessage.error(t('review.loadPlanFailed'))
  }
}

// 状态筛选函数
const filterByStatus = (status) => {
  statusFilter.value = status
  pagination.page = 1
  applyFilter()
}

const loadTestCases = async () => {
  loadingStore.showLoading()
  loading.value = true
  try {
    // 加载所有用例(不分页)
    const params = {
      page: 1,
      size: 10000  // 获取所有用例
    }
    const res = await getPlanTestCases(route.params.id, params)
    if (res.code === 200) {
      // 保持后端返回的排序，不在前端重新排序
      allTestcases.value = res.data.records || []
      // statistics 改用 computed 后会基于 allTestcases 自动重新计算
      
      // 延迟加载所有评论数量（不阻塞页面渲染）
      setTimeout(async () => {
        try {
          const ids = allTestcases.value.map(tc => tc.id)
          if (ids.length === 0) return
          const res = await getCommentCounts('review_testcase', ids)
          if (res.code === 200 && res.data) {
            // 逐个赋值，避免 Object.assign 的响应式问题
            const counts = res.data
            for (const id in counts) {
              testcaseCommentCounts.value[id] = counts[id]
            }
          }
        } catch (e) {
          console.error('加载评论数量失败:', e)
        }
      }, 500)
      
      // 应用筛选
      applyFilter()
    }
} catch (error) {
      console.error('Load cases failed:', error)
      ElMessage.error(t('review.loadCasesFailed'))
    } finally {
    loadingStore.hideLoading()
    loading.value = false
  }
}

// 应用筛选和分页
const applyFilter = () => {
  let filtered = [...allTestcases.value]

  // 根据状态筛选
  if (statusFilter.value === 'PENDING') {
    // 未执行：既无暂存也未提交
    filtered = filtered.filter(tc => !tc.pending_review_result && tc.review_status === 'PENDING')
  } else if (statusFilter.value === 'REVIEWED') {
    // 已执行：有暂存或已提交
    filtered = filtered.filter(tc => tc.pending_review_result || tc.review_status !== 'PENDING')
  } else if (statusFilter.value === 'APPROVED') {
    // 以"执行"为口径：暂存 APPROVED 或官方 APPROVED
    filtered = filtered.filter(tc => tc.pending_review_result === 'APPROVED' || (tc.pending_review_result == null && tc.review_status === 'APPROVED'))
  } else if (statusFilter.value === 'REJECTED') {
    filtered = filtered.filter(tc => tc.pending_review_result === 'REJECTED' || (tc.pending_review_result == null && tc.review_status === 'REJECTED'))
  } else if (statusFilter.value === 'DEPRECATED') {
    filtered = filtered.filter(tc => tc.pending_review_result === 'DEPRECATED' || (tc.pending_review_result == null && tc.review_status === 'DEPRECATED'))
  }
  
  // 更新总数
  pagination.total = filtered.length
  
  // 分页
  const start = (pagination.page - 1) * pagination.size
  const end = start + pagination.size
  testcaseList.value = filtered.slice(start, end)
}

const handleSelectionChange = (selection) => {
  selectedTestCases.value = selection
}

const isSelectable = (row) => {
  return row.review_status === 'PENDING'
}

const reviewTestCase = (row, result) => {
  let title = ''
  if (result === 'APPROVED') {
    title = '通过评审'
  } else if (result === 'REJECTED') {
    title = '不通过评审'
  } else {
    title = '废弃用例'
  }
  
  reviewDialogTitle.value = title
  reviewForm.result = result
  reviewForm.comment = ''
  reviewForm.testcaseIds = [row.id]
  reviewForm.isBatch = false
  reviewDialogVisible.value = true
}

const showBatchReviewDialog = (result) => {
  if (selectedTestCases.value.length === 0) {
    ElMessage.warning(t('review.pleaseSelectCase'))
    return
  }
  
  let title = ''
  if (result === 'APPROVED') {
    title = t('review.batchPassTitle')
  } else if (result === 'REJECTED') {
    title = t('review.batchRejectTitle')
  } else {
    title = t('review.batchDeprecateTitle')
  }
  
  reviewDialogTitle.value = title
  reviewForm.result = result
  reviewForm.comment = ''
  reviewForm.testcaseIds = selectedTestCases.value.map(tc => tc.id)
  reviewForm.isBatch = true
  reviewDialogVisible.value = true
}

const submitReview = async () => {
  submitting.value = true
  try {
    if (reviewForm.isBatch) {
      // 批量评审（写入暂存）
      await batchReviewTestCases(route.params.id, {
        testcase_ids: reviewForm.testcaseIds,
        result: reviewForm.result,
        comment: reviewForm.comment || undefined
      })
      ElMessage.info(`已记录 ${reviewForm.testcaseIds.length} 个用例的评审结果，提交评审计划后生效`)
    } else {
      // 单个评审（写入暂存）
      await reviewTestCaseApi(route.params.id, reviewForm.testcaseIds[0], {
        result: reviewForm.result,
        comment: reviewForm.comment || undefined
      })
      ElMessage.info('已记录，提交评审计划后生效')
    }

    // 本地合并暂存结果到 allTestcases（避免重新拉取导致分页/筛选状态丢失）
    // statistics 改用 computed，会基于 allTestcases 自动实时刷新
    const now = new Date().toISOString()
    const currentUser = JSON.parse(localStorage.getItem('user') || '{}')
    const targetIds = new Set(reviewForm.testcaseIds.map(id => Number(id)))
    allTestcases.value.forEach(tc => {
      if (targetIds.has(Number(tc.id))) {
        tc.pending_review_result = reviewForm.result
        tc.pending_review_comment = reviewForm.comment || null
        tc.pending_reviewer_id = tc.pending_reviewer_id || currentUser.id || null
        tc.pending_reviewed_at = now
      }
    })
    // 触发筛选/分页刷新，使统计与列表同步
    applyFilter()

    reviewDialogVisible.value = false
    selectedTestCases.value = []
  } catch (error) {
    ElMessage.error(t('review.reviewFailed'))
  } finally {
    submitting.value = false
  }
}

const viewReviewDetail = (row) => {
  currentTestCase.value = row
  detailDialogVisible.value = true
}

const goBack = () => {
  router.push('/review-plans')
}

// 评审结果 -> 标签类型
const getResultTagType = (result) => {
  switch (result) {
    case 'APPROVED': return 'success'
    case 'REJECTED': return 'danger'
    case 'DEPRECATED': return 'info'
    default: return 'warning'
  }
}

// 评审结果 -> 文案
const getResultText = (result) => {
  switch (result) {
    case 'APPROVED': return '已通过'
    case 'REJECTED': return '未通过'
    case 'DEPRECATED': return '已废弃'
    default: return '待评审'
  }
}

// 跳转到用例详情评审页面
const goToReviewDetail = (testcaseId) => {
  console.log('=== 点击用例编号 ===')
  console.log('testcaseId:', testcaseId)
  console.log('planId:', route.params.id)
  
  // 构建查询参数，传递当前页码
  const query = {
    page: pagination.page
  }
  
  // 使用命名路由跳转，确保参数正确传递
  router.push({
    name: 'TestCaseReviewDetail',
    params: {
      planId: route.params.id,
      testcaseId: testcaseId
    },
    query
  }).then(() => {
    console.log('路由跳转成功')
  }).catch(err => {
    console.error('路由跳转失败:', err)
  })
}

// 离开页面守卫：若仍有未完成的评审、或已全部暂存但未提交，弹窗提示
// 跳转到用例详情页（TestCaseReviewDetail）时不触发守卫，避免误拦截内部流程
onBeforeRouteLeave((to, from, next) => {
  if (to.name === 'TestCaseReviewDetail') {
    next()
    return
  }
  // 提交成功后主动跳转，不需要拦截
  if (isLeavingAfterSubmit.value) {
    next()
    return
  }
  if (planDetail.value?.status === 'COMPLETED') {
    next()
    return
  }
  const undrafted = allTestcases.value?.filter(tc => !tc.pending_review_result).length || 0
  if (undrafted > 0) {
    ElMessageBox.confirm(
      `当前评审计划还有 ${undrafted} 个用例未完成评审，确定离开吗？评审结果已自动保存，下次可继续填写。`,
      '提示',
      {
        confirmButtonText: '确定离开',
        cancelButtonText: '继续填写',
        type: 'warning'
      }
    ).then(() => next()).catch(() => next(false))
    return
  }
  // 全部暂存但还未提交
  if (canSubmit.value) {
    ElMessageBox.confirm(
      '所有用例已完成评审，但还未提交评审计划。确定离开吗？已评审结果将作为草稿保留，但不会生效。',
      '提示',
      {
        confirmButtonText: '确定离开',
        cancelButtonText: '去提交',
        type: 'warning'
      }
    ).then(() => next()).catch(() => next(false))
    return
  }
  next()
})

// 计算是否可以提交：所有用例的 pending_review_result 都已填写
const canSubmit = computed(() => {
  if (!allTestcases.value || allTestcases.value.length === 0) return false
  return allTestcases.value.every(tc => !!tc.pending_review_result)
})

// 暂存待填写的用例数
const pendingDraftCount = computed(() => {
  if (!allTestcases.value) return 0
  return allTestcases.value.filter(tc => !tc.pending_review_result).length
})

// 判断当前用户是否是评审人（管理员、项目组负责人、组织负责人或评审人）
const isReviewer = computed(() => {
  if (isSuperAdmin.value || isAdmin.value) return true
  if (currentUserRole.value === 'leader' || currentUserRole.value === 'org_manager') return true
  const currentUserId = JSON.parse(localStorage.getItem('user') || '{}').id
  const reviewerIds = planDetail.value.reviewer_ids || []
  return reviewerIds.includes(currentUserId)
})

const tableCellStyle = ({ row, column }) => {
  return {
    padding: '8px 12px',
    whiteSpace: 'pre-wrap',
    wordBreak: 'break-word'
  }
}

// 表格高度自适应
const tableContainerRef = ref(null)
const tableHeight = ref(400)
let resizeObserver = null

const updateTableHeight = () => {
  nextTick(() => {
    if (tableContainerRef.value && tableContainerRef.value.clientHeight > 0) {
      tableHeight.value = tableContainerRef.value.clientHeight
    }
  })
}

// 监听数据变化，重新计算表格布局
watch(testcaseList, () => {
  nextTick(() => {
    updateTableHeight()
    if (tableRef.value) {
      tableRef.value.doLayout()
    }
  })
})

// 监听路由查询参数变化，更新分页
watch(() => route.query.page, (newPage) => {
  if (newPage) {
    pagination.page = parseInt(newPage)
    applyFilter()
  }
})

onMounted(async () => {
  // 加载用户在当前团队中的角色
  if (currentTeam.value?.id) {
    try {
      const roleRes = await getUserRoleInTeam(currentTeam.value.id)
      if (roleRes.code === 200 && roleRes.data?.role) {
        currentUserRole.value = roleRes.data.role
      }
    } catch (e) {
      console.error('Failed to load user role:', e)
    }
  }
  loadPlanDetail()
  loadTestCases()
  window.addEventListener('scroll', handleScroll)
  window.addEventListener('resize', handleResize)
  window.addEventListener('beforeunload', handleBeforeUnload)
  // 初始化表格高度
  nextTick(() => {
    updateTableHeight()
    if (tableContainerRef.value && typeof ResizeObserver !== 'undefined') {
      resizeObserver = new ResizeObserver(updateTableHeight)
      resizeObserver.observe(tableContainerRef.value)
    }
    setTimeout(updateTableHeight, 150)
  })
})

onBeforeUnmount(() => {
  window.removeEventListener('scroll', handleScroll)
  window.removeEventListener('resize', handleResize)
  window.removeEventListener('beforeunload', handleBeforeUnload)
  if (resizeObserver) resizeObserver.disconnect()
})

// 关闭/刷新页面时弹窗
const handleBeforeUnload = (e) => {
  if (planDetail.value?.status === 'COMPLETED') return
  const undrafted = allTestcases.value?.filter(tc => !tc.pending_review_result).length || 0
  if (undrafted > 0 || canSubmit.value) {
    e.preventDefault()
    e.returnValue = ''
    return ''
  }
}

// 处理窗口大小变化
const handleResize = () => {
  updateTableHeight()
  nextTick(() => {
    if (tableRef.value) {
      tableRef.value.doLayout()
    }
  })
}

// 提交评审计划
const submitReviewPlan = async () => {
  // 前端二次校验：所有用例都需要有暂存
  if (!canSubmit.value) {
    ElMessage.warning(`还有 ${pendingDraftCount.value} 个用例未完成评审，无法提交`)
    return
  }
  try {
    await ElMessageBox.confirm(
      '提交后将把所有评审结果写入测试用例状态，且计划不可再修改。确定提交吗？',
      '提交评审计划',
      {
        confirmButtonText: t('common.confirm'),
        cancelButtonText: t('common.cancel'),
        type: 'warning'
      }
    )

    await submitReviewPlanApi(route.params.id)
    ElMessage.success(t('review.submitSuccess'))
    isLeavingAfterSubmit.value = true
    router.push('/review-plans')
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') {
      const detail = error?.response?.data?.detail
      ElMessage.error(detail || t('review.submitFailed'))
    }
  }
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

// 评论相关方法
const openCommentDialog = async (row) => {
  currentCommentTestcase.value = row
  commentDialogVisible.value = true
  newComment.value = ''
  await loadComments(row.id)
}

const loadComments = async (testcaseId) => {
  commentLoading.value = true
  try {
    const res = await getComments('review_testcase', testcaseId, false)
    if (res.code === 200) {
      testcaseComments.value[testcaseId] = res.data || []
      testcaseCommentCounts.value[testcaseId] = (res.data || []).length
    }
  } catch (error) {
    console.error('加载评论失败:', error)
  } finally {
    commentLoading.value = false
  }
}

const submitComment = async () => {
  if (!newComment.value.trim()) {
    ElMessage.warning('请输入评论内容')
    return
  }
  
  if (!currentCommentTestcase.value) return
  
  submittingComment.value = true
  try {
    await createComment({
      entity_type: 'review_testcase',
      entity_id: currentCommentTestcase.value.id,
      content: newComment.value.trim(),
      parent_id: null
    })
    ElMessage.success('评论成功')
    newComment.value = ''
    await loadComments(currentCommentTestcase.value.id)
  } catch (error) {
    ElMessage.error('评论失败')
  } finally {
    submittingComment.value = false
  }
}

const getCommentCount = (testcaseId) => {
  return testcaseCommentCounts.value[testcaseId] || 0
}

// 解析步骤文本
const parseSteps = (stepsText) => {
  if (!stepsText) return []
  
  if (Array.isArray(stepsText)) {
    return stepsText.map(item => {
      let text = ''
      if (typeof item === 'object' && item !== null) {
        text = String(item.step || '').trim()
      } else {
        text = String(item).trim()
      }
      while (/^(\d+)(?:[。、]|\.)(?!\d)\s*/.test(text)) {
        text = text.replace(/^(\d+)(?:[。、]|\.)(?!\d)\s*/, '')
      }
      return text.trim()
    }).filter(text => text)
  }
  
  const textStr = String(stepsText).trim()
  if (!textStr) return []
  
  try {
    const parsed = JSON.parse(textStr)
    if (Array.isArray(parsed)) {
      return parsed.map(item => {
        let text = ''
        if (typeof item === 'object' && item !== null) {
          text = String(item.step || '').trim()
        } else {
          text = String(item).trim()
        }
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
  
  if (Array.isArray(expectedText)) {
    return expectedText.map(item => {
      let text = ''
      if (typeof item === 'object' && item !== null) {
        text = String(item.expected || '').trim()
      } else {
        text = String(item).trim()
      }
      while (/^(\d+)(?:[。、]|\.)(?!\d)\s*/.test(text)) {
        text = text.replace(/^(\d+)(?:[。、]|\.)(?!\d)\s*/, '')
      }
      return text.trim()
    }).filter(text => text)
  }
  
  const textStr = String(expectedText).trim()
  if (!textStr) return []
  
  try {
    const parsed = JSON.parse(textStr)
    if (Array.isArray(parsed)) {
      return parsed.map(item => {
        let text = ''
        if (typeof item === 'object' && item !== null) {
          text = String(item.expected || '').trim()
        } else {
          text = String(item).trim()
        }
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

// 滚动监听
const handleScroll = () => {
  if (statsWrapperRef.value) {
    const rect = statsWrapperRef.value.getBoundingClientRect()
    isStatsFixed.value = rect.top <= 0
  }
}

</script>

<style scoped>
/* 页面容器 */
.review-execution-page {
  width: 100%;
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--demo-bg);
}

/* 头部 */
.execution-header {
  display: flex;
  align-items: center;
  padding: 8px 16px;
  background: var(--demo-bg-card);
  border-bottom: 1px solid var(--demo-border);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  flex-shrink: 0;
}

.execution-header h2 {
  font-size: 15px;
  font-weight: 600;
  color: var(--demo-text-primary);
  margin: 0 0 0 12px;
}

/* 按钮样式 - Demo主题 */
.execution-header :deep(.el-button) {
  border-radius: 8px;
  font-weight: 500;
  height: 40px;
  padding: 0 16px;
  font-size: 14px;
  transition: all 0.15s;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.execution-header :deep(.el-button--default) {
  background: #ffffff;
  border: 1px solid var(--demo-border);
  color: var(--demo-text-secondary);
}

.execution-header :deep(.el-button--default:hover) {
  background: var(--demo-bg);
  border-color: #cbd5e1;
}

/* 主内容区 */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 8px;
  gap: 8px;
}

/* 统计卡片和提交按钮容器 */
.stats-submit-wrapper {
  background: var(--demo-bg-card);
  border-radius: 8px;
  border: 1px solid var(--demo-border);
  padding: 4px 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  flex-shrink: 0;
}

.stats-submit-container {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  max-width: 100%;
}

.stats-cards {
  display: flex;
  gap: 8px;
  flex: 1;
  flex-wrap: wrap;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: var(--demo-bg);
  border-radius: 8px;
  min-width: 100px;
  transition: all 0.15s;
  border: 1px solid var(--demo-border);
  cursor: pointer;
}

.stat-card:hover {
  background: var(--demo-border-light);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.stat-card.active:not(:first-child) {
  background: var(--demo-primary);
  border-color: var(--demo-primary);
  box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3);
}

.stat-card.active:not(:first-child) .stat-label,
.stat-card.active:not(:first-child) .stat-value {
  color: white !important;
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

.submit-action {
  display: flex;
  align-items: center;
  gap: 12px;
}

.submit-action :deep(.el-button--primary) {
  background: var(--demo-primary);
  border: none;
  border-radius: 8px;
  font-weight: 500;
  height: 40px;
  padding: 0 20px;
  font-size: 14px;
}

.submit-action :deep(.el-button--primary:hover) {
  background: var(--demo-primary-hover);
}

.submit-tip {
  font-size: 14px;
  color: var(--demo-text-muted);
  white-space: nowrap;
}

/* 表格区域 */
.table-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--demo-bg-card);
  border-radius: 8px;
  border: 1px solid var(--demo-border);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  overflow: hidden;
  min-height: 0;
}

/* 批量操作栏 */
.batch-actions {
  padding: 8px 12px;
  background-color: var(--demo-primary-light);
  border-bottom: 1px solid var(--demo-border);
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.batch-actions :deep(.el-button) {
  border-radius: 8px;
  font-weight: 500;
}

/* 表格容器 */
.table-container {
  flex: 1;
  overflow: hidden;
}

.table-container :deep(.el-table) {
  width: 100%;
}

/* 表格头部样式 - Demo主题 */
.table-container :deep(.el-table th.el-table__cell) {
  background: #f8fafc !important;
  color: var(--demo-text-muted) !important;
  font-weight: 500 !important;
  font-size: 12px !important;
  text-transform: uppercase !important;
  letter-spacing: 0.05em !important;
}

/* 表格行悬停样式 */
.table-container :deep(.el-table__row:hover > td) {
  background: #f8fafc !important;
}

/* 表格行高度自适应 */
.table-container :deep(.el-table__row) {
  height: auto !important;
}

.table-container :deep(.el-table__row > td) {
  background: #fff;
  height: auto !important;
}

/* 单元格内容换行 */
.table-container :deep(.el-table .cell) {
  padding: 4px 8px !important;
  white-space: pre-wrap !important;
  word-break: break-word !important;
  line-height: 1.5 !important;
  height: auto !important;
  overflow: visible !important;
  text-overflow: unset !important;
}

/* 自定义表格容器的滚动条样式 */
.table-container :deep(.el-table__body-wrapper) {
  scrollbar-width: thin;
  scrollbar-color: #cbd5e1 var(--demo-border-light);
}

.table-container :deep(.el-table__body-wrapper)::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

.table-container :deep(.el-table__body-wrapper)::-webkit-scrollbar-track {
  background: var(--demo-border-light);
  border-radius: 4px;
}

.table-container :deep(.el-table__body-wrapper)::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}

.table-container :deep(.el-table__body-wrapper)::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

/* 分页器 */
.pagination-container {
  padding: 8px 12px;
  background: var(--demo-bg-card);
  border-top: 1px solid var(--demo-border);
  display: flex;
  justify-content: flex-end;
  align-items: center;
  flex-shrink: 0;
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

/* 多行单元格样式 */
.multi-line-cell {
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.6;
}

.step-item {
  display: flex;
  align-items: flex-start;
  line-height: 1.6;
}

.step-number {
  color: #4f46e5;
  font-weight: 500;
  min-width: 24px;
  margin-right: 4px;
}

.step-text {
  word-break: break-word;
  white-space: pre-line;
  flex: 1;
}

/* 可点击标题样式 */
.clickable-title {
  color: #4f46e5 !important;
  cursor: pointer;
  transition: all 0.15s;
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.6;
}

.clickable-title:hover {
  color: #4338ca !important;
  text-decoration: underline;
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

/* 响应式调整 */
@media (max-width: 768px) {
  .stats-cards {
    flex-direction: column;
    gap: 10px;
  }
  
  .stats-submit-container {
    flex-direction: column;
    align-items: stretch;
  }
  
  .submit-action {
    justify-content: center;
  }
}

/* 评论对话框 */
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
