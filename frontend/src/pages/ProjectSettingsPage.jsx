import { useTranslation } from "react-i18next"
import { Navigate, NavLink, Route, Routes, useParams } from "react-router-dom"
import { AlertTriangle, FileText, Plug, Webhook } from "lucide-react"

import { useProject } from "../hooks/useProjects"
import { PageBody, PageHeader } from "../components/ui/page-header"
import { GeneralTab } from "../components/projectSettings/GeneralTab"
import { IntegrationsTab } from "../components/projectSettings/IntegrationsTab"
import { WebhooksTab } from "../components/projectSettings/WebhooksTab"
import { DangerZoneTab } from "../components/projectSettings/DangerZoneTab"

const TABS = [
  { value: "general",      icon: FileText,       labelKey: "tabs.general"      },
  { value: "integrations", icon: Plug,           labelKey: "tabs.integrations" },
  { value: "webhooks",     icon: Webhook,        labelKey: "tabs.webhooks"     },
  { value: "danger",       icon: AlertTriangle,  labelKey: "tabs.danger"       },
]

export function ProjectSettingsPage() {
  const { t } = useTranslation(["projectSettings", "nav"])
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
        <div className="max-w-5xl">
          <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-100">{t("title")}</h1>
        </div>
      </PageHeader>

      <PageBody>
        <div className="max-w-5xl flex flex-col gap-6 md:flex-row">
          <nav className="md:w-56 md:flex-shrink-0">
            <ul className="space-y-0.5">
              {TABS.map(({ value, icon: Icon, labelKey }) => (
                <li key={value}>
                  <NavLink
                    to={`/projects/${projectId}/settings/${value}`}
                    end
                    className={({ isActive }) =>
                      `flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                        isActive
                          ? "bg-primary-50 dark:bg-primary-900/30 text-primary-600 dark:text-primary-300"
                          : "text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800"
                      }`
                    }
                  >
                    <Icon size={15} /> {t(labelKey)}
                  </NavLink>
                </li>
              ))}
            </ul>
          </nav>

          <section className="flex-1 min-w-0">
            <Routes>
              <Route index element={<Navigate to="general" replace />} />
              <Route path="general" element={<GeneralTab projectId={projectId} project={project} />} />
              <Route path="integrations" element={<IntegrationsTab projectId={projectId} />} />
              <Route path="webhooks" element={<WebhooksTab projectId={projectId} />} />
              <Route path="danger" element={<DangerZoneTab projectId={projectId} project={project} />} />
              <Route path="*" element={<Navigate to="general" replace />} />
            </Routes>
          </section>
        </div>
      </PageBody>
    </>
  )
}
