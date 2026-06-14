import request from './request'

// 获取系统日志列表
export function getSystemLogs(params) {
  return request({
    url: '/system/logs',
    method: 'get',
    params
  })
}

// 获取日志模块列表
export function getLogModules() {
  return request({
    url: '/system/logs/modules',
    method: 'get'
  })
}

// 获取日志操作类型列表
export function getLogActions() {
  return request({
    url: '/system/logs/actions',
    method: 'get'
  })
}

// 获取日志统计信息
export function getLogStats(days = 7) {
  return request({
    url: '/system/logs/stats',
    method: 'get',
    params: { days }
  })
}
