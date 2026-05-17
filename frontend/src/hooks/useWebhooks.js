import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { webhooksApi } from "../api/webhooks"

export function useWebhooks(projectId) {
  return useQuery({
    queryKey: ["webhooks", projectId],
    queryFn: () => webhooksApi.list(projectId),
    enabled: !!projectId,
  })
}

export function useWebhookDeliveries(webhookId, { enabled = true } = {}) {
  return useQuery({
    queryKey: ["webhook-deliveries", webhookId],
    queryFn: () => webhooksApi.listDeliveries(webhookId),
    enabled: enabled && !!webhookId,
    refetchInterval: 5000,
  })
}

export function useCreateWebhook(projectId) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data) => webhooksApi.create(projectId, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["webhooks", projectId] }),
  })
}

export function useUpdateWebhook(projectId) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }) => webhooksApi.update(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["webhooks", projectId] }),
  })
}

export function useDeleteWebhook(projectId) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: webhooksApi.delete,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["webhooks", projectId] }),
  })
}

export function useTestWebhook() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: webhooksApi.test,
    onSuccess: (webhook) =>
      qc.invalidateQueries({ queryKey: ["webhook-deliveries", webhook.id] }),
  })
}
