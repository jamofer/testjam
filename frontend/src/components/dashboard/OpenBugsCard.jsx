import { Link } from "react-router-dom"
import { useTranslation } from "react-i18next"
import { Bug as BugIcon } from "lucide-react"

import { useBugs } from "../../hooks/useBugs"
import { SEVERITY_VARIANT, STATUS_VARIANT } from "../../lib/bugConfig"
import { Badge } from "../ui/badge"
import { Skeleton } from "../ui/skeleton"

const ACTIVE_STATUSES = new Set(["open", "in_progress"])
const SEVERITY_ORDER = ["critical", "high", "medium", "low"]
const RECENT_BUG_LIMIT = 5


export function OpenBugsCard({ projectId }) {
  const { t } = useTranslation(["dashboard", "bugs"])
  const { data: bugs = [], isLoading } = useBugs(projectId)

  const activeBugs = bugs.filter(bug => ACTIVE_STATUSES.has(bug.status))
  const counts = SEVERITY_ORDER.reduce((acc, severity) => {
    acc[severity] = activeBugs.filter(bug => bug.severity === severity).length
    return acc
  }, {})
  const recent = [...activeBugs]
    .sort((a, b) => b.number - a.number)
    .slice(0, RECENT_BUG_LIMIT)

  return (
    <div className="rounded-xl border bg-white dark:bg-gray-900 p-5 shadow-sm">
      <header className="flex items-center justify-between mb-3">
        <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide flex items-center gap-2">
          <BugIcon size={13} /> {t("dashboard:openBugs")}
          <span className="text-gray-400 dark:text-gray-500 normal-case font-normal">({activeBugs.length})</span>
        </p>
        <Link to={`/projects/${projectId}/bugs`} className="text-xs text-primary-600 hover:underline">
          {t("dashboard:viewAll")}
        </Link>
      </header>

      {isLoading ? (
        <Skeleton className="h-24 w-full" />
      ) : activeBugs.length === 0 ? (
        <p className="text-sm text-gray-400 dark:text-gray-500 py-2">{t("dashboard:noOpenBugs")}</p>
      ) : (
        <>
          <div className="flex flex-wrap gap-1.5 mb-3">
            {SEVERITY_ORDER.filter(severity => counts[severity] > 0).map(severity => (
              <Badge key={severity} variant={SEVERITY_VARIANT[severity]}>
                {t(`bugs:severity.${severity}`)} · {counts[severity]}
              </Badge>
            ))}
          </div>
          <ul className="space-y-1.5">
            {recent.map(bug => (
              <li key={bug.id}>
                <Link
                  to={`/projects/${projectId}/bugs/${bug.number}`}
                  className="flex items-center gap-2 text-sm group"
                  title={bug.title}
                >
                  <span className="font-mono text-[11px] text-gray-400 dark:text-gray-500 shrink-0">#{bug.number}</span>
                  <span className="grow truncate text-gray-800 dark:text-gray-100 group-hover:text-primary-600">{bug.title}</span>
                  <Badge variant={SEVERITY_VARIANT[bug.severity]} className="shrink-0 text-[10px] px-1.5 py-0">
                    {t(`bugs:severity.${bug.severity}`)}
                  </Badge>
                  <Badge variant={STATUS_VARIANT[bug.status]} className="shrink-0 text-[10px] px-1.5 py-0">
                    {t(`bugs:statuses.${bug.status}`)}
                  </Badge>
                </Link>
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  )
}
