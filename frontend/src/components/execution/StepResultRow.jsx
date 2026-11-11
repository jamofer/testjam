import { useState, useEffect, useRef } from "react"
import { useTranslation } from "react-i18next"
import { Clock, ScrollText } from "lucide-react"
import { MdViewer } from "../MdEditor"
import { STATUS_CONFIG } from "../../lib/statusConfig"
import { fmtDuration, fmtTime } from "../../lib/format"

export function StepResultRow({ step, stepResult, onUpdate, onSaveComment, isAutomated, focused = false, followLive = false }) {
  const { t } = useTranslation(["executions", "common"])
  const [localStatus, setLocalStatus] = useState(stepResult?.status ?? "not_run")
  const [comment, setComment] = useState(stepResult?.comment ?? "")
  const [editComment, setEditComment] = useState(false)
  const [saving, setSaving] = useState(false)
  const [showLog, setShowLog] = useState(stepResult?.status === "running")
  const logRef = useRef(null)
  const rowRef = useRef(null)

  useEffect(() => {
    setLocalStatus(stepResult?.status ?? "not_run")
    setComment(stepResult?.comment ?? "")
  }, [stepResult?.status, stepResult?.comment])

  useEffect(() => {
    if (stepResult?.status === "running") setShowLog(true)
  }, [stepResult?.status])

  useEffect(() => {
    if (!followLive) return
    if (stepResult?.status === "running" && rowRef.current) {
      rowRef.current.scrollIntoView({ block: "center", behavior: "smooth" })
    }
  }, [stepResult?.status, followLive])

  useEffect(() => {
    if (focused && rowRef.current) {
      rowRef.current.scrollIntoView({ block: "nearest", behavior: "smooth" })
    }
  }, [focused])

  useEffect(() => {
    if (!showLog || !logRef.current) return
    logRef.current.scrollTop = logRef.current.scrollHeight
  }, [showLog, stepResult?.log_output])

  const config = STATUS_CONFIG[localStatus]
  const statusLabel = (status) => t(`common:status.${status}`, STATUS_CONFIG[status]?.label ?? status)

  const handleStatus = async (status) => {
    setLocalStatus(status)
    await onUpdate(step.id, status)
  }

  const handleSaveComment = async () => {
    setSaving(true)
    try {
      await onSaveComment(step.id, comment)
      setEditComment(false)
    } catch {
      // error handled upstream
    } finally {
      setSaving(false)
    }
  }

  const hasMeta = stepResult?.duration_ms != null || stepResult?.started_at
  const hasLog = Boolean(stepResult?.log_output)
  const StatusIcon = config.icon

  return (
    <div ref={rowRef} id={`step-${step.id}`} data-step-id={step.id} data-testid="step-row" data-status={localStatus}
      className={`relative border rounded-md overflow-hidden ${config.bg} ${focused ? "ring-2 ring-red-400" : ""}`}>
      <div className="flex flex-wrap items-start gap-x-2 gap-y-1 px-2.5 py-1.5">
        {isAutomated && (
          <StatusIcon size={14} className={`${config.iconColor} shrink-0 mt-[3px]`} aria-label={statusLabel(localStatus)} />
        )}
        <span className="text-xs font-mono tabular-nums text-gray-400 dark:text-gray-500 min-w-[1.25rem] mt-px shrink-0">{step.order}.</span>
        <div className="flex-1 min-w-0">
          <div className="md-compact"><MdViewer value={step.action} /></div>
          {step.expected_result && (
            <div className="md-compact md-compact-muted flex gap-1 mt-0.5 italic">
              <span className="shrink-0">{t("run.step.expected")}</span>
              <div className="min-w-0"><MdViewer value={step.expected_result} /></div>
            </div>
          )}

          {!isAutomated && (
            <div className="mt-1">
              {editComment ? (
                <div className="space-y-1">
                  <textarea
                    value={comment}
                    onChange={event => setComment(event.target.value)}
                    placeholder={t("run.step.actualPlaceholder")}
                    rows={2}
                    autoFocus
                    className="w-full text-xs border border-gray-300 dark:border-gray-700 rounded px-2 py-1 resize-none focus:outline-none focus:ring-1 focus:ring-primary-400 bg-white dark:bg-gray-900"
                  />
                  <div className="flex gap-1">
                    <button onClick={handleSaveComment} disabled={saving}
                      className="text-xs px-2 py-0.5 bg-primary-600 text-white rounded hover:bg-primary-700 disabled:opacity-50">
                      {saving ? t("run.step.saving") : t("run.step.save")}
                    </button>
                    <button onClick={() => { setEditComment(false); setComment(stepResult?.comment ?? "") }}
                      className="text-xs px-2 py-0.5 text-gray-500 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-100">
                      {t("run.step.cancel")}
                    </button>
                  </div>
                </div>
              ) : comment ? (
                <button onClick={() => setEditComment(true)} className="text-left w-full group">
                  <p className="text-xs text-gray-700 dark:text-gray-200 bg-black/5 rounded px-2 py-1 border border-black/10 group-hover:border-black/20 transition-colors break-words">
                    {comment}
                  </p>
                </button>
              ) : (
                <button onClick={() => setEditComment(true)}
                  className="text-xs text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 transition-colors">
                  {t("run.step.addNote")}
                </button>
              )}
            </div>
          )}
        </div>

        {(hasMeta || hasLog) && (
          <div className="flex items-center gap-1.5 text-[11px] text-gray-400 dark:text-gray-500 shrink-0 whitespace-nowrap mt-0.5">
            {stepResult?.duration_ms != null && (
              <span className="flex items-center gap-1"><Clock size={10} />{fmtDuration(stepResult.duration_ms)}</span>
            )}
            {stepResult?.started_at && (
              <span className="hidden sm:inline">{fmtTime(stepResult.started_at)}</span>
            )}
            {hasLog && (
              <button type="button" onClick={() => setShowLog(value => !value)}
                data-testid="step-log-toggle"
                aria-expanded={showLog}
                aria-label={showLog ? t("run.step.hideLog") : t("run.step.showLog")}
                title={showLog ? t("run.step.hideLog") : t("run.step.showLog")}
                className={`p-1 -my-1 rounded hover:text-gray-700 dark:hover:text-gray-200 hover:bg-black/5 ${showLog ? "text-gray-700 dark:text-gray-200" : ""}`}>
                <ScrollText size={13} />
              </button>
            )}
          </div>
        )}

        {!isAutomated && (
          <div className="flex gap-1 shrink-0 basis-full justify-end sm:basis-auto">
            {Object.entries(STATUS_CONFIG).map(([status, cfg]) => {
              const Ic = cfg.icon
              return (
                <button key={status}
                  onClick={() => handleStatus(status)}
                  title={statusLabel(status)}
                  className={`p-1.5 sm:p-1 rounded transition-opacity ${localStatus === status ? "opacity-100" : "opacity-25 hover:opacity-70"}`}>
                  <Ic size={16} className={cfg.iconColor} />
                </button>
              )
            })}
          </div>
        )}
      </div>

      {showLog && hasLog && (
        <div
          ref={logRef}
          data-testid="step-log-output"
          className="px-3 py-2 border-t border-gray-100 dark:border-gray-800 bg-gray-900 text-gray-100 text-[11px] leading-relaxed font-mono whitespace-pre-wrap break-words max-h-48 overflow-y-auto"
        >
          {stepResult.log_output}
        </div>
      )}
    </div>
  )
}
