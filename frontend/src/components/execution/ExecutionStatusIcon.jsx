import { EXECUTION_STATUS_CONFIG } from "../../lib/executionStatus"

export function ExecutionStatusIcon({ status, size = 14 }) {
  const config = EXECUTION_STATUS_CONFIG[status] ?? EXECUTION_STATUS_CONFIG.pending
  const Icon = config.icon
  return <Icon size={size} className={config.iconColor} aria-hidden="true" />
}
