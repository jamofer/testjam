import { useMemo } from "react"
import { useQueryClient } from "@tanstack/react-query"
import { useTopicSocket } from "./useTopicSocket"

export function useCaseLive(caseId, { enabled = true } = {}) {
  const queryClient = useQueryClient()

  const topics = useMemo(
    () => (caseId ? [`case:${caseId}`] : []),
    [caseId],
  )

  const handlers = useMemo(() => ({
    "case.comment.added": (comment) => {
      if (!comment?.test_case_id) return
      queryClient.setQueryData(["case-comments", comment.test_case_id], (rows = []) =>
        rows.some(row => row.id === comment.id) ? rows : [...rows, comment],
      )
    },
    "case.comment.updated": (comment) => {
      if (!comment?.test_case_id) return
      queryClient.setQueryData(["case-comments", comment.test_case_id], (rows = []) =>
        rows.map(row => (row.id === comment.id ? comment : row)),
      )
    },
    "case.comment.deleted": ({ id } = {}) => {
      if (!id || !caseId) return
      queryClient.setQueryData(["case-comments", caseId], (rows = []) =>
        rows.filter(row => row.id !== id),
      )
    },
  }), [queryClient, caseId])

  return useTopicSocket(topics, handlers, { enabled })
}
