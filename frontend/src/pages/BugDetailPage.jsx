import { useEffect, useMemo, useState } from "react"
import { Link, useNavigate, useParams } from "react-router-dom"
import { useTranslation } from "react-i18next"
import {
  Bug as BugIcon,
  CalendarPlus,
  CheckCircle2,
  Clock,
  ExternalLink,
  Pencil,
  Plus,
  Tag,
  Trash2,
  User as UserIcon,
} from "lucide-react"
import { toast } from "sonner"

import { bugsApi } from "../api/bugs"
import {
  useAddBugComment,
  useBug,
  useBugComments,
  useBugContext,
  useBugHistory,
  useBugLinks,
  useChangeBugStatus,
  useDeleteBug,
  useDeleteBugComment,
  useDeleteBugLink,
  useUpdateBug,
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
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select"
import { DateLabel } from "../components/ui/date-label"
import { LiveIndicator } from "../components/ui/live-indicator"
import { ContextPanel } from "../components/ui/context-panel"
import { EnvironmentBadge } from "../components/environment/EnvironmentBadge"
import { AddBugLinkDialog } from "../components/bug/AddBugLinkDialog"
import { MdEditor, MdViewer } from "../components/MdEditor"
import { SEVERITY_VARIANT, STATUS_VARIANT, STATUSES } from "../lib/bugConfig"

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
  const { data: linkContext } = useBugContext(bugId)
  const { data: links = [] } = useBugLinks(bugId)
  const bugProjectId = bug?.project_id

  const changeStatus = useChangeBugStatus(bugProjectId)
  const deleteBug = useDeleteBug(bugProjectId)
  const updateBug = useUpdateBug(bugProjectId)
  const addComment = useAddBugComment()
  const updateComment = useUpdateBugComment()
  const removeComment = useDeleteBugComment()
  const removeLink = useDeleteBugLink()

  const [commentDraft, setCommentDraft] = useState("")
  const [editingComment, setEditingComment] = useState(null)
  const [editingBody, setEditingBody] = useState("")
  const [editingDescription, setEditingDescription] = useState(false)
  const [descriptionDraft, setDescriptionDraft] = useState("")
  const sortedHistory = useMemo(() => [...history], [history])

  const contextSections = useMemo(() => {
    if (!bug) return []
    return buildContextSections({
      bug,
      links,
      linkContext,
      onDeleteLink: (linkId) => removeLink.mutateAsync({ bugId: bug.id, linkId }),
      addLinkDialog: (
        <AddBugLinkDialog
          bugId={bug.id}
          projectId={bug.project_id}
          trigger={(
            <button
              type="button"
              className="text-[11px] text-primary-600 dark:text-primary-400 hover:underline inline-flex items-center gap-1"
            >
              <Plus size={11} /> {t("links.add")}
            </button>
          )}
        />
      ),
      t,
    })
  }, [bug, links, linkContext, removeLink, t])

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

  const beginEditDescription = () => {
    setDescriptionDraft(bug.description ?? "")
    setEditingDescription(true)
  }

  const saveDescription = async () => {
    try {
      await updateBug.mutateAsync({
        id: bug.id,
        data: { description: descriptionDraft.trim() || null },
      })
      setEditingDescription(false)
      toast.success(t("toast.updated"))
    } catch (error) {
      toast.error(error?.response?.data?.detail ?? "Failed")
    }
  }

  const handleAddComment = async (event) => {
    event.preventDefault()
    const body = (commentDraft ?? "").trim()
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

  const hasMeaningfulUpdate = bug.updated_by
    && bug.updated_at
    && bug.updated_at !== bug.created_at
    && bug.updated_by?.id !== bug.created_by?.id

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
        <div className="max-w-2xl xl:max-w-4xl 2xl:max-w-5xl flex flex-col gap-3 md:flex-row md:items-start md:justify-between md:gap-4">
          <div className="min-w-0">
            <h1 className="text-xl font-bold text-gray-800 dark:text-gray-100 break-words md:truncate flex items-center gap-2 flex-wrap">
              <span className="font-mono text-gray-400 dark:text-gray-500">#{bug.number}</span>
              {bug.title}
              <LiveIndicator connected={live} />
            </h1>
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-1.5 text-sm text-gray-500 dark:text-gray-400">
              <Badge variant={SEVERITY_VARIANT[bug.severity] ?? "secondary"}>
                {t(`severity.${bug.severity}`)}
              </Badge>
              <Badge variant={STATUS_VARIANT[bug.status] ?? "secondary"}>
                {t(`statuses.${bug.status}`)}
              </Badge>
              {bug.environment && (
                <EnvironmentBadge projectId={bug.project_id} slug={bug.environment} />
              )}
              {bug.assigned_to && (
                <span className="flex items-center gap-1">
                  <UserIcon size={12} /> {bug.assigned_to.username}
                </span>
              )}
            </div>
            <div className="flex flex-wrap items-center gap-x-3 gap-y-0.5 mt-1 text-xs text-gray-400 dark:text-gray-500">
              {bug.created_by && (
                <span className="flex items-center gap-1">
                  <UserIcon size={11} />
                  {t("header.openedBy", { user: bug.created_by.full_name || bug.created_by.username })}
                  {" · "}
                  <DateLabel iso={bug.created_at} mode="relative" />
                </span>
              )}
              {hasMeaningfulUpdate && (
                <span className="flex items-center gap-1">
                  <Pencil size={11} />
                  {t("header.editedBy", { user: bug.updated_by.full_name || bug.updated_by.username })}
                  {" · "}
                  <DateLabel iso={bug.updated_at} mode="relative" />
                </span>
              )}
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2 md:shrink-0">
            <Select value={bug.status} onValueChange={handleStatusChange}>
              <SelectTrigger className="h-9 w-auto min-w-[10rem] text-sm">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {STATUSES.map(option => (
                  <SelectItem key={option} value={option}>
                    {t(`statuses.${option}`)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleDelete}
              className="text-gray-400 dark:text-gray-500 hover:text-red-500"
              title={t("actions.delete")}
            >
              <Trash2 size={14} />
            </Button>
          </div>
        </div>
      </PageHeader>

      <PageBody>
        <div className="flex gap-6">
          <div className="flex-1 min-w-0 max-w-2xl xl:max-w-4xl 2xl:max-w-5xl space-y-4">
            <Tabs defaultValue="discussion">
              <TabsList>
                <TabsTrigger value="discussion">{t("tabs.discussion")}</TabsTrigger>
                <TabsTrigger value="history">{t("tabs.history")} ({history.length})</TabsTrigger>
              </TabsList>

              <TabsContent value="discussion" className="space-y-6">
                <section className="border rounded-lg p-4 bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-800">
                  <div className="flex items-center justify-between mb-2">
                    <h2 className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
                      {t("tabs.description")}
                    </h2>
                    {!editingDescription && (
                      <button
                        type="button"
                        onClick={beginEditDescription}
                        className="text-xs text-gray-400 dark:text-gray-500 hover:text-primary-600 dark:hover:text-primary-400 inline-flex items-center gap-1"
                      >
                        <Pencil size={11} /> {t("actions.edit")}
                      </button>
                    )}
                  </div>
                  {editingDescription ? (
                    <div className="space-y-2">
                      <MdEditor
                        value={descriptionDraft}
                        onChange={setDescriptionDraft}
                        height={200}
                      />
                      <div className="flex gap-2">
                        <Button size="sm" onClick={saveDescription} disabled={updateBug.isPending}>
                          {t("actions.save")}
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => setEditingDescription(false)}
                        >
                          {t("actions.cancel")}
                        </Button>
                      </div>
                    </div>
                  ) : bug.description ? (
                    <MdViewer value={bug.description} />
                  ) : (
                    <button
                      type="button"
                      onClick={beginEditDescription}
                      className="text-sm text-gray-400 dark:text-gray-500 italic hover:text-primary-600 dark:hover:text-primary-400 text-left"
                    >
                      {t("description.empty")}
                    </button>
                  )}
                </section>

                <section className="space-y-3">
                  <h2 className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
                    {t("tabs.comments")} ({comments.length})
                  </h2>
                  {comments.length === 0 && (
                    <p className="text-sm text-gray-400 dark:text-gray-500">{t("comments.empty")}</p>
                  )}
                  <ul className="space-y-3">
                    {comments.map(comment => (
                      <li
                        key={comment.id}
                        className="border rounded-lg px-4 py-3 bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-800"
                      >
                        <div className="flex justify-between items-center text-xs text-gray-500 dark:text-gray-400 mb-2">
                          <span>
                            {comment.created_by?.username ?? "?"} · <DateLabel iso={comment.created_at} mode="relative" />
                          </span>
                          {comment.created_by?.id === me?.id && (
                            <span className="flex gap-2">
                              <button onClick={() => beginEditComment(comment)} className="hover:underline">
                                {t("actions.edit")}
                              </button>
                              <button
                                onClick={() => deleteCommentRow(comment)}
                                className="hover:underline text-red-500"
                              >
                                {t("actions.delete")}
                              </button>
                            </span>
                          )}
                        </div>
                        {editingComment === comment.id ? (
                          <div className="space-y-2">
                            <MdEditor value={editingBody} onChange={setEditingBody} height={120} />
                            <div className="flex gap-2">
                              <Button size="sm" onClick={() => saveEditComment(comment)}>
                                {t("actions.save")}
                              </Button>
                              <Button size="sm" variant="ghost" onClick={() => setEditingComment(null)}>
                                {t("actions.cancel")}
                              </Button>
                            </div>
                          </div>
                        ) : (
                          <MdViewer value={comment.body} />
                        )}
                      </li>
                    ))}
                  </ul>
                  <form className="space-y-2" onSubmit={handleAddComment}>
                    <MdEditor value={commentDraft} onChange={setCommentDraft} height={120} />
                    <Button
                      type="submit"
                      size="sm"
                      disabled={!(commentDraft ?? "").trim() || addComment.isPending}
                    >
                      {t("actions.addComment")}
                    </Button>
                  </form>
                </section>
              </TabsContent>

              <TabsContent value="history">
                {sortedHistory.length === 0 ? (
                  <p className="text-sm text-gray-400 dark:text-gray-500">{t("history.empty")}</p>
                ) : (
                  <ul className="space-y-2">
                    {sortedHistory.map(entry => (
                      <li
                        key={entry.id}
                        className="border rounded-lg px-4 py-3 bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-800 text-sm"
                      >
                        <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400">
                          <span>{entry.changed_by?.username ?? "?"} · <DateLabel iso={entry.changed_at} mode="relative" /></span>
                        </div>
                        <p className="text-gray-700 dark:text-gray-200">
                          {entry.from_status === null
                            ? `${t("history.createdLabel")}: ${t(`statuses.${entry.to_status}`)}`
                            : `${t("history.transitionLabel")}: ${t(`statuses.${entry.from_status}`)} → ${t(`statuses.${entry.to_status}`)}`}
                        </p>
                        {entry.note && (
                          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{entry.note}</p>
                        )}
                      </li>
                    ))}
                  </ul>
                )}
              </TabsContent>
            </Tabs>
          </div>
          <ContextPanel sections={contextSections} />
        </div>
      </PageBody>
    </>
  )
}

function buildContextSections({ bug, links, linkContext, onDeleteLink, addLinkDialog, t }) {
  const sections = []

  sections.push({
    title: t("context.about"),
    rows: [
      {
        label: t("context.severity"),
        value: (
          <Badge variant={SEVERITY_VARIANT[bug.severity] ?? "secondary"}>
            {t(`severity.${bug.severity}`)}
          </Badge>
        ),
      },
      {
        label: t("context.status"),
        value: (
          <Badge variant={STATUS_VARIANT[bug.status] ?? "secondary"}>
            {t(`statuses.${bug.status}`)}
          </Badge>
        ),
      },
      {
        label: t("context.assignee"),
        icon: UserIcon,
        value: bug.assigned_to ? `@${bug.assigned_to.username}` : null,
      },
      {
        label: t("context.createdBy"),
        icon: UserIcon,
        value: bug.created_by?.username ?? null,
      },
      {
        label: t("context.created"),
        icon: CalendarPlus,
        value: <DateLabel iso={bug.created_at} mode="relative" />,
      },
      {
        label: t("context.updatedBy"),
        icon: UserIcon,
        value: bug.updated_by?.username ?? null,
      },
      {
        label: t("context.updated"),
        icon: Clock,
        value: bug.updated_at && bug.updated_at !== bug.created_at
          ? <DateLabel iso={bug.updated_at} mode="relative" />
          : null,
      },
      {
        label: t("context.resolved"),
        icon: CheckCircle2,
        value: bug.resolved_at ? <DateLabel iso={bug.resolved_at} mode="relative" /> : null,
      },
    ],
  })

  const primary = buildPrimaryOccurrence(bug, linkContext)
  if (primary) {
    sections.push(occurrenceSection({
      occurrence: primary,
      bug,
      title: occurrenceTitle(t("linkedOccurrence.origin"), primary),
      t,
    }))
  }

  links
    .filter(link => link.execution_id != null)
    .forEach(link => {
      const occurrence = occurrenceFromLink(link)
      sections.push(occurrenceSection({
        occurrence,
        bug,
        title: occurrenceTitle(t("linkedOccurrence.alsoIn"), occurrence),
        onDelete: () => onDeleteLink(link.id),
        t,
      }))
    })

  const otherLinks = links.filter(link => link.execution_id == null)
  if (otherLinks.length > 0 || bug.external_ticket_url) {
    sections.push({
      title: t("linkedOccurrence.otherLinks"),
      body: (
        <OtherLinksBody
          bug={bug}
          links={otherLinks}
          onDeleteLink={onDeleteLink}
          t={t}
        />
      ),
    })
  }

  sections.push({
    title: t("linkedOccurrence.addSection"),
    defaultOpen: false,
    body: <div className="text-xs">{addLinkDialog}</div>,
  })

  sections.push({
    title: t("context.tags"),
    body: (bug.tags ?? []).length > 0 ? (
      <div className="flex flex-wrap gap-1">
        {bug.tags.map(tag => (
          <span
            key={tag}
            className="text-[11px] px-1.5 py-0.5 rounded bg-blue-50 text-blue-600 border border-blue-200 dark:bg-blue-950 dark:text-blue-300 dark:border-blue-800 inline-flex items-center gap-1"
          >
            <Tag size={9} /> {tag}
          </span>
        ))}
      </div>
    ) : (
      <p className="text-[11px] text-gray-400 dark:text-gray-500">{t("context.noTags")}</p>
    ),
  })

  return sections
}

function buildPrimaryOccurrence(bug, linkContext) {
  if (!linkContext?.execution && !linkContext?.case && !bug.version_id && !bug.environment) {
    return null
  }
  return {
    executionId: linkContext?.execution?.id ?? bug.execution_id ?? null,
    executionTitle: linkContext?.execution?.title ?? null,
    suitePath: linkContext?.suite_path ?? [],
    caseNode: linkContext?.case ?? null,
    stepNode: null,
    versionId: linkContext?.version_id ?? bug.version_id ?? null,
    versionName: linkContext?.version_name ?? bug.version_name ?? null,
    environment: linkContext?.environment ?? bug.environment ?? null,
  }
}

function occurrenceFromLink(link) {
  return {
    executionId: link.execution_id,
    executionTitle: link.execution_title,
    suitePath: link.suite_path ?? [],
    caseNode: link.test_case_id
      ? { id: link.test_case_id, name: link.test_case_name ?? `#${link.test_case_id}` }
      : null,
    stepNode: link.test_step_id
      ? { id: link.test_step_id, action: link.test_step_action ?? `#${link.test_step_id}` }
      : null,
    versionId: link.execution_version_id,
    versionName: link.execution_version_name,
    environment: link.execution_environment,
    label: link.label,
  }
}

function occurrenceTitle(prefix, occurrence) {
  if (occurrence.executionId == null) return prefix
  const head = occurrence.executionTitle
    ? `${occurrence.executionTitle} (#${occurrence.executionId})`
    : `#${occurrence.executionId}`
  return `${prefix} · ${head}`
}

function occurrenceSection({ occurrence, bug, title, onDelete, t }) {
  const rows = []
  rows.push({
    label: t("linkedOccurrence.run"),
    value: occurrence.executionId
      ? (
        <Link
          to={`/executions/${occurrence.executionId}/run`}
          className="text-primary-600 dark:text-primary-400 hover:underline break-words"
        >
          {occurrence.executionTitle ?? `#${occurrence.executionId}`}
        </Link>
      )
      : <EmptyValue t={t} />,
  })
  rows.push({
    label: t("linkedOccurrence.path"),
    value: renderPath(occurrence.suitePath, occurrence.caseNode) ?? <EmptyValue t={t} />,
  })
  rows.push({
    label: t("linkedOccurrence.step"),
    value: occurrence.stepNode
      ? <span className="break-words">{occurrence.stepNode.action}</span>
      : <EmptyValue t={t} />,
  })
  rows.push({
    label: t("linkedOccurrence.version"),
    value: occurrence.versionId && occurrence.versionName
      ? (
        <Link
          to={`/projects/${bug.project_id}/versions/${occurrence.versionId}`}
          className="text-primary-600 dark:text-primary-400 hover:underline"
        >
          {occurrence.versionName}
        </Link>
      )
      : <EmptyValue t={t} />,
  })
  rows.push({
    label: t("linkedOccurrence.environment"),
    value: occurrence.environment
      ? <EnvironmentBadge projectId={bug.project_id} slug={occurrence.environment} />
      : <EmptyValue t={t} />,
  })
  if (occurrence.label) {
    rows.push({
      label: t("linkedOccurrence.note"),
      value: <span className="italic text-gray-500 dark:text-gray-400">{occurrence.label}</span>,
    })
  }
  return {
    title,
    body: <OccurrenceRows rows={rows} onDelete={onDelete} t={t} />,
  }
}

function OccurrenceRows({ rows, onDelete, t }) {
  return (
    <div className="space-y-1">
      <dl className="grid grid-cols-[auto_1fr] gap-x-2 gap-y-1 text-xs">
        {rows.map(row => (
          <div key={row.label} className="contents">
            <dt className="text-gray-500 dark:text-gray-400 pr-1">{row.label}</dt>
            <dd className="text-gray-800 dark:text-gray-100 min-w-0 break-words">{row.value}</dd>
          </div>
        ))}
      </dl>
      {onDelete && (
        <button
          type="button"
          onClick={onDelete}
          className="text-[11px] text-gray-400 dark:text-gray-500 hover:text-red-500 inline-flex items-center gap-1 pt-1"
        >
          <Trash2 size={11} /> {t("linkedOccurrence.delete")}
        </button>
      )}
    </div>
  )
}

function EmptyValue({ t }) {
  return <span className="text-gray-300 dark:text-gray-600 italic">{t("linkedOccurrence.notSet")}</span>
}

function renderPath(suitePath, caseNode) {
  const parts = []
  suitePath.forEach((suite, index) => {
    if (index > 0) parts.push(<span key={`sep-${index}`} className="text-gray-400 dark:text-gray-600 mx-1">›</span>)
    parts.push(
      <span key={`suite-${suite.id}`} className="text-gray-700 dark:text-gray-200">{suite.name}</span>,
    )
  })
  if (caseNode) {
    if (suitePath.length > 0) parts.push(<span key="sep-case" className="text-gray-400 dark:text-gray-600 mx-1">›</span>)
    parts.push(
      <Link
        key={`case-${caseNode.id}`}
        to={`/cases/${caseNode.id}`}
        className="text-primary-600 dark:text-primary-400 hover:underline"
      >
        {caseNode.name}
      </Link>,
    )
  }
  if (parts.length === 0) return null
  return <span className="break-words leading-snug">{parts}</span>
}

function OtherLinksBody({ bug, links, onDeleteLink, t }) {
  return (
    <ul className="space-y-1.5 text-xs">
      {bug.external_ticket_url && (
        <li className="flex items-start gap-2">
          <ExternalLink size={11} className="text-gray-400 dark:text-gray-500 mt-0.5 shrink-0" />
          <a
            href={bug.external_ticket_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary-600 dark:text-primary-400 hover:underline break-all min-w-0"
          >
            {bug.external_ticket_url}
          </a>
        </li>
      )}
      {links.map(link => (
        <li key={link.id} className="flex items-start gap-2 group">
          {link.target_bug_id ? (
            <BugIcon size={11} className="text-gray-400 dark:text-gray-500 mt-0.5 shrink-0" />
          ) : (
            <ExternalLink size={11} className="text-gray-400 dark:text-gray-500 mt-0.5 shrink-0" />
          )}
          <div className="flex-1 min-w-0">
            <OtherLinkContent link={link} bug={bug} />
          </div>
          <button
            type="button"
            onClick={() => onDeleteLink(link.id)}
            className="text-gray-300 dark:text-gray-600 hover:text-red-500 opacity-0 group-hover:opacity-100 shrink-0"
            title={t("actions.delete")}
          >
            <Trash2 size={11} />
          </button>
        </li>
      ))}
    </ul>
  )
}

function OtherLinkContent({ link, bug }) {
  if (link.target_bug_id && link.target_bug_number != null) {
    return (
      <Link
        to={`/projects/${bug.project_id}/bugs/${link.target_bug_number}`}
        className="text-primary-600 dark:text-primary-400 hover:underline break-words"
      >
        {link.label || `#${link.target_bug_number} ${link.target_bug_title ?? ""}`.trim()}
      </Link>
    )
  }
  if (link.url) {
    return (
      <a
        href={link.url}
        target="_blank"
        rel="noopener noreferrer"
        className="text-primary-600 dark:text-primary-400 hover:underline break-all"
      >
        {link.label || link.url}
      </a>
    )
  }
  return <span className="text-gray-500 dark:text-gray-400">{link.label}</span>
}
