import { AlertTriangle, RotateCw } from "lucide-react"
import { useTranslation } from "react-i18next"

import { cn } from "../../lib/utils"
import { Button } from "./button"

export function ErrorState({
  icon: Icon = AlertTriangle,
  title,
  description,
  onRetry,
  className,
  compact = false,
}) {
  const { t } = useTranslation("common")
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center text-center rounded-lg border border-dashed border-red-300 dark:border-red-800 bg-red-50/60 dark:bg-red-950/30",
        compact ? "px-4 py-6 gap-1" : "px-6 py-12 gap-2",
        className
      )}
      role="alert"
    >
      <div className={cn("text-red-400 dark:text-red-500", compact ? "mb-1" : "mb-2")}>
        <Icon size={compact ? 24 : 36} strokeWidth={1.5} />
      </div>
      <p className={cn("font-medium text-gray-800 dark:text-gray-100", compact ? "text-sm" : "text-base")}>
        {title ?? t("errors.queryTitle")}
      </p>
      <p className={cn("text-gray-500 dark:text-gray-400", compact ? "text-xs" : "text-sm max-w-md")}>
        {description ?? t("errors.queryDescription")}
      </p>
      {onRetry && (
        <div className={compact ? "mt-1" : "mt-3"}>
          <Button size="sm" variant="outline" onClick={onRetry}>
            <RotateCw size={13} /> {t("errors.retry")}
          </Button>
        </div>
      )}
    </div>
  )
}
