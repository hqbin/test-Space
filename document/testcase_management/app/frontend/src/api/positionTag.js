import request from './request'

export const positionTagApi = {
  // 获取所有职位Tag
  getPositionTags: (params) => {
    return request({
      url: '/position-tags',
      method: 'get',
      params
    })
  },

  // 创建职位Tag
  createPositionTag: (data) => {
    return request({
      url: '/position-tags',
      method: 'post',
      data
    })
  },

  // 获取单个职位Tag
  getPositionTag: (id) => {
    return request({
      url: `/position-tags/${id}`,
      method: 'get'
    })
  },

  // 更新职位Tag
  updatePositionTag: (id, data) => {
    return request({
      url: `/position-tags/${id}`,
      method: 'put',
      data
    })
  },

  // 删除职位Tag
  deletePositionTag: (id) => {
    return request({
      url: `/position-tags/${id}`,
      method: 'delete'
    })
  }
}
