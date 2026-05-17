import { useEffect, useMemo, useState } from "react"
import { useNavigate, useParams } from "react-router-dom"
import { useTranslation } from "react-i18next"
import { toast } from "sonner"

import { bugsApi } from "../api/bugs"
import {
  useAddBugComment,
  useBug,
  useBugComments,
  useBugHistory,
  useChangeBugStatus,
  useDeleteBug,
  useDeleteBugComment,
  useUpdateBugComment,
} from "../hooks/useBugs"
import { useProject } from "../hooks/useProjects"
import { useMe } from "../hooks/useAuth"
import { useBugLive } from "../hooks/useBugLive"
import { PageBody, PageHeader } from "../components/ui/page-header"
import { Button } from "../components/ui/button"
import { Badge } from "../components/ui/badge"
import { Skeleton } from "../components/ui/skeleton"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs"
import { Textarea } from "../components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select"
import { DateLabel } from "../components/ui/date-label"
import { LiveIndicator } from "../components/ui/live-indicator"
import { EnvironmentBadge } from "../components/environment/EnvironmentBadge"

const STATUSES = ["open", "in_progress", "resolved", "closed", "wont_fix", "not_a_bug"]

export function BugDetailPage() {
  const { t } = useTranslation(["bugs", "nav"])
  const { bugId: directBugId, projectId, number } = useParams()
  const navigate = useNavigate()
  const { data: me } = useMe()

  const [resolvedId, setResolvedId] = useState(() =>
    directBugId ? Number(directBugId) : null,
  )

  useEffect(() => {
    if (directBugId) {
      setResolvedId(Number(directBugId))
      return undefined
    }
    if (!projectId || !number) return undefined
    let cancelled = false
    bugsApi
      .byNumber(projectId, number)
      .then(bug => { if (!cancelled) setResolvedId(bug.id) })
      .catch(() => navigate(`/projects/${projectId}/bugs`))
    return () => { cancelled = true }
  }, [directBugId, projectId, number, navigate])

  const bugId = resolvedId
  const { data: bug, isLoading } = useBug(bugId)
  const { data: project } = useProject(bug?.project_id)
  const { connected: live } = useBugLive(bugId, { enabled: !!me && !!bugId })
  const { data: comments = [] } = useBugComments(bugId)
  const { data: history = [] } = useBugHistory(bugId)
  const bugProjectId = bug?.project_id

  const changeStatus = useChangeBugStatus(bugProjectId)
  const deleteBug = useDeleteBug(bugProjectId)
  const addComment = useAddBugComment()
  const updateComment = useUpdateBugComment()
  const removeComment = useDeleteBugComment()

  const [commentDraft, setCommentDraft] = useState("")
  const [editingComment, setEditingComment] = useState(null)
  const [editingBody, setEditingBody] = useState("")
  const sortedHistory = useMemo(() => [...history], [history])

  if (isLoading || !bug) {
    return (
      <PageBody>
        <div className="max-w-3xl space-y-4">
          <Skeleton className="h-7 w-1/3" />
          <Skeleton className="h-40 w-full" />
        </div>
      </PageBody>
    )
  }

  const handleStatusChange = async (status) => {
    if (status === bug.status) return
    try {
      await changeStatus.mutateAsync({ id: bug.id, status })
      toast.success(t("toast.statusChanged"))
    } catch (error) {
      toast.error(error?.response?.data?.detail ?? "Could not change status")
    }
  }

  const handleDelete = async () => {
    if (!confirm(t("toast.deleted") + "?")) return
    try {
      await deleteBug.mutateAsync(bug.id)
      toast.success(t("toast.deleted"))
      navigate(`/projects/${bug.project_id}/bugs`)
    } catch (error) {
      toast.error(error?.response?.data?.detail ?? "Could not delete")
    }
  }

  const handleAddComment = async (event) => {
    event.preventDefault()
    const body = commentDraft.trim()
    if (!body) return
    try {
      await addComment.mutateAsync({ id: bug.id, body })
      setCommentDraft("")
      toast.success(t("toast.commentAdded"))
    } catch (error) {
      toast.error(error?.response?.data?.detail ?? "Failed")
    }
  }

  const beginEditComment = (comment) => {
    setEditingComment(comment.id)
    setEditingBody(comment.body)
  }

  const saveEditComment = async (comment) => {
    try {
      await updateComment.mutateAsync({ bugId: bug.id, commentId: comment.id, body: editingBody })
      setEditingComment(null)
      setEditingBody("")
    } catch (error) {
      toast.error(error?.response?.data?.detail ?? "Failed")
    }
  }

  const deleteCommentRow = async (comment) => {
    if (!confirm(t("actions.delete") + "?")) return
    try {
      await removeComment.mutateAsync({ bugId: bug.id, commentId: comment.id })
    } catch (error) {
      toast.error(error?.response?.data?.detail ?? "Failed")
    }
  }

  return (
    <>
      <PageHeader
        crumbs={[
          { label: t("nav:global.projects"), to: "/projects" },
          { label: project?.name ?? "…", to: `/projects/${bug.project_id}` },
          { label: t("title"), to: `/projects/${bug.project_id}/bugs` },
          { label: `#${bug.number}` },
        ]}
      >
        <div className="max-w-3xl flex flex-col gap-3">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-mono text-gray-400 dark:text-gray-500">#{bug.number}</span>
            <h1 className="text-xl font-bold text-gray-800 dark:text-gray-100 flex-1 break-words">{bug.title}</h1>
            <LiveIndicator connected={live} />
          </div>
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <Badge variant="warning">{t(`severity.${bug.severity}`)}</Badge>
            <Select value={bug.status} onValueChange={handleStatusChange}>
              <SelectTrigger className="h-7 w-40 text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {STATUSES.map(option => (
                  <SelectItem key={option} value={option}>{t(`statuses.${option}`)}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            {bug.environment && (
              <EnvironmentBadge projectId={bug.project_id} slug={bug.environment} />
            )}
            {bug.version_name && (
              <span className="text-gray-500 dark:text-gray-400">v{bug.version_name}</span>
            )}
            {bug.assigned_to && (
              <span className="text-gray-500 dark:text-gray-400">@{bug.assigned_to.username}</span>
            )}
            <Button size="sm" variant="ghost" onClick={handleDelete}>{t("actions.delete")}</Button>
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400">
            {t("history.by", { user: bug.created_by?.username ?? "?" })} · <DateLabel value={bug.created_at} />
          </div>
        </div>
      </PageHeader>

      <PageBody>
        <div className="max-w-3xl">
          <Tabs defaultValue="description">
            <TabsList>
              <TabsTrigger value="description">{t("tabs.description")}</TabsTrigger>
              <TabsTrigger value="comments">{t("tabs.comments")} ({comments.length})</TabsTrigger>
              <TabsTrigger value="history">{t("tabs.history")} ({history.length})</TabsTrigger>
            </TabsList>

            <TabsContent value="description">
              <div className="prose dark:prose-invert max-w-none border rounded-lg p-4 bg-white dark:bg-gray-900">
                {bug.description ? (
                  <pre className="whitespace-pre-wrap text-sm">{bug.description}</pre>
                ) : (
                  <p className="text-sm text-gray-400">—</p>
                )}
              </div>
            </TabsContent>

            <TabsContent value="comments">
              <div className="space-y-3">
                {comments.length === 0 && (
                  <p className="text-sm text-gray-400">{t("comments.empty")}</p>
                )}
                <ul className="space-y-3">
                  {comments.map(comment => (
                    <li key={comment.id} className="border rounded-lg px-4 py-3 bg-white dark:bg-gray-900">
                      <div className="flex justify-between items-center text-xs text-gray-500 dark:text-gray-400 mb-1">
                        <span>{comment.created_by?.username ?? "?"} · <DateLabel value={comment.created_at} /></span>
                        {comment.created_by?.id === me?.id && (
                          <span className="flex gap-2">
                            <button onClick={() => beginEditComment(comment)} className="hover:underline">{t("actions.edit")}</button>
                            <button onClick={() => deleteCommentRow(comment)} className="hover:underline text-red-500">{t("actions.delete")}</button>
                          </span>
                        )}
                      </div>
                      {editingComment === comment.id ? (
                        <div className="space-y-2">
                          <Textarea value={editingBody} onChange={event => setEditingBody(event.target.value)} rows={3} />
                          <div className="flex gap-2">
                            <Button size="sm" onClick={() => saveEditComment(comment)}>{t("actions.save")}</Button>
                            <Button size="sm" variant="ghost" onClick={() => setEditingComment(null)}>{t("actions.cancel")}</Button>
                          </div>
                        </div>
                      ) : (
                        <pre className="whitespace-pre-wrap text-sm">{comment.body}</pre>
                      )}
                    </li>
                  ))}
                </ul>
                <form className="space-y-2" onSubmit={handleAddComment}>
                  <Textarea
                    value={commentDraft}
                    onChange={event => setCommentDraft(event.target.value)}
                    placeholder={t("comments.placeholder")}
                    rows={3}
                  />
                  <Button type="submit" size="sm" disabled={!commentDraft.trim() || addComment.isPending}>
                    {t("actions.addComment")}
                  </Button>
                </form>
              </div>
            </TabsContent>

            <TabsContent value="history">
              {sortedHistory.length === 0 ? (
                <p className="text-sm text-gray-400">{t("history.empty")}</p>
              ) : (
                <ul className="space-y-2">
                  {sortedHistory.map(entry => (
                    <li key={entry.id} className="border rounded-lg px-4 py-3 bg-white dark:bg-gray-900 text-sm">
                      <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400">
                        <span>{entry.changed_by?.username ?? "?"} · <DateLabel value={entry.changed_at} /></span>
                      </div>
                      <p>
                        {entry.from_status === null
                          ? `${t("history.createdLabel")}: ${t(`statuses.${entry.to_status}`)}`
                          : `${t("history.transitionLabel")}: ${t(`statuses.${entry.from_status}`)} → ${t(`statuses.${entry.to_status}`)}`}
                      </p>
                      {entry.note && <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{entry.note}</p>}
                    </li>
                  ))}
                </ul>
              )}
            </TabsContent>
          </Tabs>
        </div>
      </PageBody>
    </>
  )
}
