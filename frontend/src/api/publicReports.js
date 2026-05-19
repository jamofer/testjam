import { api } from "./client"

export const publicReportsApi = {
  list: (projectId) =>
    api.get(`/projects/${projectId}/public-reports`).then(r => r.data),
  create: (projectId, data) =>
    api.post(`/projects/${projectId}/public-reports`, data).then(r => r.data),
  revoke: (projectId, publicReportId) =>
    api.delete(`/projects/${projectId}/public-reports/${publicReportId}`),
  publicUrl: (token) => `${window.location.origin}/api/v1/public/reports/${token}`,
}
