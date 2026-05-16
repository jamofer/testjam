import { useState } from "react"
import { useParams, useNavigate } from "react-router-dom"
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

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!title.trim()) return toast.error("Title is required")

    const selectedPlan = source === "plan" ? plans.find(p => String(p.id) === planId) : null
    if (source === "plan" && !selectedPlan) return toast.error("Select a test plan")

    const trimmedVersion = versionInput.trim()
    const matchedVersion = trimmedVersion
      ? versions.find(v => v.name.toLowerCase() === trimmedVersion.toLowerCase())
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
      const exec = await createExecution.mutateAsync(payload)
      toast.success("Execution created")
      navigate(`/executions/${exec.id}/run`)
    } catch {
      toast.error("Failed to create execution")
    }
  }

  return (
    <>
      <PageHeader crumbs={[
        { label: "Projects", to: "/projects" },
        { label: project?.name ?? "…", to: `/projects/${projectId}` },
        { label: "Executions", to: `/projects/${projectId}/executions` },
        { label: "New" },
      ]}>
        <div className="max-w-2xl xl:max-w-3xl">
          <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-100">New Execution</h1>
        </div>
      </PageHeader>
      <PageBody>
        <div className="max-w-2xl xl:max-w-3xl">
          <form onSubmit={handleSubmit} className="space-y-5">
        <div className="space-y-1.5">
          <Label>Title *</Label>
          <Input value={title} onChange={e => setTitle(e.target.value)} placeholder="Sprint 23 regression…" />
        </div>

        <div className="space-y-1.5">
          <Label>Description</Label>
          <MdEditor value={description} onChange={setDescription} height={100} />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1.5">
            <Label>Type</Label>
            <Select value={type} onValueChange={setType}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="manual">Manual</SelectItem>
                <SelectItem value="automatic">Automatic</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-1.5">
            <Label>Version</Label>
            <Input
              list="known-versions"
              value={versionInput}
              onChange={e => setVersionInput(e.target.value)}
              placeholder={versions.length > 0 ? "Pick or type… (e.g. 1.4.2)" : "e.g. 1.4.2 or sprint-23"}
            />
            {versions.length > 0 && (
              <datalist id="known-versions">
                {versions.map(v => (
                  <option key={v.id} value={v.name}>
                    {v.vcs_tag ? `${v.vcs_tag}` : v.status}
                  </option>
                ))}
              </datalist>
            )}
            <p className="text-[11px] text-gray-400 dark:text-gray-500">Optional. Existing versions auto-suggest as you type.</p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1.5">
            <Label>Environment</Label>
            <Input value={environment} onChange={e => setEnvironment(e.target.value)} placeholder="staging" />
          </div>
          {type === "automatic" && (
            <div className="space-y-1.5">
              <Label>Triggered by</Label>
              <Input value={triggeredBy} onChange={e => setTriggeredBy(e.target.value)} placeholder="github-actions" />
            </div>
          )}
        </div>

        <div className="space-y-1.5">
          <Label>Assignee</Label>
          <Select value={assigneeId} onValueChange={v => setAssigneeId(v === "__none__" ? "" : v)}>
            <SelectTrigger><SelectValue placeholder="Unassigned" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="__none__">Unassigned</SelectItem>
              {members.map(m => (
                <SelectItem key={m.user_id} value={String(m.user_id)}>{m.username}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label>Test cases source</Label>
          <div className="flex gap-4 text-sm">
            <label className="flex items-center gap-1.5 cursor-pointer">
              <input type="radio" value="cases" checked={source === "cases"} onChange={() => setSource("cases")} />
              Pick manually
            </label>
            <label className="flex items-center gap-1.5 cursor-pointer">
              <input type="radio" value="plan" checked={source === "plan"} onChange={() => setSource("plan")} />
              From test plan
            </label>
          </div>

          {source === "plan" ? (
            <Select value={planId} onValueChange={setPlanId}>
              <SelectTrigger><SelectValue placeholder="Select plan…" /></SelectTrigger>
              <SelectContent>
                {plans.map(p => <SelectItem key={p.id} value={String(p.id)}>{p.title}</SelectItem>)}
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
            <p className="text-xs text-gray-400 dark:text-gray-500">{selectedCases.length} cases selected</p>
          )}
        </div>

          <Button type="submit" className="w-full" disabled={createExecution.isPending}>
            {createExecution.isPending ? "Creating…" : "Create & start execution"}
          </Button>
          </form>
        </div>
      </PageBody>
    </>
  )
}
