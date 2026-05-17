import { useEffect, useState } from "react"
import { useQuery } from "@tanstack/react-query"

import { mentionsApi } from "../api/mentions"
import { useDebounced } from "./useDebounced"

const SEARCH_DEBOUNCE_MS = 150
const STALE_MS = 60_000

export function useMentionSearch(projectId, kind, query, { enabled = true } = {}) {
  const debouncedQuery = useDebounced(query ?? "", SEARCH_DEBOUNCE_MS)
  const isEnabled = enabled && !!projectId && !!kind
  return useQuery({
    queryKey: ["mentions-search", projectId, kind, debouncedQuery],
    queryFn: () => mentionsApi.search(projectId, kind, debouncedQuery, 10),
    enabled: isEnabled,
    staleTime: STALE_MS,
    select: data => data?.hits ?? [],
    placeholderData: previous => previous,
  })
}

// Tracks the selected index inside the popover. Resets to 0 whenever the hits
// list changes so the highlight stays on the first row after a new search.
export function useSelectedIndex(hits) {
  const [index, setIndex] = useState(0)
  useEffect(() => { setIndex(0) }, [hits])
  return [index, setIndex]
}
