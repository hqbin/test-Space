<template>
  <div class="aivoice-settings">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>Azure OpenAI 配置</span>
          <el-tag v-if="connectionStatus === 'success'" type="success" size="small">连接正常</el-tag>
          <el-tag v-else-if="connectionStatus === 'fail'" type="danger" size="small">连接失败</el-tag>
        </div>
      </template>
      <el-form :model="form" label-width="160px">
        <el-form-item label="API Endpoint">
          <el-input v-model="form.azureEndpoint" placeholder="https://your-resource.openai.azure.com" />
        </el-form-item>
        <el-form-item label="API Key">
          <el-input v-model="form.azureApiKey" type="password" show-password placeholder="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" />
        </el-form-item>
        <el-form-item label="Deployment Name">
          <el-input v-model="form.azureDeployment" placeholder="gpt-4o" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="saveSettings" :loading="saving">保存</el-button>
          <el-button @click="testConnection" :loading="testing">
            <el-icon><Connection /></el-icon>测试连接
          </el-button>
        </el-form-item>
      </el-form>

      <!-- 测试结果 -->
      <div v-if="testResult" class="test-result" :class="testResult.success ? 'success' : 'error'">
        <div class="test-result-header">
          <el-icon v-if="testResult.success"><CircleCheck /></el-icon>
          <el-icon v-else><CircleClose /></el-icon>
          <span>{{ testResult.success ? '连接成功' : '连接失败' }}</span>
        </div>
        <div class="test-result-body">
          <div v-if="testResult.model" class="result-item"><label>模型：</label><span>{{ testResult.model }}</span></div>
          <div v-if="testResult.responseTime" class="result-item"><label>响应时间：</label><span>{{ testResult.responseTime }}ms</span></div>
          <div v-if="testResult.error" class="result-item error-text"><label>错误：</label><span>{{ testResult.error }}</span></div>
          <div v-if="testResult.hint" class="result-item hint-text"><label>建议：</label><span>{{ testResult.hint }}</span></div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Connection, CircleCheck, CircleClose } from '@element-plus/icons-vue'
import { getAiVoiceSetting, updateAiVoiceSetting } from '@/api/aivoice'
import request from '@/api/request'

const form = ref({ azureEndpoint: '', azureApiKey: '', azureDeployment: '' })
const saving = ref(false)
const testing = ref(false)
const testResult = ref(null)
const connectionStatus = ref('')

const KEYS = {
  azureEndpoint: 'azure_openai_endpoint',
  azureApiKey: 'azure_openai_api_key',
  azureDeployment: 'azure_openai_deployment',
}

onMounted(async () => {
  try {
    const [ep, key, dep] = await Promise.all([
      getAiVoiceSetting(KEYS.azureEndpoint),
      getAiVoiceSetting(KEYS.azureApiKey),
      getAiVoiceSetting(KEYS.azureDeployment),
    ])
    form.value.azureEndpoint = ep.data || ''
    form.value.azureApiKey = key.data || ''
    form.value.azureDeployment = dep.data || ''
  } catch (e) { console.error(e) }
})

const saveSettings = async () => {
  saving.value = true
  try {
    await Promise.all([
      updateAiVoiceSetting(KEYS.azureEndpoint, form.value.azureEndpoint),
      updateAiVoiceSetting(KEYS.azureApiKey, form.value.azureApiKey),
      updateAiVoiceSetting(KEYS.azureDeployment, form.value.azureDeployment),
    ])
    ElMessage.success('保存成功')
  } catch (e) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

const testConnection = async () => {
  if (!form.value.azureEndpoint || !form.value.azureApiKey || !form.value.azureDeployment) {
    ElMessage.warning('请先填写完整配置信息')
    return
  }

  testing.value = true
  testResult.value = null
  connectionStatus.value = ''

  try {
    const res = await request.post('/aivoice/ai-recommend/test-connection', {
      endpoint: form.value.azureEndpoint,
      apiKey: form.value.azureApiKey,
      deployment: form.value.azureDeployment,
      apiVersion: '2024-12-01-preview'
    })
    testResult.value = res.data
    connectionStatus.value = res.data?.success ? 'success' : 'fail'
  } catch (e) {
    // 后端路由不存在或服务未重启
    const detail = e?.response?.data?.detail || e?.message || '请求失败'
    if (detail === 'Not Found' || e?.response?.status === 404) {
      testResult.value = {
        success: false,
        error: '后端接口未找到 (404)',
        hint: '请重启后端服务（python main.py），使新接口生效。'
      }
    } else {
      testResult.value = {
        success: false,
        error: detail,
        hint: '请检查网络连接或后端服务是否正常运行'
      }
    }
    connectionStatus.value = 'fail'
  } finally {
    testing.value = false
  }
}
</script>

<style scoped>
.aivoice-settings { padding: 20px; max-width: 700px; }

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.test-result {
  margin-top: 20px;
  padding: 16px;
  border-radius: 8px;
  border: 1px solid;
}

.test-result.success {
  background: #f0f9ff;
  border-color: #b3e0d2;
}

.test-result.error {
  background: #fef0f0;
  border-color: #fbc4c4;
}

.test-result-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 15px;
  margin-bottom: 12px;
}

.test-result.success .test-result-header { color: #67c23a; }
.test-result.error .test-result-header { color: #f56c6c; }

.test-result-body { font-size: 13px; }

.result-item {
  margin-bottom: 6px;
  display: flex;
  gap: 4px;
}

.result-item label {
  color: #909399;
  flex-shrink: 0;
}

.error-text span { color: #f56c6c; word-break: break-all; }
.hint-text span { color: #e6a23c; }
</style>
