import { ShortcutsDialog } from "../ui/shortcuts-dialog"
import { STATUS_CONFIG } from "../../lib/statusConfig"

export const SHORTCUT_TO_STATUS = { p: "passed", f: "failed", b: "blocked", n: "not_run" }

const NAV_ROWS = [
  { keys: ["j", "↓"], description: "Next result" },
  { keys: ["k", "↑"], description: "Previous result" },
  { keys: ["Shift+J"], description: "Next step in focused result" },
  { keys: ["Shift+K"], description: "Previous step" },
  { keys: ["Home"], description: "First result" },
  { keys: ["End"], description: "Last result" },
]

const FILTER_ROWS = [
  { keys: ["F"], description: "Jump to next failed" },
  { keys: ["B"], description: "Jump to next blocked" },
  { keys: ["U"], description: "Jump to next not run" },
]

const VIEW_ROWS = [
  { keys: ["o"], description: "Toggle expand focused result" },
  { keys: ["+"], description: "Expand all results" },
  { keys: ["-"], description: "Collapse all results" },
  { keys: ["L"], description: "Toggle follow-live" },
  { keys: ["r"], description: "Resume follow-live" },
]

const HELP_ROWS = [
  { keys: ["?"], description: "Toggle this help" },
]

function statusRows() {
  return Object.entries(SHORTCUT_TO_STATUS).map(([key, status]) => ({
    keys: [key],
    description: `Mark result as ${STATUS_CONFIG[status].label}`,
  }))
}

export function ShortcutHelpDialog({ open, onOpenChange, isAutomated }) {
  const sections = [
    { title: "Navigation", rows: NAV_ROWS },
    { title: "Filter", rows: FILTER_ROWS },
    { title: "View", rows: VIEW_ROWS },
    ...(isAutomated ? [] : [{ title: "Set status", rows: statusRows() }]),
    { title: "Help", rows: HELP_ROWS },
  ]
  return (
    <ShortcutsDialog
      open={open}
      onOpenChange={onOpenChange}
      description="Navigate and update results without the mouse."
      sections={sections}
    />
  )
}
