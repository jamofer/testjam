import { useState } from "react"
import { useParams } from "react-router-dom"
import { ExternalLink, Clock, Keyboard, User, Download } from "lucide-react"
import { exportExecutionPdf } from "../lib/exportPdf"
import { useQueryClient } from "@tanstack/react-query"
import { useExecution, useExecutionResults, useUpdateResult } from "../hooks/useExecutions"
import { executionsApi } from "../api/executions"
import { useProject } from "../hooks/useProjects"
import { useKeyboardShortcuts } from "../hooks/useKeyboardShortcuts"
import { Breadcrumbs } from "../components/ui/breadcrumbs"
import { Button } from "../components/ui/button"
import { Skeleton, SkeletonList } from "../components/ui/skeleton"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "../components/ui/dialog"
import { ResultCard } from "../components/execution/ResultCard"
import { fmtDuration } from "../lib/format"
import { STATUS_CONFIG } from "../lib/statusConfig"
import { toast } from "sonner"

const SHORTCUT_TO_STATUS = { p: "passed", f: "failed", b: "blocked", n: "not_run" }

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
  const updateResult = useUpdateResult(id)
  const [focusedIndex, setFocusedIndex] = useState(0)
  const [helpOpen, setHelpOpen] = useState(false)
  const isAutomated = execution.type === "automatic"

  const focused = results[focusedIndex]

  useKeyboardShortcuts({
    j: () => setFocusedIndex(i => Math.min(i + 1, results.length - 1)),
    ArrowDown: () => setFocusedIndex(i => Math.min(i + 1, results.length - 1)),
    k: () => setFocusedIndex(i => Math.max(i - 1, 0)),
    ArrowUp: () => setFocusedIndex(i => Math.max(i - 1, 0)),
    "?": () => setHelpOpen(o => !o),
    Escape: () => setHelpOpen(false),
    ...(isAutomated ? {} : Object.fromEntries(
      Object.entries(SHORTCUT_TO_STATUS).map(([key, status]) => [
        key,
        async () => {
          if (!focused) return
          try {
            await updateResult.mutateAsync({ id: focused.id, data: { status } })
          } catch {
            toast.error("Failed to update status")
          }
        },
      ])
    )),
  }, { enabled: results.length > 0, allowWhileTyping: ["Escape"] })

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
            {(execution.token_name || execution.created_by || execution.triggered_by) && (
              <span>{execution.token_name
                ? `via ${execution.token_name}`
                : `by ${execution.created_by?.username ?? execution.triggered_by}`}
              </span>
            )}
            {execution.assigned_to && (
              <span className="flex items-center gap-1">
                <User size={12} /> {execution.assigned_to.username}
              </span>
            )}
            <span>{done}/{summary.total ?? 0} done</span>
            {totalMs != null && (
              <span className="flex items-center gap-1 text-gray-400">
                <Clock size={12} /> {fmtDuration(totalMs)} total
              </span>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <Button variant="ghost" size="sm" onClick={() => setHelpOpen(true)} title="Keyboard shortcuts (?)">
            <Keyboard size={14} />
          </Button>
          <Button variant="outline" size="sm" onClick={() => exportExecutionPdf(execution, results, project?.name)}>
            <Download size={13} /> PDF
          </Button>
          <Button variant="outline" size="sm" onClick={() => executionsApi.exportHtml(id, execution.title)}>
            <Download size={13} /> HTML
          </Button>
          <Button
            onClick={finishExecution}
            disabled={execution.status === "completed" || finishing}
            loading={finishing}
          >
            {execution.status === "completed" ? "Completed" : "Finish execution"}
          </Button>
        </div>
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
            isAutomated={isAutomated}
            focused={i === focusedIndex}
            onFocus={() => setFocusedIndex(i)} />
        ))}
      </div>

      <ShortcutHelpDialog open={helpOpen} onOpenChange={setHelpOpen} isAutomated={isAutomated} />
    </div>
  )
}

function ShortcutHelpDialog({ open, onOpenChange, isAutomated }) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Keyboard shortcuts</DialogTitle>
          <DialogDescription>Navigate and update results without the mouse.</DialogDescription>
        </DialogHeader>
        <div className="space-y-2 text-sm">
          <ShortcutRow keys={["j", "↓"]} description="Focus next result" />
          <ShortcutRow keys={["k", "↑"]} description="Focus previous result" />
          {!isAutomated && Object.entries(SHORTCUT_TO_STATUS).map(([key, status]) => (
            <ShortcutRow key={key} keys={[key]} description={`Mark as ${STATUS_CONFIG[status].label}`} />
          ))}
          <ShortcutRow keys={["?"]} description="Toggle this help" />
          <ShortcutRow keys={["Esc"]} description="Close this help" />
        </div>
      </DialogContent>
    </Dialog>
  )
}

function ShortcutRow({ keys, description }) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex gap-1">
        {keys.map(k => (
          <kbd key={k} className="px-2 py-0.5 text-xs font-mono bg-gray-100 border border-gray-300 rounded">{k}</kbd>
        ))}
      </div>
      <span className="text-gray-600">{description}</span>
    </div>
  )
}
