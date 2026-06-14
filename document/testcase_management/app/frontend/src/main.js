import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import App from './App.vue'
import router from './router'
import i18n from './i18n'
import './styles/global.css'
import './styles/responsive.css'
import './styles/table-optimization.css'
import './styles/table-layout.css'
import './styles/tooltip.css'
import './styles/demo-theme.css'  // Demo UI主题样式
import './assets/performance.css'  // 性能优化样式
import './styles/mobile-theme.css'
import { debounce } from 'lodash-es'

const app = createApp(App)
const pinia = createPinia()

for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(pinia)
app.use(router)
app.use(i18n)
app.use(ElementPlus)

// 抑制 Vue 运行时 directive 警告（Element Plus ElDialog 组件问题，不影响功能）
// 抑制 prop type check 警告
const originalWarn = console.warn
console.warn = (...args) => {
  if (args[0] && typeof args[0] === 'string') {
    if (args[0].includes('Runtime directive')) return
    if (args[0].includes('Invalid prop')) return
  }
  originalWarn.apply(console, args)
}

app.mount('#app')

// 处理表格 title 属性和 tooltip 换行 — 使用 requestIdleCallback 避免阻塞主线程
const _ric = window.requestIdleCallback || ((cb) => setTimeout(cb, 50))

function processTableTitles() {
  _ric(() => {
    const tableCells = document.querySelectorAll('.el-table .cell[title]')
    tableCells.forEach(cell => cell.removeAttribute('title'))
  })
}

function processTooltips() {
  const tooltips = document.querySelectorAll('.el-tooltip__popper.is-dark, .el-popper.is-dark')
  tooltips.forEach(tooltip => {
    if (tooltip.dataset.processed) return
    const textContent = tooltip.textContent || tooltip.innerText
    if (textContent && (textContent.includes('\n') || textContent.includes('\r'))) {
      tooltip.innerHTML = textContent
        .replace(/\r\n/g, '<br>')
        .replace(/\n/g, '<br>')
        .replace(/\r/g, '<br>')
      tooltip.dataset.processed = 'true'
    }
  })
}

// 只监听 tooltip 弹出层容器（body 直接子节点），debounce 300ms 减少触发频率
const tooltipObserver = new MutationObserver(debounce(() => {
  _ric(processTooltips)
}, 300))

tooltipObserver.observe(document.body, {
  childList: true,
  subtree: false
})

// 路由切换后处理表格 title — 延迟到空闲时执行，不阻塞路由过渡
router.afterEach(() => {
  _ric(processTableTitles)
})

// 清理函数
window.addEventListener('beforeunload', () => {
  tooltipObserver.disconnect()
})








