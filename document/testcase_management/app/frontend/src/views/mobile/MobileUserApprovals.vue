<template>
  <div class="mobile-page approve-wrap">
    <header class="header">
      <button class="back" @click="router.back()">←</button>
      <h3>待审核注册用户</h3>
      <span class="count">{{ rows.length }}</span>
    </header>

    <div class="cards">
      <article v-for="u in rows" :key="u.id" class="mobile-card card">
        <h4>{{ u.username }}</h4>
        <p>邮箱：{{ u.email }}</p>
        <p>姓名：{{ u.full_name || '-' }}</p>
        <p>手机号：{{ u.phone || '-' }}</p>
        <p>申请时间：{{ formatDate(u.created_at) }}</p>
        <div class="btns">
          <button class="mobile-pill-btn reject" @click="doReject(u)">拒绝</button>
          <button class="mobile-pill-btn mobile-primary-btn" @click="openApprove(u)">通过并授权</button>
        </div>
      </article>
    </div>

    <section v-if="approveTarget" class="mobile-card auth-card">
      <h4>授权配置：{{ approveTarget.username }}</h4>
      <label>角色</label>
      <select v-model="approveForm.role_id">
        <option :value="null">请选择</option>
        <option v-for="r in roles" :key="r.id" :value="r.id">{{ r.name }}</option>
      </select>
      <label>数据权限</label>
      <select v-model="approveForm.position_tag_id">
        <option :value="null">请选择</option>
        <option v-for="tag in positionTags" :key="tag.id" :value="tag.id">{{ tag.name }}</option>
      </select>
      <label>组织授权</label>
      <div class="chips">
        <button
          v-for="dept in departments"
          :key="dept.id"
          type="button"
          class="chip"
          :class="{ active: approveForm.department_ids.includes(dept.id) }"
          @click="toggleDepartment(dept.id)"
        >
          {{ dept.name }}
        </button>
      </div>
      <label>项目组授权</label>
      <div class="chips">
        <button
          v-for="team in filteredTeams"
          :key="team.id"
          type="button"
          class="chip"
          :class="{ active: approveForm.team_ids.includes(team.id) }"
          @click="toggleTeam(team.id)"
        >
          {{ team.name }}
        </button>
      </div>
      <div class="btns">
        <button class="mobile-pill-btn" @click="approveTarget = null">取消</button>
        <button class="mobile-pill-btn mobile-primary-btn" @click="doApprove">确认通过</button>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { approveUser, getPendingUsers, rejectUser } from '../../api/user'
import { getRoles } from '../../api/role'
import { positionTagApi } from '../../api/positionTag'
import { organizationApi } from '../../api/organization'
import { getTeams } from '../../api/team'

const router = useRouter()
const rows = ref([])
const roles = ref([])
const positionTags = ref([])
const departments = ref([])
const teams = ref([])
const approveTarget = ref(null)
const approveForm = reactive({
  role_id: null,
  position_tag_id: null,
  department_ids: [],
  team_ids: []
})

const filteredTeams = computed(() => {
  if (!approveForm.department_ids.length) return teams.value
  return teams.value.filter(team => approveForm.department_ids.includes(team.department_id))
})

const loadData = async () => {
  const res = await getPendingUsers()
  rows.value = res.data || []
}
const openApprove = (user) => {
  approveTarget.value = user
  approveForm.role_id = null
  approveForm.position_tag_id = null
  approveForm.department_ids = []
  approveForm.team_ids = []
}

const doApprove = async () => {
  if (!approveTarget.value) return
  const payload = {}
  if (approveForm.role_id) payload.role_id = approveForm.role_id
  if (approveForm.position_tag_id) payload.position_tag_id = approveForm.position_tag_id
  if (approveForm.department_ids.length) payload.department_ids = approveForm.department_ids
  if (approveForm.team_ids.length) payload.team_ids = approveForm.team_ids
  await approveUser(approveTarget.value.id, payload)
  ElMessage.success(`已通过 ${approveTarget.value.username}`)
  approveTarget.value = null
  loadData()
}
const doReject = async (u) => {
  await rejectUser(u.id)
  ElMessage.success(`已拒绝 ${u.username}`)
  loadData()
}
const formatDate = (d) => (d ? String(d).replace('T', ' ').slice(0, 16) : '-')

const toggleDepartment = (id) => {
  if (approveForm.department_ids.includes(id)) {
    approveForm.department_ids = approveForm.department_ids.filter(item => item !== id)
  } else {
    approveForm.department_ids = [...approveForm.department_ids, id]
  }
  const validTeamIds = filteredTeams.value.map(team => team.id)
  approveForm.team_ids = approveForm.team_ids.filter(teamId => validTeamIds.includes(teamId))
}

const toggleTeam = (id) => {
  if (approveForm.team_ids.includes(id)) {
    approveForm.team_ids = approveForm.team_ids.filter(item => item !== id)
  } else {
    approveForm.team_ids = [...approveForm.team_ids, id]
  }
}

onMounted(async () => {
  await Promise.all([
    loadData(),
    getRoles({ page: 1, size: 1000 }).then(res => { roles.value = res.data.records || [] }),
    positionTagApi.getPositionTags({ page: 1, size: 1000 }).then(res => { positionTags.value = res.data.records || [] }),
    organizationApi.getDepartments({ page: 1, size: 1000 }).then(res => { departments.value = res.data.records || [] }),
    getTeams({ page: 1, size: 1000 }).then(res => { teams.value = (res.data.records || []).filter(team => team.status === 1) })
  ])
})
</script>

<style scoped>
.header { height: 52px; display:flex; align-items: center; justify-content: space-between; }
.back { border: none; background: transparent; color: #0058bb; font-size: 20px; width: 34px; }
.header h3 { margin: 0; font-size: 20px; font-weight: 800; }
.count { min-width: 28px; height: 28px; border-radius: 14px; background: #0058bb; color: #fff; font-weight: 800; display:flex; align-items:center; justify-content:center; font-size: 12px; }
.cards { display:flex; flex-direction:column; gap: 12px; margin-top: 10px; }
.card { padding: 16px; }
.auth-card { margin-top: 12px; padding: 16px; display: flex; flex-direction: column; gap: 8px; }
.auth-card h4 { margin: 0 0 4px; font-size: 16px; }
.auth-card label { font-size: 12px; color: #6b6d73; font-weight: 700; }
.auth-card select { border: none; background: #edf0f6; border-radius: 999px; height: 42px; padding: 0 12px; }
.chips { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 6px; }
.chip { border: 1px solid #dae0ef; background: #fff; color: #5f6371; border-radius: 999px; padding: 5px 10px; font-size: 12px; }
.chip.active { background: #cfcdff; color: #3631b5; border-color: #cfcdff; }
.card h4 { margin: 0 0 8px; font-size: 18px; }
.card p { margin: 3px 0; color: #5f6168; font-size: 13px; }
.btns { margin-top: 12px; display:flex; gap: 8px; }
.btns button { flex:1; }
.reject { background: #fff; color: #b31b25; border: 1px solid rgba(179, 27, 37, .2); }
</style>
