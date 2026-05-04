import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { tokensApi } from '../api/tokens'

export function useUserTokens() {
  return useQuery({ queryKey: ['user-tokens'], queryFn: tokensApi.listUser })
}

export function useCreateUserToken() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: tokensApi.createUser,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['user-tokens'] }),
  })
}

export function useRevokeUserToken() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: tokensApi.revokeUser,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['user-tokens'] }),
  })
}

export function useProjectTokens(projectId) {
  return useQuery({
    queryKey: ['project-tokens', projectId],
    queryFn: () => tokensApi.listProject(projectId),
    enabled: !!projectId,
  })
}

export function useCreateProjectToken(projectId) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data) => tokensApi.createProject(projectId, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['project-tokens', projectId] }),
  })
}

export function useRevokeProjectToken(projectId) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (tokenId) => tokensApi.revokeProject(projectId, tokenId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['project-tokens', projectId] }),
  })
}
