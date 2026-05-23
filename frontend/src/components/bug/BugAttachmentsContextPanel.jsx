import { useRef, useState } from "react"
import { useTranslation } from "react-i18next"
import { Copy, Paperclip, Trash2, Upload } from "lucide-react"
import { toast } from "sonner"

import {
  useBugAttachments,
  useDeleteBugAttachment,
  useUploadBugAttachment,
} from "../../hooks/useBugs"
import { bugsApi } from "../../api/bugs"
import { fmtBytes } from "../../lib/format"

export function BugAttachmentsContextPanel({ bugId }) {
  const { t } = useTranslation("bugs")
  const { data: attachments = [] } = useBugAttachments(bugId)
  const upload = useUploadBugAttachment()
  const remove = useDeleteBugAttachment()
  const fileInputRef = useRef(null)
  const [busyAttachmentId, setBusyAttachmentId] = useState(null)

  const handleFileChange = (event) => {
    const file = event.target.files?.[0]
    event.target.value = ""
    if (!file) return
    upload.mutate(
      { id: bugId, file },
      {
        onError: (error) =>
          toast.error(error?.response?.data?.detail ?? t("attachments.uploadFailed")),
      },
    )
  }

  const handleDownload = async (attachment) => {
    setBusyAttachmentId(attachment.id)
    try {
      await bugsApi.downloadAttachment(bugId, attachment.id, attachment.filename)
    } catch {
      toast.error(t("attachments.downloadFailed"))
    } finally {
      setBusyAttachmentId(null)
    }
  }

  const handleCopyMarkdown = async (attachment) => {
    const absoluteUrl = `${window.location.origin}${attachment.url}`
    const markdown = attachment.content_type?.startsWith("image/")
      ? `![${attachment.filename}](${absoluteUrl})`
      : `[${attachment.filename}](${absoluteUrl})`
    try {
      await navigator.clipboard.writeText(markdown)
      toast.success(t("attachments.markdownCopied"))
    } catch {
      toast.error(t("attachments.copyFailed"))
    }
  }

  const handleDelete = (attachment) => {
    remove.mutate(
      { bugId, attachmentId: attachment.id },
      {
        onError: (error) =>
          toast.error(error?.response?.data?.detail ?? t("attachments.deleteFailed")),
      },
    )
  }

  return (
    <div className="space-y-2">
      {attachments.length === 0 ? (
        <p className="text-[11px] text-gray-400 dark:text-gray-500">{t("attachments.empty")}</p>
      ) : (
        <ul className="space-y-1.5">
          {attachments.map(attachment => (
            <li
              key={attachment.id}
              className="flex items-center gap-1.5 text-xs bg-gray-50 dark:bg-gray-900 rounded px-2 py-1 border border-gray-200 dark:border-gray-800"
            >
              <Paperclip size={11} className="text-gray-400 dark:text-gray-500 shrink-0" />
              <button
                type="button"
                onClick={() => handleDownload(attachment)}
                disabled={busyAttachmentId === attachment.id}
                className="text-left text-gray-700 dark:text-gray-200 hover:text-primary-600 dark:hover:text-primary-400 min-w-0 flex-1 truncate"
              >
                {attachment.filename}
              </button>
              <span className="text-[10px] text-gray-400 dark:text-gray-500 shrink-0">
                {fmtBytes(attachment.size_bytes)}
              </span>
              <button
                type="button"
                onClick={() => handleCopyMarkdown(attachment)}
                title={t("attachments.copyMarkdown")}
                className="text-[10px] text-gray-400 dark:text-gray-500 hover:text-gray-700 dark:hover:text-gray-200 font-mono shrink-0"
              >
                MD
              </button>
              <button
                type="button"
                onClick={() => handleDelete(attachment)}
                disabled={remove.isPending}
                title={t("attachments.delete")}
                className="text-gray-300 dark:text-gray-600 hover:text-red-500 shrink-0"
              >
                <Trash2 size={11} />
              </button>
            </li>
          ))}
        </ul>
      )}
      <input
        ref={fileInputRef}
        type="file"
        className="hidden"
        onChange={handleFileChange}
      />
      <button
        type="button"
        onClick={() => fileInputRef.current?.click()}
        disabled={upload.isPending}
        className="inline-flex items-center gap-1 text-[11px] text-gray-500 dark:text-gray-400 hover:text-primary-600 dark:hover:text-primary-400"
      >
        <Upload size={11} /> {t("attachments.upload")}
      </button>
    </div>
  )
}
