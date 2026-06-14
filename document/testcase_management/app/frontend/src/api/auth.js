import request from './request'

export const login = (data) => {
  return request({
    url: '/auth/login',
    method: 'post',
    data
  })
}

export const logout = () => {
  return request({
    url: '/auth/logout',
    method: 'post'
  })
}

export const refreshToken = () => {
  return request({
    url: '/auth/refresh',
    method: 'post',
    // 标记此请求为续签请求，拦截器内不参与 401 重试链
    _isRefresh: true
  })
}

export const register = (data) => {
  return request({
    url: '/auth/register',
    method: 'post',
    data
  })
}
