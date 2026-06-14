import { ref, computed } from 'vue'
import { getMyTeams, getTeamProjects } from '../api/team'
import { eventBus } from '../utils/eventBus'

// 从localStorage恢复初始状态
const savedTeamId = localStorage.getItem('currentTeamId')
const savedTeamName = localStorage.getItem('currentTeamName')

// 全局共享的状态（单例模式）
const currentTeam = ref(
  savedTeamId && savedTeamName 
    ? { id: parseInt(savedTeamId), name: savedTeamName }
    : null
)
const teamList = ref([])
const teamProjects = ref([])  // 当前项目组的用例库列表
const loadingTeams = ref(false)
const loadingProjects = ref(false)

// 加载用户的项目组列表
const loadTeams = async () => {
  loadingTeams.value = true
  try {
    const res = await getMyTeams()
    teamList.value = res.data || []
    
    // 如果有项目组，自动选择第一个（或从localStorage恢复）
    if (teamList.value.length > 0) {
      const savedTeamId = localStorage.getItem('currentTeamId')
      const savedTeam = teamList.value.find(t => t.id === parseInt(savedTeamId))
      
      if (savedTeam) {
        currentTeam.value = savedTeam
      } else {
        currentTeam.value = teamList.value[0]
        localStorage.setItem('currentTeamId', currentTeam.value.id)
        localStorage.setItem('currentTeamName', currentTeam.value.name)
      }
      
      // 加载当前项目组的用例库
      await loadTeamProjects()
    } else {
      currentTeam.value = null
      teamProjects.value = []
    }
  } catch (error) {
    console.error('加载项目组列表失败:', error)
  } finally {
    loadingTeams.value = false
  }
}

// 加载当前项目组的用例库列表
const loadTeamProjects = async () => {
  if (!currentTeam.value) {
    teamProjects.value = []
    return
  }
  
  loadingProjects.value = true
  try {
    const res = await getTeamProjects(currentTeam.value.id)
    teamProjects.value = res.data || []
  } catch (error) {
    console.error('加载用例库列表失败:', error)
    teamProjects.value = []
  } finally {
    loadingProjects.value = false
  }
}

// 切换当前项目组
const switchTeam = async (team) => {
  currentTeam.value = team
  if (team) {
    localStorage.setItem('currentTeamId', team.id)
    localStorage.setItem('currentTeamName', team.name)
    // 切换项目组后加载该项目组的用例库
    await loadTeamProjects()
    // 通知所有页面项目组已切换（标记为内部切换，不触发自身重新加载）
    _isInternalSwitch = true
    eventBus.emit('teams-changed')
    _isInternalSwitch = false
  } else {
    localStorage.removeItem('currentTeamId')
    localStorage.removeItem('currentTeamName')
    teamProjects.value = []
    _isInternalSwitch = true
    eventBus.emit('teams-changed')
    _isInternalSwitch = false
  }
}

// 获取当前项目组ID
const currentTeamId = computed(() => {
  return currentTeam.value?.id || null
})

// 内部切换标记，避免 switchTeam 触发自身的 teams-changed 监听导致循环
let _isInternalSwitch = false

// 监听事件总线，仅在外部变更（如组织管理增删项目组）时刷新
eventBus.on('teams-changed', () => {
  if (!_isInternalSwitch) {
    loadTeams()
  }
})

eventBus.on('projects-changed', () => {
  // 用例库变化时，刷新当前项目组的用例库列表
  loadTeamProjects()
})

// 导出单例
export function useTeam() {
  return {
    currentTeam,
    teamList,
    teamProjects,
    currentTeamId,
    loadingTeams,
    loadingProjects,
    loadTeams,
    loadTeamProjects,
    switchTeam
  }
}
