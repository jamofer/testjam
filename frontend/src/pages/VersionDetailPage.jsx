import { useState, useEffect, useMemo } from "react"
import { useParams, Link } from "react-router-dom"
import { useTranslation } from "react-i18next"
import { useQuery } from "@tanstack/react-query"
import { CheckCircle2, Archive, Circle, Save, Clock, PlayCircle, XCircle, MinusCircle, Tag } from "lucide-react"
import { useProject } from "../hooks/useProjects"
import { useVersion, useUpdateVersion } from "../hooks/useVersions"
import { executionsApi } from "../api/executions"
import { PageHeader, PageBody } from "../components/ui/page-header"
import { Badge } from "../components/ui/badge"
import { Button } from "../components/ui/button"
import { Input } from "../components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select"
import { MdEditor } from "../components/MdEditor"
import { EmptyState } from "../components/ui/empty-state"
import { SkeletonList } from "../components/ui/skeleton"
import { DateLabel } from "../components/ui/date-label"
import { toast } from "sonner"

const VERSION_STATUS_STYLE = {
  active:   { icon: Circle,       badge: "default"     },
  released: { icon: CheckCircle2, badge: "success"     },
  archived: { icon: Archive,      badge: "secondary"   },
}

const VERSION_STATUSES = ["active", "released", "archived"]

const EXECUTION_STATUS_ICON = {
  completed:   <CheckCircle2 size={14} className="text-green-500" />,
  in_progress: <PlayCircle size={14} className="text-blue-500" />,
  aborted:     <XCircle size={14} className="text-red-500" />,
  pending:     <MinusCircle size={14} className="text-gray-400 dark:text-gray-500" />,
}

function aggregateStats(executions) {
  const totals = { runs: executions.length, passed: 0, failed: 0, blocked: 0, not_run: 0 }
  for (const ex of executions) {
    totals.passed   += ex.summary?.passed   ?? 0
    totals.failed   += ex.summary?.failed   ?? 0
    totals.blocked  += ex.summary?.blocked  ?? 0
    totals.not_run  += ex.summary?.not_run  ?? 0
  }
  const totalResults = totals.passed + totals.failed + totals.blocked + totals.not_run
  const passRate = totalResults > 0 ? Math.round((totals.passed / totalResults) * 100) : null
  return { ...totals, totalResults, passRate }
}

export function VersionDetailPage() {
  const { t } = useTranslation(["versions", "nav", "executions"])
  const { id: projectId, versionId } = useParams()
  const { data: project } = useProject(projectId)
  const { data: version } = useVersion(versionId)
  const updateVersion = useUpdateVersion(projectId)

  const { data: executions = [], isLoading: executionsLoading } = useQuery({
    queryKey: ["executions", projectId, { version_id: versionId }],
    queryFn: () => executionsApi.list(projectId, { version_id: versionId, limit: 200 }),
    enabled: !!projectId && !!versionId,
  })

  const [draftName, setDraftName] = useState("")
  const [draftDescription, setDraftDescription] = useState("")
  const [draftReleaseDate, setDraftReleaseDate] = useState("")

  useEffect(() => {
    if (version) {
      setDraftName(version.name)
      setDraftDescription(version.description ?? "")
      setDraftReleaseDate(version.release_date ?? "")
    }
  }, [version])

  const stats = useMemo(() => aggregateStats(executions), [executions])

  if (!version) {
    return (
      <PageBody>
        <SkeletonList count={3} />
      </PageBody>
    )
  }

  const style = VERSION_STATUS_STYLE[version.status] ?? VERSION_STATUS_STYLE.active
  const Icon = style.icon
  const nameDirty = draftName.trim() !== "" && draftName !== version.name
  const descriptionDirty = draftDescription !== (version.description ?? "")
  const releaseDateDirty = (draftReleaseDate || "") !== (version.release_date ?? "")
  const dirty = nameDirty || descriptionDirty || releaseDateDirty

  const handleSave = async () => {
    const data = {}
    if (nameDirty) data.name = draftName.trim()
    if (descriptionDirty) data.description = draftDescription || null
    if (releaseDateDirty) data.release_date = draftReleaseDate || null
    if (Object.keys(data).length === 0) return
    await updateVersion.mutateAsync({ id: version.id, data })
    toast.success(t("detail.saved"))
  }

  return (
    <>
      <PageHeader crumbs={[
        { label: t("nav:global.projects"), to: "/projects" },
        { label: project?.name ?? "…", to: `/projects/${projectId}` },
        { label: t("title"), to: `/projects/${projectId}/versions` },
        { label: version.name },
      ]}>
        <div className="max-w-2xl xl:max-w-4xl 2xl:max-w-5xl">
          <div className="flex items-center gap-3 flex-wrap">
            <Icon size={20} className="text-gray-700 dark:text-gray-200" />
            <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-100">{version.name}</h1>
            <Badge variant={style.badge}>{t(`statuses.${version.status}`)}</Badge>
            {version.vcs_tag && (
              <span className="text-xs font-mono bg-gray-100 dark:bg-gray-800 border px-1.5 py-0.5 rounded text-gray-600 dark:text-gray-300">
                <Tag size={11} className="inline mr-1" />{version.vcs_tag}
              </span>
            )}
            <span className="text-xs text-gray-400 dark:text-gray-500 flex items-center gap-1">
              <Clock size={11} /> <DateLabel iso={version.created_at} />
            </span>
            {version.released_at && (
              <span className="text-xs text-green-600 dark:text-green-400 flex items-center gap-1">
                <CheckCircle2 size={11} /> {t("detail.releasedOn")} <DateLabel iso={version.released_at} />
              </span>
            )}
          </div>
        </div>
      </PageHeader>

      <PageBody>
        <div className="max-w-2xl xl:max-w-4xl 2xl:max-w-5xl space-y-6">
          <section className="grid grid-cols-2 sm:grid-cols-5 gap-3">
            <StatCard label={t("detail.statRuns")}        value={stats.runs} />
            <StatCard label={t("detail.statPassRate")}    value={stats.passRate === null ? "—" : `${stats.passRate}%`} accent="text-green-600 dark:text-green-400" />
            <StatCard label={t("detail.statPassed")}      value={stats.passed}  accent="text-green-600 dark:text-green-400" />
            <StatCard label={t("detail.statFailed")}      value={stats.failed}  accent="text-red-500" />
            <StatCard label={t("detail.statBlocked")}     value={stats.blocked} accent="text-yellow-600 dark:text-yellow-400" />
          </section>

          <section className="space-y-2">
            <div className="flex items-center justify-between gap-2 flex-wrap">
              <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-200 uppercase tracking-wide">{t("detail.metadata")}</h2>
              <div className="flex items-center gap-2">
                <Select
                  value={version.status}
                  onValueChange={status => updateVersion.mutate({ id: version.id, data: { status } })}
                >
                  <SelectTrigger className="h-8 w-36 text-xs" title={t("changeStatus")}>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {VERSION_STATUSES.map(status => (
                      <SelectItem key={status} value={status}>{t(`statuses.${status}`)}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Button size="sm" disabled={!dirty || updateVersion.isPending} onClick={handleSave}>
                  <Save size={13} /> {t("detail.save")}
                </Button>
              </div>
            </div>
            <div className="space-y-3">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div className="sm:col-span-2">
                  <label className="text-xs text-gray-500 dark:text-gray-400 mb-1 block">{t("detail.nameLabel")}</label>
                  <Input value={draftName} onChange={event => setDraftName(event.target.value)} />
                </div>
                <div>
                  <label className="text-xs text-gray-500 dark:text-gray-400 mb-1 block">{t("detail.releaseDateLabel")}</label>
                  <Input type="date" value={draftReleaseDate ?? ""} onChange={event => setDraftReleaseDate(event.target.value)} />
                </div>
              </div>
              <div>
                <label className="text-xs text-gray-500 dark:text-gray-400 mb-1 block">{t("detail.descriptionLabel")}</label>
                <MdEditor value={draftDescription} onChange={value => setDraftDescription(value ?? "")} height={220} />
              </div>
            </div>
          </section>

          <section className="space-y-2">
            <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-200 uppercase tracking-wide">{t("detail.executions")}</h2>
            {executionsLoading ? (
              <SkeletonList count={3} />
            ) : executions.length === 0 ? (
              <EmptyState
                icon={PlayCircle}
                title={t("detail.noExecutionsTitle")}
                description={t("detail.noExecutionsDescription")}
                compact
              />
            ) : (
              <ul className="space-y-2">
                {executions.map(execution => (
                  <li key={execution.id} className="bg-white dark:bg-gray-900 border rounded-lg px-4 py-2.5 shadow-sm">
                    <div className="flex items-center justify-between gap-2">
                      <Link
                        to={`/executions/${execution.id}/run`}
                        className="font-medium text-sm text-gray-800 dark:text-gray-100 hover:underline flex items-center gap-2 min-w-0"
                      >
                        {EXECUTION_STATUS_ICON[execution.status]}
                        <span className="truncate">{execution.title}</span>
                      </Link>
                      <div className="flex gap-3 text-xs shrink-0">
                        <span className="text-green-600">✓ {execution.summary?.passed ?? 0}</span>
                        <span className="text-red-500">✗ {execution.summary?.failed ?? 0}</span>
                        <span className="text-yellow-600">⚠ {execution.summary?.blocked ?? 0}</span>
                        <span className="text-gray-400 dark:text-gray-500">— {execution.summary?.not_run ?? 0}</span>
                      </div>
                    </div>
                    <div className="text-xs text-gray-400 dark:text-gray-500 mt-0.5 flex items-center gap-1">
                      <Clock size={10} /> <DateLabel iso={execution.started_at ?? execution.created_at} />
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>
      </PageBody>
    </>
  )
}

function StatCard({ label, value, accent }) {
  return (
    <div className="bg-white dark:bg-gray-900 border rounded-lg px-3 py-2">
      <div className="text-[11px] uppercase tracking-wide text-gray-400 dark:text-gray-500">{label}</div>
      <div className={`text-lg font-semibold ${accent ?? "text-gray-800 dark:text-gray-100"}`}>{value}</div>
    </div>
  )
}
