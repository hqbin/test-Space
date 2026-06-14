import request from './request'

// 获取角色列表
export const getRoles = (params) => {
  return request.get('/roles', { params })
}

// 创建角色
export const createRole = (data) => {
  return request.post('/roles', data)
}

// 更新角色
export const updateRole = (id, data) => {
  return request.put(`/roles/${id}`, data)
}

// 删除角色
export const deleteRole = (id) => {
  return request.delete(`/roles/${id}`)
}

// 获取用户的角色
export const getUserRoles = (userId) => {
  return request.get(`/roles/user/${userId}/roles`)
}

// 为用户分配角色
export const assignRoles = (userId, roleIds) => {
  return request.post(`/roles/user/${userId}/roles`, roleIds)
}

// 模板相关API
export const getRoleTemplates = () => {
  return request.get('/roles/role-templates')
}

export const createRoleTemplate = (data) => {
  return request.post('/roles/role-templates', data)
}

export const updateRoleTemplate = (id, data) => {
  return request.put(`/roles/role-templates/${id}`, data)
}

export const deleteRoleTemplate = (id) => {
  return request.delete(`/roles/role-templates/${id}`)
}
