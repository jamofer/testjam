import { useState, useEffect } from "react"
import { Clock } from "lucide-react"
import { MdViewer } from "../MdEditor"
import { STATUS_CONFIG } from "../../lib/statusConfig"
import { fmtDuration } from "../../lib/format"

export function StepResultRow({ step, stepResult, onUpdate, onSaveComment, isAutomated }) {
  const [localStatus, setLocalStatus] = useState(stepResult?.status ?? "not_run")
  const [comment, setComment] = useState(stepResult?.comment ?? "")
  const [editComment, setEditComment] = useState(false)
  const [saving, setSaving] = useState(false)
  const [showLog, setShowLog] = useState(false)

  useEffect(() => {
    setLocalStatus(stepResult?.status ?? "not_run")
    setComment(stepResult?.comment ?? "")
  }, [stepResult?.status, stepResult?.comment])

  const config = STATUS_CONFIG[localStatus]

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

  return (
    <div className={`border rounded-lg overflow-hidden ${config.bg}`}>
      <div className="flex items-start gap-3 p-3">
        <span className="text-xs font-mono text-gray-400 mt-0.5 w-5 shrink-0">{step.order}.</span>
        <div className="flex-1 min-w-0">
          <div className="prose prose-sm"><MdViewer value={step.action} /></div>
          {step.expected_result && (
            <p className="text-xs text-gray-500 mt-1 italic">Expected: <MdViewer value={step.expected_result} /></p>
          )}
          {stepResult?.duration_ms != null && (
            <span className="text-xs text-gray-400 flex items-center gap-1 mt-0.5">
              <Clock size={9} /> {fmtDuration(stepResult.duration_ms)}
            </span>
          )}

          {!isAutomated && (
            <div className="mt-2">
              {editComment ? (
                <div className="space-y-1">
                  <textarea
                    value={comment}
                    onChange={e => setComment(e.target.value)}
                    placeholder="Actual result / notes…"
                    rows={2}
                    autoFocus
                    className="w-full text-xs border border-gray-300 rounded px-2 py-1 resize-none focus:outline-none focus:ring-1 focus:ring-primary-400 bg-white"
                  />
                  <div className="flex gap-1">
                    <button onClick={handleSaveComment} disabled={saving}
                      className="text-xs px-2 py-0.5 bg-primary-600 text-white rounded hover:bg-primary-700 disabled:opacity-50">
                      {saving ? "Saving…" : "Save"}
                    </button>
                    <button onClick={() => { setEditComment(false); setComment(stepResult?.comment ?? "") }}
                      className="text-xs px-2 py-0.5 text-gray-500 hover:text-gray-800">
                      Cancel
                    </button>
                  </div>
                </div>
              ) : comment ? (
                <button onClick={() => setEditComment(true)} className="text-left w-full group">
                  <p className="text-xs text-gray-700 bg-black/5 rounded px-2 py-1 border border-black/10 group-hover:border-black/20 transition-colors">
                    {comment}
                  </p>
                </button>
              ) : (
                <button onClick={() => setEditComment(true)}
                  className="text-xs text-gray-400 hover:text-gray-600 transition-colors">
                  + Add note
                </button>
              )}
            </div>
          )}

          {stepResult?.log_output && (
            <button onClick={() => setShowLog(l => !l)}
              className="text-xs text-gray-400 hover:text-gray-700 mt-1 underline block">
              {showLog ? "Hide log" : "Show log"}
            </button>
          )}
        </div>

        {!isAutomated && (
          <div className="flex gap-1 shrink-0">
            {Object.entries(STATUS_CONFIG).map(([status, cfg]) => {
              const Ic = cfg.icon
              return (
                <button key={status}
                  onClick={() => handleStatus(status)}
                  title={cfg.label}
                  className={`p-1 rounded transition-opacity ${localStatus === status ? "opacity-100" : "opacity-25 hover:opacity-70"}`}>
                  <Ic size={16} className={cfg.iconColor} />
                </button>
              )
            })}
          </div>
        )}
        {isAutomated && (
          <div className="shrink-0">
            {(() => { const Ic = config.icon; return <Ic size={16} className={config.iconColor} /> })()}
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
