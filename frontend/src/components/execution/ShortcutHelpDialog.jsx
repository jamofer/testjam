import { useTranslation } from "react-i18next"
import { ShortcutsDialog } from "../ui/shortcuts-dialog"
import { STATUS_CONFIG } from "../../lib/statusConfig"

export const SHORTCUT_TO_STATUS = { p: "passed", f: "failed", b: "blocked", n: "not_run" }

export function ShortcutHelpDialog({ open, onOpenChange, isAutomated }) {
  const { t } = useTranslation(["executions", "common"])
  const statusLabel = (status) => t(`common:status.${status}`, STATUS_CONFIG[status]?.label ?? status)

  const navigationRows = [
    { keys: ["j", "↓"], description: t("run.shortcuts.rows.nextResult") },
    { keys: ["k", "↑"], description: t("run.shortcuts.rows.prevResult") },
    { keys: ["Shift+J"], description: t("run.shortcuts.rows.nextStep") },
    { keys: ["Shift+K"], description: t("run.shortcuts.rows.prevStep") },
    { keys: ["Home"], description: t("run.shortcuts.rows.firstResult") },
    { keys: ["End"], description: t("run.shortcuts.rows.lastResult") },
    { keys: ["PgDn"], description: t("run.shortcuts.rows.nextSuite") },
    { keys: ["PgUp"], description: t("run.shortcuts.rows.prevSuite") },
  ]

  const filterRows = [
    { keys: ["F"], description: t("run.shortcuts.rows.jumpFailed") },
    { keys: ["B"], description: t("run.shortcuts.rows.jumpBlocked") },
    { keys: ["U"], description: t("run.shortcuts.rows.jumpNotRun") },
  ]

  const viewRows = [
    { keys: ["→", "l"], description: t("run.shortcuts.rows.expand") },
    { keys: ["←", "h"], description: t("run.shortcuts.rows.collapse") },
    { keys: ["o"], description: t("run.shortcuts.rows.toggle") },
    { keys: ["+"], description: t("run.shortcuts.rows.expandAll") },
    { keys: ["-"], description: t("run.shortcuts.rows.collapseAll") },
    { keys: ["L"], description: t("run.shortcuts.rows.toggleFollow") },
    { keys: ["r"], description: t("run.shortcuts.rows.resumeFollow") },
  ]

  const helpRows = [
    { keys: ["?"], description: t("run.shortcuts.rows.toggleHelp") },
  ]

  const statusRows = Object.entries(SHORTCUT_TO_STATUS).map(([key, status]) => ({
    keys: [key],
    description: t("run.shortcuts.rows.mark", { status: statusLabel(status) }),
  }))

  const sections = [
    { title: t("run.shortcuts.navigation"), rows: navigationRows },
    { title: t("run.shortcuts.filter"), rows: filterRows },
    { title: t("run.shortcuts.view"), rows: viewRows },
    ...(isAutomated ? [] : [{ title: t("run.shortcuts.setStatus"), rows: statusRows }]),
    { title: t("run.shortcuts.help"), rows: helpRows },
  ]
  return (
    <ShortcutsDialog
      open={open}
      onOpenChange={onOpenChange}
      description={t("run.shortcuts.description")}
      sections={sections}
    />
  )
}
