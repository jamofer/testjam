import { useState } from "react"
import { useParams, Link } from "react-router-dom"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { Plus, Trash2, ClipboardList } from "lucide-react"
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

function usePlans(projectId) {
  return useQuery({ queryKey: ["plans", projectId], queryFn: () => plansApi.list(projectId), enabled: !!projectId })
}

function CreatePlanDialog({ projectId, onCreated }) {
  const [open, setOpen] = useState(false)
  const [title, setTitle] = useState("")
  const [selectedCases, setSelectedCases] = useState([])
  const { data: rawSuites = [] } = useSuitesAll(projectId)
  const suites = sortSuitesHierarchically(rawSuites)
  const [casesBySuite, setCasesBySuite] = useState({})
  const qc = useQueryClient()

  const loadCases = async (suiteId) => {
    if (casesBySuite[suiteId]) return
    const cases = await casesApi.list(suiteId)
    setCasesBySuite(prev => ({ ...prev, [suiteId]: cases }))
  }

  const toggleCase = (id) =>
    setSelectedCases(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id])

  const handleCreate = async () => {
    if (!title.trim()) return
    await plansApi.create(projectId, { title: title.trim(), test_case_ids: selectedCases })
    qc.invalidateQueries({ queryKey: ["plans", projectId] })
    toast.success("Test plan created")
    setTitle("")
    setSelectedCases([])
    setOpen(false)
    onCreated?.()
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm"><Plus size={14} /> New plan</Button>
      </DialogTrigger>
      <DialogContent className="max-w-lg">
        <DialogHeader><DialogTitle>New test plan</DialogTitle></DialogHeader>
        <div className="space-y-4">
          <Input placeholder="Plan title…" value={title} onChange={e => setTitle(e.target.value)} />
          <div>
            <p className="text-sm font-medium mb-2">Select test cases</p>
            <div className="border rounded-lg max-h-64 overflow-y-auto divide-y">
              {suites.map(suite => (
                <details key={suite.id} onToggle={() => loadCases(suite.id)} className="group">
                  <summary className={`flex items-center gap-2 py-2 cursor-pointer text-sm font-medium bg-gray-50 hover:bg-gray-100 ${suite.parent_suite_id ? "pl-7" : "px-3"}`}>
                    {suite.name}
                  </summary>
                  <div className="px-4 py-1 space-y-1">
                    {(casesBySuite[suite.id] ?? []).map(tc => (
                      <label key={tc.id} className="flex items-center gap-2 text-sm cursor-pointer hover:bg-gray-50 px-1 py-0.5 rounded">
                        <input type="checkbox" checked={selectedCases.includes(tc.id)}
                          onChange={() => toggleCase(tc.id)} />
                        {tc.name}
                      </label>
                    ))}
                  </div>
                </details>
              ))}
            </div>
            <p className="text-xs text-gray-400 mt-1">{selectedCases.length} cases selected</p>
          </div>
          <Button onClick={handleCreate} className="w-full" disabled={!title.trim()}>Create plan</Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}

export function TestPlansPage() {
  const { id: projectId } = useParams()
  const { data: plans = [], isLoading } = usePlans(projectId)
  const qc = useQueryClient()

  const deletePlan = useMutation({
    mutationFn: plansApi.delete,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["plans", projectId] })
      toast.success("Plan deleted")
    },
  })

  const { data: project } = useProject(projectId)

  if (isLoading) return <p className="text-gray-500">Loading…</p>

  return (
    <div className="max-w-2xl space-y-6">
      <Breadcrumbs
        crumbs={[
          { label: "Projects", to: "/projects" },
          { label: project?.name ?? "…", to: `/projects/${projectId}` },
          { label: "Test Plans" },
        ]}
      />
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800">Test Plans</h1>
        <CreatePlanDialog projectId={projectId} />
      </div>

      <ul className="space-y-2">
        {plans.map(plan => (
          <li key={plan.id} className="flex items-center justify-between bg-white border rounded-lg px-4 py-3 shadow-sm">
            <Link to={`/plans/${plan.id}`} className="flex items-center gap-2 font-medium text-gray-800 hover:underline">
              <ClipboardList size={15} className="text-blue-500" />
              {plan.title}
              <span className="text-xs text-gray-400">({plan.test_case_ids?.length ?? 0} cases)</span>
            </Link>
            <Button size="icon" variant="ghost" onClick={() => deletePlan.mutate(plan.id)}>
              <Trash2 size={14} />
            </Button>
          </li>
        ))}
        {plans.length === 0 && (
          <EmptyState
            icon={ClipboardList}
            title="No test plans yet"
            description="Test plans group cases for a release or milestone. Create one above to start orchestrating test runs."
          />
        )}
      </ul>
    </div>
  )
}
