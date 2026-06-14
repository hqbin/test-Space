import request from './request'

// 为用户分配项目组
export function assignTeams(data) {
  return request({
    url: '/user-teams/assign',
    method: 'post',
    data
  })
}

// 获取用户的项目组
export function getUserTeams(userId) {
  return request({
    url: `/user-teams/${userId}`,
    method: 'get'
  })
}

// 从项目组中移除成员
export function removeMember(data) {
  return request({
    url: '/user-teams/remove-member',
    method: 'post',
    data
  })
}
