import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { environmentsApi } from '../api/environments'

export function useEnvironments(projectId, { includeArchived = false } = {}) {
  return useQuery({
    queryKey: ['environments', projectId, { includeArchived }],
    queryFn: () => environmentsApi.list(projectId, { includeArchived }),
    enabled: !!projectId,
  })
}

function invalidateAll(qc, projectId) {
  qc.invalidateQueries({ queryKey: ['environments', projectId] })
}

export function useCreateEnvironment(projectId) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data) => environmentsApi.create(projectId, data),
    onSuccess: () => invalidateAll(qc, projectId),
  })
}

export function useUpdateEnvironment(projectId) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }) => environmentsApi.update(id, data),
    onSuccess: () => invalidateAll(qc, projectId),
  })
}

export function useArchiveEnvironment(projectId) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id) => environmentsApi.archive(id),
    onSuccess: () => invalidateAll(qc, projectId),
  })
}

export function useUnarchiveEnvironment(projectId) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id) => environmentsApi.unarchive(id),
    onSuccess: () => invalidateAll(qc, projectId),
  })
}

export function useDeleteEnvironment(projectId) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id) => environmentsApi.delete(id),
    onSuccess: () => invalidateAll(qc, projectId),
  })
}

export function useReorderEnvironments(projectId) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (ids) => environmentsApi.reorder(projectId, ids),
    onSuccess: () => invalidateAll(qc, projectId),
  })
}
