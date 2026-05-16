import { useTranslation } from "react-i18next"
import { Trash2, Upload, ExternalLink } from "lucide-react"
import { useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"
import { casesApi } from "../../api/testcases"
import { useCaseRevisions } from "../../hooks/useSuites"
import { fmtDateTime } from "../../lib/format"

export function PanelAttachments({ caseId, attachments }) {
  const { t } = useTranslation("cases")
  const qc = useQueryClient()

  const upload = async (event) => {
    const file = event.target.files[0]
    if (!file) return
    await casesApi.uploadAttachment(caseId, file)
    qc.invalidateQueries({ queryKey: ["case", caseId] })
    toast.success(t("attachments.uploaded", { name: file.name }))
    event.target.value = ""
  }

  const remove = async (attachmentId) => {
    await casesApi.deleteAttachment(caseId, attachmentId)
    qc.invalidateQueries({ queryKey: ["case", caseId] })
    toast.success(t("attachments.deleted"))
  }

  return (
    <div className="space-y-1.5">
      {attachments.length === 0 && (
        <p className="text-[11px] text-gray-400 dark:text-gray-500">{t("attachments.panelEmpty")}</p>
      )}
      <ul className="space-y-1">
        {attachments.map(attachment => (
          <li key={attachment.id} className="flex items-center gap-1.5 text-xs">
            <button type="button"
              onClick={() => casesApi.downloadAttachment(caseId, attachment.id, attachment.filename)
                .catch(() => toast.error(t("attachments.downloadFailed")))}
              className="flex-1 min-w-0 truncate text-left text-gray-700 dark:text-gray-200 hover:text-primary-600 flex items-center gap-1">
              {attachment.filename}
              <ExternalLink size={10} className="shrink-0 text-gray-400 dark:text-gray-500" />
            </button>
            <button onClick={() => remove(attachment.id)}
              title={t("attachments.delete")}
              className="text-gray-300 dark:text-gray-600 hover:text-red-500 shrink-0">
              <Trash2 size={11} />
            </button>
          </li>
        ))}
      </ul>
      <label className="inline-flex items-center gap-1 cursor-pointer text-[11px] text-gray-500 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-100">
        <input type="file" className="hidden" onChange={upload} />
        <Upload size={11} /> {t("attachments.upload")}
      </label>
    </div>
  )
}

export function PanelHistory({ caseId }) {
  const { t } = useTranslation("cases")
  const { data: revs = [] } = useCaseRevisions(caseId)
  const top = revs.slice(0, 5)
  if (top.length === 0) return <p className="text-[11px] text-gray-400 dark:text-gray-500">{t("history.panelEmpty")}</p>
  return (
    <ul className="space-y-1">
      {top.map(rev => {
        const kindCls = rev.change_kind === "created"
          ? "bg-green-50 text-green-700 border-green-200"
          : "bg-blue-50 text-blue-700 border-blue-200"
        const actor = rev.actor?.full_name || rev.actor?.username || t("history.actorSystem")
        return (
          <li key={rev.id} className="flex items-center gap-1.5 text-[11px]">
            <span className={`px-1 py-0.5 rounded border text-[9px] uppercase font-bold shrink-0 ${kindCls}`}>
              {rev.change_kind}
            </span>
            <span className="text-gray-700 dark:text-gray-200 shrink-0">{actor}</span>
            <span className="text-gray-400 dark:text-gray-500 truncate">· {fmtDateTime(rev.created_at)}</span>
          </li>
        )
      })}
      {revs.length > top.length && (
        <li className="text-[11px] text-gray-400 dark:text-gray-500">{t("history.panelMore", { count: revs.length - top.length })}</li>
      )}
    </ul>
  )
}
