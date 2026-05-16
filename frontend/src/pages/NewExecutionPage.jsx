import { useState } from "react"
import { useParams, useNavigate } from "react-router-dom"
import { useTranslation } from "react-i18next"
import { useCreateExecution } from "../hooks/useExecutions"
import { useVersions } from "../hooks/useVersions"
import { useMembers } from "../hooks/useMembers"
import { useProject } from "../hooks/useProjects"
import { useQuery } from "@tanstack/react-query"
import { plansApi } from "../api/testplans"
import { Button } from "../components/ui/button"
import { Input } from "../components/ui/input"
import { Label } from "../components/ui/label"
import { MdEditor } from "../components/MdEditor"
import { PageBody, PageHeader } from "../components/ui/page-header"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select"
import { CasePicker } from "../components/ui/case-picker"
import { toast } from "sonner"

export function NewExecutionPage() {
  const { t } = useTranslation(["executions", "nav"])
  const { id: projectId } = useParams()
  const navigate = useNavigate()
  const createExecution = useCreateExecution(projectId)
  const { data: project } = useProject(projectId)
  const { data: versions = [] } = useVersions(projectId)
  const { data: members = [] } = useMembers(projectId)

  const [title, setTitle] = useState("")
  const [description, setDescription] = useState("")
  const [type, setType] = useState("manual")
  const [versionInput, setVersionInput] = useState("")
  const [environment, setEnvironment] = useState("")
  const [triggeredBy, setTriggeredBy] = useState("")
  const [assigneeId, setAssigneeId] = useState("")
  const [source, setSource] = useState("cases")
  const [planId, setPlanId] = useState("")
  const [selectedCases, setSelectedCases] = useState([])

  const { data: plans = [] } = useQuery({
    queryKey: ["plans", projectId],
    queryFn: () => plansApi.list(projectId),
    enabled: !!projectId,
  })

  const toggleCase = (id) =>
    setSelectedCases(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id])

  const handleSubmit = async (event) => {
    event.preventDefault()
    if (!title.trim()) return toast.error(t("new.titleRequired"))

    const selectedPlan = source === "plan" ? plans.find(p => String(p.id) === planId) : null
    if (source === "plan" && !selectedPlan) return toast.error(t("new.selectPlanFailure"))

    const trimmedVersion = versionInput.trim()
    const matchedVersion = trimmedVersion
      ? versions.find(version => version.name.toLowerCase() === trimmedVersion.toLowerCase())
      : null
    const payload = {
      title: title.trim(),
      description,
      type,
      version_id: matchedVersion ? matchedVersion.id : undefined,
      version: !matchedVersion && trimmedVersion ? trimmedVersion : undefined,
      environment: environment || undefined,
      triggered_by: type === "automatic" ? triggeredBy || undefined : undefined,
      assigned_to_id: assigneeId ? parseInt(assigneeId) : undefined,
      test_case_ids: source === "cases" ? selectedCases : (selectedPlan?.test_case_ids ?? []),
    }

    try {
      const execution = await createExecution.mutateAsync(payload)
      toast.success(t("new.created"))
      navigate(`/executions/${execution.id}/run`)
    } catch {
      toast.error(t("new.createFailed"))
    }
  }

  return (
    <>
      <PageHeader crumbs={[
        { label: t("nav:global.projects"), to: "/projects" },
        { label: project?.name ?? "…", to: `/projects/${projectId}` },
        { label: t("title"), to: `/projects/${projectId}/executions` },
        { label: t("new.crumb") },
      ]}>
        <div className="max-w-2xl xl:max-w-3xl">
          <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-100">{t("new.title")}</h1>
        </div>
      </PageHeader>
      <PageBody>
        <div className="max-w-2xl xl:max-w-3xl">
          <form onSubmit={handleSubmit} className="space-y-5">
        <div className="space-y-1.5">
          <Label>{t("new.titleField")}</Label>
          <Input value={title} onChange={event => setTitle(event.target.value)} placeholder={t("new.titlePlaceholder")} />
        </div>

        <div className="space-y-1.5">
          <Label>{t("new.description")}</Label>
          <MdEditor value={description} onChange={setDescription} height={100} />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1.5">
            <Label>{t("new.type")}</Label>
            <Select value={type} onValueChange={setType}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="manual">{t("new.typeManual")}</SelectItem>
                <SelectItem value="automatic">{t("new.typeAutomatic")}</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-1.5">
            <Label>{t("new.version")}</Label>
            <Input
              list="known-versions"
              value={versionInput}
              onChange={event => setVersionInput(event.target.value)}
              placeholder={versions.length > 0 ? t("new.versionPick") : t("new.versionType")}
            />
            {versions.length > 0 && (
              <datalist id="known-versions">
                {versions.map(version => (
                  <option key={version.id} value={version.name}>
                    {version.vcs_tag ? `${version.vcs_tag}` : version.status}
                  </option>
                ))}
              </datalist>
            )}
            <p className="text-[11px] text-gray-400 dark:text-gray-500">{t("new.versionHint")}</p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1.5">
            <Label>{t("new.environment")}</Label>
            <Input value={environment} onChange={event => setEnvironment(event.target.value)} placeholder={t("new.environmentPlaceholder")} />
          </div>
          {type === "automatic" && (
            <div className="space-y-1.5">
              <Label>{t("new.triggeredBy")}</Label>
              <Input value={triggeredBy} onChange={event => setTriggeredBy(event.target.value)} placeholder={t("new.triggeredByPlaceholder")} />
            </div>
          )}
        </div>

        <div className="space-y-1.5">
          <Label>{t("new.assignee")}</Label>
          <Select value={assigneeId} onValueChange={value => setAssigneeId(value === "__none__" ? "" : value)}>
            <SelectTrigger><SelectValue placeholder={t("new.unassigned")} /></SelectTrigger>
            <SelectContent>
              <SelectItem value="__none__">{t("new.unassigned")}</SelectItem>
              {members.map(member => (
                <SelectItem key={member.user_id} value={String(member.user_id)}>{member.username}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label>{t("new.casesSource")}</Label>
          <div className="flex gap-4 text-sm">
            <label className="flex items-center gap-1.5 cursor-pointer">
              <input type="radio" value="cases" checked={source === "cases"} onChange={() => setSource("cases")} />
              {t("new.pickManually")}
            </label>
            <label className="flex items-center gap-1.5 cursor-pointer">
              <input type="radio" value="plan" checked={source === "plan"} onChange={() => setSource("plan")} />
              {t("new.fromPlan")}
            </label>
          </div>

          {source === "plan" ? (
            <Select value={planId} onValueChange={setPlanId}>
              <SelectTrigger><SelectValue placeholder={t("new.selectPlan")} /></SelectTrigger>
              <SelectContent>
                {plans.map(plan => <SelectItem key={plan.id} value={String(plan.id)}>{plan.title}</SelectItem>)}
              </SelectContent>
            </Select>
          ) : (
            <CasePicker
              projectId={projectId}
              selected={selectedCases}
              onToggle={toggleCase}
              maxHeight="max-h-56"
            />
          )}
          {source === "cases" && (
            <p className="text-xs text-gray-400 dark:text-gray-500">{t("new.selectedCount", { count: selectedCases.length })}</p>
          )}
        </div>

          <Button type="submit" className="w-full" disabled={createExecution.isPending}>
            {createExecution.isPending ? t("new.creating") : t("new.create")}
          </Button>
          </form>
        </div>
      </PageBody>
    </>
  )
}
