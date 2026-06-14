import request from './request'

export function getDatabaseTables() {
  return request({ url: '/database/tables', method: 'get' })
}

export function getTableSchema(tableName) {
  return request({ url: `/database/tables/${tableName}/schema`, method: 'get' })
}

export function getTableRows(tableName, params) {
  return request({ url: `/database/tables/${tableName}/rows`, method: 'get', params })
}

export function createTableRow(tableName, data) {
  return request({ url: `/database/tables/${tableName}/rows`, method: 'post', data: { data } })
}

export function updateTableRow(tableName, pk, data) {
  return request({ url: `/database/tables/${tableName}/rows`, method: 'put', data: { pk, data } })
}

export function deleteTableRow(tableName, pk) {
  return request({ url: `/database/tables/${tableName}/rows`, method: 'delete', data: { pk } })
}

export function executeDatabaseSql(sql) {
  return request({ url: '/database/sql', method: 'post', data: { sql } })
}

export function backupDatabase(tables) {
  return request({
    url: '/database/backup',
    method: 'post',
    data: { tables },
    responseType: 'blob',
    timeout: 600000  // 10 分钟，大数据量备份可能耗时较长
  })
}

export function restoreDatabase(file, mode = 'append') {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('mode', mode)
  return request({
    url: '/database/restore/form',
    method: 'post',
    data: formData,
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 300000  // 5 分钟，足够上传 SQL 文件并启动任务；任务进度通过轮询
  })
}

export function getRestoreProgress(taskId) {
  return request({ url: `/database/restore/${taskId}`, method: 'get' })
}

export function cancelRestoreTask(taskId) {
  return request({ url: `/database/restore/${taskId}/cancel`, method: 'post' })
}
