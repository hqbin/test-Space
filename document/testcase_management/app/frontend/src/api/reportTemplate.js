import request from './request'

export function getReportTemplates(teamId) {
  return request.get(`/teams/${teamId}/report-templates`)
}

export function createReportTemplate(teamId, data) {
  return request.post(`/teams/${teamId}/report-templates`, data)
}

export function updateReportTemplate(templateId, data) {
  return request.put(`/report-templates/${templateId}`, data)
}

export function deleteReportTemplate(templateId) {
  return request.delete(`/report-templates/${templateId}`)
}

export function setDefaultReportTemplate(templateId) {
  return request.put(`/report-templates/${templateId}/default`)
}

export function getDefaultReportTemplate(teamId) {
  return request.get(`/teams/${teamId}/report-templates/default`)
}
