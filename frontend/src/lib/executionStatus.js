// Execution-level status reduction. The backend status (`completed`,
// `in_progress`, `pending`, `aborted`) tells you whether the run is
// over but not how it went — every finished run is "completed",
// regardless of pass/fail. This helper folds the result counts back
// into a single label so dashboards can render "Passed"/"Failed"
// instead of the meaningless "Completed" pill.

import { CheckCircle2, MinusCircle, PlayCircle, XCircle } from "lucide-react"

import { STATUS_CONFIG } from "./statusConfig"

/** Display of the backend execution status, which says whether a run is over, not how it went. */
export const EXECUTION_STATUS_CONFIG = {
  pending: {
    icon: MinusCircle,
    iconColor: "text-gray-400 dark:text-gray-500",
    dot: "bg-gray-400",
    pill: "bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300 border-gray-200 dark:border-gray-700",
  },
  in_progress: {
    icon: PlayCircle,
    iconColor: "text-blue-500",
    dot: "bg-blue-500",
    pill: "bg-blue-50 text-blue-700 border-blue-200",
  },
  completed: {
    icon: CheckCircle2,
    iconColor: "text-green-500",
    dot: "bg-green-500",
    pill: "bg-green-50 text-green-700 border-green-200",
  },
  aborted: {
    icon: XCircle,
    iconColor: "text-red-500",
    dot: "bg-red-500",
    pill: "bg-red-50 text-red-700 border-red-200",
  },
}

const PASSTHROUGH = new Set(["aborted", "in_progress", "pending"])
const EXTRA_PILL = {
  aborted: "bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-300",
  in_progress: "bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300",
  pending: "bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400",
}
const FALLBACK_PILL = "bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400"


export function effectiveExecutionStatus(item) {
  const status = item?.status
  if (PASSTHROUGH.has(status)) return status
  if ((item?.failed ?? 0) > 0) return "failed"
  if ((item?.blocked ?? 0) > 0) return "blocked"
  if ((item?.passed ?? 0) > 0) return "passed"
  return "not_run"
}


export function executionStatusPill(status) {
  return STATUS_CONFIG[status]?.pill ?? EXTRA_PILL[status] ?? FALLBACK_PILL
}
