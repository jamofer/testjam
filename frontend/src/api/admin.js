import { api } from './client'

export const adminApi = {
  listProjects: ({ includeArchived = true } = {}) =>
    api.get('/admin/projects', { params: { include_archived: includeArchived } }).then(r => r.data),
  transferOwnership: (projectId, newOwnerId) =>
    api.post(`/projects/${projectId}/transfer-ownership`, { new_owner_id: newOwnerId }).then(r => r.data),
}
