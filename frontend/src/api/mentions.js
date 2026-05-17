import { api } from "./client"

export const mentionsApi = {
  search: (projectId, kind, query, limit = 10) =>
    api
      .get(`/projects/${projectId}/mentions/search`, {
        params: { kind, q: query, limit },
      })
      .then(r => r.data),
  resolve: (projectId, tokens) =>
    api
      .post(`/projects/${projectId}/mentions/resolve`, { tokens })
      .then(r => r.data),
}
