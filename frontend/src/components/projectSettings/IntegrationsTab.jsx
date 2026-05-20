import { useTranslation } from "react-i18next"

import { ExternalTrackersSection } from "../integration/ExternalTrackersSection"

export function IntegrationsTab({ projectId }) {
  const { t } = useTranslation("projectSettings")
  return (
    <div className="space-y-4">
      <header>
        <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">{t("integrations.title")}</h2>
        <p className="text-sm text-gray-500 dark:text-gray-400">{t("integrations.description")}</p>
      </header>
      <ExternalTrackersSection projectId={projectId} />
    </div>
  )
}
