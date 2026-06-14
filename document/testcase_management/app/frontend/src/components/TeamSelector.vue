<template>
  <div class="team-selector-wrapper">
    <el-select
      v-model="selectedTeamId"
      placeholder="选择项目组"
      @change="handleChange"
      class="team-selector"
      filterable
      :loading="loading"
      :teleported="true"
      popper-class="team-selector-dropdown"
    >
      <el-option
        v-for="team in teamList"
        :key="team.id"
        :label="team.name"
        :value="team.id"
      >
        <div class="team-option">
          <el-icon class="team-icon"><Folder /></el-icon>
          <span class="team-name">{{ team.name }}</span>
          <span class="team-count">({{ team.project_count || 0 }}个用例库)</span>
        </div>
      </el-option>
    </el-select>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, computed } from 'vue'
import { Folder } from '@element-plus/icons-vue'
import { useTeam } from '../composables/useTeam'

const { currentTeam, teamList, loadTeams, switchTeam, loadingTeams } = useTeam()

const selectedTeamId = ref(null)
const loading = computed(() => loadingTeams.value)

const emit = defineEmits(['change'])

// 监听当前项目组变化
watch(currentTeam, (newTeam) => {
  if (newTeam) {
    selectedTeamId.value = newTeam.id
  } else {
    selectedTeamId.value = null
  }
}, { immediate: true })

const handleChange = (teamId) => {
  if (!teamId) {
    switchTeam(null)
    emit('change', null)
    return
  }
  
  const team = teamList.value.find(t => t.id === teamId)
  if (team) {
    switchTeam(team)
    emit('change', team)
  }
}

onMounted(() => {
  loadTeams()
})

// 暴露方法供父组件调用
defineExpose({
  loadTeams
})
</script>

<style scoped>
.team-selector-wrapper {
  display: inline-block;
  position: relative;
  z-index: 1000;
}

.team-selector {
  width: 260px;
}

.team-selector :deep(.el-input__wrapper) {
  border: 1px solid #e2e8f0;
  box-shadow: none;
  transition: all 0.15s;
  border-radius: 8px;
  background-color: #ffffff;
}

.team-selector :deep(.el-input__wrapper:hover) {
  border-color: #cbd5e1;
}

.team-selector :deep(.el-input__wrapper.is-focus) {
  border-color: #4f46e5;
  box-shadow: 0 0 0 1px rgba(79, 70, 229, 0.2);
}

.team-selector :deep(.el-input__inner) {
  color: #0f172a;
  font-size: 14px;
  font-weight: 500;
}

.team-option {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  height: 100%;
  line-height: normal;
}

.team-icon {
  font-size: 16px;
  color: #4f46e5;
}

.team-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #334155;
}

.team-count {
  font-size: 12px;
  color: #94a3b8;
}
</style>
