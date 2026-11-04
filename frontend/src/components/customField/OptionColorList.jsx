import { useEffect, useRef, useState } from "react"
import { useTranslation } from "react-i18next"

const UNCOLORED_SWATCH = "#9ca3af"
const COMMIT_DELAY_MS = 400

export function OptionColorList({ options, onColorChange }) {
  return (
    <ul className="flex flex-wrap gap-1.5 mt-1">
      {options.map(option => (
        <OptionColorChip
          key={option.value}
          option={option}
          onCommit={color => onColorChange(option.value, color)}
        />
      ))}
    </ul>
  )
}

function OptionColorChip({ option, onCommit }) {
  const { t } = useTranslation("customFields")
  const [color, setColor] = useState(option.color || UNCOLORED_SWATCH)
  const commitTimer = useRef(null)

  useEffect(() => () => clearTimeout(commitTimer.current), [])

  const handleChange = event => {
    const next = event.target.value
    setColor(next)
    clearTimeout(commitTimer.current)
    commitTimer.current = setTimeout(() => onCommit(next), COMMIT_DELAY_MS)
  }

  return (
    <li className="inline-flex items-center gap-1 rounded border border-gray-200 dark:border-gray-700 pl-1 pr-2 py-0.5 text-xs text-gray-600 dark:text-gray-300">
      <input
        type="color"
        value={color}
        onChange={handleChange}
        aria-label={t("options.colorFor", { label: option.label })}
        className="h-4 w-4 cursor-pointer rounded border-0 bg-transparent p-0"
      />
      {option.label}
    </li>
  )
}
