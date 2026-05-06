import { useInfiniteQuery, useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { executionsApi } from '../api/executions'

const PAGE_SIZE = 50

export function useExecutions(projectId, params) {
  return useInfiniteQuery({
    queryKey: ['executions', projectId, params],
    queryFn: ({ pageParam = 0 }) =>
      executionsApi.list(projectId, { ...params, skip: pageParam, limit: PAGE_SIZE }),
    getNextPageParam: (lastPage, pages) =>
      lastPage.length === PAGE_SIZE ? pages.length * PAGE_SIZE : undefined,
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
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['results', executionId] })
      qc.invalidateQueries({ queryKey: ['executions', executionId] })
    },
  })
}
