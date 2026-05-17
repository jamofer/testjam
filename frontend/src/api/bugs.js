import { api } from "./client"

export const bugsApi = {
  list: (projectId, params = {}) =>
    api.get(`/projects/${projectId}/bugs`, { params }).then(r => r.data),
  get: (id) => api.get(`/bugs/${id}`).then(r => r.data),
  byNumber: (projectId, number) =>
    api.get(`/projects/${projectId}/bugs/by-number/${number}`).then(r => r.data),
  create: (projectId, data) =>
    api.post(`/projects/${projectId}/bugs`, data).then(r => r.data),
  update: (id, data) => api.put(`/bugs/${id}`, data).then(r => r.data),
  delete: (id) => api.delete(`/bugs/${id}`),
  changeStatus: (id, status, note) =>
    api.post(`/bugs/${id}/status`, { status, note }).then(r => r.data),
  listComments: (id) => api.get(`/bugs/${id}/comments`).then(r => r.data),
  addComment: (id, body) =>
    api.post(`/bugs/${id}/comments`, { body }).then(r => r.data),
  updateComment: (id, commentId, body) =>
    api.put(`/bugs/${id}/comments/${commentId}`, { body }).then(r => r.data),
  deleteComment: (id, commentId) =>
    api.delete(`/bugs/${id}/comments/${commentId}`),
  listHistory: (id) => api.get(`/bugs/${id}/history`).then(r => r.data),
  listAttachments: (id) => api.get(`/bugs/${id}/attachments`).then(r => r.data),
  getContext: (id) => api.get(`/bugs/${id}/context`).then(r => r.data),
  listLinks: (id) => api.get(`/bugs/${id}/links`).then(r => r.data),
  addLink: (id, data) => api.post(`/bugs/${id}/links`, data).then(r => r.data),
  deleteLink: (id, linkId) => api.delete(`/bugs/${id}/links/${linkId}`),
  reportUrl: (projectId, { format = "html", versionId, environment } = {}) => {
    const params = new URLSearchParams({ format })
    if (versionId) params.set("version_id", versionId)
    if (environment) params.set("environment", environment)
    return `/projects/${projectId}/bugs/report?${params.toString()}`
  },
  downloadReport: (projectId, options) =>
    api.get(bugsApi.reportUrl(projectId, options), { responseType: "blob" }),
}
