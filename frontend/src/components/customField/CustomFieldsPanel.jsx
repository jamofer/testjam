import { useState } from "react"
import { useTranslation } from "react-i18next"
import { Archive, ArchiveRestore, Plus, Settings2, Trash2 } from "lucide-react"
import { toast } from "sonner"

import {
  useArchiveCustomField,
  useCreateCustomField,
  useCustomFields,
  useDeleteCustomField,
  useUnarchiveCustomField,
} from "../../hooks/useCustomFields"
import { Button } from "../ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../ui/dialog"
import { EmptyState } from "../ui/empty-state"
import { Input } from "../ui/input"
import { Label } from "../ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../ui/select"
import { Textarea } from "../ui/textarea"

const ENTITY_TYPES = ["bug", "test_case", "execution"]
const FIELD_TYPES = ["text", "number", "bool", "single_select", "multi_select", "date"]
const KEY_PATTERN = /^[a-z][a-z0-9_]*$/
const SELECT_TYPES = ["single_select", "multi_select"]

export function CustomFieldsPanel({ projectId }) {
  const { t } = useTranslation("customFields")
  const [entityType, setEntityType] = useState("bug")
  const [dialogOpen, setDialogOpen] = useState(false)
  const { data: definitions = [] } = useCustomFields(projectId, entityType, { includeArchived: true })

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <EntityTabs value={entityType} onChange={setEntityType} />
        <Button size="sm" onClick={() => setDialogOpen(true)}>
          <Plus size={13} /> {t("add")}
        </Button>
      </div>

      {definitions.length === 0 ? (
        <EmptyState
          icon={Settings2}
          title={t("empty.title")}
          description={t("empty.description")}
          compact
        />
      ) : (
        <ul className="space-y-2">
          {definitions.map(definition => (
            <DefinitionRow
              key={definition.id}
              definition={definition}
              projectId={projectId}
            />
          ))}
        </ul>
      )}

      <CreateFieldDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        projectId={projectId}
        defaultEntityType={entityType}
        onCreated={() => setDialogOpen(false)}
      />
    </div>
  )
}

function EntityTabs({ value, onChange }) {
  const { t } = useTranslation("customFields")
  return (
    <div className="inline-flex rounded-md border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-1">
      {ENTITY_TYPES.map(entity => (
        <button
          key={entity}
          onClick={() => onChange(entity)}
          className={`px-3 py-1 text-xs rounded ${
            value === entity
              ? "bg-gray-900 text-white dark:bg-gray-200 dark:text-gray-900"
              : "text-gray-600 dark:text-gray-400"
          }`}
        >
          {t(`entities.${entity}`)}
        </button>
      ))}
    </div>
  )
}

function DefinitionRow({ definition, projectId }) {
  const { t } = useTranslation("customFields")
  const archive = useArchiveCustomField(projectId)
  const unarchive = useUnarchiveCustomField(projectId)
  const remove = useDeleteCustomField(projectId)
  const isArchived = definition.archived_at !== null

  const handleArchiveToggle = () => {
    const mutation = isArchived ? unarchive : archive
    mutation.mutate(definition.id, {
      onSuccess: () =>
        toast.success(isArchived ? t("toast.unarchived") : t("toast.archived")),
    })
  }

  const handleDelete = () => {
    remove.mutate(definition.id, {
      onSuccess: () => toast.success(t("toast.deleted")),
      onError: () => toast.error(t("toast.deleteFailed")),
    })
  }

  return (
    <li className="flex items-center gap-3 border rounded-lg px-4 py-3 bg-white dark:bg-gray-900">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-medium text-sm text-gray-800 dark:text-gray-100 truncate">
            {definition.label}
          </span>
          <code className="text-xs font-mono bg-gray-100 dark:bg-gray-800 px-1.5 py-0.5 rounded text-gray-500 dark:text-gray-400">
            {definition.key}
          </code>
          <span className="text-xs text-gray-500">{t(`types.${definition.type}`)}</span>
          {definition.required && (
            <span className="text-xs text-amber-600 dark:text-amber-400">{t("badges.required")}</span>
          )}
          {isArchived && (
            <span className="text-xs text-gray-400">{t("badges.archived")}</span>
          )}
        </div>
        {definition.options && definition.options.length > 0 && (
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5 truncate">
            {definition.options.map(option => option.label).join(", ")}
          </p>
        )}
      </div>
      <button
        onClick={handleArchiveToggle}
        title={isArchived ? t("actions.unarchive") : t("actions.archive")}
        className="text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"
      >
        {isArchived ? <ArchiveRestore size={14} /> : <Archive size={14} />}
      </button>
      <button
        onClick={handleDelete}
        title={t("actions.delete")}
        className="text-gray-300 dark:text-gray-600 hover:text-red-500"
      >
        <Trash2 size={14} />
      </button>
    </li>
  )
}

function CreateFieldDialog({ open, onOpenChange, projectId, defaultEntityType, onCreated }) {
  const { t } = useTranslation("customFields")
  const create = useCreateCustomField(projectId)
  const [entityType, setEntityType] = useState(defaultEntityType)
  const [key, setKey] = useState("")
  const [label, setLabel] = useState("")
  const [type, setType] = useState("text")
  const [optionsText, setOptionsText] = useState("")
  const [required, setRequired] = useState(false)
  const [defaultValue, setDefaultValue] = useState("")

  const isSelect = SELECT_TYPES.includes(type)
  const keyValid = !key || KEY_PATTERN.test(key)

  const reset = () => {
    setEntityType(defaultEntityType)
    setKey("")
    setLabel("")
    setType("text")
    setOptionsText("")
    setRequired(false)
    setDefaultValue("")
  }

  const handleSubmit = async event => {
    event.preventDefault()
    if (!key || !label || !keyValid) return
    const payload = {
      entity_type: entityType,
      key: key.trim(),
      label: label.trim(),
      type,
      required,
    }
    if (isSelect) {
      payload.options = parseOptions(optionsText)
    }
    if (defaultValue !== "") {
      payload.default_value = coerceDefault(type, defaultValue)
    }
    try {
      await create.mutateAsync(payload)
      toast.success(t("toast.created"))
      reset()
      onCreated()
    } catch (error) {
      toast.error(error?.response?.data?.detail ?? t("errors.duplicateKey"))
    }
  }

  return (
    <Dialog open={open} onOpenChange={next => { onOpenChange(next); if (!next) reset() }}>
      <DialogContent>
        <DialogHeader><DialogTitle>{t("add")}</DialogTitle></DialogHeader>
        <form className="space-y-3" onSubmit={handleSubmit}>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <Label>{t("fields.entity_type")}</Label>
              <Select value={entityType} onValueChange={setEntityType}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {ENTITY_TYPES.map(entity => (
                    <SelectItem key={entity} value={entity}>{t(`entities.${entity}`)}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1">
              <Label>{t("fields.type")}</Label>
              <Select value={type} onValueChange={setType}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {FIELD_TYPES.map(fieldType => (
                    <SelectItem key={fieldType} value={fieldType}>{t(`types.${fieldType}`)}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="space-y-1">
            <Label>{t("fields.label")}</Label>
            <Input value={label} onChange={event => setLabel(event.target.value)} />
          </div>
          <div className="space-y-1">
            <Label>{t("fields.key")}</Label>
            <Input
              value={key}
              onChange={event => setKey(event.target.value)}
              aria-invalid={!keyValid}
            />
            <p className="text-xs text-gray-500 dark:text-gray-400">{t("fields.keyHint")}</p>
            {!keyValid && (
              <p className="text-xs text-red-600 dark:text-red-400">{t("errors.invalidKey")}</p>
            )}
          </div>
          {isSelect && (
            <div className="space-y-1">
              <Label>{t("fields.options")}</Label>
              <Textarea
                rows={4}
                value={optionsText}
                onChange={event => setOptionsText(event.target.value)}
                placeholder={"p0 | P0\np1 | P1"}
              />
              <p className="text-xs text-gray-500 dark:text-gray-400">{t("fields.optionsHint")}</p>
            </div>
          )}
          <div className="space-y-1">
            <Label>{t("fields.default")}</Label>
            <Input
              value={defaultValue}
              onChange={event => setDefaultValue(event.target.value)}
              placeholder={isSelect ? "value" : ""}
            />
            <p className="text-xs text-gray-500 dark:text-gray-400">{t("fields.defaultHint")}</p>
          </div>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={required}
              onChange={event => setRequired(event.target.checked)}
            />
            {t("fields.required")}
          </label>
          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              {t("actions.cancel")}
            </Button>
            <Button type="submit" loading={create.isPending} disabled={!key || !label || !keyValid}>
              {t("actions.save")}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}

function parseOptions(text) {
  return text
    .split("\n")
    .map(line => line.trim())
    .filter(Boolean)
    .map(line => {
      const [rawValue, rawLabel] = line.split("|").map(part => part.trim())
      return { value: rawValue, label: rawLabel || rawValue }
    })
}

function coerceDefault(type, raw) {
  if (type === "number") return Number(raw)
  if (type === "bool") return raw === "true" || raw === "1"
  if (type === "multi_select") return raw.split(",").map(item => item.trim()).filter(Boolean)
  return raw
}
