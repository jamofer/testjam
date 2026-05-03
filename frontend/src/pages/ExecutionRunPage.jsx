import { useState } from "react"
import { useParams, useNavigate, Link } from "react-router-dom"
import { CheckCircle2, XCircle, MinusCircle, AlertTriangle, Upload, ChevronDown, ChevronRight, Trash2, Copy, ExternalLink, ArrowLeft, Clock } from "lucide-react"
import { useExecution, useExecutionResults, useUpdateResult } from "../hooks/useExecutions"
import { executionsApi } from "../api/executions"
import { useCase } from "../hooks/useSuites"
import { useQueryClient } from "@tanstack/react-query"
import { MdEditor, MdViewer } from "../components/MdEditor"
import { Button } from "../components/ui/button"
import { Badge } from "../components/ui/badge"
import { toast } from "sonner"

const STATUS_CONFIG = {
  passed:  { label: "Pass",    icon: CheckCircle2,  color: "success",     bg: "bg-green-50  border-green-200" },
  failed:  { label: "Fail",    icon: XCircle,        color: "destructive", bg: "bg-red-50    border-red-200"   },
  blocked: { label: "Blocked", icon: AlertTriangle,  color: "warning",     bg: "bg-yellow-50 border-yellow-200"},
  not_run: { label: "Not run", icon: MinusCircle,    color: "secondary",   bg: "bg-gray-50   border-gray-200"  },
}

const STEP_TYPE_LABEL = { setup: "Setup", action: null, teardown: "Teardown" }
const STEP_TYPE_HEADER_COLOR = { setup: "text-blue-600 bg-blue-50", teardown: "text-orange-600 bg-orange-50" }

const STATUS_ICON_COLOR = {
  passed: "text-green-600", failed: "text-red-500", blocked: "text-yellow-600", not_run: "text-gray-400",
}

function fmtDuration(ms) {
  if (ms == null) return null
  if (ms < 1000) return `${ms}ms`
  if (ms < 60000) return `${(ms / 1000).toFixed(2)}s`
  const m = Math.floor(ms / 60000)
  const s = ((ms % 60000) / 1000).toFixed(0)
  return `${m}m ${s}s`
}

function fmtTime(iso) {
  if (!iso) return null
  return new Date(iso).toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit", second: "2-digit" })
}

function StepResultRow({ step, stepResult, onUpdate, isAutomated }) {
  const config = STATUS_CONFIG[stepResult?.status ?? "not_run"]
  const [showLog, setShowLog] = useState(false)
  const statusKey = stepResult?.status ?? "not_run"

  return (
    <div className={`border rounded-lg overflow-hidden ${config.bg}`}>
      <div className="flex items-start gap-3 p-3">
        <span className="text-xs font-mono text-gray-400 mt-0.5 w-5">{step.order}.</span>
        <div className="flex-1 min-w-0">
          <div className="prose prose-sm"><MdViewer value={step.action} /></div>
          {step.expected_result && (
            <p className="text-xs text-gray-500 mt-1 italic">Expected: <MdViewer value={step.expected_result} /></p>
          )}
          {stepResult?.log_output && (
            <button onClick={() => setShowLog(l => !l)}
              className="text-xs text-gray-400 hover:text-gray-700 mt-1 underline">
              {showLog ? "Hide log" : "Show log"}
            </button>
          )}
          {stepResult?.duration_ms != null && (
            <span className="text-xs text-gray-400 flex items-center gap-1 mt-0.5">
              <Clock size={9} /> {fmtDuration(stepResult.duration_ms)}
            </span>
          )}
        </div>
        {!isAutomated && (
          <div className="flex gap-1 shrink-0">
            {Object.entries(STATUS_CONFIG).map(([status, cfg]) => {
              const Ic = cfg.icon
              return (
                <button key={status}
                  onClick={() => onUpdate(step.id, status)}
                  title={cfg.label}
                  className={`p-1 rounded transition-opacity ${stepResult?.status === status ? "opacity-100" : "opacity-25 hover:opacity-70"}`}>
                  <Ic size={16} className={STATUS_ICON_COLOR[status]} />
                </button>
              )
            })}
          </div>
        )}
        {isAutomated && (
          <div className="shrink-0">
            {(() => {
              const Ic = STATUS_CONFIG[statusKey].icon
              return <Ic size={16} className={STATUS_ICON_COLOR[statusKey]} />
            })()}
          </div>
        )}
      </div>
      {showLog && stepResult?.log_output && (
        <div className="px-4 pb-3 border-t border-gray-100 bg-gray-900 text-gray-100 text-xs font-mono whitespace-pre-wrap rounded-b-lg max-h-48 overflow-y-auto">
          {stepResult.log_output}
        </div>
      )}
    </div>
  )
}

function StepsSection({ steps, stepResults, onUpdate, isAutomated }) {
  const byType = { setup: [], action: [], teardown: [] }
  steps.forEach(s => { (byType[s.step_type] ?? byType.action).push(s) })

  return (
    <div className="space-y-3">
      {["setup", "action", "teardown"].map(type => {
        if (!byType[type].length) return null
        const label = STEP_TYPE_LABEL[type]
        const headerColor = STEP_TYPE_HEADER_COLOR[type]
        return (
          <div key={type}>
            {label && (
              <p className={`text-xs font-semibold uppercase tracking-wide px-2 py-1 rounded mb-1 w-fit ${headerColor}`}>
                {label}
              </p>
            )}
            <div className="space-y-2">
              {byType[type].map(step => {
                const sr = stepResults.find(r => r.step_id === step.id)
                return (
                  <StepResultRow key={step.id} step={step} stepResult={sr}
                    onUpdate={onUpdate} isAutomated={isAutomated} />
                )
              })}
            </div>
          </div>
        )
      })}
    </div>
  )
}

function ResultCard({ result, index, total, isAutomated }) {
  const { data: tc } = useCase(result.test_case_id)
  const [open, setOpen] = useState(index === 0)
  const [comment, setComment] = useState(result.comment ?? "")
  const qc = useQueryClient()
  const updateResult = useUpdateResult(result.execution_id)

  const overallStatus = result.status
  const config = STATUS_CONFIG[overallStatus]
  const Icon = config.icon

  const setStatus = async (status) => {
    try {
      await updateResult.mutateAsync({ id: result.id, data: { status, comment } })
      toast.success(`Marked as ${status}`)
    } catch {
      toast.error("Failed to update status")
    }
  }

  const updateStepResult = async (stepId, status) => {
    try {
      const existingSr = (result.step_results ?? []).find(sr => sr.step_id === stepId)
      if (existingSr) {
        await executionsApi.updateStepResult(result.id, existingSr.id, { status })
      } else {
        await executionsApi.createResult(result.execution_id, {
          test_case_id: result.test_case_id,
          status: result.status,
          step_results: [{ step_id: stepId, status }],
        })
      }
      qc.invalidateQueries({ queryKey: ["results", result.execution_id] })
    } catch {
      toast.error("Failed to update step")
    }
  }

  const saveComment = async () => {
    try {
      await updateResult.mutateAsync({ id: result.id, data: { comment } })
      toast.success("Comment saved")
    } catch {
      toast.error("Failed to save comment")
    }
  }

  const uploadAttachment = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    try {
      await executionsApi.uploadResultAttachment(result.id, file)
      qc.invalidateQueries({ queryKey: ["results", result.execution_id] })
      toast.success(`${file.name} attached`)
    } catch {
      toast.error("Upload failed")
    }
    e.target.value = ""
  }

  const deleteAttachment = async (attachmentId) => {
    try {
      await executionsApi.deleteResultAttachment(result.id, attachmentId)
      qc.invalidateQueries({ queryKey: ["results", result.execution_id] })
      toast.success("Attachment deleted")
    } catch {
      toast.error("Failed to delete attachment")
    }
  }

  const copyUrl = (att) => {
    navigator.clipboard.writeText(`${window.location.origin}${att.url}`)
    toast.success("URL copied")
  }

  const copyMarkdown = (att) => {
    const url = `${window.location.origin}${att.url}`
    const md = att.content_type?.startsWith("image/")
      ? `![${att.filename}](${url})`
      : `[${att.filename}](${url})`
    navigator.clipboard.writeText(md)
    toast.success("Markdown copied")
  }

  return (
    <div className="border rounded-xl overflow-hidden shadow-sm">
      <div className={`flex items-center justify-between px-4 py-3 cursor-pointer ${config.bg} border-b`}
        onClick={() => setOpen(o => !o)}>
        <div className="flex items-center gap-3 min-w-0">
          {open ? <ChevronDown size={14} className="shrink-0" /> : <ChevronRight size={14} className="shrink-0" />}
          <span className="text-xs text-gray-400 shrink-0">{index + 1}/{total}</span>
          <span className="font-medium text-gray-800 truncate">{result.test_case_title ?? tc?.name ?? "…"}</span>
        </div>
        <div className="flex items-center gap-2 shrink-0 ml-3">
          {result.duration_ms != null && (
            <span className="text-xs text-gray-400 flex items-center gap-1">
              <Clock size={10} />{fmtDuration(result.duration_ms)}
            </span>
          )}
          {result.executed_at && (
            <span className="text-xs text-gray-400 hidden sm:block">{fmtTime(result.executed_at)}</span>
          )}
          <Badge variant={config.color}><Icon size={11} className="mr-1" />{config.label}</Badge>
        </div>
      </div>

      {open && (
        <div className="p-4 space-y-4 bg-white">
          {result.comment && !isAutomated && (
            <p className="text-sm text-gray-600 italic border-l-2 border-gray-200 pl-3">{result.comment}</p>
          )}
          {result.comment && isAutomated && (
            <div className="text-xs font-mono bg-red-50 border border-red-200 text-red-800 rounded-lg px-3 py-2 whitespace-pre-wrap">
              {result.comment}
            </div>
          )}

          {tc?.steps?.length > 0 && (
            <div className="space-y-2">
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Steps</p>
              <StepsSection
                steps={tc.steps}
                stepResults={result.step_results ?? []}
                onUpdate={updateStepResult}
                isAutomated={isAutomated}
              />
            </div>
          )}

          {!isAutomated && (
            <>
              <div className="space-y-1.5">
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Overall result</p>
                <div className="flex gap-2">
                  {Object.entries(STATUS_CONFIG).map(([status, cfg]) => {
                    const Ic = cfg.icon
                    return (
                      <Button key={status} size="sm"
                        variant={overallStatus === status ? "default" : "outline"}
                        onClick={() => setStatus(status)}>
                        <Ic size={13} /> {cfg.label}
                      </Button>
                    )
                  })}
                </div>
              </div>

              <div className="space-y-1.5">
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Comment</p>
                <MdEditor value={comment} onChange={setComment} height={80} />
                <Button size="sm" variant="outline" onClick={saveComment}
                  loading={updateResult.isPending}>Save comment</Button>
              </div>
            </>
          )}

          <div className="space-y-2">
            <label className="flex items-center gap-2 cursor-pointer w-fit">
              <input type="file" className="hidden" onChange={uploadAttachment} />
              <Button size="sm" variant="ghost" asChild>
                <span><Upload size={13} /> Attach file</span>
              </Button>
            </label>
            {(result.attachments ?? []).length > 0 && (
              <ul className="space-y-1.5">
                {(result.attachments ?? []).map(a => (
                  <li key={a.id} className="flex items-center gap-2 text-sm bg-gray-50 rounded-lg px-3 py-2">
                    <span className="text-xs bg-white border px-1.5 py-0.5 rounded text-gray-500 shrink-0">
                      {a.content_type ?? "file"}
                    </span>
                    <a href={a.url} target="_blank" rel="noopener noreferrer"
                      className="flex items-center gap-1 text-gray-700 hover:text-primary-600 min-w-0 flex-1 truncate">
                      {a.filename}<ExternalLink size={11} className="shrink-0" />
                    </a>
                    <span className="text-xs text-gray-400 shrink-0">
                      {a.size_bytes ? `${Math.round(a.size_bytes / 1024)} KB` : ""}
                    </span>
                    <button onClick={() => copyUrl(a)} title="Copy URL" className="text-gray-400 hover:text-gray-700 shrink-0">
                      <Copy size={13} />
                    </button>
                    <button onClick={() => copyMarkdown(a)} title="Copy as Markdown"
                      className="text-xs text-gray-400 hover:text-gray-700 font-mono shrink-0">MD</button>
                    <button onClick={() => deleteAttachment(a.id)} title="Delete"
                      className="text-gray-300 hover:text-red-500 shrink-0">
                      <Trash2 size={13} />
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export function ExecutionRunPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { data: execution } = useExecution(id)
  const { data: results = [] } = useExecutionResults(id)
  const qc = useQueryClient()
  const [finishing, setFinishing] = useState(false)

  const finishExecution = async () => {
    setFinishing(true)
    try {
      await executionsApi.update(id, { status: "completed", finished_at: new Date().toISOString() })
      toast.success("Execution completed")
      navigate(`/executions/${id}`)
      qc.invalidateQueries({ queryKey: ["executions", id] })
    } catch {
      toast.error("Failed to finish execution")
      setFinishing(false)
    }
  }

  if (!execution) return <p className="text-gray-500">Loading…</p>

  const summary = execution.summary ?? {}
  const done = (summary.passed ?? 0) + (summary.failed ?? 0) + (summary.blocked ?? 0)
  const totalMs = execution.started_at && execution.finished_at
    ? new Date(execution.finished_at) - new Date(execution.started_at)
    : null

  return (
    <div className="max-w-2xl space-y-4">
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <Link to={`/projects/${execution.project_id}/executions`}
          className="flex items-center gap-1 hover:text-gray-800 transition-colors">
          <ArrowLeft size={14} /> Executions
        </Link>
      </div>

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
          disabled={execution.status === "completed"}
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
          <ResultCard key={result.id} result={result} index={i} total={results.length}
            isAutomated={execution.type === "automatic"} />
        ))}
      </div>
    </div>
  )
}
