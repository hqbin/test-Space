import { ref, computed } from 'vue'
import { getMyProjects } from '../api/userProject'
import { eventBus } from '../utils/eventBus'

// 从localStorage恢复初始状态
const savedProjectId = localStorage.getItem('currentProjectId')
const savedProjectName = localStorage.getItem('currentProjectName')

// 全局共享的状态（单例模式）
const currentProject = ref(
  savedProjectId && savedProjectName 
    ? { id: parseInt(savedProjectId), name: savedProjectName }
    : null
)
const projectList = ref([])

// 加载用户的项目列表
const loadProjects = async () => {
  try {
    const res = await getMyProjects()
    projectList.value = res.data || []
    
    // 如果有项目，自动选择第一个（或从localStorage恢复）
    if (projectList.value.length > 0) {
      const savedProjectId = localStorage.getItem('currentProjectId')
      const savedProject = projectList.value.find(p => p.id === parseInt(savedProjectId))
      
      if (savedProject) {
        currentProject.value = savedProject
      } else {
        currentProject.value = projectList.value[0]
        localStorage.setItem('currentProjectId', currentProject.value.id)
        localStorage.setItem('currentProjectName', currentProject.value.name)
      }
    }
  } catch (error) {
    // 静默失败
  }
}

// 切换当前项目
const switchProject = (project) => {
  currentProject.value = project
  if (project) {
    localStorage.setItem('currentProjectId', project.id)
    localStorage.setItem('currentProjectName', project.name)
  } else {
    localStorage.removeItem('currentProjectId')
    localStorage.removeItem('currentProjectName')
  }
}

// 获取当前项目ID
const currentProjectId = computed(() => {
  return currentProject.value?.id || null
})

// 监听事件总线，自动刷新数据
eventBus.on('projects-changed', () => {
  loadProjects()
})

// 导出单例
export function useProject() {
  return {
    currentProject,
    projectList,
    currentProjectId,
    loadProjects,
    switchProject
  }
}
