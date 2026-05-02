import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { suitesApi, casesApi } from "../api/testcases"

export function useSuites(projectId) {
  return useQuery({
    queryKey: ["suites", projectId],
    queryFn: () => suitesApi.list(projectId),
    enabled: !!projectId,
  })
}

export function useSuite(id) {
  return useQuery({ queryKey: ["suites", id], queryFn: () => suitesApi.get(id), enabled: !!id })
}

export function useCreateSuite(projectId) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data) => suitesApi.create(projectId, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["suites", projectId] }),
  })
}

export function useDeleteSuite(projectId) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: suitesApi.delete,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["suites", projectId] }),
  })
}

export function useCases(suiteId) {
  return useQuery({
    queryKey: ["cases", suiteId],
    queryFn: () => casesApi.list(suiteId),
    enabled: !!suiteId,
  })
}

export function useCase(id) {
  return useQuery({ queryKey: ["cases", id], queryFn: () => casesApi.get(id), enabled: !!id })
}

export function useCreateCase(suiteId) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data) => casesApi.create(suiteId, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["cases", suiteId] }),
  })
}

export function useUpdateCase(id) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data) => casesApi.update(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["cases", id] })
    },
  })
}

export function useDeleteCase(suiteId) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: casesApi.delete,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["cases", suiteId] }),
  })
}
