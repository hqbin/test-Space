<template>
  <div class="login-container">
    <div class="login-background">
      <div class="shape shape-1"></div>
      <div class="shape shape-2"></div>
      <div class="shape shape-3"></div>
    </div>
    
    <div class="login-card">
      <div class="login-header">
        <div class="logo">
          <el-icon :size="48" color="var(--primary-100)"><Checked /></el-icon>
        </div>
        <h1>TeVaMaT</h1>
        <p class="subtitle">Welcome</p>
      </div>

      <el-form v-if="!isRegisterMode" :model="form" class="login-form" @submit.prevent="handleLogin">
        <el-form-item>
          <el-input 
            v-model="form.username" 
            placeholder="Username" 
            size="large"
            :prefix-icon="User"
          />
        </el-form-item>
        <el-form-item>
          <el-input 
            v-model="form.password" 
            :type="passwordVisible ? 'text' : 'password'" 
            placeholder="Password" 
            size="large"
            :prefix-icon="Lock"
            @keyup.enter="handleLogin"
          >
            <template #suffix>
              <el-icon class="password-toggle" @click="passwordVisible = !passwordVisible">
                <View v-if="passwordVisible" />
                <Hide v-else />
              </el-icon>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item>
          <div class="captcha-container">
            <el-input 
              v-model="captchaCode" 
              placeholder="验证码" 
              size="large"
              :prefix-icon="Key"
              @keyup.enter="handleLogin"
              style="flex: 1;"
            />
            <img 
              v-if="captchaImage" 
              :src="captchaImage" 
              class="captcha-image" 
              @click="refreshCaptcha"
              title="点击刷新验证码"
            />
          </div>
        </el-form-item>
        <el-form-item>
          <el-button 
            type="primary" 
            @click="handleLogin" 
            size="large"
            :loading="loading"
            class="login-button"
          >
            <span v-if="!loading">Sign In</span>
            <span v-else>Signing in...</span>
          </el-button>
        </el-form-item>
        <div class="form-switch">
          <span @click="isRegisterMode = true" class="switch-link">Don't have an account? Register</span>
        </div>
      </el-form>

      <el-form v-else :model="regForm" class="login-form" @submit.prevent="handleRegister">
        <el-form-item>
          <el-input 
            v-model="regForm.username" 
            placeholder="Username" 
            size="large"
            :prefix-icon="User"
          />
          <div class="field-hint">Used for login</div>
        </el-form-item>
        <el-form-item>
          <el-input 
            v-model="regForm.password" 
            type="password"
            placeholder="Password" 
            size="large"
            :prefix-icon="Lock"
            show-password
          />
          <div class="field-hint">Min 8 chars, 3 of: uppercase / lowercase / number / special</div>
        </el-form-item>
        <el-form-item>
          <el-input 
            v-model="regForm.confirmPassword" 
            type="password"
            placeholder="Confirm Password" 
            size="large"
            :prefix-icon="Lock"
            show-password
            @keyup.enter="handleRegister"
          />
        </el-form-item>
        <el-form-item>
          <el-input 
            v-model="regForm.email" 
            placeholder="Email (required)" 
            size="large"
            :prefix-icon="Message"
          />
        </el-form-item>
        <el-form-item>
          <el-input 
            v-model="regForm.full_name" 
            placeholder="Full Name (optional)" 
            size="large"
            :prefix-icon="UserFilled"
          />
        </el-form-item>
        <el-form-item>
          <el-input 
            v-model="regForm.phone" 
            placeholder="Phone (optional)" 
            size="large"
            :prefix-icon="Phone"
          />
        </el-form-item>
        <el-form-item>
          <el-button 
            type="primary" 
            @click="handleRegister" 
            size="large"
            :loading="registerLoading"
            class="login-button"
          >
            <span v-if="!registerLoading">Register</span>
            <span v-else>Submitting...</span>
          </el-button>
        </el-form-item>
        <div class="form-switch">
          <span @click="isRegisterMode = false" class="switch-link">Already have an account? Sign In</span>
        </div>
      </el-form>

      <div class="quick-tools">
        <router-link to="/adb-tool-public" class="tool-link">
          <el-icon><Iphone /></el-icon>
          <span>ADB Tool</span>
        </router-link>
      </div>
    </div>

    <!-- 强制修改密码对话框 -->
    <el-dialog
      v-model="changePasswordVisible"
      title="首次登录 — 请修改密码"
      width="420px"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      :show-close="false"
    >
      <p style="color: #64748b; margin: 0 0 20px 0; font-size: 14px;">
        为保障账户安全，首次登录需要修改初始密码。<br/>
        要求：至少8位，含大小写字母、数字、特殊字符中的至少3种。
      </p>
      <el-form :model="pwdForm" label-position="top">
        <!-- 隐藏的用户名字段，让浏览器密码管理器正确识别用户名 -->
        <input type="text" :value="form.username" autocomplete="username" name="username" style="display:none;" />
        <el-form-item label="新密码" required>
          <el-input
            v-model="pwdForm.newPassword"
            type="password"
            placeholder="请输入新密码"
            show-password
            autocomplete="new-password"
            name="new-password"
          />
        </el-form-item>
        <el-form-item label="确认新密码" required>
          <el-input
            v-model="pwdForm.confirmPassword"
            type="password"
            placeholder="再次输入新密码"
            show-password
            autocomplete="new-password"
            name="confirm-password"
            @keyup.enter="handleChangePassword"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="handleCancelChange">退出登录</el-button>
        <el-button type="primary" @click="handleChangePassword" :loading="changingPassword">确认修改</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { reactive, ref, nextTick, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { login, register } from '../../api/auth'
import { changePassword } from '../../api/profile'
import { ElMessage } from 'element-plus'
import { User, Lock, Checked, View, Hide, Iphone, Message, UserFilled, Phone, Key } from '@element-plus/icons-vue'
import { useUserStore } from '../../stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const loading = ref(false)
const passwordVisible = ref(false)
const isRegisterMode = ref(false)
const registerLoading = ref(false)
const form = reactive({
  username: '',
  password: ''
})

// 验证码相关
const captchaId = ref('')
const captchaImage = ref('')
const captchaCode = ref('')

// 页面加载时获取验证码
onMounted(() => {
  fetchCaptcha()
})

const regForm = reactive({
  username: '',
  password: '',
  confirmPassword: '',
  email: '',
  full_name: '',
  phone: ''
})

// 强制修改密码
const changePasswordVisible = ref(false)
const changingPassword = ref(false)
let originalPassword = '' // 保存登录时的原始密码，用于修改密码接口
const pwdForm = reactive({
  newPassword: '',
  confirmPassword: ''
})

const handleLogin = async () => {
  if (!form.username || !form.password) {
    ElMessage.warning('Please enter username and password')
    return
  }
  
  if (!captchaCode.value) {
    ElMessage.warning('请输入验证码')
    return
  }
  
  loading.value = true
  try {
    const loginData = {
      username: form.username,
      password: form.password,
      captcha_id: captchaId.value,
      captcha_code: captchaCode.value
    }
    const res = await login(loginData)
    localStorage.setItem('token', res.data.token)
    if (res.data.signKey) {
      localStorage.setItem('signKey', res.data.signKey)
    }
    userStore.updateUser(res.data.user)
    
    // 检查是否需要强制修改密码
    if (res.data.must_change_password) {
      // 保存原始密码用于修改密码接口，然后清空表单防止浏览器保存临时密码
      originalPassword = form.password
      form.password = ''
      changePasswordVisible.value = true
      pwdForm.newPassword = ''
      pwdForm.confirmPassword = ''
    } else {
      // 正常登录，通过隐藏表单触发浏览器保存密码
      triggerBrowserSavePassword(form.username, form.password)
      ElMessage.success('Login successful')
      const redirect = route.query.redirect || '/'
      router.push(redirect)
    }
  } catch (error) {
    refreshCaptcha()
    console.error('Login failed:', error)
  } finally {
    loading.value = false
  }
}

const fetchCaptcha = async () => {
  try {
    const res = await fetch('/api/captcha')
    const data = await res.json()
    if (data.code === 200) {
      captchaId.value = data.data.captcha_id
      captchaImage.value = data.data.image
    }
  } catch (e) {
    console.error('获取验证码失败:', e)
  }
}

const refreshCaptcha = () => {
  captchaCode.value = ''
  fetchCaptcha()
}

const handleChangePassword = async () => {
  if (!pwdForm.newPassword) {
    ElMessage.warning('请输入新密码')
    return
  }
  if (pwdForm.newPassword.length < 8) {
    ElMessage.warning('密码长度不能少于8位')
    return
  }
  if (pwdForm.newPassword !== pwdForm.confirmPassword) {
    ElMessage.warning('两次输入的密码不一致')
    return
  }
  if (pwdForm.newPassword === originalPassword) {
    ElMessage.warning('新密码不能与当前密码相同')
    return
  }
  
  changingPassword.value = true
  try {
    await changePassword({
      old_password: originalPassword,
      new_password: pwdForm.newPassword
    })
    
    // 用 Credential Management API 主动通知浏览器保存新密码
    if (window.PasswordCredential) {
      try {
        const cred = new window.PasswordCredential({
          id: form.username,
          password: pwdForm.newPassword
        })
        await navigator.credentials.store(cred)
      } catch (e) {
        console.warn('PasswordCredential store failed:', e)
      }
    }
    
    // 通过隐藏表单提交触发浏览器密码管理器保存新密码
    triggerBrowserSavePassword(form.username, pwdForm.newPassword)
    
    // 修改成功，清除登录态
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    changePasswordVisible.value = false
    form.password = ''
    ElMessage.success('密码修改成功，请用新密码重新登录')
  } catch (error) {
    console.error('Change password failed:', error)
  } finally {
    changingPassword.value = false
  }
}

const handleCancelChange = () => {
  // 退出登录，清除 token
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  changePasswordVisible.value = false
  ElMessage.info('已退出，请修改密码后重新登录')
}

/**
 * 通过隐藏表单提交触发浏览器密码管理器保存凭据
 * 原理：浏览器在检测到带有 username + password 字段的表单提交时会弹出保存密码提示
 */
const triggerBrowserSavePassword = (username, password) => {
  // 方式1: Credential Management API（Chromium/Edge 支持）
  if (window.PasswordCredential) {
    try {
      const cred = new window.PasswordCredential({ id: username, password })
      navigator.credentials.store(cred)
    } catch (e) { /* ignore */ }
  }
  // 方式2: 隐藏表单提交到 iframe
  try {
    let iframe = document.getElementById('__pwd_save_frame')
    if (!iframe) {
      iframe = document.createElement('iframe')
      iframe.id = '__pwd_save_frame'
      iframe.name = '__pwd_save_frame'
      iframe.style.display = 'none'
      document.body.appendChild(iframe)
    }
    const f = document.createElement('form')
    f.action = 'about:blank'
    f.method = 'POST'
    f.target = '__pwd_save_frame'
    f.style.display = 'none'
    const u = document.createElement('input')
    u.type = 'text'
    u.name = 'username'
    u.autocomplete = 'username'
    u.value = username
    const p = document.createElement('input')
    p.type = 'password'
    p.name = 'password'
    p.autocomplete = 'current-password'
    p.value = password
    f.appendChild(u)
    f.appendChild(p)
    document.body.appendChild(f)
    f.submit()
    setTimeout(() => document.body.removeChild(f), 100)
  } catch (e) { /* ignore */ }
}

const handleRegister = async () => {
  if (!regForm.username || !regForm.username.trim()) {
    ElMessage.warning('Please enter a username')
    return
  }
  if (!regForm.password || regForm.password.length < 8) {
    ElMessage.warning('Password must be at least 8 characters')
    return
  }
  // 密码强度校验：大写、小写、数字、特殊字符中至少3种
  let cats = 0
  if (/[A-Z]/.test(regForm.password)) cats++
  if (/[a-z]/.test(regForm.password)) cats++
  if (/\d/.test(regForm.password)) cats++
  if (/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?`~]/.test(regForm.password)) cats++
  if (cats < 3) {
    ElMessage.warning('Password must contain at least 3 of: uppercase, lowercase, numbers, special characters')
    return
  }
  if (regForm.password !== regForm.confirmPassword) {
    ElMessage.warning('Passwords do not match')
    return
  }
  if (!regForm.email || !regForm.email.includes('@')) {
    ElMessage.warning('Please enter a valid email address')
    return
  }
  
  registerLoading.value = true
  try {
    const res = await register({
      username: regForm.username.trim(),
      password: regForm.password,
      email: regForm.email.trim(),
      full_name: regForm.full_name.trim() || undefined,
      phone: regForm.phone.trim() || undefined
    })
    ElMessage({
      type: 'success',
      duration: 15000,
      showClose: true,
      dangerouslyUseHTMLString: true,
      message: 'Registration submitted. Please wait for admin approval.<br/>注册申请已提交，请等待管理员审核。'
    })
    // 切回登录模式
    isRegisterMode.value = false
    form.username = regForm.username.trim()
    form.password = ''
    // 清空注册表单
    Object.assign(regForm, { username: '', password: '', confirmPassword: '', email: '', full_name: '', phone: '' })
  } catch (error) {
    console.error('Register failed:', error)
  } finally {
    registerLoading.value = false
  }
}
</script>

<style scoped>
.login-container {
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100%;
  background: linear-gradient(135deg, var(--primary-100) 0%, var(--primary-200) 100%);
  overflow: hidden;
}

.login-background {
  position: absolute;
  width: 100%;
  height: 100%;
  overflow: hidden;
}

.shape {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  animation: float 20s infinite ease-in-out;
}

.shape-1 {
  width: 300px;
  height: 300px;
  top: -100px;
  left: -100px;
  animation-delay: 0s;
}

.shape-2 {
  width: 200px;
  height: 200px;
  bottom: -50px;
  right: 100px;
  animation-delay: 2s;
}

.shape-3 {
  width: 150px;
  height: 150px;
  top: 50%;
  right: -50px;
  animation-delay: 4s;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0) rotate(0deg);
  }
  50% {
    transform: translateY(-20px) rotate(180deg);
  }
}

.login-card {
  position: relative;
  width: 450px;
  max-width: 90vw;
  max-height: 90vh;
  overflow-y: auto;
  padding: 50px 40px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  animation: slideUp 0.5s ease-out;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.login-header {
  text-align: center;
  margin-bottom: 40px;
}

.logo {
  margin-bottom: 20px;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.05);
  }
}

h1 {
  margin: 0 0 10px 0;
  font-size: 28px;
  font-weight: 600;
  color: var(--text-100);
  letter-spacing: 1px;
}

.subtitle {
  margin: 0;
  font-size: 14px;
  color: var(--text-200);
  font-weight: 300;
  letter-spacing: 2px;
}

.login-form {
  margin-bottom: 30px;
}

.login-form :deep(.el-form-item) {
  margin-bottom: 24px;
}

.login-form :deep(.el-input__wrapper) {
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.3s;
}

.login-form :deep(.el-input__wrapper:hover) {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.login-button {
  width: 100%;
  height: 48px;
  border-radius: 10px;
  font-size: 16px;
  font-weight: 500;
  letter-spacing: 2px;
  background: linear-gradient(135deg, var(--primary-100) 0%, var(--primary-200) 100%);
  border: none;
  transition: all 0.3s;
}

.login-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(1, 155, 152, 0.4);
}

.login-button:active {
  transform: translateY(0);
}

.password-toggle {
  cursor: pointer;
  color: #909399;
  transition: color 0.2s;
  font-size: 16px;
}

.password-toggle:hover {
  color: var(--primary-100);
}

.login-footer {
  text-align: center;
}

.login-footer :deep(.el-divider__text) {
  background-color: rgba(255, 255, 255, 0.95);
  color: #909399;
  font-size: 12px;
}

.default-accounts {
  display: flex;
  justify-content: center;
  gap: 10px;
  flex-wrap: wrap;
  margin-top: 15px;
}

.default-accounts .el-tag {
  cursor: pointer;
  transition: all 0.3s;
}

.default-accounts .el-tag:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.quick-tools {
  text-align: center;
}

.form-switch {
  text-align: center;
  margin-top: -8px;
  margin-bottom: 16px;
}

.switch-link {
  color: var(--primary-100);
  cursor: pointer;
  font-size: 14px;
  transition: opacity 0.2s;
}

.switch-link:hover {
  opacity: 0.8;
  text-decoration: underline;
}

.field-hint {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
  padding-left: 2px;
}

.tool-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--primary-100);
  text-decoration: none;
  font-size: 14px;
  padding: 8px 16px;
  border-radius: 8px;
  transition: all 0.3s;
  opacity: 0.8;
}

.tool-link:hover {
  opacity: 1;
  background: rgba(1, 155, 152, 0.08);
}

.tool-link .el-icon {
  font-size: 16px;
}

/* 验证码样式 */
.captcha-container {
  display: flex;
  gap: 10px;
  width: 100%;
  align-items: center;
}

.captcha-image {
  height: 40px;
  width: 120px;
  cursor: pointer;
  border-radius: 4px;
  border: 1px solid #dcdfe6;
  object-fit: cover;
}

.captcha-image:hover {
  border-color: var(--primary-100);
}

/* 强制修改密码对话框 */
:deep(.el-dialog) {
  border-radius: 16px;
  overflow: hidden;
}
:deep(.el-dialog__header) {
  padding: 20px 24px 16px;
  border-bottom: 1px solid #e2e8f0;
  margin-right: 0;
}
:deep(.el-dialog__title) {
  font-size: 18px;
  font-weight: 600;
  color: #0f172a;
}
:deep(.el-dialog__body) {
  padding: 24px;
}
:deep(.el-dialog__footer) {
  padding: 16px 24px;
  border-top: 1px solid #e2e8f0;
}

/* 低分辨率适配 */
@media screen and (max-height: 800px) {
  .login-card {
    padding: 30px 30px;
  }
  .login-header {
    margin-bottom: 20px;
  }
  .login-form :deep(.el-form-item) {
    margin-bottom: 16px;
  }
  .login-form {
    margin-bottom: 20px;
  }
  h1 {
    font-size: 24px;
  }
  .subtitle {
    font-size: 12px;
  }
}

@media screen and (max-height: 700px) {
  .login-card {
    padding: 20px 25px;
  }
  .login-header {
    margin-bottom: 15px;
  }
  .login-form :deep(.el-form-item) {
    margin-bottom: 12px;
  }
  .login-form {
    margin-bottom: 15px;
  }
}
</style>
