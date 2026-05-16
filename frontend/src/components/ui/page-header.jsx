import { useEffect, useRef } from "react"
import { cn } from "../../lib/utils"
import { Breadcrumbs } from "./breadcrumbs"

/**
 * Sticky page header pinned to top of <main> scroll container.
 * Reserves a thin row at the top for breadcrumbs so the title row
 * sits at the same vertical offset on every page.
 *
 * Publishes its own height as the CSS custom property
 * `--page-header-height` on the document root, so siblings (e.g. a
 * sticky right-side ContextPanel) can clear it.
 */
export function PageHeader({ crumbs = [], children, className, contentClassName }) {
  const ref = useRef(null)

  useEffect(() => {
    const node = ref.current
    if (!node) return undefined
    const apply = () => {
      document.documentElement.style.setProperty(
        "--page-header-height", `${node.offsetHeight}px`,
      )
    }
    apply()
    let ro
    if (typeof ResizeObserver !== "undefined") {
      ro = new ResizeObserver(apply)
      ro.observe(node)
    }
    return () => {
      ro?.disconnect()
      document.documentElement.style.removeProperty("--page-header-height")
    }
  }, [])

  return (
    <div ref={ref} className={cn(
      "sticky top-0 z-30 pl-16 pr-4 md:px-8 pt-3 pb-4",
      "bg-gray-50 dark:bg-gray-950 border-b border-gray-200 dark:border-gray-800",
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
  return <div className={cn("px-4 pt-4 pb-6 md:px-8 md:pt-6 md:pb-8", className)}>{children}</div>
}
