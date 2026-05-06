import { useState } from "react"
import { Link, useParams } from "react-router-dom"
import { Plus, FolderOpen, PlayCircle, Clock, FileText, Search } from "lucide-react"
import { DndContext, closestCenter, PointerSensor, useSensor, useSensors } from "@dnd-kit/core"
import { SortableContext, verticalListSortingStrategy, useSortable } from "@dnd-kit/sortable"
import { CSS } from "@dnd-kit/utilities"
import { useProject } from "../hooks/useProjects"
import { useSuites, useCreateSuite, useSearchCases, useReorderProjectSuites } from "../hooks/useSuites"
import { useDebounced } from "../hooks/useDebounced"
import { Button } from "../components/ui/button"
import { Input } from "../components/ui/input"
import { SearchInput } from "../components/ui/search-input"
import { PageHeader, PageBody } from "../components/ui/page-header"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "../components/ui/dialog"
import { EmptyState } from "../components/ui/empty-state"
import { Skeleton, SkeletonList } from "../components/ui/skeleton"
import { SuiteRow } from "../components/project/SuiteRow"
import { toast } from "sonner"

function SortableSuite({ suite, projectId }) {
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

function CreateSuiteDialog({ projectId }) {
  const createSuite = useCreateSuite(projectId)
  const [open, setOpen] = useState(false)
  const [name, setName] = useState("")

  const submit = async (e) => {
    e.preventDefault()
    if (!name.trim()) return
    await createSuite.mutateAsync({ name: name.trim() })
    toast.success("Suite created")
    setName("")
    setOpen(false)
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm"><Plus size={14} /> New suite</Button>
      </DialogTrigger>
      <DialogContent className="max-w-md">
        <DialogHeader><DialogTitle>New test suite</DialogTitle></DialogHeader>
        <form onSubmit={submit} className="space-y-3">
          <Input autoFocus placeholder="Suite name…" value={name}
            onChange={e => setName(e.target.value)} />
          <Button type="submit" className="w-full" disabled={!name.trim() || createSuite.isPending}>
            Create suite
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  )
}

export function ProjectDetailPage() {
  const { id } = useParams()
  const { data: project } = useProject(id)
  const { data: suites = [], isLoading } = useSuites(id)
  const reorderSuites = useReorderProjectSuites(id)
  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 5 } }))
  const [search, setSearch] = useState("")
  const debouncedSearch = useDebounced(search, 200)
  const { data: searchResults = [], isFetching: searching } = useSearchCases(id, { q: debouncedSearch })
  const isSearching = debouncedSearch.trim().length > 0

  if (isLoading) {
    return (
      <PageBody>
        <div className="max-w-2xl space-y-4">
          <Skeleton className="h-7 w-1/3" />
          <Skeleton className="h-4 w-2/3" />
          <SkeletonList count={3} itemClassName="h-12" />
        </div>
      </PageBody>
    )
  }

  const suiteCount = project?.suite_count ?? 0
  const caseCount = project?.case_count ?? 0
  const execCount = project?.execution_count ?? 0

  return (
    <>
      <PageHeader crumbs={[{ label: "Projects", to: "/projects" }, { label: project?.name ?? "…" }]}>
        <div className="max-w-2xl space-y-3">
          <div className="flex items-center justify-between gap-4">
            <div className="min-w-0">
              <h1 className="text-2xl font-bold text-gray-800 truncate">{project?.name}</h1>
              <div className="flex flex-wrap items-center gap-x-3 gap-y-0.5 mt-0.5 text-xs text-gray-400">
                <span className="flex items-center gap-1">
                  <FolderOpen size={12} />
                  {suiteCount} {suiteCount === 1 ? "suite" : "suites"} · {caseCount} {caseCount === 1 ? "case" : "cases"}
                </span>
                <span className="flex items-center gap-1">
                  <PlayCircle size={12} />
                  {execCount} {execCount === 1 ? "execution" : "executions"}
                </span>
                {project?.last_execution_at && (
                  <span className="flex items-center gap-1">
                    <Clock size={10} />
                    {new Date(project.last_execution_at).toLocaleDateString(undefined, { month: "short", day: "numeric" })}
                  </span>
                )}
              </div>
            </div>
            <CreateSuiteDialog projectId={id} />
          </div>
          <SearchInput value={search} onChange={setSearch}
            placeholder="Search test cases by name or description…" />
        </div>
      </PageHeader>

      <PageBody>
        <div className="max-w-2xl space-y-4">
          {isSearching ? (
            <div className="space-y-2">
              {searching && searchResults.length === 0 ? (
                <SkeletonList count={3} itemClassName="h-10" />
              ) : searchResults.length === 0 ? (
                <EmptyState
                  icon={Search}
                  title="No test cases match"
                  description={`No cases found for “${debouncedSearch}”.`}
                />
              ) : (
                <ul className="divide-y divide-gray-100 border border-gray-200 rounded-md bg-white">
                  {searchResults.map(tc => (
                    <li key={tc.id}>
                      <Link
                        to={`/cases/${tc.id}`}
                        className="flex items-start gap-2 px-3 py-2 hover:bg-gray-50"
                      >
                        <FileText size={14} className="text-gray-400 mt-0.5 shrink-0" />
                        <div className="min-w-0 flex-1">
                          <div className="text-sm font-medium text-gray-800 truncate">{tc.name}</div>
                          {tc.description && (
                            <div className="text-xs text-gray-500 truncate">{tc.description}</div>
                          )}
                          {tc.tags && tc.tags.length > 0 && (
                            <div className="flex flex-wrap gap-1 mt-1">
                              {tc.tags.map(t => (
                                <span key={t} className="text-[10px] px-1.5 py-0.5 rounded bg-gray-100 text-gray-600">{t}</span>
                              ))}
                            </div>
                          )}
                        </div>
                      </Link>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          ) : (
            <DndContext
              sensors={sensors}
              collisionDetection={closestCenter}
              onDragEnd={(e) => {
                const { active, over } = e
                if (!over || active.id === over.id) return
                const oldIdx = suites.findIndex(s => s.id === active.id)
                const newIdx = suites.findIndex(s => s.id === over.id)
                if (oldIdx < 0 || newIdx < 0) return
                const next = [...suites]
                const [moved] = next.splice(oldIdx, 1)
                next.splice(newIdx, 0, moved)
                reorderSuites.mutate({ suiteIds: next.map(s => s.id), parentSuiteId: null })
              }}
            >
              <SortableContext items={suites.map(s => s.id)} strategy={verticalListSortingStrategy}>
                <div className="space-y-2">
                  {suites.map(suite => <SortableSuite key={suite.id} suite={suite} projectId={id} />)}
                  {suites.length === 0 && (
                    <EmptyState
                      icon={FolderOpen}
                      title="No test suites yet"
                      description="Suites group related test cases. Use “New suite” above to create your first one."
                    />
                  )}
                </div>
              </SortableContext>
            </DndContext>
          )}
        </div>
      </PageBody>
    </>
  )
}
