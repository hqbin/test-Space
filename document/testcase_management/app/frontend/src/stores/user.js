import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as loginApi } from '@/api/auth'

export const useUserStore = defineStore('user', () => {
  // 用户信息
  const userInfo = ref(null)
  // Token
  const token = ref(localStorage.getItem('token') || '')
  // 头像缓存破坏时间戳
  const avatarTimestamp = ref(Date.now())

  // 从localStorage加载用户信息
  const loadUserFromStorage = () => {
    const storedUser = localStorage.getItem('user')
    if (storedUser) {
      userInfo.value = JSON.parse(storedUser)
    }
  }

  // 登录
  const login = async (credentials) => {
    const res = await loginApi(credentials)
    if (res.data) {
      token.value = res.data.token || ''
      userInfo.value = res.data.user || res.data
      localStorage.setItem('token', token.value)
      localStorage.setItem('user', JSON.stringify(userInfo.value))
    }
    return res
  }

  // 登出
  const logout = () => {
    token.value = ''
    userInfo.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  // 更新用户信息
  const updateUser = (newUserInfo) => {
    userInfo.value = newUserInfo
    localStorage.setItem('user', JSON.stringify(newUserInfo))
  }

  // 刷新头像（强制浏览器重新加载）
  const refreshAvatar = () => {
    avatarTimestamp.value = Date.now()
  }

  // 清除用户信息
  const clearUser = () => {
    userInfo.value = null
    localStorage.removeItem('user')
  }

  // 计算属性：用户头像URL
  const avatarUrl = computed(() => {
    if (userInfo.value && userInfo.value.avatar) {
      if (userInfo.value.avatar.startsWith('data:')) {
        return userInfo.value.avatar
      }
      if (userInfo.value.avatar.startsWith('http')) {
        return userInfo.value.avatar
      }
      return `${userInfo.value.avatar}?t=${avatarTimestamp.value}`
    }
    const username = userInfo.value?.username || 'default'
    return `https://api.dicebear.com/7.x/avataaars/svg?seed=${username}`
  })

  // 初始化时加载用户信息
  loadUserFromStorage()

  return {
    userInfo,
    token,
    avatarUrl,
    avatarTimestamp,
    loadUserFromStorage,
    login,
    logout,
    updateUser,
    refreshAvatar,
    clearUser
  }
})
