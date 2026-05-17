import { useMemo, useState } from "react"
import { Link, useParams } from "react-router-dom"
import { useTranslation } from "react-i18next"
import { Bug as BugIcon, Download, Plus, Trash2 } from "lucide-react"
import { toast } from "sonner"

import { bugsApi } from "../api/bugs"
import { useBugs, useDeleteBug } from "../hooks/useBugs"
import { useProject } from "../hooks/useProjects"
import { useMe } from "../hooks/useAuth"
import { useProjectBugsLive } from "../hooks/useProjectBugsLive"
import { useDebounced } from "../hooks/useDebounced"
import { Button } from "../components/ui/button"
import { Badge } from "../components/ui/badge"
import { SearchInput } from "../components/ui/search-input"
import { PageHeader, PageBody } from "../components/ui/page-header"
import { EmptyState } from "../components/ui/empty-state"
import { LiveIndicator } from "../components/ui/live-indicator"
import { Skeleton, SkeletonList } from "../components/ui/skeleton"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select"
import { DateLabel } from "../components/ui/date-label"
import { EnvironmentBadge } from "../components/environment/EnvironmentBadge"
import { NewBugDialog } from "../components/bug/NewBugDialog"

const STATUS_OPTIONS = ["any", "open", "in_progress", "resolved", "closed", "wont_fix", "not_a_bug"]
const SEVERITY_OPTIONS = ["any", "critical", "high", "medium", "low"]
const SEVERITY_VARIANT = {
  critical: "destructive",
  high: "warning",
  medium: "secondary",
  low: "outline",
}
const STATUS_VARIANT = {
  open: "default",
  in_progress: "warning",
  resolved: "success",
  closed: "secondary",
  wont_fix: "outline",
  not_a_bug: "outline",
}

export function BugsPage() {
  const { t } = useTranslation(["bugs", "nav"])
  const { id: projectId } = useParams()
  const { data: project } = useProject(projectId)
  const { data: me } = useMe()
  const { connected: live } = useProjectBugsLive(projectId, { enabled: !!me })
  const [statusFilter, setStatusFilter] = useState("any")
  const [severityFilter, setSeverityFilter] = useState("any")
  const [search, setSearch] = useState("")
  const debouncedSearch = useDebounced(search, 200)

  const queryParams = useMemo(() => {
    const params = {}
    if (statusFilter !== "any") params.status = statusFilter
    if (severityFilter !== "any") params.severity = severityFilter
    return params
  }, [statusFilter, severityFilter])

  const { data: bugs = [], isLoading } = useBugs(projectId, queryParams)
  const deleteBug = useDeleteBug(projectId)

  const filtered = useMemo(() => {
    const query = debouncedSearch.trim().toLowerCase()
    if (!query) return bugs
    return bugs.filter(bug => bug.title.toLowerCase().includes(query))
  }, [bugs, debouncedSearch])

  const handleDelete = async (bug) => {
    if (!confirm(t("toast.deleted") + "?")) return
    try {
      await deleteBug.mutateAsync(bug.id)
      toast.success(t("toast.deleted"))
    } catch (error) {
      toast.error(error?.response?.data?.detail ?? t("toast.reportFailed"))
    }
  }

  const downloadReport = (format) => {
    const url = `/api/v1${bugsApi.reportUrl(projectId, { format })}`
    window.open(url, "_blank", "noopener,noreferrer")
  }

  return (
    <>
      <PageHeader
        crumbs={[
          { label: t("nav:global.projects"), to: "/projects" },
          { label: project?.name ?? "…", to: `/projects/${projectId}` },
          { label: t("title") },
        ]}
      >
        <div className="max-w-5xl flex items-center justify-between gap-3 flex-wrap">
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-100">{t("title")}</h1>
            <LiveIndicator connected={live} />
          </div>
          <div className="flex items-center gap-2">
            <Select onValueChange={downloadReport}>
              <SelectTrigger className="h-9 w-44">
                <SelectValue placeholder={t("downloadReport")} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="html">{t("reportFormats.html")}</SelectItem>
                <SelectItem value="xlsx">{t("reportFormats.xlsx")}</SelectItem>
              </SelectContent>
            </Select>
            <NewBugDialog projectId={projectId} trigger={(
              <Button size="sm"><Plus size={14} /> {t("new")}</Button>
            )} />
          </div>
        </div>
      </PageHeader>

      <PageBody>
        <div className="max-w-5xl space-y-4">
          <div className="flex flex-wrap items-center gap-2">
            <SearchInput
              value={search}
              onChange={setSearch}
              placeholder={t("filters.search")}
              className="max-w-xs"
            />
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="h-9 w-40">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {STATUS_OPTIONS.map(option => (
                  <SelectItem key={option} value={option}>
                    {option === "any" ? t("filters.any") : t(`statuses.${option}`)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={severityFilter} onValueChange={setSeverityFilter}>
              <SelectTrigger className="h-9 w-40">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {SEVERITY_OPTIONS.map(option => (
                  <SelectItem key={option} value={option}>
                    {option === "any" ? t("filters.any") : t(`severity.${option}`)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {isLoading ? (
            <SkeletonList rows={5} />
          ) : filtered.length === 0 ? (
            <EmptyState
              icon={BugIcon}
              title={t("empty.title")}
              description={t("empty.description")}
            />
          ) : (
            <ul className="space-y-2">
              {filtered.map(bug => (
                <li
                  key={bug.id}
                  className="flex items-center gap-3 border rounded-lg px-4 py-3 bg-white dark:bg-gray-900 hover:bg-gray-50 dark:hover:bg-gray-800"
                >
                  <Link
                    to={`/projects/${projectId}/bugs/${bug.number}`}
                    className="flex-1 min-w-0 flex items-center gap-3"
                  >
                    <span className="font-mono text-xs text-gray-400 dark:text-gray-500 shrink-0">
                      #{bug.number}
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-sm text-gray-800 dark:text-gray-100 truncate">
                        {bug.title}
                      </p>
                      <div className="flex flex-wrap items-center gap-2 mt-0.5 text-xs text-gray-500 dark:text-gray-400">
                        {bug.environment && (
                          <EnvironmentBadge projectId={projectId} slug={bug.environment} />
                        )}
                        {bug.version_name && <span>v{bug.version_name}</span>}
                        {bug.assigned_to && <span>@{bug.assigned_to.username}</span>}
                        <DateLabel value={bug.created_at} />
                      </div>
                    </div>
                  </Link>
                  <Badge variant={SEVERITY_VARIANT[bug.severity] ?? "secondary"}>
                    {t(`severity.${bug.severity}`)}
                  </Badge>
                  <Badge variant={STATUS_VARIANT[bug.status] ?? "secondary"}>
                    {t(`statuses.${bug.status}`)}
                  </Badge>
                  <button
                    onClick={() => handleDelete(bug)}
                    className="text-gray-300 dark:text-gray-600 hover:text-red-500"
                    title={t("actions.delete")}
                  >
                    <Trash2 size={14} />
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </PageBody>
    </>
  )
}
