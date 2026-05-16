import { useState } from "react"
import { ChevronRight, PanelRightClose, PanelRightOpen } from "lucide-react"

/**
 * Right-side context panel: sticky on lg+, collapsible. Provides a typed sections API.
 * <ContextPanel sections={[{ title: "About", rows: [{label, value, icon?}] }, ...]} />
 */
export function ContextPanel({ sections = [], children, defaultCollapsed = false, className = "" }) {
  const [collapsed, setCollapsed] = useState(defaultCollapsed)

  // Sit just below the sticky PageHeader (if any), otherwise top-20 (5rem).
  const stickyStyle = { top: "calc(var(--page-header-height, 5rem) + 1rem)" }

  if (collapsed) {
    return (
      <aside className={`hidden lg:flex shrink-0 ${className}`}>
        <button type="button"
          onClick={() => setCollapsed(false)}
          aria-label="Expand context panel"
          style={stickyStyle}
          className="self-start sticky px-1.5 py-2 border border-gray-200 dark:border-gray-700 rounded-l-md bg-white dark:bg-gray-900 hover:bg-gray-50 dark:hover:bg-gray-800 text-gray-400 dark:text-gray-500 hover:text-gray-700 dark:hover:text-gray-200">
          <PanelRightOpen size={14} />
        </button>
      </aside>
    )
  }

  return (
    <aside className={`hidden lg:block w-72 shrink-0 ${className}`}>
      <div className="sticky space-y-4" style={stickyStyle}>
        <div className="flex items-center justify-between">
          <p className="text-[11px] uppercase tracking-wide font-bold text-gray-400 dark:text-gray-500">Context</p>
          <button type="button"
            onClick={() => setCollapsed(true)}
            aria-label="Collapse context panel"
            className="text-gray-400 dark:text-gray-500 hover:text-gray-700 dark:hover:text-gray-200">
            <PanelRightClose size={14} />
          </button>
        </div>
        {sections.map((section, idx) => (
          <ContextSection key={section.title ?? idx} section={section} />
        ))}
        {children}
      </div>
    </aside>
  )
}

function ContextSection({ section }) {
  const [open, setOpen] = useState(section.defaultOpen ?? true)
  const rows = (section.rows ?? []).filter(r => r.value !== undefined && r.value !== null && r.value !== "")
  if (rows.length === 0 && !section.body) return null

  return (
    <section className="border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-900">
      <button type="button"
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between px-3 py-2 text-left hover:bg-gray-50 dark:hover:bg-gray-800 rounded-lg">
        <p className="text-xs font-semibold text-gray-700 dark:text-gray-200">{section.title}</p>
        <ChevronRight size={12}
          className={`text-gray-400 dark:text-gray-500 shrink-0 transition-transform ${open ? "rotate-90" : ""}`} />
      </button>
      {open && (
        <div className="border-t border-gray-100 dark:border-gray-800 px-3 py-2 space-y-1.5">
          {rows.map((r, i) => (
            <ContextRow key={r.label ?? i} row={r} />
          ))}
          {section.body}
        </div>
      )}
    </section>
  )
}

function ContextRow({ row }) {
  const Icon = row.icon
  return (
    <div className="flex items-start gap-2 text-xs">
      {Icon && <Icon size={11} className="text-gray-400 dark:text-gray-500 mt-0.5 shrink-0" />}
      <span className="text-gray-500 dark:text-gray-400 w-20 shrink-0">{row.label}</span>
      <span className="flex-1 min-w-0 text-gray-800 dark:text-gray-100 break-words">{row.value}</span>
    </div>
  )
}
