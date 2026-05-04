import { api } from './client'

export const tokensApi = {
  listUser:          ()                   => api.get('/users/me/tokens').then(r => r.data),
  createUser:        (data)               => api.post('/users/me/tokens', data).then(r => r.data),
  revokeUser:        (id)                 => api.delete(`/users/me/tokens/${id}`),

  listProject:       (projectId)          => api.get(`/projects/${projectId}/tokens`).then(r => r.data),
  createProject:     (projectId, data)    => api.post(`/projects/${projectId}/tokens`, data).then(r => r.data),
  revokeProject:     (projectId, tokenId) => api.delete(`/projects/${projectId}/tokens/${tokenId}`),
}
