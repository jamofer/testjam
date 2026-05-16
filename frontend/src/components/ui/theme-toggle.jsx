import { Sun, Moon, Monitor } from "lucide-react"
import { useTranslation } from "react-i18next"
import { useTheme } from "../../hooks/useTheme"

const THEME_OPTIONS = [
  { value: "light",  labelKey: "user.themeLight",  icon: Sun },
  { value: "dark",   labelKey: "user.themeDark",   icon: Moon },
  { value: "system", labelKey: "user.themeSystem", icon: Monitor },
]

export function ThemeToggle() {
  const { t } = useTranslation("nav")
  const { theme, setTheme } = useTheme()
  return (
    <div className="px-3 py-2">
      <p className="text-[11px] uppercase tracking-wide text-gray-400 dark:text-gray-500 mb-1.5">{t("user.theme")}</p>
      <div role="radiogroup" aria-label={t("user.theme")} className="flex gap-1">
        {THEME_OPTIONS.map(({ value, labelKey, icon: Icon }) => {
          const active = theme === value
          const label = t(labelKey)
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
