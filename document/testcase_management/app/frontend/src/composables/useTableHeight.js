/**
 * 表格高度自适应 - 根据容器可用空间自动撑满
 * 用于列表页、管理页等带表格的页面，统一体验
 */
import { ref, nextTick, onMounted, onBeforeUnmount } from 'vue'

export const TABLE_HEADER_STYLE = {
  background: 'rgba(139, 154, 238, 0.08)',
  color: '#606266',
  fontWeight: '600'
}

/**
 * @param {import('vue').Ref<HTMLElement | null>} [containerRef] - 表格容器 ref，不传则需在模板里用 tableContainerRef
 * @returns {{ tableContainerRef: Ref, tableHeight: Ref<number>, updateTableHeight: () => void, bindTableHeight: () => void }}
 */
export function useTableHeight(containerRef = null) {
  const tableContainerRef = containerRef || ref(null)
  const tableHeight = ref(400)
  let resizeObserver = null
  let rafId = null

  const updateTableHeight = () => {
    if (rafId) cancelAnimationFrame(rafId)
    rafId = requestAnimationFrame(() => {
      const el = tableContainerRef.value
      if (el && el.clientHeight > 0) {
        tableHeight.value = el.clientHeight
      }
      rafId = null
    })
  }

  const bindTableHeight = () => {
    nextTick(() => {
      updateTableHeight()
      const el = tableContainerRef.value
      if (el && typeof ResizeObserver !== 'undefined') {
        resizeObserver = new ResizeObserver(updateTableHeight)
        resizeObserver.observe(el)
      }
    })
  }

  const unbindTableHeight = () => {
    if (resizeObserver) {
      resizeObserver.disconnect()
      resizeObserver = null
    }
  }

  return {
    tableContainerRef,
    tableHeight,
    updateTableHeight,
    bindTableHeight,
    unbindTableHeight
  }
}
