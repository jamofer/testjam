import { api } from "./client"

export const plansApi = {
  list: (projectId) => api.get(`/projects/${projectId}/plans`).then(r => r.data),
  get: (id) => api.get(`/plans/${id}`).then(r => r.data),
  create: (projectId, data) => api.post(`/projects/${projectId}/plans`, data).then(r => r.data),
  update: (id, data) => api.put(`/plans/${id}`, data).then(r => r.data),
  delete: (id) => api.delete(`/plans/${id}`),
  addCases: (id, caseIds) => api.post(`/plans/${id}/cases`, { case_ids: caseIds }).then(r => r.data),
}
