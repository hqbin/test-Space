import { ref, watch } from 'vue'

/**
 * 分页记忆功能
 * @param {string} storageKey - localStorage的key，建议使用页面名称，如 'userManagement'
 * @param {number} defaultSize - 默认每页显示数量
 * @returns {Object} { page, size, total }
 */
export function usePagination(storageKey, defaultSize = 10) {
  // 从localStorage读取上次的分页大小
  const savedSize = localStorage.getItem(`pagination_${storageKey}_size`)
  const initialSize = savedSize ? parseInt(savedSize) : defaultSize

  const page = ref(1)
  const size = ref(initialSize)
  const total = ref(0)

  // 监听size变化，保存到localStorage
  watch(size, (newSize) => {
    localStorage.setItem(`pagination_${storageKey}_size`, newSize.toString())
  })

  return {
    page,
    size,
    total
  }
}
