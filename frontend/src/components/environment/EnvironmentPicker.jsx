import { useEffect, useState } from "react"
import { useTranslation } from "react-i18next"
import { useEnvironments } from "../../hooks/useEnvironments"
import { Input } from "../ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../ui/select"

const FREE_TEXT_OPTION = "__free_text__"
const NONE_OPTION = "__none__"

export function EnvironmentPicker({ projectId, value, onChange, allowEmpty = true }) {
  const { t } = useTranslation("environments")
  const { data: environments = [], isLoading } = useEnvironments(projectId)

  const matchingEnv = environments.find(env => env.slug === value)
  const initialMode = pickMode(value, matchingEnv, isLoading)
  const [mode, setMode] = useState(initialMode)
  const [freeText, setFreeText] = useState(initialMode === "free" ? (value ?? "") : "")

  useEffect(() => {
    if (isLoading) return
    if (value && !environments.some(env => env.slug === value)) {
      setMode("free")
      setFreeText(value)
    } else if (!value && mode === "free" && !freeText) {
      setMode("catalog")
    } else if (value && environments.some(env => env.slug === value) && mode === "free") {
      setMode("catalog")
    }
  }, [value, environments, isLoading]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!projectId) return
    if (!value && !isLoading) {
      const defaultEnv = environments.find(env => env.is_default)
      if (defaultEnv) {
        onChange(defaultEnv.slug)
      }
    }
  }, [projectId, environments, isLoading]) // eslint-disable-line react-hooks/exhaustive-deps

  function handleSelect(next) {
    if (next === FREE_TEXT_OPTION) {
      setMode("free")
      onChange(freeText || "")
      return
    }
    if (next === NONE_OPTION) {
      onChange(null)
      return
    }
    onChange(next)
  }

  if (mode === "free") {
    return (
      <div className="flex gap-2">
        <Input
          value={freeText}
          onChange={event => {
            setFreeText(event.target.value)
            onChange(event.target.value)
          }}
          placeholder={t("picker.freeTextPlaceholder")}
        />
        <button
          type="button"
          className="text-xs text-gray-500 dark:text-gray-400 hover:underline"
          onClick={() => {
            setMode("catalog")
            setFreeText("")
            onChange(null)
          }}
        >
          {t("picker.useCatalog")}
        </button>
      </div>
    )
  }

  return (
    <Select value={value ?? ""} onValueChange={handleSelect}>
      <SelectTrigger>
        <SelectValue placeholder={t("picker.placeholder")} />
      </SelectTrigger>
      <SelectContent>
        {allowEmpty && <SelectItem value={NONE_OPTION}>{t("picker.none")}</SelectItem>}
        {environments.map(env => (
          <SelectItem key={env.id} value={env.slug}>
            {env.name}
          </SelectItem>
        ))}
        <SelectItem value={FREE_TEXT_OPTION}>{t("picker.freeText")}</SelectItem>
      </SelectContent>
    </Select>
  )
}

function pickMode(value, matchingEnv, isLoading) {
  if (!value) return "catalog"
  if (isLoading) return "catalog"
  return matchingEnv ? "catalog" : "free"
}
