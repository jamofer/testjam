import { api } from './client'

export const projectGroupsApi = {
  list: (projectId) =>
    api.get(`/projects/${projectId}/groups`).then(r => r.data),
  add: (projectId, groupId, role) =>
    api.post(`/projects/${projectId}/groups`, { group_id: groupId, role }).then(r => r.data),
  update: (projectId, groupId, role) =>
    api.put(`/projects/${projectId}/groups/${groupId}`, { role }).then(r => r.data),
  remove: (projectId, groupId) =>
    api.delete(`/projects/${projectId}/groups/${groupId}`),
}
