import { Trash2, Upload, ExternalLink } from "lucide-react"
import { useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"
import { casesApi } from "../../api/testcases"
import { useCaseRevisions } from "../../hooks/useSuites"
import { fmtDateTime } from "../../lib/format"

export function PanelAttachments({ caseId, attachments }) {
  const qc = useQueryClient()

  const upload = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    await casesApi.uploadAttachment(caseId, file)
    qc.invalidateQueries({ queryKey: ["case", caseId] })
    toast.success(`${file.name} uploaded`)
    e.target.value = ""
  }

  const remove = async (attachmentId) => {
    await casesApi.deleteAttachment(caseId, attachmentId)
    qc.invalidateQueries({ queryKey: ["case", caseId] })
    toast.success("Attachment deleted")
  }

  return (
    <div className="space-y-1.5">
      {attachments.length === 0 && (
        <p className="text-[11px] text-gray-400">No attachments</p>
      )}
      <ul className="space-y-1">
        {attachments.map(att => (
          <li key={att.id} className="flex items-center gap-1.5 text-xs">
            <a href={att.url} target="_blank" rel="noopener noreferrer"
              className="flex-1 min-w-0 truncate text-gray-700 hover:text-primary-600 flex items-center gap-1">
              {att.filename}
              <ExternalLink size={10} className="shrink-0 text-gray-400" />
            </a>
            <button onClick={() => remove(att.id)}
              title="Delete"
              className="text-gray-300 hover:text-red-500 shrink-0">
              <Trash2 size={11} />
            </button>
          </li>
        ))}
      </ul>
      <label className="inline-flex items-center gap-1 cursor-pointer text-[11px] text-gray-500 hover:text-gray-800">
        <input type="file" className="hidden" onChange={upload} />
        <Upload size={11} /> Upload file
      </label>
    </div>
  )
}

export function PanelHistory({ caseId }) {
  const { data: revs = [] } = useCaseRevisions(caseId)
  const top = revs.slice(0, 5)
  if (top.length === 0) return <p className="text-[11px] text-gray-400">No history yet</p>
  return (
    <ul className="space-y-1">
      {top.map(rev => {
        const kindCls = rev.change_kind === "created"
          ? "bg-green-50 text-green-700 border-green-200"
          : "bg-blue-50 text-blue-700 border-blue-200"
        const actor = rev.actor?.full_name || rev.actor?.username || "system"
        return (
          <li key={rev.id} className="flex items-center gap-1.5 text-[11px]">
            <span className={`px-1 py-0.5 rounded border text-[9px] uppercase font-bold shrink-0 ${kindCls}`}>
              {rev.change_kind}
            </span>
            <span className="text-gray-700 shrink-0">{actor}</span>
            <span className="text-gray-400 truncate">· {fmtDateTime(rev.created_at)}</span>
          </li>
        )
      })}
      {revs.length > top.length && (
        <li className="text-[11px] text-gray-400">+ {revs.length - top.length} more in History tab</li>
      )}
    </ul>
  )
}
