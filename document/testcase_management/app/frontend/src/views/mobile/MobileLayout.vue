<template>
  <div class="mobile-page mobile-safe layout-wrap">
    <div ref="contentEl" class="content">
      <router-view />
    </div>
    <nav class="mobile-bottom-nav" v-if="tabs.length > 0 && !route.meta.hideMobileNav">
      <button
        v-for="tab in tabs"
        :key="tab.path"
        class="mobile-nav-item"
        :class="{ active: route.path.startsWith(tab.path) }"
        @click="router.push(tab.path)"
      >
        <el-icon><component :is="tab.icon" /></el-icon>
        <span>{{ tab.label }}</span>
      </button>
    </nav>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { DataAnalysis, UserFilled, Calendar, Setting } from '@element-plus/icons-vue'
import { useUserRole } from '../../composables/useUserRole'

const route = useRoute()
const router = useRouter()
const { hasMenu, loadUserRoles } = useUserRole()
const contentEl = ref(null)

const tabs = computed(() => {
  const all = [
    { key: 'testplans', path: '/m/testplans', label: '计划', icon: Calendar },
    { key: 'reports', path: '/m/reports', label: '报告', icon: DataAnalysis },
    { key: 'users', path: '/m/users', label: '用户', icon: UserFilled },
    { key: 'settings', path: '/m/settings', label: '设置', icon: Setting }
  ]
  return all.filter(item => item.key === 'settings' || hasMenu(item.key))
})

onMounted(() => {
  loadUserRoles()
})

watch(
  () => route.fullPath,
  async () => {
    await nextTick()
    contentEl.value?.scrollTo({ top: 0, behavior: 'auto' })
  }
)
</script>

<style scoped>
.layout-wrap {
  height: 100dvh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.content {
  flex: 1;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  padding-top: 12px;
  padding-bottom: 104px;
}
</style>
