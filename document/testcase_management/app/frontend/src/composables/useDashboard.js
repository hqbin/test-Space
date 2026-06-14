import { ref, reactive, computed, watch, onMounted, onUnmounted } from 'vue'
import { getDashboardStats } from '@/api/dashboard'

const CARD_TYPES = {
  TESTPLAN_STATS: 'testplan_stats',
  MY_PROGRESS: 'my_progress',
  TODO_LIST: 'todo_list',
  DEFECT_TRACKING: 'defect_tracking',
  EXECUTION_TREND: 'execution_trend',
  PROJECT_PROGRESS: 'project_progress',
  HIGH_RISK_DEFECTS: 'high_risk_defects',
  CASE_COVERAGE: 'case_coverage',
  TEAM_EFFICIENCY: 'team_efficiency',
  GLOBAL_STATUS: 'global_status',
  DEFECT_TREND: 'defect_trend',
  RESOURCE_LOAD: 'resource_load',
  SYSTEM_HEALTH: 'system_health',
  MY_TESTCASES: 'my_testcases',
  TEAM_WORKLOAD: 'team_workload',
  REVIEW_PENDING: 'review_pending',
  NOTIFICATION_CENTER: 'notification_center',
  QUICK_ACTIONS: 'quick_actions'
}

const ROLE_CARD_CONFIG = {
  tester: [
    { type: CARD_TYPES.TESTPLAN_STATS, required: true, order: 0 },
    { type: CARD_TYPES.MY_PROGRESS, required: true, order: 1 },
    { type: CARD_TYPES.TODO_LIST, required: true, order: 2 },
    { type: CARD_TYPES.DEFECT_TRACKING, required: false, order: 3 },
    { type: CARD_TYPES.EXECUTION_TREND, required: false, order: 4 },
    { type: CARD_TYPES.MY_TESTCASES, required: false, order: 5 },
    { type: CARD_TYPES.NOTIFICATION_CENTER, required: false, order: 6 },
    { type: CARD_TYPES.QUICK_ACTIONS, required: false, order: 7 }
  ],
  test_leader: [
    { type: CARD_TYPES.TESTPLAN_STATS, required: true, order: 0 },
    { type: CARD_TYPES.PROJECT_PROGRESS, required: true, order: 1 },
    { type: CARD_TYPES.HIGH_RISK_DEFECTS, required: true, order: 2 },
    { type: CARD_TYPES.CASE_COVERAGE, required: false, order: 3 },
    { type: CARD_TYPES.TEAM_EFFICIENCY, required: false, order: 4 },
    { type: CARD_TYPES.TEAM_WORKLOAD, required: false, order: 5 },
    { type: CARD_TYPES.REVIEW_PENDING, required: false, order: 6 },
    { type: CARD_TYPES.NOTIFICATION_CENTER, required: false, order: 7 }
  ],
  test_manager: [
    { type: CARD_TYPES.TESTPLAN_STATS, required: true, order: 0 },
    { type: CARD_TYPES.GLOBAL_STATUS, required: true, order: 1 },
    { type: CARD_TYPES.PROJECT_PROGRESS, required: true, order: 2 },
    { type: CARD_TYPES.HIGH_RISK_DEFECTS, required: true, order: 3 },
    { type: CARD_TYPES.CASE_COVERAGE, required: false, order: 4 },
    { type: CARD_TYPES.TEAM_EFFICIENCY, required: false, order: 5 },
    { type: CARD_TYPES.TEAM_WORKLOAD, required: false, order: 6 },
    { type: CARD_TYPES.DEFECT_TREND, required: false, order: 7 },
    { type: CARD_TYPES.RESOURCE_LOAD, required: false, order: 8 }
  ],
  rd: [
    { type: CARD_TYPES.TESTPLAN_STATS, required: true, order: 0 },
    { type: CARD_TYPES.DEFECT_TRACKING, required: true, order: 1 },
    { type: CARD_TYPES.MY_TESTCASES, required: false, order: 2 },
    { type: CARD_TYPES.NOTIFICATION_CENTER, required: false, order: 3 },
    { type: CARD_TYPES.QUICK_ACTIONS, required: false, order: 4 }
  ],
  pm: [
    { type: CARD_TYPES.TESTPLAN_STATS, required: true, order: 0 },
    { type: CARD_TYPES.PROJECT_PROGRESS, required: true, order: 1 },
    { type: CARD_TYPES.CASE_COVERAGE, required: true, order: 2 },
    { type: CARD_TYPES.DEFECT_TREND, required: false, order: 3 },
    { type: CARD_TYPES.NOTIFICATION_CENTER, required: false, order: 4 }
  ],
  admin: [
    { type: CARD_TYPES.TESTPLAN_STATS, required: true, order: 0 },
    { type: CARD_TYPES.GLOBAL_STATUS, required: true, order: 1 },
    { type: CARD_TYPES.DEFECT_TREND, required: true, order: 2 },
    { type: CARD_TYPES.RESOURCE_LOAD, required: true, order: 3 },
    { type: CARD_TYPES.SYSTEM_HEALTH, required: true, order: 4 },
    { type: CARD_TYPES.TEAM_WORKLOAD, required: false, order: 5 },
    { type: CARD_TYPES.NOTIFICATION_CENTER, required: false, order: 6 }
  ]
}

const CARD_META = {
  [CARD_TYPES.TESTPLAN_STATS]: {
    title: 'dashboard.testplanStats',
    icon: 'Calendar',
    color: '#409EFF',
    minWidth: 3,
    defaultHeight: 'auto'
  },
  [CARD_TYPES.MY_PROGRESS]: {
    title: 'dashboard.myTestProgress',
    icon: 'VideoPlay',
    color: '#67C23A',
    minWidth: 1,
    defaultHeight: 'auto'
  },
  [CARD_TYPES.TODO_LIST]: {
    title: 'dashboard.todayTodo',
    icon: 'List',
    color: '#E6A23C',
    minWidth: 1,
    defaultHeight: 'auto'
  },
  [CARD_TYPES.DEFECT_TRACKING]: {
    title: 'dashboard.defectTracking',
    icon: 'Warning',
    color: '#F56C6C',
    minWidth: 1,
    defaultHeight: 'auto'
  },
  [CARD_TYPES.EXECUTION_TREND]: {
    title: 'dashboard.executionTrend',
    icon: 'TrendCharts',
    color: '#909399',
    minWidth: 1,
    defaultHeight: 'auto'
  },
  [CARD_TYPES.PROJECT_PROGRESS]: {
    title: 'dashboard.projectProgress',
    icon: 'DataAnalysis',
    color: '#409EFF',
    minWidth: 1,
    defaultHeight: 'auto'
  },
  [CARD_TYPES.HIGH_RISK_DEFECTS]: {
    title: 'dashboard.highRiskDefects',
    icon: 'WarningFilled',
    color: '#F56C6C',
    minWidth: 1,
    defaultHeight: 'auto'
  },
  [CARD_TYPES.CASE_COVERAGE]: {
    title: 'dashboard.caseCoverage',
    icon: 'DocumentChecked',
    color: '#67C23A',
    minWidth: 1,
    defaultHeight: 'auto'
  },
  [CARD_TYPES.TEAM_EFFICIENCY]: {
    title: 'dashboard.teamEfficiency',
    icon: 'User',
    color: '#409EFF',
    minWidth: 1,
    defaultHeight: 'auto'
  },
  [CARD_TYPES.GLOBAL_STATUS]: {
    title: 'dashboard.globalStatus',
    icon: 'Folder',
    color: '#409EFF',
    minWidth: 1,
    defaultHeight: 'auto'
  },
  [CARD_TYPES.DEFECT_TREND]: {
    title: 'dashboard.defectTrend',
    icon: 'TrendCharts',
    color: '#F56C6C',
    minWidth: 1,
    defaultHeight: 'auto'
  },
  [CARD_TYPES.RESOURCE_LOAD]: {
    title: 'dashboard.resourceLoad',
    icon: 'Monitor',
    color: '#E6A23C',
    minWidth: 1,
    defaultHeight: 'auto'
  },
  [CARD_TYPES.SYSTEM_HEALTH]: {
    title: 'dashboard.systemHealth',
    icon: 'CircleCheck',
    color: '#67C23A',
    minWidth: 1,
    defaultHeight: 'auto'
  },
  [CARD_TYPES.MY_TESTCASES]: {
    title: 'dashboard.myTestcases',
    icon: 'Document',
    color: '#409EFF',
    minWidth: 1,
    defaultHeight: 'auto'
  },
  [CARD_TYPES.TEAM_WORKLOAD]: {
    title: 'dashboard.teamWorkload',
    icon: 'UserFilled',
    color: '#909399',
    minWidth: 2,
    defaultHeight: 'auto'
  },
  [CARD_TYPES.REVIEW_PENDING]: {
    title: 'dashboard.reviewPending',
    icon: 'Clock',
    color: '#E6A23C',
    minWidth: 1,
    defaultHeight: 'auto'
  },
  [CARD_TYPES.NOTIFICATION_CENTER]: {
    title: 'dashboard.notificationCenter',
    icon: 'Bell',
    color: '#409EFF',
    minWidth: 1,
    defaultHeight: 'auto'
  },
  [CARD_TYPES.QUICK_ACTIONS]: {
    title: 'dashboard.quickActions',
    icon: 'Operation',
    color: '#909399',
    minWidth: 1,
    defaultHeight: 'auto'
  }
}

const STORAGE_KEY = 'dashboard_layout_config'

export function useDashboard(userRole) {
  const loading = ref(false)
  const error = ref(null)
  const dateRange = ref([])
  const dashboardData = reactive({})
  const cardStates = reactive({})
  const cardOrder = ref([])
  const minimizedCards = ref(new Set())
  const maximizedCard = ref(null)

  const defaultCardOrder = computed(() => {
    const roleConfig = ROLE_CARD_CONFIG[userRole.value] || ROLE_CARD_CONFIG.tester
    return roleConfig.map(c => c.type)
  })

  const availableCards = computed(() => {
    const roleConfig = ROLE_CARD_CONFIG[userRole.value] || ROLE_CARD_CONFIG.tester
    return roleConfig.map(c => ({
      ...c,
      ...CARD_META[c.type]
    }))
  })

  const visibleCards = computed(() => {
    return cardOrder.value
      .filter(type => !minimizedCards.value.has(type))
      .map(type => ({
        type,
        ...CARD_META[type],
        isMaximized: maximizedCard.value === type
      }))
  })

  const loadLayoutConfig = () => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) {
        const config = JSON.parse(stored)
        const roleConfig = config[userRole.value]
        if (roleConfig) {
          cardOrder.value = roleConfig.order || defaultCardOrder.value
          minimizedCards.value = new Set(roleConfig.minimized || [])
          return
        }
      }
    } catch (e) {
      console.warn('Failed to load dashboard layout config:', e)
    }
    cardOrder.value = [...defaultCardOrder.value]
    minimizedCards.value = new Set()
  }

  const saveLayoutConfig = () => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      const config = stored ? JSON.parse(stored) : {}
      config[userRole.value] = {
        order: cardOrder.value,
        minimized: Array.from(minimizedCards.value)
      }
      localStorage.setItem(STORAGE_KEY, JSON.stringify(config))
    } catch (e) {
      console.warn('Failed to save dashboard layout config:', e)
    }
  }

  const updateCardOrder = (newOrder) => {
    cardOrder.value = newOrder
    saveLayoutConfig()
  }

  const toggleMinimize = (cardType) => {
    if (minimizedCards.value.has(cardType)) {
      minimizedCards.value.delete(cardType)
    } else {
      minimizedCards.value.add(cardType)
    }
    saveLayoutConfig()
  }

  const toggleMaximize = (cardType) => {
    if (maximizedCard.value === cardType) {
      maximizedCard.value = null
    } else {
      maximizedCard.value = cardType
    }
  }

  const resetLayout = () => {
    cardOrder.value = [...defaultCardOrder.value]
    minimizedCards.value = new Set()
    maximizedCard.value = null
    saveLayoutConfig()
  }

  const loadDashboardData = async (forceRefresh = false) => {
    if (loading.value && !forceRefresh) return

    loading.value = true
    error.value = null

    try {
      const params = {}
      if (dateRange.value && dateRange.value.length === 2) {
        params.start_date = dateRange.value[0]
        params.end_date = dateRange.value[1]
      }

      const res = await getDashboardStats(params)

      if (res.data) {
        Object.assign(dashboardData, res.data)
      }
    } catch (e) {
      error.value = e
      console.error('Failed to load dashboard data:', e)
    } finally {
      loading.value = false
    }
  }

  const setDateRange = (range) => {
    dateRange.value = range
    loadDashboardData(true)
  }

  const getCardData = (cardType) => {
    const dataMap = {
      [CARD_TYPES.TESTPLAN_STATS]: dashboardData.testplans,
      [CARD_TYPES.MY_PROGRESS]: dashboardData.my_progress,
      [CARD_TYPES.TODO_LIST]: dashboardData.todo,
      [CARD_TYPES.DEFECT_TRACKING]: dashboardData.defects,
      [CARD_TYPES.EXECUTION_TREND]: dashboardData.trend,
      [CARD_TYPES.PROJECT_PROGRESS]: dashboardData.project_progress,
      [CARD_TYPES.HIGH_RISK_DEFECTS]: dashboardData.high_risk_defects,
      [CARD_TYPES.CASE_COVERAGE]: dashboardData.coverage,
      [CARD_TYPES.TEAM_EFFICIENCY]: dashboardData.team_efficiency,
      [CARD_TYPES.GLOBAL_STATUS]: dashboardData.global_status,
      [CARD_TYPES.DEFECT_TREND]: dashboardData.defect_trend,
      [CARD_TYPES.RESOURCE_LOAD]: dashboardData.resource_load,
      [CARD_TYPES.SYSTEM_HEALTH]: dashboardData.system_health,
      [CARD_TYPES.MY_TESTCASES]: dashboardData.my_testcases,
      [CARD_TYPES.TEAM_WORKLOAD]: dashboardData.team_workload,
      [CARD_TYPES.REVIEW_PENDING]: dashboardData.review_pending,
      [CARD_TYPES.NOTIFICATION_CENTER]: dashboardData.notifications,
      [CARD_TYPES.QUICK_ACTIONS]: dashboardData.quick_actions
    }
    return dataMap[cardType] || {}
  }

  const initializeDashboard = () => {
    loadLayoutConfig()
    const end = new Date()
    const start = new Date()
    start.setDate(start.getDate() - 30)
    dateRange.value = [
      start.toISOString().split('T')[0],
      end.toISOString().split('T')[0]
    ]
    loadDashboardData()
  }

  watch(userRole, () => {
    loadLayoutConfig()
    loadDashboardData(true)
  })

  return {
    loading,
    error,
    dateRange,
    dashboardData,
    cardStates,
    cardOrder,
    minimizedCards,
    maximizedCard,
    availableCards,
    visibleCards,
    CARD_TYPES,
    CARD_META,
    loadLayoutConfig,
    saveLayoutConfig,
    updateCardOrder,
    toggleMinimize,
    toggleMaximize,
    resetLayout,
    loadDashboardData,
    setDateRange,
    getCardData,
    initializeDashboard
  }
}

export { CARD_TYPES, CARD_META, ROLE_CARD_CONFIG }
