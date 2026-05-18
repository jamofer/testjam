import { api } from './client'
import { downloadFromApi } from '../lib/download'

export const versionsApi = {
  list: (projectId) => api.get(`/projects/${projectId}/versions`).then(r => r.data),
  get: (id) => api.get(`/versions/${id}`).then(r => r.data),
  create: (projectId, data) => api.post(`/projects/${projectId}/versions`, data).then(r => r.data),
  update: (id, data) => api.put(`/versions/${id}`, data).then(r => r.data),
  delete: (id) => api.delete(`/versions/${id}`),

  listAttachments: (versionId) =>
    api.get(`/versions/${versionId}/attachments`).then(r => r.data),
  uploadAttachment: (versionId, file) => {
    const form = new FormData()
    form.append('file', file)
    return api.post(`/versions/${versionId}/attachments`, form).then(r => r.data)
  },
  deleteAttachment: (versionId, attachmentId) =>
    api.delete(`/versions/${versionId}/attachments/${attachmentId}`),
  downloadAttachment: (versionId, attachmentId, filename) =>
    downloadFromApi(`/versions/${versionId}/attachments/${attachmentId}/download`, filename),
}
