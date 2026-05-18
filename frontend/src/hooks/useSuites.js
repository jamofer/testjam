import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { suitesApi, casesApi } from "../api/testcases"

export function sortSuitesHierarchically(suites) {
  const byParent = {}
  for (const s of suites) {
    const key = s.parent_suite_id ?? null
    if (!byParent[key]) byParent[key] = []
    byParent[key].push(s)
  }
  const result = []
  const visit = (parentId) => {
    for (const s of (byParent[parentId] ?? [])) {
      result.push(s)
      visit(s.id)
    }
  }
  visit(null)
  return result
}

export function useSuites(projectId) {
  return useQuery({
    queryKey: ["suites-list", projectId],
    queryFn: () => suitesApi.list(projectId),
    enabled: !!projectId,
  })
}

export function useSuitesAll(projectId) {
  return useQuery({
    queryKey: ["suites-list-all", projectId],
    queryFn: () => suitesApi.listAll(projectId),
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

export function useArchiveSuite(projectId) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: suitesApi.archive,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["suites-list", projectId] })
      qc.invalidateQueries({ queryKey: ["suites-list-all", projectId] })
    },
  })
}

export function useReorderProjectSuites(projectId) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ suiteIds, parentSuiteId = null }) =>
      suitesApi.reorderProjectSuites(projectId, suiteIds, parentSuiteId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["suites-list", projectId] })
      qc.invalidateQueries({ queryKey: ["suites-list-all", projectId] })
    },
  })
}

export function useReorderSuiteCases(suiteId) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (caseIds) => casesApi.reorderInSuite(suiteId, caseIds),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["cases-list", suiteId] }),
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

export function useSearchCases(projectId, { q, tags } = {}) {
  const enabled = Boolean(projectId) && (Boolean(q) || (Array.isArray(tags) && tags.length > 0))
  return useQuery({
    queryKey: ["cases-search", projectId, q || "", tags || []],
    queryFn: () => casesApi.search(projectId, { q, tags }),
    enabled,
    placeholderData: (prev) => prev,
  })
}

export function useCreateCase(suiteId) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data) => casesApi.create(suiteId, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["cases-list", suiteId] })
      qc.invalidateQueries({ queryKey: ["suites-list"] })
      qc.invalidateQueries({ queryKey: ["suites-list-all"] })
    },
  })
}

export function useUpdateCase(id) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data) => casesApi.update(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["case", id] })
      qc.invalidateQueries({ queryKey: ["case-revisions", id] })
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

export function useCaseRevisions(caseId) {
  return useQuery({
    queryKey: ["case-revisions", caseId],
    queryFn: () => casesApi.listRevisions(caseId),
    enabled: !!caseId,
  })
}

export function useCaseRevision(caseId, revId) {
  return useQuery({
    queryKey: ["case-revision", caseId, revId],
    queryFn: () => casesApi.getRevision(caseId, revId),
    enabled: !!caseId && !!revId,
  })
}

export function useCaseComments(caseId) {
  return useQuery({
    queryKey: ["case-comments", caseId],
    queryFn: () => casesApi.listComments(caseId),
    enabled: !!caseId,
  })
}

export function useAddCaseComment() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ caseId, body }) => casesApi.addComment(caseId, body),
    onSuccess: (comment) =>
      qc.invalidateQueries({ queryKey: ["case-comments", comment.test_case_id] }),
  })
}

export function useUpdateCaseComment() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ caseId, commentId, body }) =>
      casesApi.updateComment(caseId, commentId, body),
    onSuccess: (comment) =>
      qc.invalidateQueries({ queryKey: ["case-comments", comment.test_case_id] }),
  })
}

export function useDeleteCaseComment() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ caseId, commentId }) => casesApi.deleteComment(caseId, commentId),
    onSuccess: (_response, variables) =>
      qc.invalidateQueries({ queryKey: ["case-comments", variables.caseId] }),
  })
}

export function useReorderSteps(caseId) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (stepIds) => casesApi.reorderSteps(caseId, stepIds),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["case", caseId] })
      qc.invalidateQueries({ queryKey: ["case-revisions", caseId] })
    },
  })
}

export function useReorderSuiteSteps(projectId) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ suiteId, stepIds }) => suitesApi.reorderSteps(suiteId, stepIds),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["suites-list", projectId] }),
  })
}
