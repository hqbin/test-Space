import request from './request'

/**
 * 获取项目的所有模块
 */
export function getModules(projectId) {
  return request({
    url: '/modules',
    method: 'get',
    params: { project_id: projectId }
  })
}

/**
 * 获取项目的模块树结构(包含用例数量)
 * @param {number|string} projectIdOrIds - 单个项目ID或逗号分隔的多个项目ID
 */
export function getModuleTree(projectIdOrIds) {
  const params = {}
  if (typeof projectIdOrIds === 'string' && projectIdOrIds.includes(',')) {
    params.project_ids = projectIdOrIds
  } else if (projectIdOrIds) {
    params.project_id = projectIdOrIds
  }
  return request({
    url: '/modules/tree',
    method: 'get',
    params,
    timeout: 60000  // 模块树数据可能较多，给60秒超时
  })
}

/**
 * 获取模块扁平列表（带完整路径，用于用例表单选择）
 */
export function getModulesFlat(projectIdOrIds) {
  const params = {}
  if (typeof projectIdOrIds === 'string' && projectIdOrIds.includes(',')) {
    params.project_ids = projectIdOrIds
  } else if (projectIdOrIds) {
    params.project_id = projectIdOrIds
  }
  return request({
    url: '/modules/flat',
    method: 'get',
    params,
    timeout: 60000  // 模块列表数据可能较多，给60秒超时
  })
}

/**
 * 创建模块
 */
export function createModule(data) {
  return request({
    url: '/modules',
    method: 'post',
    data
  })
}

/**
 * 更新模块
 */
export function updateModule(moduleId, data) {
  return request({
    url: `/modules/${moduleId}`,
    method: 'put',
    data
  })
}

/**
 * 删除模块
 */
export function deleteModule(moduleId) {
  return request({
    url: `/modules/${moduleId}`,
    method: 'delete'
  })
}

/**
 * 批量更新模块排序
 */
export function sortModules(moduleOrders) {
  return request({
    url: '/modules/sort',
    method: 'post',
    data: { module_orders: moduleOrders }
  })
}


/**
 * 获取模块下所有用例关联的PR列表
 */
export function getModulePRLinks(moduleId) {
  return request({
    url: `/modules/${moduleId}/pr-links`,
    method: 'get'
  })
}

/**
 * 获取整个用例库下所有用例关联的PR列表
 */
export function getProjectAllPRLinks(projectId) {
  return request({
    url: `/projects/${projectId}/all-pr-links`,
    method: 'get'
  })
}
