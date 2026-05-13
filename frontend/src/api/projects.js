import { api } from './client'

export const projectsApi = {
  list: ({ includeArchived = false } = {}) =>
    api.get('/projects', { params: includeArchived ? { include_archived: true } : {} }).then(r => r.data),
  get: (id) => api.get(`/projects/${id}`).then(r => r.data),
  create: (data) => api.post('/projects', data).then(r => r.data),
  update: (id, data) => api.put(`/projects/${id}`, data).then(r => r.data),
  delete: (id) => api.delete(`/projects/${id}`),
  archive: (id) => api.post(`/projects/${id}/archive`).then(r => r.data),
  unarchive: (id) => api.post(`/projects/${id}/unarchive`).then(r => r.data),
  exportZip: async (id) => {
    const response = await api.get(`/projects/${id}/export`, { responseType: 'blob' })
    const disposition = response.headers?.['content-disposition'] || ''
    const match = disposition.match(/filename="?([^";]+)"?/i)
    const filename = match ? match[1] : `project-${id}.zip`
    const url = URL.createObjectURL(response.data)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
  },
  listMembers: (id) => api.get(`/projects/${id}/members`).then(r => r.data),
  addMember: (id, data) => api.post(`/projects/${id}/members`, data).then(r => r.data),
  removeMember: (id, userId) => api.delete(`/projects/${id}/members/${userId}`),
}
