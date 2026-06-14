/**
 * 评论管理组合式函数
 */
import { ref } from 'vue'
import * as api from '@/api/comment'
import { ElMessage } from 'element-plus'

export function useComment(entityType, entityId) {
  const comments = ref([])
  const loading = ref(false)
  const submitting = ref(false)
  
  /**
   * 加载评论列表
   */
  const loadComments = async (buildTree = true) => {
    loading.value = true
    try {
      const res = await api.getComments(entityType, entityId, buildTree)
      comments.value = res.data || []
    } catch (error) {
      ElMessage.error('加载评论失败')
      console.error('加载评论失败:', error)
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 创建评论
   */
  const createComment = async (content, parentId = null) => {
    if (!content.trim()) {
      ElMessage.warning('评论内容不能为空')
      return false
    }
    
    submitting.value = true
    try {
      await api.createComment({
        entity_type: entityType,
        entity_id: entityId,
        content,
        parent_id: parentId
      })
      
      ElMessage.success('评论成功')
      await loadComments()
      return true
    } catch (error) {
      ElMessage.error('评论失败')
      console.error('评论失败:', error)
      return false
    } finally {
      submitting.value = false
    }
  }
  
  /**
   * 删除评论
   */
  const deleteComment = async (commentId) => {
    try {
      await api.deleteComment(commentId)
      ElMessage.success('删除成功')
      await loadComments()
    } catch (error) {
      ElMessage.error('删除失败')
      console.error('删除失败:', error)
    }
  }
  
  /**
   * 解析@提及
   */
  const parseMentions = (content) => {
    const pattern = /@(\w+)/g
    const mentions = []
    let match
    
    while ((match = pattern.exec(content)) !== null) {
      mentions.push(match[1])
    }
    
    return [...new Set(mentions)]
  }
  
  return {
    comments,
    loading,
    submitting,
    loadComments,
    createComment,
    deleteComment,
    parseMentions
  }
}
