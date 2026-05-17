import { useTranslation } from "react-i18next"

import { useDatePreferences } from "../../hooks/useDatePreferences"
import { fmtDate, fmtDateTime, fmtRelative } from "../../lib/format"

export function DateLabel({ iso, mode = "auto", className }) {
  const { i18n } = useTranslation()
  const { timezone, useRelativeDates } = useDatePreferences()
  if (!iso) return null
  const locale = i18n.language
  const showRelative = mode === "relative" || (mode === "auto" && useRelativeDates)
  const absolute = fmtDateTime(iso, timezone, locale)
  if (!showRelative) {
    return <span className={className} title={`${absolute} (${timezone})`}>{absolute}</span>
  }
  return (
    <span className={className} title={`${absolute} (${timezone})`}>
      {fmtRelative(iso, new Date(), locale)}
    </span>
  )
}

export function DateText({ iso, className }) {
  const { i18n } = useTranslation()
  const { timezone } = useDatePreferences()
  if (!iso) return null
  return <span className={className}>{fmtDate(iso, timezone, i18n.language)}</span>
}
