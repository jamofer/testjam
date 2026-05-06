import { useState, useMemo } from "react"
import { useParams, useNavigate, Link } from "react-router-dom"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { Plus, ClipboardList, PlayCircle, Trash2, FolderOpen, ChevronRight } from "lucide-react"
import { plansApi } from "../api/testplans"
import { casesApi } from "../api/testcases"
import { useSuitesAll, sortSuitesHierarchically } from "../hooks/useSuites"
import { useProject } from "../hooks/useProjects"
import { Button } from "../components/ui/button"
import { Input } from "../components/ui/input"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "../components/ui/dialog"
import { Breadcrumbs } from "../components/ui/breadcrumbs"
import { EmptyState } from "../components/ui/empty-state"
import { CasePicker } from "../components/ui/case-picker"
import { TestCaseItem, mapSuiteByCase } from "../components/ui/test-case-item"
import { toast } from "sonner"

function buildSuiteTree(groups, allSuites) {
  const order = sortSuitesHierarchically(allSuites).map(s => s.id)
  const suiteMap = Object.fromEntries(allSuites.map(s => [s.id, s]))

  // Add ancestor suites needed for hierarchy even if they have no direct plan cases
  const full = { ...groups }
  Object.values(groups).forEach(({ suite }) => {
    if (!suite) return
    let pid = suite.parent_suite_id
    while (pid && !full[pid]) {
      const ancestor = suiteMap[pid]
      if (!ancestor) break
      full[pid] = { suite: ancestor, cases: [] }
      pid = ancestor.parent_suite_id
    }
  })

  const topLevelIds = []
  const childrenOf = {}

  Object.values(full).forEach(({ suite }) => {
    if (!suite) return
    const parentId = suite.parent_suite_id
    if (parentId && full[parentId]) {
      if (!childrenOf[parentId]) childrenOf[parentId] = []
      childrenOf[parentId].push(suite.id)
    } else {
      topLevelIds.push(suite.id)
    }
  })

  const sort = (ids) => ids.sort((a, b) => order.indexOf(a) - order.indexOf(b))
  sort(topLevelIds)
  Object.keys(childrenOf).forEach(pid => sort(childrenOf[pid]))

  return { topLevelIds, childrenOf, full }
}

function PlanSuiteGroup({ suiteId, groups, childrenOf, removeCase }) {
  const { suite, cases: suiteCases } = groups[suiteId]
  const children = childrenOf[suiteId] ?? []

  return (
    <div className="border rounded-lg overflow-hidden">
      <details open className="group/suite">
        <summary className="flex items-center gap-2 px-3 py-2 bg-gray-50 hover:bg-gray-100 cursor-pointer list-none font-medium text-sm text-gray-800">
          <ChevronRight size={14} className="transition-transform shrink-0 group-open/suite:rotate-90" />
          <FolderOpen size={14} className="text-yellow-500 shrink-0" />
          <span className="truncate flex-1">{suite.name}</span>
          <span className="text-xs text-gray-400 shrink-0">({suiteCases.length})</span>
        </summary>
        <div className="px-2 py-1">
          {children.length > 0 && (
            <div className="pl-4 mt-2 space-y-2 border-l-2 border-gray-100">
              {children.map(childId => (
                <PlanSuiteGroup key={childId} suiteId={childId} groups={groups} childrenOf={childrenOf} removeCase={removeCase} />
              ))}
            </div>
          )}
          {suiteCases.length > 0 && (
            <ul className="pl-4 space-y-0.5">
              {suiteCases.map(tc => (
                <li key={tc.id} className="flex items-center justify-between rounded px-2 py-1.5 hover:bg-gray-50 group transition-colors">
                  <Link to={`/cases/${tc.id}`} className="min-w-0 flex-1">
                    <TestCaseItem tc={tc} />
                  </Link>
                  <button onClick={() => removeCase(tc.id)}
                    className="ml-2 shrink-0 opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-500 transition-colors">
                    <Trash2 size={13} />
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </details>
    </div>
  )
}

function AddCasesDialog({ plan, projectId }) {
  const [open, setOpen] = useState(false)
  const [selected, setSelected] = useState([])
  const qc = useQueryClient()

  const toggle = (id) =>
    setSelected(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id])

  const handleAdd = async () => {
    if (!selected.length) return
    await plansApi.addCases(plan.id, selected)
    qc.invalidateQueries({ queryKey: ["plan", plan.id] })
    toast.success(`${selected.length} cases added`)
    setSelected([])
    setOpen(false)
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm"><Plus size={14} /> Add cases</Button>
      </DialogTrigger>
      <DialogContent className="max-w-lg">
        <DialogHeader><DialogTitle>Add test cases</DialogTitle></DialogHeader>
        <div className="space-y-4">
          <CasePicker
            projectId={projectId}
            selected={selected}
            onToggle={toggle}
            excludeIds={plan.test_case_ids}
          />
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
  const { data: allSuites = [] } = useSuitesAll(plan?.project_id)

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

  const cases = caseQueries.data ?? []

  const suiteByCase = useMemo(() => mapSuiteByCase(allSuites), [allSuites])
  const { groups, topLevelIds, childrenOf } = useMemo(() => {
    const raw = {}
    cases.forEach(tc => {
      const suite = suiteByCase[tc.id]
      const key = suite?.id ?? 0
      if (!raw[key]) raw[key] = { suite: suite ?? null, cases: [] }
      raw[key].cases.push(tc)
    })
    const { topLevelIds, childrenOf, full } = buildSuiteTree(raw, allSuites)
    return { groups: full, topLevelIds, childrenOf }
  }, [cases, suiteByCase, allSuites])

  if (isLoading) return <p className="text-gray-500">Loading…</p>
  if (!plan) return null

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
    <div className="p-8 max-w-2xl space-y-6">
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
        <div className="space-y-2">
          {topLevelIds.map(suiteId => (
            <PlanSuiteGroup key={suiteId} suiteId={suiteId} groups={groups} childrenOf={childrenOf} removeCase={removeCase} />
          ))}
          {groups[0] && (
            <ul className="space-y-0.5">
              {groups[0].cases.map(tc => (
                <li key={tc.id} className="flex items-center justify-between rounded px-2 py-1.5 hover:bg-gray-50 group transition-colors">
                  <Link to={`/cases/${tc.id}`} className="min-w-0 flex-1">
                    <TestCaseItem tc={tc} />
                  </Link>
                  <button onClick={() => removeCase(tc.id)}
                    className="ml-2 shrink-0 opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-500 transition-colors">
                    <Trash2 size={13} />
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  )
}
