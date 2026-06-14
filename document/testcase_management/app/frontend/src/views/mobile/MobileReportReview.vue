<template>
  <div class="mobile-page review-wrap">
    <header class="header">
      <button class="back" @click="router.back()">←</button>
      <h3 :title="title">{{ title }}</h3>
      <span></span>
    </header>

    <section class="mobile-card hero">
      <div class="badge">verified</div>
      <h2>{{ reportData.pass_rate || '-' }} PASS</h2>
      <p :title="reportData.project_name || '-'">{{ reportData.project_name || '-' }}</p>
    </section>

    <section class="mobile-card detail">
      <div class="row"><span>项目</span><strong class="value">{{ reportData.project_name || '-' }}</strong></div>
      <div class="row"><span>周期</span><strong class="value">{{ reportData.test_cycle || '-' }}</strong></div>
      <div class="row"><span>审核人</span><strong class="value">{{ reportData.reviewer_name || '-' }}</strong></div>
    </section>

    <button class="mobile-card pdf-btn" @click="downloadPdf">
      <div>
        <strong>Download Full Report</strong>
        <p>PDF Document</p>
      </div>
      <span>›</span>
    </button>

    <div v-if="showReviewActions" class="bottom-actions">
      <button class="mobile-pill-btn reject" @click="handleReject">Reject</button>
      <button class="mobile-pill-btn mobile-primary-btn" @click="handleApprove">Approve Report</button>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { approveReport, exportReportPdf, getReportDetail, rejectReport } from '../../api/report'
import { useUserRole } from '../../composables/useUserRole'

const route = useRoute()
const router = useRouter()
const reportData = ref({})
const { isSuperAdmin, isAdmin } = useUserRole()
const canReview = computed(() => {
  if (isSuperAdmin.value || isAdmin.value) return true
  const currentUserId = JSON.parse(localStorage.getItem('user') || '{}').id
  return Number(reportData.value.reviewer_id) === Number(currentUserId)
})
const showReviewActions = computed(() => reportData.value.status === 'PENDING_REVIEW' && canReview.value)

const title = computed(() => `${reportData.value.project_name || 'Test'} Report`)

const loadData = async () => {
  const res = await getReportDetail(route.params.id)
  reportData.value = res.data.report || {}
}

const downloadPdf = async () => {
  await exportReportPdf(route.params.id, reportData.value.project_name || 'report')
  ElMessage.success('PDF下载成功')
}

const handleApprove = async () => {
  await approveReport(route.params.id)
  ElMessage.success('审核通过')
  router.push('/m/reports')
}

const handleReject = async () => {
  try {
    const { value } = await ElMessageBox.prompt('请输入拒绝原因', 'Reject', {
      inputType: 'textarea',
      inputValidator: (val) => {
        if (!val || val.trim() === '') {
          return '拒绝原因不能为空'
        }
        return true
      },
      confirmButtonText: '确认拒绝',
      cancelButtonText: '取消'
    })
    
    if (!value || value.trim() === '') {
      ElMessage.warning('拒绝原因不能为空')
      return
    }
    
    await rejectReport(route.params.id, { reject_reason: value.trim() })
    ElMessage.success('已拒绝')
    router.push('/m/reports')
  } catch (error) {
    // 用户取消对话框，不做处理
    if (error === 'cancel' || error?.message === 'cancel') {
      return
    }
    // 其他错误
    console.error('拒绝失败:', error)
    ElMessage.error(error?.message || '拒绝失败，请重试')
  }
}

onMounted(loadData)
</script>

<style scoped>
.review-wrap { padding-bottom: 110px; }
.header { height: 52px; display:flex; align-items:center; justify-content:space-between; }
.back { border: none; background: transparent; color: #0058bb; font-size: 20px; width: 34px; }
.header h3 {
  margin: 0;
  font-size: 18px;
  max-width: 76%;
  line-height: 1.2;
  text-align: center;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  word-break: break-word;
}
.hero { margin-top: 10px; padding: 26px 16px; text-align: center; }
.hero .badge { width: 52px; height: 52px; margin: 0 auto 10px; border-radius: 50%; background: rgba(0,88,187,.12); display:flex; align-items:center; justify-content:center; color:#0058bb; font-size: 11px; font-weight: 800; }
.hero h2 { margin: 0; color: #0058bb; font-size: 36px; font-weight: 900; }
.hero p {
  margin-top: 8px;
  color: #5b5d63;
  overflow-wrap: anywhere;
  word-break: break-word;
}
.detail { margin-top: 12px; padding: 14px; }
.row { display:flex; justify-content:space-between; align-items: flex-start; gap: 10px; padding: 9px 0; border-bottom: 1px solid #eff1f7; font-size: 13px; }
.row:last-child { border-bottom: none; }
.row span { color: #70727a; }
.row .value {
  flex: 1;
  text-align: right;
  overflow-wrap: anywhere;
  word-break: break-word;
}
.pdf-btn { margin-top: 12px; width: 100%; border: none; padding: 14px; display:flex; align-items:center; justify-content:space-between; text-align:left; }
.pdf-btn p { margin: 4px 0 0; font-size: 12px; color: #6f7177; }
.pdf-btn span { font-size: 28px; color: #8a8d94; }
.bottom-actions { position: fixed; left: 16px; right: 16px; bottom: max(12px, env(safe-area-inset-bottom)); display:flex; gap: 10px; }
.bottom-actions .reject { flex: 1; background: #fff; border: 2px solid rgba(179, 27, 37, 0.2); color: #b31b25; }
.bottom-actions .mobile-primary-btn { flex: 1.6; }
</style>
