import { api } from "./client"

export const webhooksApi = {
  list: (projectId) =>
    api.get(`/projects/${projectId}/webhooks`).then(r => r.data),
  create: (projectId, data) =>
    api.post(`/projects/${projectId}/webhooks`, data).then(r => r.data),
  update: (id, data) =>
    api.put(`/webhooks/${id}`, data).then(r => r.data),
  delete: (id) =>
    api.delete(`/webhooks/${id}`),
  test: (id) =>
    api.post(`/webhooks/${id}/test`).then(r => r.data),
  listDeliveries: (id, limit = 25) =>
    api.get(`/webhooks/${id}/deliveries`, { params: { limit } }).then(r => r.data),
}

export const WEBHOOK_EVENTS = [
  "execution.created",
  "execution.completed",
  "execution.aborted",
  "test_result.failed",
  "bug.created",
  "bug.resolved",
  "bug.status_changed",
]
