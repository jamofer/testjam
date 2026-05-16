import { useParams } from "react-router-dom"
import { useProject } from "../hooks/useProjects"
import { PageHeader, PageBody } from "../components/ui/page-header"
import { VersionsPanel } from "../components/project/VersionsPanel"

export function VersionsPage() {
  const { id: projectId } = useParams()
  const { data: project } = useProject(projectId)

  return (
    <>
      <PageHeader crumbs={[
        { label: "Projects", to: "/projects" },
        { label: project?.name ?? "…", to: `/projects/${projectId}` },
        { label: "Versions" },
      ]}>
        <div className="max-w-2xl xl:max-w-4xl 2xl:max-w-5xl">
          <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-100">Versions</h1>
        </div>
      </PageHeader>

      <PageBody>
        <div className="max-w-2xl xl:max-w-4xl 2xl:max-w-5xl">
          <VersionsPanel projectId={projectId} />
        </div>
      </PageBody>
    </>
  )
}
