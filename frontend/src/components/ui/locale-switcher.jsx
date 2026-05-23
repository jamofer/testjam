import { useTranslation } from "react-i18next"
import { Languages } from "lucide-react"

import { useLocale } from "../../hooks/useLocale"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./select"

const NATIVE_LANGUAGE_NAMES = {
  en: "English",
  es: "Español",
  ca: "Català",
  gl: "Galego",
  eu: "Euskara",
}

export function LocaleSwitcher({ className, compact = false }) {
  const { t } = useTranslation("common")
  const { locale, setLocale, supported } = useLocale()
  const triggerClass = compact
    ? "h-8 text-xs gap-1.5"
    : "h-9 text-sm gap-2"

  return (
    <Select value={locale} onValueChange={setLocale}>
      <SelectTrigger
        aria-label={t("language.label")}
        className={`${triggerClass} ${className ?? ""}`}
      >
        <Languages size={compact ? 12 : 14} className="text-gray-500 dark:text-gray-400" />
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        {supported.map(code => (
          <SelectItem key={code} value={code}>
            {NATIVE_LANGUAGE_NAMES[code] ?? code}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}
