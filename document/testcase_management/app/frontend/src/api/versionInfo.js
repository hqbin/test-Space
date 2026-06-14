import request from './request'

export function getPublishedVersions(params) {
  return request({ url: '/version-info', method: 'get', params })
}
