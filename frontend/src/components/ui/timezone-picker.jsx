import { useMemo, useState } from "react"
import { useTranslation } from "react-i18next"
import { Input } from "./input"
import { Check } from "lucide-react"

const IANA_TIMEZONES = (() => {
  if (typeof Intl !== "undefined" && typeof Intl.supportedValuesOf === "function") {
    try {
      return Intl.supportedValuesOf("timeZone")
    } catch {
      return []
    }
  }
  return []
})()

export function TimezonePicker({ value, onChange, disabled, placeholder }) {
  const { t } = useTranslation("ui")
  const resolvedPlaceholder = placeholder ?? t("timezone.placeholder")
  const [query, setQuery] = useState("")
  const [open, setOpen] = useState(false)

  const filtered = useMemo(() => {
    if (!query) return IANA_TIMEZONES.slice(0, 50)
    const lower = query.toLowerCase()
    return IANA_TIMEZONES.filter(zone => zone.toLowerCase().includes(lower)).slice(0, 50)
  }, [query])

  return (
    <div className="relative">
      <Input
        value={open ? query : (value ?? "")}
        onChange={event => { setQuery(event.target.value); setOpen(true) }}
        onFocus={() => setOpen(true)}
        onBlur={() => setTimeout(() => setOpen(false), 150)}
        placeholder={resolvedPlaceholder}
        disabled={disabled}
      />
      {open && filtered.length > 0 && (
        <ul className="absolute z-10 mt-1 max-h-60 w-full overflow-auto rounded-md border bg-white dark:bg-gray-900 shadow-md">
          {filtered.map(zone => (
            <li key={zone}>
              <button
                type="button"
                onMouseDown={event => {
                  event.preventDefault()
                  onChange(zone)
                  setQuery("")
                  setOpen(false)
                }}
                className="flex w-full items-center justify-between px-3 py-1.5 text-left text-sm hover:bg-gray-50 dark:hover:bg-gray-800"
              >
                <span>{zone}</span>
                {zone === value && <Check size={12} className="text-primary-600" />}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
