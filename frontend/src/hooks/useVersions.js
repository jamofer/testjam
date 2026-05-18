import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { versionsApi } from '../api/versions'

export function useVersions(projectId) {
  return useQuery({
    queryKey: ['versions', projectId],
    queryFn: () => versionsApi.list(projectId),
    enabled: !!projectId,
  })
}

export function useVersion(id) {
  return useQuery({
    queryKey: ['version', id],
    queryFn: () => versionsApi.get(id),
    enabled: !!id,
  })
}

export function useCreateVersion(projectId) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data) => versionsApi.create(projectId, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['versions', projectId] }),
  })
}

export function useUpdateVersion(projectId) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }) => versionsApi.update(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['versions', projectId] })
      qc.invalidateQueries({ queryKey: ['version'] })
    },
  })
}

export function useDeleteVersion(projectId) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id) => versionsApi.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['versions', projectId] }),
  })
}

export function useVersionAttachments(versionId) {
  return useQuery({
    queryKey: ['version-attachments', versionId],
    queryFn: () => versionsApi.listAttachments(versionId),
    enabled: !!versionId,
  })
}

export function useUploadVersionAttachment(versionId) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (file) => versionsApi.uploadAttachment(versionId, file),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['version-attachments', versionId] }),
  })
}

export function useDeleteVersionAttachment(versionId) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (attachmentId) => versionsApi.deleteAttachment(versionId, attachmentId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['version-attachments', versionId] }),
  })
}
