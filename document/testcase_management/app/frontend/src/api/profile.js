import request from './request'

/**
 * 修改密码
 */
export function changePassword(data) {
  return request({
    url: '/users/change-password',
    method: 'post',
    data
  })
}

/**
 * 上传头像
 */
export function uploadAvatar(file) {
  const formData = new FormData()
  formData.append('file', file)
  
  return request({
    url: '/users/avatar',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

/**
 * 删除头像
 */
export function deleteAvatar() {
  return request({
    url: '/users/avatar',
    method: 'delete'
  })
}

/**
 * 获取当前用户信息
 */
export function getCurrentUser() {
  return request({
    url: '/auth/me',
    method: 'get'
  })
}

/**
 * 更新个人资料
 */
export function updateProfile(data) {
  return request({
    url: '/users/profile',
    method: 'put',
    data
  })
}
