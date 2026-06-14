<template>
  <div class="team-switcher">
    <button
      class="team-pill"
      type="button"
      :disabled="disabled"
      @click="open"
      :title="currentTeam?.name || '未选择项目组'"
    >
      <span class="dot" :class="{ on: Boolean(currentTeam?.id) }"></span>
      <span class="label">{{ currentTeam?.name || '选择项目组' }}</span>
      <span class="chev">▾</span>
    </button>

    <!-- Dialog 弹窗方式 -->
    <el-dialog
      v-model="visible"
      title="切换项目组"
      width="85%"
      :show-close="false"
      class="team-dialog"
      align-center
    >
      <div class="team-content">
        <div class="team-list">
          <button
            v-for="t in teamList"
            :key="t.id"
            type="button"
            class="team-card"
            :class="{ active: Number(t.id) === Number(currentTeam?.id) }"
            @click="pick(t)"
          >
            <div class="team-info">
              <span class="team-name">{{ t.name }}</span>
              <span v-if="Number(t.id) === Number(currentTeam?.id)" class="team-badge">当前</span>
            </div>
            <span v-if="Number(t.id) === Number(currentTeam?.id)" class="team-check">✓</span>
          </button>
          <div v-if="!teamList?.length" class="team-empty">暂无可用项目组</div>
        </div>
      </div>
      <template #footer>
        <div class="team-actions">
          <el-button class="team-cancel-btn" @click="close">取消</el-button>
          <el-button type="primary" class="team-confirm-btn" @click="close">完成</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useTeam } from '../../composables/useTeam'

const emit = defineEmits(['switched'])
const props = defineProps({
  disabled: { type: Boolean, default: false }
})

const { currentTeam, teamList, loadTeams, switchTeam } = useTeam()
const visible = ref(false)

const disabled = computed(() => props.disabled)

const open = async () => {
  if (disabled.value) return
  if (!teamList.value?.length) await loadTeams()
  visible.value = true
}
const close = () => {
  visible.value = false
}

const pick = async (t) => {
  if (!t?.id) return
  if (Number(t.id) === Number(currentTeam.value?.id)) {
    close()
    return
  }
  await switchTeam(t)
  close()
  emit('switched', t)
}

onMounted(async () => {
  // 若已有 currentTeam 但 teamList 为空，补一次列表加载，确保能切换
  if (currentTeam.value?.id && !teamList.value?.length) await loadTeams()
})
</script>

<style scoped>
.team-switcher { display: inline-flex; }
.team-pill {
  height: 40px;
  border-radius: 999px;
  padding: 0 10px 0 10px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  max-width: 46vw;
  background: rgba(255, 255, 255, 0.86);
  border: 1px solid rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  box-shadow: 0 8px 20px rgba(15, 23, 42, 0.10);
  color: #2f3a4a;
}
.team-pill:disabled { opacity: 0.6; }
.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #c9ced8;
  box-shadow: inset 0 0 0 2px rgba(255,255,255,0.75);
}
.dot.on { background: linear-gradient(135deg, #0a66c7, #4a90ff); }
.label {
  font-size: 13px;
  font-weight: 800;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.chev { font-size: 12px; color: #6f7a88; flex-shrink: 0; }

/* Dialog 内容样式 */
.team-content {
  padding: 8px 0;
}

.team-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 50vh;
  overflow-y: auto;
}

.team-card {
  width: 100%;
  padding: 16px;
  border-radius: 16px;
  background: #f8fafc;
  border: 2px solid transparent;
  display: flex;
  align-items: center;
  justify-content: space-between;
  transition: all 0.2s ease;
  text-align: left;
}

.team-card:active {
  transform: scale(0.98);
}

.team-card.active {
  background: linear-gradient(135deg, rgba(10, 102, 199, 0.08), rgba(74, 144, 255, 0.06));
  border-color: rgba(10, 102, 199, 0.3);
}

.team-info {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  min-width: 0;
}

.team-name { 
  font-size: 15px;
  font-weight: 700;
  color: #2e3440;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.team-badge {
  font-size: 11px;
  font-weight: 700;
  color: #0a66c7;
  background: rgba(10, 102, 199, 0.12);
  padding: 3px 8px;
  border-radius: 999px;
  flex-shrink: 0;
}

.team-check {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: linear-gradient(135deg, #0a66c7, #4a90ff);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 700;
  flex-shrink: 0;
}

.team-empty { 
  text-align: center; 
  color: #7b8291; 
  font-size: 14px; 
  padding: 40px 0; 
}

.team-actions {
  display: flex;
  gap: 12px;
  width: 100%;
}

.team-cancel-btn {
  flex: 1;
  height: 46px;
  border-radius: 12px;
  font-weight: 700;
  border: 1px solid #e5e7eb;
  background: #f9fafb;
  color: #374151;
}

.team-confirm-btn {
  flex: 1;
  height: 46px;
  border-radius: 12px;
  font-weight: 700;
  background: linear-gradient(135deg, #0a66c7, #4a90ff);
  border: none;
}
</style>

<style>
/* 全局样式覆盖 Element Plus Dialog */
.team-dialog .el-dialog {
  border-radius: 22px;
  overflow: hidden;
  background: #fff;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
}

.team-dialog .el-dialog__header {
  padding: 20px 20px 0;
  margin-right: 0;
  text-align: center;
}

.team-dialog .el-dialog__title {
  font-weight: 900;
  font-size: 18px;
  color: #2e3440;
}

.team-dialog .el-dialog__body {
  padding: 0 20px;
}

.team-dialog .el-dialog__footer {
  padding: 0 20px 20px;
  border-top: none;
}
</style>
