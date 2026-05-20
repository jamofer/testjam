import { api } from './client'

export const customFieldsApi = {
  list: (projectId, entityType, { includeArchived = false } = {}) =>
    api
      .get(`/projects/${projectId}/custom-fields`, {
        params: { entity_type: entityType, include_archived: includeArchived },
      })
      .then(r => r.data),
  get: (id) => api.get(`/custom-fields/${id}`).then(r => r.data),
  create: (projectId, data) =>
    api.post(`/projects/${projectId}/custom-fields`, data).then(r => r.data),
  update: (id, data) =>
    api.put(`/custom-fields/${id}`, data).then(r => r.data),
  archive: (id) => api.post(`/custom-fields/${id}/archive`).then(r => r.data),
  unarchive: (id) => api.post(`/custom-fields/${id}/unarchive`).then(r => r.data),
  delete: (id) => api.delete(`/custom-fields/${id}`),
  reorder: (projectId, ids) =>
    api.post(`/projects/${projectId}/custom-fields/reorder`, { ids }).then(r => r.data),
}
