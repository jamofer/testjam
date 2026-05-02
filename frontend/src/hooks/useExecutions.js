import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { executionsApi } from '../api/executions'

export function useExecutions(projectId, params) {
  return useQuery({
    queryKey: ['executions', projectId, params],
    queryFn: () => executionsApi.list(projectId, params),
    enabled: !!projectId,
  })
}

export function useExecution(id) {
  return useQuery({
    queryKey: ['executions', id],
    queryFn: () => executionsApi.get(id),
    enabled: !!id,
  })
}

export function useCreateExecution(projectId) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data) => executionsApi.create(projectId, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['executions', projectId] }),
  })
}

export function useExecutionResults(executionId) {
  return useQuery({
    queryKey: ['results', executionId],
    queryFn: () => executionsApi.listResults(executionId),
    enabled: !!executionId,
  })
}

export function useUpdateResult(executionId) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }) => executionsApi.updateResult(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['results', executionId] }),
  })
}
