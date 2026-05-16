import { useState } from "react"
import { useTranslation } from "react-i18next"
import { Plus, Trash2, Tag, CheckCircle2, Archive, Circle } from "lucide-react"
import { useVersions, useCreateVersion, useDeleteVersion, useUpdateVersion } from "../../hooks/useVersions"
import { Button } from "../ui/button"
import { Input } from "../ui/input"
import { EmptyState } from "../ui/empty-state"
import { toast } from "sonner"

const VERSION_STATUS_STYLE = {
  active:   { icon: Circle,       color: "text-blue-500",  bg: "bg-blue-50"  },
  released: { icon: CheckCircle2, color: "text-green-600", bg: "bg-green-50" },
  archived: { icon: Archive,      color: "text-gray-400 dark:text-gray-500",  bg: "bg-gray-50 dark:bg-gray-900"  },
}

function VersionRow({ version, projectId }) {
  const { t } = useTranslation("versions")
  const deleteVersion = useDeleteVersion(projectId)
  const updateVersion = useUpdateVersion(projectId)
  const style = VERSION_STATUS_STYLE[version.status] ?? VERSION_STATUS_STYLE.active
  const Icon = style.icon

  const cycleStatus = () => {
    const next = { active: "released", released: "archived", archived: "active" }
    updateVersion.mutate({ id: version.id, data: { status: next[version.status] } })
  }

  return (
    <li className={`flex items-center gap-3 border rounded-lg px-4 py-3 ${style.bg}`}>
      <button onClick={cycleStatus} title={t("cycleStatus")} className="shrink-0">
        <Icon size={15} className={style.color} />
      </button>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-medium text-sm text-gray-800 dark:text-gray-100">{version.name}</span>
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
      <span className={`text-xs font-medium ${style.color}`}>{t(`statuses.${version.status}`)}</span>
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

  const handleCreate = async (event) => {
    event.preventDefault()
    if (!name.trim()) return
    await createVersion.mutateAsync({ name: name.trim(), vcs_tag: vcsTag.trim() || undefined })
    toast.success(t("created"))
    setName("")
    setVcsTag("")
  }

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
        {versions.map(version => <VersionRow key={version.id} version={version} projectId={projectId} />)}
        {versions.length === 0 && (
          <EmptyState
            icon={Tag}
            title={t("empty.title")}
            description={t("empty.description")}
            compact
          />
        )}
      </ul>
    </div>
  )
}
