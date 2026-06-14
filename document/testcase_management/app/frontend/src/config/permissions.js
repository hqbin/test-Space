// 独立功能权限（不属于任何页面）
export const FEATURE_PERMISSIONS = [
  { key: 'notificationBell', nameKey: 'feature.notificationBell', group: 'feature', description: '通知入口（右上角铃铛）' },
  { key: 'versionInfo', nameKey: 'feature.versionInfo', group: 'feature', description: '版本信息入口（用户下拉菜单）' }
]

// 所有可用的权限列表（页面级别）
export const ALL_PERMISSIONS = [
  { key: 'dashboard', nameKey: 'menu.dashboard', group: 'test', description: '工作台' },
  { key: 'testcases', nameKey: 'menu.testcases', group: 'test', description: '测试用例' },
  { key: 'aivoiceRecommendations', nameKey: 'menu.caseRecommend', group: 'test', description: '用例推荐' },
  { key: 'reviewPlans', nameKey: 'menu.reviewPlans', group: 'test', description: '用例评审' },
  { key: 'testplans', nameKey: 'menu.testplans', group: 'test', description: '测试计划管理' },
  { key: 'reports', nameKey: 'menu.reports', group: 'test', description: '测试报告' },
  { key: 'users', nameKey: 'menu.users', group: 'admin', description: '用户管理' },
  { key: 'projects', nameKey: 'menu.projects', group: 'admin', description: '项目管理' },
  { key: 'permissionManagement', nameKey: 'menu.permissionManagement', group: 'admin', description: '权限管理' },
  { key: 'organization', nameKey: 'menu.organization', group: 'admin', description: '组织管理' },
  { key: 'notificationManagement', nameKey: 'menu.notificationManagement', group: 'admin', description: '通知管理' },
  { key: 'templateManagement', nameKey: 'menu.templateManagement', group: 'admin', description: '模板管理' },
  { key: 'systemLog', nameKey: 'menu.systemLog', group: 'admin', description: '系统日志' },
  { key: 'database', nameKey: 'menu.database', group: 'admin', description: '数据库管理' },
  { key: 'analytics', nameKey: 'menu.analytics', group: 'projects', description: '数据统计分析' },
  { key: 'behaviorTracker', nameKey: 'menu.behaviorTracker', group: 'admin', description: '数据埋点（仅super可见）' },
  { key: 'versionRelease', nameKey: 'menu.versionRelease', group: 'admin', description: '版本发布管理（仅super可见）' },
  { key: 'adbTool', nameKey: 'menu.adbTool', group: 'standalone', description: 'ADB调试工具' },
  { key: 'amlPatch', nameKey: 'menu.amlPatch', group: 'standalone', description: 'AML Patch管理' },
  // 应用管理
  { key: 'aivoice', nameKey: 'menu.aivoice', group: 'aivoice', description: '应用管理(主开关)' },
  { key: 'aivoiceReleaseNotes', nameKey: 'menu.aivoiceReleaseNotes', group: 'aivoice', parent: 'aivoice', description: '应用管理-发版说明' },
  { key: 'aivoiceAliasTest', nameKey: 'menu.aivoiceAliasTest', group: 'aivoice', parent: 'aivoice', description: '应用管理-别名测试' },
  { key: 'aivoiceSettings', nameKey: 'menu.aivoiceSettings', group: 'admin', description: 'AI API设置' }
]

// 按钮级别的权限配置
export const BUTTON_PERMISSIONS = {
  // 测试用例页面
  testcases: {
    create: { key: 'testcases.create', nameKey: 'testcase.create', description: '新建用例' },
    copy: { key: 'testcases.copy', description: '复制用例' },
    edit: { key: 'testcases.edit', nameKey: 'common.edit', description: '编辑用例' },
    delete: { key: 'testcases.delete', nameKey: 'common.delete', description: '删除用例' },
    import: { key: 'testcases.import', nameKey: 'testcase.importExcel', description: '导入Excel' },
    export: { key: 'testcases.export', nameKey: 'testcase.exportExcel', description: '导出Excel' },
    batchEdit: { key: 'testcases.batchEdit', description: '批量编辑' },
    batchExport: { key: 'testcases.batchExport', description: '批量导出' },
    batchDelete: { key: 'testcases.batchDelete', description: '批量删除' },
    createPlan: { key: 'testcases.createPlan', description: '创建测试计划' },
    importAutoCreate: { key: 'testcases.importAutoCreate', description: '导入时自动创建用例库/模块' },
    deleteReviewPlan: { key: 'testcases.deleteReviewPlan', description: '删除评审计划' }
  },
  // 测试计划页面
  testplans: {
    create: { key: 'testplans.create', nameKey: 'testplan.create', description: '新建计划' },
    edit: { key: 'testplans.edit', nameKey: 'common.edit', description: '编辑计划' },
    delete: { key: 'testplans.delete', nameKey: 'common.delete', description: '删除计划' },
    deleteAll: { key: 'testplans.deleteAll', description: '删除所有状态计划（管理员）' },
    exportExcel: { key: 'testplans.exportExcel', description: '导出Excel报告' },
    exportPdf: { key: 'testplans.exportPdf', description: '导出PDF报告' },
    suiteTab: { key: 'testplans.suiteTab', description: '套件分页（查看套件Tab）' },
    suiteCreate: { key: 'testplans.suiteCreate', description: '新建套件' },
    suiteEdit: { key: 'testplans.suiteEdit', description: '编辑套件' },
    suiteDelete: { key: 'testplans.suiteDelete', description: '删除套件' },
    suiteExport: { key: 'testplans.suiteExport', description: '导出套件' },
    taskOverviewTab: { key: 'testplans.taskOverviewTab', description: '任务总览分页（查看任务总览Tab）' },
    taskOverviewCreate: { key: 'testplans.taskOverviewCreate', description: '新建任务总览' },
    taskOverviewEdit: { key: 'testplans.taskOverviewEdit', description: '编辑任务总览（仅创建人）' },
    taskOverviewDelete: { key: 'testplans.taskOverviewDelete', description: '删除任务总览（仅创建人）' }
  },
  // 测试报告页面
  reports: {
    generate: { key: 'reports.generate', nameKey: 'report.generate', description: '生成报告' },
    exportPdf: { key: 'reports.exportPdf', description: '导出PDF报告' },
    exportExcel: { key: 'reports.exportExcel', description: '导出Excel报告' },
    delete: { key: 'reports.delete', nameKey: 'common.delete', description: '删除报告' }
  },
  // 用户管理页面
  users: {
    create: { key: 'users.create', nameKey: 'user.createUser', description: '新建用户' },
    edit: { key: 'users.edit', nameKey: 'common.edit', description: '编辑用户' },
    delete: { key: 'users.delete', nameKey: 'common.delete', description: '删除用户' }
  },
  // 项目管理页面
  projects: {
    create: { key: 'projects.create', nameKey: 'project.createProject', description: '新建项目' },
    edit: { key: 'projects.edit', nameKey: 'common.edit', description: '编辑项目' },
    delete: { key: 'projects.delete', nameKey: 'common.delete', description: '删除项目' },
    editTag: { key: 'projects.editTag', nameKey: 'project.editTag', description: '编辑用例库Tag' },
    addModule: { key: 'projects.addModule', description: '新增模块' },
    editModule: { key: 'projects.editModule', description: '编辑模块' },
    deleteModule: { key: 'projects.deleteModule', description: '删除模块' },
    sortModule: { key: 'projects.sortModule', description: '模块排序' },
    editModuleTag: { key: 'projects.editModuleTag', description: '编辑模块Tag' },
    manageRequirementLink: { key: 'projects.manageRequirementLink', description: '管理需求链接' },
    editNamingRule: { key: 'projects.editNamingRule', description: '编辑命名规则' }
  },
  // 权限管理页面
  permissionManagement: {
    createRole: { key: 'permissionManagement.createRole', description: '新建角色' },
    editRole: { key: 'permissionManagement.editRole', description: '编辑角色' },
    deleteRole: { key: 'permissionManagement.deleteRole', description: '删除角色' }
  },
  // 组织管理页面
  organization: {
    create: { key: 'organization.create', description: '创建组织' },
    edit: { key: 'organization.edit', description: '编辑组织' },
    manageTeams: { key: 'organization.manageTeams', description: '项目组管理' },
    manageMembers: { key: 'organization.manageMembers', description: '成员管理' },
    delete: { key: 'organization.delete', description: '删除组织' }
  },
  // 工作台页面
  dashboard: {
    projectCards: { key: 'dashboard.projectCards', description: '用例库信息卡片' },
    prList: { key: 'dashboard.prList', description: '用例关联PR列表' },
    reviewPlans: { key: 'dashboard.reviewPlans', description: '评审计划卡片' },
    testPlans: { key: 'dashboard.testPlans', description: '测试计划卡片' },
    userTasks: { key: 'dashboard.userTasks', description: '用户任务统计' }
  },
  // 通知管理页面
  notificationManagement: {
    createRule: { key: 'notificationManagement.createRule', description: '新建通知规则' },
    editRule: { key: 'notificationManagement.editRule', description: '编辑通知规则' },
    deleteRule: { key: 'notificationManagement.deleteRule', description: '删除通知规则' },
    createTemplate: { key: 'notificationManagement.createTemplate', description: '新建通知模板' },
    editTemplate: { key: 'notificationManagement.editTemplate', description: '编辑通知模板' },
    deleteTemplate: { key: 'notificationManagement.deleteTemplate', description: '删除通知模板' },
    createDingtalkBot: { key: 'notificationManagement.createDingtalkBot', description: '新建钉钉机器人' },
    editDingtalkBot: { key: 'notificationManagement.editDingtalkBot', description: '编辑钉钉机器人' },
    deleteDingtalkBot: { key: 'notificationManagement.deleteDingtalkBot', description: '删除钉钉机器人' }
  },
  // AML Patch页面
  amlPatch: {
    create: { key: 'amlPatch.create', nameKey: 'amlPatch.create', description: '新建AML Patch' },
    edit: { key: 'amlPatch.edit', nameKey: 'common.edit', description: '编辑AML Patch' },
    delete: { key: 'amlPatch.delete', nameKey: 'common.delete', description: '删除AML Patch' },
    sync: { key: 'amlPatch.sync', nameKey: 'amlPatch.sync', description: '同步AML Patch到Zmind' }
  },
  // 用例推荐页面
  aivoiceRecommendations: {
    export: { key: 'aivoiceRecommendations.export', description: '导出推荐用例' },
    taskQueue: { key: 'aivoiceRecommendations.taskQueue', description: '任务队列' }
  }
}

// 获取所有按钮权限的扁平列表
export function getAllButtonPermissions() {
  const permissions = []
  for (const [page, buttons] of Object.entries(BUTTON_PERMISSIONS)) {
    for (const [action, config] of Object.entries(buttons)) {
      permissions.push({
        ...config,
        page,
        action,
        group: ALL_PERMISSIONS.find(p => p.key === page)?.group || 'test'
      })
    }
  }
  return permissions
}

// 获取所有权限（页面 + 按钮）
export function getAllPermissionsWithButtons() {
  return [...ALL_PERMISSIONS, ...getAllButtonPermissions()]
}

// 菜单配置
export const MENU_CONFIG = {
  dashboard: { path: '/dashboard', nameKey: 'menu.dashboard', icon: 'DataAnalysis' },
  testcases: { path: '/testcases', nameKey: 'menu.testcases', icon: 'Document' },
  aivoiceRecommendations: { path: '/aivoice/recommendations', nameKey: 'menu.caseRecommend', icon: 'Collection' },
  reviewPlans: { path: '/review-plans', nameKey: 'menu.reviewPlans', icon: 'DocumentChecked' },
  testplans: { path: '/testplans', nameKey: 'menu.testplans', icon: 'Calendar' },
  reports: { path: '/reports', nameKey: 'menu.reports', icon: 'Tickets' },
  projects: { path: '/projects', nameKey: 'menu.projects', icon: 'Folder' },
  users: { path: '/users', nameKey: 'menu.users', icon: 'User', group: 'admin' },
  permissionManagement: { path: '/permission-management', nameKey: 'menu.permissionManagement', icon: 'Lock', group: 'admin' },
  organization: { path: '/organization', nameKey: 'menu.organization', icon: 'OfficeBuilding', group: 'admin' },
  notificationManagement: { path: '/notification-management', nameKey: 'menu.notificationManagement', icon: 'Bell', group: 'admin' },
  templateManagement: { path: '/template-management', nameKey: 'menu.templateManagement', icon: 'Files', group: 'admin' },
  systemLog: { path: '/system-log', nameKey: 'menu.systemLog', icon: 'Document', group: 'admin' },
  database: { path: '/database', nameKey: 'menu.database', icon: 'Coin', group: 'admin' },
  analytics: { path: '/analytics', nameKey: 'menu.analytics', icon: 'TrendCharts', group: 'projects' },
  behaviorTracker: { path: '/behavior-tracker', nameKey: 'menu.behaviorTracker', icon: 'Monitor', group: 'admin', superOnly: true },
  versionRelease: { path: '/admin/version-release', nameKey: 'menu.versionRelease', icon: 'Upload', group: 'admin', superOnly: true },
  adbTool: { path: '/adb-tool/dashboard', nameKey: 'menu.adbTool', icon: 'Iphone', group: 'standalone' },
  amlPatch: { path: '/aml-patch', nameKey: 'menu.amlPatch', icon: 'DocumentCopy', group: 'standalone' },
  // 应用管理
  aivoiceReleaseNotes: { path: '/aivoice/release-notes', nameKey: 'menu.aivoiceReleaseNotes', icon: 'Edit', group: 'aivoice' },
  aivoiceAliasTest: { path: '/aivoice/alias-test', nameKey: 'menu.aivoiceAliasTest', icon: 'Connection', group: 'aivoice' },
  aivoiceSettings: { path: '/aivoice/settings', nameKey: 'menu.aivoiceSettings', icon: 'Setting', group: 'admin' }
}

// 检查用户是否有菜单权限
export function hasMenuPermission(userPermissions, menuKey) {
  return userPermissions.includes(menuKey)
}

// 过滤掉superOnly的菜单（只有super账号可见）
function filterSuperOnlyMenus(configs, username) {
  if (username === 'super') {
    return configs
  }
  return configs.filter(c => !c.superOnly)
}

// 获取用户可访问的菜单列表
export function getUserMenus(userPermissions, username = null) {
  const menus = []
  const adminMenus = []
  const standaloneMenus = []
  const aivoiceMenus = []

  for (const [key, config] of Object.entries(MENU_CONFIG)) {
    // aivoice 子入口：每个子入口独立判断自己的权限 key
    // 不因为有主开关就自动显示所有子入口
    if (!hasMenuPermission(userPermissions, key)) continue

    if (config.group === 'admin') {
      adminMenus.push({ key, ...config })
    } else if (config.group === 'standalone') {
      standaloneMenus.push({ key, ...config })
    } else if (config.group === 'aivoice') {
      aivoiceMenus.push({ key, ...config })
    } else {
      menus.push({ key, ...config })
    }
  }

  // 过滤superOnly菜单
  return {
    menus: filterSuperOnlyMenus(menus, username),
    adminMenus: filterSuperOnlyMenus(adminMenus, username),
    standaloneMenus: filterSuperOnlyMenus(standaloneMenus, username),
    aivoiceMenus: filterSuperOnlyMenus(aivoiceMenus, username)
  }
}
