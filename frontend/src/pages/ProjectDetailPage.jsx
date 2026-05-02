import { useState } from "react"
import { useParams, Link } from "react-router-dom"
import { Plus, Trash2, ChevronRight, FolderOpen, FileText, PlayCircle } from "lucide-react"
import { useProject } from "../hooks/useProjects"
import { useSuites, useCreateSuite, useDeleteSuite, useCases, useCreateCase, useDeleteCase } from "../hooks/useSuites"
import { Button } from "../components/ui/button"
import { Input } from "../components/ui/input"
import { toast } from "sonner"

function AddCaseInline({ suiteId, onDone }) {
  const [title, setTitle] = useState("")
  const createCase = useCreateCase(suiteId)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!title.trim()) return
    await createCase.mutateAsync({ title: title.trim(), suite_id: suiteId })
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
            {tc.title}
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

function SuiteRow({ suite, projectId }) {
  const [open, setOpen] = useState(true)
  const [addingCase, setAddingCase] = useState(false)
  const deleteSuite = useDeleteSuite(projectId)

  return (
    <div className="border rounded-lg overflow-hidden">
      <div className="flex items-center justify-between px-3 py-2 bg-gray-50 hover:bg-gray-100 cursor-pointer"
        onClick={() => setOpen(o => !o)}>
        <div className="flex items-center gap-2 font-medium text-sm text-gray-800">
          <ChevronRight size={14} className={`transition-transform ${open ? "rotate-90" : ""}`} />
          <FolderOpen size={14} className="text-yellow-500" />
          {suite.title}
          <span className="text-xs text-gray-400">({suite.test_case_ids?.length ?? 0})</span>
        </div>
        <div className="flex gap-1" onClick={e => e.stopPropagation()}>
          <Button size="sm" variant="ghost" onClick={() => setAddingCase(a => !a)}>
            <Plus size={13} /> Case
          </Button>
          <Button size="sm" variant="ghost"
            onClick={() => deleteSuite.mutate(suite.id, { onSuccess: () => toast.success("Suite deleted") })}>
            <Trash2 size={13} />
          </Button>
        </div>
      </div>
      {open && (
        <div className="px-2 py-1">
          {addingCase && <AddCaseInline suiteId={suite.id} onDone={() => setAddingCase(false)} />}
          <CaseList suiteId={suite.id} />
        </div>
      )}
    </div>
  )
}

export function ProjectDetailPage() {
  const { id } = useParams()
  const { data: project } = useProject(id)
  const { data: suites = [], isLoading } = useSuites(id)
  const createSuite = useCreateSuite(id)
  const [newSuite, setNewSuite] = useState("")

  const handleCreateSuite = async (e) => {
    e.preventDefault()
    if (!newSuite.trim()) return
    await createSuite.mutateAsync({ title: newSuite.trim() })
    toast.success("Suite created")
    setNewSuite("")
  }

  if (isLoading) return <p className="text-gray-500">Loading…</p>

  return (
    <div className="max-w-2xl space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">{project?.name}</h1>
          {project?.description && <p className="text-sm text-gray-500 mt-1">{project.description}</p>}
        </div>
        <Link to={`/projects/${id}/executions`}>
          <Button variant="outline" size="sm"><PlayCircle size={14} /> Executions</Button>
        </Link>
      </div>

      <form onSubmit={handleCreateSuite} className="flex gap-2">
        <Input placeholder="New suite name…" value={newSuite} onChange={e => setNewSuite(e.target.value)} />
        <Button type="submit" disabled={createSuite.isPending}><Plus size={14} /> Suite</Button>
      </form>

      <div className="space-y-2">
        {suites.map(suite => (
          <SuiteRow key={suite.id} suite={suite} projectId={id} />
        ))}
        {suites.length === 0 && <p className="text-sm text-gray-400">No suites yet.</p>}
      </div>
    </div>
  )
}
