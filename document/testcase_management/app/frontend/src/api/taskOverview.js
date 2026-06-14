import request from './request'

export const getTaskOverviews = (params) => {
  return request({
    url: '/task-overviews',
    method: 'get',
    params
  })
}

export const createTaskOverview = (data) => {
  return request({
    url: '/task-overviews',
    method: 'post',
    data
  })
}

export const getTaskOverviewDetail = (id, params = {}) => {
  return request({
    url: `/task-overviews/${id}`,
    method: 'get',
    params
  })
}

export const updateTaskOverview = (id, data) => {
  return request({
    url: `/task-overviews/${id}`,
    method: 'put',
    data
  })
}

export const deleteTaskOverview = (id) => {
  return request({
    url: `/task-overviews/${id}`,
    method: 'delete'
  })
}

export const addPlansToOverview = (id, data) => {
  return request({
    url: `/task-overviews/${id}/plans`,
    method: 'post',
    data
  })
}

export const removePlanFromOverview = (id, planId) => {
  return request({
    url: `/task-overviews/${id}/plans/${planId}`,
    method: 'delete'
  })
}
