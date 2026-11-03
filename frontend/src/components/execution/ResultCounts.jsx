import { useTranslation } from "react-i18next"

import { STATUS_CONFIG, STATUS_KEYS } from "../../lib/statusConfig"

/**
 * Passed / failed / blocked / not run tallies with the shared status icons
 * and colours. Accepts either a summary object or a row carrying the counts.
 */
export function ResultCounts({ counts, iconSize = 10, className = "" }) {
  const { t } = useTranslation("common")
  return (
    <span className={`inline-flex items-center gap-1.5 shrink-0 ${className}`}>
      {STATUS_KEYS.map(status => {
        const { icon: Icon, iconColor } = STATUS_CONFIG[status]
        return (
          <span key={status} className="inline-flex items-center gap-0.5" title={t(`status.${status}`)}>
            <Icon size={iconSize} className={iconColor} aria-hidden="true" />
            {counts?.[status] ?? 0}
          </span>
        )
      })}
    </span>
  )
}
