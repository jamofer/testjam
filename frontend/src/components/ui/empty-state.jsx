import { cn } from "../../lib/utils"

export function EmptyState({ icon: Icon, title, description, action, className, compact = false }) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center text-center rounded-lg border border-dashed border-gray-200 bg-gray-50/50",
        compact ? "px-4 py-6 gap-1" : "px-6 py-12 gap-2",
        className
      )}
      role="status"
    >
      {Icon && (
        <div className={cn("text-gray-300", compact ? "mb-1" : "mb-2")}>
          <Icon size={compact ? 24 : 36} strokeWidth={1.5} />
        </div>
      )}
      <p className={cn("font-medium text-gray-700", compact ? "text-sm" : "text-base")}>{title}</p>
      {description && (
        <p className={cn("text-gray-500", compact ? "text-xs" : "text-sm max-w-md")}>{description}</p>
      )}
      {action && <div className={compact ? "mt-1" : "mt-3"}>{action}</div>}
    </div>
  )
}
