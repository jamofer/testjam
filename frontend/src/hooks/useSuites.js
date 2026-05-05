import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { suitesApi, casesApi } from "../api/testcases"

export function useSuites(projectId) {
  return useQuery({
    queryKey: ["suites-list", projectId],
    queryFn: () => suitesApi.list(projectId),
    enabled: !!projectId,
  })
}

export function useChildSuites(projectId, parentSuiteId) {
  return useQuery({
    queryKey: ["suites-list", projectId, parentSuiteId],
    queryFn: () => suitesApi.listChildren(projectId, parentSuiteId),
    enabled: !!projectId && parentSuiteId != null,
  })
}

export function useSuite(id) {
  return useQuery({ queryKey: ["suite", id], queryFn: () => suitesApi.get(id), enabled: !!id })
}

export function useCreateSuite(projectId) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data) => suitesApi.create(projectId, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["suites-list", projectId] }),
  })
}

export function useUpdateSuite(projectId) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }) => suitesApi.update(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["suites-list", projectId] }),
  })
}

export function useDeleteSuite(projectId) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: suitesApi.delete,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["suites-list", projectId] }),
  })
}

export function useCases(suiteId) {
  return useQuery({
    queryKey: ["cases-list", suiteId],
    queryFn: () => casesApi.list(suiteId),
    enabled: !!suiteId,
  })
}

export function useCase(id) {
  return useQuery({ queryKey: ["case", id], queryFn: () => casesApi.get(id), enabled: !!id })
}

export function useCreateCase(suiteId) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data) => casesApi.create(suiteId, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["cases-list", suiteId] }),
  })
}

export function useUpdateCase(id) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data) => casesApi.update(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["case", id] })
    },
  })
}

export function useDeleteCase(suiteId) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: casesApi.delete,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["cases-list", suiteId] }),
  })
}

export function useBulkDeleteCases(suiteId) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: casesApi.bulkDelete,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["cases-list", suiteId] }),
  })
}

export function useReorderSteps(caseId) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (stepIds) => casesApi.reorderSteps(caseId, stepIds),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["case", caseId] }),
  })
}

export function useReorderSuiteSteps(projectId) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ suiteId, stepIds }) => suitesApi.reorderSteps(suiteId, stepIds),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["suites-list", projectId] }),
  })
}
