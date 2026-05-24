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
      mutateBugLists(queryClient, projectId, (rows, params) =>
        bugMatchesParams(data, params)
          ? (rows.some(row => row.id === data.id) ? rows : [data, ...rows])
          : rows.filter(row => row.id !== data.id),
      )
    },
    "bug.updated": (data) => upsertOne(queryClient, projectId, data),
    "bug.assigned": (data) => upsertOne(queryClient, projectId, data),
    "bug.status_changed": (data) => {
      upsertOne(queryClient, projectId, data)
      if (data?.id) {
        queryClient.invalidateQueries({ queryKey: ["bug-activity", data.id] })
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
  mutateBugLists(queryClient, projectId, (rows, params) => {
    const present = rows.some(row => row.id === data.id)
    if (bugMatchesParams(data, params)) {
      return present
        ? rows.map(row => (row.id === data.id ? { ...row, ...data } : row))
        : [data, ...rows]
    }
    return present ? rows.filter(row => row.id !== data.id) : rows
  })
}

function mutateBugLists(queryClient, projectId, transform) {
  const cache = queryClient.getQueryCache()
  for (const query of cache.findAll({ queryKey: ["bugs", projectId] })) {
    const previous = query.state.data
    if (!Array.isArray(previous)) continue
    const params = query.queryKey[2] ?? {}
    queryClient.setQueryData(query.queryKey, transform(previous, params))
  }
}

function bugMatchesParams(bug, params) {
  if (!bug) return false
  if (params.status && bug.status !== params.status) return false
  if (params.severity && bug.severity !== params.severity) return false
  if (params.version_id != null && Number(bug.version_id) !== Number(params.version_id)) {
    return false
  }
  if (params.fixed_in_version_id != null
      && Number(bug.fixed_in_version_id) !== Number(params.fixed_in_version_id)) {
    return false
  }
  if (params.assigned_to_id != null
      && Number(bug.assigned_to?.id ?? -1) !== Number(params.assigned_to_id)) {
    return false
  }
  if (params.tag && !(Array.isArray(bug.tags) && bug.tags.includes(params.tag))) {
    return false
  }
  if (params.cf_key) {
    const value = bug.custom_fields?.[params.cf_key]
    if (value == null) return false
    if (params.cf_value) {
      if (Array.isArray(value)) {
        if (!value.map(String).includes(params.cf_value)) return false
      } else if (typeof value === "boolean") {
        if (String(value).toLowerCase() !== String(params.cf_value).toLowerCase()) return false
      } else if (String(value) !== params.cf_value) {
        return false
      }
    }
  }
  if (params.search && !bug.title?.toLowerCase().includes(params.search.toLowerCase())) {
    return false
  }
  return true
}
