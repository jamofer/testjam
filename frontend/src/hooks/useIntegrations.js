import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { integrationsApi } from '../api/integrations'


export function useIntegrationProviders() {
  return useQuery({
    queryKey: ['integration-providers'],
    queryFn: integrationsApi.listProviders,
    staleTime: 5 * 60_000,
  })
}

export function useIntegrations(projectId) {
  return useQuery({
    queryKey: ['integrations', projectId],
    queryFn: () => integrationsApi.list(projectId),
    enabled: !!projectId,
  })
}

export function useCreateIntegration(projectId) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data) => integrationsApi.create(projectId, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['integrations', projectId] }),
  })
}

export function useUpdateIntegration(projectId) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }) => integrationsApi.update(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['integrations', projectId] }),
  })
}

export function useDeleteIntegration(projectId) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id) => integrationsApi.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['integrations', projectId] }),
  })
}

export function useTestIntegration() {
  return useMutation({
    mutationFn: (id) => integrationsApi.test(id),
  })
}

export function useRotateIntegrationCredential(projectId) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, secret }) => integrationsApi.rotateCredential(id, secret),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['integrations', projectId] }),
  })
}

export function useBugExternalLinks(bugId) {
  return useQuery({
    queryKey: ['bug-external-links', bugId],
    queryFn: () => integrationsApi.listBugLinks(bugId),
    enabled: !!bugId,
  })
}

export function usePushBugToIntegration(bugId) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ integrationId, labels }) =>
      integrationsApi.pushBug(bugId, integrationId, labels),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['bug-external-links', bugId] }),
  })
}

export function useSyncBugExternalLink(bugId) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (linkId) => integrationsApi.syncBugLink(bugId, linkId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['bug-external-links', bugId] }),
  })
}

export function useDeleteBugExternalLink(bugId) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (linkId) => integrationsApi.deleteBugLink(bugId, linkId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['bug-external-links', bugId] }),
  })
}
