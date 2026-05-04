import { Link } from "react-router-dom"
import { ChevronRight } from "lucide-react"
import { cn } from "../../lib/utils"

/**
 * crumbs: array of { label, to? }
 * The last crumb is rendered as plain text (current page).
 */
export function Breadcrumbs({ crumbs = [], className }) {
  if (crumbs.length === 0) return null
  return (
    <nav aria-label="Breadcrumb" className={cn("flex items-center gap-1 text-sm text-gray-500", className)}>
      {crumbs.map((c, i) => {
        const isLast = i === crumbs.length - 1
        return (
          <span key={i} className="flex items-center gap-1 min-w-0">
            {i > 0 && <ChevronRight size={12} className="text-gray-300 shrink-0" />}
            {isLast || !c.to ? (
              <span
                className={cn("truncate", isLast && "text-gray-700 font-medium")}
                aria-current={isLast ? "page" : undefined}
              >
                {c.label}
              </span>
            ) : (
              <Link to={c.to} className="hover:text-gray-800 transition-colors truncate">
                {c.label}
              </Link>
            )}
          </span>
        )
      })}
    </nav>
  )
}
