import request from './request'

/**
 * 获取通知列表
 * @param {Object} params - 查询参数
 * @param {number} params.page - 页码
 * @param {number} params.size - 每页数量
 * @param {string} params.notification_type - 通知类型筛选
 * @param {boolean} params.is_read - 已读状态筛选
 */
export function getNotifications(params) {
  return request({
    url: '/notifications',
    method: 'get',
    params
  })
}

/**
 * 获取未读通知数量
 */
export function getUnreadCount() {
  return request({
    url: '/notifications/unread-count',
    method: 'get'
  })
}

/**
 * 获取通知详情
 * @param {number} id - 通知ID
 */
export function getNotificationDetail(id) {
  return request({
    url: `/notifications/${id}`,
    method: 'get'
  })
}

/**
 * 标记通知为已读
 * @param {number} id - 通知ID
 */
export function markAsRead(id) {
  return request({
    url: `/notifications/${id}/read`,
    method: 'put'
  })
}

/**
 * 全部标记为已读
 */
export function markAllAsRead() {
  return request({
    url: '/notifications/read-all',
    method: 'put'
  })
}

/**
 * 删除通知
 * @param {number} id - 通知ID
 */
export function deleteNotification(id) {
  return request({
    url: `/notifications/${id}`,
    method: 'delete'
  })
}

// ==================== 通知规则管理 ====================

/**
 * 获取通知规则列表
 * @param {Object} params - 查询参数
 */
export function getNotificationRules(params) {
  return request({
    url: '/notification-rules',
    method: 'get',
    params
  })
}

/**
 * 创建通知规则
 * @param {Object} data - 规则数据
 */
export function createNotificationRule(data) {
  return request({
    url: '/notification-rules',
    method: 'post',
    data
  })
}

/**
 * 更新通知规则
 * @param {number} id - 规则ID
 * @param {Object} data - 规则数据
 */
export function updateNotificationRule(id, data) {
  return request({
    url: `/notification-rules/${id}`,
    method: 'put',
    data
  })
}

/**
 * 删除通知规则
 * @param {number} id - 规则ID
 */
export function deleteNotificationRule(id) {
  return request({
    url: `/notification-rules/${id}`,
    method: 'delete'
  })
}

// ==================== 通知模板管理 ====================

/**
 * 获取通知模板列表
 * @param {Object} params - 查询参数
 */
export function getNotificationTemplates(params) {
  return request({
    url: '/notification-templates',
    method: 'get',
    params
  })
}

/**
 * 创建通知模板
 * @param {Object} data - 模板数据
 */
export function createNotificationTemplate(data) {
  return request({
    url: '/notification-templates',
    method: 'post',
    data
  })
}

/**
 * 更新通知模板
 * @param {number} id - 模板ID
 * @param {Object} data - 模板数据
 */
export function updateNotificationTemplate(id, data) {
  return request({
    url: `/notification-templates/${id}`,
    method: 'put',
    data
  })
}

/**
 * 删除通知模板
 * @param {number} id - 模板ID
 */
export function deleteNotificationTemplate(id) {
  return request({
    url: `/notification-templates/${id}`,
    method: 'delete'
  })
}

// ==================== 用户通知偏好设置 ====================

/**
 * 获取用户通知偏好设置
 */
export function getNotificationPreferences() {
  return request({
    url: '/notifications/preferences',
    method: 'get'
  })
}

/**
 * 更新用户通知偏好设置
 * @param {Array} preferences - 偏好设置列表
 */
export function updateNotificationPreferences(preferences) {
  return request({
    url: '/notifications/preferences',
    method: 'put',
    data: preferences
  })
}
