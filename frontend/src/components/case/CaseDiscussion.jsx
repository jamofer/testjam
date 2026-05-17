import { useState } from "react"
import { useTranslation } from "react-i18next"
import { toast } from "sonner"

import { MdEditor, MdViewer } from "../MdEditor"
import { Button } from "../ui/button"
import { DateLabel } from "../ui/date-label"
import { useMe } from "../../hooks/useAuth"
import {
  useAddCaseComment,
  useCaseComments,
  useDeleteCaseComment,
  useUpdateCaseComment,
} from "../../hooks/useSuites"
import { useCaseLive } from "../../hooks/useCaseLive"

export function CaseDiscussion({ caseId, projectId }) {
  const { t } = useTranslation("cases")
  const { data: me } = useMe()
  const { data: comments = [] } = useCaseComments(caseId)
  useCaseLive(caseId, { enabled: !!me && !!caseId })

  const addComment = useAddCaseComment()
  const updateComment = useUpdateCaseComment()
  const removeComment = useDeleteCaseComment()

  const [draft, setDraft] = useState("")
  const [editingId, setEditingId] = useState(null)
  const [editingBody, setEditingBody] = useState("")

  const submit = async (event) => {
    event.preventDefault()
    const body = draft.trim()
    if (!body) return
    try {
      await addComment.mutateAsync({ caseId, body })
      setDraft("")
    } catch (error) {
      toast.error(error?.response?.data?.detail ?? "Failed")
    }
  }

  const saveEdit = async (comment) => {
    try {
      await updateComment.mutateAsync({
        caseId, commentId: comment.id, body: editingBody,
      })
      setEditingId(null)
      setEditingBody("")
    } catch (error) {
      toast.error(error?.response?.data?.detail ?? "Failed")
    }
  }

  const remove = async (comment) => {
    if (!confirm(t("discussion.deleteConfirm"))) return
    try {
      await removeComment.mutateAsync({ caseId, commentId: comment.id })
    } catch (error) {
      toast.error(error?.response?.data?.detail ?? "Failed")
    }
  }

  return (
    <section className="space-y-4">
      {comments.length === 0 && (
        <p className="text-sm text-gray-400 dark:text-gray-500">{t("discussion.empty")}</p>
      )}
      <ul className="space-y-3">
        {comments.map(comment => (
          <li
            key={comment.id}
            className="border rounded-lg px-4 py-3 bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-800"
          >
            <header className="flex justify-between items-center text-xs text-gray-500 dark:text-gray-400 mb-2">
              <span>
                {comment.created_by?.username ?? "?"} · <DateLabel iso={comment.created_at} mode="relative" />
              </span>
              {comment.created_by?.id === me?.id && (
                <span className="flex gap-2">
                  <button onClick={() => { setEditingId(comment.id); setEditingBody(comment.body) }} className="hover:underline">
                    {t("discussion.edit")}
                  </button>
                  <button onClick={() => remove(comment)} className="hover:underline text-red-500">
                    {t("discussion.delete")}
                  </button>
                </span>
              )}
            </header>
            {editingId === comment.id ? (
              <div className="space-y-2">
                <MdEditor value={editingBody} onChange={setEditingBody} height={120} projectId={projectId} />
                <div className="flex gap-2">
                  <Button size="sm" onClick={() => saveEdit(comment)}>{t("discussion.save")}</Button>
                  <Button size="sm" variant="ghost" onClick={() => setEditingId(null)}>{t("discussion.cancel")}</Button>
                </div>
              </div>
            ) : (
              <MdViewer value={comment.body} projectId={projectId} />
            )}
          </li>
        ))}
      </ul>
      <form className="space-y-2" onSubmit={submit}>
        <MdEditor value={draft} onChange={setDraft} height={120} projectId={projectId} />
        <Button type="submit" size="sm" disabled={!draft.trim() || addComment.isPending}>
          {t("discussion.add")}
        </Button>
      </form>
    </section>
  )
}
