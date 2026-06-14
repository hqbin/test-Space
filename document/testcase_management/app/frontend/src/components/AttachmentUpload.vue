<template>
  <div class="attachment-upload">
    <el-upload
      ref="uploadRef"
      :action="uploadUrl"
      :headers="uploadHeaders"
      :data="uploadData"
      :on-success="handleSuccess"
      :on-error="handleError"
      :on-progress="handleProgress"
      :before-upload="beforeUpload"
      :show-file-list="false"
      :disabled="disabled || uploading"
    >
      <el-button type="primary" :loading="uploading" :disabled="disabled">
        <el-icon v-if="!uploading"><Upload /></el-icon>
        {{ uploading ? `上传中 ${uploadProgress}%` : '上传附件' }}
      </el-button>
    </el-upload>
    
    <div v-if="uploadProgress > 0 && uploading" class="upload-progress">
      <el-progress :percentage="uploadProgress" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Upload } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  executionId: {
    type: Number,
    required: true
  },
  disabled: {
    type: Boolean,
    default: false
  },
  maxSize: {
    type: Number,
    default: 100 * 1024 * 1024 // 100MB
  }
})

const emit = defineEmits(['success', 'error'])

const uploadRef = ref(null)
const uploading = ref(false)
const uploadProgress = ref(0)

const uploadUrl = computed(() => {
  return `/api/attachments/executions/${props.executionId}/upload`
})

const uploadHeaders = computed(() => {
  const token = localStorage.getItem('token')
  return {
    'Authorization': `Bearer ${token}`
  }
})

const uploadData = computed(() => {
  return {
    execution_id: props.executionId
  }
})

const beforeUpload = (file) => {
  // 检查文件大小
  if (file.size > props.maxSize) {
    ElMessage.error(`文件大小不能超过 ${props.maxSize / 1024 / 1024}MB`)
    return false
  }
  
  uploading.value = true
  uploadProgress.value = 0
  return true
}

const handleProgress = (event) => {
  uploadProgress.value = Math.round(event.percent)
}

const handleSuccess = (response) => {
  uploading.value = false
  uploadProgress.value = 0
  
  if (response.code === 200) {
    ElMessage.success('上传成功')
    emit('success', response.data)
  } else {
    ElMessage.error(response.message || '上传失败')
    emit('error', response)
  }
}

const handleError = (error) => {
  uploading.value = false
  uploadProgress.value = 0
  ElMessage.error('上传失败')
  emit('error', error)
}
</script>

<style scoped>
.attachment-upload {
  display: inline-block;
}

.upload-progress {
  margin-top: 10px;
  width: 200px;
}
</style>
