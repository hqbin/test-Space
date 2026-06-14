import request from './request'

// 获取用户的项目授权
export const getUserProjects = (userId) => {
  return request.get(`/user-projects/user/${userId}/projects`)
}

// 获取当前用户的项目列表
export const getMyProjects = () => {
  return request.get('/user-projects/my-projects')
}

// 为用户分配项目
export const assignProjects = (data) => {
  return request.post('/user-projects/assign', data)
}

// 移除用户的项目授权
export const removeUserProject = (userId, projectId) => {
  return request.delete(`/user-projects/user/${userId}/project/${projectId}`)
}
