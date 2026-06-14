<template>
  <div
    class="dashboard-card"
    :class="{
      'is-clickable': clickable,
      'is-loading': loading,
      'is-maximized': isMaximized
    }"
    @click="handleClick"
  >
    <div class="card-header" :style="headerStyle">
      <div class="header-left">
        <el-icon class="card-icon" :style="{ color: color }">
          <component :is="iconComponent" />
        </el-icon>
        <span class="card-title">{{ title }}</span>
        <el-tag v-if="badge" :type="badgeType" size="small" class="card-badge">
          {{ badge }}
        </el-tag>
      </div>
      <div class="header-actions">
        <el-tooltip content="刷新" placement="top" v-if="showRefresh" :show-after="500">
          <el-button
            text
            circle
            size="small"
            @click.stop="handleRefresh"
            :loading="refreshing"
          >
            <el-icon><Refresh /></el-icon>
          </el-button>
        </el-tooltip>
        <el-tooltip :content="isMaximized ? '还原' : '最大化'" placement="top" v-if="showMaximize" :show-after="500">
          <el-button
            text
            circle
            size="small"
            @click.stop="handleMaximize"
          >
            <el-icon>
              <FullScreen v-if="!isMaximized" />
              <Close v-else />
            </el-icon>
          </el-button>
        </el-tooltip>
        <el-tooltip content="最小化" placement="top" v-if="showMinimize && !isMaximized" :show-after="500">
          <el-button
            text
            circle
            size="small"
            @click.stop="handleMinimize"
          >
            <el-icon><Minus /></el-icon>
          </el-button>
        </el-tooltip>
        <slot name="actions"></slot>
      </div>
    </div>

    <div class="card-body" v-loading="loading">
      <slot></slot>
    </div>

    <div v-if="$slots.footer" class="card-footer">
      <slot name="footer"></slot>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import {
  Refresh,
  FullScreen,
  Close,
  Minus,
  Calendar,
  VideoPlay,
  List,
  Warning,
  TrendCharts,
  DataAnalysis,
  WarningFilled,
  DocumentChecked,
  User,
  Folder,
  Monitor,
  CircleCheck,
  Document,
  UserFilled,
  Clock,
  Bell,
  Operation
} from '@element-plus/icons-vue'

const props = defineProps({
  title: {
    type: String,
    required: true
  },
  icon: {
    type: String,
    default: 'Document'
  },
  color: {
    type: String,
    default: '#409EFF'
  },
  loading: {
    type: Boolean,
    default: false
  },
  refreshing: {
    type: Boolean,
    default: false
  },
  clickable: {
    type: Boolean,
    default: false
  },
  isMaximized: {
    type: Boolean,
    default: false
  },
  isMinimized: {
    type: Boolean,
    default: false
  },
  showRefresh: {
    type: Boolean,
    default: true
  },
  showMaximize: {
    type: Boolean,
    default: true
  },
  showMinimize: {
    type: Boolean,
    default: true
  },
  badge: {
    type: [String, Number],
    default: null
  },
  badgeType: {
    type: String,
    default: 'primary'
  },
  headerBg: {
    type: String,
    default: null
  }
})

const emit = defineEmits(['click', 'refresh', 'maximize', 'minimize'])

const iconMap = {
  Calendar,
  VideoPlay,
  List,
  Warning,
  TrendCharts,
  DataAnalysis,
  WarningFilled,
  DocumentChecked,
  User,
  Folder,
  Monitor,
  CircleCheck,
  Document,
  UserFilled,
  Clock,
  Bell,
  Operation
}

const iconComponent = computed(() => iconMap[props.icon] || Document)

const headerStyle = computed(() => {
  if (props.headerBg) {
    return { background: props.headerBg }
  }
  return {
    background: `linear-gradient(135deg, ${props.color}15 0%, ${props.color}05 100%)`
  }
})

const handleClick = () => {
  if (props.clickable) {
    emit('click')
  }
}

const handleRefresh = () => {
  emit('refresh')
}

const handleMaximize = () => {
  emit('maximize')
}

const handleMinimize = () => {
  emit('minimize')
}
</script>

<style scoped>
.dashboard-card {
  display: flex;
  flex-direction: column;
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
  height: 100%;
  transition: all 0.3s ease;
}

.dashboard-card.is-clickable {
  cursor: pointer;
}

.dashboard-card.is-clickable:hover {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

.dashboard-card.is-loading {
  pointer-events: none;
}

.dashboard-card.is-maximized {
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #EBEEF5;
  min-height: 56px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.card-icon {
  font-size: 20px;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}

.card-badge {
  margin-left: 4px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

.header-actions .el-button {
  color: #909399;
}

.header-actions .el-button:hover {
  color: #409EFF;
  background: rgba(64, 158, 255, 0.1);
}

.card-body {
  flex: 1;
  padding: 20px;
  overflow: auto;
}

.card-footer {
  padding: 12px 20px;
  border-top: 1px solid #EBEEF5;
  background: #FAFAFA;
}
</style>
