import { useState } from "react"
import { useParams, Link } from "react-router-dom"
import { useTranslation } from "react-i18next"
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
  const { t } = useTranslation("plans")
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
    toast.success(t("created"))
    setTitle("")
    setSelectedCases([])
    setOpen(false)
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm"><Plus size={14} /> {t("newPlan")}</Button>
      </DialogTrigger>
      <DialogContent className="max-w-lg">
        <DialogHeader><DialogTitle>{t("newPlanTitle")}</DialogTitle></DialogHeader>
        <div className="space-y-4">
          <Input placeholder={t("planTitle")} value={title} onChange={event => setTitle(event.target.value)} />
          <div>
            <p className="text-sm font-medium mb-2">{t("selectCases")}</p>
            <CasePicker projectId={projectId} selected={selectedCases} onToggle={toggle} />
            <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">{t("selectedCases", { count: selectedCases.length })}</p>
          </div>
          <Button onClick={handleCreate} className="w-full" disabled={!title.trim()}>{t("create")}</Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}

export function TestPlansPage() {
  const { t } = useTranslation(["plans", "nav"])
  const { id: projectId } = useParams()
  const { data: plans = [], isLoading } = usePlans(projectId)
  const qc = useQueryClient()

  const deletePlan = useMutation({
    mutationFn: plansApi.delete,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["plans", projectId] })
      toast.success(t("deleted"))
    },
  })

  const { data: project } = useProject(projectId)

  if (isLoading) return <p className="text-gray-500 dark:text-gray-400">{t("loading")}</p>

  return (
    <>
      <PageHeader crumbs={[
        { label: t("nav:global.projects"), to: "/projects" },
        { label: project?.name ?? "…", to: `/projects/${projectId}` },
        { label: t("title") },
      ]}>
        <div className="max-w-2xl xl:max-w-4xl 2xl:max-w-5xl flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-100">{t("title")}</h1>
          <div className="self-start sm:self-auto">
            <CreatePlanDialog projectId={projectId} />
          </div>
        </div>
      </PageHeader>

      <PageBody>
      <div className="max-w-2xl xl:max-w-4xl 2xl:max-w-5xl">
      <ul className="space-y-2">
        {plans.map(plan => (
          <li key={plan.id} className="flex items-center justify-between bg-white dark:bg-gray-900 border rounded-lg px-4 py-3 shadow-sm">
            <Link to={`/plans/${plan.id}`} className="flex items-center gap-2 font-medium text-gray-800 dark:text-gray-100 hover:underline">
              <ClipboardList size={15} className="text-blue-500" />
              {plan.title}
              <span className="text-xs text-gray-400 dark:text-gray-500">{t("cases", { count: plan.test_case_ids?.length ?? 0 })}</span>
            </Link>
            <Button size="icon" variant="ghost" onClick={() => deletePlan.mutate(plan.id)}>
              <Trash2 size={14} />
            </Button>
          </li>
        ))}
        {plans.length === 0 && (
          <EmptyState
            icon={ClipboardList}
            title={t("empty.title")}
            description={t("empty.description")}
          />
        )}
      </ul>
      </div>
      </PageBody>
    </>
  )
}
