<template>
  <div class="comment-section">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>评论 ({{ comments.length }})</span>
        </div>
      </template>
      
      <!-- 评论输入框 -->
      <div class="comment-input">
        <el-input
          v-model="newComment"
          type="textarea"
          :rows="3"
          placeholder="输入评论内容，支持@username提及用户"
          :disabled="submitting"
        />
        <div class="comment-actions">
          <el-button
            type="primary"
            :loading="submitting"
            @click="handleSubmit"
          >
            发表评论
          </el-button>
        </div>
      </div>
      
      <!-- 评论列表 -->
      <div class="comment-list" v-loading="loading">
        <div v-if="comments.length === 0" class="empty-comments">
          <el-empty description="暂无评论" />
        </div>
        
        <div v-else>
          <comment-item
            v-for="comment in comments"
            :key="comment.id"
            :comment="comment"
            @reply="handleReply"
            @delete="handleDelete"
          />
        </div>
      </div>
    </el-card>
    
    <!-- 回复对话框 -->
    <el-dialog
      v-model="replyDialogVisible"
      title="回复评论"
      width="500px"
    >
      <el-input
        v-model="replyContent"
        type="textarea"
        :rows="4"
        placeholder="输入回复内容"
      />
      <template #footer>
        <el-button @click="replyDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleReplySubmit" :loading="submitting">
          提交
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessageBox } from 'element-plus'
import { useComment } from '@/composables/useComment'
import CommentItem from './CommentItem.vue'

const props = defineProps({
  entityType: {
    type: String,
    required: true,
    validator: (value) => ['testplan', 'testcase', 'execution'].includes(value)
  },
  entityId: {
    type: Number,
    required: true
  }
})

const {
  comments,
  loading,
  submitting,
  loadComments,
  createComment,
  deleteComment
} = useComment(props.entityType, props.entityId)

const newComment = ref('')
const replyDialogVisible = ref(false)
const replyContent = ref('')
const replyToCommentId = ref(null)

onMounted(() => {
  loadComments()
})

const handleSubmit = async () => {
  if (!newComment.value.trim()) {
    return
  }
  
  const success = await createComment(newComment.value)
  if (success) {
    newComment.value = ''
  }
}

const handleReply = (comment) => {
  replyToCommentId.value = comment.id
  replyContent.value = `@${comment.author_name} `
  replyDialogVisible.value = true
}

const handleReplySubmit = async () => {
  if (!replyContent.value.trim()) {
    return
  }
  
  const success = await createComment(replyContent.value, replyToCommentId.value)
  if (success) {
    replyContent.value = ''
    replyDialogVisible.value = false
    replyToCommentId.value = null
  }
}

const handleDelete = async (comment) => {
  try {
    await ElMessageBox.confirm('确定要删除此评论吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await deleteComment(comment.id)
  } catch (error) {
    // 用户取消
  }
}
</script>

<style scoped>
.comment-section {
  margin-top: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.comment-input {
  margin-bottom: 20px;
}

.comment-actions {
  margin-top: 10px;
  text-align: right;
}

.comment-list {
  min-height: 100px;
}

.empty-comments {
  padding: 20px 0;
}
</style>
