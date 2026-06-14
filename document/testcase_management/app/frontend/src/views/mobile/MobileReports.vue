<template>
  <div class="mobile-page reports-wrap">
    <div class="top-sticky">
      <div class="search-row">
        <input v-model="keyword" :placeholder="t('report.searchPlaceholder')" />
      </div>

      <div class="chips">
        <button :class="{ active: statusFilter === '' }" @click="statusFilter = ''">{{ t('report.statusAll') }}</button>
        <button :class="{ active: statusFilter === 'PENDING_REVIEW' }" @click="statusFilter = 'PENDING_REVIEW'">{{ t('report.statusPendingReview') }}</button>
        <button :class="{ active: statusFilter === 'APPROVED' }" @click="statusFilter = 'APPROVED'">{{ t('report.statusApproved') }}</button>
      </div>
    </div>

    <section class="list">
      <article v-if="loading" v-for="n in 4" :key="'skeleton-' + n" class="mobile-card card skeleton-card">
        <div class="skeleton-line w30"></div>
        <div class="skeleton-line w90"></div>
        <div class="skeleton-line w60"></div>
        <div class="skeleton-line w70"></div>
        <div class="skeleton-btn"></div>
      </article>
      <TransitionGroup name="card-fade-up" tag="div" class="list-anim" appear>
        <article
          v-for="(row, idx) in filteredList"
          :key="row.id"
          class="mobile-card card"
          :style="{ '--card-delay': `${Math.min(idx, 6) * 40}ms` }"
        >
          <div class="head">
            <div class="title-wrap">
              <span class="status" :class="statusClass(row.status)">{{ statusText(row.status) }}</span>
              <h3>{{ getDisplayName(row) }}</h3>
            </div>
            <div class="metric-box">
              <span class="metric-label">通过率</span>
              <strong class="rate">{{ row.pass_rate || '-' }}</strong>
            </div>
          </div>
          <div class="meta">
            <span>执行人：{{ row.executors || '-' }}</span>
            <span>周期：{{ row.test_cycle || '-' }}</span>
          </div>
          <div class="actions">
            <button class="mobile-pill-btn mobile-primary-btn" @click="goReview(row)">View Details</button>
          </div>
        </article>
      </TransitionGroup>
    </section>
    <button v-show="showBackTop" class="back-top-btn" @click="scrollToTop" aria-label="回到顶部">↑</button>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import { getReports } from '../../api/report'
import { useTeam } from '../../composables/useTeam'
import { useUserRole } from '../../composables/useUserRole'

const router = useRouter()
const route = useRoute()
const { t } = useI18n()
const { isSuperAdmin } = useUserRole()
const keyword = ref('')
const statusFilter = ref('')
const allData = ref([])
const loading = ref(false)
const showBackTop = ref(false)
const { currentTeam, teamProjects, loadTeamProjects } = useTeam()
let scrollEl = null

const allTeamProjectIds = computed(() => (teamProjects.value || []).map(p => p.id))

const loadData = async () => {
  loading.value = true
  try {
    if (allTeamProjectIds.value.length === 0) {
      allData.value = []
      return
    }
    const params = { page: 1, size: 1000 }
    // 所有用户（包括超级管理员）都根据选择的项目组来显示数据
    if (currentTeam.value?.id) params.team_id = currentTeam.value.id
    params.project_ids = allTeamProjectIds.value.join(',')
    const res = await getReports(params)
    allData.value = res.data.records || []
  } finally {
    loading.value = false
  }
}

const filteredList = computed(() => {
  const k = keyword.value.trim().toLowerCase()
  return allData.value.filter(row => {
    if (row.status === 'REJECTED') return false
    if (statusFilter.value && row.status !== statusFilter.value) return false
    if (!k) return true
    const text = `${row.name || ''} ${row.project_name || ''}`.toLowerCase()
    return text.includes(k)
  })
})

const getDisplayName = (row) => (row.project_name || row.name || '').replace(/\s*-\s*测试报告$/, '')
const goReview = (row) => router.push(`/m/reports/review/${row.id}`)
const statusText = (status) => {
  if (status === 'PENDING_REVIEW') return t('report.statusPendingReview')
  if (status === 'APPROVED') return t('report.statusApproved')
  if (status === 'REJECTED') return t('report.statusRejected')
  return t('report.unknown')
}
const statusClass = (status) => {
  if (status === 'APPROVED') return 'ok'
  if (status === 'PENDING_REVIEW') return 'warn'
  return 'reject'
}
// 退出登录与项目组切换已移动到“设置”页

const handleScroll = () => {
  if (!scrollEl) return
  showBackTop.value = scrollEl.scrollTop > 280
}

const scrollToTop = () => {
  if (!scrollEl) return
  scrollEl.scrollTo({ top: 0, behavior: 'smooth' })
}

watch(allTeamProjectIds, loadData)
watch(
  () => currentTeam.value?.id,
  async (id, oldId) => {
    if (!id || Number(id) === Number(oldId)) return
    // 切换项目组时强制刷新对应项目组的项目列表与数据
    await loadTeamProjects()
    loadData()
    scrollToTop()
  }
)
onMounted(async () => {
  scrollEl = document.querySelector('.layout-wrap .content')
  if (scrollEl) scrollEl.addEventListener('scroll', handleScroll, { passive: true })
  if (!allTeamProjectIds.value.length && currentTeam.value) await loadTeamProjects()
  loadData()
})
onUnmounted(() => {
  if (scrollEl) scrollEl.removeEventListener('scroll', handleScroll)
})
</script>

<style scoped>
.reports-wrap { padding: 8px 0 10px; }
.top-sticky {
  position: sticky;
  top: -12px;
  z-index: 12;
  background: #f6f6fb;
  padding: 14px 0 2px;
}
.search-row { display: flex; align-items: center; gap: 10px; }
.search-row input {
  width: 100%;
  box-sizing: border-box;
  border: 1px solid transparent;
  height: 52px;
  border-radius: 16px;
  background: #e8ebf2;
  padding: 0 16px;
  font-size: 16px;
}
.search-row input:focus {
  outline: none;
  border-color: #8abfff;
  box-shadow: inset 0 0 0 1px #8abfff;
}
.chips { display:flex; gap:10px; overflow:auto; padding: 14px 0 16px; }
.chips button { white-space: nowrap; border: none; height: 36px; border-radius: 20px; padding: 0 14px; background: #e7e8ee; color: #55575d; font-weight: 800; font-size: 14px;}
.chips button.active { background: #0058bb; color: #fff; }
.list { display: flex; flex-direction: column; gap: 14px; }
.list-anim { display: flex; flex-direction: column; gap: 14px; }
.card { padding: 18px 16px; border-radius: 22px; }
.head { display:flex; justify-content: space-between; align-items:flex-start; gap: 12px; }
.title-wrap { flex: 1; min-width: 0; }
.head h3 { margin: 8px 0 0; font-size: 18px; line-height: 1.2; overflow-wrap: anywhere; word-break: break-word; }
.status { font-size: 11px; font-weight: 900; letter-spacing: .08em; }
.status.ok { color: #15914a; }
.status.warn { color: #cb8a00; }
.status.reject { color: #b31b25; }
.metric-box { display: flex; flex-direction: column; align-items: flex-end; gap: 4px; min-width: 86px; }
.metric-label { font-size: 11px; color: #7d8088; font-weight: 700; }
.rate { flex-shrink: 0; min-width: 72px; text-align: right; font-size: 14px; line-height: 1.1; }
.meta { display:flex; flex-direction: column; gap: 5px; margin: 14px 0; color: #5e6066; font-size: 13px; }
.actions button { width: 100%; }
.skeleton-card { position: relative; overflow: hidden; }
.skeleton-card::after {
  content: '';
  position: absolute;
  inset: 0;
  transform: translateX(-100%);
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.65), transparent);
  animation: shimmer 1.4s infinite;
}
.skeleton-line {
  height: 12px;
  border-radius: 8px;
  margin-bottom: 10px;
  background: linear-gradient(135deg, #eceff5, #e5e8ef);
  animation: breathe 1.6s ease-in-out infinite;
}
.skeleton-btn {
  margin-top: 8px;
  height: 40px;
  border-radius: 999px;
  background: linear-gradient(135deg, #d9deea, #e2e6f1);
  animation: breathe 1.6s ease-in-out infinite;
}
.w30 { width: 30%; }
.w60 { width: 60%; }
.w70 { width: 70%; }
.w90 { width: 90%; }
@keyframes breathe {
  0%, 100% { opacity: 0.95; }
  50% { opacity: 0.58; }
}
@keyframes shimmer {
  100% { transform: translateX(100%); }
}
.card-fade-up-enter-active {
  transition: opacity 260ms ease, transform 260ms ease;
  transition-delay: var(--card-delay, 0ms);
}
.card-fade-up-leave-active { transition: opacity 180ms ease, transform 180ms ease; }
.card-fade-up-enter-from,
.card-fade-up-leave-to {
  opacity: 0;
  transform: translate3d(0, 8px, 0) scale(0.995);
}
.back-top-btn {
  position: fixed;
  right: 22px;
  bottom: calc(max(92px, env(safe-area-inset-bottom) + 84px));
  width: 42px;
  height: 42px;
  border-radius: 21px;
  background: rgba(255, 255, 255, 0.86);
  border: 1px solid rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  color: #3d5f88;
  font-size: 20px;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 20px rgba(15, 23, 42, 0.14);
  z-index: 30;
}

@media (max-width: 480px) {
  .head h3 { font-size: 18px; }
  .rate { font-size: 14px; min-width: 66px; }
  .meta { font-size: 13px; }
}
</style>
