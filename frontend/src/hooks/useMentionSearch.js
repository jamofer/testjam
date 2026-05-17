import { useEffect, useState } from "react"
import { useQuery } from "@tanstack/react-query"

import { mentionsApi } from "../api/mentions"
import { useDebounced } from "./useDebounced"

const SEARCH_DEBOUNCE_MS = 150
const STALE_MS = 60_000

export function useMentionSearch(projectId, kind, query, { enabled = true, parents = [] } = {}) {
  const debouncedQuery = useDebounced(query ?? "", SEARCH_DEBOUNCE_MS)
  const isEnabled = enabled && !!projectId && !!kind && _hasRequiredParents(kind, parents)
  return useQuery({
    queryKey: ["mentions-search", projectId, kind, debouncedQuery, parents],
    queryFn: () => mentionsApi.search(projectId, kind, debouncedQuery, 10, parents),
    enabled: isEnabled,
    staleTime: STALE_MS,
    select: data => data?.hits ?? [],
    placeholderData: previous => previous,
  })
}

function _hasRequiredParents(kind, parents) {
  if (kind === "result") return parents.length >= 1
  if (kind === "step_result") return parents.length >= 2
  return true
}

// Tracks the selected index inside the popover. Resets to 0 whenever the hits
// list changes so the highlight stays on the first row after a new search.
export function useSelectedIndex(hits) {
  const [index, setIndex] = useState(0)
  useEffect(() => { setIndex(0) }, [hits])
  return [index, setIndex]
}
