import { api } from './client'

export const projectsApi = {
  list: () => api.get('/projects').then(r => r.data),
  get: (id) => api.get(`/projects/${id}`).then(r => r.data),
  create: (data) => api.post('/projects', data).then(r => r.data),
  update: (id, data) => api.put(`/projects/${id}`, data).then(r => r.data),
  delete: (id) => api.delete(`/projects/${id}`),
  listMembers: (id) => api.get(`/projects/${id}/members`).then(r => r.data),
  addMember: (id, data) => api.post(`/projects/${id}/members`, data).then(r => r.data),
  removeMember: (id, userId) => api.delete(`/projects/${id}/members/${userId}`),
}
