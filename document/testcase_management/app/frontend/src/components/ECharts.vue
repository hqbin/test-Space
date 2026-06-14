<template>
  <div ref="chartRef" class="echarts-container" :style="{ height: height }"></div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  option: {
    type: Object,
    required: true
  },
  height: {
    type: String,
    default: '300px'
  },
  autoResize: {
    type: Boolean,
    default: true
  },
  theme: {
    type: String,
    default: null
  }
})

const emit = defineEmits(['chartClick', 'chartReady'])

const chartRef = ref(null)
let chartInstance = null

const initChart = () => {
  if (!chartRef.value) return

  if (chartInstance) {
    chartInstance.dispose()
  }

  chartInstance = echarts.init(chartRef.value, props.theme)

  chartInstance.setOption(props.option)

  chartInstance.on('click', (params) => {
    emit('chartClick', params)
  })

  emit('chartReady', chartInstance)
}

const updateChart = () => {
  if (!chartInstance) return

  chartInstance.setOption(props.option, {
    notMerge: true,
    lazyUpdate: true
  })
}

const resizeChart = () => {
  if (!chartInstance) return

  chartInstance.resize()
}

const handleResize = () => {
  resizeChart()
}

watch(
  () => props.option,
  () => {
    nextTick(() => {
      updateChart()
    })
  },
  { deep: true }
)

watch(
  () => props.height,
  () => {
    nextTick(() => {
      resizeChart()
    })
  }
)

onMounted(() => {
  nextTick(() => {
    initChart()
  })

  if (props.autoResize) {
    window.addEventListener('resize', handleResize)
  }
})

onUnmounted(() => {
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }

  if (props.autoResize) {
    window.removeEventListener('resize', handleResize)
  }
})

defineExpose({
  chartInstance,
  resizeChart,
  updateChart
})
</script>

<style scoped>
.echarts-container {
  width: 100%;
}
</style>
