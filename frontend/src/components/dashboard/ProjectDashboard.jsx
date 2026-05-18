import { Link } from "react-router-dom"
import { useTranslation } from "react-i18next"
import { FileText, FolderOpen, Layers, PlayCircle, Tag } from "lucide-react"

import { useDashboard } from "../../hooks/useDashboard"
import { fmtDuration } from "../../lib/format"
import { STATUS_CONFIG } from "../../lib/statusConfig"
import { DateLabel } from "../ui/date-label"
import { Skeleton } from "../ui/skeleton"
import { Sparkline } from "./Sparkline"
import { OpenBugsCard } from "./OpenBugsCard"

const RANGES = [7, 30, 90]

export function ProjectDashboard({ projectId, range, onRangeChange }) {
  const { t } = useTranslation("dashboard")
  const { data, isPending } = useDashboard(projectId, { range })

  return (
    <section className="space-y-4" aria-label={t("aria")}>
      <DashboardHeader range={range} onRangeChange={onRangeChange} />

      <div className="grid gap-4 md:grid-cols-2">
        <CountsCard counts={data?.counts} loading={isPending} />
        <PassRateCard passRate={data?.pass_rate} loading={isPending} />
        <RecentExecutionsCard recent={data?.recent_executions} loading={isPending} projectId={projectId} />
        <TopFailCard topFail={data?.top_fail} loading={isPending} projectId={projectId} />
        <OpenBugsCard projectId={projectId} />
        <VersionsCard versions={data?.versions} loading={isPending} projectId={projectId} />
      </div>
    </section>
  )
}

function DashboardHeader({ range, onRangeChange }) {
  const { t } = useTranslation("dashboard")
  return (
    <div className="flex items-center justify-between">
      <h2 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">
        {t("lastDays", { count: range })}
      </h2>
      <div role="radiogroup" aria-label={t("range")} className="flex items-center rounded-md border bg-white dark:bg-gray-900 text-xs overflow-hidden">
        {RANGES.map(option => (
          <button
            key={option}
            role="radio"
            aria-checked={option === range}
            onClick={() => onRangeChange(option)}
            className={
              "px-3 py-1.5 transition-colors " +
              (option === range
                ? "bg-primary-600 text-white"
                : "text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800")
            }
          >
            {t("rangeDays", { count: option })}
          </button>
        ))}
      </div>
    </div>
  )
}

function Card({ title, action, children }) {
  return (
    <div className="rounded-xl border bg-white dark:bg-gray-900 p-5 shadow-sm">
      <header className="flex items-center justify-between mb-3">
        <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">{title}</p>
        {action}
      </header>
      {children}
    </div>
  )
}

function CountsCard({ counts, loading }) {
  const { t } = useTranslation("dashboard")
  if (loading) return <Card title={t("project")}><Skeleton className="h-24 w-full" /></Card>
  if (!counts) return null
  return (
    <Card title={t("project")}>
      <div className="grid grid-cols-2 gap-4">
        <Stat icon={FolderOpen} label={t("suites")} value={counts.suites} />
        <Stat icon={FileText} label={t("cases")} value={counts.cases} />
        <Stat icon={Layers} label={t("plans")} value={counts.plans} />
        <Stat icon={PlayCircle} label={t("inFlight")} value={counts.executions_in_flight} />
      </div>
    </Card>
  )
}

function Stat({ icon: Icon, label, value }) {
  return (
    <div className="flex items-center gap-3">
      <div className="w-10 h-10 rounded-lg bg-gray-50 dark:bg-gray-900 text-gray-500 dark:text-gray-400 flex items-center justify-center">
        <Icon size={18} />
      </div>
      <div>
        <p className="text-xs text-gray-500 dark:text-gray-400">{label}</p>
        <p className="text-xl font-semibold text-gray-800 dark:text-gray-100 leading-tight">{value}</p>
      </div>
    </div>
  )
}

function PassRateCard({ passRate, loading }) {
  const { t } = useTranslation("dashboard")
  if (loading) return <Card title={t("passRate")}><Skeleton className="h-24 w-full" /></Card>
  if (!passRate) return null
  const overall = passRate.overall_pass_rate
  const points = passRate.series.map(point => point.passed + point.failed === 0
    ? 0
    : point.passed / (point.passed + point.failed))
  return (
    <Card title={t("passRate")}>
      <div className="flex items-end justify-between gap-4">
        <div>
          <p className="text-3xl font-bold text-gray-800 dark:text-gray-100 leading-none">
            {overall == null ? "—" : `${Math.round(overall * 100)}%`}
          </p>
          <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
            {t("results", { count: passRate.total_results })}
          </p>
        </div>
        <div className="grow max-w-[60%]">
          <Sparkline points={points} />
        </div>
      </div>
    </Card>
  )
}

function TopFailCard({ topFail, loading, projectId }) {
  const { t } = useTranslation("dashboard")
  if (loading) return <Card title={t("topFail")}><Skeleton className="h-24 w-full" /></Card>
  const rows = topFail?.cases ?? []
  return (
    <Card
      title={t("topFail")}
      action={
        <Link to={`/projects/${projectId}/cases`} className="text-xs text-primary-600 hover:underline">
          {t("viewAll")}
        </Link>
      }
    >
      {rows.length === 0 ? (
        <p className="text-sm text-gray-400 dark:text-gray-500 py-2">{t("noFailures")}</p>
      ) : (
        <ul className="space-y-2">
          {rows.map(row => (
            <li key={row.case_id} className="flex items-center justify-between gap-3">
              <Link
                to={`/cases/${row.case_id}`}
                className="truncate text-sm text-gray-800 dark:text-gray-100 hover:underline"
                title={row.case_name}
              >
                {row.case_name}
              </Link>
              <span className="shrink-0 text-xs font-medium text-red-600">
                {t("fail", { count: row.fail_count })}
              </span>
            </li>
          ))}
        </ul>
      )}
    </Card>
  )
}

function RecentExecutionsCard({ recent, loading, projectId }) {
  const { t } = useTranslation("dashboard")
  if (loading) return <Card title={t("recentExecutions")}><Skeleton className="h-24 w-full" /></Card>
  const items = recent?.executions ?? []
  return (
    <Card
      title={t("recentExecutions")}
      action={
        <Link to={`/projects/${projectId}/executions`} className="text-xs text-primary-600 hover:underline">
          {t("viewAll")}
        </Link>
      }
    >
      {items.length === 0 ? (
        <p className="text-sm text-gray-400 dark:text-gray-500 py-2">{t("noExecutions")}</p>
      ) : (
        <ul className="space-y-2">
          {items.map(item => <RecentExecutionRow key={item.id} item={item} />)}
        </ul>
      )}
    </Card>
  )
}

function VersionsCard({ versions, loading, projectId }) {
  const { t } = useTranslation("dashboard")
  if (loading) return <Card title={t("versions")}><Skeleton className="h-24 w-full" /></Card>
  const items = versions?.items ?? []
  return (
    <Card
      title={t("versions")}
      action={
        <Link to={`/projects/${projectId}/versions`} className="text-xs text-primary-600 hover:underline">
          {t("viewAll")}
        </Link>
      }
    >
      {items.length === 0 ? (
        <p className="text-sm text-gray-400 dark:text-gray-500 py-2">{t("noVersions")}</p>
      ) : (
        <ul className="space-y-2">
          {items.map(item => <VersionsCardRow key={item.id} item={item} projectId={projectId} />)}
        </ul>
      )}
    </Card>
  )
}

function VersionsCardRow({ item, projectId }) {
  const { t } = useTranslation("dashboard")
  const passPercent = item.pass_rate == null ? null : Math.round(item.pass_rate * 100)
  return (
    <li className="flex items-center gap-3 text-sm">
      <Tag size={13} className="text-gray-400 dark:text-gray-500 shrink-0" />
      <Link
        to={`/projects/${projectId}/versions/${item.id}`}
        className="truncate text-gray-800 dark:text-gray-100 hover:underline flex-1"
        title={item.name}
      >
        {item.name}
      </Link>
      <span className="text-xs text-gray-400 dark:text-gray-500 shrink-0">
        {t("runs", { count: item.total_runs })}
      </span>
      <span className={`text-xs font-medium shrink-0 ${passPercent == null ? "text-gray-400 dark:text-gray-500" : passPercent >= 80 ? "text-green-600" : passPercent >= 50 ? "text-yellow-600" : "text-red-500"}`}>
        {passPercent == null ? t("neverRun") : `${passPercent}%`}
      </span>
    </li>
  )
}

function RecentExecutionRow({ item }) {
  const { t } = useTranslation("common")
  const status = STATUS_CONFIG[item.status] ?? STATUS_CONFIG.not_run
  return (
    <li className="flex items-center gap-2">
      <span className={`shrink-0 text-[10px] font-medium px-1.5 py-0.5 rounded ${status.pill}`}>
        {t(`status.${item.status}`, status.label)}
      </span>
      <Link
        to={`/executions/${item.id}/run`}
        className="grow truncate text-sm text-gray-800 dark:text-gray-100 hover:underline"
        title={item.title}
      >
        {item.title}
      </Link>
      <span className="shrink-0 text-xs text-gray-400 dark:text-gray-500">
        {fmtDuration(item.duration_ms) ?? <DateLabel iso={item.created_at} />}
      </span>
    </li>
  )
}
