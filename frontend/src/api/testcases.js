import { api } from './client'

export const suitesApi = {
  list: (projectId) => api.get(`/projects/${projectId}/suites`).then(r => r.data),
  get: (id) => api.get(`/suites/${id}`).then(r => r.data),
  create: (projectId, data) => api.post(`/projects/${projectId}/suites`, data).then(r => r.data),
  update: (id, data) => api.put(`/suites/${id}`, data).then(r => r.data),
  delete: (id) => api.delete(`/suites/${id}`),
}

export const casesApi = {
  list: (suiteId) => api.get(`/suites/${suiteId}/cases`).then(r => r.data),
  get: (id) => api.get(`/cases/${id}`).then(r => r.data),
  create: (suiteId, data) => api.post(`/suites/${suiteId}/cases`, data).then(r => r.data),
  update: (id, data) => api.put(`/cases/${id}`, data).then(r => r.data),
  delete: (id) => api.delete(`/cases/${id}`),

  listSteps: (caseId) => api.get(`/cases/${caseId}/steps`).then(r => r.data),
  createStep: (caseId, data) => api.post(`/cases/${caseId}/steps`, data).then(r => r.data),
  updateStep: (caseId, stepId, data) => api.put(`/cases/${caseId}/steps/${stepId}`, data).then(r => r.data),
  deleteStep: (caseId, stepId) => api.delete(`/cases/${caseId}/steps/${stepId}`),

  uploadAttachment: (caseId, file) => {
    const form = new FormData()
    form.append('file', file)
    return api.post(`/cases/${caseId}/attachments`, form).then(r => r.data)
  },
  deleteAttachment: (caseId, attachmentId) =>
    api.delete(`/cases/${caseId}/attachments/${attachmentId}`),
}
