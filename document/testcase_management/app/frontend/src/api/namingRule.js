import request from './request'

export const getNamingRule = () => {
  return request.get('/naming-rule')
}

export const updateNamingRule = (data) => {
  return request.put('/naming-rule', { data })
}
