<template>
  <div class="notification-management">
    <el-card shadow="never">
      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <el-tab-pane :label="$t('menu.notificationRules')" name="rules">
          <NotificationRuleContent />
        </el-tab-pane>
        <el-tab-pane :label="$t('menu.notificationTemplates')" name="templates">
          <NotificationTemplateContent />
        </el-tab-pane>
        <el-tab-pane label="钉钉机器人" name="dingtalk">
          <DingtalkBotContent />
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import NotificationRuleContent from './NotificationRuleContent.vue'
import NotificationTemplateContent from './NotificationTemplateContent.vue'
import DingtalkBotContent from './DingtalkBotContent.vue'

const route = useRoute()
const router = useRouter()

// 从路由参数获取初始tab，默认为rules
const activeTab = ref(route.query.tab || 'rules')

const handleTabChange = (tab) => {
  // 更新URL参数但不刷新页面
  router.replace({ query: { tab } })
}
</script>

<style scoped>
.notification-management {
  height: 100%;
  background: #f8fafc;
  padding: 24px;
  overflow-y: auto;
}

.notification-management :deep(.el-card) {
  height: 100%;
  border-radius: 16px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.notification-management :deep(.el-card__body) {
  height: 100%;
  padding: 0 !important;
}

.notification-management :deep(.el-tabs) {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.notification-management :deep(.el-tabs__header) {
  padding: 0 20px;
  margin-bottom: 0;
  border-bottom: 1px solid #e2e8f0;
}

.notification-management :deep(.el-tabs__item) {
  font-weight: 500;
  color: #64748b;
  font-size: 14px;
}

.notification-management :deep(.el-tabs__item.is-active) {
  color: #4f46e5;
}

.notification-management :deep(.el-tabs__active-bar) {
  background-color: #4f46e5;
}

.notification-management :deep(.el-tabs__content) {
  flex: 1;
  overflow: hidden;
}

.notification-management :deep(.el-tab-pane) {
  height: 100%;
}
</style>
