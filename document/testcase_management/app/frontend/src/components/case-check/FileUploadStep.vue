<template>
  <div class="file-upload-step">
    <el-form label-width="100px">
      <el-form-item label="选择模板" required>
        <el-select
          v-model="selectedTemplateId"
          placeholder="请选择模板"
          style="width: 300px"
        >
          <el-option
            v-for="template in templates"
            :key="template.id"
            :label="template.name + (template.is_default || template.isDefault ? ' (默认)' : '')"
            :value="template.id"
          />
        </el-select>
        <el-text v-if="!templates.length" type="warning" style="margin-left: 12px">
          暂无模板，请先上传模板
        </el-text>
      </el-form-item>

      <el-form-item label="上传文件" required>
        <el-upload
          ref="uploadRef"
          :auto-upload="false"
          :limit="1"
          accept=".xlsx,.xls"
          :on-change="handleFileChange"
          :on-exceed="handleExceed"
          :on-remove="handleRemove"
          drag
          class="upload-area"
        >
          <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
          <div class="el-upload__text">
            拖拽文件到此处，或<em>点击上传</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">
              支持 .xlsx, .xls 格式，文件大小不超过 100MB
            </div>
          </template>
        </el-upload>
      </el-form-item>
    </el-form>

    <div class="actions">
      <el-button
        type="primary"
        :loading="loading"
        :disabled="!canStart"
        @click="handleStart"
      >
        开始校对
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'

const props = defineProps({
  projectId: Number,
  templates: {
    type: Array,
    default: () => []
  },
  loading: Boolean
})

const emit = defineEmits(['start-check'])

const selectedTemplateId = ref(null)
const selectedFile = ref(null)
const uploadRef = ref(null)

const canStart = computed(() => {
  return selectedTemplateId.value && selectedFile.value
})

// 设置默认模板
watch(() => props.templates, (templates) => {
  if (templates.length && !selectedTemplateId.value) {
    // 支持两种字段名格式：is_default（后端原始）和 isDefault（驼峰）
    const defaultTemplate = templates.find(t => t.is_default || t.isDefault)
    if (defaultTemplate) {
      selectedTemplateId.value = defaultTemplate.id
    } else {
      selectedTemplateId.value = templates[0].id
    }
  }
}, { immediate: true })

const handleFileChange = (file) => {
  // 验证文件大小
  if (file.size > 100 * 1024 * 1024) {
    ElMessage.warning('文件大小不能超过 100MB')
    uploadRef.value?.clearFiles()
    return
  }
  selectedFile.value = file.raw
}

const handleExceed = () => {
  ElMessage.warning('只能上传一个文件')
}

const handleRemove = () => {
  selectedFile.value = null
}

const handleStart = () => {
  if (!canStart.value) return
  emit('start-check', {
    templateId: selectedTemplateId.value,
    file: selectedFile.value
  })
}
</script>

<style scoped>
.file-upload-step {
  padding: 20px;
}

.upload-area {
  width: 100%;
}

.upload-area :deep(.el-upload-dragger) {
  width: 100%;
}

.actions {
  display: flex;
  justify-content: center;
  margin-top: 30px;
}
</style>
