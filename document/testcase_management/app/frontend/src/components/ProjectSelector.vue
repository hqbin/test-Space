<template>
  <div ref="selectorRef" class="project-selector-wrapper">
    <div ref="triggerRef" class="project-selector-trigger" @click.stop="togglePopover">
      <div v-if="selectedIds.length > 0" class="selected-tags">
        <span 
          v-for="id in selectedIds" 
          :key="id" 
          class="selected-tag"
        >
          <span class="tag-text">{{ getProjectName(id) }}</span>
          <el-icon class="tag-close" @click.stop="handleRemoveProject(id)"><Close /></el-icon>
        </span>
      </div>
      <span v-else class="trigger-label">全部用例库</span>
      <el-icon class="trigger-icon" :class="{ 'is-reverse': popoverVisible }">
        <ArrowDown />
      </el-icon>
    </div>
    
    <!-- 使用 Teleport 将下拉框渲染到 body，避免被父容器裁剪 -->
    <Teleport to="body">
      <Transition name="dropdown">
        <div 
          v-show="popoverVisible" 
          ref="dropdownRef"
          class="project-selector-dropdown"
          :style="dropdownStyle"
          @click.stop
        >
          <!-- 全部选项 -->
          <div 
            class="project-option all-option"
            :class="{ active: isAllSelected }"
            @click="handleSelectAll"
          >
            <el-icon v-if="isAllSelected" class="check-icon"><Check /></el-icon>
            <span>全部用例库</span>
            <span class="count-badge">{{ projectList.length }}</span>
          </div>
          
          <div class="dropdown-divider"></div>
          
          <!-- 用例库列表 -->
          <div class="project-list">
            <div 
              v-for="project in projectList"
              :key="project.id"
              class="project-option"
              :class="{ active: isProjectSelected(project.id) }"
              @click="handleToggleProject(project.id)"
            >
              <el-icon v-if="isProjectSelected(project.id)" class="check-icon"><Check /></el-icon>
              <span class="project-name">{{ project.name }}</span>
            </div>
            <div v-if="projectList.length === 0" class="empty-tip">
              暂无用例库
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, watch, onBeforeUnmount, nextTick } from 'vue'
import { ArrowDown, Check, Close } from '@element-plus/icons-vue'

const props = defineProps({
  projectList: {
    type: Array,
    default: () => []
  },
  modelValue: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

const selectorRef = ref(null)
const triggerRef = ref(null)
const dropdownRef = ref(null)
const popoverVisible = ref(false)

// 下拉框位置样式
const dropdownStyle = ref({
  position: 'fixed',
  top: '0px',
  left: '0px',
  width: '200px',
  zIndex: 99999
})

// 更新下拉框位置
const updateDropdownPosition = () => {
  if (!triggerRef.value) return
  
  const rect = triggerRef.value.getBoundingClientRect()
  const dropdownWidth = Math.max(rect.width, 200)
  
  dropdownStyle.value = {
    position: 'fixed',
    top: `${rect.bottom + 4}px`,
    left: `${rect.left}px`,
    width: `${dropdownWidth}px`,
    zIndex: 99999
  }
}

// 切换弹出框显示状态
const togglePopover = async () => {
  popoverVisible.value = !popoverVisible.value
  if (popoverVisible.value) {
    await nextTick()
    updateDropdownPosition()
  }
}

// 内部选中的用例库ID列表
const selectedIds = ref([])

// 是否选中全部（只有 selectedIds 为空时才视为"全部"）
const isAllSelected = computed(() => {
  return selectedIds.value.length === 0
})

// 显示标签
const displayLabel = computed(() => {
  if (isAllSelected.value) {
    return '全部用例库'
  }
  if (selectedIds.value.length === 1) {
    const project = props.projectList.find(p => p.id === selectedIds.value[0])
    return project ? project.name : '选择用例库'
  }
  return `已选 ${selectedIds.value.length} 个用例库`
})

// 检查用例库是否被选中
const isProjectSelected = (projectId) => {
  return selectedIds.value.includes(projectId)
}

// 选择全部
const handleSelectAll = () => {
  selectedIds.value = []
  emitChange()
  popoverVisible.value = false
}

// 切换用例库选中状态
const handleToggleProject = (projectId) => {
  const index = selectedIds.value.indexOf(projectId)
  if (index > -1) {
    selectedIds.value.splice(index, 1)
  } else {
    selectedIds.value.push(projectId)
  }
  emitChange()
}

// 获取用例库名称
const getProjectName = (projectId) => {
  const project = props.projectList.find(p => p.id === projectId)
  return project ? project.name : ''
}

// 移除选中的用例库（标签×按钮）
const handleRemoveProject = (projectId) => {
  const index = selectedIds.value.indexOf(projectId)
  if (index > -1) {
    selectedIds.value.splice(index, 1)
    emitChange()
  }
}

// 发送变更事件
const emitChange = () => {
  emit('update:modelValue', [...selectedIds.value])
  emit('change', [...selectedIds.value])
}

// 监听外部值变化
watch(() => props.modelValue, (newVal) => {
  if (newVal && newVal.length > 0) {
    selectedIds.value = [...newVal]
  } else {
    selectedIds.value = []
  }
}, { immediate: true })

// 注意：不再自动选择第一个用例库，默认保持"全部用例库"状态
// 如果需要自动选择，应该由父组件控制

// 点击外部关闭
const handleClickOutside = (e) => {
  if (!selectorRef.value) return
  if (selectorRef.value.contains(e.target)) return
  if (dropdownRef.value && dropdownRef.value.contains(e.target)) return
  popoverVisible.value = false
}

// 窗口滚动或调整大小时更新位置
const handleScrollOrResize = () => {
  if (popoverVisible.value) {
    updateDropdownPosition()
  }
}

// 监听 popoverVisible 变化
watch(popoverVisible, (visible) => {
  if (visible) {
    setTimeout(() => {
      document.addEventListener('click', handleClickOutside)
      window.addEventListener('scroll', handleScrollOrResize, true)
      window.addEventListener('resize', handleScrollOrResize)
    }, 0)
  } else {
    document.removeEventListener('click', handleClickOutside)
    window.removeEventListener('scroll', handleScrollOrResize, true)
    window.removeEventListener('resize', handleScrollOrResize)
  }
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside)
  window.removeEventListener('scroll', handleScrollOrResize, true)
  window.removeEventListener('resize', handleScrollOrResize)
})

defineExpose({
  close: () => { popoverVisible.value = false }
})
</script>

<style scoped>
.project-selector-wrapper {
  position: relative;
  width: 100%;
}

.project-selector-trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: #fff;
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  min-height: 34px;
}

.project-selector-trigger:hover {
  border-color: #8b9aee;
}

.trigger-label {
  font-size: 13px;
  color: #303133;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.selected-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  flex: 1;
  overflow: hidden;
}

.selected-tag {
  display: inline-flex;
  align-items: center;
  background: rgba(139, 154, 238, 0.12);
  color: #6366f1;
  border-radius: 4px;
  padding: 2px 6px;
  font-size: 12px;
  max-width: 120px;
  line-height: 1.4;
}

.selected-tag .tag-text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.selected-tag .tag-close {
  margin-left: 4px;
  font-size: 12px;
  cursor: pointer;
  color: #8b9aee;
  flex-shrink: 0;
  border-radius: 50%;
  transition: all 0.15s;
}

.selected-tag .tag-close:hover {
  color: #fff;
  background: #8b9aee;
}

.trigger-icon {
  color: #909399;
  transition: transform 0.3s;
  margin-left: 8px;
  flex-shrink: 0;
}

.trigger-icon.is-reverse {
  transform: rotate(180deg);
}
</style>

<style>
/* 全局样式，因为下拉框被 Teleport 到 body */
.project-selector-dropdown {
  max-height: 320px;
  overflow-y: auto;
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.12);
  padding: 8px;
}

.project-selector-dropdown .dropdown-divider {
  height: 1px;
  background: #e4e7ed;
  margin: 8px 0;
}

.project-selector-dropdown .project-option {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.2s;
  margin: 2px 0;
}

.project-selector-dropdown .project-option:hover {
  background: rgba(139, 154, 238, 0.08);
}

.project-selector-dropdown .project-option.active {
  background: rgba(139, 154, 238, 0.12);
  color: #8b9aee;
}

.project-selector-dropdown .project-option .check-icon {
  margin-right: 8px;
  color: #8b9aee;
  font-size: 14px;
}

.project-selector-dropdown .project-option .project-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13px;
}

.project-selector-dropdown .all-option {
  font-weight: 500;
}

.project-selector-dropdown .count-badge {
  background: rgba(139, 154, 238, 0.15);
  color: #8b9aee;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 12px;
  margin-left: auto;
}

.project-selector-dropdown .project-list {
  max-height: 240px;
  overflow-y: auto;
}

.project-selector-dropdown .empty-tip {
  text-align: center;
  color: #909399;
  padding: 20px;
  font-size: 13px;
}

/* 下拉动画 */
.dropdown-enter-active,
.dropdown-leave-active {
  transition: opacity 0.2s, transform 0.2s;
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
