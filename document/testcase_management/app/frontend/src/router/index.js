import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/auth/Login.vue'
import Layout from '../views/Layout.vue'
import { getUserRoles } from '../api/role'
import { ALL_PERMISSIONS, FEATURE_PERMISSIONS } from '../config/permissions'
import { useBehaviorTracker } from '../composables/useBehaviorTracker'

const EXCLUDED_TRACK_PATHS = [
  '/testplans/:id/execution',
  '/testplans/:planId/testcases/:testcaseId'
]

function shouldTrackPage(path) {
  return !EXCLUDED_TRACK_PATHS.some(excluded => {
    const regex = new RegExp('^' + excluded.replace(/:[^/]+/g, '[^/]+') + '$')
    return regex.test(path)
  })
}

const isMobileDevice = () => {
  if (typeof window === 'undefined') return false
  const ua = navigator.userAgent || ''
  return /Android|iPhone|iPad|iPod|Mobile|HarmonyOS/i.test(ua) || window.innerWidth <= 900
}

const getMobilePath = (path) => {
  if (path === '/login') return '/m/login'
  if (path.startsWith('/reports/review/')) return path.replace('/reports/review/', '/m/reports/review/')
  if (path === '/testplans') return '/m/testplans'
  if (path === '/reports') return '/m/reports'
  if (path === '/users') return '/m/users'
  if (path === '/settings') return '/m/settings'
  return '/m/reports'
}

const getDesktopPath = (path) => {
  if (path === '/m/login') return '/login'
  if (path.startsWith('/m/reports/review/')) return path.replace('/m/reports/review/', '/reports/review/')
  if (path === '/m/testplans') return '/testplans'
  if (path === '/m/reports') return '/reports'
  if (path === '/m/users' || path.startsWith('/m/users/')) return '/users'
  if (path === '/m/settings') return '/dashboard'
  return '/dashboard'
}

const SUPER_ADMINS = ['admin', 'super']
const ALL_PERMISSION_KEYS = [
  ...ALL_PERMISSIONS.map(p => p.key),
  ...FEATURE_PERMISSIONS.map(p => p.key)
]

const getCurrentUser = () => {
  try {
    return JSON.parse(localStorage.getItem('user') || '{}')
  } catch {
    return {}
  }
}

const getRequiredMenuByPath = (path) => {
  if (path.startsWith('/m/reports')) return 'reports'
  if (path.startsWith('/m/testplans')) return 'testplans'
  if (path.startsWith('/m/users')) return 'users'
  return null
}

const getCachedPermissions = (userId) => {
  try {
    const cache = JSON.parse(sessionStorage.getItem('mobile_permissions_cache') || '{}')
    if (cache.userId === userId && Array.isArray(cache.permissions)) {
      return cache.permissions
    }
  } catch {
    // ignore
  }
  return null
}

const setCachedPermissions = (userId, permissions) => {
  sessionStorage.setItem('mobile_permissions_cache', JSON.stringify({ userId, permissions }))
}

const loadPermissions = async () => {
  const user = getCurrentUser()
  if (SUPER_ADMINS.includes(user.username)) return ALL_PERMISSION_KEYS
  if (!user.id) return []
  const cached = getCachedPermissions(user.id)
  if (cached) return cached
  const res = await getUserRoles(user.id)
  const set = new Set()
  ;(res.data || []).forEach(role => {
    ;(role.permissions || []).forEach(perm => set.add(perm))
  })
  const permissions = Array.from(set)
  setCachedPermissions(user.id, permissions)
  return permissions
}

const getDefaultMobileHome = (permissions) => {
  if (permissions.includes('reports')) return '/m/reports'
  if (permissions.includes('testplans')) return '/m/testplans'
  if (permissions.includes('users')) return '/m/users'
  return '/m/reports'
}

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/adb-tool-public',
    name: 'AdbToolPublic',
    component: () => import('../views/admin/AdbTool.vue'),
    meta: { title: 'ADB Tool', public: true }
  },
  {
    path: '/m/login',
    name: 'MobileLogin',
    component: () => import('../views/mobile/MobileLogin.vue'),
    meta: { title: 'Mobile Login', mobileOnly: true }
  },
  {
    path: '/m',
    component: () => import('../views/mobile/MobileLayout.vue'),
    redirect: '/m/reports',
    meta: { mobileOnly: true },
    children: [
      {
        path: 'testplans',
        name: 'MobileTestPlans',
        component: () => import('../views/mobile/MobileTestPlans.vue'),
        meta: { title: 'Mobile Test Plans', mobileOnly: true }
      },
      {
        path: 'reports',
        name: 'MobileReports',
        component: () => import('../views/mobile/MobileReports.vue'),
        meta: { title: 'Mobile Reports', mobileOnly: true }
      },
      {
        path: 'reports/review/:id',
        name: 'MobileReportReview',
        component: () => import('../views/mobile/MobileReportReview.vue'),
        meta: { title: 'Mobile Report Review', mobileOnly: true, hideMobileNav: true }
      },
      {
        path: 'users',
        name: 'MobileUsers',
        component: () => import('../views/mobile/MobileUsers.vue'),
        meta: { title: 'Mobile Users', mobileOnly: true }
      },
      {
        path: 'users/edit',
        name: 'MobileUserCreate',
        component: () => import('../views/mobile/MobileUserEdit.vue'),
        meta: { title: 'Mobile User Edit', mobileOnly: true, hideMobileNav: true }
      },
      {
        path: 'users/edit/:id',
        name: 'MobileUserEdit',
        component: () => import('../views/mobile/MobileUserEdit.vue'),
        meta: { title: 'Mobile User Edit', mobileOnly: true, hideMobileNav: true }
      },
      {
        path: 'users/approvals',
        name: 'MobileUserApprovals',
        component: () => import('../views/mobile/MobileUserApprovals.vue'),
        meta: { title: 'Mobile User Approvals', mobileOnly: true, hideMobileNav: true }
      },
      {
        path: 'settings',
        name: 'MobileSettings',
        component: () => import('../views/mobile/MobileSettings.vue'),
        meta: { title: 'Mobile Settings', mobileOnly: true }
      }
    ]
  },
  {
    path: '/',
    component: Layout,
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('../views/dashboard/Dashboard.vue'),
        meta: { title: 'menu.dashboard' }
      },
      {
        path: 'testcases',
        name: 'TestCases',
        component: () => import('../views/testcase/TestCaseList.vue'),
        meta: { title: 'menu.testcases' }
      },
      {
        path: 'testcases/:testcaseId/detail',
        name: 'TestCaseDetail',
        component: () => import('../views/testcase/TestCaseDetailPage.vue'),
        meta: { title: '用例详情' }
      },
      {
        path: 'testplans',
        name: 'TestPlans',
        component: () => import('../views/testplan/TestPlanList.vue'),
        meta: { title: 'menu.testplans' }
      },
      {
        path: 'testplans/:id',
        name: 'TestPlanDetail',
        component: () => import('../views/testplan/TestPlanDetail.vue'),
        meta: { title: 'menu.testPlanDetail', collapseSidebar: true }
      },
      {
        path: 'testplans/:id/execution',
        name: 'TestPlanExecution',
        component: () => import('../views/testplan/TestPlanExecution.vue'),
        meta: { title: 'menu.testPlanExecution', collapseSidebar: true }
      },
      {
        path: 'testplans/:planId/testcases/:testcaseId',
        name: 'TestCaseExecutionDetail',
        component: () => import('../views/testplan/TestCaseExecutionDetail.vue'),
        meta: { title: 'menu.testCaseExecutionDetail', collapseSidebar: true }
      },
      {
        path: 'testplans/:planId/preview-report',
        name: 'TestPlanReportPreview',
        component: () => import('../views/report/ReportReview.vue'),
        meta: { title: 'menu.previewReport' }
      },
      {
        path: 'testplans/:planId/submit-preview',
        name: 'TestPlanSubmitPreview',
        component: () => import('../views/report/ReportReview.vue'),
        meta: { title: 'menu.previewReport' }
      },
      {
        path: 'task-overviews',
        name: 'TaskOverviews',
        component: () => import('../views/testplan/TaskOverviewList.vue'),
        meta: { title: 'menu.taskOverview' }
      },
      {
        path: 'task-overviews/:id',
        name: 'TaskOverviewDetail',
        component: () => import('../views/testplan/TaskOverviewDetail.vue'),
        meta: { title: 'menu.taskOverviewDetail', collapseSidebar: true }
      },
      {
        path: 'reports',
        name: 'Reports',
        component: () => import('../views/report/ReportList.vue'),
        meta: { title: 'menu.reports' }
      },
      {
        path: 'reports/review/:id',
        name: 'ReportReview',
        component: () => import('../views/report/ReportReview.vue'),
        meta: { title: 'menu.reportReview' }
      },
      {
        path: 'zmind',
        name: 'Zmind',
        component: () => import('../views/zmind/ZmindIntegration.vue'),
        meta: { title: 'menu.zmind', keepAlive: true }
      },
      {
        path: 'users',
        name: 'Users',
        component: () => import('../views/admin/UserManagement.vue'),
        meta: { title: 'menu.users' }
      },
      {
        path: 'projects',
        name: 'Projects',
        component: () => import('../views/admin/ProjectManagement.vue'),
        meta: { title: 'menu.projects' }
      },
      {
        path: 'projects/:projectId/modules',
        name: 'ProjectModuleManagement',
        component: () => import('../views/testcase/ProjectModuleManagement.vue'),
        meta: { title: '用例库模块管理', collapseSidebar: true }
      },
      {
        path: 'projects/:projectId/modules/:moduleId',
        name: 'ModuleDetail',
        component: () => import('../views/testcase/ModuleDetail.vue'),
        meta: { title: '模块详情', collapseSidebar: true }
      },
      {
        path: 'notifications',
        name: 'Notifications',
        component: () => import('../views/notification/NotificationList.vue'),
        meta: { title: 'menu.notifications' }
      },
      {
        path: 'analytics',
        name: 'DataAnalytics',
        component: () => import('../views/analytics/DataAnalytics.vue'),
        meta: { title: 'menu.analytics' }
      },
      {
        path: 'behavior-tracker',
        name: 'BehaviorTracker',
        component: () => import('../views/analytics/BehaviorTracker.vue'),
        meta: { title: 'menu.behaviorTracker', superOnly: true }
      },
      {
        path: 'admin/version-release',
        name: 'VersionRelease',
        component: () => import('../views/admin/VersionRelease.vue'),
        meta: { title: 'menu.versionRelease', superOnly: true }
      },
      {
        path: 'system-log',
        name: 'SystemLog',
        component: () => import('../views/admin/SystemLog.vue'),
        meta: { title: 'menu.systemLog' }
      },
      {
        path: 'database',
        name: 'DatabaseManagement',
        component: () => import('../views/admin/DatabaseManagement.vue'),
        meta: { title: 'menu.database' }
      },
      {
        path: 'permission-management',
        name: 'PermissionManagement',
        component: () => import('../views/admin/PermissionManagement.vue'),
        meta: { title: 'menu.permissionManagement' }
      },
      {
        path: 'organization',
        name: 'Organization',
        component: () => import('../views/admin/OrganizationManagement.vue'),
        meta: { title: 'menu.organization' }
      },
      {
        path: 'notification-management',
        name: 'NotificationManagement',
        component: () => import('../views/admin/NotificationManagement.vue'),
        meta: { title: 'menu.notificationManagement' }
      },
      {
        path: 'template-management',
        name: 'TemplateManagement',
        component: () => import('../views/admin/TemplateManagement.vue'),
        meta: { title: 'menu.templateManagement' }
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('../views/user/UserProfile.vue'),
        meta: { title: 'menu.profile' }
      },
      {
        path: 'review-plans',
        name: 'ReviewPlanList',
        component: () => import('../views/review/ReviewPlanList.vue'),
        meta: { title: 'menu.reviewPlans' }
      },
      {
        path: 'review-plans/:id',
        name: 'ReviewPlanDetail',
        component: () => import('../views/review/ReviewPlanDetail.vue'),
        meta: { title: 'menu.reviewPlanDetail' }
      },
      {
        path: 'review-plans/:id/execution',
        name: 'ReviewPlanExecution',
        component: () => import('../views/review/ReviewPlanExecution.vue'),
        meta: { title: 'menu.reviewPlanExecution', collapseSidebar: true }
      },
      {
        path: 'review-plans/:planId/testcases/:testcaseId',
        name: 'TestCaseReviewDetail',
        component: () => import('../views/review/TestCaseReviewDetail.vue'),
        meta: { title: 'menu.testCaseReviewDetail', collapseSidebar: true }
      },
      {
        path: 'icons',
        name: 'Icons',
        component: () => import('../views/IconList.vue'),
        meta: { title: 'Icons' }
      },
      {
        path: 'aml-patch',
        name: 'AmlPatch',
        component: () => import('../views/admin/AmlPatch.vue'),
        meta: { title: 'menu.amlPatch' }
      },
      // 应用管理
      {
        path: 'aivoice/release-notes',
        name: 'AivoiceReleaseNotes',
        component: () => import('../views/aivoice/ReleaseNotes.vue'),
        meta: { title: '发版说明' }
      },
      {
        path: 'aivoice/recommendations',
        name: 'AivoiceRecommendations',
        component: () => import('../views/aivoice/Recommendations.vue'),
        meta: { title: '用例推荐' }
      },
      {
        path: 'aivoice/alias-test',
        name: 'AivoiceAliasTest',
        component: () => import('../views/aivoice/AliasTest.vue'),
        meta: { title: '别名测试' }
      },
      {
        path: 'aivoice/settings',
        name: 'AivoiceSettings',
        component: () => import('../views/aivoice/AivoiceSettings.vue'),
        meta: { title: 'AI API设置' }
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    redirect: '/dashboard'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫 - 优化性能
router.beforeEach(async (to, from, next) => {
  const token = localStorage.getItem('token')
  const mobile = isMobileDevice()
  const isMobileRoute = to.path.startsWith('/m/')

  if (mobile && !isMobileRoute && !to.meta.public) {
    next(getMobilePath(to.path))
    return
  }
  if (!mobile && isMobileRoute) {
    next(getDesktopPath(to.path))
    return
  }

  const isPublicRoute = to.meta.public || to.path === '/login'
  const isPublicMobileRoute = to.path === '/m/login'
  if (!isPublicRoute && !isPublicMobileRoute && !token) {
    // 未登录：保存目标路径，登录后跳回
    const loginPath = mobile ? '/m/login' : '/login'
    next({ path: loginPath, query: { redirect: to.fullPath } })
  } else if ((to.path === '/login' || to.path === '/m/login') && token) {
    if (mobile) {
      const permissions = await loadPermissions()
      next(getDefaultMobileHome(permissions))
      return
    }
    next('/')
  } else {
    // 移动端页面按菜单权限访问（超级管理员不受控制）
    if (to.path.startsWith('/m/')) {
      const user = getCurrentUser()
      if (!SUPER_ADMINS.includes(user.username)) {
        const requiredMenu = getRequiredMenuByPath(to.path)
        if (requiredMenu) {
          const permissions = await loadPermissions()
          if (!permissions.includes(requiredMenu)) {
            next(getDefaultMobileHome(permissions))
            return
          }
        }
      }
    }
    next()
  }
})

// 页面名称映射
const PAGE_NAME_MAP = {
  '/dashboard': '工作台',
  '/testcases': '测试用例',
  '/testplans': '测试计划',
  '/reports': '测试报告',
  '/zmind': 'Zmind集成',
  '/users': '用户管理',
  '/projects': '用例库管理',
  '/notifications': '通知中心',
  '/analytics': '数据统计',
  '/behavior-tracker': '数据埋点',
  '/system-log': '系统日志',
  '/database': '数据库管理',
  '/permission-management': '权限管理',
  '/organization': '组织管理',
  '/notification-management': '通知管理',
  '/template-management': '模板管理',
  '/profile': '个人中心',
  '/review-plans': '用例评审',
  '/icons': '图标列表',
  '/aml-patch': 'AML Patch管理',
  '/login': '登录'
}

// 路由后置守卫 - 自动追踪页面访问
router.afterEach((to) => {
  const token = localStorage.getItem('token')
  if (!token || !shouldTrackPage(to.path)) {
    return
  }
  const { trackPageView } = useBehaviorTracker()

  // 根据路由生成更详细的页面名称
  let pageName = ''
  if (to.path.startsWith('/testplans/') && to.params.id) {
    const planName = sessionStorage.getItem(`plan_name_${to.params.id}`)
    if (planName) {
      pageName = `测试计划-${planName}`
    } else {
      pageName = '测试计划详情'
    }
  } else if (to.path.startsWith('/projects/') && to.params.projectId && to.path.includes('/modules')) {
    const projectName = sessionStorage.getItem(`project_name_${to.params.projectId}`)
    if (projectName) {
      pageName = `${projectName}-模块管理`
    } else {
      pageName = '模块管理'
    }
  } else if (to.path.match(/^\/projects\/\d+\/modules\/\d+$/)) {
    pageName = '模块详情'
  } else if (to.path.startsWith('/reports/review/') && to.params.id) {
    const reportName = sessionStorage.getItem(`report_name_${to.params.id}`)
    if (reportName) {
      pageName = `报告评审-${reportName}`
    } else {
      pageName = '报告评审'
    }
  } else if (to.path.startsWith('/review-plans/') && to.params.id && !to.path.includes('/execution')) {
    pageName = '评审计划详情'
  } else if (to.path.startsWith('/review-plans/') && to.params.id && to.path.includes('/execution')) {
    pageName = '评审执行'
  } else if (to.path.startsWith('/testcases/') && to.params.testcaseId) {
    const caseName = sessionStorage.getItem(`testcase_name_${to.params.testcaseId}`)
    if (caseName) {
      pageName = `用例详情-${caseName}`
    } else {
      pageName = '用例详情'
    }
  } else {
    // 使用映射表获取中文名称
    pageName = PAGE_NAME_MAP[to.path] || to.path
  }

  trackPageView(to.path, pageName)
})

// 动态 import 失败时自动刷新（部署后旧 chunk 文件不存在）
router.onError((error) => {
  if (
    error.message.includes('Failed to fetch dynamically imported module') ||
    error.message.includes('Importing a module script failed')
  ) {
    const reloadKey = 'chunk_reload_' + window.location.pathname
    // 防止无限刷新：同一路径只刷新一次
    if (!sessionStorage.getItem(reloadKey)) {
      sessionStorage.setItem(reloadKey, '1')
      window.location.reload()
    }
  }
})

export default router
