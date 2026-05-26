import { useEffect, useMemo, useState } from "react"
import { Link, useParams, useSearchParams } from "react-router-dom"
import { useTranslation } from "react-i18next"
import { Bug as BugIcon, Download, Link2, Plus, Trash2 } from "lucide-react"
import { toast } from "sonner"

import { bugsApi } from "../api/bugs"
import { useBugs, useDeleteBug } from "../hooks/useBugs"
import { useProject } from "../hooks/useProjects"
import { useVersions } from "../hooks/useVersions"
import { useCustomFields } from "../hooks/useCustomFields"
import { useMe } from "../hooks/useAuth"
import { useProjectRole } from "../hooks/useProjectRole"
import { useProjectBugsLive } from "../hooks/useProjectBugsLive"
import { useDebounced } from "../hooks/useDebounced"
import { Button } from "../components/ui/button"
import { Badge } from "../components/ui/badge"
import { ConfirmDialog } from "../components/ui/confirm-dialog"
import { SearchInput } from "../components/ui/search-input"
import { PageHeader, PageBody } from "../components/ui/page-header"
import { EmptyState } from "../components/ui/empty-state"
import { LiveIndicator } from "../components/ui/live-indicator"
import { Skeleton, SkeletonList } from "../components/ui/skeleton"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select"
import { DateLabel } from "../components/ui/date-label"
import { EnvironmentBadge } from "../components/environment/EnvironmentBadge"
import { NewBugDialog } from "../components/bug/NewBugDialog"
import { CustomFieldFilter } from "../components/customField/CustomFieldFilter"
import { CustomFieldColumnToggle } from "../components/customField/CustomFieldColumnToggle"
import { CustomFieldValue } from "../components/customField/CustomFieldInput"
import { useCustomFieldColumns } from "../hooks/useCustomFieldColumns"
import { PublicReportDialog } from "../components/share/PublicReportDialog"
import { SEVERITY_VARIANT, STATUS_VARIANT } from "../lib/bugConfig"

const STATUS_OPTIONS = ["any", "open", "in_progress", "resolved", "closed", "wont_fix", "not_a_bug"]
const SEVERITY_OPTIONS = ["any", "critical", "high", "medium", "low"]
const ANY = "any"

export function BugsPage() {
  const { t } = useTranslation(["bugs", "nav"])
  const { id: projectId } = useParams()
  const { data: project } = useProject(projectId)
  const { data: me } = useMe()
  const { canDelete } = useProjectRole(projectId)
  const { connected: live } = useProjectBugsLive(projectId, { enabled: !!me })
  const [searchParams, setSearchParams] = useSearchParams()
  const statusFilter = searchParams.get("status") || ANY
  const severityFilter = searchParams.get("severity") || ANY
  const versionFilter = searchParams.get("version_id") || ANY
  const sortBy = searchParams.get("sort_by") || "number"
  const cfFieldKey = searchParams.get("cf_key") || ANY
  const cfFieldValue = searchParams.get("cf_value") || ANY
  const urlSearch = searchParams.get("search") || ""
  const [search, setSearch] = useState(urlSearch)
  const debouncedSearch = useDebounced(search, 200)

  const replaceParam = (mutate) => {
    const next = new URLSearchParams(searchParams)
    mutate(next)
    setSearchParams(next, { replace: true })
  }
  const setSingleParam = (key, value) => {
    replaceParam(next => {
      if (!value || value === ANY) next.delete(key)
      else next.set(key, value)
    })
  }
  const setStatusFilter = (value) => setSingleParam("status", value)
  const setSeverityFilter = (value) => setSingleParam("severity", value)
  const setVersionFilter = (value) => setSingleParam("version_id", value)
  const setSortBy = (value) => setSingleParam("sort_by", value === "number" ? null : value)
  const setCfFieldKey = (value) => {
    replaceParam(next => {
      if (!value || value === ANY) { next.delete("cf_key"); next.delete("cf_value") }
      else { next.set("cf_key", value); next.delete("cf_value") }
    })
  }
  const setCfFieldValue = (value) => setSingleParam("cf_value", value)

  useEffect(() => {
    const trimmed = debouncedSearch.trim()
    if (trimmed === (searchParams.get("search") || "")) return
    setSingleParam("search", trimmed)
  }, [debouncedSearch])  // eslint-disable-line react-hooks/exhaustive-deps
  const { data: versions = [] } = useVersions(projectId)
  const { data: customFieldDefs = [] } = useCustomFields(projectId, "bug")
  const selectedCfDef = customFieldDefs.find(definition => definition.key === cfFieldKey)
  const { visibleKeys: visibleCfColumns, toggle: toggleCfColumn } = useCustomFieldColumns("bug", projectId)
  const visibleCfDefs = useMemo(
    () => customFieldDefs.filter(definition => visibleCfColumns.includes(definition.key)),
    [customFieldDefs, visibleCfColumns],
  )

  const queryParams = useMemo(() => {
    const params = {}
    if (statusFilter !== "any") params.status = statusFilter
    if (severityFilter !== "any") params.severity = severityFilter
    if (versionFilter !== "any") params.version_id = versionFilter
    if (cfFieldKey !== "any") {
      params.cf_key = cfFieldKey
      if (cfFieldValue !== "any") params.cf_value = cfFieldValue
    }
    const query = debouncedSearch.trim()
    if (query) params.search = query
    if (sortBy !== "number") params.sort_by = sortBy
    return params
  }, [statusFilter, severityFilter, versionFilter, cfFieldKey, cfFieldValue, debouncedSearch, sortBy])

  const { data: bugs = [], isLoading } = useBugs(projectId, queryParams)
  const deleteBug = useDeleteBug(projectId)
  const filtered = bugs
  const hasActiveFilters =
    statusFilter !== "any" ||
    severityFilter !== "any" ||
    versionFilter !== "any" ||
    cfFieldKey !== "any" ||
    debouncedSearch.trim().length > 0

  const [bugPendingDelete, setBugPendingDelete] = useState(null)

  const confirmDelete = async () => {
    if (!bugPendingDelete) return
    try {
      await deleteBug.mutateAsync(bugPendingDelete.id)
      toast.success(t("toast.deleted"))
    } catch (error) {
      toast.error(error?.response?.data?.detail ?? t("toast.reportFailed"))
    } finally {
      setBugPendingDelete(null)
    }
  }

  const downloadHtml = async () => {
    try {
      await bugsApi.exportHtml(projectId, project?.name)
    } catch (error) {
      toast.error(error?.response?.data?.detail ?? t("toast.reportFailed"))
    }
  }

  const downloadReleaseNotes = async () => {
    try {
      await bugsApi.releaseNotesHtml(projectId, project?.name)
    } catch (error) {
      toast.error(error?.response?.data?.detail ?? t("toast.reportFailed"))
    }
  }

  const downloadPdf = async () => {
    try {
      const { exportBugsPdf } = await import("../lib/exportPdf")
      exportBugsPdf(filtered, project?.name, { username: me?.username, timezone: me?.timezone })
    } catch (error) {
      toast.error(error?.response?.data?.detail ?? t("toast.reportFailed"))
    }
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
            <Button variant="outline" size="sm" onClick={downloadHtml}>
              <Download size={13} /> {t("downloadHtml")}
            </Button>
            <Button variant="outline" size="sm" onClick={downloadPdf}>
              <Download size={13} /> {t("downloadPdf")}
            </Button>
            <Button variant="outline" size="sm" onClick={downloadReleaseNotes}>
              <Download size={13} /> {t("downloadReleaseNotes")}
            </Button>
            <PublicReportDialog
              projectId={projectId}
              defaultKind="bug_report"
              versionId={versionFilter !== "any" ? versionFilter : null}
              trigger={(
                <Button variant="outline" size="sm">
                  <Link2 size={13} /> {t("publicReports:share")}
                </Button>
              )}
            />
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
              <SelectTrigger className="h-9 w-44" aria-label={t("filters.statusLabel")}>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {STATUS_OPTIONS.map(option => (
                  <SelectItem key={option} value={option}>
                    {option === "any" ? t("filters.anyStatus") : t(`statuses.${option}`)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={severityFilter} onValueChange={setSeverityFilter}>
              <SelectTrigger className="h-9 w-44" aria-label={t("filters.severityLabel")}>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {SEVERITY_OPTIONS.map(option => (
                  <SelectItem key={option} value={option}>
                    {option === "any" ? t("filters.anySeverity") : t(`severity.${option}`)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={versionFilter} onValueChange={setVersionFilter}>
              <SelectTrigger className="h-9 w-44" aria-label={t("filters.versionLabel")}>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="any">{t("filters.anyVersion")}</SelectItem>
                {versions.map(version => (
                  <SelectItem key={version.id} value={String(version.id)}>
                    {version.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={sortBy} onValueChange={setSortBy}>
              <SelectTrigger className="h-9 w-44" aria-label={t("filters.sortLabel")}>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="number">{t("filters.sortNewest")}</SelectItem>
                <SelectItem value="severity">{t("filters.sortSeverity")}</SelectItem>
                <SelectItem value="created_at">{t("filters.sortCreated")}</SelectItem>
              </SelectContent>
            </Select>
            {customFieldDefs.length > 0 && (
              <CustomFieldFilter
                definitions={customFieldDefs}
                fieldKey={cfFieldKey}
                fieldValue={cfFieldValue}
                onFieldKeyChange={setCfFieldKey}
                onFieldValueChange={setCfFieldValue}
                selectedDefinition={selectedCfDef}
              />
            )}
            <div className="ml-auto">
              <CustomFieldColumnToggle
                definitions={customFieldDefs}
                visibleKeys={visibleCfColumns}
                onToggle={toggleCfColumn}
              />
            </div>
          </div>

          {isLoading ? (
            <SkeletonList rows={5} />
          ) : filtered.length === 0 ? (
            <EmptyState
              icon={BugIcon}
              title={hasActiveFilters ? t("empty.titleNoMatches") : t("empty.title")}
              description={hasActiveFilters ? t("empty.descriptionNoMatches") : t("empty.description")}
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
                        {bug.duplicate_of_number && (
                          <Badge variant="outline" className="font-mono">
                            {t("duplicateOf", { number: bug.duplicate_of_number })}
                          </Badge>
                        )}
                        {bug.assigned_to && <span>@{bug.assigned_to.username}</span>}
                        {bug.created_by && <span>{bug.created_by.username}</span>}
                        <DateLabel iso={bug.created_at} />
                        {bug.updated_at && bug.updated_at !== bug.created_at && (
                          <span className="italic">
                            {t("list.updated")} <DateLabel iso={bug.updated_at} mode="relative" />
                          </span>
                        )}
                      </div>
                    </div>
                  </Link>
                  {visibleCfDefs.length > 0 && (
                    <div className="hidden md:flex flex-col items-end gap-0.5 text-[11px] text-gray-500 dark:text-gray-400 max-w-[12rem]">
                      {visibleCfDefs.map(definition => (
                        <div key={definition.id} className="flex items-center gap-1 truncate">
                          <span className="text-gray-400 dark:text-gray-500">{definition.label}:</span>
                          <CustomFieldValue
                            definition={definition}
                            value={(bug.custom_fields ?? {})[definition.key]}
                          />
                        </div>
                      ))}
                    </div>
                  )}
                  <Badge variant={SEVERITY_VARIANT[bug.severity] ?? "secondary"}>
                    {t(`severity.${bug.severity}`)}
                  </Badge>
                  <Badge variant={STATUS_VARIANT[bug.status] ?? "secondary"}>
                    {t(`statuses.${bug.status}`)}
                  </Badge>
                  {canDelete && (
                    <button
                      onClick={() => setBugPendingDelete(bug)}
                      className="text-gray-300 dark:text-gray-600 hover:text-red-500"
                      title={t("actions.delete")}
                    >
                      <Trash2 size={14} />
                    </button>
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>
      </PageBody>

      <ConfirmDialog
        open={bugPendingDelete !== null}
        onOpenChange={(open) => { if (!open) setBugPendingDelete(null) }}
        title={t("delete.bugTitle", { number: bugPendingDelete?.number ?? "" })}
        description={t("delete.bugDescription")}
        confirmLabel={t("actions.delete")}
        destructive
        busy={deleteBug.isPending}
        onConfirm={confirmDelete}
      />
    </>
  )
}
