<template>
  <div class="progress-statistics">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>执行进度统计</span>
          <el-button
            link
            :icon="Refresh"
            @click="handleRefresh"
            :loading="loading"
          >
            刷新
          </el-button>
        </div>
      </template>
      
      <div v-loading="loading">
        <!-- 进度条 -->
        <div class="progress-bar">
          <el-progress
            :percentage="statistics.progress_percentage"
            :color="progressColor"
            :stroke-width="20"
          >
            <span class="progress-text">
              {{ statistics.executed }} / {{ statistics.total }}
            </span>
          </el-progress>
        </div>
        
        <!-- 统计卡片 -->
        <el-row :gutter="20" class="statistics-cards">
          <el-col :span="6">
            <div class="stat-card total">
              <div class="stat-value">{{ statistics.total }}</div>
              <div class="stat-label">总用例数</div>
            </div>
          </el-col>
          
          <el-col :span="6">
            <div class="stat-card executed">
              <div class="stat-value">{{ statistics.executed }}</div>
              <div class="stat-label">已执行</div>
            </div>
          </el-col>
          
          <el-col :span="6">
            <div class="stat-card not-executed">
              <div class="stat-value">{{ statistics.not_executed }}</div>
              <div class="stat-label">未执行</div>
            </div>
          </el-col>
          
          <el-col :span="6">
            <div class="stat-card pass-rate">
              <div class="stat-value">{{ passRate }}%</div>
              <div class="stat-label">通过率</div>
            </div>
          </el-col>
        </el-row>
        
        <!-- 结果统计 -->
        <el-row :gutter="20" class="result-cards">
          <el-col :span="6">
            <div class="result-card passed">
              <el-icon><CircleCheck /></el-icon>
              <div class="result-value">{{ statistics.passed }}</div>
              <div class="result-label">通过</div>
            </div>
          </el-col>
          
          <el-col :span="6">
            <div class="result-card failed">
              <el-icon><CircleClose /></el-icon>
              <div class="result-value">{{ statistics.failed }}</div>
              <div class="result-label">失败</div>
            </div>
          </el-col>
          
          <el-col :span="6">
            <div class="result-card blocked">
              <el-icon><WarningFilled /></el-icon>
              <div class="result-value">{{ statistics.blocked }}</div>
              <div class="result-label">阻塞</div>
            </div>
          </el-col>
          
          <el-col :span="6">
            <div class="result-card skipped">
              <el-icon><Remove /></el-icon>
              <div class="result-value">{{ statistics.skipped }}</div>
              <div class="result-label">跳过</div>
            </div>
          </el-col>
        </el-row>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { Refresh, CircleCheck, CircleClose, WarningFilled, Remove } from '@element-plus/icons-vue'
import { useProgress } from '@/composables/useProgress'

const props = defineProps({
  testplanId: {
    type: Number,
    required: true
  },
  autoRefresh: {
    type: Boolean,
    default: false
  },
  refreshInterval: {
    type: Number,
    default: 30000 // 30秒
  }
})

const emit = defineEmits(['refresh'])

const {
  statistics,
  loading,
  passRate,
  loadStatistics,
  refreshStatistics
} = useProgress(props.testplanId)

const progressColor = computed(() => {
  const percentage = statistics.value.progress_percentage
  if (percentage < 30) return '#F56C6C'
  if (percentage < 70) return '#E6A23C'
  return '#67C23A'
})

onMounted(() => {
  loadStatistics()
  
  // 自动刷新
  if (props.autoRefresh) {
    setInterval(() => {
      refreshStatistics()
    }, props.refreshInterval)
  }
})

const handleRefresh = async () => {
  await loadStatistics()
  emit('refresh')
}
</script>

<style scoped>
.progress-statistics {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.progress-bar {
  margin-bottom: 30px;
}

.progress-text {
  font-size: 14px;
  font-weight: bold;
}

.statistics-cards,
.result-cards {
  margin-top: 20px;
}

.stat-card,
.result-card {
  padding: 20px;
  text-align: center;
  border-radius: 8px;
  background: #f5f7fa;
}

.stat-value,
.result-value {
  font-size: 32px;
  font-weight: bold;
  margin-bottom: 10px;
}

.stat-label,
.result-label {
  font-size: 14px;
  color: #666;
}

.stat-card.total .stat-value {
  color: #409EFF;
}

.stat-card.executed .stat-value {
  color: #67C23A;
}

.stat-card.not-executed .stat-value {
  color: #909399;
}

.stat-card.pass-rate .stat-value {
  color: #E6A23C;
}

.result-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.result-card .el-icon {
  font-size: 32px;
}

.result-card.passed {
  background: #f0f9ff;
  color: #67C23A;
}

.result-card.failed {
  background: #fef0f0;
  color: #F56C6C;
}

.result-card.blocked {
  background: #fdf6ec;
  color: #E6A23C;
}

.result-card.skipped {
  background: #f4f4f5;
  color: #909399;
}
</style>
