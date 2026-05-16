import { api } from './client'

export const versionsApi = {
  list: (projectId) => api.get(`/projects/${projectId}/versions`).then(r => r.data),
  get: (id) => api.get(`/versions/${id}`).then(r => r.data),
  create: (projectId, data) => api.post(`/projects/${projectId}/versions`, data).then(r => r.data),
  update: (id, data) => api.put(`/versions/${id}`, data).then(r => r.data),
  delete: (id) => api.delete(`/versions/${id}`),
}
