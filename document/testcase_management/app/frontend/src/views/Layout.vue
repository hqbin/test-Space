<template>
  <el-container class="layout-container">
    <!-- Demo风格侧边栏 - 深色背景 -->
    <el-aside :width="isCollapse ? '64px' : '256px'" class="sidebar-demo">
      <div class="logo-container-demo" :style="isCollapse ? 'padding: 0 4px;' : ''">
        <div v-if="!isCollapse" class="logo-full-demo">
          <div class="logo-text-demo">TeVaMaT</div>
          <div class="logo-sub-demo">TEst & VAlidation MAnagement Tool</div>
        </div>
        <div v-else class="logo-text-collapsed">TeVaMaT</div>
      </div>
      
      <div class="collapse-button-demo" @click="toggleCollapse">
        <el-icon :size="14">
          <DArrowLeft v-if="!isCollapse" />
          <DArrowRight v-else />
        </el-icon>
      </div>
      
      <nav class="sidebar-nav">
        <div 
          v-for="menu in userMenus.menus" 
          :key="menu.key" 
          class="nav-item"
          :class="{ 'is-active': activeMenu === menu.path }"
          @click="handleNavClick(menu.path)"
        >
          <el-icon class="nav-icon"><component :is="menu.icon" /></el-icon>
          <span v-if="!isCollapse" class="nav-label">{{ $t(menu.nameKey) }}</span>
        </div>
        
        <!-- 应用管理 -->
        <div v-if="userMenus.aivoiceMenus.length > 0">
          <div
            class="nav-item nav-group-title"
            @click="aivoiceExpanded = !aivoiceExpanded"
          >
            <el-icon class="nav-icon"><Microphone /></el-icon>
            <span v-if="!isCollapse" class="nav-label">{{ $t('menu.aivoice') }}</span>
            <el-icon v-if="!isCollapse" class="nav-arrow" :class="{ 'is-expanded': aivoiceExpanded }"><ArrowDown /></el-icon>
          </div>
          <div v-show="aivoiceExpanded && !isCollapse" class="nav-sub-items">
            <div
              v-for="menu in userMenus.aivoiceMenus"
              :key="menu.key"
              class="nav-item nav-sub-item"
              :class="{ 'is-active': activeMenu === menu.path }"
              @click="handleNavClick(menu.path)"
            >
              <el-icon class="nav-icon"><component :is="menu.icon" /></el-icon>
              <span class="nav-label">{{ $t(menu.nameKey) }}</span>
            </div>
          </div>
        </div>

        <div v-if="userMenus.adminMenus.length > 0">
          <div 
            class="nav-item nav-group-title"
            :class="{ 'is-active': adminMenuPaths.includes(activeMenu) }"
            @click="adminExpanded = !adminExpanded"
          >
            <el-icon class="nav-icon"><Setting /></el-icon>
            <span v-if="!isCollapse" class="nav-label">{{ $t('menu.systemManagement') }}</span>
            <el-icon v-if="!isCollapse" class="nav-arrow" :class="{ 'is-expanded': adminExpanded }"><ArrowDown /></el-icon>
          </div>
          <div v-show="adminExpanded && !isCollapse" class="nav-sub-items">
            <div 
              v-for="menu in userMenus.adminMenus" 
              :key="menu.key" 
              class="nav-item nav-sub-item"
              :class="{ 'is-active': activeMenu === menu.path }"
              @click="handleNavClick(menu.path)"
            >
              <el-icon class="nav-icon"><component :is="menu.icon" /></el-icon>
              <span class="nav-label">{{ $t(menu.nameKey) }}</span>
            </div>
          </div>
        </div>

        <!-- ADB工具（点击打开独立页面） -->
        <div v-for="menu in userMenus.standaloneMenus" :key="menu.key">
          <template v-if="menu.key === 'adbTool'">
            <div 
              class="nav-item"
              @click="openAdbTool"
            >
              <el-icon class="nav-icon"><component :is="menu.icon" /></el-icon>
              <span v-if="!isCollapse" class="nav-label">{{ $t(menu.nameKey) }}</span>
              <el-icon v-if="!isCollapse" class="nav-external-icon"><Link /></el-icon>
            </div>
          </template>
          <template v-else>
            <div 
              class="nav-item"
              :class="{ 'is-active': activeMenu === menu.path }"
              @click="handleNavClick(menu.path)"
            >
              <el-icon class="nav-icon"><component :is="menu.icon" /></el-icon>
              <span v-if="!isCollapse" class="nav-label">{{ $t(menu.nameKey) }}</span>
            </div>
          </template>
        </div>
      </nav>
      
      <!-- 底部Logo -->
      <div class="sidebar-bottom-logo">
        <img src="@/assets/images/whaletv-logo.png" alt="WhaleTV" :class="{ 'collapsed': isCollapse }" />
      </div>
    </el-aside>

    <el-container>
      <!-- Demo风格顶部栏 - 白色背景 -->
      <el-header class="header-demo">
        <div class="header-left-demo">
          <!-- 全局项目组选择器 -->
          <div class="team-selector-wrapper-demo">
            <TeamSelector @change="handleTeamChange" />
          </div>
        </div>
        <div class="header-right-demo">
          <div v-if="hasFeature('notificationBell')" class="notification-bell-demo" @click="showNotificationDrawer = true">
            <el-badge :value="unreadCount" :hidden="unreadCount === 0" :max="99">
              <el-icon :size="18"><Bell /></el-icon>
            </el-badge>
          </div>
          
          <el-dropdown @command="handleLanguageChange" class="language-selector-demo" trigger="click">
            <div class="language-button-demo">
              <el-icon :size="18"><Operation /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="zh-CN">
                  <span :class="{ 'active-lang': currentLanguage === 'zh-CN' }">简体中文</span>
                </el-dropdown-item>
                <el-dropdown-item command="en-US">
                  <span :class="{ 'active-lang': currentLanguage === 'en-US' }">English</span>
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          
          <div class="header-divider"></div>
          
          <el-dropdown @command="handleCommand" class="user-dropdown-demo" trigger="click" popper-class="user-dropdown-popper">
            <div class="user-info-header-demo">
              <el-avatar :size="32" :src="userAvatarUrl" class="user-avatar-demo">
                <span class="avatar-letter">{{ (currentUser.username || 'U').charAt(0).toUpperCase() }}</span>
              </el-avatar>
              <span class="username-demo">{{ currentUser.username || $t('common.user') }}</span>
              <el-icon class="dropdown-icon-demo"><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item disabled class="user-info-item">
                  <div class="user-detail">
                    <div class="user-name">{{ currentUser.username }}</div>
                    <div class="user-email">{{ currentUser.email || '' }}</div>
                  </div>
                </el-dropdown-item>
                <el-dropdown-item divided command="profile">
                  <el-icon><User /></el-icon>
                  <span>{{ $t('menu.profile') }}</span>
                </el-dropdown-item>
                <el-dropdown-item command="versionInfo" v-if="hasFeature('versionInfo')">
                  <el-icon><InfoFilled /></el-icon>
                  <span>版本信息</span>
                </el-dropdown-item>
                <el-dropdown-item divided command="feedback">
                  <el-icon><ChatDotRound /></el-icon>
                  <span>意见反馈</span>
                </el-dropdown-item>
                <el-dropdown-item divided command="logout">
                  <el-icon><SwitchButton /></el-icon>
                  <span>{{ $t('common.logout') }}</span>
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main class="main-content-demo">
        <div v-if="loadingStore.isLoading" class="content-loading-mask">
          <div class="loading-spinner">
            <svg class="spinner-icon" viewBox="0 0 50 50">
              <circle class="spinner-path" cx="25" cy="25" r="20" fill="none" stroke-width="4"></circle>
            </svg>
            <div class="loading-text">{{ loadingStore.loadingText }}</div>
          </div>
        </div>
        <router-view v-slot="{ Component, route: viewRoute }">
          <keep-alive :include="cachedViews">
            <component :is="Component" :key="viewRoute.name" />
          </keep-alive>
        </router-view>
      </el-main>
    </el-container>
    
    <el-drawer
      v-model="showNotificationDrawer"
      :title="$t('notification.title')"
      direction="rtl"
      size="900px"
      :close-on-click-modal="true"
      @open="onNotificationDrawerOpen"
    >
      <NotificationList ref="notificationListRef" :is-drawer="true" @update-count="loadUnreadCount" />
    </el-drawer>

    <VersionInfoDialog v-model="showVersionInfoDialog" />

  </el-container>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { eventBus } from '../utils/eventBus'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Document, Calendar, VideoPlay, Link, Setting, User, Folder,
  Expand, Fold, ArrowDown, SwitchButton, Checked, Tickets, DataAnalysis, DocumentChecked, UserFilled, Operation, DArrowLeft, DArrowRight, Bell, OfficeBuilding, Files, Iphone, TrendCharts, ChatDotRound, InfoFilled, Microphone, Edit, Collection, Connection
} from '@element-plus/icons-vue'
import TeamSelector from '../components/TeamSelector.vue'
import NotificationList from './notification/NotificationList.vue'
import VersionInfoDialog from '../components/VersionInfoDialog.vue'
import { useUserRole } from '../composables/useUserRole'
import { useNotification } from '../composables/useNotification'
import { useUserStore } from '../stores/user'
import { useLoadingStore } from '../stores/loading'

const { userMenus, loadUserRoles, hasFeature } = useUserRole()
const { unreadCount, connected, startRealtime, stopRealtime, fetchUnreadCount } = useNotification()
const { locale, t } = useI18n()
const userStore = useUserStore()
const loadingStore = useLoadingStore()

const router = useRouter()
const route = useRoute()
const isCollapse = ref(false)
const currentLanguage = ref(localStorage.getItem('language') || 'zh-CN')
const showNotificationDrawer = ref(false)
const showVersionInfoDialog = ref(false)
const notificationListRef = ref(null)
let pollTimer = null

const onNotificationDrawerOpen = () => {
  if (notificationListRef.value && notificationListRef.value.loadData) {
    notificationListRef.value.loadData()
  }
}

const activeMenu = computed(() => route.path)

const adminExpanded = ref(false)
const aivoiceExpanded = ref(false)
const adminMenuPaths = computed(() => 
  userMenus.value.adminMenus.map(m => m.path)
)

// ADB工具 - 打开独立页面
const openAdbTool = () => {
  window.open('/adb-tool-public', '_blank')
}

// 缓存重页面，避免每次导航都重新创建组件
const cachedViews = ref([
  'Dashboard',
  'TestCaseList',
  'TestPlanList',
  'ReportList',
  'ZmindIntegration',
  'ReviewPlanList',
  'ProjectModuleManagement'
])

// 处理项目组切换 - 数据刷新由 teams-changed 事件驱动，无需强制路由刷新
const handleTeamChange = (team) => {
  // switchTeam 已通过 eventBus emit 'teams-changed'，各页面自行响应
}

const currentUser = computed(() => userStore.userInfo || {})

const userAvatarUrl = computed(() => userStore.avatarUrl)

const userRoleLabel = computed(() => {
  const user = JSON.parse(localStorage.getItem('user') || '{}')
  const roleName = user.roleName || ''

  if (user.username === 'admin' || user.username === 'super') {
    return t('layout.admin')
  }

  return roleName || t('layout.admin')
})

const loadUnreadCount = async () => {
  await fetchUnreadCount()
}

const handleLanguageChange = (lang) => {
  currentLanguage.value = lang
  locale.value = lang
  localStorage.setItem('language', lang)
  ElMessage.success(lang === 'zh-CN' ? t('common.switchLangZh') : t('common.switchLangEn'))
}

const pageNames = computed(() => ({
  '/testcases': t('layout.pageNames.testcases'),
  '/testplans': t('layout.pageNames.testplans'),
  '/reports': t('layout.pageNames.reports'),
  '/zmind': t('layout.pageNames.zmind'),
  '/users': t('layout.pageNames.users'),
  '/projects': t('layout.pageNames.projects'),
  '/roles': t('layout.pageNames.roles'),
  '/notifications': t('layout.pageNames.notifications'),
  '/system-log': t('layout.pageNames.systemLog')
}))

const currentPageName = computed(() => {
  return pageNames.value[route.path] || t('layout.home')
})

const toggleCollapse = () => {
  isCollapse.value = !isCollapse.value
}

// 响应外部请求折叠/展开导航栏（如批量新建对话框）
const _onNavCollapse = (collapsed) => {
  isCollapse.value = collapsed
}
eventBus.on('nav-collapse', _onNavCollapse)

// 进入需要折叠侧边栏的页面时自动折叠，离开时恢复
watch(
  () => route.meta.collapseSidebar,
  (shouldCollapse) => {
    if (shouldCollapse) {
      isCollapse.value = true
    } else {
      isCollapse.value = false
    }
  },
  { immediate: true }
)

const handleNavClick = (path) => {
  if (path === route.path) return
  router.push(path)
}

const handleCommand = (command) => {
  if (command === 'logout') {
    ElMessageBox.confirm(
      t('common.logout') + '?', 
      t('user.deleteTitle'), 
      {
        confirmButtonText: t('common.confirm'),
        cancelButtonText: t('common.cancel'),
        type: 'warning'
      }
    ).then(() => {
      localStorage.removeItem('token')
      userStore.clearUser()
      ElMessage.success(t('common.logout') + t('common.success'))
      router.push('/login')
    }).catch(() => {})
  } else if (command === 'profile') {
    router.push('/profile')
  } else if (command === 'feedback') {
    window.open('https://zmind.whaletv.com/projects/tms-optimization/issues', '_blank')
  } else if (command === 'versionInfo') {
    showVersionInfoDialog.value = true
  } else if (command === 'settings') {
    ElMessage.info(t('common.settingsDev'))
  }
}

onMounted(async () => {
  await loadUserRoles()
  if (hasFeature('notificationBell')) {
    startRealtime()
    // 基线轮询：每60秒刷新未读数，WebSocket已覆盖实时场景
    pollTimer = setInterval(() => {
      fetchUnreadCount()
    }, 60000)
  }
})

onUnmounted(() => {
  stopRealtime()
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
  eventBus.off('nav-collapse', _onNavCollapse)
})
</script>

<style scoped>
.layout-container {
  height: 100%;
  background: #f8fafc;
}

/* ==================== */
/* Demo风格侧边栏 - 深色背景 */
/* ==================== */
.sidebar-demo {
  background: #0f172a;
  transition: width 0.15s ease-out !important;
  overflow: hidden;
  border-right: 1px solid #1e293b;
  position: relative;
  display: flex;
  flex-direction: column;
  will-change: width;
  transform: translateZ(0);
  flex-shrink: 0;
  contain: layout style;
}

.logo-container-demo {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 24px;
  border-bottom: 1px solid #1e293b;
  overflow: hidden;
}

.logo-full-demo {
  display: flex;
  flex-direction: column;
  width: 100%;
}

.logo-text-demo {
  font-size: 16px;
  font-weight: 700;
  color: #fff;
  letter-spacing: -0.3px;
}

.logo-sub-demo {
  font-size: 10px;
  color: #94a3b8;
  margin-top: 2px;
}

.logo-text-collapsed {
  font-size: 11px;
  font-weight: 700;
  color: #fff;
  text-align: center;
  width: 100%;
  white-space: nowrap;
  overflow: visible;
  letter-spacing: 0px;
}

.collapse-button-demo {
  position: absolute;
  right: -12px;
  top: 50%;
  transform: translateY(-50%);
  width: 24px;
  height: 48px;
  background: #1e293b;
  border: none;
  border-radius: 0 12px 12px 0;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 100;
  opacity: 0;
  transition: opacity 0.15s, background-color 0.15s;
}

.sidebar-demo:hover .collapse-button-demo {
  opacity: 1;
}

.collapse-button-demo:hover {
  background: #334155;
}

.collapse-button-demo :deep(.el-icon) {
  color: #94a3b8;
}

/* 自定义导航菜单 - 纯 CSS，无 Element Plus 开销 */
.sidebar-nav {
  padding: 24px 12px;
  flex: 1;
  overflow-y: auto;
  contain: content;
}

.sidebar-bottom-logo {
  padding: 16px;
  display: flex;
  justify-content: center;
  align-items: center;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.sidebar-bottom-logo img {
  width: 120px;
  opacity: 0.6;
  transition: opacity 0.2s;
}

.sidebar-bottom-logo img:hover {
  opacity: 0.9;
}

.sidebar-bottom-logo img.collapsed {
  width: 32px;
}

.nav-item {
  display: flex;
  align-items: center;
  height: 44px;
  padding: 0 12px;
  margin: 4px 0;
  border-radius: 8px;
  color: #94a3b8;
  font-size: 14px;
  font-weight: 400;
  cursor: pointer;
  user-select: none;
  will-change: background-color;
}

.nav-item:hover {
  background: #1e293b;
  color: #fff;
}

.nav-item:hover .nav-icon {
  color: #94a3b8;
}

.nav-item:active {
  background: #334155;
}

.nav-item.is-active {
  background: rgba(99, 102, 241, 0.1);
  color: #818cf8;
  font-weight: 500;
}

.nav-item.is-active .nav-icon {
  color: #818cf8;
}

.nav-icon {
  color: #64748b;
  font-size: 18px;
  margin-right: 12px;
  flex-shrink: 0;
}

.nav-label {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.nav-arrow {
  font-size: 12px;
  color: #64748b;
  transition: transform 0.15s;
  flex-shrink: 0;
}

.nav-arrow.is-expanded {
  transform: rotate(180deg);
}

.nav-external-icon {
  font-size: 12px;
  color: #94a3b8;
  margin-left: auto;
  flex-shrink: 0;
}

.nav-sub-items {
  padding-left: 8px;
}

.nav-sub-item {
  height: 40px;
  font-size: 14px;
  margin: 2px 0;
}

.nav-group-title {
  position: relative;
}

/* ==================== */
/* Demo风格顶部栏 - 白色背景 */
/* ==================== */
.header-demo {
  background: #fff;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  height: 64px !important;
  z-index: 10;
  flex-shrink: 0;
}

.header-left-demo {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-right-demo {
  display: flex;
  align-items: center;
  gap: 16px;
}

.team-selector-wrapper-demo {
  display: flex;
  align-items: center;
}

.team-selector-wrapper-demo :deep(.el-select) {
  --el-fill-color-blank: transparent;
  --el-border-color: transparent;
}

.team-selector-wrapper-demo :deep(.el-input__wrapper) {
  background-color: transparent !important;
  border: none !important;
  box-shadow: none !important;
  padding: 4px 12px;
  border-radius: 8px;
}

.team-selector-wrapper-demo :deep(.el-input__wrapper:hover) {
  background-color: #f1f5f9 !important;
}

.team-selector-wrapper-demo :deep(.el-input.is-focus .el-input__wrapper) {
  background-color: #fff !important;
  box-shadow: 0 0 0 1px #4f46e5 inset !important;
}

.team-selector-wrapper-demo :deep(.el-input__inner) {
  color: #334155;
  font-weight: 500;
  font-size: 14px;
}

.team-selector-wrapper-demo :deep(.el-select__caret) {
  color: #94a3b8;
  font-size: 12px;
}

.notification-bell-demo {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.1s !important;
  position: relative;
}

.notification-bell-demo:hover {
  background: #f1f5f9;
}

.notification-bell-demo .el-icon {
  color: #64748b;
}

.notification-bell-demo:hover .el-icon {
  color: #475569;
}

.notification-bell-demo :deep(.el-badge__content) {
  background: #f43f5e;
  border: 2px solid #fff;
  font-size: 10px;
  height: 16px;
  line-height: 12px;
  padding: 0 4px;
  min-width: 16px;
}

.language-selector-demo {
  cursor: pointer;
}

.language-button-demo {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.1s !important;
}

.language-button-demo:hover {
  background: #f1f5f9;
}

.language-button-demo .el-icon {
  color: #64748b;
}

.language-button-demo:hover .el-icon {
  color: #475569;
}

.header-divider {
  width: 1px;
  height: 24px;
  background: #e2e8f0;
}

.user-dropdown-demo {
  cursor: pointer;
}

.user-info-header-demo {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 8px;
  border-radius: 6px;
  transition: background-color 0.1s !important;
  cursor: pointer;
}

.user-info-header-demo:hover {
  background: #f8fafc;
}

.user-avatar-demo {
  background: #eef2ff;
  color: #6366f1;
  font-weight: 600;
  font-size: 14px;
}

.user-avatar-demo .avatar-letter {
  font-weight: 700;
}

.username-demo {
  font-size: 14px;
  color: #334155;
  font-weight: 500;
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 1.5;
}

.dropdown-icon-demo {
  color: #94a3b8;
  font-size: 12px;
}

.active-lang {
  color: #6366f1;
  font-weight: 600;
}

.user-info-item {
  cursor: default !important;
  background: #f8fafc !important;
}

.user-detail {
  padding: 4px 0;
}

.user-name {
  font-size: 14px;
  font-weight: 600;
  color: #0f172a;
  margin-bottom: 2px;
}

.user-email {
  font-size: 12px;
  color: #64748b;
  white-space: nowrap;
}

.user-dropdown-demo :deep(.el-dropdown-menu__item) {
  padding: 10px 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: background-color 0.1s, color 0.1s !important;
  font-size: 14px;
}

.user-dropdown-demo :deep(.el-dropdown-menu__item .el-icon) {
  font-size: 16px;
  color: #64748b;
}

.user-dropdown-demo :deep(.el-dropdown-menu__item:hover) {
  background: #f1f5f9;
  color: #334155;
}

/* ==================== */
/* Demo风格主内容区 */
/* ==================== */
.main-content-demo {
  background: #f8fafc;
  padding: 24px;
  overflow-y: auto;
  flex: 1;
  height: 0;
  will-change: contents;
  transform: translateZ(0);
  contain: layout style;
  position: relative;
}

.main-content-demo::-webkit-scrollbar {
  width: 8px;
}

.main-content-demo::-webkit-scrollbar-track {
  background: transparent;
}

.main-content-demo::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}

.main-content-demo::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

/* 加载遮罩 */
.content-loading-mask {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(248, 250, 252, 0.95);
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: all;
  cursor: wait;
}

.loading-spinner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.spinner-icon {
  width: 40px;
  height: 40px;
  animation: spinner-rotate 1.4s linear infinite !important;
}

.spinner-path {
  stroke: #6366f1;
  stroke-linecap: round;
  animation: spinner-dash 1.4s ease-in-out infinite !important;
}

@keyframes spinner-rotate {
  100% { transform: rotate(360deg); }
}

@keyframes spinner-dash {
  0% {
    stroke-dasharray: 1, 126;
    stroke-dashoffset: 0;
  }
  50% {
    stroke-dasharray: 90, 126;
    stroke-dashoffset: -35;
  }
  100% {
    stroke-dasharray: 90, 126;
    stroke-dashoffset: -124;
  }
}

.loading-text {
  font-size: 14px;
  color: #64748b;
  font-weight: 500;
}

/* 过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s !important;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 响应式 */
@media (max-width: 1024px) {
  .sidebar-demo {
    width: 64px !important;
  }
  
  .username-demo {
    display: none;
  }
  
  .dropdown-icon-demo {
    display: none;
  }
}

@media (max-width: 768px) {
  .header-demo {
    padding: 0 16px;
    height: 56px !important;
  }
  
  .main-content-demo {
    padding: 16px;
  }
  
  .header-divider {
    display: none;
  }
  
  .language-button-demo {
    display: none;
  }
}

</style>
