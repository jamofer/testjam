import { useMemo } from "react"
import { useQueryClient } from "@tanstack/react-query"
import { useTopicSocket } from "./useTopicSocket"

export function useBugLive(bugId, { enabled = true } = {}) {
  const queryClient = useQueryClient()

  const topics = useMemo(
    () => (bugId ? [`bug:${bugId}`] : []),
    [bugId],
  )

  const handlers = useMemo(() => ({
    "bug.comment.added": (comment) => {
      if (!comment?.bug_id) return
      queryClient.setQueryData(["bug-comments", comment.bug_id], (rows = []) =>
        rows.some(row => row.id === comment.id) ? rows : [...rows, comment],
      )
    },
    "bug.comment.updated": (comment) => {
      if (!comment?.bug_id) return
      queryClient.setQueryData(["bug-comments", comment.bug_id], (rows = []) =>
        rows.map(row => (row.id === comment.id ? comment : row)),
      )
    },
    "bug.comment.deleted": ({ id } = {}) => {
      if (!id || !bugId) return
      queryClient.setQueryData(["bug-comments", bugId], (rows = []) =>
        rows.filter(row => row.id !== id),
      )
    },
    "bug.history.added": (entry) => {
      if (!entry?.bug_id) return
      queryClient.setQueryData(["bug-history", entry.bug_id], (rows = []) =>
        rows.some(row => row.id === entry.id) ? rows : [...rows, entry],
      )
    },
    "bug.attachment.added": (attachment) => {
      if (!attachment?.bug_id) return
      queryClient.setQueryData(["bug-attachments", attachment.bug_id], (rows = []) =>
        rows.some(row => row.id === attachment.id) ? rows : [...rows, attachment],
      )
    },
    "bug.attachment.deleted": ({ id } = {}) => {
      if (!id || !bugId) return
      queryClient.setQueryData(["bug-attachments", bugId], (rows = []) =>
        rows.filter(row => row.id !== id),
      )
    },
    "bug.link.added": (link) => {
      if (!link?.bug_id) return
      queryClient.setQueryData(["bug-links", link.bug_id], (rows = []) =>
        rows.some(row => row.id === link.id) ? rows : [...rows, link],
      )
    },
    "bug.link.deleted": ({ id } = {}) => {
      if (!id || !bugId) return
      queryClient.setQueryData(["bug-links", bugId], (rows = []) =>
        rows.filter(row => row.id !== id),
      )
    },
  }), [queryClient, bugId])

  return useTopicSocket(topics, handlers, { enabled })
}
