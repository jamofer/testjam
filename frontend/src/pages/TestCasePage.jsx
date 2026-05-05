import { useState } from "react"
import { useParams } from "react-router-dom"
import { Plus, Trash2, GripVertical, Upload, Copy, ExternalLink } from "lucide-react"
import { useCase, useUpdateCase, useReorderSteps, useSuite } from "../hooks/useSuites"
import { useProject } from "../hooks/useProjects"
import { casesApi } from "../api/testcases"
import { useQueryClient } from "@tanstack/react-query"
import { DndContext, closestCenter, PointerSensor, useSensor, useSensors } from "@dnd-kit/core"
import { SortableContext, verticalListSortingStrategy, useSortable } from "@dnd-kit/sortable"
import { CSS } from "@dnd-kit/utilities"
import { MdEditor, MdViewer } from "../components/MdEditor"
import { Button } from "../components/ui/button"
import { Input } from "../components/ui/input"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "../components/ui/tabs"
import { EmptyState } from "../components/ui/empty-state"
import { Breadcrumbs } from "../components/ui/breadcrumbs"
import { toast } from "sonner"

const STEP_TYPE_STYLE = {
  setup:    "bg-blue-50 text-blue-600 border-blue-200",
  action:   "bg-gray-50 text-gray-500 border-gray-200",
  teardown: "bg-orange-50 text-orange-600 border-orange-200",
}

function SortableStepRow({ step, caseId, onDelete }) {
  const [editing, setEditing] = useState(false)
  const [action, setAction] = useState(step.action)
  const [expected, setExpected] = useState(step.expected_result ?? "")
  const qc = useQueryClient()

  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({ id: step.id, activationConstraint: { distance: 5 } })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  }

  const save = async () => {
    await casesApi.updateStep(caseId, step.id, { action, expected_result: expected, order: step.order })
    qc.invalidateQueries({ queryKey: ["case", caseId] })
    setEditing(false)
    toast.success("Step saved")
  }

  const typeStyle = STEP_TYPE_STYLE[step.step_type] ?? STEP_TYPE_STYLE.action

  return (
    <div ref={setNodeRef} style={style} className="border rounded-lg p-3 space-y-2 bg-white">
      <div className="flex items-start gap-2">
        <button {...attributes} {...listeners} className="text-gray-300 hover:text-gray-500 mt-1 cursor-grab touch-none">
          <GripVertical size={14} />
        </button>
        <span className="text-xs font-mono text-gray-400 mt-1 w-6">{step.order}.</span>
        <span className={`text-xs px-1.5 py-0.5 rounded border mt-0.5 shrink-0 ${typeStyle}`}>
          {step.step_type}
        </span>
        <div className="flex-1">
          {editing ? (
            <div className="space-y-2">
              <div>
                <p className="text-xs text-gray-500 mb-1">Step</p>
                <MdEditor value={action} onChange={setAction} height={120} />
              </div>
              <div>
                <p className="text-xs text-gray-500 mb-1">Expected result</p>
                <MdEditor value={expected} onChange={setExpected} height={80} />
              </div>
              <div className="flex gap-2">
                <Button size="sm" onClick={save}>Save</Button>
                <Button size="sm" variant="ghost" onClick={() => setEditing(false)}>Cancel</Button>
              </div>
            </div>
          ) : (
            <div className="cursor-pointer" onClick={() => setEditing(true)}>
              <div className="prose prose-sm text-gray-800"><MdViewer value={step.action} /></div>
              {step.expected_result && (
                <div className="mt-1 text-xs text-gray-400 italic">
                  Expected: <MdViewer value={step.expected_result} />
                </div>
              )}
            </div>
          )}
        </div>
        <button onClick={onDelete} className="text-gray-300 hover:text-red-500 mt-1">
          <Trash2 size={13} />
        </button>
      </div>
    </div>
  )
}

function AttachmentList({ caseId, attachments }) {
  const qc = useQueryClient()

  const handleUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    await casesApi.uploadAttachment(caseId, file)
    qc.invalidateQueries({ queryKey: ["case", caseId] })
    toast.success(`${file.name} uploaded`)
    e.target.value = ""
  }

  const handleDelete = async (attachmentId) => {
    await casesApi.deleteAttachment(caseId, attachmentId)
    qc.invalidateQueries({ queryKey: ["case", caseId] })
    toast.success("Attachment deleted")
  }

  const copyUrl = (att) => {
    const url = `${window.location.origin}${att.url}`
    navigator.clipboard.writeText(url)
    toast.success("URL copied")
  }

  const copyMarkdown = (att) => {
    const url = `${window.location.origin}${att.url}`
    const md = att.content_type?.startsWith("image/")
      ? `![${att.filename}](${url})`
      : `[${att.filename}](${url})`
    navigator.clipboard.writeText(md)
    toast.success("Markdown copied")
  }

  return (
    <div className="space-y-3">
      <label className="flex items-center gap-2 cursor-pointer w-fit">
        <input type="file" className="hidden" onChange={handleUpload} />
        <Button variant="outline" size="sm" asChild>
          <span><Upload size={13} /> Upload file</span>
        </Button>
      </label>
      {attachments.length === 0 && (
        <EmptyState
          icon={Upload}
          title="No attachments"
          description="Attach screenshots, logs or other supporting files."
          compact
        />
      )}
      <ul className="space-y-1.5">
        {attachments.map(att => (
          <li key={att.id} className="flex items-center gap-2 text-sm bg-gray-50 rounded-lg px-3 py-2">
            <span className="text-xs bg-white border px-1.5 py-0.5 rounded text-gray-500 shrink-0">
              {att.content_type ?? "file"}
            </span>
            <a href={att.url} target="_blank" rel="noopener noreferrer"
              className="flex items-center gap-1 text-gray-700 hover:text-primary-600 min-w-0 flex-1 truncate">
              {att.filename}
              <ExternalLink size={11} className="shrink-0" />
            </a>
            <span className="text-xs text-gray-400 shrink-0">
              {att.size_bytes ? `${Math.round(att.size_bytes / 1024)} KB` : ""}
            </span>
            <button onClick={() => copyUrl(att)} title="Copy URL" className="text-gray-400 hover:text-gray-700 shrink-0">
              <Copy size={13} />
            </button>
            <button onClick={() => copyMarkdown(att)} title="Copy as Markdown"
              className="text-xs text-gray-400 hover:text-gray-700 font-mono shrink-0">MD</button>
            <button onClick={() => handleDelete(att.id)} title="Delete"
              className="text-gray-300 hover:text-red-500 shrink-0">
              <Trash2 size={13} />
            </button>
          </li>
        ))}
      </ul>
    </div>
  )
}

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
    setNewStepContent("")
    toast.success("Step added")
  }

  const deleteStep = async (stepId) => {
    await casesApi.deleteStep(id, stepId)
    qc.invalidateQueries({ queryKey: ["case", id] })
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

  return (
    <div className="max-w-2xl space-y-6">
      <Breadcrumbs crumbs={[
        { label: "Projects", to: "/projects" },
        { label: project?.name ?? "…", to: `/projects/${suite?.project_id}` },
        { label: tc?.name },
      ]} />

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
        <div className="flex items-start justify-between gap-2">
          <div className="cursor-pointer group flex-1" onClick={startEditMeta}>
            <h1 className="text-2xl font-bold text-gray-800 group-hover:text-gray-600">{tc.name}</h1>
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
        </div>
      )}

      <Tabs defaultValue="steps">
        <TabsList>
          <TabsTrigger value="steps">Steps ({tc.steps?.length ?? 0})</TabsTrigger>
          <TabsTrigger value="attachments">Attachments ({tc.attachments?.length ?? 0})</TabsTrigger>
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
      </Tabs>
    </div>
  )
}
