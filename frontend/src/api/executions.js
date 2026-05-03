import { api } from './client'

export const executionsApi = {
  list: (projectId, params) => api.get(`/projects/${projectId}/executions`, { params }).then(r => r.data),
  get: (id) => api.get(`/executions/${id}`).then(r => r.data),
  create: (projectId, data) => api.post(`/projects/${projectId}/executions`, data).then(r => r.data),
  update: (id, data) => api.put(`/executions/${id}`, data).then(r => r.data),
  delete: (id) => api.delete(`/executions/${id}`),

  listResults: (executionId, params) => api.get(`/executions/${executionId}/results`, { params }).then(r => r.data),
  createResult: (executionId, data) => api.post(`/executions/${executionId}/results`, data).then(r => r.data),
  bulkResults: (executionId, data) => api.post(`/executions/${executionId}/results/bulk`, data).then(r => r.data),
  updateResult: (id, data) => api.put(`/results/${id}`, data).then(r => r.data),
  updateStepResult: (resultId, stepResultId, data) =>
    api.put(`/results/${resultId}/step-results/${stepResultId}`, data).then(r => r.data),

  uploadResultAttachment: (resultId, file) => {
    const form = new FormData()
    form.append('file', file)
    return api.post(`/results/${resultId}/attachments`, form).then(r => r.data)
  },
  deleteResultAttachment: (resultId, attachmentId) =>
    api.delete(`/results/${resultId}/attachments/${attachmentId}`),

  importJunit: (executionId, file) => {
    const form = new FormData()
    form.append('file', file)
    return api.post(`/executions/${executionId}/results/import/junit`, form).then(r => r.data)
  },
  importRobotFramework: (executionId, file) => {
    const form = new FormData()
    form.append('file', file)
    return api.post(`/executions/${executionId}/results/import/robotframework`, form).then(r => r.data)
  },
}
