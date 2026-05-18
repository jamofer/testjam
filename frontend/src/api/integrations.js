import { api } from './client'


export const integrationsApi = {
  listProviders: () => api.get('/integrations/providers').then(r => r.data),

  list: (projectId) =>
    api.get(`/projects/${projectId}/integrations`).then(r => r.data),
  get: (id) => api.get(`/integrations/${id}`).then(r => r.data),
  create: (projectId, data) =>
    api.post(`/projects/${projectId}/integrations`, data).then(r => r.data),
  update: (id, data) => api.put(`/integrations/${id}`, data).then(r => r.data),
  delete: (id) => api.delete(`/integrations/${id}`),
  test: (id) => api.post(`/integrations/${id}/test`),
  rotateCredential: (id, secret) =>
    api.post(`/integrations/${id}/rotate-credential`, { secret }).then(r => r.data),

  listBugLinks: (bugId) =>
    api.get(`/bugs/${bugId}/external-links`).then(r => r.data),
  pushBug: (bugId, integrationId, labels) =>
    api.post(`/bugs/${bugId}/external-links`,
      { integration_id: integrationId, labels: labels ?? [] }).then(r => r.data),
  syncBugLink: (bugId, linkId) =>
    api.post(`/bugs/${bugId}/external-links/${linkId}/sync`).then(r => r.data),
  deleteBugLink: (bugId, linkId) =>
    api.delete(`/bugs/${bugId}/external-links/${linkId}`),
}
