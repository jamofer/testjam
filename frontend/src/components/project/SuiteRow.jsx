import { useState, useMemo, useEffect, useContext, createContext } from "react"
import { Link, useParams } from "react-router-dom"
import { useTranslation } from "react-i18next"
import { Plus, Trash2, Pencil, ChevronRight, FolderOpen, ListPlus, X, GripVertical } from "lucide-react"
import { useTreeItemNav } from "../../hooks/useTreeItemNav"

export const SuiteCollapseContext = createContext({ version: 0, desiredOpen: true })
import { TestCaseItem } from "../ui/test-case-item"
import { useQueryClient, useQuery } from "@tanstack/react-query"
import {
  useChildSuites, useCreateSuite, useUpdateSuite, useDeleteSuite, useArchiveSuite, useReorderProjectSuites,
  useCases, useCreateCase, useDeleteCase, useBulkDeleteCases, useReorderSuiteSteps, useReorderSuiteCases,
} from "../../hooks/useSuites"
import { suitesApi } from "../../api/testcases"
import { plansApi } from "../../api/testplans"
import { Button } from "../ui/button"
import { Input } from "../ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../ui/select"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "../ui/dialog"
import { MdEditor, MdViewer } from "../MdEditor"
import { toast } from "sonner"
import { DndContext, closestCenter, PointerSensor, useSensor, useSensors } from "@dnd-kit/core"
import { SortableContext, verticalListSortingStrategy, useSortable } from "@dnd-kit/sortable"
import { CSS } from "@dnd-kit/utilities"

function AddCaseInline({ suiteId, onDone }) {
  const { t } = useTranslation("suites")
  const [title, setTitle] = useState("")
  const createCase = useCreateCase(suiteId)

  const handleSubmit = async (event) => {
    event.preventDefault()
    if (!title.trim()) return
    await createCase.mutateAsync({ name: title.trim(), suite_id: suiteId })
    toast.success(t("row.caseCreated"))
    setTitle("")
    onDone()
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-2 px-2 py-1">
      <Input autoFocus placeholder={t("row.addCaseTitle")} value={title}
        onChange={event => setTitle(event.target.value)} className="h-8 text-xs" />
      <Button size="sm" type="submit" disabled={createCase.isPending}>{t("row.addCaseButton")}</Button>
      <Button size="sm" variant="ghost" type="button" onClick={onDone}>{t("row.cancel")}</Button>
    </form>
  )
}

function AddSubSuiteInline({ parentSuiteId, projectId, onDone }) {
  const { t } = useTranslation("suites")
  const [name, setName] = useState("")
  const createSuite = useCreateSuite(projectId)

  const handleSubmit = async (event) => {
    event.preventDefault()
    if (!name.trim()) return
    await createSuite.mutateAsync({ name: name.trim(), parent_suite_id: parentSuiteId })
    toast.success(t("subSuiteCreated"))
    setName("")
    onDone()
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-2 px-2 py-1">
      <Input autoFocus placeholder={t("subSuiteName")} value={name}
        onChange={event => setName(event.target.value)} className="h-8 text-xs" />
      <Button size="sm" type="submit" disabled={createSuite.isPending}>{t("row.addCaseButton")}</Button>
      <Button size="sm" variant="ghost" type="button" onClick={onDone}>{t("row.cancel")}</Button>
    </form>
  )
}

function SortableCaseRow({ tc, suiteId, deleteCase, selected, toggle }) {
  const { t } = useTranslation("suites")
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({ id: tc.id, activationConstraint: { distance: 5 } })
  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.55 : 1,
  }
  const handleKeyDown = useTreeItemNav({
    onCollapse: () => {
      const parent = document.querySelector(
        `[data-treeitem-kind="suite"][data-suite-id="${suiteId}"]`,
      )
      parent?.focus()
    },
    onToggleSelect: () => toggle(tc.id),
  })
  return (
    <li ref={setNodeRef} style={style}
      className={`flex items-center justify-between rounded px-2 py-1.5 hover:bg-gray-50 dark:hover:bg-gray-800 group transition-colors ${selected.has(tc.id) ? "bg-blue-50" : ""}`}>
      <div className="flex items-center gap-2 min-w-0 flex-1">
        <button {...attributes} {...listeners}
          className="text-gray-300 dark:text-gray-600 hover:text-gray-500 dark:hover:text-gray-400 cursor-grab touch-none shrink-0"
          aria-label={t("row.dragHandle")}>
          <GripVertical size={12} />
        </button>
        <input type="checkbox" checked={selected.has(tc.id)}
          onChange={() => toggle(tc.id)}
          onClick={event => event.stopPropagation()}
          className="cursor-pointer" />
        <Link to={`/cases/${tc.id}`}
          role="treeitem"
          data-treeitem-kind="case"
          data-suite-id={suiteId}
          data-case-id={tc.id}
          onKeyDown={handleKeyDown}
          className="hover:text-gray-900 dark:hover:text-white min-w-0 outline-none focus:ring-2 focus:ring-primary-300 rounded">
          <TestCaseItem tc={tc} />
        </Link>
      </div>
      <button
        onClick={() => deleteCase.mutate(tc.id, { onSuccess: () => toast.success(t("row.caseDeleted")) })}
        className="opacity-0 group-hover:opacity-100 text-gray-400 dark:text-gray-500 hover:text-red-500 shrink-0">
        <Trash2 size={13} />
      </button>
    </li>
  )
}

function CaseList({ suiteId }) {
  const { t } = useTranslation("suites")
  const { id: projectId } = useParams()
  const { data: cases = [] } = useCases(suiteId)
  const deleteCase = useDeleteCase(suiteId)
  const bulkDelete = useBulkDeleteCases(suiteId)
  const reorderCases = useReorderSuiteCases(suiteId)
  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 5 } }))
  const [selected, setSelected] = useState(new Set())
  const [planId, setPlanId] = useState("")

  const { data: plans = [] } = useQuery({
    queryKey: ["plans", projectId],
    queryFn: () => plansApi.list(projectId),
    enabled: !!projectId && selected.size > 0,
  })

  const allIds = useMemo(() => cases.map(c => c.id), [cases])
  const allSelected = cases.length > 0 && selected.size === cases.length

  const toggle = (id) => setSelected(current => {
    const next = new Set(current)
    next.has(id) ? next.delete(id) : next.add(id)
    return next
  })
  const toggleAll = () => setSelected(allSelected ? new Set() : new Set(allIds))
  const clear = () => setSelected(new Set())

  const handleBulkDelete = async () => {
    const ids = [...selected]
    if (!confirm(t("row.bulkDeleteConfirm", { count: ids.length }))) return
    try {
      await bulkDelete.mutateAsync(ids)
      toast.success(t("row.bulkDeleted", { count: ids.length }))
      clear()
    } catch {
      toast.error(t("row.bulkDeleteFailed"))
    }
  }

  const handleAddToPlan = async () => {
    if (!planId) return toast.error(t("row.selectPlan"))
    try {
      await plansApi.addCases(parseInt(planId), [...selected])
      toast.success(t("row.addedToPlan", { count: selected.size }))
      setPlanId("")
      clear()
    } catch {
      toast.error(t("row.addToPlanFailed"))
    }
  }

  if (cases.length === 0)
    return <p className="text-xs text-gray-400 dark:text-gray-500 pl-2 py-1">{t("row.noCases")}</p>

  return (
    <div>
      {cases.length > 1 && (
        <label className="flex items-center gap-2 pl-4 pr-2 py-1 text-xs text-gray-500 dark:text-gray-400 cursor-pointer">
          <input type="checkbox" checked={allSelected}
            onChange={toggleAll}
            ref={el => { if (el) el.indeterminate = selected.size > 0 && !allSelected }} />
          {selected.size > 0 ? t("row.selectedCount", { count: selected.size }) : t("row.selectAll")}
        </label>
      )}
      <DndContext
        sensors={sensors}
        collisionDetection={closestCenter}
        onDragEnd={({ active, over }) => {
          if (!over || active.id === over.id) return
          const oldIdx = cases.findIndex(c => c.id === active.id)
          const newIdx = cases.findIndex(c => c.id === over.id)
          if (oldIdx < 0 || newIdx < 0) return
          const next = [...cases]
          const [moved] = next.splice(oldIdx, 1)
          next.splice(newIdx, 0, moved)
          reorderCases.mutate(next.map(c => c.id))
        }}
      >
        <SortableContext items={cases.map(c => c.id)} strategy={verticalListSortingStrategy}>
          <ul className="pl-4 space-y-0.5">
            {cases.map(tc => (
              <SortableCaseRow key={tc.id} tc={tc} suiteId={suiteId} deleteCase={deleteCase}
                selected={selected} toggle={toggle} />
            ))}
          </ul>
        </SortableContext>
      </DndContext>

      {selected.size > 0 && (
        <div className="ml-4 mt-2 flex items-center gap-2 p-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
          <span className="text-xs font-medium text-gray-600 dark:text-gray-300">
            {t("row.selectedCount", { count: selected.size })}
          </span>
          <Button size="sm" variant="outline" onClick={handleBulkDelete}
            disabled={bulkDelete.isPending}>
            <Trash2 size={12} /> {t("row.deleteButton")}
          </Button>
          {plans.length > 0 && (
            <div className="flex items-center gap-1">
              <Select value={planId} onValueChange={setPlanId}>
                <SelectTrigger className="h-8 text-xs min-w-[140px]">
                  <SelectValue placeholder={t("row.addToPlan")} />
                </SelectTrigger>
                <SelectContent>
                  {plans.map(plan => (
                    <SelectItem key={plan.id} value={String(plan.id)}>{plan.title}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Button size="sm" variant="outline" onClick={handleAddToPlan} disabled={!planId}>
                <ListPlus size={12} /> {t("row.addToPlanButton")}
              </Button>
            </div>
          )}
          <Button size="sm" variant="ghost" onClick={clear} className="ml-auto">
            <X size={12} />
          </Button>
        </div>
      )}
    </div>
  )
}

const SUITE_STEP_STYLE = {
  setup:    "bg-blue-50 text-blue-600 border-blue-200",
  teardown: "bg-orange-50 text-orange-600 border-orange-200",
}

function SortableSuiteStep({ step, stepType, onDelete }) {
  const { t } = useTranslation("suites")
  const style = SUITE_STEP_STYLE[stepType]
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({ id: step.id, activationConstraint: { distance: 5 } })

  const dragStyle = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  }

  return (
    <div ref={setNodeRef} style={dragStyle}
      className={`flex items-start gap-2 border rounded-lg px-3 py-2 ${style}`}>
      <button {...attributes} {...listeners}
        aria-label={t("row.dragHandle")}
        className="text-gray-300 dark:text-gray-600 hover:text-gray-500 dark:hover:text-gray-400 mt-0.5 cursor-grab touch-none">
        <GripVertical size={12} />
      </button>
      <span className="flex-1 text-sm">{step.action}</span>
      <button onClick={onDelete} className="text-gray-300 dark:text-gray-600 hover:text-red-500 shrink-0 mt-0.5">
        <Trash2 size={12} />
      </button>
    </div>
  )
}

function SuiteStepList({ suiteId, projectId, steps, stepType, onRefresh }) {
  const { t } = useTranslation("suites")
  const [newAction, setNewAction] = useState("")
  const reorderSuiteSteps = useReorderSuiteSteps(projectId)
  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 5 } }))

  const addStep = async () => {
    if (!newAction.trim()) return
    const order = steps.filter(step => step.step_type === stepType).length + 1
    await suitesApi.createStep(suiteId, { action: newAction.trim(), step_type: stepType, order })
    setNewAction("")
    onRefresh()
  }

  const deleteStep = async (stepId) => {
    await suitesApi.deleteStep(suiteId, stepId)
    onRefresh()
  }

  const handleDragEnd = ({ active, over }) => {
    if (!over || active.id === over.id) return
    const typeSteps = steps.filter(step => step.step_type === stepType)
    const oldIndex = typeSteps.findIndex(step => step.id === active.id)
    const newIndex = typeSteps.findIndex(step => step.id === over.id)
    const reordered = [...typeSteps]
    const [moved] = reordered.splice(oldIndex, 1)
    reordered.splice(newIndex, 0, moved)
    reorderSuiteSteps.mutate({ suiteId, stepIds: reordered.map(step => step.id) })
  }

  const typeSteps = steps.filter(step => step.step_type === stepType)
  const stepTypeLabel = stepType === "setup" ? t("row.setupLabel") : t("row.teardownLabel")

  return (
    <div className="space-y-1.5">
      <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
        <SortableContext items={typeSteps.map(step => step.id)} strategy={verticalListSortingStrategy}>
          {typeSteps.map(step => (
            <SortableSuiteStep key={step.id} step={step} stepType={stepType}
              onDelete={() => deleteStep(step.id)} />
          ))}
        </SortableContext>
      </DndContext>
      <div className="flex gap-2">
        <Input value={newAction} onChange={event => setNewAction(event.target.value)}
          placeholder={t("row.addStep", { stepType: stepTypeLabel })} className="h-8 text-xs"
          onKeyDown={event => event.key === "Enter" && addStep()} />
        <Button size="sm" variant="outline" onClick={addStep} disabled={!newAction.trim()}>
          <Plus size={12} />
        </Button>
      </div>
    </div>
  )
}

function SuiteEditPanel({ suite, projectId, onClose, updateSuite }) {
  const { t } = useTranslation("suites")
  const [name, setName] = useState(suite.name)
  const [description, setDescription] = useState(suite.description ?? "")
  const [tagsInput, setTagsInput] = useState((suite.tags ?? []).join(", "))
  const qc = useQueryClient()

  const refresh = () => qc.invalidateQueries({ queryKey: ["suites-list", projectId] })

  const handleSave = async () => {
    const trimmed = name.trim()
    if (!trimmed) return
    const tags = tagsInput.split(",").map(tag => tag.trim()).filter(Boolean)
    await updateSuite.mutateAsync({
      id: suite.id,
      data: { name: trimmed, description: description || null, tags },
    })
    toast.success(t("saved"))
    onClose()
  }

  return (
    <div className="border-t bg-white dark:bg-gray-900 px-4 py-4 space-y-4" onClick={event => event.stopPropagation()}>
      <div className="space-y-1">
        <p className="text-xs text-gray-500 dark:text-gray-400">{t("row.name")}</p>
        <Input value={name} onChange={event => setName(event.target.value)} />
      </div>
      <div className="space-y-1">
        <p className="text-xs text-gray-500 dark:text-gray-400">{t("row.description")}</p>
        <MdEditor value={description} onChange={setDescription} height={80} />
      </div>
      <div className="space-y-1">
        <p className="text-xs text-gray-500 dark:text-gray-400">{t("row.tagsLabel")} <span className="text-gray-400 dark:text-gray-500">{t("row.tagsHint")}</span></p>
        <Input value={tagsInput} onChange={event => setTagsInput(event.target.value)} placeholder={t("row.tagsPlaceholder")} />
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-1.5">
          <p className="text-xs font-semibold text-blue-600 uppercase tracking-wide">{t("row.suiteSetup")}</p>
          <SuiteStepList suiteId={suite.id} projectId={projectId} steps={suite.steps ?? []} stepType="setup" onRefresh={refresh} />
        </div>
        <div className="space-y-1.5">
          <p className="text-xs font-semibold text-orange-600 uppercase tracking-wide">{t("row.suiteTeardown")}</p>
          <SuiteStepList suiteId={suite.id} projectId={projectId} steps={suite.steps ?? []} stepType="teardown" onRefresh={refresh} />
        </div>
      </div>
      <div className="flex gap-2">
        <Button size="sm" onClick={handleSave} loading={updateSuite.isPending}>{t("row.save")}</Button>
        <Button size="sm" variant="ghost" onClick={onClose}>{t("row.cancel")}</Button>
      </div>
    </div>
  )
}

function SortableChildSuite({ suite, projectId }) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({ id: suite.id, activationConstraint: { distance: 5 } })
  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.55 : 1,
  }
  return (
    <div ref={setNodeRef} style={style}>
      <SuiteRow suite={suite} projectId={projectId} dragHandleProps={{ ...attributes, ...listeners }} />
    </div>
  )
}

function ChildSuites({ projectId, parentSuiteId }) {
  const { data: children = [] } = useChildSuites(projectId, parentSuiteId)
  const reorderSuites = useReorderProjectSuites(projectId)
  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 5 } }))
  if (children.length === 0) return null
  return (
    <div className="pl-4 mt-2 space-y-2 border-l-2 border-gray-100 dark:border-gray-800">
      <DndContext
        sensors={sensors}
        collisionDetection={closestCenter}
        onDragEnd={({ active, over }) => {
          if (!over || active.id === over.id) return
          const oldIdx = children.findIndex(suite => suite.id === active.id)
          const newIdx = children.findIndex(suite => suite.id === over.id)
          if (oldIdx < 0 || newIdx < 0) return
          const next = [...children]
          const [moved] = next.splice(oldIdx, 1)
          next.splice(newIdx, 0, moved)
          reorderSuites.mutate({ suiteIds: next.map(suite => suite.id), parentSuiteId })
        }}
      >
        <SortableContext items={children.map(suite => suite.id)} strategy={verticalListSortingStrategy}>
          {children.map(child => (
            <SortableChildSuite key={child.id} suite={child} projectId={projectId} />
          ))}
        </SortableContext>
      </DndContext>
    </div>
  )
}

export function SuiteRow({ suite, projectId, dragHandleProps }) {
  const { t } = useTranslation("suites")
  const { version, desiredOpen } = useContext(SuiteCollapseContext)
  const [open, setOpen] = useState(desiredOpen)
  useEffect(() => {
    if (version > 0) setOpen(desiredOpen)
  }, [version, desiredOpen])
  const [addingCase, setAddingCase] = useState(false)
  const [addingSuite, setAddingSuite] = useState(false)
  const [editing, setEditing] = useState(false)
  const deleteSuite = useDeleteSuite(projectId)
  const archiveSuite = useArchiveSuite(projectId)
  const updateSuite = useUpdateSuite(projectId)
  const [deleteImpact, setDeleteImpact] = useState(null)
  const [confirmOpen, setConfirmOpen] = useState(false)
  const handleDeleteClick = async () => {
    try {
      const impact = await suitesApi.deleteImpact(suite.id)
      if (impact.result_count > 0) {
        setDeleteImpact(impact)
        setConfirmOpen(true)
        return
      }
    } catch {
      // fall through to plain delete on impact failure
    }
    deleteSuite.mutate(suite.id, { onSuccess: () => toast.success(t("deleted")) })
  }
  const handleArchiveConfirmed = () => {
    archiveSuite.mutate(suite.id, {
      onSuccess: () => {
        toast.success(t("archived"))
        setConfirmOpen(false)
      },
      onError: () => toast.error(t("archiveFailed")),
    })
  }
  const handleDeleteConfirmed = () => {
    deleteSuite.mutate(suite.id, {
      onSuccess: () => {
        toast.success(t("deleted"))
        setConfirmOpen(false)
      },
    })
  }

  const toggleOpen = () => setOpen(value => !value)
  const handleKeyDown = useTreeItemNav({
    onCollapse: () => { if (open) setOpen(false) },
    onExpand: () => { if (!open) setOpen(true) },
    onActivate: toggleOpen,
    onToggleSelect: toggleOpen,
    ignoreUnlessSelfTarget: true,
  })

  return (
    <div className="border rounded-lg overflow-hidden">
      <div className="flex items-center justify-between px-3 py-2 bg-gray-50 dark:bg-gray-900 hover:bg-gray-100 dark:hover:bg-gray-800 cursor-pointer focus:outline-none focus:ring-2 focus:ring-primary-300"
        role="treeitem"
        tabIndex={0}
        aria-expanded={open}
        aria-label={suite.name}
        data-treeitem-kind="suite"
        data-suite-id={suite.id}
        onKeyDown={handleKeyDown}
        onClick={() => setOpen(value => !value)}>
        <div className="flex items-center gap-2 font-medium text-sm text-gray-800 dark:text-gray-100 flex-1 min-w-0">
          {dragHandleProps && (
            <button {...dragHandleProps} onClick={event => event.stopPropagation()}
              className="text-gray-300 dark:text-gray-600 hover:text-gray-500 dark:hover:text-gray-400 cursor-grab touch-none shrink-0"
              aria-label={t("row.dragReorder")}>
              <GripVertical size={14} />
            </button>
          )}
          <ChevronRight size={14} className={`transition-transform shrink-0 ${open ? "rotate-90" : ""}`} />
          <FolderOpen size={14} className="text-yellow-500 shrink-0" />
          <span className="truncate">{suite.name}</span>
          <span className="text-xs text-gray-400 dark:text-gray-500 shrink-0">({suite.test_case_ids?.length ?? 0})</span>
          {(suite.tags ?? []).map(tag => (
            <span key={tag} className="text-xs bg-blue-50 text-blue-600 border border-blue-200 px-1.5 py-0.5 rounded-full shrink-0">{tag}</span>
          ))}
        </div>
        <div className="flex gap-1 shrink-0" onClick={event => event.stopPropagation()}>
          <Button size="sm" variant="ghost" onClick={() => setEditing(value => !value)}>
            <Pencil size={13} />
          </Button>
          <Button size="sm" variant="ghost" onClick={() => { setAddingSuite(value => !value); setAddingCase(false) }}>
            <Plus size={13} /> {t("row.addSuite")}
          </Button>
          <Button size="sm" variant="ghost" onClick={() => { setAddingCase(value => !value); setAddingSuite(false) }}>
            <Plus size={13} /> {t("row.addCase")}
          </Button>
          <Button size="sm" variant="ghost" onClick={handleDeleteClick}>
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
            <div className="px-2 pt-2 pb-1 text-xs text-gray-500 dark:text-gray-400 prose prose-sm">
              <MdViewer value={suite.description} />
            </div>
          )}
          {(suite.steps ?? []).length > 0 && (
            <div className="flex gap-4 px-2 pb-2 text-xs text-gray-500 dark:text-gray-400">
              {["setup", "teardown"].map(stepType => {
                const typeSteps = suite.steps.filter(step => step.step_type === stepType)
                if (!typeSteps.length) return null
                const color = stepType === "setup" ? "text-blue-600" : "text-orange-600"
                const label = stepType === "setup" ? t("row.setupLabel") : t("row.teardownLabel")
                return (
                  <div key={stepType}>
                    <span className={`font-medium ${color}`}>{label}:</span>{" "}
                    {typeSteps.map(step => step.action).join(" → ")}
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
      <DeleteSuiteDialog
        open={confirmOpen}
        impact={deleteImpact}
        onCancel={() => setConfirmOpen(false)}
        onArchive={handleArchiveConfirmed}
        onDelete={handleDeleteConfirmed}
        archiving={archiveSuite.isPending}
        deleting={deleteSuite.isPending}
      />
    </div>
  )
}

function DeleteSuiteDialog({ open, impact, onCancel, onArchive, onDelete, archiving, deleting }) {
  const { t } = useTranslation("suites")
  const hasResults = (impact?.result_count ?? 0) > 0
  return (
    <Dialog open={open} onOpenChange={(value) => { if (!value) onCancel() }}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{t("confirmDelete.title")}</DialogTitle>
          <DialogDescription>
            {hasResults
              ? t("confirmDelete.impactWithResults", {
                  caseCount: impact?.case_count ?? 0,
                  resultCount: impact?.result_count ?? 0,
                  executionCount: impact?.execution_count ?? 0,
                })
              : t("confirmDelete.impactNoResults")}
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="destructive" onClick={onDelete} disabled={deleting}>
            {t("confirmDelete.delete")}
          </Button>
          {hasResults && (
            <Button onClick={onArchive} disabled={archiving}>
              {t("confirmDelete.archive")}
            </Button>
          )}
          <Button variant="ghost" onClick={onCancel}>
            {t("confirmDelete.cancel")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
