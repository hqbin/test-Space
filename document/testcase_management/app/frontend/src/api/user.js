import request from './request'

export const getUsers = (params) => {
  return request({
    url: '/users',
    method: 'get',
    params
  })
}

export const createUser = (data) => {
  return request({
    url: '/users',
    method: 'post',
    data
  })
}

export const updateUser = (id, data) => {
  return request({
    url: `/users/${id}`,
    method: 'put',
    data
  })
}

export const deleteUser = (id) => {
  return request({
    url: `/users/${id}`,
    method: 'delete'
  })
}

export const toggleUserStatus = (id) => {
  return request({
    url: `/users/${id}/toggle-status`,
    method: 'put'
  })
}

export const resetUserPassword = (id) => {
  return request({
    url: `/users/${id}/reset-password`,
    method: 'post'
  })
}

export const unlockUser = (id) => {
  return request({
    url: `/users/${id}/unlock`,
    method: 'post'
  })
}

export const getUserList = (params = {}) => {
  return request({
    url: '/users',
    method: 'get',
    params: {
      size: 1000, // 加载足够多的用户
      ...params
    }
  })
}

export const getPendingUsers = () => {
  return request({
    url: '/users/pending',
    method: 'get'
  })
}

export const approveUser = (id, data = {}) => {
  return request({
    url: `/users/pending/${id}/approve`,
    method: 'post',
    data
  })
}

export const rejectUser = (id) => {
  return request({
    url: `/users/pending/${id}/reject`,
    method: 'post'
  })
}

// Mobile API aliases
export const getUserDetail = (id) => {
  return request({
    url: `/users/${id}`,
    method: 'get'
  })
}

export const getPendingRegistrations = () => {
  return request({
    url: '/users/pending',
    method: 'get'
  })
}

export const approveRegistration = (id) => {
  return request({
    url: `/users/pending/${id}/approve`,
    method: 'post'
  })
}

export const rejectRegistration = (id, data = {}) => {
  return request({
    url: `/users/pending/${id}/reject`,
    method: 'post',
    data
  })
}

export const downloadUserTemplate = () => {
  return request({
    url: '/users/template',
    method: 'get',
    responseType: 'blob'
  })
}

export const importUsers = (file, overwrite = false) => {
  const formData = new FormData()
  formData.append('file', file)
  if (overwrite) {
    formData.append('overwrite', 'true')
  }
  return request({
    url: '/users/batch-import',
    method: 'post',
    data: formData,
    timeout: 300000,  // 5分钟超时，大文件上传需要更长时间
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

export const getImportProgress = (taskId) => {
  return request({
    url: `/users/batch-import/progress/${taskId}`,
    method: 'get'
  })
}
