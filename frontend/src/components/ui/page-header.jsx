import { cn } from "../../lib/utils"
import { Breadcrumbs } from "./breadcrumbs"

/**
 * Sticky page header pinned to top of <main> scroll container.
 * Reserves a thin row at the top for breadcrumbs so the title row
 * sits at the same vertical offset on every page.
 */
export function PageHeader({ crumbs = [], children, className, contentClassName }) {
  return (
    <div className={cn(
      "sticky top-0 z-30 px-8 pt-3 pb-4",
      "bg-gray-50 border-b border-gray-200",
      className,
    )}>
      <div className="h-[18px] mb-1.5">
        {crumbs.length > 0 && <Breadcrumbs crumbs={crumbs} />}
      </div>
      <div className={cn("space-y-3", contentClassName)}>
        {children}
      </div>
    </div>
  )
}

/** Padded body wrapper to use after a PageHeader. */
export function PageBody({ children, className }) {
  return <div className={cn("px-8 pt-6 pb-8", className)}>{children}</div>
}
