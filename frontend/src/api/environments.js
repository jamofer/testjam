import { api } from './client'

export const environmentsApi = {
  list: (projectId, { includeArchived = false } = {}) =>
    api
      .get(`/projects/${projectId}/environments`, { params: { include_archived: includeArchived } })
      .then(r => r.data),
  get: (id) => api.get(`/environments/${id}`).then(r => r.data),
  create: (projectId, data) =>
    api.post(`/projects/${projectId}/environments`, data).then(r => r.data),
  update: (id, data) => api.put(`/environments/${id}`, data).then(r => r.data),
  archive: (id) => api.post(`/environments/${id}/archive`).then(r => r.data),
  unarchive: (id) => api.post(`/environments/${id}/unarchive`).then(r => r.data),
  delete: (id) => api.delete(`/environments/${id}`),
  reorder: (projectId, ids) =>
    api.post(`/projects/${projectId}/environments/reorder`, { ids }).then(r => r.data),
}
