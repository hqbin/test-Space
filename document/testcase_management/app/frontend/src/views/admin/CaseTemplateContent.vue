<template>
  <div class="template-management">
    <div class="content-header">
      <div class="header-actions">
        <el-button type="primary" @click="handleUpload" :disabled="!currentTeamId">
          <el-icon><Upload /></el-icon>
          上传模板
        </el-button>
      </div>
    </div>

      <!-- 表格 -->
      <div class="table-wrapper">
        <el-table
          :data="templates"
          style="width: 100%"
          border
          v-loading="loading"
        >
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="name" label="模板名称" min-width="150" />
          <el-table-column prop="file_name" label="文件名" min-width="180" :show-overflow-tooltip="{ showAfter: 500 }" />
          <el-table-column prop="field_count" label="字段数" width="100" align="center">
            <template #default="{ row }">
              <el-tag type="info">{{ row.field_count }} 个</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="is_default" label="默认" width="100" align="center">
            <template #default="{ row }">
              <el-tag v-if="row.is_default" type="success">默认</el-tag>
              <span v-else style="color: #909399;">-</span>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="180">
            <template #default="{ row }">
              {{ formatDate(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column prop="created_by_name" label="创建人" width="120" />
          <el-table-column label="操作" width="280">
            <template #default="{ row }">
              <el-button link type="primary" @click="handleEdit(row)">
                <el-icon><Edit /></el-icon>
                配置
              </el-button>
              <el-button link type="success" @click="handleSetDefault(row)" :disabled="row.is_default">
                <el-icon><Star /></el-icon>
                设为默认
              </el-button>
              <el-button link type="warning" @click="handleDownload(row)">
                <el-icon><Download /></el-icon>
                下载
              </el-button>
              <el-button link type="danger" @click="handleDelete(row)">
                <el-icon><Delete /></el-icon>
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <el-empty v-if="!currentTeamId" description="请先选择项目组" />

    <!-- 上传对话框 -->
    <el-dialog 
      v-model="uploadDialogVisible" 
      title="上传模板" 
      width="500px"
      destroy-on-close
      :close-on-click-modal="false"
      class="template-upload-dialog"
    >
      <el-form :model="uploadForm" label-width="80px">
        <el-form-item label="模板名称">
          <el-input v-model="uploadForm.name" placeholder="留空则使用文件名" />
        </el-form-item>
        <el-form-item label="模板文件" required>
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="1"
            accept=".xlsx,.xls"
            :on-change="handleFileChange"
            :on-exceed="handleExceed"
            drag
            class="upload-dragger"
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">
              拖拽文件到此处，或<em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                支持 .xlsx, .xls 格式
              </div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="uploadDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitUpload" :loading="uploading">
            上传并解析
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 字段配置对话框 -->
    <el-dialog v-model="configDialogVisible" title="配置字段规则" width="800px" class="template-config-dialog">
      <el-form :model="configForm" label-width="80px">
        <el-form-item label="模板名称">
          <el-input v-model="configForm.name" />
        </el-form-item>
      </el-form>
      
      <el-table :data="configForm.fields" border style="margin-top: 16px">
        <el-table-column prop="original_name" label="原始名称" width="150" />
        <el-table-column label="显示名称" width="150">
          <template #default="{ row }">
            <el-input v-model="row.name" size="small" />
          </template>
        </el-table-column>
        <el-table-column label="必填" width="80" align="center">
          <template #default="{ row }">
            <el-checkbox v-model="row.required" />
          </template>
        </el-table-column>
        <el-table-column label="类型" width="120">
          <template #default="{ row }">
            <el-select v-model="row.field_type" size="small">
              <el-option label="文本" value="string" />
              <el-option label="长文本" value="text" />
              <el-option label="枚举" value="enum" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="枚举值">
          <template #default="{ row }">
            <el-input
              v-if="row.field_type === 'enum'"
              v-model="row.enum_values_str"
              size="small"
              placeholder="用逗号分隔，如: L1,L2,L3,L4"
            />
            <span v-else style="color: #909399;">-</span>
          </template>
        </el-table-column>
      </el-table>

      <template #footer>
        <el-button @click="configDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitConfig" :loading="saving">
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload, UploadFilled, Edit, Star, Download, Delete } from '@element-plus/icons-vue'
import {
  getTemplates,
  createTemplate,
  getTemplate,
  updateTemplate,
  deleteTemplate,
  setDefaultTemplate,
  downloadTemplate
} from '@/api/caseTemplate'
import { useTeam } from '@/composables/useTeam'

const { currentTeam } = useTeam()
const currentTeamId = computed(() => currentTeam.value?.id || null)

// 状态
const loading = ref(false)
const uploading = ref(false)
const saving = ref(false)
const templates = ref([])

// 上传对话框
const uploadDialogVisible = ref(false)
const uploadRef = ref(null)
const uploadForm = ref({
  name: '',
  file: null
})

// 配置对话框
const configDialogVisible = ref(false)
const configForm = ref({
  id: null,
  name: '',
  fields: []
})

// 加载模板列表
const loadTemplates = async () => {
  if (!currentTeamId.value) {
    templates.value = []
    return
  }
  
  loading.value = true
  try {
    const res = await getTemplates(currentTeamId.value)
    // 后端返回格式: { code: 200, data: [...] }
    templates.value = res.data || []
  } catch (error) {
    console.error('加载模板失败:', error)
    ElMessage.error('加载模板失败')
  } finally {
    loading.value = false
  }
}

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

// 上传相关
const handleUpload = () => {
  uploadForm.value = { name: '', file: null }
  uploadDialogVisible.value = true
}

const handleFileChange = (file) => {
  uploadForm.value.file = file.raw
}

const handleExceed = () => {
  ElMessage.warning('只能上传一个文件')
}

const submitUpload = async () => {
  if (!uploadForm.value.file) {
    ElMessage.warning('请选择文件')
    return
  }
  
  uploading.value = true
  try {
    await createTemplate(currentTeamId.value, uploadForm.value.file, uploadForm.value.name)
    ElMessage.success('模板上传成功')
    uploadDialogVisible.value = false
    loadTemplates()
  } catch (error) {
    console.error('上传失败:', error)
    ElMessage.error(error.response?.data?.detail || '上传失败')
  } finally {
    uploading.value = false
  }
}

// 配置相关
const handleEdit = async (row) => {
  try {
    const res = await getTemplate(row.id)
    const template = res.data
    configForm.value = {
      id: template.id,
      name: template.name,
      fields: template.fields.map(f => ({
        ...f,
        enum_values_str: f.enum_values ? f.enum_values.join(',') : ''
      }))
    }
    configDialogVisible.value = true
  } catch (error) {
    ElMessage.error('获取模板详情失败')
  }
}

const submitConfig = async () => {
  saving.value = true
  try {
    const fields = configForm.value.fields.map(f => ({
      ...f,
      enum_values: f.field_type === 'enum' && f.enum_values_str
        ? f.enum_values_str.split(',').map(v => v.trim()).filter(v => v)
        : null
    }))
    
    await updateTemplate(configForm.value.id, {
      name: configForm.value.name,
      fields
    })
    ElMessage.success('保存成功')
    configDialogVisible.value = false
    loadTemplates()
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

// 设为默认
const handleSetDefault = async (row) => {
  try {
    await setDefaultTemplate(row.id)
    ElMessage.success('已设为默认模板')
    loadTemplates()
  } catch (error) {
    ElMessage.error('设置失败')
  }
}

// 下载
const handleDownload = async (row) => {
  try {
    const res = await downloadTemplate(row.id)
    const blob = new Blob([res.data], { type: res.headers['content-type'] || 'application/octet-stream' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = row.file_name
    link.click()
    window.URL.revokeObjectURL(url)
  } catch (error) {
    ElMessage.error('下载失败')
  }
}

// 删除
const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除该模板吗？', '提示', {
      type: 'warning'
    })
    await deleteTemplate(row.id)
    ElMessage.success('删除成功')
    loadTemplates()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

onMounted(() => {
  if (currentTeamId.value) loadTemplates()
})

watch(() => currentTeam.value?.id, () => {
  loadTemplates()
})
</script>

<style scoped>
.template-management {
  padding: 0;
  height: 100%;
  overflow-y: auto;
}

.header-actions {
  display: flex;
  align-items: center;
}

.table-wrapper {
  margin-top: 16px;
}
</style>

<!-- 对话框样式需要不使用 scoped，因为对话框是 teleport 到 body 的 -->
<style>
/* 上传对话框样式 */
.template-upload-dialog .el-dialog__body {
  padding: 20px;
  overflow: visible;
}

.template-upload-dialog .el-form {
  width: 100%;
}

.template-upload-dialog .el-form-item {
  margin-bottom: 22px;
}

.template-upload-dialog .el-upload {
  width: 100%;
  display: block;
}

.template-upload-dialog .el-upload-dragger {
  width: 100%;
  min-height: 150px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  border: 1px dashed #d9d9d9;
  border-radius: 6px;
  background: #fafafa;
  /* 重置 performance.css 的影响 */
  transform: none !important;
  backface-visibility: visible !important;
}

.template-upload-dialog .el-upload-dragger:hover {
  border-color: #409eff;
}

.template-upload-dialog .el-icon--upload {
  font-size: 48px;
  color: #c0c4cc;
  margin-bottom: 8px;
}

.template-upload-dialog .el-upload__text {
  color: #606266;
  font-size: 14px;
}

.template-upload-dialog .el-upload__text em {
  color: #409eff;
  font-style: normal;
}

.template-upload-dialog .el-upload__tip {
  margin-top: 8px;
  color: #909399;
  font-size: 12px;
  line-height: 1.5;
}

.template-upload-dialog .el-upload-list {
  margin-top: 10px;
}

.template-upload-dialog .el-dialog__footer {
  padding: 10px 20px 20px;
  border-top: 1px solid #ebeef5;
}

/* 配置对话框样式 */
.template-config-dialog .el-dialog__body {
  padding: 20px;
}

.template-config-dialog .el-table {
  margin-top: 16px;
}
</style>
