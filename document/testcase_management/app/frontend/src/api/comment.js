/**
 * 评论管理API
 */
import request from './request'

/**
 * 创建评论
 * @param {object} data - 评论数据
 * @param {string} data.entity_type - 实体类型 (testplan/testcase/execution)
 * @param {number} data.entity_id - 实体ID
 * @param {string} data.content - 评论内容
 * @param {number} data.parent_id - 父评论ID（可选）
 */
export function createComment(data) {
  return request({
    url: '/comments',
    method: 'post',
    data
  })
}

/**
 * 获取评论列表
 * @param {string} entityType - 实体类型
 * @param {number} entityId - 实体ID
 * @param {boolean} buildTree - 是否构建树形结构
 */
export function getComments(entityType, entityId, buildTree = true) {
  return request({
    url: `/comments/${entityType}/${entityId}`,
    method: 'get',
    params: { build_tree: buildTree }
  })
}

/**
 * 删除评论
 * @param {number} commentId - 评论ID
 */
export function deleteComment(commentId) {
  return request({
    url: `/comments/${commentId}`,
    method: 'delete'
  })
}

/**
 * 批量获取评论数量
 * @param {string} entityType - 实体类型
 * @param {number[]} entityIds - 实体ID数组
 */
export function getCommentCounts(entityType, entityIds) {
  return request({
    url: `/comments/counts/${entityType}`,
    method: 'get',
    params: { entity_ids: entityIds.join(',') }
  })
}
