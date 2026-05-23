import { useRef, useState } from "react"
import { useTranslation } from "react-i18next"
import { Paperclip, Trash2, Upload } from "lucide-react"
import { toast } from "sonner"

import {
  useBugAttachments,
  useDeleteBugAttachment,
  useUploadBugAttachment,
} from "../../hooks/useBugs"
import { bugsApi } from "../../api/bugs"
import { Button } from "../ui/button"
import { DateLabel } from "../ui/date-label"
import { fmtBytes } from "../../lib/format"

export function BugAttachmentsPanel({ bugId, canWrite = true }) {
  const { t } = useTranslation("bugs")
  const { data: attachments = [], isLoading } = useBugAttachments(bugId)
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
    <section className="space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
          {t("tabs.attachments")} ({attachments.length})
        </h2>
        {canWrite && (
          <>
            <input
              ref={fileInputRef}
              type="file"
              className="hidden"
              onChange={handleFileChange}
            />
            <Button
              size="sm"
              variant="outline"
              onClick={() => fileInputRef.current?.click()}
              disabled={upload.isPending}
            >
              <Upload size={14} className="mr-1" /> {t("attachments.upload")}
            </Button>
          </>
        )}
      </div>

      {isLoading ? (
        <p className="text-sm text-gray-400 dark:text-gray-500">{t("attachments.loading")}</p>
      ) : attachments.length === 0 ? (
        <p className="text-sm text-gray-400 dark:text-gray-500">{t("attachments.empty")}</p>
      ) : (
        <ul className="space-y-2">
          {attachments.map(attachment => (
            <li
              key={attachment.id}
              className="border rounded-lg px-3 py-2 bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-800 flex items-center gap-3"
            >
              <Paperclip size={14} className="text-gray-400 dark:text-gray-500 shrink-0" />
              <button
                type="button"
                onClick={() => handleDownload(attachment)}
                disabled={busyAttachmentId === attachment.id}
                className="text-sm font-medium text-primary-600 dark:text-primary-400 hover:underline truncate"
              >
                {attachment.filename}
              </button>
              <span className="text-xs text-gray-400 dark:text-gray-500 shrink-0">
                {fmtBytes(attachment.size_bytes)}
              </span>
              <span className="text-xs text-gray-400 dark:text-gray-500 shrink-0 ml-auto">
                {attachment.uploaded_by?.username ?? "?"} ·{" "}
                <DateLabel iso={attachment.uploaded_at} mode="relative" />
              </span>
              {canWrite && (
                <button
                  type="button"
                  onClick={() => handleDelete(attachment)}
                  disabled={remove.isPending}
                  className="text-gray-400 dark:text-gray-500 hover:text-red-500"
                  title={t("attachments.delete")}
                >
                  <Trash2 size={14} />
                </button>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
