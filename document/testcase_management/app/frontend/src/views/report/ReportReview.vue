<template>
  <div class="report-review-container">
    <div class="review-header">
      <el-button v-if="!isSubmitPreviewMode" @click="goBack">
        <el-icon><ArrowLeft /></el-icon>
        {{ $t('report.back') }}
      </el-button>
      <div v-else></div>
      <h2 v-if="isSubmitPreviewMode">报告预览</h2>
      <h2 v-else-if="isPreviewMode">{{ $t('execution.previewReport') }}</h2>
      <h2 v-else>{{ reportData.status === 'PENDING_REVIEW' ? $t('report.reportReview') : $t('report.reportDetail') }}</h2>
      <div class="review-actions" v-if="isSubmitPreviewMode">
        <el-button @click="handleGoBackToEdit">返回修改</el-button>
        <el-button type="primary" @click="handleConfirmSubmit" :loading="submitting">确认提交</el-button>
      </div>
      <div class="review-actions" v-else-if="!isPreviewMode && reportData.status === 'PENDING_REVIEW' && canReview">
        <el-button type="primary" @click="handleApprove">{{ $t('report.approve') }}</el-button>
        <el-button type="danger" @click="handleReject">{{ $t('report.reject') }}</el-button>
      </div>
      <div class="review-actions" v-else-if="!isPreviewMode && reportData.status === 'APPROVED'">
        <el-button v-if="hasButton('reports', 'exportPdf')" type="primary" @click="handleExportPdf">{{ $t('report.exportPdf') }}</el-button>
        <el-button v-if="hasButton('reports', 'exportExcel')" @click="handleExportExcel">{{ $t('report.exportExcelBtn') }}</el-button>
        <el-dropdown v-if="canArchiveOrWithdraw" trigger="hover" @command="(cmd) => handleArchiveCommand(cmd)">
          <el-button>
            <el-icon><MoreFilled /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item v-if="reportData.is_archived !== 1" command="archive">
                <span>归档</span>
              </el-dropdown-item>
              <el-dropdown-item v-if="reportData.is_archived === 1 && canArchiveOrWithdraw" command="withdraw">
                <span>撤回</span>
              </el-dropdown-item>
              <el-dropdown-item v-if="reportData.is_archived === 1 && isSuperAdmin" command="unarchive">
                <span>撤回归档</span>
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
      <div v-else-if="isPreviewMode" class="review-actions">
        <span style="color: #f59e0b; font-size: 14px;">{{ $t('execution.previewReportTip') }}</span>
      </div>
    </div>

    <!-- 报告主体：Logo到Severity -->
    <el-card class="report-main-card" shadow="never">
      <!-- 版权信息 -->
      <div class="copyright-content">
        <img src="../../assets/images/whaletv-logo.png" alt="Logo" class="copyright-logo" />
        <div class="copyright-text">
          Confidential & Proprietary<br/>
          Copyright © {{ currentYear }} Whale TV Information Technology
        </div>
      </div>

      <!-- 报告标题 -->
      <h2 class="report-title">{{ reportData.project_name }} Report</h2>

      <!-- 封面表格 -->
      <table class="cover-table" border="1" cellspacing="0" cellpadding="0">
        <tbody>
          <tr v-for="(row, index) in coverData" :key="index">
            <td class="label-cell" v-html="row.label.replace(/\n/g, '<br/>')"></td>
            <td class="content-cell" v-html="row.value"></td>
          </tr>
        </tbody>
      </table>

      <!-- 测试结果详情 -->
      <template v-if="showTestResults">
        <div class="section-spacer"></div>
        <div class="section-title">Test Result Detail</div>
        <el-table :data="testResultsWithSummary" border class="result-table">
          <el-table-column prop="module" label="Module" width="150" align="center" />
          <el-table-column prop="test_cases" label="TestCases" width="100" align="center" />
          <el-table-column prop="pass" label="PASS" width="80" align="center" />
          <el-table-column prop="fail" label="FAIL" width="80" align="center" />
          <el-table-column prop="block" label="BLOCK" width="80" align="center" />
          <el-table-column prop="nt" label="NT" width="80" align="center" />
          <el-table-column prop="na" label="NA" width="80" align="center" />
          <el-table-column v-if="hasAssist" prop="assist" label="协测" width="80" align="center" />
          <el-table-column prop="passing_rate" label="Passing rate" width="120" align="center">
            <template #default="{ row }">
              <span v-if="row.isPassed" class="conclusion-cell" :class="row.passing_rate === 'OK' ? 'conclusion-ok' : 'conclusion-ng'">
                {{ row.passing_rate }}
              </span>
              <span v-else>{{ row.passing_rate }}</span>
            </template>
          </el-table-column>
        </el-table>
        <div class="result-note">
          {{ $t('report.resultNote') }}
        </div>
      </template>

      <!-- Zmind-PR统计 -->
      <template v-if="showZmindStats && zmindData.length > 0">
        <div class="section-spacer"></div>
        <el-table :data="zmindData" border class="zmind-table" :span-method="zmindSpanMethod">
          <el-table-column prop="type" label="Zmind-PR" width="150" align="center" />
          <el-table-column prop="prs" label="PRs" width="100" align="center" />
          <el-table-column prop="blocker" label="Blocker" width="100" align="center" />
          <el-table-column prop="critical" label="Critical" width="100" align="center" />
          <el-table-column prop="major" label="Major" width="100" align="center" />
          <el-table-column prop="minor" label="Minor" width="100" align="center" />
          <el-table-column prop="enhancement" label="Enhancement" width="120" align="center" />
          <el-table-column prop="conclusion" label="Conclusion" width="120" align="center">
            <template #default="{ row }">
              <span v-if="row.isOpen" class="conclusion-cell" :class="row.conclusion === 'OK' ? 'conclusion-ok' : 'conclusion-ng'">
                {{ row.conclusion }}
              </span>
            </template>
          </el-table-column>
        </el-table>
        <div class="severity-note">
          {{ $t('report.severityNote') }}
        </div>
      </template>
    </el-card>

    <!-- 用例详细情况 -->
    <el-card v-if="showTestCases" class="case-details" shadow="never">
      <div class="case-header">
        <span class="case-count">{{ $t('report.caseCount', { count: testCases.length }) }}</span>
      </div>
      <div class="case-table-wrapper">
        <el-table :data="paginatedTestCases" border>
          <el-table-column prop="case_number" label="用例编号" width="160">
            <template #default="{ row }">
              <el-tooltip :content="row.case_number" placement="top" :show-after="500">
                <div class="cell-ellipsis">{{ row.case_number }}</div>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column prop="module" label="所属模块" width="100">
            <template #default="{ row }">
              <el-tooltip :content="row.module" placement="top" :show-after="500">
                <div class="cell-ellipsis">{{ row.module }}</div>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column prop="name" label="用例标题" width="160">
            <template #default="{ row }">
              <el-tooltip :content="row.name" placement="top" :show-after="500">
                <div class="cell-ellipsis">{{ row.name }}</div>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column prop="precondition" label="前置条件" width="140">
            <template #default="{ row }">
              <el-tooltip :content="row.precondition || '-'" placement="top" :show-after="500">
                <div class="cell-ellipsis">{{ row.precondition || '-' }}</div>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column prop="steps" label="操作步骤" width="160">
            <template #default="{ row }">
              <el-tooltip :content="row.steps || '-'" placement="top" :show-after="500">
                <div class="cell-ellipsis">{{ row.steps || '-' }}</div>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column prop="expected_result" label="预期结果" width="140">
            <template #default="{ row }">
              <el-tooltip :content="row.expected_result || '-'" placement="top" :show-after="500">
                <div class="cell-ellipsis">{{ row.expected_result || '-' }}</div>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column prop="level" label="用例等级" width="80" align="center" />
          <el-table-column prop="result" label="测试结果" width="80" align="center">
            <template #default="{ row }">
              <span v-if="row.result === 'PASS'" style="color: #67c23a;">PASS</span>
              <span v-else-if="row.result === 'FAIL'" style="color: #f56c6c;">FAIL</span>
              <span v-else-if="row.result === 'BLOCK'" style="color: #e6a23c;">BLOCK</span>
              <span v-else-if="row.result === 'NA'" style="color: #909399;">NA</span>
              <span v-else-if="row.result === 'NT'" style="color: #909399;">NT</span>
            </template>
          </el-table-column>
          <el-table-column prop="remark" label="执行备注" width="100">
            <template #default="{ row }">
              <el-tooltip placement="top" :show-after="500" raw-content>
                <template #content>
                  <div v-html="renderRemarkWithPR(row.remark) || '-'"></div>
                </template>
                <div class="cell-ellipsis" v-html="renderRemarkWithPR(row.remark) || '-'"></div>
              </el-tooltip>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <el-pagination
        v-if="testCases.length > casePageSize"
        class="case-pagination"
        v-model:current-page="caseCurrentPage"
        v-model:page-size="casePageSize"
        :page-sizes="[50, 100]"
        :total="testCases.length"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleCasePageSizeChange"
        @current-change="handleCasePageChange"
      />
    </el-card>

    <!-- MpList（放在Issue列表前面） -->
    <el-card v-if="mplistData.rows && mplistData.rows.length > 0" class="mplist-details" shadow="never">
      <div class="section-title">Mp List <span class="issue-count">({{ mplistData.rows.length }}条)</span></div>
      <div class="mplist-table-wrapper">
        <el-table :data="paginatedMplistData" border class="mplist-table">
          <el-table-column
            v-for="(header, colIdx) in mplistData.headers"
            :key="colIdx"
            :label="header"
            :min-width="getMplistColWidth(header, colIdx)"
            align="center"
          >
            <template #default="{ row }">
              <el-tooltip :content="row[colIdx] || '-'" placement="top" :show-after="500">
                <div class="cell-ellipsis">{{ row[colIdx] || '-' }}</div>
              </el-tooltip>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <el-pagination
        v-if="mplistData.rows.length > mplistPageSize"
        class="mplist-pagination"
        v-model:current-page="mplistCurrentPage"
        v-model:page-size="mplistPageSize"
        :page-sizes="[20, 50, 100]"
        :total="mplistData.rows.length"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleMplistPageSizeChange"
        @current-change="handleMplistPageChange"
      />
    </el-card>

    <!-- Issue列表（放在用例表格后面） -->
    <el-card v-if="showIssueList && issueList.length > 0" class="issue-details" shadow="never">
      <div class="section-title">Issue List <span class="issue-count">({{ $t('report.issueCount', { count: issueList.length }) }})</span></div>
      <div class="issue-table-wrapper">
        <el-table :data="paginatedIssueList" border class="issue-table">
          <el-table-column prop="pr_number" label="#(PR号)" width="100" align="center">
            <template #default="{ row }">
              <el-tooltip :content="row.pr_number" placement="top" :show-after="500">
                <div class="cell-ellipsis cell-center">{{ row.pr_number }}</div>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column prop="tracker" label="跟踪" width="80" align="center">
            <template #default="{ row }">
              <el-tooltip :content="row.tracker || '-'" placement="top" :show-after="500">
                <div class="cell-ellipsis cell-center">{{ row.tracker || '-' }}</div>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column prop="category" label="类别" width="100" align="center">
            <template #default="{ row }">
              <el-tooltip :content="row.category || '-'" placement="top" :show-after="500">
                <div class="cell-ellipsis cell-center">{{ row.category || '-' }}</div>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column prop="severity" label="Severity" width="120" align="center">
            <template #default="{ row }">
              <div class="cell-center">
                <span :class="getSeverityClass(row.severity)">{{ row.severity || '-' }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="120" align="center">
            <template #default="{ row }">
              <div class="cell-center">
                <span :class="getStatusClass(row.status)">{{ row.status || '-' }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="priority" label="优先级" width="100" align="center">
            <template #default="{ row }">
              <el-tooltip :content="row.priority || '-'" placement="top" :show-after="500">
                <div class="cell-ellipsis cell-center">{{ row.priority || '-' }}</div>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column prop="subject" label="主题" min-width="200" align="center">
            <template #default="{ row }">
              <el-tooltip :content="row.subject || '-'" placement="top" :show-after="500">
                <div class="cell-ellipsis">{{ row.subject || '-' }}</div>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column prop="assignee" label="指派给" width="100" align="center">
            <template #default="{ row }">
              <el-tooltip :content="row.assignee || '-'" placement="top" :show-after="500">
                <div class="cell-ellipsis cell-center">{{ row.assignee || '-' }}</div>
              </el-tooltip>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <el-pagination
        v-if="issueList.length > issuePageSize"
        class="issue-pagination"
        v-model:current-page="issueCurrentPage"
        v-model:page-size="issuePageSize"
        :page-sizes="[20, 50, 100]"
        :total="issueList.length"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleIssuePageSizeChange"
        @current-change="handleIssuePageChange"
      />
    </el-card>
  </div>
  
  <!-- 导出进度对话框 -->
  <el-dialog v-model="exportDialogVisible" title="正在导出" :close-on-click-modal="false" :show-close="false" width="420px">
    <div style="text-align: center; padding: 20px 0;">
      <el-progress :percentage="exportProgress" :stroke-width="16" :text-inside="true" />
      <p style="margin-top: 16px; color: #909399; font-size: 14px;">{{ exportMessage }}</p>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, MoreFilled } from '@element-plus/icons-vue'
import { getReportDetail, approveReport, rejectReport, archiveReport, unarchiveReport, withdrawReport, startAsyncExport, pollExportStatus, downloadAsyncExport } from '../../api/report'
import { previewTestPlanReport, submitTestPlanForReview } from '../../api/testplan'
import { useLoadingStore } from '../../stores/loading'
import { useI18n } from 'vue-i18n'
import { useUserRole } from '../../composables/useUserRole'
import { renderRemarkWithPR } from '../../composables/useRemarkPR'

const { t } = useI18n()
const { isSuperAdmin, isAdmin, hasButton } = useUserRole()
const route = useRoute()
const router = useRouter()
const loadingStore = useLoadingStore()
const loading = ref(true)
const reportData = ref({})
const testResults = ref([])
const testCases = ref([])
const coverData = ref([])
const testResultsWithSummary = ref([])
const zmindData = ref([])
const issueList = ref([])
const mplistData = ref({ headers: [], rows: [] })
const includePrClosed = ref(0)
const hasZmindCsv = ref(false)
const reportTemplateConfig = ref(null)
const templateSelectedFields = ref(null)  // 模板选中的字段列表
const hasAssist = ref(false)  // 是否有协测结果

// 导出进度
const exportDialogVisible = ref(false)
const exportProgress = ref(0)
const exportMessage = ref('')

// 判断是预览模式还是审核模式
const isPreviewMode = computed(() => route.name === 'TestPlanReportPreview')
const isSubmitPreviewMode = computed(() => route.name === 'TestPlanSubmitPreview')
const reportId = computed(() => route.params.id)
const planId = computed(() => route.params.planId)
const submitting = ref(false)

// 判断当前用户是否可以审核（管理员或审核人）
const canReview = computed(() => {
  if (isSuperAdmin.value || isAdmin.value) return true
  const currentUserId = JSON.parse(localStorage.getItem('user') || '{}').id
  return reportData.value.reviewer_id === currentUserId
})

// 判断当前用户是否可以归档或撤回（审核人或超管）
const canArchiveOrWithdraw = computed(() => {
  if (isSuperAdmin.value) return true
  const currentUserId = JSON.parse(localStorage.getItem('user') || '{}').id
  return reportData.value.reviewer_id === currentUserId
})

// 用例表格分页
const caseCurrentPage = ref(1)
const casePageSize = ref(50)

// Issue表格分页
const issueCurrentPage = ref(1)
const issuePageSize = ref(20)

// MpList表格分页
const mplistCurrentPage = ref(1)
const mplistPageSize = ref(20)

// 计算分页后的用例数据
const paginatedTestCases = computed(() => {
  const start = (caseCurrentPage.value - 1) * casePageSize.value
  const end = start + casePageSize.value
  return testCases.value.slice(start, end)
})

// 计算分页后的Issue数据
const paginatedIssueList = computed(() => {
  const start = (issueCurrentPage.value - 1) * issuePageSize.value
  const end = start + issuePageSize.value
  return issueList.value.slice(start, end)
})

// 计算分页后的MpList数据
const paginatedMplistData = computed(() => {
  const data = mplistData.value.rows || []
  const start = (mplistCurrentPage.value - 1) * mplistPageSize.value
  const end = start + mplistPageSize.value
  return data.slice(start, end)
})

// 用例分页事件
const handleCasePageChange = (page) => {
  caseCurrentPage.value = page
}

const handleCasePageSizeChange = (size) => {
  casePageSize.value = size
  caseCurrentPage.value = 1
}

// Issue分页事件
const handleIssuePageChange = (page) => {
  issueCurrentPage.value = page
}

const handleIssuePageSizeChange = (size) => {
  issuePageSize.value = size
  issueCurrentPage.value = 1
}

// MpList分页事件
const handleMplistPageChange = (page) => {
  mplistCurrentPage.value = page
}

const handleMplistPageSizeChange = (size) => {
  mplistPageSize.value = size
  mplistCurrentPage.value = 1
}

// MpList动态列宽：短表头用固定宽度，长表头（如"主题"）用min-width自适应
const getMplistColWidth = (header, colIdx) => {
  const len = (header || '').length
  if (len <= 4) return '80'
  if (len <= 8) return '120'
  return '180'
}

const currentYear = new Date().getFullYear()

const loadReportData = async () => {
  loadingStore.showLoading('生成报告中...')
  try {
    let res
    if (isSubmitPreviewMode.value) {
      // 从sessionStorage读取预览数据
      const cached = sessionStorage.getItem('submitPreviewData')
      if (!cached) {
        ElMessage.error('预览数据已过期，请返回重新生成')
        router.back()
        return
      }
      res = { code: 200, data: JSON.parse(cached) }
    } else if (isPreviewMode.value) {
      res = await previewTestPlanReport(planId.value)
    } else {
      res = await getReportDetail(reportId.value)
    }
    if (res.code === 200) {
      reportData.value = res.data.report
      testResults.value = res.data.test_results
      testCases.value = res.data.test_cases
      issueList.value = res.data.issue_list || []
      mplistData.value = res.data.mplist_data || { headers: [], rows: [] }
      includePrClosed.value = res.data.include_pr_closed || 0
      hasZmindCsv.value = res.data.has_zmind_csv || false
      reportTemplateConfig.value = res.data.report_template_config || null
      templateSelectedFields.value = res.data.report_template_config?.selected_fields || null
      hasAssist.value = res.data.has_assist || false

      // 存储报告名称供数据埋点使用
      if (res.data.report?.project_name) {
        sessionStorage.setItem(`report_name_${reportId.value}`, res.data.report.project_name)
      }

      // 构建测试结果汇总
      buildTestResultsSummary()
      
      // 构建Zmind数据（仅在上传了CSV时）
      if (hasZmindCsv.value) {
        buildZmindData(res.data.zmind_stats || {})
      } else {
        zmindData.value = []
      }
      
      // 构建封面数据（依赖上面两个表格的数据）
      buildCoverData()
    }
  } catch (error) {
    if (error?.response?.status === 404) {
      ElMessage.warning('该报告不存在或已被撤回')
      router.push('/testplans')
      return
    }
    ElMessage.error('加载报告数据失败')
  } finally {
    loadingStore.hideLoading()
    loading.value = false
  }
}

// Severity样式
const getSeverityClass = (severity) => {
  if (!severity) return ''
  const s = severity.toLowerCase()
  if (s === 'blocker') return 'severity-blocker'
  if (s === 'critical') return 'severity-critical'
  if (s === 'major') return 'severity-major'
  if (s === 'minor') return 'severity-minor'
  if (s === 'enhancement') return 'severity-enhancement'
  return ''
}

// 状态样式
const getStatusClass = (status) => {
  if (!status) return ''
  const openStatuses = ['New', 'On-going', 'Re-Open', 'Verification Failed', 'Info', 'Confirm']
  if (openStatuses.includes(status)) return 'status-open'
  if (['Closed', 'Suspended', 'Pending', 'Device Issue', 'App Issue', 'Confirm Issue'].includes(status)) return 'status-closed'
  return ''
}

// 检查字段是否在模板中选中（无模板时全部显示）
const isFieldVisible = (fieldKey) => {
  if (!templateSelectedFields.value || templateSelectedFields.value.length === 0) return true
  return templateSelectedFields.value.includes(fieldKey)
}

// 控制各大区块的显示
const showTestResults = computed(() => isFieldVisible('test_results'))
const showTestCases = computed(() => isFieldVisible('test_cases'))
const showZmindStats = computed(() => isFieldVisible('zmind_stats'))
const showIssueList = computed(() => isFieldVisible('issue_list'))

const buildCoverData = () => {
  const data = reportData.value
  
  // 从 Test Result Detail 表的 Total 行获取 Passing rate
  const totalRow = testResultsWithSummary.value.find(r => r.isTotal)
  const passingRateStr = totalRow ? totalRow.passing_rate : '0.00%'
  const passingRateNum = parseFloat(passingRateStr)
  
  let conclusion, releaseCriteria
  
  const templateConfig = reportTemplateConfig.value
  
  if (templateConfig && templateConfig.rules && templateConfig.rules.length > 0) {
    // 使用模板配置动态生成结论
    const result = generateConclusionFromTemplate(templateConfig, passingRateNum)
    conclusion = result.conclusion
    releaseCriteria = result.releaseCriteria
  } else {
    // 无模板配置，使用默认硬编码逻辑
    const result = generateConclusionDefault(passingRateNum)
    conclusion = result.conclusion
    releaseCriteria = result.releaseCriteria
  }
  
  // 所有封面行定义，带 fieldKey 标识可配置字段
  const allCoverRows = [
    { fieldKey: null, label: '项目名称\nProject name', value: data.project_name || '' },
    { fieldKey: 'test_cycle', label: '测试周期\nTest Cycle', value: data.test_cycle || '' },
    { fieldKey: 'testers', label: '测试人员\nTesters', value: data.testers || '' },
    { fieldKey: 'reviewer_name', label: '审核人员\nReviewer', value: data.reviewer_name || '' },
    { fieldKey: null, label: '验证环境\nVerified environment', value: (data.verify_env || '').replace(/\n/g, '<br/>') },
    { fieldKey: null, label: '提测内容\nRelease Note', value: (data.release_note || '').replace(/\n/g, '<br/>') },
    { fieldKey: 'test_conclusion', label: '测试结论\nTest Conclusion', value: conclusion },
    { fieldKey: 'release_criteria', label: '测试通过标准\nRelease Criteria', value: releaseCriteria },
    { fieldKey: null, label: '风险评估\nRisk Assessment', value: (data.risk_assessment || '').replace(/\n/g, '<br/>') },
    { fieldKey: 'remark', label: '备注\nRemark', value: (data.report_remark || '').replace(/\n/g, '<br/>') }
  ]
  
  // 根据模板 selected_fields 过滤：fieldKey 为 null 的始终显示，有 fieldKey 的按模板配置
  coverData.value = allCoverRows.filter(row => {
    if (!row.fieldKey) return true  // 不可配置字段始终显示
    return isFieldVisible(row.fieldKey)
  }).map(({ label, value }) => ({ label, value }))
}

// 比较函数
const compareValue = (actual, operator, threshold) => {
  if (operator === '>=') return actual >= threshold
  if (operator === '<=') return actual <= threshold
  if (operator === '=') return actual === threshold
  if (operator === '>') return actual > threshold
  if (operator === '<') return actual < threshold
  if (operator === '!=') return actual !== threshold
  return false
}

// 使用模板配置生成结论
const generateConclusionFromTemplate = (config, passRate) => {
  const rules = config.rules || []
  const conclusionPassText = config.conclusion_pass || 'Therefore, the test results meet the product release standards.'
  const conclusionFailText = config.conclusion_fail || 'Therefore, the test results fail to meet the product release criteria.'
  
  const passingRateStr = passRate.toFixed(2) + '%'
  let allMet = true
  const criteriaParts = []
  
  const zmindOpenRow = zmindData.value.find(r => r.isOpen)
  const zmindClosedRow = zmindData.value.find(r => r.isClosed)
  
  for (const rule of rules) {
    const metric = rule.metric || ''
    
    if (metric === 'testcase_pass_rate') {
      const op = rule.operator || '>='
      const val = rule.value || 95
      if (!compareValue(passRate, op, val)) allMet = false
      criteriaParts.push(`Testcase pass rate ${op}${val}%`)
    } else if (metric === 'open_pr_count') {
      const subRules = rule.sub_rules || []
      const prParts = []
      for (const sr of subRules) {
        const level = sr.level || ''
        const op = sr.operator || '='
        const val = sr.value || 0
        const actual = (hasZmindCsv.value && zmindOpenRow) ? (zmindOpenRow[level.toLowerCase()] || 0) : 0
        if (!compareValue(actual, op, val)) allMet = false
        prParts.push(`${level}${op}${val}`)
      }
      if (prParts.length) criteriaParts.push(`Open PR:${prParts.join(',')}`)
    } else if (metric === 'pr_closure_rate') {
      const subRules = rule.sub_rules || []
      const prParts = []
      for (const sr of subRules) {
        const level = sr.level || ''
        const op = sr.operator || '>='
        const val = sr.value || 100
        let actual = 100
        if (hasZmindCsv.value && zmindClosedRow) {
          actual = parseFloat(zmindClosedRow[level.toLowerCase()]) || 100
        }
        if (!compareValue(actual, op, val)) allMet = false
        prParts.push(`${level}${op}${val}%`)
      }
      if (prParts.length) criteriaParts.push(`PR closure rate: ${prParts.join(',')}`)
    }
  }
  
  const releaseCriteria = criteriaParts.length ? criteriaParts.join(';') + '。' : ''
  const meetsWord = allMet ? 'Meets' : 'Fails to meet'
  const resultText = allMet ? conclusionPassText : conclusionFailText
  const standardStr = criteriaParts.join(' & ')
  
  let actualStr
  if (hasZmindCsv.value && zmindOpenRow) {
    actualStr = `The test case pass rate has achieved ${passingRateStr},with Blocker PR=${zmindOpenRow.blocker || 0},Critical PR=${zmindOpenRow.critical || 0},Major PR=${zmindOpenRow.major || 0}; `
  } else {
    actualStr = `The test case pass rate has achieved ${passingRateStr}; `
  }
  
  const conclusion = `${actualStr}${meetsWord} the test standard of ${standardStr}； ${resultText}`
  
  return { conclusion, releaseCriteria }
}

// 默认硬编码结论生成（无模板时的回退逻辑）
const generateConclusionDefault = (passingRateNum) => {
  const passingRateStr = passingRateNum.toFixed(2) + '%'
  let conclusion, releaseCriteria
  
  if (hasZmindCsv.value) {
    const zmindOpenRow = zmindData.value.find(r => r.isOpen)
    const zmindClosedRow = zmindData.value.find(r => r.isClosed)
    
    const passRateMet = passingRateNum >= 95
    let prStandard, meetsWord, resultWord
    
    if (includePrClosed.value) {
      const blockerClosedRate = zmindClosedRow ? parseFloat(zmindClosedRow.blocker) : 100
      const criticalClosedRate = zmindClosedRow ? parseFloat(zmindClosedRow.critical) : 100
      const majorClosedRate = zmindClosedRow ? parseFloat(zmindClosedRow.major) : 100
      
      const allMet = passRateMet && blockerClosedRate >= 100 && criticalClosedRate >= 98 && majorClosedRate >= 90
      meetsWord = allMet ? 'Meets' : 'Fails to meet'
      resultWord = allMet ? 'meet' : 'fail to meet'
      prStandard = 'PR closure rate: Blocker=100%,Critical>=98%,Major>=90%'
      
      const openBlocker = zmindOpenRow ? zmindOpenRow.blocker : 0
      const openCritical = zmindOpenRow ? zmindOpenRow.critical : 0
      const openMajor = zmindOpenRow ? zmindOpenRow.major : 0
      
      conclusion = `The test case pass rate has achieved ${passingRateStr},with Blocker PR=${openBlocker},Critical PR=${openCritical},Major PR=${openMajor}; `
      conclusion += `${meetsWord} the test standard of Testcase Pass >=95% & ${prStandard}； Therefore, the test results ${resultWord} the product release criteria.`
      releaseCriteria = 'Testcase pass rate >=95%;PR closure rate: Blocker=100%,Critical>=98%,Major>=90%。'
    } else {
      const openBlocker = zmindOpenRow ? zmindOpenRow.blocker : 0
      const openCritical = zmindOpenRow ? zmindOpenRow.critical : 0
      const openMajor = zmindOpenRow ? zmindOpenRow.major : 0
      
      const allMet = passRateMet && openBlocker === 0 && openCritical === 0 && openMajor <= 5
      meetsWord = allMet ? 'Meets' : 'Fails to meet'
      resultWord = allMet ? 'meet' : 'fail to meet'
      prStandard = 'Open PR:Blocker=0,Critical=0,Major<=5'
      
      conclusion = `The test case pass rate has achieved ${passingRateStr},with Blocker PR=${openBlocker},Critical PR=${openCritical},Major PR=${openMajor}; `
      conclusion += `${meetsWord} the test standard of Testcase Pass >=95% & ${prStandard}； Therefore, the test results ${resultWord} the product release criteria.`
      releaseCriteria = 'Testcase pass rate >=95%;Open PR:Blocker=0,Critical=0,Major<=5。'
    }
  } else {
    const passRateMet = passingRateNum >= 95
    const meetsWord = passRateMet ? 'Meets' : 'Fails to meet'
    const resultWord = passRateMet ? 'meet' : 'fail to meet'
    
    conclusion = `The test case pass rate has achieved ${passingRateStr}; `
    conclusion += `${meetsWord} the test standard of Testcase Pass >=95%； Therefore, the test results ${resultWord} the product release criteria.`
    releaseCriteria = 'Testcase pass rate >=95%。'
  }
  
  return { conclusion, releaseCriteria }
}

const buildTestResultsSummary = () => {
  const results = [...testResults.value]
  
  // 检测是否有协测数据（后端可能已设置 has_assist，也从数据中检测）
  if (!hasAssist.value) {
    hasAssist.value = results.some(r => (r.assist || 0) > 0)
  }
  
  // 计算总计
  let totalCases = 0
  let totalPass = 0
  let totalFail = 0
  let totalBlock = 0
  let totalNt = 0
  let totalNa = 0
  let totalAssist = 0
  
  results.forEach(result => {
    totalCases += result.test_cases || 0
    totalPass += result.pass || 0
    totalFail += result.fail || 0
    totalBlock += result.block || 0
    totalNt += result.nt || 0
    totalNa += result.na || 0
    totalAssist += result.assist || 0
  })
  
  // Passing rate = PASS / test_cases（后端已经把 test_cases 设为有效用例数）
  const totalPassingRate = totalCases > 0 ? (totalPass / totalCases) : 0
  
  // 添加Total行
  const totalRow = {
    module: 'Total',
    test_cases: totalCases,
    pass: totalPass,
    fail: totalFail,
    block: totalBlock,
    nt: totalNt,
    na: totalNa,
    passing_rate: (totalPassingRate * 100).toFixed(2) + '%',
    isTotal: true
  }
  if (hasAssist.value) {
    totalRow.assist = totalAssist
  }
  results.push(totalRow)
  
  // 添加Test Case Passed行（PASS/FAIL/BLOCK/NT 参与百分比计算，NA/协测不参与）
  const totalExecuted = totalCases
  const passPercentage = totalExecuted > 0 ? (totalPass / totalExecuted) : 0
  const failPercentage = totalExecuted > 0 ? (totalFail / totalExecuted) : 0
  const blockPercentage = totalExecuted > 0 ? (totalBlock / totalExecuted) : 0
  const ntPercentage = totalExecuted > 0 ? (totalNt / totalExecuted) : 0

  const passedRow = {
    module: 'Test Case Passed',
    test_cases: ((passPercentage + failPercentage + blockPercentage + ntPercentage) * 100).toFixed(2) + '%',
    pass: (passPercentage * 100).toFixed(2) + '%',
    fail: (failPercentage * 100).toFixed(2) + '%',
    block: (blockPercentage * 100).toFixed(2) + '%',
    nt: (ntPercentage * 100).toFixed(2) + '%',
    na: '',
    passing_rate: totalPassingRate >= 0.95 ? 'OK' : 'NG',
    isPassed: true
  }
  if (hasAssist.value) {
    passedRow.assist = ''
  }
  results.push(passedRow)
  
  testResultsWithSummary.value = results
}

const buildZmindData = (zmindStats) => {
  if (!zmindStats || Object.keys(zmindStats).length === 0) {
    zmindData.value = []
    return
  }
  
  const totalPrs = zmindStats.total_prs || 0
  const blocker = zmindStats.blocker || 0
  const critical = zmindStats.critical || 0
  const major = zmindStats.major || 0
  const minor = zmindStats.minor || 0
  const enhancement = zmindStats.enhancement || 0
  
  const openBlocker = zmindStats.open_blocker || 0
  const openCritical = zmindStats.open_critical || 0
  const openMajor = zmindStats.open_major || 0
  const openMinor = zmindStats.open_minor || 0
  const openEnhancement = zmindStats.open_enhancement || 0
  const openCount = openBlocker + openCritical + openMajor + openMinor + openEnhancement
  
  // 计算各Severity关闭率
  const blockerClosedRate = blocker > 0 ? ((blocker - openBlocker) / blocker * 100) : 100
  const criticalClosedRate = critical > 0 ? ((critical - openCritical) / critical * 100) : 100
  const majorClosedRate = major > 0 ? ((major - openMajor) / major * 100) : 100
  
  // Conclusion判断标准（优先使用模板配置）
  let conclusion
  if (includePrClosed.value) {
    // 从模板配置读取 pr_closure_rate 规则
    const templateRules = reportTemplateConfig.value?.rules || []
    const prClosureRule = templateRules.find(r => r.metric === 'pr_closure_rate')
    if (prClosureRule && prClosureRule.sub_rules) {
      let allMet = true
      for (const sr of prClosureRule.sub_rules) {
        const level = (sr.level || '').toLowerCase()
        const op = sr.operator || '>='
        const val = sr.value || 100
        let actual = 100
        if (level === 'blocker') actual = blockerClosedRate
        else if (level === 'critical') actual = criticalClosedRate
        else if (level === 'major') actual = majorClosedRate
        if (!compareValue(actual, op, val)) allMet = false
      }
      conclusion = allMet ? 'OK' : 'NG'
    } else {
      // 无模板配置时使用默认标准
      conclusion = (blockerClosedRate >= 100 && criticalClosedRate >= 98 && majorClosedRate >= 90) ? 'OK' : 'NG'
    }
  } else {
    // 不统计PR closed时：从模板读取 open_pr_count 规则
    const templateRules = reportTemplateConfig.value?.rules || []
    const openPrRule = templateRules.find(r => r.metric === 'open_pr_count')
    if (openPrRule && openPrRule.sub_rules) {
      let allMet = true
      for (const sr of openPrRule.sub_rules) {
        const level = (sr.level || '').toLowerCase()
        const op = sr.operator || '='
        const val = sr.value || 0
        let actual = 0
        if (level === 'blocker') actual = openBlocker
        else if (level === 'critical') actual = openCritical
        else if (level === 'major') actual = openMajor
        if (!compareValue(actual, op, val)) allMet = false
      }
      conclusion = allMet ? 'OK' : 'NG'
    } else {
      // 无模板配置时使用默认标准
      conclusion = (openBlocker === 0 && openCritical === 0 && openMajor <= 5) ? 'OK' : 'NG'
    }
  }
  
  const rows = []
  
  // Open行（始终显示）
  rows.push({
    type: 'Open',
    prs: openCount,
    blocker: openBlocker,
    critical: openCritical,
    major: openMajor,
    minor: openMinor,
    enhancement: openEnhancement,
    conclusion: conclusion,
    isOpen: true
  })
  
  // 如果选择了统计PR closed，显示Total和PR closed行
  if (includePrClosed.value) {
    rows.push({
      type: 'Total',
      prs: totalPrs,
      blocker: blocker,
      critical: critical,
      major: major,
      minor: minor,
      enhancement: enhancement,
      conclusion: '',
      isTotal: true
    })
    
    const closedRate = totalPrs > 0 ? ((totalPrs - openCount) / totalPrs * 100) : 100
    const minorClosedRate = minor > 0 ? ((minor - openMinor) / minor * 100) : 100
    const enhancementClosedRate = enhancement > 0 ? ((enhancement - openEnhancement) / enhancement * 100) : 100
    
    rows.push({
      type: 'PR closed',
      prs: closedRate.toFixed(2) + '%',
      blocker: blockerClosedRate.toFixed(2) + '%',
      critical: criticalClosedRate.toFixed(2) + '%',
      major: majorClosedRate.toFixed(2) + '%',
      minor: minorClosedRate.toFixed(2) + '%',
      enhancement: enhancementClosedRate.toFixed(2) + '%',
      conclusion: '',
      isClosed: true
    })
  }
  
  zmindData.value = rows
}

// Zmind表格Conclusion列合并
const zmindSpanMethod = ({ row, column, rowIndex, columnIndex }) => {
  // Conclusion列（第7列，index=7）
  if (columnIndex === 7) {
    if (rowIndex === 0) {
      // 第一行合并所有行
      return { rowspan: zmindData.value.length, colspan: 1 }
    } else {
      // 其他行隐藏
      return { rowspan: 0, colspan: 0 }
    }
  }
}

const handleApprove = async () => {
  try {
    const res = await approveReport(reportId.value)
    if (res.code === 200) {
      ElMessage.success(t('report.approveSuccess'))
      goBack()
    }
  } catch (error) {
    ElMessage.error('审核失败')
  }
}

const handleReject = async () => {
  try {
    const { value: reason } = await ElMessageBox.prompt(
      t('report.rejectReasonTip'),
      t('report.rejectConfirmTitle'),
      {
        confirmButtonText: t('common.confirm'),
        cancelButtonText: t('common.cancel'),
        type: 'warning',
        inputType: 'textarea',
        inputPlaceholder: t('report.rejectReasonPlaceholder'),
        inputValidator: (val) => {
          if (!val || !val.trim()) return t('report.rejectReasonRequired')
          return true
        }
      }
    )
    
    const res = await rejectReport(reportId.value, { reject_reason: reason.trim() })
    if (res.code === 200) {
      ElMessage.success(t('report.rejectSuccess'))
      goBack()
    }
  } catch (error) {
    // 用户取消操作
    if (error === 'cancel' || error?.toString?.().includes('cancel')) {
      return
    }
    ElMessage.error('审核失败')
  }
}

const handleExportPdf = async () => {
  exportProgress.value = 0
  exportMessage.value = '正在启动导出...'
  exportDialogVisible.value = true
  try {
    const taskId = await startAsyncExport(reportId.value, 'pdf')
    await _pollAndDownload(taskId, reportData.value.project_name || 'report')
    ElMessage.success('PDF导出成功')
  } catch (error) {
    ElMessage.error(error.message || 'PDF导出失败')
  } finally {
    exportDialogVisible.value = false
  }
}

const handleExportExcel = async () => {
  exportProgress.value = 0
  exportMessage.value = '正在启动导出...'
  exportDialogVisible.value = true
  try {
    const taskId = await startAsyncExport(reportId.value, 'excel')
    await _pollAndDownload(taskId, reportData.value.project_name || 'report')
    ElMessage.success('Excel导出成功')
  } catch (error) {
    ElMessage.error(error.message || 'Excel导出失败')
  } finally {
    exportDialogVisible.value = false
  }
}

const _pollAndDownload = async (taskId, reportName) => {
  let retries = 0
  const maxRetries = 600
  while (retries < maxRetries) {
    const status = await pollExportStatus(taskId)
    if (status.status === 'completed') {
      exportProgress.value = 100
      exportMessage.value = '正在下载文件...'
      await downloadAsyncExport(taskId, reportName)
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
}

const handleArchiveCommand = async (command) => {
  if (command === 'archive') {
    try {
      await archiveReport(reportId.value)
      ElMessage.success('归档成功')
      loadReportData()
    } catch (error) {
      ElMessage.error('归档失败')
    }
  } else if (command === 'unarchive') {
    try {
      await unarchiveReport(reportId.value)
      ElMessage.success('撤回归档成功')
      loadReportData()
    } catch (error) {
      ElMessage.error('撤回归档失败')
    }
  } else if (command === 'withdraw') {
    try {
      await withdrawReport(reportId.value)
      ElMessage.success('撤回成功，报告已变为进行中')
      goBack()
    } catch (error) {
      ElMessage.error('撤回失败')
    }
  }
}

const goBack = () => {
  if (isSubmitPreviewMode.value) {
    // 清理预览数据
    sessionStorage.removeItem('submitPreviewData')
    router.back()
  } else if (isPreviewMode.value) {
    router.back()
  } else {
    router.push('/reports')
  }
}

// 返回修改 - 回到执行页面的信息填写对话框
const handleGoBackToEdit = () => {
  router.back()
}

// 确认提交 - 使用之前存储的FormData调用真正的提交接口
const handleConfirmSubmit = async () => {
  const formData = window.__submitReviewFormData
  const storedPlanId = window.__submitReviewPlanId
  
  if (!formData || !storedPlanId) {
    ElMessage.error('提交数据已过期，请返回重新生成报告')
    return
  }
  
  submitting.value = true
  try {
    const res = await submitTestPlanForReview(storedPlanId, formData)
    if (res.code === 200) {
      ElMessage.success('提交审核成功')
      // 清理临时数据
      sessionStorage.removeItem('submitPreviewData')
      delete window.__submitReviewFormData
      delete window.__submitReviewPlanId
      // 跳转到测试计划列表
      router.push('/testplans')
    } else {
      ElMessage.error(res.message || '提交审核失败')
    }
  } catch (error) {
    ElMessage.error('提交审核失败')
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  loadReportData()
})
</script>

<style scoped>
.report-review-container {
  padding: 0;
  max-width: 1400px;
  margin: 0 auto;
  background: #f8fafc;
  min-height: 100%;
}

.review-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: -24px -24px 24px -24px;
  padding: 16px 24px;
  border-bottom: 1px solid #e2e8f0;
  position: sticky;
  top: -24px;
  z-index: 100;
  background: #f8fafc;
}

.review-header h2 {
  margin: 0;
  color: #0f172a;
}

.review-actions {
  display: flex;
  gap: 10px;
}

/* ==================== */
/* 按钮 - 统一设计 */
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

.copyright-card {
  margin-bottom: 10px;
  border-radius: 8px;
}

.copyright-content {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 0;
}

.copyright-logo {
  height: 22px;
  object-fit: contain;
}

.copyright-text {
  font-size: 12px;
  color: #666;
  line-height: 1.6;
  text-align: right;
  flex: 1;
  margin-left: 20px;
}

.title-card {
  margin-bottom: 20px;
  border-radius: 8px;
  text-align: center;
}

.report-title {
  margin: 0 0 20px 0;
  font-size: 18px;
  font-weight: bold;
  color: #0f172a;
  text-align: center;
}

.report-main-card {
  margin-bottom: 24px;
  border-radius: 16px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.section-spacer {
  height: 30px;
}

.case-details {
  margin-bottom: 24px;
  border-radius: 16px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  overflow: hidden;
}

.case-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.case-count {
  font-size: 14px;
  color: #64748b;
}

.case-pagination {
  margin-top: 16px;
  padding: 16px 0 0;
  border-top: 1px solid #e2e8f0;
  justify-content: flex-end;
}

.case-pagination :deep(.el-pager li) {
  background: transparent;
  font-weight: 500;
  border-radius: 6px;
  min-width: 32px;
  height: 32px;
}

.case-pagination :deep(.el-pager li.is-active) {
  background: #eef2ff;
  color: #4f46e5;
  font-weight: 600;
}

.case-pagination :deep(.el-pager li:hover:not(.is-active)) {
  background: #f1f5f9;
}

.case-pagination :deep(.el-pagination__total) {
  font-size: 14px;
  color: #64748b;
}

.case-details h3 {
  margin-bottom: 20px;
  color: #303133;
}

.case-details :deep(.el-card__body) {
  padding: 20px;
}

.case-table-wrapper {
  width: 100%;
  overflow-x: auto;
}

.case-table-wrapper :deep(.el-table) {
  width: max-content;
  min-width: 100%;
}

.cell-ellipsis {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 100%;
}

.case-details :deep(.el-table th .cell) {
  white-space: nowrap !important;
}

.cover-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}

.cover-table td {
  border: 1px solid #000000;
  padding: 12px 8px;
  vertical-align: middle;
}

.cover-table .label-cell {
  width: 280px;
  font-weight: bold;
  text-align: center;
  white-space: normal;
  font-size: 13px;
  line-height: 1.4;
  background-color: #FFCC99;
}

.cover-table .content-cell {
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.6;
  font-size: 13px;
  overflow-wrap: break-word;
  text-align: left;
}

.result-table,
.zmind-table {
  margin-top: 0 !important;
}

.section-title {
  font-size: 16px;
  font-weight: bold;
  text-align: center;
  padding: 15px;
  background-color: #f1f5f9;
  margin-bottom: 0;
  border-radius: 4px;
  color: #0f172a;
}

.result-table {
  width: 100%;
}

.result-table :deep(.el-table__header-wrapper th) {
  background-color: #f1f5f9 !important;
  color: #0f172a !important;
  font-weight: bold;
}

.result-table :deep(.el-table__row .el-table__cell:first-child) {
  background-color: #f1f5f9 !important;
}

.result-table :deep(.el-table__row:nth-last-child(2) .el-table__cell),
.result-table :deep(.el-table__row:last-child .el-table__cell) {
  font-weight: bold;
}

.zmind-table {
  width: 100%;
}

.zmind-table :deep(.el-table__row .el-table__cell:first-child) {
  background-color: #f1f5f9 !important;
}

.zmind-table :deep(.el-table__header-wrapper th) {
  background-color: #f1f5f9 !important;
  color: #0f172a !important;
  font-weight: bold;
}

/* Conclusion合并单元格居中 */
.zmind-table :deep(td[rowspan]) {
  vertical-align: middle !important;
  text-align: center !important;
}

/* OK/NG 结论单元格样式 */
.conclusion-cell {
  display: inline-block;
  padding: 4px 16px;
  border-radius: 4px;
  font-weight: bold;
  font-size: 14px;
}

.conclusion-ok {
  background-color: #e8f5e9;
  color: #2e7d32;
}

.conclusion-ng {
  background-color: #ffebee;
  color: #c62828;
}

.result-note,
.severity-note {
  margin-top: 0;
  padding: 10px;
  font-size: 12px;
  color: #64748b;
  background-color: #f1f5f9;
  border-radius: 0;
  line-height: 1.6;
}

/* ===== 所有el-table统一黑色边框 + 表头表体一体化 ===== */
.report-main-card :deep(.el-table),
.case-details :deep(.el-table) {
  --el-table-border-color: #000000;
  border-color: #000000;
}

/* 表头和表体table使用相同的布局，确保列宽对齐 */
.report-main-card :deep(.el-table table),
.case-details :deep(.el-table table) {
  table-layout: fixed;
}

/* 表头和表体单元格边框 */
.report-main-card :deep(.el-table td.el-table__cell),
.report-main-card :deep(.el-table th.el-table__cell),
.case-details :deep(.el-table td.el-table__cell),
.case-details :deep(.el-table th.el-table__cell) {
  border-color: #000000 !important;
  border-right: 1px solid #000000 !important;
  border-bottom: 1px solid #000000 !important;
}

/* 表格外边框 */
.report-main-card :deep(.el-table--border),
.case-details :deep(.el-table--border) {
  border-color: #000000 !important;
  --el-table-border-color: #000000;
}

/* 表格四周伪元素边框线 */
.report-main-card :deep(.el-table--border::after),
.report-main-card :deep(.el-table--border::before),
.report-main-card :deep(.el-table__inner-wrapper::before),
.case-details :deep(.el-table--border::after),
.case-details :deep(.el-table--border::before),
.case-details :deep(.el-table__inner-wrapper::before) {
  background-color: #000000 !important;
}

.report-main-card :deep(.el-table--border .el-table__inner-wrapper::after),
.case-details :deep(.el-table--border .el-table__inner-wrapper::after) {
  background-color: #000000 !important;
}

/* 消除表头和表体之间的间隙/阴影，使其一体化 */
.report-main-card :deep(.el-table__header-wrapper),
.case-details :deep(.el-table__header-wrapper) {
  border-bottom: none;
}

.report-main-card :deep(.el-table__header-wrapper th.el-table__cell),
.case-details :deep(.el-table__header-wrapper th.el-table__cell) {
  border-bottom: 1px solid #000000 !important;
}

/* 去掉表头底部多余的分隔线 */
.report-main-card :deep(.el-table__header-wrapper::after),
.case-details :deep(.el-table__header-wrapper::after) {
  display: none !important;
}

/* 去掉表头默认的box-shadow分隔效果 */
.report-main-card :deep(.el-table .el-table__header-wrapper::after),
.report-main-card :deep(.el-table--border .el-table__header-wrapper::after),
.case-details :deep(.el-table .el-table__header-wrapper::after),
.case-details :deep(.el-table--border .el-table__header-wrapper::after) {
  display: none !important;
  height: 0 !important;
}

/* 去掉固定列的阴影效果 */
.report-main-card :deep(.el-table .el-table-fixed-column--left),
.report-main-card :deep(.el-table .el-table-fixed-column--right),
.case-details :deep(.el-table .el-table-fixed-column--left),
.case-details :deep(.el-table .el-table-fixed-column--right) {
  box-shadow: none !important;
}

/* 确保scrollbar不产生间隙 */
.report-main-card :deep(.el-table__header-wrapper .el-table-column--selection .cell),
.case-details :deep(.el-table__header-wrapper .el-table-column--selection .cell) {
  padding: 0;
}

/* 去掉el-table滚动条区域的间隙 */
.report-main-card :deep(.el-table .el-table__body-wrapper .el-scrollbar__bar),
.case-details :deep(.el-table .el-table__body-wrapper .el-scrollbar__bar) {
  display: none;
}

/* 消除表头gutter导致的列宽不对齐 */
.report-main-card :deep(.el-table__header-wrapper .gutter),
.case-details :deep(.el-table__header-wrapper .gutter) {
  width: 0 !important;
  display: none !important;
}

/* 确保body-wrapper没有多余的滚动条空间 */
.report-main-card :deep(.el-table .el-table__body-wrapper .el-scrollbar__wrap),
.case-details :deep(.el-table .el-table__body-wrapper .el-scrollbar__wrap) {
  overflow-x: hidden;
}

/* 去掉el-table__border-left-patch和border-bottom-patch */
.report-main-card :deep(.el-table__border-left-patch),
.report-main-card :deep(.el-table__border-bottom-patch),
.case-details :deep(.el-table__border-left-patch),
.case-details :deep(.el-table__border-bottom-patch) {
  background-color: #000000 !important;
}

/* 确保表头和表体之间没有额外的间距 */
.report-main-card :deep(.el-table__inner-wrapper),
.case-details :deep(.el-table__inner-wrapper) {
  display: flex;
  flex-direction: column;
}

/* 去掉表头滚动时的阴影 */
.report-main-card :deep(.el-table--scrollable-y .el-table__body-wrapper),
.case-details :deep(.el-table--scrollable-y .el-table__body-wrapper) {
  overflow-y: visible;
}

.el-table {
  margin-top: 20px;
}

/* 确保结果表格和zmind表格内容可以换行 */
.result-table :deep(.cell),
.zmind-table :deep(.cell) {
  white-space: normal !important;
  word-break: break-word;
  line-height: 1.5;
}

/* 表格滚动 */
.el-table :deep(.el-table__body-wrapper) {
  overflow-x: auto;
}

/* ===== Issue列表表格样式 ===== */
.issue-table-wrapper {
  width: 100%;
  overflow-x: auto;
}

.issue-table-wrapper :deep(.el-table) {
  width: max-content;
  min-width: 100%;
}

.issue-table {
  width: 100%;
}

.issue-table :deep(.el-table__header-wrapper th) {
  background-color: #f1f5f9 !important;
  color: #0f172a !important;
  font-weight: bold;
}

.cell-center {
  text-align: center;
}

/* Severity颜色样式 */
.severity-blocker {
  color: #f56c6c;
  font-weight: bold;
}

.severity-critical {
  color: #e6a23c;
  font-weight: bold;
}

.severity-major {
  color: #409eff;
  font-weight: bold;
}

.severity-minor {
  color: #67c23a;
}

.severity-enhancement {
  color: #909399;
}

/* 状态颜色样式 */
.status-open {
  color: #f56c6c;
  font-weight: bold;
}

.status-closed {
  color: #67c23a;
}

/* Issue详情卡片样式 */
.issue-details {
  margin-bottom: 24px;
  border-radius: 16px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  overflow: hidden;
}

.issue-details :deep(.el-card__body) {
  padding: 20px;
}

.issue-table-wrapper {
  width: 100%;
  overflow-x: auto;
}

.issue-table-wrapper :deep(.el-table) {
  width: max-content;
  min-width: 100%;
}

/* Issue表格也使用统一的黑色边框样式 */
.issue-details :deep(.el-table),
.issue-details :deep(.el-table--border) {
  --el-table-border-color: #000000;
  border-color: #000000;
}

/* 确保表头和表体使用相同的布局 */
.issue-details :deep(.el-table table) {
  table-layout: fixed;
}

.issue-details :deep(.el-table th.el-table__cell),
.issue-details :deep(.el-table td.el-table__cell) {
  border-color: #000000 !important;
  border-right: 1px solid #000000 !important;
  border-bottom: 1px solid #000000 !important;
}

/* 表头样式 */
.issue-details :deep(.el-table__header-wrapper th) {
  background-color: #E7E6E6 !important;
  color: #303133 !important;
  font-weight: bold;
}

.issue-details :deep(.el-table--border::after),
.issue-details :deep(.el-table--border::before),
.issue-details :deep(.el-table__inner-wrapper::before) {
  background-color: #000000 !important;
}

.issue-details :deep(.el-table--border .el-table__inner-wrapper::after) {
  background-color: #000000 !important;
}

.issue-details :deep(.el-table__header-wrapper) {
  border-bottom: none;
}

.issue-details :deep(.el-table__header-wrapper th.el-table__cell) {
  border-bottom: 1px solid #000000 !important;
}

.issue-details :deep(.el-table__header-wrapper::after),
.issue-details :deep(.el-table .el-table__header-wrapper::after),
.issue-details :deep(.el-table--border .el-table__header-wrapper::after) {
  display: none !important;
  height: 0 !important;
}

.issue-details :deep(.el-table__border-left-patch),
.issue-details :deep(.el-table__border-bottom-patch) {
  background-color: #000000 !important;
}

.issue-count {
  font-size: 14px;
  font-weight: normal;
  color: #64748b;
}

.issue-pagination {
  margin-top: 16px;
  padding: 16px 0 0;
  border-top: 1px solid #e2e8f0;
  justify-content: flex-end;
}

.issue-pagination :deep(.el-pager li) {
  background: transparent;
  font-weight: 500;
  border-radius: 6px;
  min-width: 32px;
  height: 32px;
}

.issue-pagination :deep(.el-pager li.is-active) {
  background: #eef2ff;
  color: #4f46e5;
  font-weight: 600;
}

/* MpList详情卡片样式 - 复用issue-details样式 */
.mplist-details {
  margin-bottom: 24px;
  border-radius: 16px;
}

.mplist-details :deep(.el-card__body) {
  padding: 20px;
}

.mplist-details :deep(.el-table),
.mplist-details :deep(.el-table--border) {
  --el-table-border-color: #000000;
  border-color: #000000;
}

.mplist-details :deep(.el-table table) {
  table-layout: fixed;
}

.mplist-details :deep(.el-table th.el-table__cell),
.mplist-details :deep(.el-table td.el-table__cell) {
  border-color: #000000 !important;
  border-right: 1px solid #000000 !important;
}

.mplist-details :deep(.el-table__header-wrapper th) {
  background-color: #E7E6E6 !important;
  color: #303133 !important;
}

.mplist-details :deep(.el-table--border::after),
.mplist-details :deep(.el-table--border::before),
.mplist-details :deep(.el-table__inner-wrapper::before) {
  background-color: #000000 !important;
}

.mplist-details :deep(.el-table--border .el-table__inner-wrapper::after) {
  background-color: #000000 !important;
}

.mplist-details :deep(.el-table__header-wrapper) {
  border-bottom: none;
}

.mplist-details :deep(.el-table__header-wrapper th.el-table__cell) {
  border-bottom: 1px solid #000000 !important;
}

.mplist-details :deep(.el-table__header-wrapper::after),
.mplist-details :deep(.el-table .el-table__header-wrapper::after),
.mplist-details :deep(.el-table--border .el-table__header-wrapper::after) {
  display: none !important;
  height: 0 !important;
}

.mplist-details :deep(.el-table__border-left-patch),
.mplist-details :deep(.el-table__border-bottom-patch) {
  background-color: #000000 !important;
}

.mplist-pagination {
  margin-top: 16px;
  padding: 16px 0 0;
  border-top: 1px solid #e2e8f0;
  justify-content: flex-end;
}

.mplist-pagination :deep(.el-pager li) {
  background: transparent;
  font-weight: 500;
  border-radius: 6px;
  min-width: 32px;
  height: 32px;
}

.mplist-pagination :deep(.el-pager li.is-active) {
  background: #eef2ff;
  color: #4f46e5;
  font-weight: 600;
}

.issue-pagination :deep(.el-pager li:hover:not(.is-active)) {
  background: #f1f5f9;
}

.issue-pagination :deep(.el-pagination__total) {
  font-size: 14px;
  color: #64748b;
}
</style>