import { useTranslation } from "react-i18next"

import { CustomFieldsPanel } from "../customField/CustomFieldsPanel"

export function CustomFieldsTab({ projectId }) {
  const { t } = useTranslation("projectSettings")
  return (
    <div className="space-y-4">
      <header>
        <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">{t("customFields.title")}</h2>
        <p className="text-sm text-gray-500 dark:text-gray-400">{t("customFields.description")}</p>
      </header>
      <CustomFieldsPanel projectId={projectId} />
    </div>
  )
}
