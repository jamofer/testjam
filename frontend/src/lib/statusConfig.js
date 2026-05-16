import { CheckCircle2, XCircle, MinusCircle, AlertTriangle, Loader2 } from "lucide-react"

export const STATUS_KEYS = ["passed", "failed", "blocked", "not_run"]

export const STATUS_CONFIG = {
  running: {
    label: "Running",
    icon: Loader2,
    badgeVariant: "default",
    iconColor: "text-blue-500 animate-spin",
    bg: "bg-blue-50 dark:bg-blue-950/40 border-blue-200 dark:border-blue-800 animate-pulse",
    pill: "bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300",
  },
  passed: {
    label: "Pass",
    icon: CheckCircle2,
    badgeVariant: "success",
    iconColor: "text-green-600 dark:text-green-400",
    bg: "bg-green-100 dark:bg-green-900/30 border-green-300 dark:border-green-800",
    pill: "bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300",
  },
  failed: {
    label: "Fail",
    icon: XCircle,
    badgeVariant: "destructive",
    iconColor: "text-red-500 dark:text-red-400",
    bg: "bg-red-100 dark:bg-red-900/30 border-red-300 dark:border-red-800",
    pill: "bg-red-100 dark:bg-red-900/40 text-red-600 dark:text-red-300",
  },
  blocked: {
    label: "Blocked",
    icon: AlertTriangle,
    badgeVariant: "warning",
    iconColor: "text-yellow-600 dark:text-yellow-400",
    bg: "bg-yellow-100 dark:bg-yellow-900/30 border-yellow-300 dark:border-yellow-800",
    pill: "bg-yellow-100 dark:bg-yellow-900/40 text-yellow-700 dark:text-yellow-300",
  },
  not_run: {
    label: "Not run",
    icon: MinusCircle,
    badgeVariant: "secondary",
    iconColor: "text-gray-400 dark:text-gray-500",
    bg: "bg-gray-50 dark:bg-gray-900 border-gray-200 dark:border-gray-700",
    pill: "bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400",
  },
}

export function statusLabel(status) {
  return STATUS_CONFIG[status]?.label ?? status
}
