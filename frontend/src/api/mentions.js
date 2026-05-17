import { api } from "./client"

export const mentionsApi = {
  search: (projectId, kind, query, limit = 10, parents = []) => {
    const params = { kind, q: query, limit }
    if (parents[0] != null) params.execution_id = parents[0]
    if (parents[1] != null) params.result_id = parents[1]
    return api
      .get(`/projects/${projectId}/mentions/search`, { params })
      .then(r => r.data)
  },
  resolve: (projectId, tokens) =>
    api
      .post(`/projects/${projectId}/mentions/resolve`, { tokens })
      .then(r => r.data),
}
