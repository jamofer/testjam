import { useEffect, useState } from "react"
import { useTranslation } from "react-i18next"
import { toast } from "sonner"
import { Pencil } from "lucide-react"
import { Button } from "../ui/button"
import { Input } from "../ui/input"
import { Label } from "../ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../ui/select"
import { useCustomFields } from "../../hooks/useCustomFields"

const NONE_VALUE = "__none__"

export function CustomFieldInput({ definition, value, onChange }) {
  const { t } = useTranslation("customFields")
  return (
    <div className="space-y-1">
      <Label className="text-xs flex items-center gap-2">
        {definition.label}
        {definition.required && (
          <span className="text-[10px] uppercase tracking-wide text-amber-600 dark:text-amber-400">
            {t("badges.required")}
          </span>
        )}
      </Label>
      <FieldControl definition={definition} value={value} onChange={onChange} />
    </div>
  )
}

export function CustomFieldsForm({ definitions, values, onChange }) {
  if (!definitions || definitions.length === 0) return null
  const update = (key, next) => {
    const draft = { ...(values || {}) }
    if (next === undefined || next === null || next === "") {
      delete draft[key]
    } else {
      draft[key] = next
    }
    onChange(draft)
  }
  return (
    <div className="space-y-3">
      {definitions.map(definition => (
        <CustomFieldInput
          key={definition.id}
          definition={definition}
          value={(values || {})[definition.key]}
          onChange={next => update(definition.key, next)}
        />
      ))}
    </div>
  )
}

function FieldControl({ definition, value, onChange }) {
  switch (definition.type) {
    case "text":
      return (
        <Input
          value={value ?? ""}
          onChange={event => onChange(event.target.value)}
        />
      )
    case "number":
      return (
        <Input
          type="number"
          value={value ?? ""}
          onChange={event => {
            const raw = event.target.value
            onChange(raw === "" ? undefined : Number(raw))
          }}
        />
      )
    case "bool":
      return (
        <input
          type="checkbox"
          checked={!!value}
          onChange={event => onChange(event.target.checked)}
          className="h-4 w-4"
        />
      )
    case "date":
      return (
        <Input
          type="date"
          value={value ?? ""}
          onChange={event => onChange(event.target.value || undefined)}
        />
      )
    case "single_select":
      return <SingleSelectControl definition={definition} value={value} onChange={onChange} />
    case "multi_select":
      return <MultiSelectControl definition={definition} value={value} onChange={onChange} />
    default:
      return null
  }
}

function SingleSelectControl({ definition, value, onChange }) {
  const { t } = useTranslation("customFields")
  const selected = value ?? NONE_VALUE
  return (
    <Select
      value={selected}
      onValueChange={next => onChange(next === NONE_VALUE ? undefined : next)}
    >
      <SelectTrigger><SelectValue /></SelectTrigger>
      <SelectContent>
        <SelectItem value={NONE_VALUE}>{t("filter.any")}</SelectItem>
        {(definition.options || []).map(option => (
          <SelectItem key={option.value} value={option.value}>
            <span className="inline-flex items-center gap-2">
              {option.color && (
                <span
                  className="inline-block w-2 h-2 rounded-full"
                  style={{ backgroundColor: option.color }}
                />
              )}
              {option.label}
            </span>
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}

export function CustomFieldsEditableBody({ projectId, entityType, values, onSave, saving }) {
  const { t } = useTranslation("customFields")
  const { data: definitions = [] } = useCustomFields(projectId, entityType)
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(values ?? {})

  useEffect(() => {
    if (!editing) setDraft(values ?? {})
  }, [values, editing])

  if (definitions.length === 0) {
    return <p className="text-[11px] text-gray-400 dark:text-gray-500">{t("section.none")}</p>
  }

  if (editing) {
    return (
      <div className="space-y-3">
        <CustomFieldsForm definitions={definitions} values={draft} onChange={setDraft} />
        <div className="flex gap-2">
          <Button
            size="sm"
            disabled={saving}
            onClick={async () => {
              try {
                await onSave(draft)
                toast.success(t("toast.updated"))
                setEditing(false)
              } catch (error) {
                toast.error(error?.response?.data?.detail ?? "Failed")
              }
            }}
          >
            {t("actions.save")}
          </Button>
          <Button size="sm" variant="ghost" onClick={() => setEditing(false)}>
            {t("actions.cancel")}
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-1">
      <dl className="grid grid-cols-[auto_1fr] gap-x-2 gap-y-1 text-xs">
        {definitions.map(definition => (
          <div key={definition.id} className="contents">
            <dt className="text-gray-500 dark:text-gray-400 pr-1">{definition.label}</dt>
            <dd className="text-gray-800 dark:text-gray-100 min-w-0 break-words">
              <CustomFieldValue
                definition={definition}
                value={(values ?? {})[definition.key]}
              />
            </dd>
          </div>
        ))}
      </dl>
      <button
        type="button"
        onClick={() => setEditing(true)}
        className="text-[11px] text-primary-600 dark:text-primary-400 hover:underline inline-flex items-center gap-1 pt-1"
      >
        <Pencil size={11} /> {t("actions.edit")}
      </button>
    </div>
  )
}

export function CustomFieldValue({ definition, value }) {
  if (value === undefined || value === null || value === "") {
    return <span className="text-gray-300 dark:text-gray-600 italic">—</span>
  }
  if (definition.type === "bool") {
    return <span>{value ? "✓" : "✗"}</span>
  }
  if (definition.type === "single_select") {
    const option = (definition.options || []).find(opt => opt.value === value)
    if (!option) return <span>{value}</span>
    return (
      <span className="inline-flex items-center gap-1">
        {option.color && (
          <span
            className="inline-block w-2 h-2 rounded-full"
            style={{ backgroundColor: option.color }}
          />
        )}
        {option.label}
      </span>
    )
  }
  if (definition.type === "multi_select") {
    const selected = Array.isArray(value) ? value : []
    if (selected.length === 0) {
      return <span className="text-gray-300 dark:text-gray-600 italic">—</span>
    }
    return (
      <div className="flex flex-wrap gap-1">
        {selected.map(item => {
          const option = (definition.options || []).find(opt => opt.value === item)
          const label = option?.label ?? item
          return (
            <span
              key={item}
              className="text-[10px] px-1.5 py-0.5 rounded border border-gray-300 dark:border-gray-700"
              style={option?.color ? { backgroundColor: option.color, borderColor: option.color, color: "#fff" } : undefined}
            >
              {label}
            </span>
          )
        })}
      </div>
    )
  }
  return <span>{String(value)}</span>
}

function MultiSelectControl({ definition, value, onChange }) {
  const selected = Array.isArray(value) ? value : []
  const toggle = optionValue => {
    if (selected.includes(optionValue)) {
      const next = selected.filter(item => item !== optionValue)
      onChange(next.length ? next : undefined)
    } else {
      onChange([...selected, optionValue])
    }
  }
  return (
    <div className="flex flex-wrap gap-1.5">
      {(definition.options || []).map(option => {
        const active = selected.includes(option.value)
        return (
          <button
            type="button"
            key={option.value}
            onClick={() => toggle(option.value)}
            className={`text-xs px-2 py-1 rounded-full border transition ${
              active
                ? "bg-gray-900 text-white border-gray-900 dark:bg-gray-200 dark:text-gray-900 dark:border-gray-200"
                : "border-gray-300 dark:border-gray-700 text-gray-700 dark:text-gray-300"
            }`}
            style={active && option.color ? { backgroundColor: option.color, borderColor: option.color } : undefined}
          >
            {option.label}
          </button>
        )
      })}
    </div>
  )
}
