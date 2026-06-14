/**
 * 简单的事件总线，用于跨组件通信
 * 主要用于：管理页面 CRUD 操作后通知其他组件刷新数据
 * 
 * 事件列表：
 * - teams-changed: 项目组增删改后触发
 * - projects-changed: 用例库增删改后触发
 * - users-changed: 用户增删改后触发
 * - organization-changed: 组织增删改后触发
 * - roles-changed: 角色增删改后触发
 */

class EventBus {
  constructor() {
    this.listeners = {}
  }

  on(event, callback) {
    if (!this.listeners[event]) {
      this.listeners[event] = []
    }
    this.listeners[event].push(callback)
  }

  off(event, callback) {
    if (!this.listeners[event]) return
    this.listeners[event] = this.listeners[event].filter(cb => cb !== callback)
  }

  emit(event, data) {
    if (!this.listeners[event]) return
    this.listeners[event].forEach(cb => cb(data))
  }
}

export const eventBus = new EventBus()
