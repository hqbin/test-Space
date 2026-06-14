<template>
  <el-dialog
    v-model="visible"
    title="用例校对"
    width="95%"
    top="2vh"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    @close="handleClose"
  >
    <!-- 步骤条 V1.3: 支持Sheet选择步骤 -->
    <el-steps :active="activeStepIndex" finish-status="success" style="margin-bottom: 20px">
      <el-step title="上传文件" />
      <el-step title="选择Sheet" v-if="showSheetStep" />
      <el-step title="字段映射" v-if="needsMapping" />
      <el-step title="校对结果" />
    </el-steps>

    <!-- 步骤内容 -->
    <div class="step-content">
      <!-- 步骤1: 文件上传 -->
      <FileUploadStep
        v-if="currentStep === 'upload'"
        :project-id="projectId"
        :templates="templates"
        :loading="loading"
        @start-check="handleStartCheck"
      />

      <!-- V1.3 新增: 步骤1.5: Sheet选择 -->
      <SheetSelectionStep
        v-else-if="currentStep === 'sheet-selection'"
        :sheets="sheetsData.sheets"
        :recommended-sheet="sheetsData.recommended_sheet"
        :loading="loading"
        @select="handleSheetSelect"
        @confirm="handleSheetConfirm"
        @back="currentStep = 'upload'"
      />

      <!-- 步骤2: 字段映射 -->
      <FieldMappingStep
        v-else-if="currentStep === 'mapping' && needsMapping"
        :headers="checkResult.headers"
        :field-mapping="checkResult.field_mapping"
        :template-fields="checkResult.template_fields"
        :loading="loading"
        :header-row="selectedHeaderRow"
        @confirm="handleConfirmMapping"
        @back="handleMappingBack"
        @header-row-change="handleHeaderRowChange"
      />

      <!-- 步骤3: 校对结果 -->
      <ValidationResultStep
        v-else-if="currentStep === 'result'"
        :task-id="taskId"
        :check-result="checkResult"
        :loading="loading"
        @update-cell="handleUpdateCell"
        @apply-fix="handleApplyFix"
        @reset="handleReset"
        @export="handleExport"
        @refresh="fetchCheckResult"
        @back="handleResultBack"
      />
    </div>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import FileUploadStep from './FileUploadStep.vue'
import SheetSelectionStep from './SheetSelectionStep.vue'
import FieldMappingStep from './FieldMappingStep.vue'
import ValidationResultStep from './ValidationResultStep.vue'
import { getTemplates, getDefaultTemplate } from '@/api/caseTemplate'
import { getTeamByProject } from '@/api/team'
import {
  parseSheets,
  startCheck,
  getCheckResult,
  confirmMapping,
  updateCell,
  applyFix,
  resetToOriginal,
  exportResult
} from '@/api/caseCheck'

const props = defineProps({
  modelValue: Boolean,
  projectId: {
    type: Number,
    required: true
  }
})

const emit = defineEmits(['update:modelValue', 'success'])

// 状态
const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

// V1.3: 使用字符串标识步骤
const currentStep = ref('upload')
const loading = ref(false)
const templates = ref([])
const teamId = ref(null)
const taskId = ref(null)

// V1.3: Sheet选择相关状态
const sheetsData = ref({
  file_id: '',
  file_name: '',
  sheet_count: 0,
  sheets: [],
  recommended_sheet: ''
})
const selectedSheet = ref('')
const selectedHeaderRow = ref(1)
const selectedTemplateId = ref(null)
const selectedFile = ref(null)

// V1.3: 是否显示Sheet选择步骤
const showSheetStep = computed(() => sheetsData.value.sheet_count > 1)

// 计算当前步骤索引（用于步骤条显示）
const activeStepIndex = computed(() => {
  const steps = ['upload']
  if (showSheetStep.value) steps.push('sheet-selection')
  if (needsMapping.value) steps.push('mapping')
  steps.push('result')
  
  return steps.indexOf(currentStep.value)
})

const checkResult = ref({
  headers: [],
  field_mapping: {},
  template_fields: [],
  needs_mapping: false,
  statistics: {},
  rows: []
})

const needsMapping = computed(() => checkResult.value.needs_mapping)

// 加载模板列表
const loadTemplates = async () => {
  if (!props.projectId) {
    console.log('loadTemplates: projectId is empty')
    return
  }
  console.log('loadTemplates: projectId =', props.projectId)
  
  try {
    // 先根据 projectId 获取对应的 teamId
    const teamRes = await getTeamByProject(props.projectId)
    console.log('loadTemplates: teamRes =', teamRes)
    
    if (!teamRes.data) {
      console.log('loadTemplates: 该用例库未关联项目组')
      templates.value = []
      return
    }
    
    teamId.value = teamRes.data.id
    console.log('loadTemplates: teamId =', teamId.value)
    
    // 然后根据 teamId 获取模板列表
    const res = await getTemplates(teamId.value)
    console.log('loadTemplates: response =', res)
    templates.value = res.data || []
    console.log('loadTemplates: templates =', templates.value)
    
    // 获取默认模板
    const defaultRes = await getDefaultTemplate(teamId.value)
    console.log('loadTemplates: defaultRes =', defaultRes)
    if (defaultRes.data?.default_template) {
      // 标记默认模板
      templates.value = templates.value.map(t => ({
        ...t,
        isDefault: t.id === defaultRes.data.default_template.id
      }))
    }
  } catch (error) {
    console.error('加载模板失败:', error)
  }
}

// V1.3: 开始校对 - 先解析Sheet
const handleStartCheck = async ({ templateId, file }) => {
  loading.value = true
  selectedTemplateId.value = templateId
  selectedFile.value = file
  
  try {
    // 先解析Sheet列表
    const res = await parseSheets(props.projectId, file)
    sheetsData.value = res.data
    
    // 判断是否需要Sheet选择
    if (res.data.sheet_count > 1) {
      // 多Sheet，进入选择步骤
      selectedSheet.value = res.data.recommended_sheet || ''
      currentStep.value = 'sheet-selection'
    } else {
      // 单Sheet，直接开始校对
      const sheetName = res.data.sheets[0]?.name || null
      selectedHeaderRow.value = res.data.sheets[0]?.detected_header_row || 1
      await doStartCheck(templateId, res.data.file_id, sheetName, selectedHeaderRow.value)
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '解析文件失败')
  } finally {
    loading.value = false
  }
}

// V1.3: Sheet选择
const handleSheetSelect = (sheetName) => {
  selectedSheet.value = sheetName
  // 更新检测到的表头行
  const sheet = sheetsData.value.sheets.find(s => s.name === sheetName)
  if (sheet) {
    selectedHeaderRow.value = sheet.detected_header_row || 1
  }
}

// V1.3: 确认Sheet选择
const handleSheetConfirm = async ({ sheetName, detectedHeaderRow }) => {
  selectedSheet.value = sheetName
  selectedHeaderRow.value = detectedHeaderRow
  
  loading.value = true
  try {
    await doStartCheck(
      selectedTemplateId.value,
      sheetsData.value.file_id,
      sheetName,
      detectedHeaderRow
    )
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '校对失败')
  } finally {
    loading.value = false
  }
}

// V1.3: 实际执行校对
const doStartCheck = async (templateId, fileId, sheetName, headerRow) => {
  const res = await startCheck(props.projectId, templateId, null, {
    fileId,
    sheetName,
    headerRow
  })
  taskId.value = res.data.task_id
  
  // 轮询获取结果
  await fetchCheckResult()
  
  // 根据结果决定下一步
  if (checkResult.value.needs_mapping) {
    currentStep.value = 'mapping'
  } else {
    currentStep.value = 'result'
  }
}

// V1.3: 字段映射返回
const handleMappingBack = () => {
  if (showSheetStep.value) {
    currentStep.value = 'sheet-selection'
  } else {
    currentStep.value = 'upload'
  }
}

// V1.3: 从结果页返回
const handleResultBack = () => {
  if (showSheetStep.value) {
    currentStep.value = 'sheet-selection'
  } else if (checkResult.value.needs_mapping) {
    currentStep.value = 'mapping'
  } else {
    currentStep.value = 'upload'
  }
}

// V1.3: 表头行变更
const handleHeaderRowChange = async (newRow) => {
  selectedHeaderRow.value = newRow
  // 重新开始校对
  loading.value = true
  try {
    await doStartCheck(
      selectedTemplateId.value,
      sheetsData.value.file_id,
      selectedSheet.value || null,
      newRow
    )
  } catch (error) {
    ElMessage.error('更新表头行失败')
  } finally {
    loading.value = false
  }
}

// 获取校对结果
const fetchCheckResult = async () => {
  if (!taskId.value) return
  
  try {
    const res = await getCheckResult(taskId.value)
    checkResult.value = res.data
    
    // 如果还在处理中，继续轮询
    if (res.data.status === 'processing') {
      setTimeout(fetchCheckResult, 500)
    }
  } catch (error) {
    ElMessage.error('获取校对结果失败')
  }
}

// 确认字段映射
const handleConfirmMapping = async (mapping) => {
  loading.value = true
  try {
    await confirmMapping(taskId.value, mapping)
    await fetchCheckResult()
    currentStep.value = 'result'
  } catch (error) {
    ElMessage.error('确认映射失败')
  } finally {
    loading.value = false
  }
}

// 更新单元格
const handleUpdateCell = async ({ rowIndex, field, value }) => {
  try {
    const res = await updateCell(taskId.value, rowIndex, field, value)
    // 更新本地数据
    checkResult.value.rows[rowIndex] = res.data
    // 重新获取统计信息
    await fetchCheckResult()
  } catch (error) {
    ElMessage.error('更新失败')
  }
}

// 应用修复
const handleApplyFix = async ({ rowIndices, fixType }) => {
  loading.value = true
  try {
    const res = await applyFix(taskId.value, rowIndices, fixType)
    ElMessage.success(`已修复 ${res.data.fixed_count} 处问题`)
    await fetchCheckResult()
  } catch (error) {
    ElMessage.error('修复失败')
  } finally {
    loading.value = false
  }
}

// 重置
const handleReset = async () => {
  loading.value = true
  try {
    await resetToOriginal(taskId.value)
    await fetchCheckResult()
    ElMessage.success('已重置到原始数据')
  } catch (error) {
    ElMessage.error('重置失败')
  } finally {
    loading.value = false
  }
}

// 导出
const handleExport = async () => {
  loading.value = true
  try {
    const response = await exportResult(taskId.value)
    // response 是完整的 axios response 对象（因为 responseType: 'blob'）
    const blob = response.data || response
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    // 文件名包含 Sheet 名
    const baseName = checkResult.value.original_file_name?.replace(/\.[^.]+$/, '') || 'export'
    const sheetSuffix = selectedSheet.value ? `_${selectedSheet.value}` : ''
    link.download = `${baseName}${sheetSuffix}_校对后.xlsx`
    link.click()
    window.URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败')
  } finally {
    loading.value = false
  }
}

// 关闭对话框
const handleClose = () => {
  visible.value = false
  // 重置状态
  currentStep.value = 'upload'
  taskId.value = null
  sheetsData.value = {
    file_id: '',
    file_name: '',
    sheet_count: 0,
    sheets: [],
    recommended_sheet: ''
  }
  selectedSheet.value = ''
  selectedHeaderRow.value = 1
  selectedTemplateId.value = null
  selectedFile.value = null
  checkResult.value = {
    headers: [],
    field_mapping: {},
    template_fields: [],
    needs_mapping: false,
    statistics: {},
    rows: []
  }
}

// 监听对话框打开
watch(visible, (val) => {
  if (val) {
    loadTemplates()
  }
})
</script>

<style scoped>
.step-content {
  height: calc(90vh - 200px);
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}
</style>
