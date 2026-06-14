<template>
  <div class="user-profile-container">
    <el-card class="profile-card" shadow="never">
      <!-- 头像区域 -->
      <div class="avatar-section">
        <div 
          class="avatar-wrapper" 
          @mouseenter="showAvatarEdit = true"
          @mouseleave="showAvatarEdit = false"
          @click="handleAvatarClick"
        >
          <el-avatar :size="120" :src="userAvatar" class="user-avatar">
            <el-icon><User /></el-icon>
          </el-avatar>
          
          <!-- 上传进度 -->
          <div v-if="uploadingAvatar" class="avatar-uploading">
            <el-progress 
              type="circle" 
              :percentage="uploadProgress" 
              :width="80"
              :stroke-width="4"
            />
            <div class="upload-text">{{ $t('common.uploading') }}</div>
          </div>
          
          <!-- 悬停编辑提示 -->
          <div v-if="showAvatarEdit && !uploadingAvatar" class="avatar-overlay">
            <el-icon :size="24"><Edit /></el-icon>
            <div class="edit-text">{{ $t('profile.editAvatar') }}</div>
          </div>
        </div>
        
        <!-- 用户信息 -->
        <div class="user-info">
          <h2 class="user-name">{{ currentUser.username || $t('common.user') }}</h2>
        </div>
      </div>

      <!-- 基础信息 -->
      <div class="basic-info-section">
        <h3 class="section-title">
          <el-icon><User /></el-icon>
          {{ $t('profile.basicInfo') }}
        </h3>
        
        <el-form 
          ref="profileFormRef" 
          :model="profileForm" 
          label-width="100px"
          class="profile-form"
        >
          <el-form-item :label="$t('profile.username')">
            <el-input v-model="currentUser.username" disabled />
          </el-form-item>

          <el-form-item :label="$t('profile.fullName')">
            <el-input 
              v-model="profileForm.full_name" 
              :placeholder="$t('user.inputFullName')"
              :disabled="!editingProfile"
            />
          </el-form-item>

          <el-form-item :label="$t('profile.email')">
            <el-input 
              v-model="profileForm.email" 
              :placeholder="$t('user.inputEmail')"
              :disabled="!editingProfile"
            >
              <template #suffix>
                <span v-if="profileForm.email && !editingProfile" class="verified-badge">
                  <el-icon color="#67C23A"><CircleCheck /></el-icon>
                </span>
              </template>
            </el-input>
          </el-form-item>

          <el-form-item :label="$t('profile.phone')">
            <el-input 
              v-model="profileForm.phone" 
              :placeholder="$t('user.inputPhone')"
              :disabled="!editingProfile"
            />
          </el-form-item>

          <el-form-item :label="$t('profile.department')">
            <el-input 
              v-model="departmentsDisplay" 
              :placeholder="$t('profile.noDepartment')"
              disabled
            >
              <template #suffix>
                <el-tooltip :content="$t('profile.deptTip')" placement="top" :show-after="500">
                  <el-icon><InfoFilled /></el-icon>
                </el-tooltip>
              </template>
            </el-input>
          </el-form-item>

          <el-form-item :label="$t('profile.team')">
            <el-input 
              v-model="projectGroupsDisplay" 
              :placeholder="$t('profile.noTeam')"
              disabled
            >
              <template #suffix>
                <el-tooltip :content="$t('profile.teamTip')" placement="top" :show-after="500">
                  <el-icon><InfoFilled /></el-icon>
                </el-tooltip>
              </template>
            </el-input>
          </el-form-item>

          <el-form-item>
            <el-button 
              v-if="!editingProfile"
              type="primary" 
              @click="startEditProfile"
            >
              <el-icon><Edit /></el-icon>
              {{ $t('profile.editProfile') }}
            </el-button>
            <template v-else>
              <el-button 
                type="primary" 
                :loading="submittingProfile"
                @click="handleProfileSubmit"
              >
                <el-icon v-if="!submittingProfile"><Check /></el-icon>
                {{ submittingProfile ? $t('common.saving') : $t('profile.saveChanges') }}
              </el-button>
              <el-button @click="cancelEditProfile">{{ $t('common.cancel') }}</el-button>
            </template>
          </el-form-item>
        </el-form>
      </div>

      <!-- 分隔线 -->
      <el-divider />

      <!-- Zmind API Key配置区域 -->
      <div class="zmind-section">
        <h3 class="section-title">
          <el-icon><Link /></el-icon>
          {{ $t('profile.zmindIntegration') }}
        </h3>
        
        <!-- 未展开时显示按钮 -->
        <div v-if="!showZmindForm" class="zmind-prompt">
          <div class="prompt-content">
            <el-icon class="prompt-icon"><Link /></el-icon>
            <div class="prompt-text">
              <div class="prompt-title">{{ $t('profile.zmindApiKey') }}</div>
              <div class="prompt-desc">{{ $t('profile.zmindApiKeyDesc') }}</div>
              <div class="api-key-status">
                <el-icon v-if="currentUser.zmind_api_key"><CircleCheck /></el-icon>
                <el-icon v-else><CircleClose /></el-icon>
                {{ currentUser.zmind_api_key ? $t('profile.zmindConfigured') : $t('profile.zmindNotConfigured') }}
              </div>
            </div>
          </div>
          <el-button type="primary" @click="showZmindForm = true">
            <el-icon><Edit /></el-icon>
            {{ currentUser.zmind_api_key ? $t('profile.modifyConfig') : $t('profile.configApiKey') }}
          </el-button>
        </div>

        <!-- 展开后显示表单 -->
        <el-form 
          v-else
          ref="zmindFormRef" 
          :model="zmindForm" 
          label-width="120px"
          class="zmind-form"
        >
          <el-form-item :label="$t('profile.zmindApiKey')">
            <el-input
              v-model="zmindForm.zmind_api_key"
              type="password"
              :placeholder="$t('profile.inputApiKey')"
              show-password
              autocomplete="new-password"
            >
              <template #prefix>
                <el-icon><Key /></el-icon>
              </template>
            </el-input>
            <div class="form-tip">
              <el-icon><InfoFilled /></el-icon>
              <span>{{ $t('profile.apiKeyTip') }}</span>
            </div>
          </el-form-item>

          <el-form-item>
            <el-button 
              type="primary" 
              :loading="submittingZmind"
              @click="handleZmindSubmit"
            >
              <el-icon v-if="!submittingZmind"><Check /></el-icon>
              {{ submittingZmind ? $t('common.saving') : $t('profile.saveConfig') }}
            </el-button>
            <el-button @click="cancelZmindEdit">{{ $t('common.cancel') }}</el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- 分隔线 -->
      <el-divider />

      <!-- 密码修改区域 -->
      <div class="password-section">
        <h3 class="section-title">
          <el-icon><Lock /></el-icon>
          {{ $t('profile.security') }}
        </h3>
        
        <!-- 未展开时显示按钮 -->
        <div v-if="!showPasswordForm" class="password-prompt">
          <div class="prompt-content">
            <el-icon class="prompt-icon"><Lock /></el-icon>
            <div class="prompt-text">
              <div class="prompt-title">{{ $t('profile.changePassword') }}</div>
              <div class="prompt-desc">{{ $t('profile.changePasswordDesc') }}</div>
              <div class="last-change">
                <el-icon><Clock /></el-icon>
                {{ $t('profile.lastPasswordChange') }}：{{ lastPasswordChange }}
              </div>
            </div>
          </div>
          <el-button type="primary" @click="showPasswordForm = true">
            <el-icon><Edit /></el-icon>
            {{ $t('profile.changePassword') }}
          </el-button>
        </div>

        <!-- 展开后显示表单 -->
        <el-form 
          v-else
          ref="passwordFormRef" 
          :model="passwordForm" 
          :rules="formRules"
          label-width="100px"
          class="password-form"
        >
          <el-form-item :label="$t('profile.currentPassword')" prop="oldPassword">
            <el-input
              v-model="passwordForm.oldPassword"
              type="password"
              :placeholder="$t('profile.inputCurrentPassword')"
              show-password
              :class="{ 'shake-error': oldPasswordError }"
              @blur="validateOldPassword"
            >
              <template #prefix>
                <el-icon><Lock /></el-icon>
              </template>
            </el-input>
          </el-form-item>

          <el-form-item :label="$t('profile.newPassword')" prop="newPassword">
            <el-input
              v-model="passwordForm.newPassword"
              type="password"
              :placeholder="$t('profile.inputNewPassword')"
              show-password
              @input="checkPasswordStrength"
            >
              <template #prefix>
                <el-icon><Lock /></el-icon>
              </template>
            </el-input>
            
            <!-- 密码强度指示器 -->
            <div v-if="passwordForm.newPassword" class="password-strength">
              <div class="strength-bar">
                <div 
                  class="strength-fill" 
                  :class="`strength-${passwordStrength.level}`"
                  :style="{ width: passwordStrength.percentage + '%' }"
                ></div>
              </div>
              <span class="strength-text" :class="`strength-${passwordStrength.level}`">
                {{ passwordStrength.text }}
              </span>
            </div>
            
            <!-- 密码规则清单 -->
            <div v-if="passwordForm.newPassword" class="password-rules">
              <div class="rule-item" :class="{ 'rule-valid': rules.hasLength }">
                <span class="rule-icon">{{ rules.hasLength ? '✓' : '✗' }}</span>
                <span>{{ $t('profile.ruleLength') }}</span>
              </div>
              <div class="rule-item" :class="{ 'rule-valid': rules.hasLetter }">
                <span class="rule-icon">{{ rules.hasLetter ? '✓' : '✗' }}</span>
                <span>{{ $t('profile.ruleLetter') }}</span>
              </div>
              <div class="rule-item" :class="{ 'rule-valid': rules.hasNumber }">
                <span class="rule-icon">{{ rules.hasNumber ? '✓' : '✗' }}</span>
                <span>{{ $t('profile.ruleNumber') }}</span>
              </div>
            </div>
          </el-form-item>

          <el-form-item :label="$t('profile.confirmPassword')" prop="confirmPassword">
            <el-input
              v-model="passwordForm.confirmPassword"
              type="password"
              :placeholder="$t('profile.inputConfirmPassword')"
              show-password
            >
              <template #prefix>
                <el-icon><Lock /></el-icon>
              </template>
            </el-input>
          </el-form-item>

          <el-form-item>
            <el-button 
              type="primary" 
              :loading="submittingPassword"
              :disabled="!isPasswordFormValid"
              @click="handlePasswordSubmit"
            >
              <el-icon v-if="!submittingPassword"><Check /></el-icon>
              {{ submittingPassword ? $t('common.saving') : $t('profile.saveChanges') }}
            </el-button>
            <el-button @click="cancelPasswordEdit">{{ $t('common.cancel') }}</el-button>
          </el-form-item>
        </el-form>
      </div>
    </el-card>

    <!-- 头像操作面板 -->
    <el-dialog
      v-model="avatarDialogVisible"
      :title="$t('profile.editAvatar')"
      width="400px"
      :close-on-click-modal="false"
    >
      <div class="avatar-actions">
        <el-upload
          ref="uploadRef"
          :auto-upload="false"
          :show-file-list="false"
          :on-change="handleAvatarChange"
          accept="image/jpeg,image/png,image/gif,image/webp"
        >
          <el-button type="primary" :icon="Upload">
            {{ $t('profile.uploadAvatar') }}
          </el-button>
        </el-upload>
        
        <el-button 
          v-if="currentUser.avatar" 
          type="danger" 
          plain 
          :icon="Delete"
          @click="handleDeleteAvatar"
        >
          {{ $t('profile.deleteAvatar') }}
        </el-button>
      </div>
      
      <div class="upload-tips">
        <el-icon><InfoFilled /></el-icon>
        <span>{{ $t('profile.avatarTip') }}</span>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  User, Edit, Message, Phone, OfficeBuilding, Lock, Check, Clock,
  Upload, Delete, InfoFilled, CircleCheck, Link, Key, CircleClose
} from '@element-plus/icons-vue'
import { 
  changePassword, 
  uploadAvatar as uploadAvatarAPI, 
  deleteAvatar as deleteAvatarAPI, 
  getCurrentUser,
  updateProfile
} from '@/api/profile'
import { updateUserApiKey, getUserApiKey } from '@/api/zmind'
import { useUserStore } from '@/stores/user'
import { useLoadingStore } from '../../stores/loading'

import { useI18n } from 'vue-i18n'

const router = useRouter()
const userStore = useUserStore()
const loadingStore = useLoadingStore()
const { t } = useI18n()

// 当前用户信息
const currentUser = ref({})
const lastPasswordChange = ref('2024-02-10 14:30')

// 头像相关状态
const showAvatarEdit = ref(false)
const avatarDialogVisible = ref(false)
const uploadingAvatar = ref(false)
const uploadProgress = ref(0)
const uploadRef = ref(null)

// 个人资料编辑
const editingProfile = ref(false)
const submittingProfile = ref(false)
const profileFormRef = ref(null)
const profileForm = reactive({
  full_name: '',
  email: '',
  phone: ''
})

// 密码修改
const showPasswordForm = ref(false)
const passwordFormRef = ref(null)
const passwordForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})
const submittingPassword = ref(false)
const oldPasswordError = ref(false)

// Zmind API Key配置
const showZmindForm = ref(false)
const zmindFormRef = ref(null)
const zmindForm = reactive({
  zmind_api_key: ''
})
const submittingZmind = ref(false)

// 用户头像
const userAvatar = computed(() => {
  if (currentUser.value && currentUser.value.avatar) {
    if (currentUser.value.avatar.startsWith('data:')) {
      return currentUser.value.avatar
    }
    if (currentUser.value.avatar.startsWith('http')) {
      return currentUser.value.avatar
    }
    return `${currentUser.value.avatar}?t=${userStore.avatarTimestamp}`
  }
  const username = currentUser.value?.username || 'default'
  return `https://api.dicebear.com/7.x/avataaars/svg?seed=${username}`
})

// 组织显示
const departmentsDisplay = computed(() => {
  if (currentUser.value && currentUser.value.department_names && currentUser.value.department_names.length > 0) {
    return currentUser.value.department_names.join('、')
  }
  return t('profile.noDepartment')
})

// 项目组显示
const projectGroupsDisplay = computed(() => {
  if (currentUser.value && currentUser.value.team_names && currentUser.value.team_names.length > 0) {
    return currentUser.value.team_names.join('、')
  }
  return t('profile.noTeam')
})

// 密码强度
const passwordStrength = ref({
  level: 'weak',
  percentage: 0,
  text: '弱'
})

// 密码规则验证
const rules = reactive({
  hasLength: false,
  hasLetter: false,
  hasNumber: false
})

// 表单验证规则
const formRules = {
  oldPassword: [
    { required: true, message: t('profile.inputCurrentPassword'), trigger: 'blur' }
  ],
  newPassword: [
    { required: true, message: t('profile.inputNewPassword'), trigger: 'blur' },
    { min: 8, message: t('profile.passwordMinLength'), trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: t('profile.inputConfirmPassword'), trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== passwordForm.newPassword) {
          callback(new Error(t('profile.passwordMismatch')))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

// 表单是否有效
const isPasswordFormValid = computed(() => {
  return passwordForm.oldPassword && 
         passwordForm.newPassword && 
         passwordForm.confirmPassword &&
         passwordForm.newPassword === passwordForm.confirmPassword &&
         rules.hasLength &&
         rules.hasLetter &&
         rules.hasNumber
})

// 开始编辑个人资料
const startEditProfile = () => {
  editingProfile.value = true
}

// 取消编辑个人资料
const cancelEditProfile = () => {
  editingProfile.value = false
  // 恢复原始数据
  profileForm.full_name = currentUser.value.full_name || ''
  profileForm.email = currentUser.value.email || ''
  profileForm.phone = currentUser.value.phone || ''
}

// 提交个人资料
const handleProfileSubmit = async () => {
  submittingProfile.value = true
  
  try {
    await updateProfile({
      full_name: profileForm.full_name,
      email: profileForm.email,
      phone: profileForm.phone
    })
    
    // 重新加载完整的用户信息（包括角色、项目组等）
    await loadUserInfo()
    
    editingProfile.value = false
    ElMessage.success(t('profile.profileUpdateSuccess'))
  } catch (error) {
    const errorMsg = error.response?.data?.detail || t('profile.profileUpdateFailed')
    ElMessage.error(errorMsg)
  } finally {
    submittingProfile.value = false
  }
}

// 点击头像
const handleAvatarClick = () => {
  if (!uploadingAvatar.value) {
    avatarDialogVisible.value = true
  }
}

// 头像文件改变
const handleAvatarChange = (file) => {
  const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
  const isAllowed = allowedTypes.includes(file.raw.type)
  const isLt2M = file.raw.size / 1024 / 1024 < 10

  if (!isAllowed) {
    ElMessage.error(t('profile.avatarFormatError'))
    return
  }
  if (!isLt2M) {
    ElMessage.error(t('profile.avatarSizeError'))
    return
  }
  
  doUploadAvatar(file.raw)
}

// 上传头像
const doUploadAvatar = async (file) => {
  uploadingAvatar.value = true
  uploadProgress.value = 0
  avatarDialogVisible.value = false
  
  const progressInterval = setInterval(() => {
    if (uploadProgress.value < 90) {
      uploadProgress.value += 10
    }
  }, 200)
  
  try {
    const response = await uploadAvatarAPI(file)
    
    clearInterval(progressInterval)
    uploadProgress.value = 100
    
    // 重新加载完整的用户信息（包括角色、项目组等）
    await loadUserInfo()
    userStore.refreshAvatar()
    
    setTimeout(() => {
      uploadingAvatar.value = false
      uploadProgress.value = 0
      ElMessage.success('✓ ' + t('profile.avatarUpdated'))
    }, 500)
  } catch (error) {
    clearInterval(progressInterval)
    uploadingAvatar.value = false
    uploadProgress.value = 0
    
    const errorMsg = error.response?.data?.detail || '上传失败，请重试'
    ElMessage.error(errorMsg)
  }
}

// 删除头像
const handleDeleteAvatar = () => {
  ElMessageBox.confirm(t('profile.deleteAvatarConfirm'), t('common.tip'), {
    confirmButtonText: t('common.confirm'),
    cancelButtonText: t('common.cancel'),
    type: 'warning'
  }).then(async () => {
    try {
      await deleteAvatarAPI()
      
      // 重新加载完整的用户信息（包括角色、项目组等）
      await loadUserInfo()
      userStore.refreshAvatar()
      
      ElMessage.success(t('profile.avatarDeleted'))
      avatarDialogVisible.value = false
    } catch (error) {
      const errorMsg = error.response?.data?.detail || '删除失败，请重试'
      ElMessage.error(errorMsg)
    }
  }).catch(() => {})
}

// 验证旧密码
const validateOldPassword = async () => {
  if (!passwordForm.oldPassword) return
}

// 检查密码强度
const checkPasswordStrength = () => {
  const password = passwordForm.newPassword
  
  rules.hasLength = password.length >= 8
  rules.hasLetter = /[a-zA-Z]/.test(password)
  rules.hasNumber = /\d/.test(password)
  
  let strength = 0
  if (rules.hasLength) strength += 33
  if (rules.hasLetter) strength += 33
  if (rules.hasNumber) strength += 34
  
  passwordStrength.value.percentage = strength
  
  if (strength < 50) {
    passwordStrength.value.level = 'weak'
    passwordStrength.value.text = t('profile.passwordStrengthWeak')
  } else if (strength < 100) {
    passwordStrength.value.level = 'medium'
    passwordStrength.value.text = t('profile.passwordStrengthMedium')
  } else {
    passwordStrength.value.level = 'strong'
    passwordStrength.value.text = t('profile.passwordStrengthStrong')
  }
}

// 提交密码修改
const handlePasswordSubmit = async () => {
  if (!passwordFormRef.value) return
  
  await passwordFormRef.value.validate((valid) => {
    if (valid) {
      ElMessageBox.confirm(t('profile.changePasswordConfirm'), t('common.confirm'), {
        confirmButtonText: t('common.confirm'),
        cancelButtonText: t('common.cancel'),
        type: 'warning'
      }).then(async () => {
        submittingPassword.value = true
        
        try {
          await changePassword({
            old_password: passwordForm.oldPassword,
            new_password: passwordForm.newPassword
          })
          
          const now = new Date()
          lastPasswordChange.value = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')} ${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`
          
          ElMessageBox.alert(t('profile.passwordChangeSuccess'), t('common.success'), {
            confirmButtonText: t('common.confirm'),
            type: 'success',
            callback: () => {
              localStorage.removeItem('token')
              localStorage.removeItem('user')
              router.push('/login')
            }
          })
        } catch (error) {
          submittingPassword.value = false
          
          if (error.response?.data?.detail === '当前密码不正确') {
            oldPasswordError.value = true
            ElMessage.error(t('profile.passwordIncorrect'))
            setTimeout(() => {
              oldPasswordError.value = false
            }, 500)
          } else {
            ElMessage.error(t('profile.passwordChangeFailed'))
          }
        }
      }).catch(() => {})
    }
  })
}

// 取消密码修改
const cancelPasswordEdit = () => {
  showPasswordForm.value = false
  resetPasswordForm()
}

// 重置密码表单
const resetPasswordForm = () => {
  passwordFormRef.value?.resetFields()
  passwordForm.oldPassword = ''
  passwordForm.newPassword = ''
  passwordForm.confirmPassword = ''
  passwordStrength.value = { level: 'weak', percentage: 0, text: t('profile.passwordStrengthWeak') }
  rules.hasLength = false
  rules.hasUpperLower = false
  rules.hasNumber = false
}

// 提交Zmind配置
const handleZmindSubmit = async () => {
  if (!zmindForm.zmind_api_key || !zmindForm.zmind_api_key.trim()) {
    ElMessage.warning(t('profile.inputApiKey'))
    return
  }
  
  submittingZmind.value = true
  
  try {
    await updateUserApiKey({
      zmind_api_key: zmindForm.zmind_api_key
    })
    
    // 重新加载用户信息
    await loadUserInfo()
    
    showZmindForm.value = false
    // 清空表单
    zmindForm.zmind_api_key = ''
    ElMessage.success(t('profile.zmindConfigSuccess'))
  } catch (error) {
    const errorMsg = error.response?.data?.detail || t('profile.zmindConfigFailed')
    ElMessage.error(errorMsg)
  } finally {
    submittingZmind.value = false
  }
}

// 取消Zmind配置
const cancelZmindEdit = () => {
  showZmindForm.value = false
  // 清空表单,不显示原有的API Key
  zmindForm.zmind_api_key = ''
}

// 加载用户信息
const loadUserInfo = async () => {
  loadingStore.showLoading()
  try {
    console.log('=== 开始加载用户信息 ===')
    
    // 先从 localStorage 加载基本信息（用于快速显示）
    const storedUser = localStorage.getItem('user')
    if (storedUser) {
      const parsedUser = JSON.parse(storedUser)
      // 只加载基本字段，避免显示过期的角色信息
      currentUser.value = {
        ...parsedUser,
        role_name: parsedUser.role_name || '加载中...' // 显示加载中而不是未分配
      }
      console.log('从localStorage加载:', currentUser.value)
      // 初始化表单
      profileForm.full_name = parsedUser.full_name || ''
      profileForm.email = parsedUser.email || ''
      profileForm.phone = parsedUser.phone || ''
    }
    
    // 然后从 API 获取最新数据
    console.log('调用API获取最新数据...')
    const response = await getCurrentUser()
    console.log('API完整响应:', JSON.stringify(response, null, 2))
    console.log('response.data:', response.data)
    
    if (response.data) {
      console.log('用户数据:', JSON.stringify(response.data, null, 2))
      console.log('团队名称字段:', response.data.team_names)
      console.log('所有字段:', Object.keys(response.data))
      
      currentUser.value = response.data
      // 更新store和localStorage
      userStore.updateUser(response.data)
      // 更新表单
      profileForm.full_name = response.data.full_name || ''
      profileForm.email = response.data.email || ''
      profileForm.phone = response.data.phone || ''
    }
  } catch (error) {
    console.error('加载用户信息失败:', error)
    // 如果 API 失败，至少保留 localStorage 中的数据
    if (!currentUser.value.username) {
      const storedUser = localStorage.getItem('user')
      if (storedUser) {
        currentUser.value = JSON.parse(storedUser)
      }
    }
  } finally {
    loadingStore.hideLoading()
  }
}

onMounted(() => {
  loadUserInfo()
  // 不预填充Zmind API Key,保持为空
})
</script>

<style scoped>
.user-profile-container {
  max-width: 960px;
  margin: 0 auto;
  padding: 24px;
}

.profile-card {
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  border: none;
}

.avatar-section {
  text-align: center;
  padding: 32px 0;
}

.avatar-wrapper {
  position: relative;
  display: inline-block;
  cursor: pointer;
  margin-bottom: 16px;
}

.user-avatar {
  border: 3px solid #f0f0f0;
  transition: all 0.3s;
}

.avatar-wrapper:hover .user-avatar {
  border-color: #8b9aee;
}

.avatar-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #fff;
  transition: all 0.3s;
}

.edit-text {
  font-size: 12px;
  margin-top: 4px;
}

.avatar-uploading {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.upload-text {
  font-size: 12px;
  color: #86909C;
  margin-top: 8px;
}

.user-info {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.user-name {
  font-size: 18px;
  font-weight: 600;
  color: #1F2329;
  margin: 0;
}

.role-tag {
  background: #8b9aee;
  border: none;
  color: #fff;
  padding: 6px 16px;
  font-size: 14px;
}

.basic-info-section {
  margin-top: 24px;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #1F2329;
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 24px;
}

.profile-form {
  max-width: 600px;
}

.verified-badge {
  display: flex;
  align-items: center;
}

.password-section {
  margin-top: 24px;
}

.zmind-section {
  margin-top: 24px;
}

.zmind-prompt {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  background: #f7f8fa;
  border-radius: 8px;
}

.api-key-status {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #86909C;
  margin-top: 4px;
}

.zmind-form {
  max-width: 600px;
  margin-top: 16px;
}

.form-tip {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #86909C;
  margin-top: 4px;
}

.password-section {
  margin-top: 24px;
}

.password-prompt {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  background: #f7f8fa;
  border-radius: 8px;
}

.prompt-content {
  display: flex;
  gap: 16px;
  align-items: center;
}

.prompt-icon {
  font-size: 32px;
  color: #8b9aee;
}

.prompt-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.prompt-title {
  font-size: 16px;
  font-weight: 600;
  color: #1F2329;
}

.prompt-desc {
  font-size: 14px;
  color: #86909C;
}

.last-change {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #86909C;
  margin-top: 4px;
}

.password-form {
  max-width: 600px;
  margin-top: 16px;
}

.shake-error {
  animation: shake 0.5s;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
  20%, 40%, 60%, 80% { transform: translateX(5px); }
}

.password-strength {
  margin-top: 8px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.strength-bar {
  flex: 1;
  height: 4px;
  background: #f0f0f0;
  border-radius: 2px;
  overflow: hidden;
}

.strength-fill {
  height: 100%;
  transition: all 0.3s;
}

.strength-fill.strength-weak {
  background: #f56c6c;
}

.strength-fill.strength-medium {
  background: #e6a23c;
}

.strength-fill.strength-strong {
  background: #67c23a;
}

.strength-text {
  font-size: 12px;
  font-weight: 500;
  min-width: 20px;
}

.strength-text.strength-weak {
  color: #f56c6c;
}

.strength-text.strength-medium {
  color: #e6a23c;
}

.strength-text.strength-strong {
  color: #67c23a;
}

.password-rules {
  display: flex;
  gap: 16px;
  margin-top: 8px;
}

.rule-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #86909C;
}

.rule-item.rule-valid {
  color: #67c23a;
}

.rule-icon {
  font-size: 14px;
  font-weight: bold;
}

.avatar-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 16px;
}

.upload-tips {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #86909C;
  padding: 12px;
  background: #f7f8fa;
  border-radius: 4px;
}

@media (max-width: 768px) {
  .profile-form {
    max-width: 100%;
  }
  
  .password-form {
    max-width: 100%;
  }
  
  .password-prompt {
    flex-direction: column;
    gap: 16px;
  }
}
</style>
