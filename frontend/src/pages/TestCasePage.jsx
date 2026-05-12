import { useState } from "react"
import { useParams, Link } from "react-router-dom"
import { Plus, History, User as UserIcon, Clock } from "lucide-react"
import { useCase, useUpdateCase, useReorderSteps, useSuite } from "../hooks/useSuites"
import { useProject } from "../hooks/useProjects"
import { casesApi } from "../api/testcases"
import { useQueryClient } from "@tanstack/react-query"
import { DndContext, closestCenter, PointerSensor, useSensor, useSensors } from "@dnd-kit/core"
import { SortableContext, verticalListSortingStrategy } from "@dnd-kit/sortable"
import { MdEditor, MdViewer } from "../components/MdEditor"
import { Button } from "../components/ui/button"
import { Input } from "../components/ui/input"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "../components/ui/tabs"
import { PageHeader, PageBody } from "../components/ui/page-header"
import { CaseRevisions } from "../components/case/CaseRevisions"
import { SortableStepRow } from "../components/case/SortableStepRow"
import { AttachmentList } from "../components/case/AttachmentList"
import { PanelAttachments, PanelHistory } from "../components/case/CaseSidePanels"
import { ContextPanel } from "../components/ui/context-panel"
import { fmtDateTime } from "../lib/format"
import { toast } from "sonner"

export function TestCasePage() {
  const { id } = useParams()
  const { data: tc, isLoading } = useCase(id)
  const { data: suite } = useSuite(tc?.suite_id)
  const { data: project } = useProject(suite?.project_id)
  const updateCase = useUpdateCase(id)
  const reorderSteps = useReorderSteps(id)
  const qc = useQueryClient()

  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 5 } }))

  const [editingTitle, setEditingTitle] = useState(false)
  const [title, setTitle] = useState("")
  const [description, setDescription] = useState("")
  const [preconditions, setPreconditions] = useState("")
  const [newStepContent, setNewStepContent] = useState("")

  if (isLoading) return <p className="text-gray-500">Loading…</p>
  if (!tc) return null

  const startEditMeta = () => {
    setTitle(tc.name)
    setDescription(tc.description ?? "")
    setPreconditions(tc.preconditions ?? "")
    setEditingTitle(true)
  }

  const saveMeta = async () => {
    await updateCase.mutateAsync({ name: title, description, preconditions })
    toast.success("Saved")
    setEditingTitle(false)
  }

  const addStep = async () => {
    if (!newStepContent.trim()) return
    const order = (tc.steps?.length ?? 0) + 1
    await casesApi.createStep(id, { action: newStepContent, order })
    qc.invalidateQueries({ queryKey: ["case", id] })
    qc.invalidateQueries({ queryKey: ["case-revisions", id] })
    setNewStepContent("")
    toast.success("Step added")
  }

  const deleteStep = async (stepId) => {
    await casesApi.deleteStep(id, stepId)
    qc.invalidateQueries({ queryKey: ["case", id] })
    qc.invalidateQueries({ queryKey: ["case-revisions", id] })
    toast.success("Step deleted")
  }

  const handleDragEnd = ({ active, over }) => {
    if (!over || active.id === over.id) return
    const steps = tc.steps ?? []
    const oldIndex = steps.findIndex(s => s.id === active.id)
    const newIndex = steps.findIndex(s => s.id === over.id)
    const reordered = [...steps]
    const [moved] = reordered.splice(oldIndex, 1)
    reordered.splice(newIndex, 0, moved)
    reorderSteps.mutate(reordered.map(s => s.id))
  }

  const userLink = (u) => u
    ? <Link to="/users" className="text-primary-600 hover:underline">{u.full_name || u.username}</Link>
    : null

  const contextSections = [
    {
      title: "About",
      rows: [
        { label: "Project", value: project?.name },
        { label: "Suite", value: suite?.name },
        { label: "External ID", value: tc.external_id },
        { label: "Created by", value: userLink(tc.created_by) },
        { label: "Created", value: fmtDateTime(tc.created_at) },
        { label: "Updated by", value: userLink(tc.updated_by) },
        { label: "Updated", value: fmtDateTime(tc.updated_at) },
      ],
    },
    {
      title: "Tags",
      body: (tc.tags ?? []).length > 0 ? (
        <div className="flex flex-wrap gap-1">
          {tc.tags.map(t => (
            <span key={t} className="text-[11px] px-1.5 py-0.5 rounded bg-blue-50 text-blue-600 border border-blue-200">{t}</span>
          ))}
        </div>
      ) : <p className="text-[11px] text-gray-400">No tags</p>,
    },
    {
      title: `Attachments (${tc.attachments?.length ?? 0})`,
      body: <PanelAttachments caseId={id} attachments={tc.attachments ?? []} />,
    },
    {
      title: "History",
      body: <PanelHistory caseId={id} />,
    },
    {
      title: "Counts",
      rows: [
        { label: "Steps", value: tc.steps?.length ?? 0 },
        { label: "Attachments", value: tc.attachments?.length ?? 0 },
      ],
    },
  ]

  return (
    <>
      <PageHeader crumbs={[
        { label: "Projects", to: "/projects" },
        { label: project?.name ?? "…", to: `/projects/${suite?.project_id}` },
        { label: tc?.name },
      ]}>
        <div className="max-w-2xl xl:max-w-4xl 2xl:max-w-5xl">
          {editingTitle ? (
            <div className="space-y-3">
              <Input value={title} onChange={e => setTitle(e.target.value)} className="text-lg font-bold" />
              <div>
                <p className="text-xs text-gray-500 mb-1">Preconditions</p>
                <MdEditor value={preconditions} onChange={setPreconditions} height={80} />
              </div>
              <div>
                <p className="text-xs text-gray-500 mb-1">Description</p>
                <MdEditor value={description} onChange={setDescription} height={120} />
              </div>
              <div className="flex gap-2">
                <Button size="sm" onClick={saveMeta} loading={updateCase.isPending}>Save</Button>
                <Button size="sm" variant="ghost" onClick={() => setEditingTitle(false)}>Cancel</Button>
              </div>
            </div>
          ) : (
            <div className="cursor-pointer group" onClick={startEditMeta}>
              <h1 className="text-2xl font-bold text-gray-800 group-hover:text-gray-600">{tc.name}</h1>
              <div className="flex flex-wrap items-center gap-x-3 gap-y-0.5 mt-1 text-xs text-gray-400">
                {tc.created_by && (
                  <span className="flex items-center gap-1">
                    <UserIcon size={11} /> Created by {tc.created_by.full_name || tc.created_by.username}
                  </span>
                )}
                {tc.created_at && (
                  <span className="flex items-center gap-1">
                    <Clock size={11} /> {fmtDateTime(tc.created_at)}
                  </span>
                )}
                {tc.updated_by && tc.updated_at && tc.updated_at !== tc.created_at && (
                  <span className="flex items-center gap-1">
                    <History size={11} /> Updated by {tc.updated_by.full_name || tc.updated_by.username} · {fmtDateTime(tc.updated_at)}
                  </span>
                )}
              </div>
              {tc.preconditions && (
                <div className="mt-2">
                  <p className="text-xs text-gray-400 uppercase tracking-wide">Preconditions</p>
                  <div className="prose prose-sm mt-1"><MdViewer value={tc.preconditions} /></div>
                </div>
              )}
              {tc.description && (
                <div className="mt-2 prose prose-sm text-gray-600"><MdViewer value={tc.description} /></div>
              )}
              {!tc.preconditions && !tc.description && (
                <p className="text-sm text-gray-400 mt-1">Click to add description…</p>
              )}
            </div>
          )}
        </div>
      </PageHeader>

      <PageBody>
        <div className="flex gap-6">
          <div className="flex-1 min-w-0 max-w-2xl xl:max-w-4xl 2xl:max-w-5xl space-y-6">
            <Tabs defaultValue="steps">
              <TabsList>
                <TabsTrigger value="steps">Steps ({tc.steps?.length ?? 0})</TabsTrigger>
                <TabsTrigger value="attachments">Attachments ({tc.attachments?.length ?? 0})</TabsTrigger>
                <TabsTrigger value="history">History</TabsTrigger>
              </TabsList>

              <TabsContent value="steps">
                <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
                  <SortableContext items={(tc.steps ?? []).map(s => s.id)} strategy={verticalListSortingStrategy}>
                    <div className="space-y-2">
                      {(tc.steps ?? []).map(step => (
                        <SortableStepRow key={step.id} step={step} caseId={id} onDelete={() => deleteStep(step.id)} />
                      ))}
                      <div className="border rounded-lg p-3 space-y-2">
                        <p className="text-xs text-gray-500">New step</p>
                        <MdEditor value={newStepContent} onChange={setNewStepContent} height={100} />
                        <Button size="sm" onClick={addStep} disabled={!newStepContent.trim()}>
                          <Plus size={13} /> Add step
                        </Button>
                      </div>
                    </div>
                  </SortableContext>
                </DndContext>
              </TabsContent>

              <TabsContent value="attachments">
                <AttachmentList caseId={id} attachments={tc.attachments ?? []} />
              </TabsContent>

              <TabsContent value="history">
                <CaseRevisions caseId={id} />
              </TabsContent>
            </Tabs>
          </div>
          <ContextPanel sections={contextSections} />
        </div>
      </PageBody>
    </>
  )
}
