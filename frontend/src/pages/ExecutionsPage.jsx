import { useState, useMemo } from "react"
import { useParams, Link } from "react-router-dom"
import { PlayCircle, CheckCircle2, XCircle, MinusCircle, Plus, Clock, Search } from "lucide-react"
import { useExecutions } from "../hooks/useExecutions"
import { useProject } from "../hooks/useProjects"
import { useDebounced } from "../hooks/useDebounced"
import { Button } from "../components/ui/button"
import { Badge } from "../components/ui/badge"
import { Breadcrumbs } from "../components/ui/breadcrumbs"
import { SearchInput } from "../components/ui/search-input"
import { EmptyState } from "../components/ui/empty-state"
import { SkeletonList } from "../components/ui/skeleton"

function fmtDate(iso) {
  if (!iso) return null
  const d = new Date(iso)
  return d.toLocaleString(undefined, { dateStyle: "short", timeStyle: "short" })
}

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
  const { data: executions = [], isLoading } = useExecutions(projectId)
  const { data: project } = useProject(projectId)
  const [search, setSearch] = useState("")
  const [statusFilter, setStatusFilter] = useState("all")
  const debouncedSearch = useDebounced(search, 150)

  const filtered = useMemo(() => {
    const q = debouncedSearch.trim().toLowerCase()
    return executions.filter(ex => {
      if (statusFilter !== "all" && ex.status !== statusFilter) return false
      if (q && !ex.title.toLowerCase().includes(q)) return false
      return true
    })
  }, [executions, debouncedSearch, statusFilter])

  return (
    <div className="max-w-3xl space-y-6">
      <Breadcrumbs
        crumbs={[
          { label: "Projects", to: "/projects" },
          { label: project?.name ?? "…", to: `/projects/${projectId}` },
          { label: "Executions" },
        ]}
      />
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800">Executions</h1>
        <Link to={`/projects/${projectId}/executions/new`}>
          <Button size="sm"><Plus size={14} /> New execution</Button>
        </Link>
      </div>

      {!isLoading && executions.length > 0 && (
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
        </div>
      )}

      {isLoading && <SkeletonList count={3} />}

      <ul className="space-y-2">
        {filtered.map(ex => (
          <li key={ex.id} className="bg-white border rounded-lg px-4 py-3 shadow-sm">
            <div className="flex items-center justify-between">
              <Link to={`/executions/${ex.id}/run`}
                className="font-medium text-gray-800 hover:underline flex items-center gap-2">
                {statusIcon[ex.status]}
                {ex.title}
              </Link>
              <Badge variant={typeBadge[ex.type]}>{ex.type}</Badge>
            </div>
            <div className="flex flex-wrap gap-x-3 gap-y-0.5 mt-1 text-xs text-gray-400">
              {ex.version && <span>v{ex.version}</span>}
              {ex.environment && <span>{ex.environment}</span>}
              {ex.triggered_by && <span>by {ex.triggered_by}</span>}
              {(ex.started_at || ex.created_at) && (
                <span className="flex items-center gap-1">
                  <Clock size={10} /> {fmtDate(ex.started_at ?? ex.created_at)}
                </span>
              )}
              {ex.finished_at && <span>→ {fmtDate(ex.finished_at)}</span>}
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
      {!isLoading && executions.length === 0 && (
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
      {!isLoading && executions.length > 0 && filtered.length === 0 && (
        <EmptyState
          icon={Search}
          title="No matches"
          description="No executions match the current filters."
          compact
        />
      )}
    </div>
  )
}
