import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { customFieldsApi } from '../api/customFields'

const queryKey = (projectId, entityType, includeArchived) =>
  ['customFields', projectId, entityType, { includeArchived }]

export function useCustomFields(projectId, entityType, { includeArchived = false } = {}) {
  return useQuery({
    queryKey: queryKey(projectId, entityType, includeArchived),
    queryFn: () => customFieldsApi.list(projectId, entityType, { includeArchived }),
    enabled: !!projectId && !!entityType,
  })
}

function invalidateAll(queryClient, projectId) {
  queryClient.invalidateQueries({ queryKey: ['customFields', projectId] })
}

export function useCreateCustomField(projectId) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data) => customFieldsApi.create(projectId, data),
    onSuccess: () => invalidateAll(queryClient, projectId),
  })
}

export function useUpdateCustomField(projectId) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }) => customFieldsApi.update(id, data),
    onSuccess: () => invalidateAll(queryClient, projectId),
  })
}

export function useArchiveCustomField(projectId) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id) => customFieldsApi.archive(id),
    onSuccess: () => invalidateAll(queryClient, projectId),
  })
}

export function useUnarchiveCustomField(projectId) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id) => customFieldsApi.unarchive(id),
    onSuccess: () => invalidateAll(queryClient, projectId),
  })
}

export function useDeleteCustomField(projectId) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id) => customFieldsApi.delete(id),
    onSuccess: () => invalidateAll(queryClient, projectId),
  })
}

export function useReorderCustomFields(projectId) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (ids) => customFieldsApi.reorder(projectId, ids),
    onSuccess: () => invalidateAll(queryClient, projectId),
  })
}
