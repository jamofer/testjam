import { Link } from "react-router-dom"
import { useTranslation } from "react-i18next"
import { Bug as BugIcon } from "lucide-react"

import { useBugs } from "../../hooks/useBugs"
import { Badge } from "../ui/badge"
import { Skeleton } from "../ui/skeleton"

const ACTIVE_STATUSES = new Set(["open", "in_progress"])
const SEVERITY_ORDER = ["critical", "high", "medium", "low"]
const SEVERITY_VARIANT = {
  critical: "destructive",
  high: "warning",
  medium: "secondary",
  low: "outline",
}

export function OpenBugsCard({ projectId }) {
  const { t } = useTranslation("bugs")
  const { data: bugs = [], isLoading } = useBugs(projectId)

  const counts = SEVERITY_ORDER.reduce((acc, severity) => {
    acc[severity] = bugs.filter(
      bug => ACTIVE_STATUSES.has(bug.status) && bug.severity === severity,
    ).length
    return acc
  }, {})
  const total = SEVERITY_ORDER.reduce((sum, severity) => sum + counts[severity], 0)

  return (
    <Link
      to={`/projects/${projectId}/bugs`}
      className="block border rounded-lg p-4 bg-white dark:bg-gray-900 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
    >
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-200 flex items-center gap-2">
          <BugIcon size={14} /> {t("title")}
        </h3>
        <span className="text-xs text-gray-500 dark:text-gray-400">{total}</span>
      </div>
      {isLoading ? (
        <Skeleton className="h-6 w-full" />
      ) : (
        <div className="flex flex-wrap gap-1.5">
          {SEVERITY_ORDER.map(severity => (
            <Badge key={severity} variant={SEVERITY_VARIANT[severity]}>
              {t(`severity.${severity}`)} · {counts[severity]}
            </Badge>
          ))}
        </div>
      )}
    </Link>
  )
}
