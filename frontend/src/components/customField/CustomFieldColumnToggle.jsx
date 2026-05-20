import { useEffect, useRef, useState } from "react"
import { useTranslation } from "react-i18next"
import { Columns3, Check } from "lucide-react"
import { Button } from "../ui/button"

export function CustomFieldColumnToggle({ definitions, visibleKeys, onToggle }) {
  const { t } = useTranslation("customFields")
  const [open, setOpen] = useState(false)
  const containerRef = useRef(null)

  useEffect(() => {
    if (!open) return undefined
    const handleClick = (event) => {
      if (!containerRef.current?.contains(event.target)) setOpen(false)
    }
    document.addEventListener("mousedown", handleClick)
    return () => document.removeEventListener("mousedown", handleClick)
  }, [open])

  if (definitions.length === 0) return null

  return (
    <div ref={containerRef} className="relative">
      <Button
        size="sm"
        variant="outline"
        onClick={() => setOpen(value => !value)}
        title={t("columns.title")}
      >
        <Columns3 size={13} /> {t("columns.title")}
        {visibleKeys.length > 0 && (
          <span className="ml-1 text-[10px] opacity-70">{visibleKeys.length}</span>
        )}
      </Button>
      {open && (
        <div className="absolute right-0 mt-1 z-20 min-w-[12rem] rounded-md border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 shadow-md p-1">
          <p className="px-2 py-1 text-[10px] uppercase tracking-wide text-gray-400 dark:text-gray-500">
            {t("columns.subtitle")}
          </p>
          {definitions.map(definition => {
            const active = visibleKeys.includes(definition.key)
            return (
              <button
                type="button"
                key={definition.id}
                onClick={() => onToggle(definition.key)}
                className="flex w-full items-center gap-2 rounded px-2 py-1 text-xs text-left hover:bg-gray-50 dark:hover:bg-gray-800"
              >
                <span className="inline-flex h-3 w-3 items-center justify-center">
                  {active && <Check size={12} className="text-primary-600 dark:text-primary-400" />}
                </span>
                <span className="flex-1 truncate">{definition.label}</span>
              </button>
            )
          })}
        </div>
      )}
    </div>
  )
}
