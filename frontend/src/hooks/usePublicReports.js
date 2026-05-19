import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { publicReportsApi } from "../api/publicReports"


export function usePublicReports(projectId, { enabled = true } = {}) {
  return useQuery({
    queryKey: ["public-reports", projectId],
    queryFn: () => publicReportsApi.list(projectId),
    enabled: !!projectId && enabled,
  })
}

export function useCreatePublicReport(projectId) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data) => publicReportsApi.create(projectId, data),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["public-reports", projectId] }),
  })
}

export function useRevokePublicReport(projectId) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (publicReportId) =>
      publicReportsApi.revoke(projectId, publicReportId),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["public-reports", projectId] }),
  })
}
