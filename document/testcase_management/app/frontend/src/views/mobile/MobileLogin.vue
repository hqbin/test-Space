<template>
  <div class="mobile-page mobile-safe login-wrap">
    <div class="orb orb-left"></div>
    <div class="orb orb-right"></div>
    <section class="brand">
      <div class="logo">T</div>
      <h1>TeVaMaT</h1>
      <p>Welcome</p>
    </section>

    <section class="mobile-card form-card">
      <label>USERNAME</label>
      <input v-model="form.username" placeholder="Username" />
      <label>PASSWORD</label>
      <input v-model="form.password" type="password" @keyup.enter="handleLogin" placeholder="Password" />
      <button class="mobile-pill-btn mobile-primary-btn sign-btn" :disabled="loading" @click="handleLogin">
        {{ loading ? 'Signing in...' : 'Sign In' }}
      </button>
    </section>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { login } from '../../api/auth'
import { useUserStore } from '../../stores/user'
import { getUserRoles } from '../../api/role'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const loading = ref(false)
const form = reactive({ username: '', password: '' })

const handleLogin = async () => {
  if (!form.username || !form.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  loading.value = true
  try {
    const res = await login(form)
    localStorage.setItem('token', res.data.token)
    userStore.updateUser(res.data.user)
    sessionStorage.removeItem('mobile_permissions_cache')
    let defaultPath = '/m/reports'
    const user = res.data.user || {}
    if (user.username !== 'admin' && user.username !== 'super' && user.id) {
      const roleRes = await getUserRoles(user.id)
      const permissionSet = new Set()
      ;(roleRes.data || []).forEach(role => {
        ;(role.permissions || []).forEach(perm => permissionSet.add(perm))
      })
      if (!permissionSet.has('reports') && permissionSet.has('users')) {
        defaultPath = '/m/users'
      }
    }
    const redirect = route.query.redirect || defaultPath
    // 登录成功后刷新页面以清除缓存数据
    window.location.href = redirect
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-wrap {
  min-height: 100dvh;
  display: flex;
  flex-direction: column;
  justify-content: center;
  position: relative;
  overflow: hidden;
  background: linear-gradient(135deg, #f6f6fb 0%, #e0e7ff 50%, #f3e8ff 100%);
}
.orb { position: absolute; width: 220px; height: 220px; border-radius: 50%; filter: blur(80px); }
.orb-left { background: rgba(0, 88, 187, 0.15); top: -80px; left: -80px; }
.orb-right { background: rgba(136, 60, 147, 0.16); right: -80px; bottom: -80px; }
.brand { text-align: center; margin-bottom: 26px; z-index: 1; }
.brand h1 { margin: 10px 0 6px; font-size: 28px; font-weight: 800; }
.brand p { color: #5a5b60; font-size: 12px; font-weight: 600; }
.logo { width: 72px; height: 72px; border-radius: 50%; margin: 0 auto; background: linear-gradient(135deg, #0058bb, #6c9fff); color: #fff; display:flex; align-items:center; justify-content:center; font-size: 34px; font-weight: 800; box-shadow: 0 16px 28px rgba(0,88,187,.25);}
.form-card { padding: 22px; z-index: 1; backdrop-filter: blur(8px); background: rgba(255,255,255,.82); }
.form-card label { display:block; margin: 12px 0 8px; font-size: 11px; font-weight: 800; color: #6a6c73; letter-spacing: .08em; }
.form-card input { width:100%; height: 46px; border-radius: 999px; border: none; background: #fff; padding: 0 14px; outline: 2px solid transparent; }
.form-card input:focus { outline-color: rgba(0,88,187,.24); }
.sign-btn { width: 100%; margin-top: 22px; }
</style>
