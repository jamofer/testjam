import { useEffect, useState } from "react"
import { useTranslation } from "react-i18next"
import { toast } from "sonner"
import { Clock, Copy, Download, Eye, EyeOff, Key, Plus, Trash2 } from "lucide-react"

import { projectsApi } from "../../api/projects"
import { useUpdateProject } from "../../hooks/useProjects"
import {
  useProjectTokens,
  useCreateProjectToken,
  useRevokeProjectToken,
} from "../../hooks/useTokens"
import { Button } from "../ui/button"
import { Input } from "../ui/input"
import { Label } from "../ui/label"
import { Textarea } from "../ui/textarea"
import { EmptyState } from "../ui/empty-state"

export function GeneralTab({ projectId, project }) {
  const { t } = useTranslation("projectSettings")

  return (
    <div className="space-y-6">
      <header>
        <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">{t("general.title")}</h2>
        <p className="text-sm text-gray-500 dark:text-gray-400">{t("general.description")}</p>
      </header>

      <ProjectInfoSection projectId={projectId} project={project} />
      <ExportSection projectId={projectId} />
      <TokensSection projectId={projectId} />
    </div>
  )
}

function SectionCard({ title, description, children }) {
  return (
    <section className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl overflow-hidden">
      <header className="px-5 py-4 border-b border-gray-100 dark:border-gray-800">
        <h3 className="font-semibold text-gray-800 dark:text-gray-100">{title}</h3>
        {description && (
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{description}</p>
        )}
      </header>
      <div className="p-5">{children}</div>
    </section>
  )
}

function ProjectInfoSection({ projectId, project }) {
  const { t } = useTranslation("projectSettings")
  const update = useUpdateProject()
  const [name, setName] = useState(project?.name ?? "")
  const [description, setDescription] = useState(project?.description ?? "")

  useEffect(() => {
    setName(project?.name ?? "")
    setDescription(project?.description ?? "")
  }, [project?.id, project?.name, project?.description])

  const isArchived = !!project?.archived_at
  const dirty = name !== (project?.name ?? "") || description !== (project?.description ?? "")

  const submit = async (event) => {
    event.preventDefault()
    try {
      await update.mutateAsync({ id: projectId, data: { name: name.trim(), description } })
      toast.success(t("general.form.saved"))
    } catch (err) {
      toast.error(err?.response?.data?.detail ?? t("general.form.saveFailed"))
    }
  }

  return (
    <SectionCard title={t("general.form.title")}>
      <form onSubmit={submit} className="space-y-4">
        <div className="space-y-1">
          <Label>{t("general.form.name")}</Label>
          <Input
            value={name}
            onChange={(event) => setName(event.target.value)}
            disabled={isArchived}
            required
          />
        </div>
        <div className="space-y-1">
          <Label>{t("general.form.descriptionLabel")}</Label>
          <Textarea
            value={description ?? ""}
            onChange={(event) => setDescription(event.target.value)}
            placeholder={t("general.form.descriptionPlaceholder")}
            disabled={isArchived}
            rows={4}
          />
        </div>
        <div className="flex justify-end">
          <Button
            type="submit"
            size="sm"
            disabled={!dirty || isArchived || !name.trim() || update.isPending}
            loading={update.isPending}
          >
            {t("general.form.save")}
          </Button>
        </div>
      </form>
    </SectionCard>
  )
}

function ExportSection({ projectId }) {
  const { t } = useTranslation("projectSettings")
  const [busy, setBusy] = useState(false)

  const handleExport = async () => {
    setBusy(true)
    try {
      await projectsApi.exportZip(projectId)
    } catch {
      toast.error(t("general.form.saveFailed"))
    } finally {
      setBusy(false)
    }
  }

  return (
    <SectionCard title={t("general.export.title")} description={t("general.export.description")}>
      <Button size="sm" variant="outline" onClick={handleExport} loading={busy}>
        <Download size={14} /> {t("general.export.button")}
      </Button>
    </SectionCard>
  )
}

function fmtDate(iso, fallback) {
  if (!iso) return fallback
  return new Date(iso).toLocaleString(undefined, { dateStyle: "short", timeStyle: "short" })
}

function NewTokenValue({ token, onDone }) {
  const { t } = useTranslation("members")
  const [visible, setVisible] = useState(false)
  const copy = () => { navigator.clipboard.writeText(token); toast.success(t("tokens.copied")) }

  return (
    <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4 space-y-3">
      <p className="text-sm font-medium text-green-800 dark:text-green-300">{t("tokens.created")}</p>
      <div className="flex items-center gap-2">
        <code className="flex-1 bg-white dark:bg-gray-900 border rounded px-3 py-1.5 text-sm font-mono text-gray-800 dark:text-gray-100 truncate">
          {visible ? token : token.slice(0, 4) + "•".repeat(token.length - 4)}
        </code>
        <button onClick={() => setVisible(value => !value)} className="text-gray-400 dark:text-gray-500 hover:text-gray-700 dark:hover:text-gray-200 p-1">
          {visible ? <EyeOff size={15} /> : <Eye size={15} />}
        </button>
        <button onClick={copy} className="text-gray-400 dark:text-gray-500 hover:text-gray-700 dark:hover:text-gray-200 p-1">
          <Copy size={15} />
        </button>
      </div>
      <Button size="sm" variant="outline" onClick={onDone}>{t("tokens.done")}</Button>
    </div>
  )
}

function TokensSection({ projectId }) {
  const { t } = useTranslation(["projectSettings", "members"])
  const { data: tokens = [] } = useProjectTokens(projectId)
  const create = useCreateProjectToken(projectId)
  const revoke = useRevokeProjectToken(projectId)
  const [name, setName] = useState("")
  const [newToken, setNewToken] = useState(null)

  const handleCreate = async (event) => {
    event.preventDefault()
    if (!name.trim()) return
    try {
      const created = await create.mutateAsync({ name: name.trim() })
      setNewToken(created.token)
      setName("")
    } catch {
      toast.error(t("members:tokens.createFailed"))
    }
  }

  const handleRevoke = async (tokenId) => {
    try {
      await revoke.mutateAsync(tokenId)
      toast.success(t("members:tokens.revoked"))
    } catch {
      toast.error(t("members:tokens.revokeFailed"))
    }
  }

  return (
    <SectionCard title={t("projectSettings:general.tokens.title")} description={t("projectSettings:general.tokens.description")}>
      <div className="space-y-4">
        {newToken && <NewTokenValue token={newToken} onDone={() => setNewToken(null)} />}

        <form onSubmit={handleCreate} className="flex gap-2">
          <Input
            value={name}
            onChange={event => setName(event.target.value)}
            placeholder={t("members:tokens.namePlaceholder")}
            className="flex-1"
          />
          <Button type="submit" size="sm" loading={create.isPending}>
            <Plus size={14} /> {t("members:tokens.newToken")}
          </Button>
        </form>

        {tokens.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-xs text-gray-400 dark:text-gray-500 uppercase">
                <tr>
                  <th className="text-left pb-2">{t("members:tokens.headers.name")}</th>
                  <th className="text-left pb-2">{t("members:tokens.headers.prefix")}</th>
                  <th className="text-left pb-2">{t("members:tokens.headers.lastUsed")}</th>
                  <th className="text-left pb-2">{t("members:tokens.headers.created")}</th>
                  <th />
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50 dark:divide-gray-800">
                {tokens.map(token => (
                  <tr key={token.id}>
                    <td className="py-2 font-medium text-gray-800 dark:text-gray-100">{token.name}</td>
                    <td className="py-2 font-mono text-gray-500 dark:text-gray-400">{token.prefix}…</td>
                    <td className="py-2 text-gray-400 dark:text-gray-500">
                      <span className="inline-flex items-center gap-1">
                        <Clock size={11} />{fmtDate(token.last_used_at, t("members:tokens.never"))}
                      </span>
                    </td>
                    <td className="py-2 text-gray-400 dark:text-gray-500">{fmtDate(token.created_at, t("members:tokens.never"))}</td>
                    <td className="py-2 text-right">
                      <button
                        onClick={() => handleRevoke(token.id)}
                        className="text-gray-300 dark:text-gray-600 hover:text-red-500 transition-colors p-1"
                      >
                        <Trash2 size={14} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {tokens.length === 0 && !newToken && (
          <EmptyState
            icon={Key}
            title={t("members:tokens.empty.title")}
            description={t("members:tokens.empty.description")}
            compact
          />
        )}
      </div>
    </SectionCard>
  )
}
