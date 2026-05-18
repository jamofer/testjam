import { useRef, useState } from "react"
import { useTranslation } from "react-i18next"
import { Trash2, Upload, ExternalLink } from "lucide-react"
import { toast } from "sonner"
import {
  useVersionAttachments,
  useUploadVersionAttachment,
  useDeleteVersionAttachment,
} from "../../hooks/useVersions"
import { versionsApi } from "../../api/versions"
import { Button } from "../ui/button"
import { EmptyState } from "../ui/empty-state"
import { SkeletonList } from "../ui/skeleton"

export function VersionAttachmentList({ versionId }) {
  const { t } = useTranslation("versions")
  const { data: attachments = [], isLoading } = useVersionAttachments(versionId)
  const uploadAttachment = useUploadVersionAttachment(versionId)
  const deleteAttachment = useDeleteVersionAttachment(versionId)
  const fileInputRef = useRef(null)
  const [dragOver, setDragOver] = useState(false)

  const upload = async (file) => {
    try {
      await uploadAttachment.mutateAsync(file)
      toast.success(t("attachments.uploaded", { name: file.name }))
    } catch {
      toast.error(t("attachments.uploadFailed"))
    }
  }

  const handlePickerChange = async (event) => {
    const file = event.target.files?.[0]
    if (file) await upload(file)
    event.target.value = ""
  }

  const handleDrop = async (event) => {
    event.preventDefault()
    setDragOver(false)
    const file = event.dataTransfer?.files?.[0]
    if (file) await upload(file)
  }

  const handleDelete = async (attachment) => {
    try {
      await deleteAttachment.mutateAsync(attachment.id)
      toast.success(t("attachments.deleted"))
    } catch {
      toast.error(t("attachments.deleteFailed"))
    }
  }

  const handleDownload = (attachment) => {
    versionsApi
      .downloadAttachment(versionId, attachment.id, attachment.filename)
      .catch(() => toast.error(t("attachments.downloadFailed")))
  }

  if (isLoading) return <SkeletonList count={2} />

  return (
    <div className="space-y-3">
      <div
        onDragOver={(event) => { event.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-lg p-4 text-center text-sm transition-colors ${
          dragOver
            ? "border-primary-500 bg-primary-50 dark:bg-primary-950"
            : "border-gray-200 dark:border-gray-700 text-gray-500 dark:text-gray-400"
        }`}
      >
        <p>{t("attachments.dropHint")}</p>
        <Button variant="outline" size="sm" className="mt-2"
          onClick={() => fileInputRef.current?.click()}
          disabled={uploadAttachment.isPending}
        >
          <Upload size={13} /> {t("attachments.upload")}
        </Button>
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          onChange={handlePickerChange}
        />
      </div>

      {attachments.length === 0 ? (
        <EmptyState
          icon={Upload}
          title={t("attachments.emptyTitle")}
          description={t("attachments.emptyDescription")}
          compact
        />
      ) : (
        <ul className="space-y-1.5">
          {attachments.map((attachment) => (
            <li key={attachment.id} className="flex items-center gap-2 text-sm bg-gray-50 dark:bg-gray-900 border rounded-lg px-3 py-2">
              <span className="text-xs bg-white dark:bg-gray-950 border px-1.5 py-0.5 rounded text-gray-500 dark:text-gray-400 shrink-0">
                {attachment.content_type ?? "file"}
              </span>
              <button
                type="button"
                onClick={() => handleDownload(attachment)}
                className="flex items-center gap-1 text-left text-gray-700 dark:text-gray-200 hover:text-primary-600 min-w-0 flex-1 truncate"
              >
                {attachment.filename}
                <ExternalLink size={11} className="shrink-0" />
              </button>
              <span className="text-xs text-gray-400 dark:text-gray-500 shrink-0">
                {attachment.size_bytes ? `${Math.round(attachment.size_bytes / 1024)} KB` : ""}
              </span>
              {attachment.uploaded_by?.username && (
                <span className="text-xs text-gray-400 dark:text-gray-500 shrink-0">
                  {attachment.uploaded_by.username}
                </span>
              )}
              <button
                onClick={() => handleDelete(attachment)}
                title={t("attachments.delete")}
                className="text-gray-300 dark:text-gray-600 hover:text-red-500 shrink-0"
              >
                <Trash2 size={13} />
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
