import request from './request'

export const organizationApi = {
  // 部门管理
  getDepartments: (params) => {
    return request({
      url: '/organization/departments',
      method: 'get',
      params
    })
  },

  createDepartment: (data) => {
    return request({
      url: '/organization/departments',
      method: 'post',
      data
    })
  },

  updateDepartment: (id, data) => {
    return request({
      url: `/organization/departments/${id}`,
      method: 'put',
      data
    })
  },

  deleteDepartment: (id) => {
    return request({
      url: `/organization/departments/${id}`,
      method: 'delete'
    })
  },

  // 组织成员管理
  getDepartmentMembers: (deptId, search = '') => {
    return request({
      url: `/organization/departments/${deptId}/members`,
      method: 'get',
      params: { search: search || undefined }
    })
  },

  removeDepartmentMember: (deptId, userId) => {
    return request({
      url: `/organization/departments/${deptId}/members/${userId}`,
      method: 'delete'
    })
  },

  addDepartmentMembers: (deptId, userIds) => {
    return request({
      url: `/organization/departments/${deptId}/members`,
      method: 'post',
      data: { user_ids: userIds }
    })
  },

  getAvailableUsersForDepartment: (deptId, search) => {
    return request({
      url: `/organization/departments/${deptId}/available-users`,
      method: 'get',
      params: { search }
    })
  },

  // 项目组管理
  getProjectGroups: (departmentId) => {
    return request({
      url: '/organization/project-groups',
      method: 'get',
      params: {
        department_id: departmentId,
        size: 1000 // 加载足够多的项目组
      }
    })
  },

  createProjectGroup: (data) => {
    return request({
      url: '/organization/project-groups',
      method: 'post',
      data
    })
  },

  updateProjectGroup: (id, data) => {
    return request({
      url: `/organization/project-groups/${id}`,
      method: 'put',
      data
    })
  },

  deleteProjectGroup: (id) => {
    return request({
      url: `/organization/project-groups/${id}`,
      method: 'delete'
    })
  },

  // 用户组织关联
  assignUserDepartments: (userId, deptIds) => {
    return request({
      url: `/organization/users/${userId}/departments`,
      method: 'post',
      data: { department_ids: deptIds }
    })
  },

  assignUserProjectGroup: (userId, groupId) => {
    return request({
      url: `/organization/users/${userId}/project-groups`,
      method: 'post',
      data: { project_group_id: groupId }
    })
  },

  getUserOrganizations: (userId) => {
    return request({
      url: `/organization/users/${userId}`,
      method: 'get'
    })
  }
}
