import { Link } from "react-router-dom"

// Renders a mention token detected by rehypeMentions. The `data-*` attributes
// are emitted by the rehype plugin; we only render the canonical raw token as
// a styled link. Hover/preview/access checks happen via the resolve endpoint
// in a later iteration — keeping this MVP purely static.

const STYLE_BY_KIND = {
  user: "bg-blue-50 text-blue-700 dark:bg-blue-950 dark:text-blue-300 border-blue-200 dark:border-blue-900",
  bug: "bg-red-50 text-red-700 dark:bg-red-950 dark:text-red-300 border-red-200 dark:border-red-900",
  execution: "bg-amber-50 text-amber-700 dark:bg-amber-950 dark:text-amber-300 border-amber-200 dark:border-amber-900",
  result: "bg-amber-50 text-amber-700 dark:bg-amber-950 dark:text-amber-300 border-amber-200 dark:border-amber-900",
  step_result: "bg-amber-50 text-amber-700 dark:bg-amber-950 dark:text-amber-300 border-amber-200 dark:border-amber-900",
  case: "bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300 border-emerald-200 dark:border-emerald-900",
}

export function MentionChip({ kind, raw, slug, id, subIds, projectId }) {
  const url = buildUrl({ kind, slug, id, subIds, projectId })
  const className = `inline-flex items-center px-1.5 py-0.5 mx-0.5 rounded text-[12px] font-medium border ${STYLE_BY_KIND[kind] ?? ""} no-underline hover:underline`
  if (!url) {
    return <span className={className}>{raw}</span>
  }
  return (
    <Link to={url} className={className}>{raw}</Link>
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
  if (kind === "step_result" && id != null && subIds?.[1] != null) {
    return `/executions/${id}/run#step-${subIds[1]}`
  }
  if (kind === "case" && id != null) return `/cases/${id}`
  return null
}
