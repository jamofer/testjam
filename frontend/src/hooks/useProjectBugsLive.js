import { useMemo } from "react"
import { useQueryClient } from "@tanstack/react-query"
import { useTopicSocket } from "./useTopicSocket"

export function useProjectBugsLive(projectId, { enabled = true } = {}) {
  const queryClient = useQueryClient()

  const topics = useMemo(
    () => (projectId ? [`project:${projectId}`] : []),
    [projectId],
  )

  const handlers = useMemo(() => ({
    "bug.created": (data) => {
      if (!data?.id) return
      mutateBugLists(queryClient, projectId, (rows) =>
        rows.some(row => row.id === data.id) ? rows : [data, ...rows],
      )
    },
    "bug.updated": (data) => upsertOne(queryClient, projectId, data),
    "bug.assigned": (data) => upsertOne(queryClient, projectId, data),
    "bug.status_changed": (data) => {
      upsertOne(queryClient, projectId, data)
      if (data?.id) {
        queryClient.invalidateQueries({ queryKey: ["bug-history", data.id] })
      }
    },
    "bug.deleted": ({ id } = {}) => {
      if (!id) return
      mutateBugLists(queryClient, projectId, (rows) => rows.filter(row => row.id !== id))
      queryClient.removeQueries({ queryKey: ["bug", id] })
    },
  }), [queryClient, projectId])

  return useTopicSocket(topics, handlers, { enabled })
}

function upsertOne(queryClient, projectId, data) {
  if (!data?.id) return
  queryClient.setQueryData(["bug", data.id], (previous) =>
    previous ? { ...previous, ...data } : data,
  )
  mutateBugLists(queryClient, projectId, (rows) =>
    rows.map(row => (row.id === data.id ? { ...row, ...data } : row)),
  )
}

function mutateBugLists(queryClient, projectId, transform) {
  queryClient.setQueriesData(
    { queryKey: ["bugs", projectId] },
    (oldData) => (Array.isArray(oldData) ? transform(oldData) : oldData),
  )
}
