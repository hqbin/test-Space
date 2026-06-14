import { ref } from 'vue'

const STORAGE_KEY = 'projectSelectorPreference'

/**
 * 用例库选择偏好管理（全局单例）
 * 
 * 所有页面共享同一个选择状态：
 * - 在用例管理页面选了某个用例库，其他页面也会自动应用
 * - 刷新页面后从 localStorage 恢复
 * - 项目组切换时重置
 * 
 * 存储格式：
 * - null / 不存在：无偏好（首次使用）
 * - { type: 'all' }：用户选择了"全部用例库"
 * - { type: 'selected', ids: [1, 2, 3] }：用户选择了指定用例库
 */

// 全局共享状态 - 所有页面共用
const selectedProjectIdList = ref([])
let initialized = false

// 从 localStorage 读取偏好
const loadPreference = () => {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) {
      const parsed = JSON.parse(raw)
      // 兼容旧格式（纯数组）
      if (Array.isArray(parsed)) {
        return parsed.length > 0 ? { type: 'selected', ids: parsed } : { type: 'all' }
      }
      return parsed
    }
  } catch {
    // ignore
  }
  return null
}

// 保存偏好到 localStorage
const savePreference = (ids) => {
  try {
    if (ids.length === 0) {
      // 空数组表示"全部用例库"
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ type: 'all' }))
    } else {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ type: 'selected', ids }))
    }
  } catch {
    // ignore
  }
}

/**
 * 当用例库列表加载完成后调用，自动应用偏好或默认选中全部
 * @param {Array} projectList - 可用的用例库列表
 * @returns {number[]} 选中的用例库ID列表
 */
const applyPreference = (projectList) => {
  if (!projectList || projectList.length === 0) {
    selectedProjectIdList.value = []
    initialized = true
    return selectedProjectIdList.value
  }

  // 如果已经初始化且有有效选择，验证选择是否仍然有效
  if (initialized && selectedProjectIdList.value.length > 0) {
    const validIds = selectedProjectIdList.value.filter(id => projectList.some(p => p.id === id))
    if (validIds.length > 0) {
      return selectedProjectIdList.value
    }
  }

  // 从 localStorage 恢复
  const saved = loadPreference()
  if (saved) {
    if (saved.type === 'all') {
      // 用户之前选的是"全部用例库"
      selectedProjectIdList.value = []
      initialized = true
      return selectedProjectIdList.value
    }
    if (saved.type === 'selected' && saved.ids && saved.ids.length > 0) {
      const validIds = saved.ids.filter(id => projectList.some(p => p.id === id))
      if (validIds.length > 0) {
        selectedProjectIdList.value = validIds
        initialized = true
        return selectedProjectIdList.value
      }
    }
  }

  // 无有效偏好（首次使用），默认选中全部用例库
  selectedProjectIdList.value = []
  savePreference([])
  initialized = true
  return selectedProjectIdList.value
}

/**
 * 用户手动切换用例库时调用
 * @param {number[]} ids - 新选中的用例库ID列表
 */
const updateSelection = (ids) => {
  selectedProjectIdList.value = ids
  if (initialized) {
    savePreference(ids)
  }
}

/**
 * 重置偏好（项目组切换时调用）
 */
const resetPreference = () => {
  initialized = false
  selectedProjectIdList.value = []
}

export function useProjectPreference() {
  return {
    selectedProjectIdList,
    applyPreference,
    updateSelection,
    resetPreference
  }
}
