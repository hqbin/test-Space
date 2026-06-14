<template>
  <div class="attachment-list">
    <el-card v-if="attachments.length > 0">
      <template #header>
        <div class="card-header">
          <span>{{ $t('attachment.attachmentList') }} ({{ attachments.length }})</span>
        </div>
      </template>
      
      <el-table :data="attachments" style="width: 100%">
        <el-table-column prop="file_name" :label="$t('attachment.fileName')" min-width="200" />
        <el-table-column :label="$t('attachment.fileSize')" width="120">
          <template #default="{ row }">
            {{ formatFileSize(row.file_size) }}
          </template>
        </el-table-column>
        <el-table-column prop="file_type" :label="$t('attachment.fileType')" width="150" />
        <el-table-column :label="$t('attachment.uploadTime')" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.upload_time) }}
          </template>
        </el-table-column>
        <el-table-column prop="description" :label="$t('common.description')" min-width="150" />
        <el-table-column :label="$t('common.operation')" width="150">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              @click="handleDownload(row)"
            >
              {{ $t('attachment.download') }}
            </el-button>
            <el-button
              type="danger"
              size="small"
              @click="handleDelete(row)"
              v-if="canDelete(row)"
            >
              {{ $t('common.delete') }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <el-empty v-else :description="$t('testcase.noAttachment')" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { ElMessageBox } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { useAttachment } from '@/composables/useAttachment'

const { t } = useI18n()

const props = defineProps({
  executionId: {
    type: Number,
    required: true
  },
  attachments: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['refresh'])

const { downloadAttachment, deleteAttachment } = useAttachment(props.executionId)

const currentUserId = computed(() => {
  const userStr = localStorage.getItem('user')
  if (userStr) {
    const user = JSON.parse(userStr)
    return user.id
  }
  return null
})

const canDelete = (attachment) => {
  const userStr = localStorage.getItem('user')
  if (userStr) {
    const user = JSON.parse(userStr)
    return user.username === 'admin' || user.username === 'super' || user.id === attachment.uploader_id
  }
  return false
}

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

const formatDateTime = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

const handleDownload = async (attachment) => {
  await downloadAttachment(attachment.id, attachment.file_name)
}

const handleDelete = async (attachment) => {
  try {
    await ElMessageBox.confirm(t('attachment.confirmDelete'), t('common.tip'), {
      confirmButtonText: t('common.confirm'),
      cancelButtonText: t('common.cancel'),
      type: 'warning'
    })
    
    await deleteAttachment(attachment.id)
    emit('refresh')
  } catch (error) {
    // user cancelled
  }
}
</script>

<style scoped>
.attachment-list {
  margin-top: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
