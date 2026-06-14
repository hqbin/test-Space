<template>
  <div class="testcase-detail-page">
    <div class="detail-header">
      <el-button :icon="ArrowLeft" @click="goBack">返回</el-button>
      <span class="header-title" v-if="testcase">{{ testcase.case_number }} - {{ testcase.name }}</span>
    </div>
    <div class="detail-body" v-loading="loading">
      <template v-if="testcase">
        <el-tabs v-model="activeTab">
          <el-tab-pane label="基本信息" name="basic">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="用例编号">
                <el-tag type="info" size="small">{{ testcase.case_number }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="用例类型">
                <el-tag :type="caseTypeTag(testcase.case_type).type" size="small">
                  {{ caseTypeTag(testcase.case_type).label }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="所属模块">{{ testcase.module || '-' }}</el-descriptions-item>
              <el-descriptions-item label="用例标题" :span="2">
                <div style="display: flex; align-items: center; gap: 8px;">
                  <el-icon color="#6366f1"><Document /></el-icon>
                  <span style="font-weight: 500;">{{ testcase.name }}</span>
                </div>
              </el-descriptions-item>
              <el-descriptions-item label="前置条件" :span="2">
                <div class="detail-section">{{ testcase.precondition || '-' }}</div>
              </el-descriptions-item>
              <el-descriptions-item label="操作步骤" :span="2">
                <div class="detail-section">
                  <div v-for="(step, i) in parsedSteps" :key="'s'+i" class="detail-step-item">
                    <span class="step-number">{{ i + 1 }}.</span>
                    <span class="step-text">{{ step }}</span>
                  </div>
                  <span v-if="parsedSteps.length === 0">{{ testcase.steps || '-' }}</span>
                </div>
              </el-descriptions-item>
              <el-descriptions-item label="预期结果" :span="2">
                <div class="detail-section">
                  <div v-for="(result, i) in parsedExpected" :key="'e'+i" class="detail-step-item">
                    <span class="step-number">{{ i + 1 }}.</span>
                    <span class="step-text">{{ result }}</span>
                  </div>
                  <span v-if="parsedExpected.length === 0">{{ testcase.expected_result || '-' }}</span>
                </div>
              </el-descriptions-item>
              <el-descriptions-item label="用例等级">
                <el-tag :type="getLevelType(testcase.level)" size="small">{{ testcase.level }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="自动化">
                <el-tag v-if="testcase.automation === 'Y'" type="success" size="small">{{ $t('testcase.automationY') }}</el-tag>
                <el-tag v-else-if="testcase.automation === 'D'" type="success" size="small">{{ $t('testcase.automationD') }}</el-tag>
                <el-tag v-else-if="testcase.automation && testcase.automation.startsWith('N-')" type="info" size="small">
                  {{ $t('testcase.automationNA') }} - {{ getAutomationLabel(testcase.automation) }}
                </el-tag>
                <el-tag v-else-if="testcase.automation === 'N'" type="info" size="small">{{ $t('testcase.automationN') }}</el-tag>
                <span v-else>-</span>
              </el-descriptions-item>
              <el-descriptions-item label="状态">
                <el-tag v-if="testcase.status === 'REVIEWED'" type="success" size="small">已评审</el-tag>
                <el-tag v-else-if="testcase.status === 'PENDING'" type="warning" size="small">待评审</el-tag>
                <el-tag v-else-if="testcase.status === 'REJECTED'" type="danger" size="small">未通过</el-tag>
                <el-tag v-else-if="testcase.status === 'DEPRECATED'" type="info" size="small">已废弃</el-tag>
                <span v-else>-</span>
              </el-descriptions-item>
              <el-descriptions-item label="备注" :span="2">
                <div class="detail-section">{{ testcase.remarks || '-' }}</div>
              </el-descriptions-item>
              <el-descriptions-item label="创建时间">{{ formatDateTime(testcase.created_at) }}</el-descriptions-item>
              <el-descriptions-item label="更新时间">{{ formatDateTime(testcase.updated_at) }}</el-descriptions-item>
            </el-descriptions>
          </el-tab-pane>
        </el-tabs>
      </template>
      <el-empty v-else-if="!loading" description="用例不存在" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Document } from '@element-plus/icons-vue'
import { getTestCaseDetail } from '@/api/testcase'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const testcase = ref(null)
const activeTab = ref('basic')

const CASE_TYPE_MAP = {
  COMMON: { label: '功能测试', type: '' },
  PERFORMANCE: { label: '性能测试', type: 'warning' },
  SECURITY: { label: '安全测试', type: 'danger' },
  INTERFACE: { label: '接口测试', type: 'success' },
  INSTALL: { label: '安装部署', type: 'info' },
  CONFIG: { label: '配置相关', type: 'info' },
  COMPATIBILITY: { label: '兼容性测试', type: 'success' },
  OTHER: { label: '其他', type: 'info' }
}
const caseTypeTag = (type) => CASE_TYPE_MAP[type] || { label: type || '未知', type: 'info' }

const parseJsonArray = (raw) => {
  if (!raw) return []
  try {
    const parsed = JSON.parse(raw)
    if (Array.isArray(parsed)) {
      return parsed.map(item => {
        if (typeof item === 'string') return item
        return item.step || item.text || item.result || item.expected || JSON.stringify(item)
      }).filter(Boolean)
    }
  } catch {}
  return raw.split('\n').filter(l => l.trim())
}

const parsedSteps = computed(() => {
  if (!testcase.value?.steps) return []
  try {
    const parsed = JSON.parse(testcase.value.steps)
    if (Array.isArray(parsed)) return parsed.map(item => item.step || item.text || String(item)).filter(Boolean)
  } catch {}
  return testcase.value.steps.split('\n').filter(l => l.trim())
})

const parsedExpected = computed(() => {
  if (!testcase.value) return []
  // Try steps JSON format first (has expected field)
  try {
    const parsed = JSON.parse(testcase.value.steps)
    if (Array.isArray(parsed) && parsed.length > 0 && parsed[0].expected) {
      return parsed.map(item => item.expected).filter(Boolean)
    }
  } catch {}
  // Fall back to expected_result field
  if (!testcase.value.expected_result) return []
  return parseJsonArray(testcase.value.expected_result)
})

const getLevelType = (level) => {
  const map = { L1: 'danger', L2: 'warning', L3: '', L4: 'info' }
  return map[level] || 'info'
}

const formatDateTime = (dt) => {
  if (!dt) return '-'
  try {
    return new Date(dt).toLocaleString('zh-CN')
  } catch { return dt }
}

const getAutomationLabel = (value) => {
  const map = {
    'N-HW_PHYSICAL': '硬件物理交互类',
    'N-VISUAL_JUDGE': '视觉主观判断类',
    'N-BOOT_PROCESS': '开机启动流程类',
    'N-MEDIA_PLAY': '媒体播放验证类',
    'N-OTA_UPGRADE': 'OTA升级专项类',
    'N-DATA_CONFIG': '数据配置核对类',
    'N-LOG_CHECK': '日志数据核对类',
    'N-BACKEND_CONFIG': '后台配置交互类',
    'N-DATA_DYNAMIC': '数据动态变化类',
    'N-OTHER_SPECIAL': '其他特殊场景类'
  }
  return map[value] || value
}

const goBack = () => {
  if (window.history.length > 1) {
    router.back()
  } else {
    router.push('/testcases')
  }
}

onMounted(async () => {
  const id = route.params.testcaseId
  if (!id) return
  loading.value = true
  try {
    const res = await getTestCaseDetail(id)
    testcase.value = res.data
    // 存储用例名称供数据埋点使用
    if (res.data.name) {
      sessionStorage.setItem(`testcase_name_${id}`, res.data.name)
    }
  } catch (e) {
    console.error('加载用例详情失败:', e)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.testcase-detail-page {
  max-width: 1000px;
  margin: 0 auto;
}
.detail-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}
.header-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}
.detail-body {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
  min-height: 400px;
}
.detail-section {
  white-space: pre-wrap;
  line-height: 1.8;
  color: #606266;
}
.detail-step-item {
  display: flex;
  gap: 6px;
  margin-bottom: 4px;
}
.step-number {
  color: #6366f1;
  font-weight: 600;
  flex-shrink: 0;
}
.step-text {
  color: #303133;
  white-space: pre-line;
}
</style>
