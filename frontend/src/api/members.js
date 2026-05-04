import { api } from './client'

export const membersApi = {
  list:   (projectId)             => api.get(`/projects/${projectId}/members`).then(r => r.data),
  add:    (projectId, data)        => api.post(`/projects/${projectId}/members`, data).then(r => r.data),
  update: (projectId, userId, data) => api.put(`/projects/${projectId}/members/${userId}`, data).then(r => r.data),
  remove: (projectId, userId)      => api.delete(`/projects/${projectId}/members/${userId}`),
}
