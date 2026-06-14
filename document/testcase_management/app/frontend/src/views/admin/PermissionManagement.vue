<template>
  <div class="permission-management">
    <el-card shadow="never">
      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <el-tab-pane :label="$t('permission.rolePermission')" name="roles">
          <RoleManagementContent />
        </el-tab-pane>
        <el-tab-pane :label="$t('permission.dataPermission')" name="dataPermissions">
          <DataPermissionContent />
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import RoleManagementContent from './RoleManagementContent.vue'
import DataPermissionContent from './DataPermissionContent.vue'

const route = useRoute()
const router = useRouter()

const activeTab = ref(route.query.tab || 'roles')

const handleTabChange = (tab) => {
  router.replace({ query: { tab } })
}
</script>

<style scoped>
.permission-management {
  height: 100%;
  background: #f8fafc;
  padding: 24px;
  overflow-y: auto;
}

.permission-management :deep(.el-card) {
  height: 100%;
  border-radius: 16px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.permission-management :deep(.el-card__body) {
  height: 100%;
  padding: 0 !important;
}

.permission-management :deep(.el-tabs) {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.permission-management :deep(.el-tabs__header) {
  padding: 0 20px;
  margin-bottom: 0;
  border-bottom: 1px solid #e2e8f0;
}

.permission-management :deep(.el-tabs__item) {
  font-weight: 500;
  color: #64748b;
  font-size: 14px;
}

.permission-management :deep(.el-tabs__item.is-active) {
  color: #4f46e5;
}

.permission-management :deep(.el-tabs__active-bar) {
  background-color: #4f46e5;
}

.permission-management :deep(.el-tabs__content) {
  flex: 1;
  overflow: hidden;
}

.permission-management :deep(.el-tab-pane) {
  height: 100%;
}
</style>
