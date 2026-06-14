<template>
  <div class="dashboard-grid" :class="{ 'is-maximized': !!maximizedCard }">
    <transition-group
      name="card-move"
      tag="div"
      class="grid-container"
      :style="gridStyle"
    >
      <div
        v-for="card in visibleCards"
        :key="card.type"
        class="grid-item"
        :class="{
          'is-dragging': draggedCard === card.type,
          'is-maximized': card.isMaximized,
          'is-minimized': minimizedCards.has(card.type)
        }"
        :style="getCardStyle(card)"
        draggable="true"
        @dragstart="handleDragStart($event, card.type)"
        @dragend="handleDragEnd"
        @dragover="handleDragOver($event, card.type)"
        @drop="handleDrop($event, card.type)"
      >
        <slot
          :name="card.type"
          :card="card"
          :data="getCardData(card.type)"
          :isMaximized="card.isMaximized"
          :isMinimized="minimizedCards.has(card.type)"
          :onMaximize="() => toggleMaximize(card.type)"
          :onMinimize="() => toggleMinimize(card.type)"
          :onRefresh="() => onRefresh(card.type)"
        >
          <div class="card-placeholder">
            {{ card.title }}
          </div>
        </slot>
      </div>
    </transition-group>

    <div v-if="minimizedCards.size > 0" class="minimized-bar">
      <div class="minimized-label">
        <el-icon><Minus /></el-icon>
        <span>已最小化的卡片</span>
      </div>
      <div class="minimized-cards">
        <el-tag
          v-for="cardType in Array.from(minimizedCards)"
          :key="cardType"
          closable
          @close="toggleMinimize(cardType)"
          @click="toggleMinimize(cardType)"
          class="minimized-tag"
        >
          <el-icon class="tag-icon">
            <component :is="getCardIcon(cardType)" />
          </el-icon>
          {{ $t(CARD_META[cardType]?.title || cardType) }}
        </el-tag>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { Minus, Calendar, VideoPlay, List, Warning, TrendCharts, DataAnalysis, WarningFilled, DocumentChecked, User, Folder, Monitor, CircleCheck, Document, UserFilled, Clock, Bell, Operation } from '@element-plus/icons-vue'
import { CARD_META } from '@/composables/useDashboard'

const props = defineProps({
  visibleCards: {
    type: Array,
    required: true
  },
  minimizedCards: {
    type: Set,
    required: true
  },
  maximizedCard: {
    type: String,
    default: null
  },
  columns: {
    type: Number,
    default: 3
  },
  gap: {
    type: String,
    default: '20px'
  }
})

const emit = defineEmits([
  'update:order',
  'toggle:minimize',
  'toggle:maximize',
  'refresh'
])

const draggedCard = ref(null)
const dropTarget = ref(null)

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

const getCardIcon = (cardType) => {
  const meta = CARD_META[cardType]
  return meta ? iconMap[meta.icon] : Document
}

const gridStyle = computed(() => ({
  display: 'grid',
  gridTemplateColumns: props.maximizedCard ? '1fr' : `repeat(${props.columns}, 1fr)`,
  gap: props.gap,
  transition: 'all 0.3s ease'
}))

const getCardStyle = (card) => {
  if (card.isMaximized) {
    return {
      gridColumn: '1 / -1',
      minHeight: '400px'
    }
  }

  const meta = CARD_META[card.type]
  if (meta?.minWidth && meta.minWidth > 1) {
    return {
      gridColumn: `span ${Math.min(meta.minWidth, props.columns)}`
    }
  }

  return {}
}

const getCardData = (cardType) => {
  return props.dashboardData?.[cardType] || {}
}

const handleDragStart = (event, cardType) => {
  if (props.maximizedCard) {
    event.preventDefault()
    return
  }

  draggedCard.value = cardType
  event.dataTransfer.effectAllowed = 'move'
  event.dataTransfer.setData('text/plain', cardType)

  event.target.style.opacity = '0.5'
}

const handleDragEnd = (event) => {
  draggedCard.value = null
  dropTarget.value = null
  event.target.style.opacity = '1'
}

const handleDragOver = (event, cardType) => {
  if (!draggedCard.value || draggedCard.value === cardType) return

  event.preventDefault()
  event.dataTransfer.dropEffect = 'move'

  dropTarget.value = cardType
}

const handleDrop = (event, targetCardType) => {
  event.preventDefault()

  if (!draggedCard.value || draggedCard.value === targetCardType) return

  const currentOrder = props.visibleCards.map(c => c.type)
  const draggedIndex = currentOrder.indexOf(draggedCard.value)
  const targetIndex = currentOrder.indexOf(targetCardType)

  if (draggedIndex === -1 || targetIndex === -1) return

  const newOrder = [...currentOrder]
  newOrder.splice(draggedIndex, 1)
  newOrder.splice(targetIndex, 0, draggedCard.value)

  emit('update:order', newOrder)

  draggedCard.value = null
  dropTarget.value = null
}

const toggleMinimize = (cardType) => {
  emit('toggle:minimize', cardType)
}

const toggleMaximize = (cardType) => {
  emit('toggle:maximize', cardType)
}

const onRefresh = (cardType) => {
  emit('refresh', cardType)
}
</script>

<style scoped>
.dashboard-grid {
  position: relative;
  width: 100%;
}

.grid-container {
  width: 100%;
  min-height: 200px;
}

.grid-item {
  position: relative;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  cursor: grab;
  overflow: hidden;
}

.grid-item:hover {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.12);
  transform: translateY(-2px);
}

.grid-item.is-dragging {
  opacity: 0.5;
  cursor: grabbing;
}

.grid-item.is-maximized {
  position: fixed;
  top: 80px;
  left: 20px;
  right: 20px;
  bottom: 20px;
  z-index: 1000;
  margin: 0;
  cursor: default;
}

.grid-item.is-minimized {
  display: none;
}

.card-placeholder {
  padding: 40px;
  text-align: center;
  color: #909399;
  font-size: 14px;
}

.minimized-bar {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  padding: 12px 20px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  display: flex;
  align-items: center;
  gap: 16px;
  z-index: 100;
  max-width: 80vw;
  overflow-x: auto;
}

.minimized-label {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #606266;
  font-size: 13px;
  white-space: nowrap;
  border-right: 1px solid #EBEEF5;
  padding-right: 16px;
}

.minimized-cards {
  display: flex;
  gap: 8px;
  flex-wrap: nowrap;
}

.minimized-tag {
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
}

.tag-icon {
  font-size: 14px;
}

.card-move-enter-active,
.card-move-leave-active {
  transition: all 0.3s ease;
}

.card-move-enter-from,
.card-move-leave-to {
  opacity: 0;
  transform: scale(0.9);
}

@media (max-width: 1400px) {
  .grid-container {
    grid-template-columns: repeat(2, 1fr) !important;
  }
}

@media (max-width: 768px) {
  .grid-container {
    grid-template-columns: 1fr !important;
  }

  .minimized-bar {
    left: 10px;
    right: 10px;
    transform: none;
    max-width: none;
  }
}
</style>
