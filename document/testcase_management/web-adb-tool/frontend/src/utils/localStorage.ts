/**
 * LocalStorage 工具类
 * 
 * 用于管理应用的本地存储数据
 */

export interface CustomButton {
  id: string
  name: string
  command: string
  description?: string
  created_at: string
}

export interface IpHistoryEntry {
  ip: string
  port: number
  last_used: string
}

const STORAGE_KEYS = {
  CUSTOM_BUTTONS: 'adb_tool_custom_buttons',
  IP_HISTORY: 'adb_tool_ip_history',
  USER_PREFERENCES: 'adb_tool_preferences',
}

// ==================== 自定义按钮管理 ====================

export const getCustomButtons = (): CustomButton[] => {
  try {
    const data = localStorage.getItem(STORAGE_KEYS.CUSTOM_BUTTONS)
    return data ? JSON.parse(data) : []
  } catch (error) {
    console.error('Failed to get custom buttons:', error)
    return []
  }
}

export const saveCustomButton = (button: Omit<CustomButton, 'id' | 'created_at'>): CustomButton => {
  const buttons = getCustomButtons()
  const newButton: CustomButton = {
    ...button,
    id: Date.now().toString(),
    created_at: new Date().toISOString(),
  }
  buttons.push(newButton)
  localStorage.setItem(STORAGE_KEYS.CUSTOM_BUTTONS, JSON.stringify(buttons))
  return newButton
}

export const updateCustomButton = (id: string, updates: Partial<CustomButton>): boolean => {
  const buttons = getCustomButtons()
  const index = buttons.findIndex(b => b.id === id)
  if (index === -1) return false
  
  buttons[index] = { ...buttons[index], ...updates }
  localStorage.setItem(STORAGE_KEYS.CUSTOM_BUTTONS, JSON.stringify(buttons))
  return true
}

export const deleteCustomButton = (id: string): boolean => {
  const buttons = getCustomButtons()
  const filtered = buttons.filter(b => b.id !== id)
  if (filtered.length === buttons.length) return false
  
  localStorage.setItem(STORAGE_KEYS.CUSTOM_BUTTONS, JSON.stringify(filtered))
  return true
}

// ==================== IP 历史记录管理 ====================

export const getIpHistory = (limit: number = 10): IpHistoryEntry[] => {
  try {
    const data = localStorage.getItem(STORAGE_KEYS.IP_HISTORY)
    const history: IpHistoryEntry[] = data ? JSON.parse(data) : []
    return history.slice(0, limit)
  } catch (error) {
    console.error('Failed to get IP history:', error)
    return []
  }
}

export const addIpToHistory = (ip: string, port: number): void => {
  try {
    let history = getIpHistory(100) // 获取更多历史记录用于去重
    
    // 移除已存在的相同 IP:port
    history = history.filter(entry => !(entry.ip === ip && entry.port === port))
    
    // 添加到开头
    history.unshift({
      ip,
      port,
      last_used: new Date().toISOString(),
    })
    
    // 只保留最近 20 条
    history = history.slice(0, 20)
    
    localStorage.setItem(STORAGE_KEYS.IP_HISTORY, JSON.stringify(history))
  } catch (error) {
    console.error('Failed to add IP to history:', error)
  }
}

export const clearIpHistory = (): void => {
  localStorage.removeItem(STORAGE_KEYS.IP_HISTORY)
}

// ==================== 用户偏好设置 ====================

export interface UserPreferences {
  theme?: 'light' | 'dark'
  language?: string
  autoRefresh?: boolean
  [key: string]: any
}

export const getUserPreferences = (): UserPreferences => {
  try {
    const data = localStorage.getItem(STORAGE_KEYS.USER_PREFERENCES)
    return data ? JSON.parse(data) : {}
  } catch (error) {
    console.error('Failed to get user preferences:', error)
    return {}
  }
}

export const saveUserPreferences = (preferences: UserPreferences): void => {
  try {
    const current = getUserPreferences()
    const updated = { ...current, ...preferences }
    localStorage.setItem(STORAGE_KEYS.USER_PREFERENCES, JSON.stringify(updated))
  } catch (error) {
    console.error('Failed to save user preferences:', error)
  }
}

export const clearUserPreferences = (): void => {
  localStorage.removeItem(STORAGE_KEYS.USER_PREFERENCES)
}

// ==================== 清除所有数据 ====================

export const clearAllData = (): void => {
  Object.values(STORAGE_KEYS).forEach(key => {
    localStorage.removeItem(key)
  })
}

// ==================== 数据导入导出 ====================

export interface ExportData {
  version: string
  exportDate: string
  customButtons: CustomButton[]
  ipHistory: IpHistoryEntry[]
  userPreferences: UserPreferences
}

/**
 * 导出所有数据为 JSON
 */
export const exportAllData = (): string => {
  const data: ExportData = {
    version: '1.0',
    exportDate: new Date().toISOString(),
    customButtons: getCustomButtons(),
    ipHistory: getIpHistory(100),
    userPreferences: getUserPreferences(),
  }
  return JSON.stringify(data, null, 2)
}

/**
 * 从 JSON 导入数据
 * @param jsonData - JSON 字符串
 * @param merge - 是否合并现有数据（true）还是覆盖（false）
 */
export const importAllData = (jsonData: string, merge: boolean = false): boolean => {
  try {
    const data: ExportData = JSON.parse(jsonData)
    
    // 验证数据格式
    if (!data.version || !data.customButtons || !data.ipHistory) {
      throw new Error('Invalid data format')
    }
    
    if (merge) {
      // 合并模式：保留现有数据，添加新数据
      const existingButtons = getCustomButtons()
      const existingHistory = getIpHistory(100)
      
      // 合并自定义按钮（避免重复）
      const existingButtonNames = new Set(existingButtons.map(b => b.name))
      const newButtons = data.customButtons.filter(b => !existingButtonNames.has(b.name))
      const mergedButtons = [...existingButtons, ...newButtons]
      localStorage.setItem(STORAGE_KEYS.CUSTOM_BUTTONS, JSON.stringify(mergedButtons))
      
      // 合并 IP 历史（避免重复）
      const existingIpSet = new Set(existingHistory.map(h => `${h.ip}:${h.port}`))
      const newHistory = data.ipHistory.filter(h => !existingIpSet.has(`${h.ip}:${h.port}`))
      const mergedHistory = [...existingHistory, ...newHistory].slice(0, 20)
      localStorage.setItem(STORAGE_KEYS.IP_HISTORY, JSON.stringify(mergedHistory))
      
      // 合并用户偏好
      const mergedPreferences = { ...getUserPreferences(), ...data.userPreferences }
      localStorage.setItem(STORAGE_KEYS.USER_PREFERENCES, JSON.stringify(mergedPreferences))
    } else {
      // 覆盖模式：直接替换所有数据
      localStorage.setItem(STORAGE_KEYS.CUSTOM_BUTTONS, JSON.stringify(data.customButtons))
      localStorage.setItem(STORAGE_KEYS.IP_HISTORY, JSON.stringify(data.ipHistory))
      localStorage.setItem(STORAGE_KEYS.USER_PREFERENCES, JSON.stringify(data.userPreferences))
    }
    
    return true
  } catch (error) {
    console.error('Failed to import data:', error)
    return false
  }
}

/**
 * 下载数据为 JSON 文件
 */
export const downloadDataAsFile = (): void => {
  const jsonData = exportAllData()
  const blob = new Blob([jsonData], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `adb-tool-backup-${new Date().toISOString().split('T')[0]}.json`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

/**
 * 从文件读取并导入数据
 */
export const importDataFromFile = (file: File, merge: boolean = false): Promise<boolean> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    
    reader.onload = (e) => {
      try {
        const jsonData = e.target?.result as string
        const success = importAllData(jsonData, merge)
        resolve(success)
      } catch (error) {
        reject(error)
      }
    }
    
    reader.onerror = () => {
      reject(new Error('Failed to read file'))
    }
    
    reader.readAsText(file)
  })
}

// ==================== 通用输入历史记录（按 key 隔离，最近优先，上限 15） ====================

const INPUT_HISTORY_KEY = 'adb_tool_input_history'
const INPUT_HISTORY_LIMIT = 15

type InputHistoryStore = Record<string, string[]>

const readInputHistoryStore = (): InputHistoryStore => {
  try {
    const data = localStorage.getItem(INPUT_HISTORY_KEY)
    return data ? (JSON.parse(data) as InputHistoryStore) : {}
  } catch {
    return {}
  }
}

const writeInputHistoryStore = (store: InputHistoryStore): void => {
  try {
    localStorage.setItem(INPUT_HISTORY_KEY, JSON.stringify(store))
  } catch (error) {
    console.error('Failed to write input history:', error)
  }
}

/** 获取指定 key 的输入历史（最新在前，去重，最多 15 条） */
export const getInputHistory = (key: string): string[] => {
  const store = readInputHistoryStore()
  return Array.isArray(store[key]) ? store[key].slice(0, INPUT_HISTORY_LIMIT) : []
}

/** 添加一条输入到指定 key 的历史，最新替换最旧，最多保留 15 条 */
export const addInputHistory = (key: string, value: string): void => {
  const trimmed = value.trim()
  if (!trimmed) return
  const store = readInputHistoryStore()
  const list = Array.isArray(store[key]) ? store[key] : []
  // 去重：移除相同值
  const deduped = list.filter((item) => item !== trimmed)
  // 添加到开头
  deduped.unshift(trimmed)
  // 截断到 15
  store[key] = deduped.slice(0, INPUT_HISTORY_LIMIT)
  writeInputHistoryStore(store)
}

/** 清空指定 key 的历史 */
export const clearInputHistory = (key: string): void => {
  const store = readInputHistoryStore()
  delete store[key]
  writeInputHistoryStore(store)
}
