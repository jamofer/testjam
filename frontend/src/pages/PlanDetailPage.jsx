import { useState } from "react"
import { useParams, useNavigate, Link } from "react-router-dom"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { Trash2, Plus, ClipboardList, PlayCircle, X } from "lucide-react"
import { plansApi } from "../api/testplans"
import { casesApi } from "../api/testcases"
import { useSuitesAll, sortSuitesHierarchically } from "../hooks/useSuites"
import { useProject } from "../hooks/useProjects"
import { Button } from "../components/ui/button"
import { Input } from "../components/ui/input"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "../components/ui/dialog"
import { Breadcrumbs } from "../components/ui/breadcrumbs"
import { EmptyState } from "../components/ui/empty-state"
import { toast } from "sonner"

function AddCasesDialog({ plan, projectId, onAdded }) {
  const [open, setOpen] = useState(false)
  const [selected, setSelected] = useState([])
  const [casesBySuite, setCasesBySuite] = useState({})
  const { data: rawSuites = [] } = useSuitesAll(projectId)
  const suites = sortSuitesHierarchically(rawSuites)
  const qc = useQueryClient()

  const existing = new Set(plan.test_case_ids)

  const loadCases = async (suiteId) => {
    if (casesBySuite[suiteId]) return
    const cases = await casesApi.list(suiteId)
    setCasesBySuite(prev => ({ ...prev, [suiteId]: cases }))
  }

  const toggle = (id) =>
    setSelected(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id])

  const handleAdd = async () => {
    if (!selected.length) return
    await plansApi.addCases(plan.id, selected)
    qc.invalidateQueries({ queryKey: ["plan", plan.id] })
    toast.success(`${selected.length} cases added`)
    setSelected([])
    setOpen(false)
    onAdded?.()
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm"><Plus size={14} /> Add cases</Button>
      </DialogTrigger>
      <DialogContent className="max-w-lg">
        <DialogHeader><DialogTitle>Add test cases</DialogTitle></DialogHeader>
        <div className="space-y-4">
          <div className="border rounded-lg max-h-64 overflow-y-auto divide-y">
            {suites.map(suite => (
              <details key={suite.id} onToggle={() => loadCases(suite.id)} className="group">
                <summary className={`flex items-center gap-2 py-2 cursor-pointer text-sm font-medium bg-gray-50 hover:bg-gray-100 ${suite.parent_suite_id ? "pl-7" : "px-3"}`}>
                  {suite.name}
                </summary>
                <div className="px-4 py-1 space-y-1">
                  {(casesBySuite[suite.id] ?? []).filter(tc => !existing.has(tc.id)).map(tc => (
                    <label key={tc.id} className="flex items-center gap-2 text-sm cursor-pointer hover:bg-gray-50 px-1 py-0.5 rounded">
                      <input type="checkbox" checked={selected.includes(tc.id)} onChange={() => toggle(tc.id)} />
                      {tc.name}
                    </label>
                  ))}
                  {(casesBySuite[suite.id] ?? []).filter(tc => existing.has(tc.id)).length === (casesBySuite[suite.id] ?? []).length
                    && (casesBySuite[suite.id] ?? []).length > 0 && (
                    <p className="text-xs text-gray-400 py-1">All cases already in plan</p>
                  )}
                </div>
              </details>
            ))}
          </div>
          <p className="text-xs text-gray-400">{selected.length} selected</p>
          <Button onClick={handleAdd} className="w-full" disabled={!selected.length}>Add to plan</Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}

export function PlanDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const qc = useQueryClient()

  const { data: plan, isLoading } = useQuery({
    queryKey: ["plan", parseInt(id)],
    queryFn: () => plansApi.get(id),
    enabled: !!id,
  })

  const { data: project } = useProject(plan?.project_id)

  const updatePlan = useMutation({
    mutationFn: (data) => plansApi.update(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["plan", parseInt(id)] }),
  })

  const [editingTitle, setEditingTitle] = useState(false)
  const [title, setTitle] = useState("")

  const caseQueries = useQuery({
    queryKey: ["plan-cases", parseInt(id), plan?.test_case_ids],
    queryFn: async () => {
      if (!plan?.test_case_ids?.length) return []
      const results = await Promise.all(plan.test_case_ids.map(cid => casesApi.get(cid)))
      return results
    },
    enabled: !!plan,
  })

  if (isLoading) return <p className="text-gray-500">Loading…</p>
  if (!plan) return null

  const cases = caseQueries.data ?? []

  const startEditTitle = () => { setTitle(plan.title); setEditingTitle(true) }
  const saveTitle = async () => {
    await updatePlan.mutateAsync({ title })
    toast.success("Plan updated")
    setEditingTitle(false)
  }

  const removeCase = async (caseId) => {
    const remaining = plan.test_case_ids.filter(id => id !== caseId)
    await updatePlan.mutateAsync({ test_case_ids: remaining })
    toast.success("Case removed")
  }

  return (
    <div className="max-w-2xl space-y-6">
      <Breadcrumbs
        crumbs={[
          { label: "Projects", to: "/projects" },
          { label: project?.name ?? "…", to: `/projects/${plan.project_id}` },
          { label: "Test Plans", to: `/projects/${plan.project_id}/plans` },
          { label: plan.title },
        ]}
      />

      {editingTitle ? (
        <div className="flex gap-2 items-center">
          <Input value={title} onChange={e => setTitle(e.target.value)} className="text-lg font-bold" />
          <Button size="sm" onClick={saveTitle}>Save</Button>
          <Button size="sm" variant="ghost" onClick={() => setEditingTitle(false)}>Cancel</Button>
        </div>
      ) : (
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-800 cursor-pointer hover:text-gray-600"
            onClick={startEditTitle}>
            {plan.title}
          </h1>
          <Link to={`/projects/${plan.project_id}/executions/new?planId=${plan.id}`}>
            <Button size="sm"><PlayCircle size={14} /> Run</Button>
          </Link>
        </div>
      )}

      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-500">{plan.test_case_ids.length} test cases</p>
        <AddCasesDialog plan={plan} projectId={plan.project_id} />
      </div>

      {cases.length === 0 ? (
        <EmptyState
          icon={ClipboardList}
          title="No test cases"
          description="Add test cases to this plan to run them together."
        />
      ) : (
        <ul className="space-y-1.5">
          {cases.map(tc => (
            <li key={tc.id} className="flex items-center justify-between bg-white border rounded-lg px-4 py-2.5 group">
              <Link to={`/cases/${tc.id}`} className="text-sm text-gray-800 hover:underline">{tc.name}</Link>
              <button onClick={() => removeCase(tc.id)}
                className="opacity-0 group-hover:opacity-100 text-gray-300 hover:text-red-500">
                <X size={14} />
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
