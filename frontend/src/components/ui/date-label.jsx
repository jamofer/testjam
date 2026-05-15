import { useDatePreferences } from "../../hooks/useDatePreferences"
import { fmtDate, fmtDateTime, fmtRelative } from "../../lib/format"

export function DateLabel({ iso, mode = "auto", className }) {
  const { timezone, useRelativeDates } = useDatePreferences()
  if (!iso) return null
  const showRelative = mode === "relative" || (mode === "auto" && useRelativeDates)
  const absolute = fmtDateTime(iso, timezone)
  if (!showRelative) {
    return <span className={className} title={`${absolute} (${timezone})`}>{absolute}</span>
  }
  return (
    <span className={className} title={`${absolute} (${timezone})`}>
      {fmtRelative(iso)}
    </span>
  )
}

export function DateText({ iso, className }) {
  const { timezone } = useDatePreferences()
  if (!iso) return null
  return <span className={className}>{fmtDate(iso, timezone)}</span>
}
