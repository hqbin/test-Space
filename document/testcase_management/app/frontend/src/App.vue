<template>
  <el-config-provider :locale="elementLocale">
    <div id="app">
      <router-view />
    </div>
  </el-config-provider>
</template>

<script setup>
import { computed, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElConfigProvider } from 'element-plus'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import en from 'element-plus/dist/locale/en.mjs'

const { locale } = useI18n()

const elementLocale = computed(() => {
  return locale.value === 'en-US' ? en : zhCn
})

// 自适应 zoom：基于物理屏幕宽度（screen.width）
// 使用 screen.width 而非 innerWidth，这样：
// 1. 不受浏览器 Ctrl+/- 缩放影响（用户仍可自由缩放）
// 2. 自动适配 OS 缩放比例（如 200% 缩放下 screen.width 会变小）
const BASE_WIDTH = 1920
const MAX_ZOOM = 1
// 分段缩放策略：
// - 宽屏（>=1920）：不缩放
// - 中等屏幕（1200~1920）：温和缩放（0.85~1），适合 125%~150% 缩放
// - 小屏幕（<1200）：激进缩放（按比例），适合 200%+ 高缩放
const BREAK_POINT = 1200
const BREAK_ZOOM = 0.85

const applyZoom = () => {
  const width = window.screen.width
  const el = document.getElementById('app')
  if (!el) return
  const ua = navigator.userAgent || ''
  const isMobileDevice = /Android|iPhone|iPad|iPod|Mobile|HarmonyOS/i.test(ua) || window.innerWidth <= 900
  const isMobileRoute = window.location.pathname.startsWith('/m/')
  // 移动端页面不做全局缩放，避免界面被压缩得过小
  if (isMobileDevice || isMobileRoute) {
    el.style.zoom = 1
    return
  }
  if (width >= BASE_WIDTH) {
    el.style.zoom = MAX_ZOOM
  } else if (width >= BREAK_POINT) {
    // 1200~1920 线性映射到 0.85~1
    const ratio = (width - BREAK_POINT) / (BASE_WIDTH - BREAK_POINT)
    el.style.zoom = BREAK_ZOOM + ratio * (MAX_ZOOM - BREAK_ZOOM)
  } else {
    // <1200 直接按比例缩放
    el.style.zoom = width / BASE_WIDTH
  }
}

// 监听 DPI 变化（如拖拽窗口到不同缩放比例的显示器）
let dpiMql = null
const watchDpiChange = () => {
  // 清理旧的监听器
  if (dpiMql) {
    dpiMql.removeEventListener('change', onDpiChange)
    dpiMql = null
  }
  // 创建匹配当前 DPI 的媒体查询，当 DPI 变化时触发
  const dpr = window.devicePixelRatio || 1
  dpiMql = window.matchMedia(`(resolution: ${dpr}dppx)`)
  dpiMql.addEventListener('change', onDpiChange)
}

const onDpiChange = () => {
  applyZoom()
  // DPI 变了，需要重新注册监听（因为旧的 dppx 值已不匹配）
  watchDpiChange()
}

onMounted(() => {
  applyZoom()
  watchDpiChange()
  window.addEventListener('resize', applyZoom)
})

onUnmounted(() => {
  if (dpiMql) {
    dpiMql.removeEventListener('change', onDpiChange)
    dpiMql = null
  }
  window.removeEventListener('resize', applyZoom)
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

:root {
  --primary-color: #4f46e5;
  --primary-light: #6366f1;
  --primary-dark: #4338ca;
  --primary-gradient: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
  --bg-light-purple: #eef2ff;
  --bg-cream: #f8fafc;
  --border-light: #e2e8f0;
}

body {
  margin: 0;
  padding: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB',
    'Microsoft YaHei', 'Helvetica Neue', Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background: #ffffff;
}

#app {
  height: 100%;
  overflow: hidden;
}

/* Element Plus 主题色覆盖 */
.el-button--primary {
  background: #4f46e5;
  border: none;
}

.el-button--primary:hover,
.el-button--primary:focus {
  background: #4338ca;
  border: none;
}

.el-button--primary.is-plain {
  background: #eef2ff;
  border: 1px solid #4f46e5;
  color: #4f46e5;
}

.el-button--primary.is-plain:hover,
.el-button--primary.is-plain:focus {
  background: #4f46e5;
  border-color: #4f46e5;
  color: #fff;
}

.el-button--primary.is-link {
  color: #4f46e5;
  background: transparent !important;
  border: none !important;
}

.el-button--primary.is-link:hover {
  color: #4338ca;
  background: transparent !important;
  border: none !important;
}

.el-button--primary.is-link:focus,
.el-button--primary.is-link:active {
  color: #4f46e5;
  background: transparent !important;
  border: none !important;
}

/* Element Plus 全局样式优化 */
.el-button {
  font-weight: 500;
  letter-spacing: 0.5px;
}

.el-card {
  transition: all 0.15s;
  border: 1px solid #e2e8f0;
}

.el-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border-color: #cbd5e1;
}

/* 滚动条美化 */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
  transition: background 0.15s;
}

::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

/* 表格优化 */
.el-table {
  font-size: 14px;
  background-color: #fff;
}

.el-table th {
  font-weight: 600;
  background-color: rgba(248, 250, 252, 0.8) !important;
}

.el-table td,
.el-table th {
  padding: 14px 0;
}

.el-table--striped .el-table__body tr.el-table__row--striped td {
  background-color: #fafbfc;
}

.el-table__body tr:hover > td {
  background-color: rgba(248, 250, 252, 0.8) !important;
}

/* 对话框优化 */
.el-dialog {
  border-radius: 16px;
}

.el-dialog__header {
  border-bottom: 1px solid #e2e8f0;
}

/* 输入框优化 */
.el-input__wrapper {
  transition: all 0.15s;
  background-color: #ffffff !important;
}

.el-input__wrapper:hover {
  box-shadow: 0 0 0 1px #4f46e5 inset;
}

.el-input__wrapper.is-focus {
  box-shadow: 0 0 0 1px #4f46e5 inset !important;
}

/* 标签优化 */
.el-tag {
  border-radius: 6px;
  padding: 4px 12px;
  font-weight: 500;
}

/* 分页优化 */
.el-pagination {
  font-weight: 500;
}

.el-pagination.is-background .el-pager li {
  border-radius: 6px;
  margin: 0 4px;
}

.el-pagination.is-background .el-pager li:not(.is-disabled).is-active {
  background: #4f46e5;
}

/* 消息提示优化 */
.el-message {
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

/* 面包屑优化 */
.el-breadcrumb__item {
  font-weight: 500;
}

.el-breadcrumb__item:last-child .el-breadcrumb__inner {
  color: var(--primary-color);
}

/* 下拉菜单优化 */
.el-dropdown-menu__item:hover {
  background-color: #eef2ff;
  color: #4f46e5;
}

/* 图标颜色统一 */
.el-icon {
  color: inherit;
}

/* MessageBox 弹窗按钮统一为 indigo */
.el-message-box {
  border-radius: 16px;
  overflow: hidden;
}

.el-message-box__header {
  border-bottom: 1px solid #e2e8f0;
  padding: 20px 24px 16px;
}

.el-message-box__title {
  font-size: 18px;
  font-weight: 600;
  color: #0f172a;
}

.el-message-box__content {
  padding: 24px;
}

.el-message-box__btns {
  padding: 16px 24px;
  border-top: 1px solid #e2e8f0;
}

.el-message-box__btns .el-button {
  border-radius: 8px;
  font-weight: 500;
}

.el-message-box__btns .el-button--primary {
  background: #4f46e5 !important;
  border: none !important;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.el-message-box__btns .el-button--primary:hover {
  background: #4338ca !important;
}

/* ==================== */
/* 全局下拉框面板样式 */
/* ==================== */
.el-select-dropdown {
  border-radius: 12px !important;
  border: 1px solid #e2e8f0 !important;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08) !important;
  overflow: hidden !important;
  padding: 0 !important;
  background-color: #ffffff !important;
}

.el-select-dropdown .el-scrollbar {
  overflow: hidden !important;
  background-color: #ffffff !important;
}

.el-select-dropdown .el-scrollbar__view.el-select-dropdown__list {
  padding: 6px 0 !important;
  background-color: #ffffff !important;
}

.el-select-dropdown .el-select-dropdown__item {
  font-size: 14px;
  color: #334155;
  padding: 0 16px !important;
  height: 34px;
  line-height: 34px;
  transition: background-color 0.15s, color 0.15s;
  display: flex !important;
  align-items: center !important;
}

.el-select-dropdown .el-select-dropdown__item:hover,
.el-select-dropdown .el-select-dropdown__item.is-hovering,
.el-select-dropdown .el-select-dropdown__item.hover {
  background-color: #f1f5f9 !important;
}

.el-select-dropdown .el-select-dropdown__item.selected,
.el-select-dropdown .el-select-dropdown__item.is-selected {
  color: #4f46e5 !important;
  font-weight: 600;
  background-color: #eef2ff !important;
}

/* 隐藏 el-select 下拉框的箭头指示器 */
.el-popper.is-light[role="listbox"] .el-popper__arrow,
.el-select-dropdown .el-popper__arrow {
  display: none !important;
}

/* 确保 select popper 容器有白色背景 */
.el-popper.is-light[role="listbox"],
.el-popper.is-light.el-select__popper {
  background-color: #ffffff !important;
  border-radius: 12px !important;
  border: 1px solid #e2e8f0 !important;
  overflow: hidden !important;
}

/* 日期选择器 popper 样式 */
.el-popper.is-pure {
  background-color: #ffffff !important;
  border-radius: 12px !important;
  border: 1px solid #e2e8f0 !important;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08) !important;
}

.el-popper.is-pure .el-popper__arrow::before {
  border-color: #e2e8f0 !important;
}

/* 日期选择器面板美化 */
.el-date-table td.today .el-date-table-cell__text {
  color: #4f46e5 !important;
  font-weight: 600 !important;
}

.el-date-table td.current:not(.disabled) .el-date-table-cell__text {
  background-color: #4f46e5 !important;
  color: #fff !important;
  border-radius: 6px !important;
}

.el-date-table td.available:hover .el-date-table-cell__text {
  color: #4f46e5 !important;
  background-color: #eef2ff !important;
  border-radius: 6px !important;
}

/* 确保 dropdown 内部 scrollbar 撑满整个 popper 宽度 */
.el-select-dropdown .el-scrollbar {
  width: 100% !important;
}

.el-select-dropdown .el-scrollbar__wrap {
  width: 100% !important;
}

.el-select-dropdown .el-select-dropdown__wrap {
  width: 100% !important;
  background-color: #ffffff !important;
}

/* 全局 el-select 聚焦边框颜色 */
.el-select .el-input.is-focus .el-input__wrapper {
  box-shadow: 0 0 0 1px #4f46e5 inset !important;
}

/* TeamSelector 下拉面板 */
.team-selector-dropdown {
  margin-top: 4px !important;
}

/* 用户下拉菜单宽度 */
.user-dropdown-popper {
  min-width: 320px !important;
  width: auto !important;
}

.user-dropdown-popper .el-dropdown-menu {
  min-width: 320px !important;
  width: auto !important;
}

.user-dropdown-popper .el-dropdown-menu__item {
  white-space: nowrap !important;
  max-width: none !important;
}

.user-dropdown-popper .user-detail {
  width: 100% !important;
}

.user-dropdown-popper .user-email {
  white-space: nowrap !important;
  overflow: visible !important;
  text-overflow: unset !important;
  font-size: 12px;
  color: #64748b;
}

.user-dropdown-popper .user-name {
  font-size: 14px;
  font-weight: 600;
  color: #0f172a;
  margin-bottom: 2px;
}

.user-dropdown-popper .user-info-item {
  cursor: default !important;
  background: #f8fafc !important;
  padding: 12px 16px !important;
}

/* 全局表格固定列不透明背景 - 防止 fixed 列内容透出 */
.el-table th.el-table__cell {
  background: #f8fafc !important;
}
.el-table td.el-table__cell {
  background: #fff !important;
}
.el-table__body tr:hover > td.el-table__cell {
  background: #f8fafc !important;
}
</style>
