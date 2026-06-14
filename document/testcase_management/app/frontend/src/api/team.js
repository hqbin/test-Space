import request from './request'

// 获取项目组列表
export function getTeams(params) {
  return request({
    url: '/teams',
    method: 'get',
    params
  })
}

// 创建项目组
export function createTeam(data) {
  return request({
    url: '/teams',
    method: 'post',
    data
  })
}

// 更新项目组
export function updateTeam(id, data) {
  return request({
    url: `/teams/${id}`,
    method: 'put',
    data
  })
}

// 删除项目组
export function deleteTeam(id) {
  return request({
    url: `/teams/${id}`,
    method: 'delete'
  })
}

// 获取项目组成员
export function getTeamMembers(id) {
  return request({
    url: `/teams/${id}/members`,
    method: 'get'
  })
}

// 为项目组授权用例库
export function assignProjectsToTeam(data) {
  return request({
    url: '/teams/assign-projects',
    method: 'post',
    data
  })
}

// 获取项目组的用例库
export function getTeamProjects(id) {
  return request({
    url: `/teams/${id}/projects`,
    method: 'get'
  })
}

// 获取当前用户被授权的项目组列表
export function getMyTeams() {
  return request({
    url: '/teams/my-teams',
    method: 'get'
  })
}

// 获取当前用户在项目组中的角色
export function getUserRoleInTeam(teamId) {
  return request({
    url: `/teams/${teamId}/user-role`,
    method: 'get'
  })
}

// 获取可选择的成员列表
export function getAvailableMembersForSelection(teamId, selectionType = 'executor', search = '') {
  return request({
    url: `/teams/${teamId}/available-members`,
    method: 'get',
    params: { 
      selection_type: selectionType,
      search: search || undefined
    }
  })
}

// 根据用例库ID获取对应的项目组
export function getTeamByProject(projectId) {
  return request({
    url: `/teams/by-project/${projectId}`,
    method: 'get'
  })
}
