<template>
  <div class="comment-item">
    <div class="comment-header">
      <span class="author">{{ comment.author_name }}</span>
      <span class="time">{{ formatDateTime(comment.created_at) }}</span>
    </div>
    
    <div class="comment-content">
      {{ comment.content }}
    </div>
    
    <div class="comment-actions">
      <el-button link size="small" @click="handleReply">
        回复
      </el-button>
      <el-button
        v-if="canDelete"
        link
        size="small"
        @click="handleDelete"
        class="delete-btn"
      >
        删除
      </el-button>
    </div>
    
    <!-- 子评论 -->
    <div v-if="comment.children && comment.children.length > 0" class="comment-children">
      <comment-item
        v-for="child in comment.children"
        :key="child.id"
        :comment="child"
        @reply="handleReply"
        @delete="handleDelete"
      />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  comment: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['reply', 'delete'])

const canDelete = computed(() => {
  const userStr = localStorage.getItem('user')
  if (userStr) {
    const user = JSON.parse(userStr)
    // 只有管理员可以删除评论
    return user.username === 'admin' || user.username === 'super'
  }
  return false
})

const formatDateTime = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

const handleReply = () => {
  emit('reply', props.comment)
}

const handleDelete = () => {
  emit('delete', props.comment)
}
</script>

<style scoped>
.comment-item {
  padding: 15px;
  border-bottom: 1px solid #eee;
}

.comment-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.author {
  font-weight: bold;
  color: #409EFF;
}

.time {
  font-size: 12px;
  color: #999;
}

.comment-content {
  margin-bottom: 10px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

.comment-actions {
  display: flex;
  gap: 10px;
}

.delete-btn {
  color: #F56C6C;
}

.comment-children {
  margin-left: 30px;
  margin-top: 10px;
  border-left: 2px solid #eee;
}
</style>
