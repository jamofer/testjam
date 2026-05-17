import { useState, useEffect, useRef } from "react"
import { useTranslation } from "react-i18next"
import { Clock } from "lucide-react"
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

  return (
    <div ref={rowRef} id={`step-${step.id}`} data-step-id={step.id}
      className={`relative border rounded-lg overflow-hidden ${config.bg} ${focused ? "ring-2 ring-red-400" : ""}`}>
      <div className="flex items-start gap-3 p-3">
        <span className="text-xs font-mono text-gray-400 dark:text-gray-500 mt-0.5 w-5 shrink-0">{step.order}.</span>
        <div className="flex-1 min-w-0">
          <div className="prose prose-sm"><MdViewer value={step.action} /></div>
          {step.expected_result && (
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 italic">{t("run.step.expected")} <MdViewer value={step.expected_result} /></p>
          )}

          {!isAutomated && (
            <div className="mt-2">
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
                  <p className="text-xs text-gray-700 dark:text-gray-200 bg-black/5 rounded px-2 py-1 border border-black/10 group-hover:border-black/20 transition-colors">
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

          {stepResult?.log_output && (
            <button onClick={() => setShowLog(value => !value)}
              className="text-xs text-gray-400 dark:text-gray-500 hover:text-gray-700 dark:hover:text-gray-200 mt-1 underline block">
              {showLog ? t("run.step.hideLog") : t("run.step.showLog")}
            </button>
          )}
        </div>

        {hasMeta && (
          <div className="flex items-center gap-2 text-[11px] text-gray-400 dark:text-gray-500 shrink-0 self-center whitespace-nowrap">
            {stepResult?.duration_ms != null && (
              <span className="flex items-center gap-1"><Clock size={10} />{fmtDuration(stepResult.duration_ms)}</span>
            )}
            {stepResult?.started_at && (
              <>
                {stepResult?.duration_ms != null && <span>·</span>}
                <span>{fmtTime(stepResult.started_at)}</span>
              </>
            )}
          </div>
        )}

        {!isAutomated && (
          <div className="flex gap-1 shrink-0 self-center">
            {Object.entries(STATUS_CONFIG).map(([status, cfg]) => {
              const Ic = cfg.icon
              return (
                <button key={status}
                  onClick={() => handleStatus(status)}
                  title={statusLabel(status)}
                  className={`p-1 rounded transition-opacity ${localStatus === status ? "opacity-100" : "opacity-25 hover:opacity-70"}`}>
                  <Ic size={16} className={cfg.iconColor} />
                </button>
              )
            })}
          </div>
        )}
        {isAutomated && (
          <div className="shrink-0 self-center">
            {(() => { const Ic = config.icon; return <Ic size={16} className={config.iconColor} /> })()}
          </div>
        )}
      </div>

      {showLog && stepResult?.log_output && (
        <div
          ref={logRef}
          data-testid="step-log-output"
          className="px-4 pb-3 border-t border-gray-100 dark:border-gray-800 bg-gray-900 text-gray-100 text-xs font-mono whitespace-pre-wrap rounded-b-lg max-h-48 overflow-y-auto"
        >
          {stepResult.log_output}
        </div>
      )}
    </div>
  )
}
