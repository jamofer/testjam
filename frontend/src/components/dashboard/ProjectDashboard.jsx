import { Link } from "react-router-dom"
import { FileText, FolderOpen, Layers, PlayCircle } from "lucide-react"

import { useDashboard } from "../../hooks/useDashboard"
import { fmtDuration } from "../../lib/format"
import { STATUS_CONFIG } from "../../lib/statusConfig"
import { DateLabel } from "../ui/date-label"
import { Skeleton } from "../ui/skeleton"
import { Sparkline } from "./Sparkline"

const RANGES = [7, 30, 90]

export function ProjectDashboard({ projectId, range, onRangeChange }) {
  const { data, isPending } = useDashboard(projectId, { range })

  return (
    <section className="space-y-4" aria-label="Project dashboard">
      <DashboardHeader range={range} onRangeChange={onRangeChange} />

      <div className="grid gap-4 md:grid-cols-2">
        <CountsCard counts={data?.counts} loading={isPending} />
        <PassRateCard passRate={data?.pass_rate} loading={isPending} />
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <RecentExecutionsCard recent={data?.recent_executions} loading={isPending} projectId={projectId} />
        <TopFailCard topFail={data?.top_fail} loading={isPending} projectId={projectId} />
      </div>
    </section>
  )
}

function DashboardHeader({ range, onRangeChange }) {
  return (
    <div className="flex items-center justify-between">
      <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
        Last {range} days
      </h2>
      <div role="radiogroup" aria-label="Range" className="flex items-center rounded-md border bg-white text-xs overflow-hidden">
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
                : "text-gray-600 hover:bg-gray-50")
            }
          >
            {option}d
          </button>
        ))}
      </div>
    </div>
  )
}

function Card({ title, action, children }) {
  return (
    <div className="rounded-xl border bg-white p-5 shadow-sm">
      <header className="flex items-center justify-between mb-3">
        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">{title}</p>
        {action}
      </header>
      {children}
    </div>
  )
}

function CountsCard({ counts, loading }) {
  if (loading) return <Card title="Project"><Skeleton className="h-24 w-full" /></Card>
  if (!counts) return null
  return (
    <Card title="Project">
      <div className="grid grid-cols-2 gap-4">
        <Stat icon={FolderOpen} label="Suites" value={counts.suites} />
        <Stat icon={FileText} label="Cases" value={counts.cases} />
        <Stat icon={Layers} label="Plans" value={counts.plans} />
        <Stat icon={PlayCircle} label="In flight" value={counts.executions_in_flight} />
      </div>
    </Card>
  )
}

function Stat({ icon: Icon, label, value }) {
  return (
    <div className="flex items-center gap-3">
      <div className="w-10 h-10 rounded-lg bg-gray-50 text-gray-500 flex items-center justify-center">
        <Icon size={18} />
      </div>
      <div>
        <p className="text-xs text-gray-500">{label}</p>
        <p className="text-xl font-semibold text-gray-800 leading-tight">{value}</p>
      </div>
    </div>
  )
}

function PassRateCard({ passRate, loading }) {
  if (loading) return <Card title="Pass rate"><Skeleton className="h-24 w-full" /></Card>
  if (!passRate) return null
  const overall = passRate.overall_pass_rate
  const points = passRate.series.map(point => point.passed + point.failed === 0
    ? 0
    : point.passed / (point.passed + point.failed))
  return (
    <Card title="Pass rate">
      <div className="flex items-end justify-between gap-4">
        <div>
          <p className="text-3xl font-bold text-gray-800 leading-none">
            {overall == null ? "—" : `${Math.round(overall * 100)}%`}
          </p>
          <p className="text-xs text-gray-400 mt-1">
            {passRate.total_results} result{passRate.total_results === 1 ? "" : "s"}
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
  if (loading) return <Card title="Top fail-prone cases"><Skeleton className="h-24 w-full" /></Card>
  const rows = topFail?.cases ?? []
  return (
    <Card
      title="Top fail-prone cases"
      action={
        <Link to={`/projects/${projectId}/cases`} className="text-xs text-primary-600 hover:underline">
          View all
        </Link>
      }
    >
      {rows.length === 0 ? (
        <p className="text-sm text-gray-400 py-2">No failures in this window.</p>
      ) : (
        <ul className="space-y-2">
          {rows.map(row => (
            <li key={row.case_id} className="flex items-center justify-between gap-3">
              <Link
                to={`/cases/${row.case_id}`}
                className="truncate text-sm text-gray-800 hover:underline"
                title={row.case_name}
              >
                {row.case_name}
              </Link>
              <span className="shrink-0 text-xs font-medium text-red-600">
                {row.fail_count} fail{row.fail_count === 1 ? "" : "s"}
              </span>
            </li>
          ))}
        </ul>
      )}
    </Card>
  )
}

function RecentExecutionsCard({ recent, loading, projectId }) {
  if (loading) return <Card title="Recent executions"><Skeleton className="h-24 w-full" /></Card>
  const items = recent?.executions ?? []
  return (
    <Card
      title="Recent executions"
      action={
        <Link to={`/projects/${projectId}/executions`} className="text-xs text-primary-600 hover:underline">
          View all
        </Link>
      }
    >
      {items.length === 0 ? (
        <p className="text-sm text-gray-400 py-2">No executions in this window.</p>
      ) : (
        <ul className="space-y-2">
          {items.map(item => <RecentExecutionRow key={item.id} item={item} />)}
        </ul>
      )}
    </Card>
  )
}

function RecentExecutionRow({ item }) {
  const status = STATUS_CONFIG[item.status] ?? STATUS_CONFIG.not_run
  return (
    <li className="flex items-center gap-2">
      <span className={`shrink-0 text-[10px] font-medium px-1.5 py-0.5 rounded ${status.pill}`}>
        {status.label}
      </span>
      <Link
        to={`/executions/${item.id}/run`}
        className="grow truncate text-sm text-gray-800 hover:underline"
        title={item.title}
      >
        {item.title}
      </Link>
      <span className="shrink-0 text-xs text-gray-400">
        {fmtDuration(item.duration_ms) ?? <DateLabel iso={item.created_at} />}
      </span>
    </li>
  )
}
