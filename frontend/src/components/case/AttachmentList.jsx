import { Trash2, Upload, Copy, ExternalLink } from "lucide-react"
import { useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"
import { casesApi } from "../../api/testcases"
import { Button } from "../ui/button"
import { EmptyState } from "../ui/empty-state"

export function AttachmentList({ caseId, attachments }) {
  const qc = useQueryClient()

  const handleUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    await casesApi.uploadAttachment(caseId, file)
    qc.invalidateQueries({ queryKey: ["case", caseId] })
    toast.success(`${file.name} uploaded`)
    e.target.value = ""
  }

  const handleDelete = async (attachmentId) => {
    await casesApi.deleteAttachment(caseId, attachmentId)
    qc.invalidateQueries({ queryKey: ["case", caseId] })
    toast.success("Attachment deleted")
  }

  const copyUrl = (att) => {
    const url = `${window.location.origin}${att.url}`
    navigator.clipboard.writeText(url)
    toast.success("URL copied")
  }

  const copyMarkdown = (att) => {
    const url = `${window.location.origin}${att.url}`
    const md = att.content_type?.startsWith("image/")
      ? `![${att.filename}](${url})`
      : `[${att.filename}](${url})`
    navigator.clipboard.writeText(md)
    toast.success("Markdown copied")
  }

  return (
    <div className="space-y-3">
      <label className="flex items-center gap-2 cursor-pointer w-fit">
        <input type="file" className="hidden" onChange={handleUpload} />
        <Button variant="outline" size="sm" asChild>
          <span><Upload size={13} /> Upload file</span>
        </Button>
      </label>
      {attachments.length === 0 && (
        <EmptyState
          icon={Upload}
          title="No attachments"
          description="Attach screenshots, logs or other supporting files."
          compact
        />
      )}
      <ul className="space-y-1.5">
        {attachments.map(att => (
          <li key={att.id} className="flex items-center gap-2 text-sm bg-gray-50 rounded-lg px-3 py-2">
            <span className="text-xs bg-white dark:bg-gray-900 border px-1.5 py-0.5 rounded text-gray-500 dark:text-gray-400 shrink-0">
              {att.content_type ?? "file"}
            </span>
            <button type="button"
              onClick={() => casesApi.downloadAttachment(caseId, att.id, att.filename)
                .catch(() => toast.error("Download failed"))}
              className="flex items-center gap-1 text-left text-gray-700 dark:text-gray-200 hover:text-primary-600 min-w-0 flex-1 truncate">
              {att.filename}
              <ExternalLink size={11} className="shrink-0" />
            </button>
            <span className="text-xs text-gray-400 dark:text-gray-500 shrink-0">
              {att.size_bytes ? `${Math.round(att.size_bytes / 1024)} KB` : ""}
            </span>
            <button onClick={() => copyUrl(att)} title="Copy URL" className="text-gray-400 dark:text-gray-500 hover:text-gray-700 dark:hover:text-gray-200 shrink-0">
              <Copy size={13} />
            </button>
            <button onClick={() => copyMarkdown(att)} title="Copy as Markdown"
              className="text-xs text-gray-400 dark:text-gray-500 hover:text-gray-700 dark:hover:text-gray-200 font-mono shrink-0">MD</button>
            <button onClick={() => handleDelete(att.id)} title="Delete"
              className="text-gray-300 dark:text-gray-600 hover:text-red-500 shrink-0">
              <Trash2 size={13} />
            </button>
          </li>
        ))}
      </ul>
    </div>
  )
}
