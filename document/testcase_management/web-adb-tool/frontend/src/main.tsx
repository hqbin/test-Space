import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'
import './utils/version'  // 导入版本工具，使其在控制台可用

// 嵌入模式检测：
// embedded.html 已在 <script> 标签中设置 window.__ADB_EMBEDDED__ = true
// 这里只需处理 hash 路径转换（平台通过 embedded.html#/devices 传递子页面）
if ((window as any).__ADB_EMBEDDED__) {
  const hash = window.location.hash
  if (hash && hash.startsWith('#/')) {
    // #/devices -> /adb-tool/devices
    const targetPath = '/adb-tool' + hash.slice(1)
    window.history.replaceState(null, '', targetPath)
  } else if (window.location.pathname === '/adb-tool/embedded.html' || window.location.pathname === '/adb-tool/index.html') {
    // 修正路径，避免路由不匹配
    window.history.replaceState(null, '', '/adb-tool/')
  }
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
