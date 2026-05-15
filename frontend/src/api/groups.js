import { api } from './client'

export const groupsApi = {
  list: () => api.get('/groups').then(r => r.data),
  get: (id) => api.get(`/groups/${id}`).then(r => r.data),
  create: (data) => api.post('/groups', data).then(r => r.data),
  update: (id, data) => api.put(`/groups/${id}`, data).then(r => r.data),
  delete: (id) => api.delete(`/groups/${id}`),
  listMembers: (id) => api.get(`/groups/${id}/members`).then(r => r.data),
  addMember: (groupId, userId, role = "member") =>
    api.post(`/groups/${groupId}/members`, null, { params: { user_id: userId, role } }),
  removeMember: (groupId, userId) => api.delete(`/groups/${groupId}/members/${userId}`),
}
