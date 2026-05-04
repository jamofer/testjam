import { useState } from "react"
import { useParams } from "react-router-dom"
import { ExternalLink, Clock } from "lucide-react"
import { useQueryClient } from "@tanstack/react-query"
import { useExecution, useExecutionResults } from "../hooks/useExecutions"
import { executionsApi } from "../api/executions"
import { useProject } from "../hooks/useProjects"
import { Breadcrumbs } from "../components/ui/breadcrumbs"
import { Button } from "../components/ui/button"
import { Skeleton, SkeletonList } from "../components/ui/skeleton"
import { ResultCard } from "../components/execution/ResultCard"
import { fmtDuration } from "../lib/format"
import { toast } from "sonner"

export function ExecutionRunPage() {
  const { id } = useParams()
  const { data: execution } = useExecution(id)
  const { data: results = [] } = useExecutionResults(id)
  const qc = useQueryClient()
  const [finishing, setFinishing] = useState(false)

  const finishExecution = async () => {
    setFinishing(true)
    try {
      await executionsApi.update(id, { status: "completed", finished_at: new Date().toISOString() })
      qc.invalidateQueries({ queryKey: ["executions", id] })
      toast.success("Execution completed")
    } catch {
      toast.error("Failed to finish execution")
      setFinishing(false)
    }
  }

  if (!execution) {
    return (
      <div className="max-w-2xl space-y-4">
        <Skeleton className="h-4 w-24" />
        <Skeleton className="h-7 w-1/2" />
        <Skeleton className="h-4 w-2/3" />
        <SkeletonList count={3} itemClassName="h-24" />
      </div>
    )
  }

  const summary = execution.summary ?? {}
  const done = (summary.passed ?? 0) + (summary.failed ?? 0) + (summary.blocked ?? 0)
  const totalMs = execution.started_at && execution.finished_at
    ? new Date(execution.finished_at) - new Date(execution.started_at)
    : null

  return <ExecutionRunBody {...{ execution, results, id, summary, done, totalMs, finishExecution, finishing }} />
}

function ExecutionRunBody({ execution, results, id, summary, done, totalMs, finishExecution, finishing }) {
  const { data: project } = useProject(execution.project_id)

  return (
    <div className="max-w-2xl space-y-4">
      <Breadcrumbs
        crumbs={[
          { label: "Projects", to: "/projects" },
          { label: project?.name ?? "…", to: `/projects/${execution.project_id}` },
          { label: "Executions", to: `/projects/${execution.project_id}/executions` },
          { label: execution.title },
        ]}
      />

      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-gray-800">{execution.title}</h1>
          <div className="flex flex-wrap items-center gap-x-3 gap-y-0.5 mt-1 text-sm text-gray-500">
            {execution.version && <span>v{execution.version}</span>}
            {execution.environment && <span>{execution.environment}</span>}
            {execution.triggered_by && <span>by {execution.triggered_by}</span>}
            <span>{done}/{summary.total ?? 0} done</span>
            {totalMs != null && (
              <span className="flex items-center gap-1 text-gray-400">
                <Clock size={12} /> {fmtDuration(totalMs)} total
              </span>
            )}
          </div>
        </div>
        <Button
          onClick={finishExecution}
          disabled={execution.status === "completed" || finishing}
          loading={finishing}
          className="shrink-0"
        >
          {execution.status === "completed" ? "Completed" : "Finish execution"}
        </Button>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex gap-3 text-sm">
          <span className="text-green-600 font-medium">✓ {summary.passed ?? 0} passed</span>
          <span className="text-red-500 font-medium">✗ {summary.failed ?? 0} failed</span>
          <span className="text-yellow-600 font-medium">⚠ {summary.blocked ?? 0} blocked</span>
          <span className="text-gray-400">— {summary.not_run ?? 0} not run</span>
        </div>
        {(execution.attachments ?? []).length > 0 && (
          <div className="flex gap-2 ml-auto">
            {execution.attachments.map(a => (
              <a key={a.id} href={a.url} target="_blank" rel="noopener noreferrer"
                className="flex items-center gap-1 text-xs text-gray-500 hover:text-primary-600 border rounded px-2 py-1 bg-white hover:bg-gray-50 transition-colors">
                <ExternalLink size={11} />{a.filename}
              </a>
            ))}
          </div>
        )}
      </div>

      <div className="space-y-3">
        {results.map((result, i) => (
          <ResultCard key={result.id} result={result} executionId={id} index={i} total={results.length}
            isAutomated={execution.type === "automatic"} />
        ))}
      </div>
    </div>
  )
}
