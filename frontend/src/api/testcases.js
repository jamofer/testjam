import { api } from './client'

export const suitesApi = {
  list: (projectId) => api.get(`/projects/${projectId}/suites`).then(r => r.data),
  listChildren: (projectId, parentSuiteId) =>
    api.get(`/projects/${projectId}/suites`, { params: { parent_suite_id: parentSuiteId } }).then(r => r.data),
  get: (id) => api.get(`/suites/${id}`).then(r => r.data),
  create: (projectId, data) => api.post(`/projects/${projectId}/suites`, data).then(r => r.data),
  update: (id, data) => api.put(`/suites/${id}`, data).then(r => r.data),
  delete: (id) => api.delete(`/suites/${id}`),

  createStep: (suiteId, data) => api.post(`/suites/${suiteId}/steps`, data).then(r => r.data),
  updateStep: (suiteId, stepId, data) => api.put(`/suites/${suiteId}/steps/${stepId}`, data).then(r => r.data),
  deleteStep: (suiteId, stepId) => api.delete(`/suites/${suiteId}/steps/${stepId}`),
  deleteStepsByType: (suiteId, stepType) => api.delete(`/suites/${suiteId}/steps`, { params: { step_type: stepType } }),
  reorderSteps: (suiteId, stepIds) => api.post(`/suites/${suiteId}/steps/reorder`, { step_ids: stepIds }).then(r => r.data),
}

export const casesApi = {
  list: (suiteId) => api.get(`/suites/${suiteId}/cases`).then(r => r.data),
  get: (id) => api.get(`/cases/${id}`).then(r => r.data),
  create: (suiteId, data) => api.post(`/suites/${suiteId}/cases`, data).then(r => r.data),
  update: (id, data) => api.put(`/cases/${id}`, data).then(r => r.data),
  delete: (id) => api.delete(`/cases/${id}`),
  bulkDelete: (ids) => api.post('/cases/bulk-delete', { ids }).then(r => r.data),

  listSteps: (caseId) => api.get(`/cases/${caseId}/steps`).then(r => r.data),
  createStep: (caseId, data) => api.post(`/cases/${caseId}/steps`, data).then(r => r.data),
  updateStep: (caseId, stepId, data) => api.put(`/cases/${caseId}/steps/${stepId}`, data).then(r => r.data),
  deleteStep: (caseId, stepId) => api.delete(`/cases/${caseId}/steps/${stepId}`),
  reorderSteps: (caseId, stepIds) => api.post(`/cases/${caseId}/steps/reorder`, { step_ids: stepIds }).then(r => r.data),

  uploadAttachment: (caseId, file) => {
    const form = new FormData()
    form.append('file', file)
    return api.post(`/cases/${caseId}/attachments`, form).then(r => r.data)
  },
  deleteAttachment: (caseId, attachmentId) =>
    api.delete(`/cases/${caseId}/attachments/${attachmentId}`),
}
