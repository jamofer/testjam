import { api } from './client'

export const coverageApi = {
  matrix: (projectId, params) => api.get(`/projects/${projectId}/coverage/matrix`, { params }).then(r => r.data),
}
