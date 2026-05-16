import { useState } from "react"
import { Link } from "react-router-dom"
import { useTranslation } from "react-i18next"
import { Plus, Trash2, Tag, CheckCircle2, Archive, Circle, ChevronDown, ChevronRight } from "lucide-react"
import { useVersions, useCreateVersion, useDeleteVersion, useUpdateVersion } from "../../hooks/useVersions"
import { Button } from "../ui/button"
import { Input } from "../ui/input"
import { EmptyState } from "../ui/empty-state"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../ui/select"
import { toast } from "sonner"

const VERSION_STATUS_STYLE = {
  active:   { icon: Circle,       color: "text-blue-500",  bg: "bg-blue-50"  },
  released: { icon: CheckCircle2, color: "text-green-600", bg: "bg-green-50" },
  archived: { icon: Archive,      color: "text-gray-400 dark:text-gray-500", bg: "bg-gray-50 dark:bg-gray-900" },
}

const STATUS_ORDER = { active: 0, released: 1, archived: 2 }
const VERSION_STATUSES = ["active", "released", "archived"]

function VersionRow({ version, projectId }) {
  const { t } = useTranslation("versions")
  const deleteVersion = useDeleteVersion(projectId)
  const updateVersion = useUpdateVersion(projectId)
  const style = VERSION_STATUS_STYLE[version.status] ?? VERSION_STATUS_STYLE.active
  const Icon = style.icon

  return (
    <li className={`flex items-center gap-3 border rounded-lg px-4 py-3 ${style.bg}`}>
      <Icon size={15} className={`${style.color} shrink-0`} />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <Link
            to={`/projects/${projectId}/versions/${version.id}`}
            className="font-medium text-sm text-gray-800 dark:text-gray-100 hover:underline truncate"
            title={t("openDetail")}
          >
            {version.name}
          </Link>
          {version.vcs_tag && (
            <span className="text-xs font-mono bg-white dark:bg-gray-900 border px-1.5 py-0.5 rounded text-gray-500 dark:text-gray-400">
              {version.vcs_tag}
            </span>
          )}
        </div>
        {version.description && (
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5 truncate">{version.description}</p>
        )}
      </div>
      <Select
        value={version.status}
        onValueChange={status => updateVersion.mutate({ id: version.id, data: { status } })}
      >
        <SelectTrigger className="h-7 w-32 text-xs" title={t("changeStatus")}>
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {VERSION_STATUSES.map(status => (
            <SelectItem key={status} value={status}>{t(`statuses.${status}`)}</SelectItem>
          ))}
        </SelectContent>
      </Select>
      <button
        onClick={() => deleteVersion.mutate(version.id, { onSuccess: () => toast.success(t("deleted")) })}
        className="text-gray-300 dark:text-gray-600 hover:text-red-500 shrink-0">
        <Trash2 size={13} />
      </button>
    </li>
  )
}

export function VersionsPanel({ projectId }) {
  const { t } = useTranslation("versions")
  const { data: versions = [] } = useVersions(projectId)
  const createVersion = useCreateVersion(projectId)
  const [name, setName] = useState("")
  const [vcsTag, setVcsTag] = useState("")
  const [showArchived, setShowArchived] = useState(false)

  const handleCreate = async (event) => {
    event.preventDefault()
    if (!name.trim()) return
    await createVersion.mutateAsync({ name: name.trim(), vcs_tag: vcsTag.trim() || undefined })
    toast.success(t("created"))
    setName("")
    setVcsTag("")
  }

  const sorted = [...versions].sort((a, b) => STATUS_ORDER[a.status] - STATUS_ORDER[b.status])
  const archivedCount = versions.filter(version => version.status === "archived").length
  const visible = showArchived ? sorted : sorted.filter(version => version.status !== "archived")

  return (
    <div className="space-y-4">
      <form onSubmit={handleCreate} className="flex gap-2">
        <Input placeholder={t("namePlaceholder")} value={name}
          onChange={event => setName(event.target.value)} />
        <Input placeholder={t("tagPlaceholder")} value={vcsTag}
          onChange={event => setVcsTag(event.target.value)} className="w-40" />
        <Button type="submit" disabled={createVersion.isPending}>
          <Plus size={14} /> {t("add")}
        </Button>
      </form>

      <ul className="space-y-2">
        {visible.map(version => <VersionRow key={version.id} version={version} projectId={projectId} />)}
        {versions.length === 0 && (
          <EmptyState
            icon={Tag}
            title={t("empty.title")}
            description={t("empty.description")}
            compact
          />
        )}
      </ul>

      {archivedCount > 0 && (
        <button
          onClick={() => setShowArchived(value => !value)}
          className="flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"
        >
          {showArchived ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
          {showArchived ? t("hideArchived") : t("showArchived", { count: archivedCount })}
        </button>
      )}
    </div>
  )
}
