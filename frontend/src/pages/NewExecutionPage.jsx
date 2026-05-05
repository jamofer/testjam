import { useState } from "react"
import { useParams, useNavigate } from "react-router-dom"
import { useCreateExecution } from "../hooks/useExecutions"
import { useSuites, useCases } from "../hooks/useSuites"
import { useVersions } from "../hooks/useVersions"
import { useMembers } from "../hooks/useMembers"
import { useQuery } from "@tanstack/react-query"
import { plansApi } from "../api/testplans"
import { Button } from "../components/ui/button"
import { Input } from "../components/ui/input"
import { Label } from "../components/ui/label"
import { MdEditor } from "../components/MdEditor"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select"
import { toast } from "sonner"

function CasePicker({ projectId, selectedCases, onChange }) {
  const { data: suites = [] } = useSuites(projectId)
  const [casesBySuite, setCasesBySuite] = useState({})

  const loadCases = async (suiteId) => {
    if (casesBySuite[suiteId]) return
    const { casesApi } = await import("../api/testcases")
    const cases = await casesApi.list(suiteId)
    setCasesBySuite(prev => ({ ...prev, [suiteId]: cases }))
  }

  const toggle = (id) =>
    onChange(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id])

  return (
    <div className="border rounded-lg max-h-56 overflow-y-auto divide-y text-sm">
      {suites.map(suite => (
        <details key={suite.id} onToggle={() => loadCases(suite.id)}>
          <summary className="px-3 py-2 cursor-pointer font-medium bg-gray-50 hover:bg-gray-100">{suite.name}</summary>
          <div className="px-4 py-1 space-y-1">
            {(casesBySuite[suite.id] ?? []).map(tc => (
              <label key={tc.id} className="flex items-center gap-2 cursor-pointer hover:bg-gray-50 px-1 py-0.5 rounded">
                <input type="checkbox" checked={selectedCases.includes(tc.id)} onChange={() => toggle(tc.id)} />
                {tc.name}
              </label>
            ))}
          </div>
        </details>
      ))}
    </div>
  )
}

export function NewExecutionPage() {
  const { id: projectId } = useParams()
  const navigate = useNavigate()
  const createExecution = useCreateExecution(projectId)
  const { data: versions = [] } = useVersions(projectId)
  const { data: members = [] } = useMembers(projectId)

  const [title, setTitle] = useState("")
  const [description, setDescription] = useState("")
  const [type, setType] = useState("manual")
  const [versionId, setVersionId] = useState("")
  const [versionFreeText, setVersionFreeText] = useState("")
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

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!title.trim()) return toast.error("Title is required")

    const payload = {
      title: title.trim(),
      description,
      type,
      version_id: versionId ? parseInt(versionId) : undefined,
      version: !versionId && versionFreeText ? versionFreeText : undefined,
      environment: environment || undefined,
      triggered_by: type === "automatic" ? triggeredBy || undefined : undefined,
      assigned_to_id: assigneeId ? parseInt(assigneeId) : undefined,
      test_case_ids: source === "cases" ? selectedCases : [],
      test_plan_id: source === "plan" && planId ? parseInt(planId) : undefined,
    }

    try {
      const exec = await createExecution.mutateAsync(payload)
      toast.success("Execution created")
      navigate(`/executions/${exec.id}/run`)
    } catch {
      toast.error("Failed to create execution")
    }
  }

  const selectedVersion = versions.find(v => String(v.id) === versionId)

  return (
    <div className="max-w-xl space-y-6">
      <h1 className="text-2xl font-bold text-gray-800">New Execution</h1>
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
            {versions.length > 0 ? (
              <div className="space-y-1.5">
                <Select value={versionId} onValueChange={v => { setVersionId(v); setVersionFreeText("") }}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select version…" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">— Free text —</SelectItem>
                    {versions.map(v => (
                      <SelectItem key={v.id} value={String(v.id)}>
                        {v.name}{v.vcs_tag ? ` (${v.vcs_tag})` : ""}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {!versionId && (
                  <Input value={versionFreeText} onChange={e => setVersionFreeText(e.target.value)}
                    placeholder="or type a version string…" className="text-sm" />
                )}
              </div>
            ) : (
              <Input value={versionFreeText} onChange={e => setVersionFreeText(e.target.value)}
                placeholder="1.4.2" />
            )}
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
          <Select value={assigneeId} onValueChange={setAssigneeId}>
            <SelectTrigger><SelectValue placeholder="Unassigned" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="">Unassigned</SelectItem>
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
            <CasePicker projectId={projectId} selectedCases={selectedCases} onChange={setSelectedCases} />
          )}
          {source === "cases" && (
            <p className="text-xs text-gray-400">{selectedCases.length} cases selected</p>
          )}
        </div>

        <Button type="submit" className="w-full" disabled={createExecution.isPending}>
          {createExecution.isPending ? "Creating…" : "Create & start execution"}
        </Button>
      </form>
    </div>
  )
}
