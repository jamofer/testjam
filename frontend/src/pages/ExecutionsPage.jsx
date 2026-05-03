import { useParams, Link } from "react-router-dom"
import { PlayCircle, CheckCircle2, XCircle, MinusCircle, Plus, ArrowLeft, Clock } from "lucide-react"
import { useExecutions } from "../hooks/useExecutions"
import { Button } from "../components/ui/button"
import { Badge } from "../components/ui/badge"

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

export function ExecutionsPage() {
  const { id: projectId } = useParams()
  const { data: executions = [], isLoading } = useExecutions(projectId)

  if (isLoading) return <p className="text-gray-500">Loading…</p>

  return (
    <div className="max-w-3xl space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link to={`/projects/${projectId}`} className="text-gray-400 hover:text-gray-700">
            <ArrowLeft size={16} />
          </Link>
          <h1 className="text-2xl font-bold text-gray-800">Executions</h1>
        </div>
        <Link to={`/projects/${projectId}/executions/new`}>
          <Button size="sm"><Plus size={14} /> New execution</Button>
        </Link>
      </div>

      <ul className="space-y-2">
        {executions.map(ex => (
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
        {executions.length === 0 && <p className="text-sm text-gray-400">No executions yet.</p>}
      </ul>
    </div>
  )
}
