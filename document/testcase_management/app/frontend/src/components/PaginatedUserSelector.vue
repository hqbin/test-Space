<template>
  <div class="paginated-user-selector">
    <div class="selector-toolbar">
      <el-input v-model="searchKeyword" placeholder="搜索用户名 / 姓名 / 邮箱" clearable size="default" class="search-input" @keyup.enter="handleSearch" @clear="handleSearch">
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>
      <div class="toolbar-right">
        <el-tag type="primary" effect="plain" round>已选 {{ selectedIds.size }} 人</el-tag>
        <el-button size="small" text :disabled="!selectedIds.size" @click="clearAll">清空</el-button>
      </div>
    </div>

    <div class="select-all-bar">
      <el-checkbox
        :model-value="isAllCurrentPageSelected"
        :indeterminate="isCurrentPageIndeterminate"
        @change="toggleSelectAllCurrentPage"
      >
        全选当前页 <span class="page-count">({{ currentUsers.length }} 人)</span>
      </el-checkbox>
    </div>

    <div class="user-list" v-loading="loading">
      <el-checkbox
        v-for="user in currentUsers"
        :key="user.id"
        :model-value="selectedIds.has(user.id)"
        @change="toggleUser(user.id, $event)"
        class="user-item"
      >
        <span class="user-name">{{ user.username }}</span>
        <span v-if="user.full_name" class="user-fullname">{{ user.full_name }}</span>
        <span v-if="user.email" class="user-email">{{ user.email }}</span>
      </el-checkbox>
      <el-empty v-if="!currentUsers.length && !loading" description="暂无可选用户" :image-size="40" />
    </div>

    <div class="pagination-bar">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="displayTotal"
        :page-sizes="[20, 50, 100]"
        layout="total, sizes, prev, pager, next"
        small
        background
        @size-change="handlePageSizeChange"
        @current-change="handlePageChange"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { getUsers } from '@/api/user'

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  excludeUserIds: { type: Array, default: () => [] }
})
const emit = defineEmits(['update:modelValue'])

const loading = ref(false)
const searchKeyword = ref('')
const allUsers = ref([])
const currentPage = ref(1)
const pageSize = ref(20)

const selectedIds = ref(new Set())

watch(() => props.modelValue, (val) => {
  selectedIds.value = new Set(val || [])
}, { immediate: true })

const excludeSet = computed(() => new Set(props.excludeUserIds))

const filteredUsers = computed(() => {
  if (excludeSet.value.size === 0) return allUsers.value
  return allUsers.value.filter(u => !excludeSet.value.has(u.id))
})

const displayTotal = computed(() => filteredUsers.value.length)

const currentUsers = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredUsers.value.slice(start, start + pageSize.value)
})

const isAllCurrentPageSelected = computed(() => {
  if (!currentUsers.value.length) return false
  return currentUsers.value.every(u => selectedIds.value.has(u.id))
})

const isCurrentPageIndeterminate = computed(() => {
  if (!currentUsers.value.length) return false
  const selected = currentUsers.value.filter(u => selectedIds.value.has(u.id))
  return selected.length > 0 && selected.length < currentUsers.value.length
})

const emitChange = () => {
  emit('update:modelValue', Array.from(selectedIds.value))
}

const toggleUser = (userId, checked) => {
  if (checked) selectedIds.value.add(userId)
  else selectedIds.value.delete(userId)
  emitChange()
}

const toggleSelectAllCurrentPage = (checked) => {
  if (checked) {
    currentUsers.value.forEach(u => selectedIds.value.add(u.id))
  } else {
    currentUsers.value.forEach(u => selectedIds.value.delete(u.id))
  }
  emitChange()
}

const clearAll = () => {
  selectedIds.value.clear()
  emitChange()
}

const handleSearch = () => {
  currentPage.value = 1
  loadAll()
}

const handlePageSizeChange = () => {
  currentPage.value = 1
}

const handlePageChange = () => {
  // frontend pagination, no need to reload
}

const loadAll = async () => {
  loading.value = true
  try {
    const res = await getUsers({ page: 1, size: 9999, search: searchKeyword.value || undefined, status: 1 })
    allUsers.value = res.data?.records || []
  } catch {
    allUsers.value = []
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadAll()
})

defineExpose({ loadUsers: loadAll })
</script>

<style scoped>
.paginated-user-selector {
  border: 1px solid rgba(79, 70, 229, 0.15);
  border-radius: 10px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.8);
}
.selector-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  background: rgba(245, 247, 250, 0.8);
  border-bottom: 1px solid #ebeef5;
  gap: 12px;
}
.search-input {
  max-width: 260px;
}
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
  white-space: nowrap;
}
.select-all-bar {
  padding: 8px 14px;
  background: rgba(245, 247, 250, 0.5);
  border-bottom: 1px solid #ebeef5;
}
.page-count {
  color: #909399;
  font-size: 12px;
}
.user-list {
  max-height: 280px;
  overflow-y: auto;
  padding: 4px 0;
}
.user-item {
  display: flex;
  align-items: center;
  padding: 6px 14px;
  width: 100%;
  box-sizing: border-box;
  transition: background 0.15s;
}
.user-item:hover {
  background: rgba(79, 70, 229, 0.04);
}
.user-name {
  font-size: 13px;
  color: #303133;
}
.user-fullname {
  font-size: 12px;
  color: #909399;
  margin-left: 8px;
}
.user-email {
  font-size: 12px;
  color: #909399;
  margin-left: 8px;
}
.pagination-bar {
  display: flex;
  justify-content: center;
  padding: 10px 14px;
  border-top: 1px solid #ebeef5;
  background: rgba(245, 247, 250, 0.5);
}
</style>
