import { ref, computed } from 'vue'
import { getUserRoles } from '../api/role'
import { getUserMenus, ALL_PERMISSIONS, BUTTON_PERMISSIONS, FEATURE_PERMISSIONS } from '../config/permissions'

const userPermissions = ref([])
const userMenus = ref({ menus: [], adminMenus: [], standaloneMenus: [], aivoiceMenus: [] })

// 默认超级管理员账号列表
const SUPER_ADMINS = ['admin', 'super']

// 所有权限列表（页面 + 按钮 + 独立功能）
const ALL_PERMISSION_KEYS = [
  ...ALL_PERMISSIONS.map(p => p.key),
  ...Object.values(BUTTON_PERMISSIONS).flatMap(page => Object.values(page).map(btn => btn.key)),
  ...FEATURE_PERMISSIONS.map(p => p.key)
]

export function useUserRole() {
  // 加载用户角色和权限
  const loadUserRoles = async () => {
    try {
      const user = JSON.parse(localStorage.getItem('user') || '{}')
      
      // 如果是默认超级管理员，直接设置所有权限，不受角色管理系统控制
      if (SUPER_ADMINS.includes(user.username)) {
        userPermissions.value = ALL_PERMISSION_KEYS
        // superOnly菜单只对super账号可见
        userMenus.value = getUserMenus(userPermissions.value, user.username)
        return
      }
      
      // 其他用户从数据库加载角色，并获取角色的权限
      if (user.id) {
        const res = await getUserRoles(user.id)
        
        // 合并所有角色的权限
        const permissionsSet = new Set()
        res.data.forEach(role => {
          if (role.permissions && Array.isArray(role.permissions)) {
            role.permissions.forEach(perm => permissionsSet.add(perm))
          }
        })
        
        userPermissions.value = Array.from(permissionsSet)
      }
      
      // 如果没有权限，默认为空（无任何菜单）
      if (userPermissions.value.length === 0) {
        userPermissions.value = []
      }

      // 更新用户菜单，传入username用于过滤superOnly菜单
      userMenus.value = getUserMenus(userPermissions.value, user.username)
    } catch (error) {
      // 默认为空权限
      userPermissions.value = []
      const user = JSON.parse(localStorage.getItem('user') || '{}')
      userMenus.value = getUserMenus(userPermissions.value, user.username)
    }
  }

  // 检查是否有某个菜单权限
  const hasMenu = (menuKey) => {
    return userPermissions.value.includes(menuKey)
  }

  // 检查是否有某个按钮权限
  // 超级管理员拥有所有权限
  // 普通用户：需要明确拥有该按钮权限
  const hasButton = (page, action) => {
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    
    // 超级管理员拥有所有权限
    if (SUPER_ADMINS.includes(user.username)) {
      return true
    }
    
    // 检查是否有具体的按钮权限
    const buttonPermissionKey = `${page}.${action}`
    return userPermissions.value.includes(buttonPermissionKey)
  }

  // 检查是否有某个独立功能权限
  const hasFeature = (featureKey) => {
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    if (SUPER_ADMINS.includes(user.username)) {
      return true
    }
    return userPermissions.value.includes(featureKey)
  }

  // 是否是管理员（拥有所有管理功能权限）
  const isAdmin = computed(() => {
    const adminPermissions = ['users', 'projects', 'roles']
    return adminPermissions.every(perm => userPermissions.value.includes(perm))
  })
  
  // 是否是超级管理员
  const isSuperAdmin = computed(() => {
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    return SUPER_ADMINS.includes(user.username)
  })

  return {
    userPermissions,
    userMenus,
    loadUserRoles,
    hasMenu,
    hasButton,
    hasFeature,
    isAdmin,
    isSuperAdmin
  }
}
