<template>
  <div class="flex flex-1 min-h-0 overflow-hidden pb-4 box-border select-none flex-col gap-3">
    <!-- 顶部：仅用于切换分页 Tab（后续可扩展其它平台） -->
    <div class="glass-panel rounded-xl p-2 px-3 flex items-center gap-2 flex-nowrap shrink-0">
      <div class="flex gap-1 shrink-0">
        <button v-for="tab in tabs" :key="tab.key"
          class="glass-hover rounded-md px-3 py-1.5 flex items-center gap-1.5 text-label-md font-label-md select-none"
          :class="activeTab === tab.key ? 'glass-active font-semibold' : 'text-graphite'"
          @click="activeTab = tab.key">
          <span class="material-symbols-outlined text-[15px]"
            :style="{ fontVariationSettings: `'FILL' ${activeTab === tab.key ? 1 : 0}` }">{{ tab.icon }}</span>
          <span class="text-[12px] font-semibold tracking-wide whitespace-nowrap">{{ tab.label }}</span>
        </button>
      </div>
    </div>

    <!-- 启动中：正在尝试恢复上次会话 -->
    <div v-if="booting" class="flex-1 glass-panel rounded-xl flex items-center justify-center">
      <span class="w-4 h-4 border-2 border-secondary border-t-transparent rounded-full animate-spin"></span>
    </div>

    <!-- 未登录：登录卡片 -->
    <div v-else-if="!loggedIn" class="flex-1 glass-panel rounded-xl flex items-center justify-center overflow-y-auto custom-scrollbar">
      <div class="w-[372px] p-7 flex flex-col gap-3.5">
        <div class="flex items-center gap-2">
          <span class="material-symbols-outlined text-[22px] text-secondary">passkey</span>
          <span class="text-[14px] font-semibold text-on-surface">{{ t('backend.needLogin') }}</span>
        </div>

        <div class="flex flex-col gap-1.5">
          <span class="text-[11px] text-on-surface-variant">{{ t('backend.env') }}</span>
          <div class="flex rounded-full border border-outline-variant/50 overflow-hidden">
            <button v-for="e in envOptions" :key="e.key"
              class="flex-1 px-3 py-1.5 text-[12px] transition-colors tracking-wide"
              :class="env === e.key ? 'bg-secondary/15 text-secondary font-semibold' : 'text-on-surface-variant hover:bg-secondary/5'"
              @click="switchEnv(e.key)">{{ e.label }}</button>
          </div>
        </div>

        <div class="flex flex-col gap-1.5">
          <span class="text-[11px] text-on-surface-variant">{{ t('backend.account') }}</span>
          <input v-model="email" type="text" autocomplete="username" spellcheck="false"
            class="glass-input px-3 py-2 rounded-lg text-[12px] text-on-surface select-text"
            :placeholder="t('backend.account')" />
        </div>

        <div class="flex flex-col gap-1.5">
          <span class="text-[11px] text-on-surface-variant">{{ t('backend.password') }}</span>
          <input v-model="password" type="password" autocomplete="current-password"
            class="glass-input px-3 py-2 rounded-lg text-[12px] text-on-surface select-text"
            :placeholder="t('backend.password')" @keyup.enter="doLogin" />
        </div>

        <button class="glass-button rounded-lg px-4 py-2 text-[12px] font-semibold flex items-center justify-center gap-1.5"
          :disabled="busy" @click="doLogin">
          <span v-if="busy" class="w-3 h-3 border-2 border-secondary border-t-transparent rounded-full animate-spin"></span>
          <span v-else class="material-symbols-outlined text-[15px]">login</span>
          {{ busy ? t('backend.loggingIn') : t('backend.login') }}
        </button>

        <div v-if="message" class="text-[11px] text-center truncate" :class="messageType === 'error' ? 'text-error' : 'text-success-indicator'">{{ message }}</div>
      </div>
    </div>

    <!-- 已登录 -->
    <div v-else class="flex-1 min-h-0 overflow-hidden">
      <AdConfigTab :key="sessionVersion" :env="env" :can-write="true"
        @session-expired="onSessionExpired"
        @logout="doLogout"
        @switch-env="switchEnv(env === 'acc' ? 'prod' : 'acc')" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from '@/composables/useI18n'
import {
  loadSspCredential,
  loadSspPrefs,
  restoreSspSession,
  saveSspCredential,
  saveSspEnv,
  sspLogin,
  sspLogout,
  type SspCredential,
  type SspEnv,
} from '@/services/sspApi'
import AdConfigTab from './AdConfigTab.vue'

defineOptions({ name: 'BackendSpacePage' })

const { t } = useI18n()

const activeTab = ref('ads')
const tabs = computed(() => [
  { key: 'ads', label: t('backend.tabAds'), icon: 'campaign' },
])

const env = ref<SspEnv>('acc')
const envOptions = computed(() => [
  { key: 'acc' as SspEnv, label: t('backend.acc') },
  { key: 'prod' as SspEnv, label: t('backend.prod') },
])
const email = ref('')
const password = ref('')
/** ACC / PROD 各存一份账号，切换环境时同步切账号 */
const accounts = ref<Record<SspEnv, SspCredential>>({
  acc: { email: '', password: '' },
  prod: { email: '', password: '' },
})
const busy = ref(false)
const loggedIn = ref(false)
const booting = ref(true)
const sessionVersion = ref(0)
const message = ref('')
const messageType = ref<'success' | 'error'>('success')
let messageTimer: number | null = null

function showMessage(text: string, type: 'success' | 'error' = 'success') {
  message.value = text
  messageType.value = type
  if (messageTimer) window.clearTimeout(messageTimer)
  messageTimer = window.setTimeout(() => { message.value = '' }, 6000)
}

function errText(e: unknown): string {
  return e instanceof Error ? e.message : String(e)
}

/** 把当前输入框内容写回对应环境的账号槽 */
function stashCredential() {
  accounts.value[env.value] = { email: email.value.trim(), password: password.value }
}

/** 切换环境时把输入框换成该环境已保存的账号 */
function applyCredential(next: SspEnv) {
  const cred = accounts.value[next] || { email: '', password: '' }
  email.value = cred.email
  password.value = cred.password
}

async function doLogin() {
  if (busy.value) return
  if (!email.value.trim() || !password.value) {
    showMessage(t('backend.account') + ' / ' + t('backend.password'), 'error')
    return
  }
  busy.value = true
  try {
    await sspLogin(env.value, email.value.trim(), password.value)
    accounts.value[env.value] = { email: email.value.trim(), password: password.value }
    // 账号密码按环境持久化，下次进来 / 切环境自动带出
    await saveSspCredential(env.value, email.value.trim(), password.value)
    loggedIn.value = true
    sessionVersion.value++
    message.value = ''
  } catch (e) {
    showMessage(errText(e), 'error')
  } finally {
    busy.value = false
  }
}

async function doLogout() {
  stashCredential()
  await sspLogout()
  loggedIn.value = false
  sessionVersion.value++
  message.value = ''
}

async function switchEnv(next: SspEnv) {
  if (next === env.value) return
  stashCredential()
  env.value = next
  applyCredential(next)
  void saveSspEnv(next)
  if (loggedIn.value) await doLogout()
}

function onSessionExpired() {
  stashCredential()
  loggedIn.value = false
  sessionVersion.value++
  void sspLogout()
  showMessage(t('backend.sessionExpired'), 'error')
}

onMounted(async () => {
  try {
    const prefs = await loadSspPrefs()
    accounts.value = prefs.accounts
    env.value = prefs.env
    applyCredential(prefs.env)
  } catch {
    // 读取失败不阻塞页面
  }
  // 热更新 / 重启后恢复上次会话，避免每次改动都被踢回登录页
  try {
    const restored = await restoreSspSession()
    if (restored) {
      env.value = restored.env
      email.value = restored.email
      // 会话里的账号优先，密码仍取本地保存的那份
      const cred = await loadSspCredential(restored.env).catch(() => null)
      password.value = cred?.password || ''
      accounts.value[restored.env] = { email: restored.email, password: password.value }
      loggedIn.value = true
      sessionVersion.value++
    }
  } catch {
    // 恢复失败保持登录页
  } finally {
    booting.value = false
  }
})
</script>
