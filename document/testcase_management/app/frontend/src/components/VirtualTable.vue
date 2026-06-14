<template>
  <div class="virtual-table-container" ref="containerRef">
    <el-table
      ref="tableRef"
      :data="virtualItems"
      style="width: 100%"
      :height="tableHeight"
      :header-cell-style="headerCellStyle"
      v-loading="loading"
      element-loading-text="加载中..."
      @sort-change="handleSortChange"
      @selection-change="handleSelectionChange"
      @row-click="handleRowClick"
      row-key="id"
      :row-class-name="getRowClassName"
    >
      <slot></slot>
    </el-table>
    <div
      class="virtual-scroll-container"
      ref="scrollContainerRef"
      @scroll="handleScroll"
      :style="{ height: tableHeight }"
    >
      <div
        class="virtual-scroll-content"
        ref="scrollContentRef"
        :style="{ height: totalHeight + 'px' }"
      >
        <div
          class="virtual-scroll-viewport"
          ref="viewportRef"
          :style="{ transform: `translateY(${offsetTop}px)`, height: viewportHeight + 'px' }"
        >
          <el-table
            ref="virtualTableRef"
            :data="virtualItems"
            style="width: 100%"
            :show-header="false"
            :header-cell-style="headerCellStyle"
            row-key="id"
            :row-class-name="getRowClassName"
          >
            <slot></slot>
          </el-table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useVirtualizer } from '@tanstack/vue-virtual'

// Props
const props = defineProps({
  data: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  },
  height: {
    type: [String, Number],
    default: 600
  },
  rowHeight: {
    type: Number,
    default: 48
  },
  overscan: {
    type: Number,
    default: 5
  }
})

// Emits
const emit = defineEmits([
  'sort-change',
  'selection-change',
  'row-click'
])

// Refs
const containerRef = ref(null)
const scrollContainerRef = ref(null)
const scrollContentRef = ref(null)
const viewportRef = ref(null)
const tableRef = ref(null)
const virtualTableRef = ref(null)

// Computed
const tableHeight = computed(() => {
  return typeof props.height === 'number' ? `${props.height}px` : props.height
})

const totalHeight = computed(() => {
  return props.data.length * props.rowHeight
})

const viewportHeight = computed(() => {
  return props.height
})

// State
const offsetTop = ref(0)
const virtualItems = ref([])
const virtualizer = ref(null)

// Handlers
const handleSortChange = (params) => {
  emit('sort-change', params)
}

const handleSelectionChange = (selection) => {
  emit('selection-change', selection)
}

const handleRowClick = (row) => {
  emit('row-click', row)
}

const getRowClassName = (row) => {
  return ''
}

const handleScroll = (event) => {
  if (virtualizer.value) {
    virtualizer.value.scrollToOffset(event.target.scrollTop)
  }
}

const headerCellStyle = {
  background: 'rgba(139, 154, 238, 0.08)',
  color: '#606266',
  fontWeight: '600'
}

// Lifecycle
onMounted(() => {
  // 初始化虚拟滚动
  if (scrollContainerRef.value && viewportRef.value && scrollContentRef.value) {
    virtualizer.value = useVirtualizer({
      count: props.data.length,
      getScrollElement: () => scrollContainerRef.value,
      estimateSize: () => props.rowHeight,
      overscan: props.overscan,
      onChange: (instance) => {
        const startIndex = instance.getVirtualItems()[0].index
        const endIndex = instance.getVirtualItems()[instance.getVirtualItems().length - 1].index
        virtualItems.value = props.data.slice(startIndex, endIndex + 1)
        offsetTop.value = instance.getVirtualItems()[0].start
      }
    })
  }
})

onUnmounted(() => {
  if (virtualizer.value) {
    virtualizer.value.destroy()
  }
})

// Watch for data changes
watch(() => props.data.length, (newLength) => {
  if (virtualizer.value) {
    virtualizer.value.setCount(newLength)
  }
})
</script>

<style scoped>
.virtual-table-container {
  position: relative;
  width: 100%;
}

.virtual-scroll-container {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  overflow-y: auto;
  pointer-events: none;
  z-index: 1;
}

.virtual-scroll-content {
  position: relative;
  width: 100%;
}

.virtual-scroll-viewport {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  overflow: hidden;
}

.el-table {
  border: none;
}

.el-table__header-wrapper {
  border-bottom: 1px solid #ebeef5;
}

.el-table__body-wrapper {
  overflow: hidden;
}
</style>