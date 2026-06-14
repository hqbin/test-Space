import request from './request'

// ==================== 钉钉机器人配置管理 ====================

export function getDingtalkBots(params) {
  return request({ url: '/dingtalk-bots', method: 'get', params })
}

export function createDingtalkBot(data) {
  return request({ url: '/dingtalk-bots', method: 'post', data })
}

export function updateDingtalkBot(id, data) {
  return request({ url: `/dingtalk-bots/${id}`, method: 'put', data })
}

export function deleteDingtalkBot(id) {
  return request({ url: `/dingtalk-bots/${id}`, method: 'delete' })
}

export function toggleDingtalkBot(id) {
  return request({ url: `/dingtalk-bots/${id}/toggle`, method: 'put' })
}

export function testDingtalkBot(id) {
  return request({ url: `/dingtalk-bots/${id}/test`, method: 'post' })
}
