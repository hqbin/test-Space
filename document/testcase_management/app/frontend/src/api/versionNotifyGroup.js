import request from './request'

export function getVersionNotifyGroups(params) {
  return request({ url: '/version-notify-groups', method: 'get', params })
}

export function getAllVersionNotifyGroups() {
  return request({ url: '/version-notify-groups/all', method: 'get' })
}

export function getVersionNotifyGroup(id) {
  return request({ url: `/version-notify-groups/${id}`, method: 'get' })
}

export function createVersionNotifyGroup(data) {
  return request({ url: '/version-notify-groups', method: 'post', data })
}

export function updateVersionNotifyGroup(id, data) {
  return request({ url: `/version-notify-groups/${id}`, method: 'put', data })
}

export function deleteVersionNotifyGroup(id) {
  return request({ url: `/version-notify-groups/${id}`, method: 'delete' })
}

export function addGroupMembers(groupId, data) {
  return request({ url: `/version-notify-groups/${groupId}/members`, method: 'post', data })
}

export function removeGroupMember(groupId, userId) {
  return request({ url: `/version-notify-groups/${groupId}/members/${userId}`, method: 'delete' })
}

export function moveGroupMembers(data) {
  return request({ url: '/version-notify-groups/members/move', method: 'post', data })
}
