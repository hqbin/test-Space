/**
 * 分页切换后滚动回顶部
 * 用于列表/表格页：点击下一页、上一页或修改每页条数后，将页面和表格滚动条重置到顶部
 */
import { nextTick } from 'vue'

/**
 * @param {import('vue').Ref} [tableRef] - el-table 的 ref，用于将表格体滚动条置顶
 * @param {import('vue').Ref<HTMLElement>|string} [scrollContainerRef] - 主滚动容器 ref 或选择器（如 .main-content），用于将容器滚动条置顶
 * @returns {{ scrollToTop: () => void }}
 */
export function useScrollToTop(tableRef = null, scrollContainerRef = null) {
  const scrollToTop = () => {
    // 滚动窗口到顶部
    window.scrollTo({ top: 0, left: 0, behavior: 'auto' })
    
    nextTick(() => {
      // 滚动自定义容器到顶部
      const container =
        typeof scrollContainerRef === 'string'
          ? document.querySelector(scrollContainerRef)
          : scrollContainerRef?.value
      if (container && typeof container.scrollTo === 'function') {
        container.scrollTo({ top: 0, left: 0, behavior: 'auto' })
      }
      
      // 滚动表格内容到顶部
      if (tableRef?.value) {
        // 尝试多种方式获取表格的滚动容器
        const tableEl = tableRef.value.$el || tableRef.value
        
        if (tableEl) {
          // 方法1: 查找 el-table__body-wrapper
          const bodyWrapper = tableEl.querySelector('.el-table__body-wrapper')
          if (bodyWrapper) {
            bodyWrapper.scrollTop = 0
            bodyWrapper.scrollLeft = 0
          }
          
          // 方法2: 查找 el-scrollbar__wrap（Element Plus 新版本）
          const scrollbarWrap = tableEl.querySelector('.el-scrollbar__wrap')
          if (scrollbarWrap) {
            scrollbarWrap.scrollTop = 0
            scrollbarWrap.scrollLeft = 0
          }
          
          // 方法3: 直接设置表格元素的scrollTop
          if (tableEl.scrollTop !== undefined) {
            tableEl.scrollTop = 0
          }
        }
      }
    })
  }
  return { scrollToTop }
}
