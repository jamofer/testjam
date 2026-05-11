import { CheckCircle2, XCircle, MinusCircle, AlertTriangle, Loader2 } from "lucide-react"

export const STATUS_KEYS = ["passed", "failed", "blocked", "not_run"]

export const STATUS_CONFIG = {
  running: {
    label: "Running",
    icon: Loader2,
    badgeVariant: "default",
    iconColor: "text-blue-500 animate-spin",
    bg: "bg-blue-50 border-blue-200 animate-pulse",
    pill: "bg-blue-100 text-blue-700",
  },
  passed: {
    label: "Pass",
    icon: CheckCircle2,
    badgeVariant: "success",
    iconColor: "text-green-600",
    bg: "bg-green-100 border-green-300",
    pill: "bg-green-100 text-green-700",
  },
  failed: {
    label: "Fail",
    icon: XCircle,
    badgeVariant: "destructive",
    iconColor: "text-red-500",
    bg: "bg-red-100 border-red-300",
    pill: "bg-red-100 text-red-600",
  },
  blocked: {
    label: "Blocked",
    icon: AlertTriangle,
    badgeVariant: "warning",
    iconColor: "text-yellow-600",
    bg: "bg-yellow-100 border-yellow-300",
    pill: "bg-yellow-100 text-yellow-700",
  },
  not_run: {
    label: "Not run",
    icon: MinusCircle,
    badgeVariant: "secondary",
    iconColor: "text-gray-400",
    bg: "bg-gray-50 border-gray-200",
    pill: "bg-gray-100 text-gray-500",
  },
}

export function statusLabel(status) {
  return STATUS_CONFIG[status]?.label ?? status
}
