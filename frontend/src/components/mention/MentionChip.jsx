import { Link } from "react-router-dom"

import { useResolvedMention } from "./MentionResolveContext"

// Renders a mention token detected by rehypeMentions. The `data-*` attributes
// are emitted by the rehype plugin; if a MentionResolveProvider is in the tree
// the chip swaps the raw token for the resolved label and follows the resolver
// URL. Composite mentions (result, step_result) render as a breadcrumb chain
// of color-coded badges, one per level — the outer link still navigates to
// the deepest target.

const BADGE_BY_KIND = {
  user: "bg-rose-50 text-rose-700 border-rose-200 dark:bg-rose-950 dark:text-rose-300 dark:border-rose-900",
  bug: "bg-red-50 text-red-700 border-red-200 dark:bg-red-950 dark:text-red-300 dark:border-red-900",
  execution: "bg-sky-50 text-sky-700 border-sky-200 dark:bg-sky-950 dark:text-sky-300 dark:border-sky-900",
  result: "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950 dark:text-amber-300 dark:border-amber-900",
  step_result: "bg-gray-100 text-gray-700 border-gray-200 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-700",
  case: "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950 dark:text-amber-300 dark:border-amber-900",
}

const UNRESOLVED_BADGE = "bg-gray-100 text-gray-500 border-gray-200 dark:bg-gray-800 dark:text-gray-500 dark:border-gray-700 line-through"

export function MentionChip({ kind, raw, slug, id, subIds, projectId }) {
  const resolved = useResolvedMention({ kind, slug, id, sub_ids: subIds ?? [] })
  const accessible = resolved?.accessible !== false
  const url = accessible
    ? (resolved?.url ?? buildUrl({ kind, slug, id, subIds, projectId }))
    : null
  const tooltip = resolved?.description ?? undefined

  const parts = accessible && resolved?.parts?.length
    ? resolved.parts
    : [{ kind, label: accessible ? (resolved?.label || raw) : raw }]

  const containerClass = `inline-flex items-stretch align-baseline rounded border overflow-hidden text-[12px] font-medium leading-[1.4] !no-underline ${
    accessible ? "border-gray-200 dark:border-gray-700 hover:brightness-110" : "border-gray-200 dark:border-gray-700 opacity-70"
  }`

  const segments = parts.map((part, index) => {
    const palette = accessible ? (BADGE_BY_KIND[part.kind] ?? "") : UNRESOLVED_BADGE
    const divider = index > 0 ? "border-l border-gray-200 dark:border-gray-700" : ""
    return (
      <span key={index} className={`inline-flex items-center px-1.5 ${palette} ${divider}`}>
        {part.label}
      </span>
    )
  })

  if (!url) {
    return <span className={containerClass} title={tooltip}>{segments}</span>
  }
  return (
    <Link to={url} className={containerClass} title={tooltip}>
      {segments}
    </Link>
  )
}

export function isMentionElement(props) {
  return props?.["data-mention"] === "true"
}

export function chipPropsFromAttributes(props) {
  const subIdsRaw = props["data-mention-sub-ids"]
  return {
    kind: props["data-mention-kind"],
    raw: props["data-mention-raw"],
    slug: props["data-mention-slug"],
    id: props["data-mention-id"] ? Number(props["data-mention-id"]) : undefined,
    subIds: subIdsRaw ? subIdsRaw.split(",").map(Number) : [],
  }
}

function buildUrl({ kind, slug, id, subIds, projectId }) {
  if (kind === "user" && slug) return `/users/${slug}`
  if (kind === "bug" && id != null && projectId) {
    return `/projects/${projectId}/bugs/${id}`
  }
  if (kind === "execution" && id != null) return `/executions/${id}/run`
  if (kind === "result" && id != null && subIds?.[0] != null) {
    return `/executions/${id}/run#result-${subIds[0]}`
  }
  if (kind === "step_result" && id != null && subIds?.[0] != null && subIds?.[1] != null) {
    return `/executions/${id}/run#result-${subIds[0]}-step-${subIds[1]}`
  }
  if (kind === "case" && id != null) return `/cases/${id}`
  return null
}
