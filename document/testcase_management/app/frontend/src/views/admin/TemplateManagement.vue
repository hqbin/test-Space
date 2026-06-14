<template>
  <div class="template-management">
    <el-card shadow="never">
      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <el-tab-pane :label="$t('templateMgmt.reportTemplateTab')" name="reportTemplate">
          <ReportTemplateContent />
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ReportTemplateContent from './ReportTemplateContent.vue'

const route = useRoute()
const router = useRouter()

const activeTab = ref('reportTemplate')

const handleTabChange = (tab) => {
  router.replace({ query: { tab } })
}
</script>

<style scoped>
.template-management {
  height: 100%;
  background: #f8fafc;
  padding: 24px;
  overflow-y: auto;
}

.template-management :deep(.el-card) {
  height: 100%;
  border-radius: 16px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.template-management :deep(.el-card__body) {
  height: 100%;
  padding: 0 !important;
}

.template-management :deep(.el-tabs) {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.template-management :deep(.el-tabs__header) {
  padding: 0 20px;
  margin-bottom: 0;
  border-bottom: 1px solid #e2e8f0;
}

.template-management :deep(.el-tabs__item) {
  font-weight: 500;
  color: #64748b;
  font-size: 14px;
}

.template-management :deep(.el-tabs__item.is-active) {
  color: #4f46e5;
}

.template-management :deep(.el-tabs__active-bar) {
  background-color: #4f46e5;
}

.template-management :deep(.el-tabs__content) {
  flex: 1;
  overflow: hidden;
}

.template-management :deep(.el-tab-pane) {
  height: 100%;
}
</style>
