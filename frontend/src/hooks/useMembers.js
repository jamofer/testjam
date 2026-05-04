import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { membersApi } from '../api/members'

export function useMembers(projectId) {
  return useQuery({
    queryKey: ['members', projectId],
    queryFn: () => membersApi.list(projectId),
    enabled: !!projectId,
  })
}

export function useAddMember(projectId) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data) => membersApi.add(projectId, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['members', projectId] }),
  })
}

export function useUpdateMember(projectId) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ userId, data }) => membersApi.update(projectId, userId, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['members', projectId] }),
  })
}

export function useRemoveMember(projectId) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (userId) => membersApi.remove(projectId, userId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['members', projectId] }),
  })
}
