import { useState } from "react"
import { useParams, Link } from "react-router-dom"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { Plus, Trash2, ClipboardList } from "lucide-react"
import { plansApi } from "../api/testplans"
import { useProject } from "../hooks/useProjects"
import { Button } from "../components/ui/button"
import { Input } from "../components/ui/input"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "../components/ui/dialog"
import { EmptyState } from "../components/ui/empty-state"
import { PageHeader, PageBody } from "../components/ui/page-header"
import { CasePicker } from "../components/ui/case-picker"
import { toast } from "sonner"

function usePlans(projectId) {
  return useQuery({ queryKey: ["plans", projectId], queryFn: () => plansApi.list(projectId), enabled: !!projectId })
}

function CreatePlanDialog({ projectId }) {
  const [open, setOpen] = useState(false)
  const [title, setTitle] = useState("")
  const [selectedCases, setSelectedCases] = useState([])
  const qc = useQueryClient()

  const toggle = (id) =>
    setSelectedCases(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id])

  const handleCreate = async () => {
    if (!title.trim()) return
    await plansApi.create(projectId, { title: title.trim(), test_case_ids: selectedCases })
    qc.invalidateQueries({ queryKey: ["plans", projectId] })
    toast.success("Test plan created")
    setTitle("")
    setSelectedCases([])
    setOpen(false)
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
            <CasePicker projectId={projectId} selected={selectedCases} onToggle={toggle} />
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
    <>
      <PageHeader crumbs={[
        { label: "Projects", to: "/projects" },
        { label: project?.name ?? "…", to: `/projects/${projectId}` },
        { label: "Test Plans" },
      ]}>
        <div className="max-w-2xl flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <h1 className="text-2xl font-bold text-gray-800">Test Plans</h1>
          <div className="self-start sm:self-auto">
            <CreatePlanDialog projectId={projectId} />
          </div>
        </div>
      </PageHeader>

      <PageBody>
      <div className="max-w-2xl">
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
      </PageBody>
    </>
  )
}
