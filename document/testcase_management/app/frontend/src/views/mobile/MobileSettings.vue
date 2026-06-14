<template>
  <div class="mobile-page settings-wrap">
    <div class="top-sticky">
      
    </div>

    <section class="mobile-card profile">
      <div class="profile-main">
        <div class="name-row">
          <div class="name">{{ displayName }}</div>
        </div>
        <div class="sub">{{ userEmail }}</div>
        
      </div>
    </section>

    <div class="group-title">项目组</div>
    <section class="mobile-card group">
      <button class="item" type="button" @click="openTeamSheet">
        <span class="icon">👥</span>
        <div class="item-main">
          <div class="item-title">切换项目组</div>
          <div class="item-desc">查看对应项目组的数据</div>
        </div>
        <span class="value">{{ teamName }}</span>
        <span class="chev">›</span>
      </button>
      <div class="inline-sheet">
        <MobileTeamSwitcher ref="teamSwitcherRef" />
      </div>
    </section>

    <div class="group-title">账号</div>
    <section class="mobile-card group">
      <button class="item danger" type="button" @click="handleLogout">
        <span class="icon danger">⎋</span>
        <div class="item-main">
          <div class="item-title">退出登录</div>
          <div class="item-desc">退出当前账号并返回登录页</div>
        </div>
        <span class="chev">›</span>
      </button>
    </section>

    <!-- 退出登录确认弹窗 -->
    <el-dialog
      v-model="logoutDialogVisible"
      title="确认退出登录"
      width="85%"
      :show-close="false"
      class="logout-dialog"
      align-center
    >
      <div class="logout-content">
        <div class="logout-icon">⎋</div>
        <p class="logout-message">确定要退出当前账号吗？</p>
        <p class="logout-submessage">退出后将返回登录页面</p>
      </div>
      <template #footer>
        <div class="logout-actions">
          <el-button class="logout-cancel-btn" @click="logoutDialogVisible = false">取消</el-button>
          <el-button type="primary" class="logout-confirm-btn" @click="confirmLogout">确认退出</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import MobileTeamSwitcher from './MobileTeamSwitcher.vue'
import { useTeam } from '../../composables/useTeam'

const router = useRouter()
const teamSwitcherRef = ref(null)
const { currentTeam } = useTeam()
const logoutDialogVisible = ref(false)

const user = computed(() => {
  try {
    return JSON.parse(localStorage.getItem('user') || '{}')
  } catch {
    return {}
  }
})
const displayName = computed(() => user.value.username || user.value.full_name || '用户')
const userEmail = computed(() => user.value.email || '—')
const teamName = computed(() => currentTeam.value?.name || '未选择')
const avatarText = computed(() => (displayName.value || 'U').trim().slice(0, 1).toUpperCase())

const openTeamSheet = () => {
  // 触发子组件打开弹层（通过点击其按钮即可）
  const el = teamSwitcherRef.value?.$el
  const btn = el?.querySelector?.('button.team-pill')
  btn?.click?.()
}

const handleLogout = () => {
  logoutDialogVisible.value = true
}

const confirmLogout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  sessionStorage.removeItem('mobile_permissions_cache')
  logoutDialogVisible.value = false
  router.push('/m/login')
}
</script>

<style scoped>
.settings-wrap { padding: 8px 0 10px; }
.top-sticky {
  position: sticky;
  top: -12px;
  z-index: 12;
  background: #f6f6fb;
  padding: 14px 0 8px;
}
.title-row { display:flex; align-items:center; justify-content: space-between; }
.title-row h3 { margin: 0; font-size: 20px; font-weight: 900; letter-spacing: -0.02em; }

.profile {
  padding: 18px 16px;
  border-radius: 22px;
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 14px;
  background: linear-gradient(135deg, rgba(10, 102, 199, 0.12), rgba(74, 144, 255, 0.08));
  border: 1px solid rgba(0, 88, 187, 0.08);
}
.avatar {
  width: 54px;
  height: 54px;
  border-radius: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 900;
  color: #0a4c97;
  background: rgba(255, 255, 255, 0.86);
  border: 1px solid rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.10);
}
.profile-main { flex: 1; min-width: 0; }
.name-row { display: flex; align-items: center; gap: 8px; }
.name {
  font-size: 18px;
  font-weight: 900;
  letter-spacing: -0.02em;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.badge {
  font-size: 11px;
  font-weight: 900;
  color: #0a66c7;
  background: rgba(255, 255, 255, 0.75);
  border: 1px solid rgba(255, 255, 255, 0.7);
  border-radius: 999px;
  padding: 2px 8px;
}
.sub { margin-top: 4px; font-size: 13px; color: #5d6675; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.team-row { margin-top: 10px; display: flex; align-items: center; gap: 10px; }
.team-label { font-size: 12px; color: #4e5a6b; font-weight: 800; }
.team-name {
  font-size: 12px;
  font-weight: 900;
  color: #2b3a4f;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(255, 255, 255, 0.7);
  border-radius: 999px;
  padding: 4px 10px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 60vw;
}

.group-title {
  margin: 12px 4px 10px;
  font-size: 12px;
  font-weight: 900;
  letter-spacing: .12em;
  color: #7b8291;
}
.group { border-radius: 22px; overflow: hidden; margin-bottom: 14px; }
.item {
  width: 100%;
  padding: 14px 14px;
  display: flex;
  align-items: center;
  gap: 12px;
  text-align: left;
  background: #fff;
}
.icon {
  width: 36px;
  height: 36px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(10, 102, 199, 0.10);
  color: #0a66c7;
  font-size: 16px;
  flex-shrink: 0;
}
.icon.danger { background: rgba(179, 27, 37, 0.10); color: #b31b25; }
.item-main { flex: 1; min-width: 0; }
.item-title { font-size: 15px; font-weight: 900; color: #2e3440; }
.item-desc { margin-top: 3px; font-size: 12px; color: #6b7280; }
.value {
  font-size: 12px;
  font-weight: 900;
  color: #4b5563;
  max-width: 34vw;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.chev { color: #9aa2b1; font-size: 20px; }
.item.danger .item-title { color: #b31b25; }
.inline-sheet { height: 0; overflow: hidden; }

/* 退出登录弹窗内容样式 */
.logout-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px 0;
  text-align: center;
}

.logout-icon {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: rgba(179, 27, 37, 0.10);
  color: #b31b25;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  margin-bottom: 16px;
}

.logout-message {
  font-size: 17px;
  font-weight: 800;
  color: #2e3440;
  margin: 0 0 8px 0;
}

.logout-submessage {
  font-size: 13px;
  color: #6b7280;
  margin: 0;
}

.logout-actions {
  display: flex;
  gap: 12px;
  width: 100%;
}

.logout-cancel-btn {
  flex: 1;
  height: 46px;
  border-radius: 12px;
  font-weight: 700;
  border: 1px solid #e5e7eb;
  background: #f9fafb;
  color: #374151;
}

.logout-confirm-btn {
  flex: 1;
  height: 46px;
  border-radius: 12px;
  font-weight: 700;
  background: linear-gradient(135deg, #b31b25, #dc2626);
  border: none;
}
</style>

<style>
/* 全局样式覆盖 Element Plus Dialog */
.logout-dialog .el-dialog {
  border-radius: 22px;
  overflow: hidden;
  background: #fff;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
}

.logout-dialog .el-dialog__header {
  padding: 20px 20px 0;
  margin-right: 0;
  text-align: center;
}

.logout-dialog .el-dialog__title {
  font-weight: 900;
  font-size: 18px;
  color: #2e3440;
}

.logout-dialog .el-dialog__body {
  padding: 0 20px;
}

.logout-dialog .el-dialog__footer {
  padding: 0 20px 20px;
  border-top: none;
}
</style>
