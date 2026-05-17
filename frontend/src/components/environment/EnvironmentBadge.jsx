import { useEnvironments } from "../../hooks/useEnvironments"

const FALLBACK_BG = "bg-gray-100 dark:bg-gray-800"
const FALLBACK_TEXT = "text-gray-700 dark:text-gray-300"

export function EnvironmentBadge({ projectId, slug, className = "" }) {
  const { data: environments = [] } = useEnvironments(projectId, { includeArchived: true })

  if (!slug) return null

  const match = environments.find(env => env.slug === slug)
  const label = match?.name ?? slug
  const inlineStyle = match?.color
    ? { backgroundColor: hexToTintBg(match.color), color: match.color, borderColor: match.color }
    : null
  const colorClasses = inlineStyle ? "" : `${FALLBACK_BG} ${FALLBACK_TEXT}`

  return (
    <span
      style={inlineStyle ?? undefined}
      className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium border-transparent ${colorClasses} ${className}`}
    >
      {label}
    </span>
  )
}

function hexToTintBg(hex) {
  const normalized = hex.startsWith("#") ? hex.slice(1) : hex
  const full =
    normalized.length === 3
      ? normalized
          .split("")
          .map(c => c + c)
          .join("")
      : normalized
  const r = parseInt(full.slice(0, 2), 16)
  const g = parseInt(full.slice(2, 4), 16)
  const b = parseInt(full.slice(4, 6), 16)
  if ([r, g, b].some(Number.isNaN)) return undefined
  return `rgba(${r}, ${g}, ${b}, 0.15)`
}
