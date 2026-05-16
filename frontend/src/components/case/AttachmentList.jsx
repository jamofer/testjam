import { useTranslation } from "react-i18next"
import { Trash2, Upload, Copy, ExternalLink } from "lucide-react"
import { useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"
import { casesApi } from "../../api/testcases"
import { Button } from "../ui/button"
import { EmptyState } from "../ui/empty-state"

export function AttachmentList({ caseId, attachments }) {
  const { t } = useTranslation("cases")
  const qc = useQueryClient()

  const handleUpload = async (event) => {
    const file = event.target.files[0]
    if (!file) return
    await casesApi.uploadAttachment(caseId, file)
    qc.invalidateQueries({ queryKey: ["case", caseId] })
    toast.success(t("attachments.uploaded", { name: file.name }))
    event.target.value = ""
  }

  const handleDelete = async (attachmentId) => {
    await casesApi.deleteAttachment(caseId, attachmentId)
    qc.invalidateQueries({ queryKey: ["case", caseId] })
    toast.success(t("attachments.deleted"))
  }

  const copyUrl = (attachment) => {
    const url = `${window.location.origin}${attachment.url}`
    navigator.clipboard.writeText(url)
    toast.success(t("attachments.urlCopied"))
  }

  const copyMarkdown = (attachment) => {
    const url = `${window.location.origin}${attachment.url}`
    const markdown = attachment.content_type?.startsWith("image/")
      ? `![${attachment.filename}](${url})`
      : `[${attachment.filename}](${url})`
    navigator.clipboard.writeText(markdown)
    toast.success(t("attachments.markdownCopied"))
  }

  return (
    <div className="space-y-3">
      <label className="flex items-center gap-2 cursor-pointer w-fit">
        <input type="file" className="hidden" onChange={handleUpload} />
        <Button variant="outline" size="sm" asChild>
          <span><Upload size={13} /> {t("attachments.upload")}</span>
        </Button>
      </label>
      {attachments.length === 0 && (
        <EmptyState
          icon={Upload}
          title={t("attachments.emptyTitle")}
          description={t("attachments.emptyDescription")}
          compact
        />
      )}
      <ul className="space-y-1.5">
        {attachments.map(attachment => (
          <li key={attachment.id} className="flex items-center gap-2 text-sm bg-gray-50 rounded-lg px-3 py-2">
            <span className="text-xs bg-white dark:bg-gray-900 border px-1.5 py-0.5 rounded text-gray-500 dark:text-gray-400 shrink-0">
              {attachment.content_type ?? "file"}
            </span>
            <button type="button"
              onClick={() => casesApi.downloadAttachment(caseId, attachment.id, attachment.filename)
                .catch(() => toast.error(t("attachments.downloadFailed")))}
              className="flex items-center gap-1 text-left text-gray-700 dark:text-gray-200 hover:text-primary-600 min-w-0 flex-1 truncate">
              {attachment.filename}
              <ExternalLink size={11} className="shrink-0" />
            </button>
            <span className="text-xs text-gray-400 dark:text-gray-500 shrink-0">
              {attachment.size_bytes ? `${Math.round(attachment.size_bytes / 1024)} KB` : ""}
            </span>
            <button onClick={() => copyUrl(attachment)} title={t("attachments.copyUrl")} className="text-gray-400 dark:text-gray-500 hover:text-gray-700 dark:hover:text-gray-200 shrink-0">
              <Copy size={13} />
            </button>
            <button onClick={() => copyMarkdown(attachment)} title={t("attachments.copyMarkdown")}
              className="text-xs text-gray-400 dark:text-gray-500 hover:text-gray-700 dark:hover:text-gray-200 font-mono shrink-0">MD</button>
            <button onClick={() => handleDelete(attachment.id)} title={t("attachments.delete")}
              className="text-gray-300 dark:text-gray-600 hover:text-red-500 shrink-0">
              <Trash2 size={13} />
            </button>
          </li>
        ))}
      </ul>
    </div>
  )
}
