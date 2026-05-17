import { createContext, useContext, useMemo } from "react"
import { useQuery } from "@tanstack/react-query"

import { mentionsApi } from "../../api/mentions"
import { parse } from "../../lib/mentions/parser"

const MentionResolveContext = createContext(null)
const STALE_MS = 60_000

// Parses the markdown source once, batches every detected token to
// /mentions/resolve, and exposes a lookup map keyed by `kind|id|sub_ids|slug`
// so each MentionChip can pick up its enriched label / accessibility without
// triggering its own request.
export function MentionResolveProvider({ projectId, source, children }) {
  const tokens = useMemo(() => collectTokens(source), [source])
  const { data = [] } = useQuery({
    queryKey: ["mentions-resolve", projectId, tokens],
    queryFn: () => mentionsApi.resolve(projectId, tokens).then(payload => payload.mentions),
    enabled: !!projectId && tokens.length > 0,
    staleTime: STALE_MS,
  })

  const lookup = useMemo(() => buildLookup(data), [data])
  return (
    <MentionResolveContext.Provider value={lookup}>
      {children}
    </MentionResolveContext.Provider>
  )
}

export function useResolvedMention(token) {
  const lookup = useContext(MentionResolveContext)
  if (!lookup) return null
  return lookup.get(keyFor(token)) ?? null
}

function collectTokens(source) {
  return parse(source ?? "").map(token => ({
    kind: token.kind,
    slug: token.slug,
    id: token.id,
    sub_ids: token.sub_ids ?? [],
  }))
}

function buildLookup(mentions) {
  const map = new Map()
  for (const mention of mentions) {
    map.set(keyFor(mention), mention)
  }
  return map
}

function keyFor(token) {
  return [
    token.kind,
    token.slug ?? "",
    token.id ?? "",
    (token.sub_ids ?? []).join(","),
  ].join("|")
}
