import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { projectsApi } from '../api/projects'

export function useProjects({ includeArchived = false } = {}) {
  return useQuery({
    queryKey: ['projects', { includeArchived }],
    queryFn: () => projectsApi.list({ includeArchived }),
  })
}

export function useProject(id) {
  return useQuery({ queryKey: ['projects', id], queryFn: () => projectsApi.get(id), enabled: !!id })
}

export function useCreateProject() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: projectsApi.create,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['projects'] }),
  })
}

export function useDeleteProject() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: projectsApi.delete,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['projects'] }),
  })
}

export function useArchiveProject() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: projectsApi.archive,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['projects'] }),
  })
}

export function useUnarchiveProject() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: projectsApi.unarchive,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['projects'] }),
  })
}
