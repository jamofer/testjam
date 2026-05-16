import { useState } from "react"
import { Link, useParams } from "react-router-dom"
import { Download, FolderOpen, PlayCircle } from "lucide-react"

import { useProject } from "../hooks/useProjects"
import { projectsApi } from "../api/projects"
import { Button } from "../components/ui/button"
import { PageBody, PageHeader } from "../components/ui/page-header"
import { Skeleton } from "../components/ui/skeleton"
import { ProjectDashboard } from "../components/dashboard/ProjectDashboard"
import { ImportExecutionDialog } from "../components/execution/ImportExecutionDialog"
import { toast } from "sonner"

export function ProjectDetailPage() {
  const { id } = useParams()
  const { data: project, isLoading } = useProject(id)
  const [range, setRange] = useState(30)

  if (isLoading) {
    return (
      <PageBody>
        <div className="max-w-4xl xl:max-w-5xl 2xl:max-w-6xl space-y-4">
          <Skeleton className="h-7 w-1/3" />
          <Skeleton className="h-40 w-full" />
        </div>
      </PageBody>
    )
  }

  return (
    <>
      <PageHeader crumbs={[{ label: "Projects", to: "/projects" }, { label: project?.name ?? "…" }]}>
        <div className="max-w-4xl xl:max-w-5xl 2xl:max-w-6xl space-y-3">
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between md:gap-4">
            <div className="min-w-0">
              <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-100 break-words md:truncate">{project?.name}</h1>
              {project?.description && (
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5 line-clamp-2">{project.description}</p>
              )}
            </div>
            <ProjectActions projectId={id} />
          </div>
        </div>
      </PageHeader>

      <PageBody>
        <div className="max-w-4xl xl:max-w-5xl 2xl:max-w-6xl space-y-6">
          <ProjectDashboard projectId={id} range={range} onRangeChange={setRange} />
        </div>
      </PageBody>
    </>
  )
}

function ProjectActions({ projectId }) {
  const [downloading, setDownloading] = useState(false)

  const exportZip = async () => {
    setDownloading(true)
    try {
      await projectsApi.exportZip(projectId)
      toast.success("Project exported")
    } catch {
      toast.error("Export failed")
    } finally {
      setDownloading(false)
    }
  }

  return (
    <div className="flex flex-wrap items-center gap-2">
      <Button asChild size="sm">
        <Link to={`/projects/${projectId}/executions/new`}>
          <PlayCircle size={14} /> New execution
        </Link>
      </Button>
      <Button asChild size="sm" variant="outline">
        <Link to={`/projects/${projectId}/cases`}>
          <FolderOpen size={14} /> Test cases
        </Link>
      </Button>
      <ImportExecutionDialog projectId={projectId} />
      <Button size="sm" variant="ghost" onClick={exportZip} loading={downloading} title="Download project as ZIP">
        <Download size={14} /> Export
      </Button>
    </div>
  )
}
