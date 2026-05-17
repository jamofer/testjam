import { useState, useEffect, useRef, useContext, createContext } from "react"
import { useTranslation } from "react-i18next"
import { useQueryClient } from "@tanstack/react-query"
import { Bug, ChevronDown, ChevronRight, Trash2, Copy, ExternalLink, Upload, Clock } from "lucide-react"
import { useCase } from "../../hooks/useSuites"
import { useExecution, useUpdateResult } from "../../hooks/useExecutions"
import { NewBugDialog } from "../bug/NewBugDialog"
import { executionsApi } from "../../api/executions"
import { MdEditor } from "../MdEditor"
import { Button } from "../ui/button"
import { Badge } from "../ui/badge"
import { STATUS_CONFIG } from "../../lib/statusConfig"
import { fmtDuration, fmtTime } from "../../lib/format"
import { StepsSection } from "./StepsSection"
import { toast } from "sonner"

const KEEP_OPEN_STATUSES = new Set(["running", "failed", "blocked"])

export const ResultExpandContext = createContext({ version: 0, desiredOpen: null })

export function ResultCard({ result, executionId, index, total, isAutomated, focused = false, onFocus, focusedStepId = null }) {
  const { t } = useTranslation(["executions", "common"])
  const { data: tc } = useCase(result.test_case_id)
  const { data: execution } = useExecution(executionId)
  const [open, setOpen] = useState(index === 0 || KEEP_OPEN_STATUSES.has(result.status))
  const [comment, setComment] = useState(result.comment ?? "")
  const [localStatus, setLocalStatus] = useState(result.status)
  const qc = useQueryClient()
  const updateResult = useUpdateResult(executionId)
  const cardRef = useRef(null)
  const previousStatusRef = useRef(result.status)
  const lastStepTickRef = useRef(Date.now())

  useEffect(() => {
    setLocalStatus(result.status)
    setComment(result.comment ?? "")
  }, [result.status, result.comment])

  useEffect(() => {
    const previousStatus = previousStatusRef.current
    if (previousStatus === result.status) return
    previousStatusRef.current = result.status
    if (result.status === "passed") setOpen(false)
    else if (KEEP_OPEN_STATUSES.has(result.status)) setOpen(true)
  }, [result.status])

  useEffect(() => {
    if (focused && cardRef.current) {
      cardRef.current.scrollIntoView({ block: "center", behavior: "smooth" })
    }
  }, [focused])

  const expandContext = useContext(ResultExpandContext)
  useEffect(() => {
    if (expandContext.version > 0 && expandContext.desiredOpen != null) {
      setOpen(expandContext.desiredOpen)
    }
  }, [expandContext.version, expandContext.desiredOpen])

  useEffect(() => {
    const card = cardRef.current
    if (!card) return undefined
    const handler = (event) => {
      const desired = event.detail?.open
      setOpen(typeof desired === "boolean" ? desired : (value => !value))
    }
    card.addEventListener("result-toggle", handler)
    return () => card.removeEventListener("result-toggle", handler)
  }, [])

  const config = STATUS_CONFIG[localStatus]
  const Icon = config.icon
  const commentDirty = comment !== (result.comment ?? "")
  const statusLabel = (status) => t(`common:status.${status}`, STATUS_CONFIG[status]?.label ?? status)

  const setStatus = async (status) => {
    setLocalStatus(status)
    try {
      const data = commentDirty ? { status, comment } : { status }
      await updateResult.mutateAsync({ id: result.id, data })
      qc.invalidateQueries({ queryKey: ["executions", executionId] })
    } catch {
      setLocalStatus(result.status)
      toast.error(t("run.updateStatusFailed"))
    }
  }

  const updateStepResult = async (stepId, status) => {
    try {
      const now = Date.now()
      const duration_ms = Math.max(0, now - lastStepTickRef.current)
      lastStepTickRef.current = now
      const existingSr = (result.step_results ?? []).find(sr => sr.step_id === stepId)
      if (existingSr) {
        await executionsApi.updateStepResult(result.id, existingSr.id, { status, duration_ms })
      } else {
        await executionsApi.createResult(executionId, {
          test_case_id: result.test_case_id,
          status: result.status,
          step_results: [{ step_id: stepId, status, duration_ms }],
        })
      }
      qc.invalidateQueries({ queryKey: ["results", executionId] })
      qc.invalidateQueries({ queryKey: ["executions", executionId] })
    } catch {
      toast.error(t("run.updateStepFailed"))
    }
  }

  const saveStepComment = async (stepId, stepComment) => {
    try {
      const existingSr = (result.step_results ?? []).find(sr => sr.step_id === stepId)
      if (existingSr) {
        await executionsApi.updateStepResult(result.id, existingSr.id, { comment: stepComment })
      } else {
        await executionsApi.createResult(executionId, {
          test_case_id: result.test_case_id,
          status: result.status,
          step_results: [{ step_id: stepId, status: "not_run", comment: stepComment }],
        })
      }
      qc.invalidateQueries({ queryKey: ["results", executionId] })
    } catch {
      toast.error(t("run.saveNoteFailed"))
    }
  }

  const saveComment = async () => {
    try {
      await updateResult.mutateAsync({ id: result.id, data: { comment } })
    } catch {
      toast.error(t("run.saveCommentFailed"))
    }
  }

  const uploadAttachment = async (event) => {
    const file = event.target.files[0]
    if (!file) return
    try {
      await executionsApi.uploadResultAttachment(result.id, file)
      qc.invalidateQueries({ queryKey: ["results", executionId] })
      toast.success(t("run.attachedSuccess", { name: file.name }))
    } catch {
      toast.error(t("run.uploadFailed"))
    }
    event.target.value = ""
  }

  const deleteAttachment = async (attachmentId) => {
    try {
      await executionsApi.deleteResultAttachment(result.id, attachmentId)
      qc.invalidateQueries({ queryKey: ["results", executionId] })
      toast.success(t("run.attachmentDeleted"))
    } catch {
      toast.error(t("run.attachmentDeleteFailed"))
    }
  }

  const copyUrl = (attachment) => {
    navigator.clipboard.writeText(`${window.location.origin}${attachment.url}`)
    toast.success(t("run.urlCopied"))
  }

  const copyMarkdown = (attachment) => {
    const url = `${window.location.origin}${attachment.url}`
    const markdown = attachment.content_type?.startsWith("image/")
      ? `![${attachment.filename}](${url})`
      : `[${attachment.filename}](${url})`
    navigator.clipboard.writeText(markdown)
    toast.success(t("run.markdownCopied"))
  }

  return (
    <div ref={cardRef}
      id={`result-${result.id}`}
      data-result-id={result.id}
      className="relative border rounded-xl overflow-hidden shadow-sm transition-shadow">
      {focused && (
        <span aria-hidden="true"
          className="absolute left-0 top-0 bottom-0 w-[3px] bg-red-500 pointer-events-none z-10" />
      )}
      <div className={`flex items-center justify-between px-4 py-3 cursor-pointer ${config.bg} border-b`}
        onClick={() => { setOpen(value => !value); onFocus?.() }}>
        <div className="flex items-center gap-3 min-w-0">
          {open ? <ChevronDown size={14} className="shrink-0" /> : <ChevronRight size={14} className="shrink-0" />}
          <span className="text-xs text-gray-400 dark:text-gray-500 shrink-0">{index + 1}/{total}</span>
          <span className="font-medium text-gray-800 dark:text-gray-100 truncate">{result.test_case_title ?? tc?.name ?? "…"}</span>
        </div>
        <div className="flex items-center gap-2 shrink-0 ml-3">
          {result.duration_ms != null && (
            <span className="text-xs text-gray-400 dark:text-gray-500 flex items-center gap-1">
              <Clock size={10} />{fmtDuration(result.duration_ms)}
            </span>
          )}
          {result.executed_at && (
            <span className="text-xs text-gray-400 dark:text-gray-500 hidden sm:block">{fmtTime(result.executed_at)}</span>
          )}
          <Badge variant={config.badgeVariant}><Icon size={11} className="mr-1" />{statusLabel(localStatus)}</Badge>
        </div>
      </div>

      {open && (
        <div className="p-4 space-y-4 bg-white dark:bg-gray-900">
          {tc?.steps?.length > 0 && (
            <div className="space-y-2">
              <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">{t("run.stepsLabel")}</p>
              <StepsSection
                steps={tc.steps}
                stepResults={result.step_results ?? []}
                onUpdate={updateStepResult}
                onSaveComment={saveStepComment}
                isAutomated={isAutomated}
                focusedStepId={focused ? focusedStepId : null}
              />
            </div>
          )}

          {!isAutomated && (
            <>
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">{t("run.commentLabel")}</p>
                  {commentDirty && (
                    <button type="button" onClick={saveComment}
                      className="text-xs text-primary-600 hover:underline disabled:opacity-50"
                      disabled={updateResult.isPending}>
                      {t("run.saveComment")}
                    </button>
                  )}
                </div>
                <MdEditor value={comment} onChange={setComment} height={80} />
                <p className="text-[11px] text-gray-400 dark:text-gray-500">{t("run.commentHint")}</p>
              </div>

              <div className="space-y-1.5">
                <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">{t("run.overallResult")}</p>
                <div className="flex gap-2 flex-wrap">
                  {Object.entries(STATUS_CONFIG).map(([status, cfg]) => {
                    const Ic = cfg.icon
                    return (
                      <Button key={status} size="sm"
                        variant={localStatus === status ? "default" : "outline"}
                        onClick={() => setStatus(status)}>
                        <Ic size={13} /> {statusLabel(status)}
                      </Button>
                    )
                  })}
                </div>
              </div>
            </>
          )}

          {isAutomated && result.comment && (
            <div className="text-xs font-mono bg-red-50 border border-red-200 text-red-800 rounded-lg px-3 py-2 whitespace-pre-wrap">
              {result.comment}
            </div>
          )}

          <div className="space-y-2">
            {(localStatus === "failed" || localStatus === "blocked") && execution?.project_id && (
              <NewBugDialog
                projectId={execution.project_id}
                prefill={{
                  result_id: result.id,
                  execution_id: executionId,
                  version_id: execution.version_id,
                  environment: execution.environment,
                  description: result.comment
                    ? `**From result:** ${tc?.name ?? result.test_case_id}\n\n\`\`\`\n${result.comment}\n\`\`\``
                    : `**From result:** ${tc?.name ?? result.test_case_id}`,
                  severity: localStatus === "blocked" ? "critical" : "high",
                }}
                trigger={(
                  <Button size="sm" variant="outline">
                    <Bug size={13} /> {t("run.reportBug", "Report bug")}
                  </Button>
                )}
              />
            )}
            <label className="flex items-center gap-2 cursor-pointer w-fit">
              <input type="file" className="hidden" onChange={uploadAttachment} />
              <Button size="sm" variant="ghost" asChild>
                <span><Upload size={13} /> {t("run.attachFile")}</span>
              </Button>
            </label>
            {(result.attachments ?? []).length > 0 && (
              <ul className="space-y-1.5">
                {(result.attachments ?? []).map(attachment => (
                  <li key={attachment.id} className="flex items-center gap-2 text-sm bg-gray-50 dark:bg-gray-900 rounded-lg px-3 py-2">
                    <span className="text-xs bg-white dark:bg-gray-900 border px-1.5 py-0.5 rounded text-gray-500 dark:text-gray-400 shrink-0">
                      {attachment.content_type ?? "file"}
                    </span>
                    <button type="button"
                      onClick={() => executionsApi
                        .downloadResultAttachment(result.id, attachment.id, attachment.filename)
                        .catch(() => toast.error(t("run.downloadFailed")))}
                      className="flex items-center gap-1 text-left text-gray-700 dark:text-gray-200 hover:text-primary-600 min-w-0 flex-1 truncate">
                      {attachment.filename}<ExternalLink size={11} className="shrink-0" />
                    </button>
                    <span className="text-xs text-gray-400 dark:text-gray-500 shrink-0">
                      {attachment.size_bytes ? `${Math.round(attachment.size_bytes / 1024)} KB` : ""}
                    </span>
                    <button onClick={() => copyUrl(attachment)} title={t("run.copyUrl")} className="text-gray-400 dark:text-gray-500 hover:text-gray-700 dark:hover:text-gray-200 shrink-0">
                      <Copy size={13} />
                    </button>
                    <button onClick={() => copyMarkdown(attachment)} title={t("run.copyMarkdown")}
                      className="text-xs text-gray-400 dark:text-gray-500 hover:text-gray-700 dark:hover:text-gray-200 font-mono shrink-0">MD</button>
                    <button onClick={() => deleteAttachment(attachment.id)} title={t("run.deleteAttachment")}
                      className="text-gray-300 dark:text-gray-600 hover:text-red-500 shrink-0">
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
