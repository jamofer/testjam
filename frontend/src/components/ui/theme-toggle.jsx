import { Sun, Moon, Monitor } from "lucide-react"
import { useTheme } from "../../hooks/useTheme"

const THEME_OPTIONS = [
  { value: "light",  label: "Light",  icon: Sun },
  { value: "dark",   label: "Dark",   icon: Moon },
  { value: "system", label: "System", icon: Monitor },
]

export function ThemeToggle() {
  const { theme, setTheme } = useTheme()
  return (
    <div className="px-3 py-2">
      <p className="text-[11px] uppercase tracking-wide text-gray-400 dark:text-gray-500 mb-1.5">Theme</p>
      <div role="radiogroup" aria-label="Theme" className="flex gap-1">
        {THEME_OPTIONS.map(({ value, label, icon: Icon }) => {
          const active = theme === value
          return (
            <button
              key={value}
              type="button"
              role="radio"
              aria-checked={active}
              aria-label={label}
              title={label}
              onClick={() => setTheme(value)}
              className={`flex-1 flex items-center justify-center gap-1 px-2 py-1.5 rounded-md text-xs transition-colors ${
                active
                  ? "bg-primary-50 dark:bg-primary-900/30 text-primary-600 dark:text-primary-300"
                  : "text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800"
              }`}
            >
              <Icon size={13} />
            </button>
          )
        })}
      </div>
    </div>
  )
}
