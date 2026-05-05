import { useState } from "react"
import { useParams } from "react-router-dom"
import { Plus, FolderOpen, PlayCircle, Tag, Clock } from "lucide-react"
import { useProject } from "../hooks/useProjects"
import { useSuites, useCreateSuite } from "../hooks/useSuites"
import { Button } from "../components/ui/button"
import { Input } from "../components/ui/input"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "../components/ui/tabs"
import { EmptyState } from "../components/ui/empty-state"
import { Skeleton, SkeletonList } from "../components/ui/skeleton"
import { Breadcrumbs } from "../components/ui/breadcrumbs"
import { SuiteRow } from "../components/project/SuiteRow"
import { VersionsPanel } from "../components/project/VersionsPanel"
import { toast } from "sonner"

export function ProjectDetailPage() {
  const { id } = useParams()
  const { data: project } = useProject(id)
  const { data: suites = [], isLoading } = useSuites(id)
  const createSuite = useCreateSuite(id)
  const [newSuite, setNewSuite] = useState("")

  const handleCreateSuite = async (e) => {
    e.preventDefault()
    if (!newSuite.trim()) return
    await createSuite.mutateAsync({ name: newSuite.trim() })
    toast.success("Suite created")
    setNewSuite("")
  }

  if (isLoading) {
    return (
      <div className="max-w-2xl space-y-4">
        <Skeleton className="h-7 w-1/3" />
        <Skeleton className="h-4 w-2/3" />
        <SkeletonList count={3} itemClassName="h-12" />
      </div>
    )
  }

  return (
    <div className="max-w-2xl space-y-6">
      <Breadcrumbs crumbs={[{ label: "Projects", to: "/projects" }, { label: project?.name ?? "…" }]} />
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">{project?.name}</h1>
          {project?.description && <p className="text-sm text-gray-500 mt-0.5">{project.description}</p>}
          <div className="flex items-center gap-4 mt-2 text-xs text-gray-400">
            <span className="flex items-center gap-1">
              <FolderOpen size={12} />
              {project?.suite_count ?? 0} {project?.suite_count === 1 ? "suite" : "suites"} · {project?.case_count ?? 0} {project?.case_count === 1 ? "case" : "cases"}
            </span>
            <span className="flex items-center gap-1">
              <PlayCircle size={12} />
              {project?.execution_count ?? 0} {project?.execution_count === 1 ? "execution" : "executions"}
              {project?.last_execution_at && (
                <span className="flex items-center gap-1 ml-1">
                  <Clock size={10} />
                  {new Date(project.last_execution_at).toLocaleDateString(undefined, { month: "short", day: "numeric" })}
                </span>
              )}
            </span>
          </div>
        </div>
      </div>

      <Tabs defaultValue="suites">
        <TabsList>
          <TabsTrigger value="suites"><FolderOpen size={13} className="mr-1" /> Test suites</TabsTrigger>
          <TabsTrigger value="versions"><Tag size={13} className="mr-1" /> Versions</TabsTrigger>
        </TabsList>

        <TabsContent value="suites" className="mt-4 space-y-4">
          <form onSubmit={handleCreateSuite} className="flex gap-2">
            <Input placeholder="New suite name…" value={newSuite} onChange={e => setNewSuite(e.target.value)} />
            <Button type="submit" disabled={createSuite.isPending}><Plus size={14} /> Suite</Button>
          </form>
          <div className="space-y-2">
            {suites.map(suite => <SuiteRow key={suite.id} suite={suite} projectId={id} />)}
            {suites.length === 0 && (
              <EmptyState
                icon={FolderOpen}
                title="No test suites yet"
                description="Suites group related test cases. Create one above to organise your tests."
              />
            )}
          </div>
        </TabsContent>

        <TabsContent value="versions" className="mt-4">
          <VersionsPanel projectId={id} />
        </TabsContent>
      </Tabs>
    </div>
  )
}
