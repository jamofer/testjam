import { useState } from "react"
import { Plus, Trash2, Tag, CheckCircle2, Archive, Circle } from "lucide-react"
import { useVersions, useCreateVersion, useDeleteVersion, useUpdateVersion } from "../../hooks/useVersions"
import { Button } from "../ui/button"
import { Input } from "../ui/input"
import { EmptyState } from "../ui/empty-state"
import { toast } from "sonner"

const VERSION_STATUS_CONFIG = {
  active:   { label: "Active",   icon: Circle,       color: "text-blue-500",  bg: "bg-blue-50"  },
  released: { label: "Released", icon: CheckCircle2, color: "text-green-600", bg: "bg-green-50" },
  archived: { label: "Archived", icon: Archive,      color: "text-gray-400",  bg: "bg-gray-50"  },
}

function VersionRow({ version, projectId }) {
  const deleteVersion = useDeleteVersion(projectId)
  const updateVersion = useUpdateVersion(projectId)
  const cfg = VERSION_STATUS_CONFIG[version.status] ?? VERSION_STATUS_CONFIG.active
  const Icon = cfg.icon

  const cycleStatus = () => {
    const next = { active: "released", released: "archived", archived: "active" }
    updateVersion.mutate({ id: version.id, data: { status: next[version.status] } })
  }

  return (
    <li className={`flex items-center gap-3 border rounded-lg px-4 py-3 ${cfg.bg}`}>
      <button onClick={cycleStatus} title="Click to change status" className="shrink-0">
        <Icon size={15} className={cfg.color} />
      </button>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-medium text-sm text-gray-800">{version.name}</span>
          {version.vcs_tag && (
            <span className="text-xs font-mono bg-white border px-1.5 py-0.5 rounded text-gray-500">
              {version.vcs_tag}
            </span>
          )}
        </div>
        {version.description && (
          <p className="text-xs text-gray-500 mt-0.5 truncate">{version.description}</p>
        )}
      </div>
      <span className={`text-xs font-medium ${cfg.color}`}>{cfg.label}</span>
      <button
        onClick={() => deleteVersion.mutate(version.id, { onSuccess: () => toast.success("Version deleted") })}
        className="text-gray-300 hover:text-red-500 shrink-0">
        <Trash2 size={13} />
      </button>
    </li>
  )
}

export function VersionsPanel({ projectId }) {
  const { data: versions = [] } = useVersions(projectId)
  const createVersion = useCreateVersion(projectId)
  const [name, setName] = useState("")
  const [vcsTag, setVcsTag] = useState("")

  const handleCreate = async (e) => {
    e.preventDefault()
    if (!name.trim()) return
    await createVersion.mutateAsync({ name: name.trim(), vcs_tag: vcsTag.trim() || undefined })
    toast.success("Version created")
    setName("")
    setVcsTag("")
  }

  return (
    <div className="space-y-4">
      <form onSubmit={handleCreate} className="flex gap-2">
        <Input placeholder="Version name (e.g. 1.4.0, sprint-23)…" value={name}
          onChange={e => setName(e.target.value)} />
        <Input placeholder="VCS tag (optional)" value={vcsTag}
          onChange={e => setVcsTag(e.target.value)} className="w-40" />
        <Button type="submit" disabled={createVersion.isPending}>
          <Plus size={14} /> Add
        </Button>
      </form>

      <ul className="space-y-2">
        {versions.map(v => <VersionRow key={v.id} version={v} projectId={projectId} />)}
        {versions.length === 0 && (
          <EmptyState
            icon={Tag}
            title="No versions yet"
            description="Versions tag releases or sprints. Tie executions to a version to see test results per release."
            compact
          />
        )}
      </ul>
    </div>
  )
}
