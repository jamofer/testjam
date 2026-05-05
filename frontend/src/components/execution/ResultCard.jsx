import { useState, useEffect, useRef } from "react"
import { useQueryClient } from "@tanstack/react-query"
import { ChevronDown, ChevronRight, Trash2, Copy, ExternalLink, Upload, Clock } from "lucide-react"
import { useCase } from "../../hooks/useSuites"
import { useUpdateResult } from "../../hooks/useExecutions"
import { executionsApi } from "../../api/executions"
import { MdEditor, MdViewer } from "../MdEditor"
import { Button } from "../ui/button"
import { Badge } from "../ui/badge"
import { STATUS_CONFIG } from "../../lib/statusConfig"
import { fmtDuration, fmtTime } from "../../lib/format"
import { StepsSection } from "./StepsSection"
import { toast } from "sonner"

export function ResultCard({ result, executionId, index, total, isAutomated, focused = false, onFocus }) {
  const { data: tc } = useCase(result.test_case_id)
  const [open, setOpen] = useState(index === 0)
  const [comment, setComment] = useState(result.comment ?? "")
  const [editComment, setEditComment] = useState(false)
  const [localStatus, setLocalStatus] = useState(result.status)
  const qc = useQueryClient()
  const updateResult = useUpdateResult(executionId)
  const cardRef = useRef(null)

  useEffect(() => {
    setLocalStatus(result.status)
    setComment(result.comment ?? "")
  }, [result.status, result.comment])

  useEffect(() => {
    if (focused && cardRef.current) {
      cardRef.current.scrollIntoView({ block: "nearest", behavior: "smooth" })
    }
  }, [focused])

  const config = STATUS_CONFIG[localStatus]
  const Icon = config.icon

  const setStatus = async (status) => {
    setLocalStatus(status)
    try {
      await updateResult.mutateAsync({ id: result.id, data: { status } })
      qc.invalidateQueries({ queryKey: ["executions", executionId] })
    } catch {
      setLocalStatus(result.status)
      toast.error("Failed to update status")
    }
  }

  const updateStepResult = async (stepId, status) => {
    try {
      const existingSr = (result.step_results ?? []).find(sr => sr.step_id === stepId)
      if (existingSr) {
        await executionsApi.updateStepResult(result.id, existingSr.id, { status })
      } else {
        await executionsApi.createResult(executionId, {
          test_case_id: result.test_case_id,
          status: result.status,
          step_results: [{ step_id: stepId, status }],
        })
      }
      qc.invalidateQueries({ queryKey: ["results", executionId] })
      qc.invalidateQueries({ queryKey: ["executions", executionId] })
    } catch {
      toast.error("Failed to update step")
    }
  }

  const saveStepComment = async (stepId, comment) => {
    try {
      const existingSr = (result.step_results ?? []).find(sr => sr.step_id === stepId)
      if (existingSr) {
        await executionsApi.updateStepResult(result.id, existingSr.id, { comment })
      } else {
        await executionsApi.createResult(executionId, {
          test_case_id: result.test_case_id,
          status: result.status,
          step_results: [{ step_id: stepId, status: "not_run", comment }],
        })
      }
      qc.invalidateQueries({ queryKey: ["results", executionId] })
    } catch {
      toast.error("Failed to save note")
    }
  }

  const saveComment = async () => {
    try {
      await updateResult.mutateAsync({ id: result.id, data: { comment } })
      setEditComment(false)
    } catch {
      toast.error("Failed to save comment")
    }
  }

  const uploadAttachment = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    try {
      await executionsApi.uploadResultAttachment(result.id, file)
      qc.invalidateQueries({ queryKey: ["results", executionId] })
      toast.success(`${file.name} attached`)
    } catch {
      toast.error("Upload failed")
    }
    e.target.value = ""
  }

  const deleteAttachment = async (attachmentId) => {
    try {
      await executionsApi.deleteResultAttachment(result.id, attachmentId)
      qc.invalidateQueries({ queryKey: ["results", executionId] })
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
    <div ref={cardRef}
      className={`border rounded-xl overflow-hidden shadow-sm transition-shadow ${focused ? "ring-2 ring-primary-400 shadow-md" : ""}`}>
      <div className={`flex items-center justify-between px-4 py-3 cursor-pointer ${config.bg} border-b`}
        onClick={() => { setOpen(o => !o); onFocus?.() }}>
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
          <Badge variant={config.badgeVariant}><Icon size={11} className="mr-1" />{config.label}</Badge>
        </div>
      </div>

      {open && (
        <div className="p-4 space-y-4 bg-white">
          {tc?.steps?.length > 0 && (
            <div className="space-y-2">
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Steps</p>
              <StepsSection
                steps={tc.steps}
                stepResults={result.step_results ?? []}
                onUpdate={updateStepResult}
                onSaveComment={saveStepComment}
                isAutomated={isAutomated}
              />
            </div>
          )}

          {!isAutomated && (
            <>
              <div className="space-y-1.5">
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Overall result</p>
                <div className="flex gap-2 flex-wrap">
                  {Object.entries(STATUS_CONFIG).map(([status, cfg]) => {
                    const Ic = cfg.icon
                    return (
                      <Button key={status} size="sm"
                        variant={localStatus === status ? "default" : "outline"}
                        onClick={() => setStatus(status)}>
                        <Ic size={13} /> {cfg.label}
                      </Button>
                    )
                  })}
                </div>
              </div>

              <div className="space-y-1.5">
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Comment</p>
                {editComment ? (
                  <div className="space-y-1.5">
                    <MdEditor value={comment} onChange={setComment} height={80} />
                    <div className="flex gap-2">
                      <Button size="sm" variant="outline" onClick={saveComment} loading={updateResult.isPending}>
                        Save
                      </Button>
                      <Button size="sm" variant="ghost" onClick={() => { setEditComment(false); setComment(result.comment ?? "") }}>
                        Cancel
                      </Button>
                    </div>
                  </div>
                ) : comment ? (
                  <button onClick={() => setEditComment(true)} className="text-left w-full group">
                    <div className="text-sm text-gray-600 italic border-l-2 border-gray-200 pl-3 group-hover:border-gray-400 transition-colors">
                      <MdViewer value={comment} />
                    </div>
                  </button>
                ) : (
                  <button onClick={() => setEditComment(true)}
                    className="text-xs text-gray-400 hover:text-gray-600 transition-colors">
                    + Add comment
                  </button>
                )}
              </div>
            </>
          )}

          {isAutomated && result.comment && (
            <div className="text-xs font-mono bg-red-50 border border-red-200 text-red-800 rounded-lg px-3 py-2 whitespace-pre-wrap">
              {result.comment}
            </div>
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
