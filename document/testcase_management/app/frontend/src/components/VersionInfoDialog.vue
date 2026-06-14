<template>
  <el-dialog title="版本信息" v-model="visible" width="660px" class="version-info-dialog" :close-on-click-modal="true" @close="$emit('update:modelValue', false)" destroy-on-close>
    <div class="version-info-content" v-loading="loading">
      <div v-if="versions.length === 0 && !loading" class="empty-state">
        <el-empty description="暂无版本信息" :image-size="80" />
      </div>
      <div v-for="(version, idx) in versions" :key="version.id" class="version-block">
        <div class="version-header">
          <div class="version-badge-pill">{{ version.version_number }}</div>
          <div class="version-meta">
            <span class="version-title">{{ version.title }}</span>
            <span class="version-date">{{ formatDate(version.published_at) }}</span>
          </div>
        </div>
        <div class="version-items">
          <div v-for="item in version.items" :key="item.id" class="version-item">
            <span class="item-icon">{{ itemIcons[item.item_type] || '●' }}</span>
            <span class="item-type-badge" :class="'type-' + item.item_type">{{ itemLabels[item.item_type] || item.item_type }}</span>
            <span class="item-content">{{ item.content }}</span>
          </div>
        </div>
        <el-divider v-if="idx < versions.length - 1" />
      </div>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { getPublishedVersions } from '@/api/versionInfo'

const props = defineProps({
  modelValue: { type: Boolean, default: false }
})
const emit = defineEmits(['update:modelValue'])

const visible = ref(props.modelValue)
const loading = ref(false)
const versions = ref([])

const itemLabels = { new: '新增', fix: '修复', improve: '优化', delete: '删除', other: '其他' }
const itemIcons = { new: '✅', fix: '🔧', improve: '⚡', delete: '❌', other: '📌' }

const formatDate = (t) => {
  if (!t) return ''
  return t.replace('T', ' ').replace(/\.\d+$/, '').substring(0, 19)
}

watch(() => props.modelValue, (val) => {
  visible.value = val
  if (val) loadVersions()
})

watch(visible, (val) => {
  if (!val) emit('update:modelValue', false)
})

const loadVersions = async () => {
  loading.value = true
  try {
    const res = await getPublishedVersions({ page: 1, size: 100 })
    versions.value = res.data?.records || []
  } catch {
    versions.value = []
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.version-info-content {
  max-height: 60vh;
  overflow-y: auto;
  padding: 0 4px;
}
.version-block {
  margin-bottom: 4px;
}
.version-header {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 12px;
}
.version-badge-pill {
  background: var(--el-color-primary);
  color: #fff;
  padding: 5px 14px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
  box-shadow: 0 2px 8px rgba(79, 70, 229, 0.3);
}
.version-meta {
  display: flex;
  flex-direction: column;
}
.version-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}
.version-date {
  font-size: 12px;
  color: #909399;
  margin-top: 3px;
  font-variant-numeric: tabular-nums;
}
.version-items {
  padding-left: 10px;
}
.version-item {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 8px;
  line-height: 1.6;
}
.item-icon {
  font-size: 13px;
  flex-shrink: 0;
}
.item-type-badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 6px;
  flex-shrink: 0;
  font-weight: 600;
}
.type-new {
  background: #e1f3d8;
  color: #67c23a;
}
.type-fix {
  background: #fdf6ec;
  color: #e6a23c;
}
.type-improve {
  background: #ecf5ff;
  color: #409eff;
}
.type-delete {
  background: #fef0f0;
  color: #f56c6c;
}
.type-other {
  background: #f4f4f5;
  color: #909399;
}
.item-content {
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
}
.empty-state {
  padding: 24px 0;
}

:deep(.el-dialog) {
  border-radius: 16px;
  overflow: hidden;
}
:deep(.el-dialog__header) {
  background: linear-gradient(135deg, #f5f7fa 0%, var(--el-color-primary-light-9) 100%);
  padding: 16px 24px;
  margin: 0;
  border-bottom: 1px solid #e4e7ed;
}
:deep(.el-dialog__title) {
  font-weight: 600;
}
:deep(.el-dialog__body) {
  padding: 24px;
}
:deep(.el-divider) {
  margin: 16px 0;
}
</style>
