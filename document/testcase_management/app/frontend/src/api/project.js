import request from './request'

export const getProjects = (params) => {
  return request({
    url: '/projects',
    method: 'get',
    params
  })
}

export const getProjectTree = () => {
  return request({
    url: '/projects/tree',
    method: 'get'
  })
}

export const createProject = (data) => {
  return request({
    url: '/projects',
    method: 'post',
    data
  })
}

export const updateProject = (id, data) => {
  return request({
    url: `/projects/${id}`,
    method: 'put',
    data
  })
}

export const deleteProject = (id) => {
  return request({
    url: `/projects/${id}`,
    method: 'delete'
  })
}

export const toggleProjectStatus = (id) => {
  return request({
    url: `/projects/${id}/status`,
    method: 'patch'
  })
}

export const getUserAccessibleTeams = () => {
  return request({
    url: '/projects/user-teams',
    method: 'get'
  })
}

export const updateProjectTeams = (projectId, teamIds) => {
  return request({
    url: `/projects/${projectId}/teams`,
    method: 'put',
    data: teamIds
  })
}
