import { useState, useMemo } from "react"
import { useParams, Link, useSearchParams } from "react-router-dom"
import { useTranslation } from "react-i18next"
import { PlayCircle, CheckCircle2, XCircle, MinusCircle, Plus, Clock, Search, User, Download, Trash2 } from "lucide-react"
import { toast } from "sonner"
import { useExecutions, useDeleteExecution } from "../hooks/useExecutions"
import { useProject } from "../hooks/useProjects"
import { useVersions } from "../hooks/useVersions"
import { useMe } from "../hooks/useAuth"
import { useDebounced } from "../hooks/useDebounced"
import { useProjectExecutionsLive } from "../hooks/useProjectExecutionsLive"
import { executionsApi } from "../api/executions"
import { Button } from "../components/ui/button"
import { Badge } from "../components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select"
import { SearchInput } from "../components/ui/search-input"
import { PageHeader, PageBody } from "../components/ui/page-header"
import { DateLabel } from "../components/ui/date-label"
import { fmtDuration } from "../lib/format"
import { EmptyState } from "../components/ui/empty-state"
import { LiveIndicator } from "../components/ui/live-indicator"
import { SkeletonList } from "../components/ui/skeleton"
import { EnvironmentBadge } from "../components/environment/EnvironmentBadge"
import { ImportExecutionDialog } from "../components/execution/ImportExecutionDialog"

const statusIcon = {
  completed:  <CheckCircle2 size={15} className="text-green-500" />,
  in_progress: <PlayCircle size={15} className="text-blue-500" />,
  aborted:    <XCircle size={15} className="text-red-500" />,
  pending:    <MinusCircle size={15} className="text-gray-400 dark:text-gray-500" />,
}

const typeBadge = {
  manual:    "secondary",
  automatic: "default",
}

const STATUS_FILTERS = ["all", "pending", "in_progress", "completed", "aborted"]

const VERSION_FILTER_ALL = "all"

export function ExecutionsPage() {
  const { t } = useTranslation(["executions", "nav"])
  const { id: projectId } = useParams()
  const [searchParams, setSearchParams] = useSearchParams()
  const [statusFilter, setStatusFilter] = useState("all")
  const versionFilter = searchParams.get("version_id") ?? VERSION_FILTER_ALL
  const updateVersionFilter = (value) => {
    const next = new URLSearchParams(searchParams)
    if (value === VERSION_FILTER_ALL) next.delete("version_id")
    else next.set("version_id", value)
    setSearchParams(next, { replace: true })
  }
  const queryParams = {
    ...(statusFilter !== "all" ? { status: statusFilter } : {}),
    ...(versionFilter !== VERSION_FILTER_ALL ? { version_id: versionFilter } : {}),
  }
  const {
    data,
    isLoading,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useExecutions(projectId, Object.keys(queryParams).length > 0 ? queryParams : undefined)
  const { data: project } = useProject(projectId)
  const { data: versions = [] } = useVersions(projectId)
  const { data: me } = useMe()
  const { connected: live } = useProjectExecutionsLive(projectId, { enabled: !!me })
  const deleteExecution = useDeleteExecution(projectId)
  const [search, setSearch] = useState("")
  const [mineOnly, setMineOnly] = useState(false)
  const debouncedSearch = useDebounced(search, 150)

  const handleDelete = async (execution) => {
    if (!confirm(t("deleteConfirm", { title: execution.title }))) return
    try {
      await deleteExecution.mutateAsync(execution.id)
      toast.success(t("deleted"))
    } catch {
      toast.error(t("deleteFailed"))
    }
  }

  const executions = useMemo(() => (data?.pages ?? []).flat(), [data])
  const hasFiltersActive =
    statusFilter !== "all" ||
    versionFilter !== VERSION_FILTER_ALL ||
    debouncedSearch.trim() !== "" ||
    mineOnly

  const filtered = useMemo(() => {
    const query = debouncedSearch.trim().toLowerCase()
    return executions.filter(execution => {
      if (mineOnly && execution.assigned_to?.id !== me?.id) return false
      if (query && !execution.title.toLowerCase().includes(query)) return false
      return true
    })
  }, [executions, debouncedSearch, mineOnly, me?.id])

  return (
    <>
      <PageHeader crumbs={[
        { label: t("nav:global.projects"), to: "/projects" },
        { label: project?.name ?? "…", to: `/projects/${projectId}` },
        { label: t("title") },
      ]}>
        <div className="max-w-2xl xl:max-w-4xl 2xl:max-w-5xl space-y-3">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-100 flex items-center gap-2">
              {t("title")}
              <LiveIndicator connected={live} />
            </h1>
            <div className="flex items-center gap-2 self-start sm:self-auto">
              <ImportExecutionDialog projectId={projectId} />
              <Link to={`/projects/${projectId}/executions/new`}>
                <Button size="sm"><Plus size={14} /> {t("newExecution")}</Button>
              </Link>
            </div>
          </div>
          {!isLoading && (executions.length > 0 || hasFiltersActive) && (
            <div className="flex flex-wrap gap-2 items-center">
              <SearchInput value={search} onChange={setSearch} placeholder={t("searchPlaceholder")} className="flex-1 min-w-[180px]" />
              <div className="flex gap-1">
                {STATUS_FILTERS.map(status => (
                  <Button
                    key={status}
                    size="sm"
                    variant={statusFilter === status ? "default" : "outline"}
                    onClick={() => setStatusFilter(status)}
                  >
                    {t(`filters.${status}`)}
                  </Button>
                ))}
              </div>
              {versions.length > 0 && (
                <Select value={versionFilter} onValueChange={updateVersionFilter}>
                  <SelectTrigger className="h-8 text-xs w-44" aria-label={t("filters.version")}>
                    <SelectValue placeholder={t("filters.allVersions")} />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value={VERSION_FILTER_ALL}>{t("filters.allVersions")}</SelectItem>
                    {versions.map(version => (
                      <SelectItem key={version.id} value={String(version.id)}>
                        {version.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
              {me && (
                <Button
                  size="sm"
                  variant={mineOnly ? "default" : "outline"}
                  onClick={() => setMineOnly(value => !value)}
                  title={t("mineOnlyTitle")}
                >
                  <User size={13} /> {t("mineOnly")}
                </Button>
              )}
            </div>
          )}
        </div>
      </PageHeader>

      <PageBody>
      <div className="max-w-2xl xl:max-w-4xl 2xl:max-w-5xl space-y-6">
      {isLoading && <SkeletonList count={3} />}

      <ul className="space-y-2">
        {filtered.map(execution => (
          <li key={execution.id} className="bg-white dark:bg-gray-900 border rounded-lg px-4 py-3 shadow-sm">
            <div className="flex items-center justify-between gap-2">
              <Link to={`/executions/${execution.id}/run`}
                className="font-medium text-gray-800 dark:text-gray-100 hover:underline flex items-center gap-2 min-w-0">
                {statusIcon[execution.status]}
                <span className="truncate">{execution.title}</span>
              </Link>
              <div className="flex items-center gap-2 shrink-0">
                <Badge variant={typeBadge[execution.type]}>{execution.type}</Badge>
                <button
                  onClick={() => executionsApi.exportHtml(execution.id, execution.title)}
                  className="text-gray-400 dark:text-gray-500 hover:text-gray-700 dark:hover:text-gray-200 p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-800"
                  title={t("downloadHtml")}
                >
                  <Download size={13} />
                </button>
                <button
                  onClick={() => handleDelete(execution)}
                  className="text-gray-400 dark:text-gray-500 hover:text-red-600 p-1 rounded hover:bg-red-50"
                  title={t("deleteTitle")}
                  disabled={deleteExecution.isPending}
                >
                  <Trash2 size={13} />
                </button>
              </div>
            </div>
            <div className="flex flex-wrap gap-x-3 gap-y-0.5 mt-1 text-xs text-gray-400 dark:text-gray-500">
              {execution.version_name && <span>v{execution.version_name}</span>}
              {execution.environment && (
                <EnvironmentBadge projectId={projectId} slug={execution.environment} />
              )}
              {(execution.token_name || execution.created_by || execution.triggered_by) && (
                <span>{execution.token_name
                  ? t("via", { token: execution.token_name })
                  : t("by", { name: execution.created_by?.username ?? execution.triggered_by })}
                </span>
              )}
              {execution.assigned_to && (
                <span className="flex items-center gap-1 text-gray-500 dark:text-gray-400">
                  <User size={10} /> {execution.assigned_to.username}
                </span>
              )}
              {(execution.started_at || execution.created_at) && (
                <span className="flex items-center gap-1">
                  <Clock size={10} /> <DateLabel iso={execution.started_at ?? execution.created_at} />
                </span>
              )}
              {execution.finished_at && (execution.started_at || execution.created_at) && (
                <span>· {fmtDuration(new Date(execution.finished_at) - new Date(execution.started_at ?? execution.created_at))}</span>
              )}
            </div>
            <div className="flex gap-3 mt-1.5 text-xs">
              <span className="text-green-600">✓ {execution.summary?.passed ?? 0}</span>
              <span className="text-red-500">✗ {execution.summary?.failed ?? 0}</span>
              <span className="text-yellow-600">⚠ {execution.summary?.blocked ?? 0}</span>
              <span className="text-gray-400 dark:text-gray-500">— {execution.summary?.not_run ?? 0}</span>
            </div>
          </li>
        ))}
      </ul>
      {!isLoading && executions.length === 0 && !hasFiltersActive && (
        <EmptyState
          icon={PlayCircle}
          title={t("empty.title")}
          description={t("empty.description")}
          action={
            <Link to={`/projects/${projectId}/executions/new`}>
              <Button size="sm"><Plus size={14} /> {t("newExecution")}</Button>
            </Link>
          }
        />
      )}
      {!isLoading && filtered.length === 0 && hasFiltersActive && (
        <EmptyState
          icon={Search}
          title={t("noMatches.title")}
          description={t("noMatches.description")}
          compact
        />
      )}
      {hasNextPage && (
        <div className="flex justify-center">
          <Button variant="outline" size="sm" onClick={() => fetchNextPage()} disabled={isFetchingNextPage}>
            {isFetchingNextPage ? t("loadingMore") : t("loadMore")}
          </Button>
        </div>
      )}
      </div>
      </PageBody>
    </>
  )
}
