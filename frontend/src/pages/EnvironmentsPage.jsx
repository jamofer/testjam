import { useParams } from "react-router-dom"
import { useTranslation } from "react-i18next"
import { useProject } from "../hooks/useProjects"
import { PageHeader, PageBody } from "../components/ui/page-header"
import { EnvironmentsPanel } from "../components/project/EnvironmentsPanel"

export function EnvironmentsPage() {
  const { t } = useTranslation(["environments", "nav"])
  const { id: projectId } = useParams()
  const { data: project } = useProject(projectId)

  return (
    <>
      <PageHeader
        crumbs={[
          { label: t("nav:global.projects"), to: "/projects" },
          { label: project?.name ?? "…", to: `/projects/${projectId}` },
          { label: t("title") },
        ]}
      >
        <div className="max-w-2xl xl:max-w-4xl 2xl:max-w-5xl flex items-center justify-between gap-3 flex-wrap">
          <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-100">{t("title")}</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">{t("subtitle")}</p>
        </div>
      </PageHeader>

      <PageBody>
        <div className="max-w-2xl xl:max-w-4xl 2xl:max-w-5xl">
          <EnvironmentsPanel projectId={projectId} />
        </div>
      </PageBody>
    </>
  )
}
