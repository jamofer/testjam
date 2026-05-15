import { api } from './client'
import { downloadFromApi } from '../lib/download'

export const suitesApi = {
  list: (projectId) => api.get(`/projects/${projectId}/suites`).then(r => r.data),
  listAll: (projectId) => api.get(`/projects/${projectId}/suites`, { params: { all: true } }).then(r => r.data),
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
  reorderProjectSuites: (projectId, suiteIds, parentSuiteId) =>
    api.post(`/projects/${projectId}/suites/reorder`,
      { suite_ids: suiteIds },
      { params: parentSuiteId != null ? { parent_suite_id: parentSuiteId } : undefined }
    ).then(r => r.data),
}

export const casesApi = {
  list: (suiteId) => api.get(`/suites/${suiteId}/cases`).then(r => r.data),
  search: (projectId, { q, tags } = {}) =>
    api.get(`/projects/${projectId}/cases`, { params: { q: q || undefined, tags: tags?.length ? tags : undefined } })
      .then(r => r.data),
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
  reorderInSuite: (suiteId, caseIds) =>
    api.post(`/suites/${suiteId}/cases/reorder`, { case_ids: caseIds }).then(r => r.data),

  uploadAttachment: (caseId, file) => {
    const form = new FormData()
    form.append('file', file)
    return api.post(`/cases/${caseId}/attachments`, form).then(r => r.data)
  },
  deleteAttachment: (caseId, attachmentId) =>
    api.delete(`/cases/${caseId}/attachments/${attachmentId}`),
  downloadAttachment: (caseId, attachmentId, filename) =>
    downloadFromApi(`/cases/${caseId}/attachments/${attachmentId}/download`, filename),

  listRevisions: (caseId) =>
    api.get(`/cases/${caseId}/revisions`).then(r => r.data),
  getRevision: (caseId, revId) =>
    api.get(`/cases/${caseId}/revisions/${revId}`).then(r => r.data),
}
