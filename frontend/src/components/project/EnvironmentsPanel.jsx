import { useState } from "react"
import { useTranslation } from "react-i18next"
import { Archive, ArchiveRestore, Plus, Server, Star, Trash2 } from "lucide-react"
import { toast } from "sonner"
import {
  useArchiveEnvironment,
  useCreateEnvironment,
  useDeleteEnvironment,
  useEnvironments,
  useUnarchiveEnvironment,
  useUpdateEnvironment,
} from "../../hooks/useEnvironments"
import { Button } from "../ui/button"
import { Input } from "../ui/input"
import { Label } from "../ui/label"
import { EmptyState } from "../ui/empty-state"

const DEFAULT_COLOR = "#10b981"
const SLUG_PATTERN = /^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$/

function slugify(value) {
  return value
    .trim()
    .toLowerCase()
    .replace(/[_\s]+/g, "-")
    .replace(/[^a-z0-9-]+/g, "-")
    .replace(/-{2,}/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 64)
}

function EnvironmentRow({ environment, projectId }) {
  const { t } = useTranslation("environments")
  const update = useUpdateEnvironment(projectId)
  const archive = useArchiveEnvironment(projectId)
  const unarchive = useUnarchiveEnvironment(projectId)
  const remove = useDeleteEnvironment(projectId)
  const isArchived = environment.archived_at !== null

  const handleSetDefault = () =>
    update.mutate(
      { id: environment.id, data: { is_default: !environment.is_default } },
      {
        onSuccess: () =>
          toast.success(environment.is_default ? t("toast.unsetDefault") : t("toast.setDefault")),
      },
    )

  const handleDelete = () =>
    remove.mutate(environment.id, {
      onSuccess: () => toast.success(t("toast.deleted")),
      onError: error => {
        const detail = error?.response?.data?.detail
        toast.error(detail ?? t("toast.deleteFailed"))
      },
    })

  const swatch = environment.color ?? "#9ca3af"

  return (
    <li className="flex items-center gap-3 border rounded-lg px-4 py-3 bg-white dark:bg-gray-900">
      <span
        className="inline-block w-3 h-3 rounded-full shrink-0"
        style={{ backgroundColor: swatch }}
        aria-hidden
      />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-medium text-sm text-gray-800 dark:text-gray-100 truncate">
            {environment.name}
          </span>
          <code className="text-xs font-mono bg-gray-100 dark:bg-gray-800 px-1.5 py-0.5 rounded text-gray-500 dark:text-gray-400">
            {environment.slug}
          </code>
          {environment.is_default && (
            <span className="text-xs text-amber-600 dark:text-amber-400 inline-flex items-center gap-1">
              <Star size={11} fill="currentColor" /> {t("badges.default")}
            </span>
          )}
          {isArchived && (
            <span className="text-xs text-gray-400">{t("badges.archived")}</span>
          )}
        </div>
        {environment.host && (
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5 truncate">{environment.host}</p>
        )}
      </div>
      <button
        onClick={handleSetDefault}
        title={environment.is_default ? t("actions.unsetDefault") : t("actions.setDefault")}
        className="text-gray-400 hover:text-amber-500"
      >
        <Star size={14} fill={environment.is_default ? "currentColor" : "none"} />
      </button>
      <button
        onClick={() => (isArchived ? unarchive.mutate(environment.id) : archive.mutate(environment.id))}
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

export function EnvironmentsPanel({ projectId }) {
  const { t } = useTranslation("environments")
  const { data: environments = [] } = useEnvironments(projectId, { includeArchived: true })
  const create = useCreateEnvironment(projectId)
  const [name, setName] = useState("")
  const [slug, setSlug] = useState("")
  const [host, setHost] = useState("")
  const [color, setColor] = useState(DEFAULT_COLOR)
  const [slugTouched, setSlugTouched] = useState(false)

  const handleNameChange = event => {
    const next = event.target.value
    setName(next)
    if (!slugTouched) {
      setSlug(slugify(next))
    }
  }

  const handleSlugChange = event => {
    setSlugTouched(true)
    setSlug(event.target.value)
  }

  const slugValid = !slug || SLUG_PATTERN.test(slug)

  const handleCreate = async event => {
    event.preventDefault()
    if (!name.trim() || !slug.trim() || !slugValid) return
    await create.mutateAsync({
      name: name.trim(),
      slug: slug.trim(),
      host: host.trim() || null,
      color: color || null,
    })
    toast.success(t("toast.created"))
    setName("")
    setSlug("")
    setHost("")
    setColor(DEFAULT_COLOR)
    setSlugTouched(false)
  }

  return (
    <div className="space-y-4">
      <form onSubmit={handleCreate} className="grid gap-2 sm:grid-cols-[1fr_1fr_1fr_auto_auto] items-end">
        <div>
          <Label className="text-xs">{t("fields.name")}</Label>
          <Input value={name} onChange={handleNameChange} placeholder={t("placeholders.name")} />
        </div>
        <div>
          <Label className="text-xs">{t("fields.slug")}</Label>
          <Input
            value={slug}
            onChange={handleSlugChange}
            placeholder={t("placeholders.slug")}
            aria-invalid={!slugValid}
          />
          {!slugValid && (
            <p className="text-xs text-red-600 dark:text-red-400 mt-1">{t("errors.invalidSlug")}</p>
          )}
        </div>
        <div>
          <Label className="text-xs">{t("fields.host")}</Label>
          <Input value={host} onChange={event => setHost(event.target.value)} placeholder={t("placeholders.host")} />
        </div>
        <div className="flex flex-col">
          <Label className="text-xs">{t("fields.color")}</Label>
          <input
            type="color"
            value={color}
            onChange={event => setColor(event.target.value)}
            className="h-9 w-12 rounded border border-gray-300 dark:border-gray-700 bg-transparent"
          />
        </div>
        <Button type="submit" disabled={create.isPending || !slugValid || !name.trim() || !slug.trim()}>
          <Plus size={14} /> {t("add")}
        </Button>
      </form>

      <ul className="space-y-2">
        {environments.map(environment => (
          <EnvironmentRow key={environment.id} environment={environment} projectId={projectId} />
        ))}
        {environments.length === 0 && (
          <EmptyState
            icon={Server}
            title={t("empty.title")}
            description={t("empty.description")}
            compact
          />
        )}
      </ul>
    </div>
  )
}
