<template>
  <div class="attachment-uploader">
    <el-upload
      :action="uploadUrl"
      :headers="uploadHeaders"
      :on-success="handleSuccess"
      :on-error="handleError"
      :before-upload="beforeUpload"
      :file-list="fileList"
      :on-remove="handleRemove"
      multiple
      :limit="10"
    >
      <el-button type="primary" :icon="Upload">选择文件</el-button>
      <template #tip>
        <div class="el-upload__tip">
          支持上传图片、文档、压缩包等文件，单个文件不超过50MB
        </div>
      </template>
    </el-upload>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Upload } from '@element-plus/icons-vue'

const props = defineProps({
  testCaseId: {
    type: Number,
    required: true
  },
  attachments: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['uploaded', 'removed'])

const fileList = ref([])

const uploadUrl = computed(() => {
  return `/api/testcases/${props.testCaseId}/attachments`
})

const uploadHeaders = computed(() => ({
  Authorization: `Bearer ${localStorage.getItem('token')}`
}))

const beforeUpload = (file) => {
  const maxSize = 50 * 1024 * 1024 // 50MB
  if (file.size > maxSize) {
    ElMessage.error('文件大小不能超过50MB')
    return false
  }
  return true
}

const handleSuccess = (response, file) => {
  if (response.code === 200) {
    ElMessage.success('上传成功')
    emit('uploaded', response.data)
  } else {
    ElMessage.error(response.message || '上传失败')
  }
}

const handleError = () => {
  ElMessage.error('上传失败')
}

const handleRemove = (file) => {
  emit('removed', file)
}
</script>

<style scoped>
.attachment-uploader {
  width: 100%;
}

:deep(.el-upload__tip) {
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
}
</style>
