import { useState } from "react"
import { Link } from "react-router-dom"
import { Plus, Trash2, Pencil, ChevronRight, FolderOpen, FileText } from "lucide-react"
import { useQueryClient } from "@tanstack/react-query"
import {
  useChildSuites, useCreateSuite, useUpdateSuite, useDeleteSuite,
  useCases, useCreateCase, useDeleteCase,
} from "../../hooks/useSuites"
import { suitesApi } from "../../api/testcases"
import { Button } from "../ui/button"
import { Input } from "../ui/input"
import { MdEditor, MdViewer } from "../MdEditor"
import { toast } from "sonner"

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

function AddSubSuiteInline({ parentSuiteId, projectId, onDone }) {
  const [name, setName] = useState("")
  const createSuite = useCreateSuite(projectId)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!name.trim()) return
    await createSuite.mutateAsync({ name: name.trim(), parent_suite_id: parentSuiteId })
    toast.success("Sub-suite created")
    setName("")
    onDone()
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-2 px-2 py-1">
      <Input autoFocus placeholder="Sub-suite name…" value={name}
        onChange={e => setName(e.target.value)} className="h-7 text-xs" />
      <Button size="sm" type="submit" disabled={createSuite.isPending}>Add</Button>
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

function ChildSuites({ projectId, parentSuiteId }) {
  const { data: children = [] } = useChildSuites(projectId, parentSuiteId)
  if (children.length === 0) return null
  return (
    <div className="pl-4 mt-2 space-y-2 border-l-2 border-gray-100">
      {children.map(child => (
        <SuiteRow key={child.id} suite={child} projectId={projectId} />
      ))}
    </div>
  )
}

export function SuiteRow({ suite, projectId }) {
  const [open, setOpen] = useState(true)
  const [addingCase, setAddingCase] = useState(false)
  const [addingSuite, setAddingSuite] = useState(false)
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
          <Button size="sm" variant="ghost" onClick={() => { setAddingSuite(a => !a); setAddingCase(false) }}>
            <Plus size={13} /> Suite
          </Button>
          <Button size="sm" variant="ghost" onClick={() => { setAddingCase(a => !a); setAddingSuite(false) }}>
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
          {addingSuite && (
            <AddSubSuiteInline parentSuiteId={suite.id} projectId={projectId} onDone={() => setAddingSuite(false)} />
          )}
          {addingCase && <AddCaseInline suiteId={suite.id} onDone={() => setAddingCase(false)} />}
          <ChildSuites projectId={projectId} parentSuiteId={suite.id} />
          <CaseList suiteId={suite.id} />
        </div>
      )}
    </div>
  )
}
