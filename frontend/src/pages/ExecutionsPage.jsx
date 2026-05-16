import { useState, useMemo } from "react"
import { useParams, Link } from "react-router-dom"
import { PlayCircle, CheckCircle2, XCircle, MinusCircle, Plus, Clock, Search, User, Download, Trash2 } from "lucide-react"
import { toast } from "sonner"
import { useExecutions, useDeleteExecution } from "../hooks/useExecutions"
import { useProject } from "../hooks/useProjects"
import { useMe } from "../hooks/useAuth"
import { useDebounced } from "../hooks/useDebounced"
import { useProjectExecutionsLive } from "../hooks/useProjectExecutionsLive"
import { executionsApi } from "../api/executions"
import { Button } from "../components/ui/button"
import { Badge } from "../components/ui/badge"
import { SearchInput } from "../components/ui/search-input"
import { PageHeader, PageBody } from "../components/ui/page-header"
import { DateLabel } from "../components/ui/date-label"
import { fmtDuration } from "../lib/format"
import { EmptyState } from "../components/ui/empty-state"
import { LiveIndicator } from "../components/ui/live-indicator"
import { SkeletonList } from "../components/ui/skeleton"
import { ImportExecutionDialog } from "../components/execution/ImportExecutionDialog"

const statusIcon = {
  completed:  <CheckCircle2 size={15} className="text-green-500" />,
  in_progress: <PlayCircle size={15} className="text-blue-500" />,
  aborted:    <XCircle size={15} className="text-red-500" />,
  pending:    <MinusCircle size={15} className="text-gray-400" />,
}

const typeBadge = {
  manual:    "secondary",
  automatic: "default",
}

const STATUS_FILTERS = ["all", "pending", "in_progress", "completed", "aborted"]

export function ExecutionsPage() {
  const { id: projectId } = useParams()
  const [statusFilter, setStatusFilter] = useState("all")
  const {
    data,
    isLoading,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useExecutions(projectId, statusFilter !== "all" ? { status: statusFilter } : undefined)
  const { data: project } = useProject(projectId)
  const { data: me } = useMe()
  const { connected: live } = useProjectExecutionsLive(projectId, { enabled: !!me })
  const deleteExecution = useDeleteExecution(projectId)
  const [search, setSearch] = useState("")
  const [mineOnly, setMineOnly] = useState(false)
  const debouncedSearch = useDebounced(search, 150)

  const handleDelete = async (ex) => {
    if (!confirm(`Delete execution "${ex.title}"? This cannot be undone.`)) return
    try {
      await deleteExecution.mutateAsync(ex.id)
      toast.success("Execution deleted")
    } catch {
      toast.error("Failed to delete execution")
    }
  }

  const executions = useMemo(() => (data?.pages ?? []).flat(), [data])
  const hasFiltersActive = statusFilter !== "all" || debouncedSearch.trim() !== "" || mineOnly

  const filtered = useMemo(() => {
    const q = debouncedSearch.trim().toLowerCase()
    return executions.filter(ex => {
      if (mineOnly && ex.assigned_to?.id !== me?.id) return false
      if (q && !ex.title.toLowerCase().includes(q)) return false
      return true
    })
  }, [executions, debouncedSearch, mineOnly, me?.id])

  return (
    <>
      <PageHeader crumbs={[
        { label: "Projects", to: "/projects" },
        { label: project?.name ?? "…", to: `/projects/${projectId}` },
        { label: "Executions" },
      ]}>
        <div className="max-w-2xl xl:max-w-4xl 2xl:max-w-5xl space-y-3">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
              Executions
              <LiveIndicator connected={live} />
            </h1>
            <div className="flex items-center gap-2 self-start sm:self-auto">
              <ImportExecutionDialog projectId={projectId} />
              <Link to={`/projects/${projectId}/executions/new`}>
                <Button size="sm"><Plus size={14} /> New execution</Button>
              </Link>
            </div>
          </div>
          {!isLoading && (executions.length > 0 || hasFiltersActive) && (
            <div className="flex flex-wrap gap-2 items-center">
              <SearchInput value={search} onChange={setSearch} placeholder="Search by title…" className="flex-1 min-w-[180px]" />
              <div className="flex gap-1">
                {STATUS_FILTERS.map(s => (
                  <Button
                    key={s}
                    size="sm"
                    variant={statusFilter === s ? "default" : "outline"}
                    onClick={() => setStatusFilter(s)}
                  >
                    {s === "all" ? "All" : s.replace("_", " ")}
                  </Button>
                ))}
              </div>
              {me && (
                <Button
                  size="sm"
                  variant={mineOnly ? "default" : "outline"}
                  onClick={() => setMineOnly(v => !v)}
                  title="Show only executions assigned to me"
                >
                  <User size={13} /> Mine
                </Button>
              )}
            </div>
          )}
        </div>
      </PageHeader>

      <PageBody>
      <div className="max-w-2xl xl:max-w-4xl 2xl:max-w-5xl space-y-6">
      {isLoading && <SkeletonList count={3} />}

      <ul className="space-y-2">
        {filtered.map(ex => (
          <li key={ex.id} className="bg-white border rounded-lg px-4 py-3 shadow-sm">
            <div className="flex items-center justify-between gap-2">
              <Link to={`/executions/${ex.id}/run`}
                className="font-medium text-gray-800 hover:underline flex items-center gap-2 min-w-0">
                {statusIcon[ex.status]}
                <span className="truncate">{ex.title}</span>
              </Link>
              <div className="flex items-center gap-2 shrink-0">
                <Badge variant={typeBadge[ex.type]}>{ex.type}</Badge>
                <button
                  onClick={() => executionsApi.exportHtml(ex.id, ex.title)}
                  className="text-gray-400 hover:text-gray-700 p-1 rounded hover:bg-gray-100"
                  title="Download HTML report"
                >
                  <Download size={13} />
                </button>
                <button
                  onClick={() => handleDelete(ex)}
                  className="text-gray-400 hover:text-red-600 p-1 rounded hover:bg-red-50"
                  title="Delete execution"
                  disabled={deleteExecution.isPending}
                >
                  <Trash2 size={13} />
                </button>
              </div>
            </div>
            <div className="flex flex-wrap gap-x-3 gap-y-0.5 mt-1 text-xs text-gray-400">
              {ex.version && <span>v{ex.version}</span>}
              {ex.environment && <span>{ex.environment}</span>}
              {(ex.token_name || ex.created_by || ex.triggered_by) && (
                <span>{ex.token_name
                  ? `via ${ex.token_name}`
                  : `by ${ex.created_by?.username ?? ex.triggered_by}`}
                </span>
              )}
              {ex.assigned_to && (
                <span className="flex items-center gap-1 text-gray-500">
                  <User size={10} /> {ex.assigned_to.username}
                </span>
              )}
              {(ex.started_at || ex.created_at) && (
                <span className="flex items-center gap-1">
                  <Clock size={10} /> <DateLabel iso={ex.started_at ?? ex.created_at} />
                </span>
              )}
              {ex.finished_at && (ex.started_at || ex.created_at) && (
                <span>· {fmtDuration(new Date(ex.finished_at) - new Date(ex.started_at ?? ex.created_at))}</span>
              )}
            </div>
            <div className="flex gap-3 mt-1.5 text-xs">
              <span className="text-green-600">✓ {ex.summary?.passed ?? 0}</span>
              <span className="text-red-500">✗ {ex.summary?.failed ?? 0}</span>
              <span className="text-yellow-600">⚠ {ex.summary?.blocked ?? 0}</span>
              <span className="text-gray-400">— {ex.summary?.not_run ?? 0}</span>
            </div>
          </li>
        ))}
      </ul>
      {!isLoading && executions.length === 0 && !hasFiltersActive && (
        <EmptyState
          icon={PlayCircle}
          title="No executions yet"
          description="Run a test plan or import results from JUnit / Robot Framework to track your test runs over time."
          action={
            <Link to={`/projects/${projectId}/executions/new`}>
              <Button size="sm"><Plus size={14} /> New execution</Button>
            </Link>
          }
        />
      )}
      {!isLoading && filtered.length === 0 && hasFiltersActive && (
        <EmptyState
          icon={Search}
          title="No matches"
          description="No executions match the current filters."
          compact
        />
      )}
      {hasNextPage && (
        <div className="flex justify-center">
          <Button variant="outline" size="sm" onClick={() => fetchNextPage()} disabled={isFetchingNextPage}>
            {isFetchingNextPage ? "Loading…" : "Load more"}
          </Button>
        </div>
      )}
      </div>
      </PageBody>
    </>
  )
}
