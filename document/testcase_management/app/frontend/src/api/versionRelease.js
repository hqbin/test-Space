import request from './request'

export function getVersionReleases(params) {
  return request({ url: '/version-releases', method: 'get', params })
}

export function getVersionRelease(id) {
  return request({ url: `/version-releases/${id}`, method: 'get' })
}

export function createVersionRelease(data) {
  return request({ url: '/version-releases', method: 'post', data })
}

export function updateVersionRelease(id, data) {
  return request({ url: `/version-releases/${id}`, method: 'put', data })
}

export function deleteVersionRelease(id) {
  return request({ url: `/version-releases/${id}`, method: 'delete' })
}

export function publishVersion(id, data) {
  return request({ url: `/version-releases/${id}/publish`, method: 'post', data })
}

export function unpublishVersion(id) {
  return request({ url: `/version-releases/${id}/unpublish`, method: 'post' })
}
