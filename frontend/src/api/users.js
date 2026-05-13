import { api } from './client'

export const usersApi = {
  list: ({ includeDeleted = false } = {}) =>
    api.get('/users', { params: includeDeleted ? { include_deleted: true } : {} }).then(r => r.data),
  get: (id) => api.get(`/users/${id}`).then(r => r.data),
  create: (data) => api.post('/users', data).then(r => r.data),
  delete: (id, body = {}) =>
    api.delete(`/users/${id}`, { data: body }),
  deleteSelf: (body = {}) =>
    api.delete('/users/me', { data: body }),
  restore: (id) => api.post(`/users/${id}/restore`).then(r => r.data),
}
