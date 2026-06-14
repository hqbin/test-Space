/**
 * 版本信息工具
 */

import { getAgentVersion } from '@services/localAgent'

export const FRONTEND_VERSION = '2.0.0'

/**
 * 在控制台显示版本信息
 */
export async function showVersion() {
  console.log('%c=== ADB Web Tool 版本信息 ===', 'color: #6366f1; font-size: 16px; font-weight: bold')
  console.log(`%c前端版本: v${FRONTEND_VERSION}`, 'color: #2196f3; font-size: 14px')
  
  try {
    const agent = await getAgentVersion()
    if (agent) {
      console.log(`%c代理版本: v${agent.version}`, 'color: #4caf50; font-size: 14px')
      console.log(`%c代理名称: ${agent.name}`, 'color: #4caf50; font-size: 14px')
    } else {
      console.log('%c代理版本: 未运行', 'color: #ff9800; font-size: 14px')
    }
  } catch (error) {
    console.log('%c代理版本: 未运行', 'color: #ff9800; font-size: 14px')
  }
  
  console.log('%c=============================', 'color: #6366f1; font-size: 16px; font-weight: bold')
  console.log('%c提示: 在控制台输入 showVersion() 可随时查看版本信息', 'color: #757575; font-size: 12px')
}

/**
 * 获取版本信息对象
 */
export async function getVersionInfo() {
  const agent = await getAgentVersion()
  return {
    frontend: FRONTEND_VERSION,
    agent: agent?.version || 'not running',
    agentName: agent?.name || 'N/A',
  }
}

// 声明全局类型
declare global {
  interface Window {
    showVersion: typeof showVersion
    getVersionInfo: typeof getVersionInfo
  }
}

// 将函数挂载到 window 对象，方便在控制台调用
if (typeof window !== 'undefined') {
  window.showVersion = showVersion
  window.getVersionInfo = getVersionInfo
}
