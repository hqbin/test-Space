<template>
  <div class="mobile-page users-wrap">
    <div class="top-sticky">
      <header class="ops-head">
        <div class="ops">
          <button class="invite" @click="toEdit()">Invite</button>
          <button class="invite ghost" @click="router.push('/m/users/approvals')">Approvals</button>
        </div>
      </header>

      <input v-model="keyword" class="search" placeholder="Search by name, email or role..." />
    </div>

    <section class="cards">
      <article v-if="loading" v-for="n in 4" :key="'user-skeleton-' + n" class="mobile-card user-card skeleton-card">
        <div class="skeleton-line w50"></div>
        <div class="skeleton-line w70"></div>
        <div class="skeleton-line w40"></div>
      </article>
      <TransitionGroup name="card-fade-up" tag="div" class="cards-anim" appear>
        <article
          v-for="(u, idx) in filteredUsers"
          :key="u.id"
          class="mobile-card user-card"
          :style="{ '--card-delay': `${Math.min(idx, 6) * 40}ms` }"
          @click="toEdit(u.id)"
        >
          <div>
            <h3>{{ u.username || u.full_name }}</h3>
            <p>{{ u.email }}</p>
            <div class="tags">
              <span>{{ roleName(u.roleId) || 'Unassigned' }}</span>
              <span :class="u.status === 1 ? 'active' : 'off'">{{ u.status === 1 ? 'Active' : 'Offline' }}</span>
            </div>
          </div>
          <button class="status-switch" :class="{ on: u.status === 1 }" @click.stop="toggleStatus(u)">
            <span class="status-dot"></span>
          </button>
        </article>
      </TransitionGroup>
    </section>
    <button v-show="showBackTop" class="back-top-btn" @click="scrollToTop" aria-label="回到顶部">↑</button>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getRoles } from '../../api/role'
import { getUsers, toggleUserStatus } from '../../api/user'
import { useTeam } from '../../composables/useTeam'
import { useUserRole } from '../../composables/useUserRole'

const router = useRouter()
const keyword = ref('')
const rows = ref([])
const roles = ref([])
const loading = ref(false)
const showBackTop = ref(false)
const { teamList, loadTeams } = useTeam()
const { isSuperAdmin } = useUserRole()
let scrollEl = null

const myTeamIds = computed(() => (teamList.value || []).map(t => t.id))

const filteredUsers = computed(() => {
  const k = keyword.value.trim().toLowerCase()
  return rows.value.filter(u => {
    if (!isSuperAdmin.value && myTeamIds.value.length && Array.isArray(u.teamIds) && u.teamIds.length) {
      if (!u.teamIds.some(id => myTeamIds.value.includes(id))) return false
    }
    if (!k) return true
    return `${u.username || ''} ${u.email || ''}`.toLowerCase().includes(k)
  })
})

const roleName = (id) => (roles.value.find(r => r.id === id) || {}).name
const toEdit = (id) => router.push(id ? `/m/users/edit/${id}` : '/m/users/edit')
const toggleStatus = async (user) => {
  const toEnable = user.status !== 1
  const actionText = toEnable ? '启用' : '禁用'
  try {
    await ElMessageBox.confirm(`确认${actionText}用户 ${user.username}？`, '状态切换', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await toggleUserStatus(user.id)
    user.status = toEnable ? 1 : 0
    ElMessage.success(`${actionText}成功`)
  } catch {
    // cancel
  }
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

onMounted(async () => {
  scrollEl = document.querySelector('.layout-wrap .content')
  if (scrollEl) scrollEl.addEventListener('scroll', handleScroll, { passive: true })
  loading.value = true
  try {
    await loadTeams()
    const [userRes, roleRes] = await Promise.all([getUsers({ page: 1, size: 1000 }), getRoles({ page: 1, size: 1000 })])
    rows.value = userRes.data.records || []
    roles.value = roleRes.data.records || []
  } finally {
    loading.value = false
  }
})
onUnmounted(() => {
  if (scrollEl) scrollEl.removeEventListener('scroll', handleScroll)
})
</script>

<style scoped>
.users-wrap { padding-bottom: 10px; }
.top-sticky {
  position: sticky;
  top: -12px;
  z-index: 12;
  background: #f6f6fb;
  padding-top: 14px;
}
.ops-head { display:flex; justify-content: flex-end; align-items: center; margin-bottom: 12px; }
.ops { display:flex; gap: 8px; flex-shrink: 0; }
.invite { height: 36px; border: none; border-radius: 999px; padding: 0 14px; background: linear-gradient(135deg,#0a66c7,#4a90ff); color: #fff; font-weight: 800; }
.invite.ghost { background: #e9edf6; color: #4e5157; }
.search {
  width:100%;
  box-sizing: border-box;
  border: 1px solid transparent;
  border-radius: 16px;
  background: #fff;
  height: 50px;
  padding: 0 16px;
  margin-bottom: 12px;
  font-size: 16px;
}
.search:focus {
  outline: none;
  border-color: #8abfff;
  box-shadow: inset 0 0 0 1px #8abfff;
}
.cards { display:flex; flex-direction: column; gap: 12px; }
.cards-anim { display:flex; flex-direction: column; gap: 12px; }
.user-card { padding: 15px; display:flex; justify-content: space-between; align-items: flex-start; border-radius: 20px; }
.user-card h3 { margin: 0; font-size: 18px; }
.user-card p { margin: 6px 0 10px; color: #63656c; font-size: 13px; word-break: break-all; }
.status-switch {
  width: 44px;
  height: 26px;
  border-radius: 999px;
  background: #d4d7df;
  border: none;
  display: flex;
  align-items: center;
  padding: 0 3px;
  flex-shrink: 0;
  transition: background 0.2s;
}
.status-switch.on { background: linear-gradient(135deg, #0a66c7, #4a90ff); }
.status-dot {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.18);
  transform: translateX(0);
  transition: transform 0.2s;
}
.status-switch.on .status-dot { transform: translateX(18px); }
.tags { display:flex; gap: 8px; flex-wrap: wrap; }
.tags span { padding: 3px 10px; border-radius: 999px; font-size: 11px; font-weight: 700; background: #ebedf4; color: #61646b; }
.tags span.active { background: #e6f7eb; color: #158243; }
.tags span.off { background: #f2f4f7; color: #8a8c92; }
.skeleton-card {
  position: relative;
  overflow: hidden;
  flex-direction: column;
  align-items: stretch;
  gap: 8px;
}
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
  background: linear-gradient(135deg, #eceff5, #e5e8ef);
  animation: breathe 1.6s ease-in-out infinite;
}
.w40 { width: 40%; }
.w50 { width: 50%; }
.w70 { width: 70%; }
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
</style>
