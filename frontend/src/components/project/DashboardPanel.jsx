import { useMemo } from "react"
import { Link } from "react-router-dom"
import { useTranslation } from "react-i18next"
import { CheckCircle2, XCircle, AlertTriangle, MinusCircle, PlayCircle, FolderOpen, FileText, TrendingUp } from "lucide-react"

const STATUS_DOT = {
  completed:   "bg-green-500",
  in_progress: "bg-blue-500",
  pending:     "bg-gray-400",
  aborted:     "bg-red-500",
}

function passRateOf(execution) {
  const ran = (execution.passed ?? 0) + (execution.failed ?? 0) + (execution.blocked ?? 0)
  if (ran === 0) return null
  return (execution.passed ?? 0) / ran
}

function Sparkline({ values, width = 140, height = 32 }) {
  if (values.length < 2) return null
  const min = 0
  const max = 1
  const step = width / (values.length - 1)
  const points = values.map((value, index) => {
    const x = index * step
    const y = height - ((value - min) / (max - min || 1)) * height
    return `${x.toFixed(1)},${y.toFixed(1)}`
  }).join(" ")
  const last = values[values.length - 1]
  const lastX = (values.length - 1) * step
  const lastY = height - ((last - min) / (max - min || 1)) * height
  return (
    <svg width={width} height={height} className="overflow-visible">
      <polyline fill="none" stroke="#e11d48" strokeWidth="1.6"
        strokeLinecap="round" strokeLinejoin="round" points={points} />
      <circle cx={lastX} cy={lastY} r="2.4" fill="#e11d48" />
    </svg>
  )
}

export function DashboardPanel({ project, compact = false }) {
  const { t } = useTranslation("projects")
  const recent = project?.recent_executions ?? []
  const chronological = useMemo(() => [...recent].reverse(), [recent])
  const passRates = useMemo(
    () => chronological.map(passRateOf).filter(value => value != null),
    [chronological],
  )
  const avgPass = passRates.length > 0
    ? passRates.reduce((sum, value) => sum + value, 0) / passRates.length
    : null

  const totals = {
    suites: project?.suite_count ?? 0,
    cases: project?.case_count ?? 0,
    executions: project?.execution_count ?? 0,
  }

  return (
    <div className={`grid gap-3 ${compact ? "grid-cols-3" : "grid-cols-1 sm:grid-cols-3"}`}>
      <div className="bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg p-3">
        <p className="text-[10px] font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500">{t("panel.library")}</p>
        <div className="mt-1.5 grid grid-cols-2 gap-y-1 text-xs">
          <span className="flex items-center gap-1.5 text-gray-600 dark:text-gray-300"><FolderOpen size={11} className="text-yellow-500" /> {t("panel.suites")}</span>
          <span className="text-right font-semibold">{totals.suites}</span>
          <span className="flex items-center gap-1.5 text-gray-600 dark:text-gray-300"><FileText size={11} className="text-gray-400 dark:text-gray-500" /> {t("panel.cases")}</span>
          <span className="text-right font-semibold">{totals.cases}</span>
          <span className="flex items-center gap-1.5 text-gray-600 dark:text-gray-300"><PlayCircle size={11} className="text-blue-500" /> {t("panel.executions")}</span>
          <span className="text-right font-semibold">{totals.executions}</span>
        </div>
      </div>

      <div className="bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg p-3">
        <div className="flex items-center justify-between">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500">{t("panel.passRate")}</p>
          <span className="text-[10px] text-gray-400 dark:text-gray-500">{t("panel.lastN", { count: passRates.length })}</span>
        </div>
        <div className="mt-0.5 flex items-end gap-2">
          <div className="text-xl font-bold text-gray-800 dark:text-gray-100">
            {avgPass != null ? `${Math.round(avgPass * 100)}%` : "—"}
          </div>
          {avgPass != null && (
            <span className="text-[10px] text-gray-400 dark:text-gray-500 mb-1 flex items-center gap-1">
              <TrendingUp size={10} /> {t("panel.avg")}
            </span>
          )}
        </div>
        <div>
          {passRates.length >= 2 ? (
            <Sparkline values={passRates} />
          ) : (
            <p className="text-[11px] text-gray-400 dark:text-gray-500 py-1">{t("panel.notEnough")}</p>
          )}
        </div>
      </div>

      <div className="bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg p-3">
        <p className="text-[10px] font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500 mb-1.5">{t("panel.recentRuns")}</p>
        {recent.length === 0 ? (
          <p className="text-[11px] text-gray-400 dark:text-gray-500 py-1">{t("panel.noExecutions")}</p>
        ) : (
          <ul className="space-y-1">
            {recent.slice(0, 3).map(execution => (
              <li key={execution.id}>
                <Link to={`/executions/${execution.id}/run`} className="flex items-center gap-1.5 text-xs group">
                  <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${STATUS_DOT[execution.status] ?? "bg-gray-400"}`} />
                  <span className="truncate flex-1 text-gray-700 dark:text-gray-200 group-hover:text-primary-600">{execution.title}</span>
                  <span className="flex items-center gap-1 text-[10px] text-gray-400 dark:text-gray-500 shrink-0">
                    <CheckCircle2 size={9} className="text-green-500" />{execution.passed ?? 0}
                    <XCircle size={9} className="text-red-500" />{execution.failed ?? 0}
                    <AlertTriangle size={9} className="text-yellow-500" />{execution.blocked ?? 0}
                    <MinusCircle size={9} className="text-gray-400 dark:text-gray-500" />{execution.not_run ?? 0}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
