<template>
  <div class="mobile-page edit-wrap">
    <header class="header">
      <button class="plain" @click="router.back()">←</button>
      <h3>Edit Profile</h3>
      <button class="plain save" @click="submit">Save</button>
    </header>

    <section class="mobile-card form">
      <label>Username</label>
      <input v-model="form.username" :disabled="Boolean(form.id)" />
      <label>Full Name</label>
      <input v-model="form.full_name" />
      <label>Email</label>
      <input v-model="form.email" />
      <label>Phone</label>
      <input v-model="form.phone" />
      <label>Role</label>
      <select v-model="form.roleId">
        <option :value="null">请选择</option>
        <option v-for="r in roles" :key="r.id" :value="r.id">{{ r.name }}</option>
      </select>
      <label>Data Permission</label>
      <select v-model="form.position_tag_id">
        <option :value="null">请选择</option>
        <option v-for="tag in positionTags" :key="tag.id" :value="tag.id">{{ tag.name }}</option>
      </select>

      <label>Department Authorization</label>
      <div class="multi-select">
        <button
          v-for="dept in departments"
          :key="dept.id"
          type="button"
          class="chip"
          :class="{ active: form.departmentIds.includes(dept.id) }"
          @click="toggleDepartment(dept.id)"
        >
          {{ dept.name }}
        </button>
      </div>

      <label>Project Team Authorization</label>
      <div class="multi-select">
        <button
          v-for="team in filteredTeams"
          :key="team.id"
          type="button"
          class="chip"
          :class="{ active: form.teamIds.includes(team.id) }"
          @click="toggleTeam(team.id)"
        >
          {{ team.name }}
        </button>
      </div>

      <template v-if="form.id">
        <label>Security Management</label>
        <div class="security-actions">
          <button class="security-btn" :disabled="resettingPassword" @click="handleResetPassword">
            {{ resettingPassword ? '重置中...' : '重置密码' }}
          </button>
          <button class="security-btn" :disabled="unlocking" @click="handleUnlockUser">
            {{ unlocking ? '解锁中...' : '解锁账户' }}
          </button>
        </div>
      </template>
    </section>

    <footer class="footer">
      <button class="mobile-pill-btn mobile-muted-btn" @click="router.back()">Cancel</button>
      <button class="mobile-pill-btn mobile-primary-btn" @click="submit">Confirm Changes</button>
    </footer>

    <div v-if="passwordSheetVisible" class="ios-sheet-mask" @click="passwordSheetVisible = false"></div>
    <div v-if="passwordSheetVisible" class="ios-sheet">
      <div class="ios-sheet-handle"></div>
      <h4>密码已重置</h4>
      <p>新密码仅显示一次，请立即复制并妥善保存。</p>
      <div class="pwd-box">{{ generatedPassword }}</div>
      <div class="ios-sheet-actions">
        <button class="ios-btn ghost" :disabled="copyingPassword" @click="copyPassword">
          {{ copyingPassword ? '复制中...' : '复制密码' }}
        </button>
        <button class="ios-btn primary" @click="passwordSheetVisible = false">完成</button>
      </div>
      <div v-if="copiedVisible" class="copy-ok">已复制到剪贴板</div>
      <div v-if="copyHintVisible" class="copy-hint">若无法自动复制，请长按上方密码手动复制</div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { createUser, getUsers, resetUserPassword, unlockUser, updateUser } from '../../api/user'
import { assignRoles, getRoles } from '../../api/role'
import { positionTagApi } from '../../api/positionTag'
import { organizationApi } from '../../api/organization'
import { assignTeams } from '../../api/userTeam'
import { getTeams } from '../../api/team'

const route = useRoute()
const router = useRouter()
const roles = ref([])
const positionTags = ref([])
const departments = ref([])
const teams = ref([])
const resettingPassword = ref(false)
const unlocking = ref(false)
const passwordSheetVisible = ref(false)
const generatedPassword = ref('')
const copyHintVisible = ref(false)
const copyingPassword = ref(false)
const copiedVisible = ref(false)
const form = reactive({
  id: null, username: '', full_name: '', email: '', phone: '', roleId: null, position_tag_id: null, departmentIds: [], teamIds: [], status: 1
})

const filteredTeams = computed(() => {
  if (!form.departmentIds.length) return teams.value
  return teams.value.filter(team => form.departmentIds.includes(team.department_id))
})

const loadDetail = async () => {
  if (!route.params.id) return
  const res = await getUsers({ page: 1, size: 1000 })
  const row = (res.data.records || []).find(item => Number(item.id) === Number(route.params.id))
  if (!row) return
  Object.assign(form, row, {
    roleId: row.roleId || null,
    position_tag_id: row.position_tag_id || null,
    departmentIds: row.departmentIds || [],
    teamIds: row.teamIds || []
  })
}

const submit = async () => {
  if (!form.roleId) {
    ElMessage.warning('请选择角色')
    return
  }
  if (!form.position_tag_id) {
    ElMessage.warning('请选择数据权限')
    return
  }
  const payload = {
    username: form.username,
    full_name: form.full_name,
    email: form.email,
    phone: form.phone || null,
    status: form.status,
    position_tag_id: form.position_tag_id
  }
  let userId = form.id
  if (form.id) {
    await updateUser(form.id, payload)
  } else {
    payload.password = form.email
    const res = await createUser(payload)
    userId = res.data.id
  }
  await assignRoles(userId, [form.roleId])
  await organizationApi.assignUserDepartments(userId, form.departmentIds || [])
  await assignTeams({ user_id: userId, team_ids: form.teamIds || [] })
  ElMessage.success('保存成功')
  router.push('/m/users')
}

const toggleDepartment = (id) => {
  if (form.departmentIds.includes(id)) {
    form.departmentIds = form.departmentIds.filter(item => item !== id)
  } else {
    form.departmentIds = [...form.departmentIds, id]
  }
  const validTeamIds = filteredTeams.value.map(team => team.id)
  form.teamIds = form.teamIds.filter(teamId => validTeamIds.includes(teamId))
}

const toggleTeam = (id) => {
  if (form.teamIds.includes(id)) {
    form.teamIds = form.teamIds.filter(item => item !== id)
  } else {
    form.teamIds = [...form.teamIds, id]
  }
}

const handleResetPassword = async () => {
  if (!form.id || !form.username) return
  try {
    await ElMessageBox.confirm(`确认重置用户 ${form.username} 的密码？`, '重置密码', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'warning'
    })
    resettingPassword.value = true
    const res = await resetUserPassword(form.id)
    const newPwd = res.data?.new_password
    if (!newPwd) {
      ElMessage.success('密码重置成功')
      return
    }
    generatedPassword.value = newPwd
    copyHintVisible.value = false
    passwordSheetVisible.value = true
    await copyPassword(true)
  } catch {
    // cancel
  } finally {
    resettingPassword.value = false
  }
}

const copyPassword = async (silent = false) => {
  const text = generatedPassword.value || ''
  if (!text) return
  copyingPassword.value = true
  try {
    // 优先使用 Clipboard API，失败则降级到 execCommand，兼容更多 WebView 场景
    let copied = false
    if (navigator?.clipboard?.writeText) {
      try {
        await navigator.clipboard.writeText(text)
        copied = true
      } catch {
        copied = false
      }
    }
    if (!copied) {
      const textarea = document.createElement('textarea')
      textarea.value = text
      textarea.setAttribute('readonly', 'readonly')
      textarea.style.position = 'fixed'
      textarea.style.opacity = '0'
      textarea.style.left = '-9999px'
      textarea.style.top = '-9999px'
      document.body.appendChild(textarea)
      textarea.select()
      textarea.setSelectionRange(0, textarea.value.length)
      copied = document.execCommand('copy')
      document.body.removeChild(textarea)
    }
    if (!copied) {
      throw new Error('copy failed')
    }
    copyHintVisible.value = false
    copiedVisible.value = true
    setTimeout(() => {
      copiedVisible.value = false
    }, 1800)
    ElMessage.success('新密码已复制')
  } catch {
    copyHintVisible.value = true
    if (!silent) ElMessage.warning('复制失败，请手动复制')
  } finally {
    copyingPassword.value = false
  }
}

const handleUnlockUser = async () => {
  if (!form.id || !form.username) return
  try {
    await ElMessageBox.confirm(`确认解锁用户 ${form.username} 的账户？`, '解锁账户', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'warning'
    })
    unlocking.value = true
    await unlockUser(form.id)
    ElMessage.success('账户已解锁')
  } catch {
    // cancel
  } finally {
    unlocking.value = false
  }
}

onMounted(async () => {
  const [roleRes, tagRes, deptRes, teamRes] = await Promise.all([
    getRoles({ page: 1, size: 1000 }),
    positionTagApi.getPositionTags({ page: 1, size: 1000 }),
    organizationApi.getDepartments({ page: 1, size: 1000 }),
    getTeams({ page: 1, size: 1000 })
  ])
  roles.value = roleRes.data.records || []
  positionTags.value = tagRes.data.records || []
  departments.value = deptRes.data.records || []
  teams.value = (teamRes.data.records || []).filter(team => team.status === 1)
  form.id = route.params.id ? Number(route.params.id) : null
  await loadDetail()
})
</script>

<style scoped>
.edit-wrap { padding-bottom: 110px; }
.header { height: 52px; display:flex; justify-content:space-between; align-items:center; }
.header h3 { margin: 0; font-size: 20px; font-weight: 800; }
.plain { border: none; background: transparent; color: #0058bb; font-weight: 700; }
.form { margin-top: 8px; padding: 16px; display: flex; flex-direction: column; gap: 8px; }
.form label { font-size: 12px; color: #6b6d73; font-weight: 700; }
.form input, .form select { border: none; background: #edf0f6; border-radius: 999px; height: 42px; padding: 0 12px; }
.multi-select { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 6px; }
.chip { border: 1px solid #dae0ef; background: #fff; color: #5f6371; border-radius: 999px; padding: 5px 10px; font-size: 12px; }
.chip.active { background: #cfcdff; color: #3631b5; border-color: #cfcdff; }
.security-actions { display: flex; gap: 8px; margin-bottom: 6px; }
.security-btn {
  flex: 1;
  height: 40px;
  border-radius: 999px;
  border: none;
  background: #eef1f7;
  color: #4f5561;
  font-weight: 700;
}
.security-btn:disabled { opacity: 0.65; }
.footer { position: fixed; left: 16px; right: 16px; bottom: max(12px, env(safe-area-inset-bottom)); display:flex; gap: 10px; }
.footer button { flex: 1; }

.ios-sheet-mask {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.28);
  z-index: 60;
}
.ios-sheet {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 61;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(28px);
  -webkit-backdrop-filter: blur(28px);
  border-top-left-radius: 22px;
  border-top-right-radius: 22px;
  padding: 10px 16px calc(18px + env(safe-area-inset-bottom));
  box-shadow: 0 -12px 28px rgba(15, 23, 42, 0.18);
}
.ios-sheet-handle {
  width: 42px;
  height: 5px;
  border-radius: 3px;
  background: #d1d5de;
  margin: 0 auto 10px;
}
.ios-sheet h4 {
  margin: 0;
  text-align: center;
  font-size: 17px;
  font-weight: 800;
}
.ios-sheet p {
  margin: 8px 0 12px;
  text-align: center;
  color: #5d6370;
  font-size: 13px;
}
.pwd-box {
  border-radius: 14px;
  background: #f2f4f8;
  padding: 12px 14px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 14px;
  word-break: break-all;
  user-select: text;
  -webkit-user-select: text;
}
.ios-sheet-actions {
  display: flex;
  gap: 10px;
  margin-top: 12px;
}
.ios-btn {
  flex: 1;
  height: 44px;
  border-radius: 14px;
  border: none;
  font-weight: 700;
}
.ios-btn.ghost {
  background: #eef1f7;
  color: #4d5564;
}
.ios-btn:disabled { opacity: 0.65; }
.ios-btn.primary {
  background: linear-gradient(135deg, #0a66c7, #4a90ff);
  color: #fff;
}
.copy-hint {
  margin-top: 8px;
  color: #8b5e00;
  font-size: 12px;
  text-align: center;
}
.copy-ok {
  margin-top: 8px;
  color: #158243;
  font-size: 12px;
  text-align: center;
  font-weight: 700;
}
</style>
