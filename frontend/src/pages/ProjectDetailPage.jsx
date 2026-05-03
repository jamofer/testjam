import { useState } from "react"
import { useParams, Link } from "react-router-dom"
import { Plus, Trash2, Pencil, ChevronRight, FolderOpen, FileText, PlayCircle, Tag, CheckCircle2, Archive, Circle, Clock } from "lucide-react"
import { useProject } from "../hooks/useProjects"
import { useSuites, useCreateSuite, useUpdateSuite, useDeleteSuite, useCases, useCreateCase, useDeleteCase } from "../hooks/useSuites"
import { useVersions, useCreateVersion, useDeleteVersion, useUpdateVersion } from "../hooks/useVersions"
import { useQueryClient } from "@tanstack/react-query"
import { suitesApi } from "../api/testcases"
import { Button } from "../components/ui/button"
import { Input } from "../components/ui/input"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "../components/ui/tabs"
import { MdEditor, MdViewer } from "../components/MdEditor"
import { toast } from "sonner"

// ─── Suite tree ───────────────────────────────────────────────────────────────

function AddCaseInline({ suiteId, onDone }) {
  const [title, setTitle] = useState("")
  const createCase = useCreateCase(suiteId)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!title.trim()) return
    await createCase.mutateAsync({ name: title.trim(), suite_id: suiteId })
    toast.success("Test case created")
    setTitle("")
    onDone()
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-2 px-2 py-1">
      <Input autoFocus placeholder="Test case title…" value={title}
        onChange={e => setTitle(e.target.value)} className="h-7 text-xs" />
      <Button size="sm" type="submit" disabled={createCase.isPending}>Add</Button>
      <Button size="sm" variant="ghost" type="button" onClick={onDone}>Cancel</Button>
    </form>
  )
}

function CaseList({ suiteId }) {
  const { data: cases = [] } = useCases(suiteId)
  const deleteCase = useDeleteCase(suiteId)

  if (cases.length === 0)
    return <p className="text-xs text-gray-400 pl-2 py-1">No test cases</p>

  return (
    <ul className="pl-4 space-y-0.5">
      {cases.map(tc => (
        <li key={tc.id} className="flex items-center justify-between rounded px-2 py-1 hover:bg-gray-50 group">
          <Link to={`/cases/${tc.id}`}
            className="flex items-center gap-2 text-sm text-gray-700 hover:text-gray-900">
            <FileText size={13} className="text-gray-400" />
            {tc.name}
          </Link>
          <button
            onClick={() => deleteCase.mutate(tc.id, { onSuccess: () => toast.success("Deleted") })}
            className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-500">
            <Trash2 size={13} />
          </button>
        </li>
      ))}
    </ul>
  )
}

const SUITE_STEP_STYLE = {
  setup:    "bg-blue-50 text-blue-600 border-blue-200",
  teardown: "bg-orange-50 text-orange-600 border-orange-200",
}

function SuiteStepList({ suiteId, steps, stepType, onRefresh }) {
  const [newAction, setNewAction] = useState("")

  const addStep = async () => {
    if (!newAction.trim()) return
    const order = steps.filter(s => s.step_type === stepType).length + 1
    await suitesApi.createStep(suiteId, { action: newAction.trim(), step_type: stepType, order })
    setNewAction("")
    onRefresh()
  }

  const deleteStep = async (stepId) => {
    await suitesApi.deleteStep(suiteId, stepId)
    onRefresh()
  }

  const typeSteps = steps.filter(s => s.step_type === stepType)
  const style = SUITE_STEP_STYLE[stepType]

  return (
    <div className="space-y-1.5">
      {typeSteps.map((step, i) => (
        <div key={step.id} className={`flex items-start gap-2 border rounded-lg px-3 py-2 ${style}`}>
          <span className="text-xs font-mono text-gray-400 mt-0.5 w-4">{i + 1}.</span>
          <span className="flex-1 text-sm">{step.action}</span>
          <button onClick={() => deleteStep(step.id)} className="text-gray-300 hover:text-red-500 shrink-0 mt-0.5">
            <Trash2 size={12} />
          </button>
        </div>
      ))}
      <div className="flex gap-2">
        <Input value={newAction} onChange={e => setNewAction(e.target.value)}
          placeholder={`Add ${stepType} step…`} className="h-7 text-xs"
          onKeyDown={e => e.key === "Enter" && addStep()} />
        <Button size="sm" variant="outline" onClick={addStep} disabled={!newAction.trim()}>
          <Plus size={12} />
        </Button>
      </div>
    </div>
  )
}

function SuiteEditPanel({ suite, projectId, onClose, updateSuite }) {
  const [name, setName] = useState(suite.name)
  const [description, setDescription] = useState(suite.description ?? "")
  const [tagsInput, setTagsInput] = useState((suite.tags ?? []).join(", "))
  const qc = useQueryClient()

  const refresh = () => qc.invalidateQueries({ queryKey: ["suites-list", projectId] })

  const handleSave = async () => {
    const trimmed = name.trim()
    if (!trimmed) return
    const tags = tagsInput.split(",").map(t => t.trim()).filter(Boolean)
    await updateSuite.mutateAsync({
      id: suite.id,
      data: { name: trimmed, description: description || null, tags },
    })
    toast.success("Suite saved")
    onClose()
  }

  return (
    <div className="border-t bg-white px-4 py-4 space-y-4" onClick={e => e.stopPropagation()}>
      <div className="space-y-1">
        <p className="text-xs text-gray-500">Name</p>
        <Input value={name} onChange={e => setName(e.target.value)} />
      </div>
      <div className="space-y-1">
        <p className="text-xs text-gray-500">Description</p>
        <MdEditor value={description} onChange={setDescription} height={80} />
      </div>
      <div className="space-y-1">
        <p className="text-xs text-gray-500">Tags <span className="text-gray-400">(comma-separated)</span></p>
        <Input value={tagsInput} onChange={e => setTagsInput(e.target.value)} placeholder="smoke, regression…" />
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-1.5">
          <p className="text-xs font-semibold text-blue-600 uppercase tracking-wide">Suite Setup</p>
          <SuiteStepList suiteId={suite.id} steps={suite.steps ?? []} stepType="setup" onRefresh={refresh} />
        </div>
        <div className="space-y-1.5">
          <p className="text-xs font-semibold text-orange-600 uppercase tracking-wide">Suite Teardown</p>
          <SuiteStepList suiteId={suite.id} steps={suite.steps ?? []} stepType="teardown" onRefresh={refresh} />
        </div>
      </div>
      <div className="flex gap-2">
        <Button size="sm" onClick={handleSave} loading={updateSuite.isPending}>Save</Button>
        <Button size="sm" variant="ghost" onClick={onClose}>Cancel</Button>
      </div>
    </div>
  )
}

function SuiteRow({ suite, projectId }) {
  const [open, setOpen] = useState(true)
  const [addingCase, setAddingCase] = useState(false)
  const [editing, setEditing] = useState(false)
  const deleteSuite = useDeleteSuite(projectId)
  const updateSuite = useUpdateSuite(projectId)

  return (
    <div className="border rounded-lg overflow-hidden">
      <div className="flex items-center justify-between px-3 py-2 bg-gray-50 hover:bg-gray-100 cursor-pointer"
        onClick={() => setOpen(o => !o)}>
        <div className="flex items-center gap-2 font-medium text-sm text-gray-800 flex-1 min-w-0">
          <ChevronRight size={14} className={`transition-transform shrink-0 ${open ? "rotate-90" : ""}`} />
          <FolderOpen size={14} className="text-yellow-500 shrink-0" />
          <span className="truncate">{suite.name}</span>
          <span className="text-xs text-gray-400 shrink-0">({suite.test_case_ids?.length ?? 0})</span>
          {(suite.tags ?? []).map(t => (
            <span key={t} className="text-xs bg-blue-50 text-blue-600 border border-blue-200 px-1.5 py-0.5 rounded-full shrink-0">{t}</span>
          ))}
        </div>
        <div className="flex gap-1 shrink-0" onClick={e => e.stopPropagation()}>
          <Button size="sm" variant="ghost" onClick={() => setEditing(v => !v)}>
            <Pencil size={13} />
          </Button>
          <Button size="sm" variant="ghost" onClick={() => setAddingCase(a => !a)}>
            <Plus size={13} /> Case
          </Button>
          <Button size="sm" variant="ghost"
            onClick={() => deleteSuite.mutate(suite.id, { onSuccess: () => toast.success("Suite deleted") })}>
            <Trash2 size={13} />
          </Button>
        </div>
      </div>
      {editing && (
        <SuiteEditPanel suite={suite} projectId={projectId} onClose={() => setEditing(false)} updateSuite={updateSuite} />
      )}
      {open && !editing && (
        <div className="px-2 py-1">
          {suite.description && (
            <div className="px-2 pt-2 pb-1 text-xs text-gray-500 prose prose-sm">
              <MdViewer value={suite.description} />
            </div>
          )}
          {(suite.steps ?? []).length > 0 && (
            <div className="flex gap-4 px-2 pb-2 text-xs text-gray-500">
              {["setup", "teardown"].map(t => {
                const typeSteps = suite.steps.filter(s => s.step_type === t)
                if (!typeSteps.length) return null
                const color = t === "setup" ? "text-blue-600" : "text-orange-600"
                return (
                  <div key={t}>
                    <span className={`font-medium ${color}`}>{t === "setup" ? "Setup" : "Teardown"}:</span>{" "}
                    {typeSteps.map(s => s.action).join(" → ")}
                  </div>
                )
              })}
            </div>
          )}
          {addingCase && <AddCaseInline suiteId={suite.id} onDone={() => setAddingCase(false)} />}
          <CaseList suiteId={suite.id} />
        </div>
      )}
    </div>
  )
}

// ─── Versions ─────────────────────────────────────────────────────────────────

const VERSION_STATUS_CONFIG = {
  active:   { label: "Active",   icon: Circle,       color: "text-blue-500",  bg: "bg-blue-50"   },
  released: { label: "Released", icon: CheckCircle2, color: "text-green-600", bg: "bg-green-50"  },
  archived: { label: "Archived", icon: Archive,      color: "text-gray-400",  bg: "bg-gray-50"   },
}

function VersionRow({ version, projectId }) {
  const deleteVersion = useDeleteVersion(projectId)
  const updateVersion = useUpdateVersion(projectId)
  const cfg = VERSION_STATUS_CONFIG[version.status] ?? VERSION_STATUS_CONFIG.active
  const Icon = cfg.icon

  const cycleStatus = () => {
    const next = { active: "released", released: "archived", archived: "active" }
    updateVersion.mutate({ id: version.id, data: { status: next[version.status] } })
  }

  return (
    <li className={`flex items-center gap-3 border rounded-lg px-4 py-3 ${cfg.bg}`}>
      <button onClick={cycleStatus} title="Click to change status" className="shrink-0">
        <Icon size={15} className={cfg.color} />
      </button>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-medium text-sm text-gray-800">{version.name}</span>
          {version.vcs_tag && (
            <span className="text-xs font-mono bg-white border px-1.5 py-0.5 rounded text-gray-500">
              {version.vcs_tag}
            </span>
          )}
        </div>
        {version.description && (
          <p className="text-xs text-gray-500 mt-0.5 truncate">{version.description}</p>
        )}
      </div>
      <span className={`text-xs font-medium ${cfg.color}`}>{cfg.label}</span>
      <button
        onClick={() => deleteVersion.mutate(version.id, { onSuccess: () => toast.success("Version deleted") })}
        className="text-gray-300 hover:text-red-500 shrink-0">
        <Trash2 size={13} />
      </button>
    </li>
  )
}

function VersionsPanel({ projectId }) {
  const { data: versions = [] } = useVersions(projectId)
  const createVersion = useCreateVersion(projectId)
  const [name, setName] = useState("")
  const [vcsTag, setVcsTag] = useState("")

  const handleCreate = async (e) => {
    e.preventDefault()
    if (!name.trim()) return
    await createVersion.mutateAsync({ name: name.trim(), vcs_tag: vcsTag.trim() || undefined })
    toast.success("Version created")
    setName("")
    setVcsTag("")
  }

  return (
    <div className="space-y-4">
      <form onSubmit={handleCreate} className="flex gap-2">
        <Input placeholder="Version name (e.g. 1.4.0, sprint-23)…" value={name}
          onChange={e => setName(e.target.value)} />
        <Input placeholder="VCS tag (optional)" value={vcsTag}
          onChange={e => setVcsTag(e.target.value)} className="w-40" />
        <Button type="submit" disabled={createVersion.isPending}>
          <Plus size={14} /> Add
        </Button>
      </form>

      <ul className="space-y-2">
        {versions.map(v => <VersionRow key={v.id} version={v} projectId={projectId} />)}
        {versions.length === 0 && (
          <p className="text-sm text-gray-400">No versions yet. Create one to track releases.</p>
        )}
      </ul>
    </div>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export function ProjectDetailPage() {
  const { id } = useParams()
  const { data: project } = useProject(id)
  const { data: suites = [], isLoading } = useSuites(id)
  const createSuite = useCreateSuite(id)
  const [newSuite, setNewSuite] = useState("")

  const handleCreateSuite = async (e) => {
    e.preventDefault()
    if (!newSuite.trim()) return
    await createSuite.mutateAsync({ name: newSuite.trim() })
    toast.success("Suite created")
    setNewSuite("")
  }

  if (isLoading) return <p className="text-gray-500">Loading…</p>

  return (
    <div className="max-w-2xl space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">{project?.name}</h1>
          {project?.description && <p className="text-sm text-gray-500 mt-0.5">{project.description}</p>}
          <div className="flex items-center gap-4 mt-2 text-xs text-gray-400">
            <span className="flex items-center gap-1">
              <FolderOpen size={12} />
              {project?.suite_count ?? 0} {project?.suite_count === 1 ? "suite" : "suites"} · {project?.case_count ?? 0} {project?.case_count === 1 ? "case" : "cases"}
            </span>
            <span className="flex items-center gap-1">
              <PlayCircle size={12} />
              {project?.execution_count ?? 0} {project?.execution_count === 1 ? "execution" : "executions"}
              {project?.last_execution_at && (
                <span className="flex items-center gap-1 ml-1">
                  <Clock size={10} />
                  {new Date(project.last_execution_at).toLocaleDateString(undefined, { month: "short", day: "numeric" })}
                </span>
              )}
            </span>
          </div>
        </div>
        <Link to={`/projects/${id}/executions`}>
          <Button variant="outline" size="sm"><PlayCircle size={14} /> Executions</Button>
        </Link>
      </div>

      <Tabs defaultValue="suites">
        <TabsList>
          <TabsTrigger value="suites"><FolderOpen size={13} className="mr-1" /> Test suites</TabsTrigger>
          <TabsTrigger value="versions"><Tag size={13} className="mr-1" /> Versions</TabsTrigger>
        </TabsList>

        <TabsContent value="suites" className="mt-4 space-y-4">
          <form onSubmit={handleCreateSuite} className="flex gap-2">
            <Input placeholder="New suite name…" value={newSuite} onChange={e => setNewSuite(e.target.value)} />
            <Button type="submit" disabled={createSuite.isPending}><Plus size={14} /> Suite</Button>
          </form>
          <div className="space-y-2">
            {suites.map(suite => <SuiteRow key={suite.id} suite={suite} projectId={id} />)}
            {suites.length === 0 && <p className="text-sm text-gray-400">No suites yet.</p>}
          </div>
        </TabsContent>

        <TabsContent value="versions" className="mt-4">
          <VersionsPanel projectId={id} />
        </TabsContent>
      </Tabs>
    </div>
  )
}
