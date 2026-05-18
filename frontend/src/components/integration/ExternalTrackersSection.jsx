import { useState } from "react"
import { useTranslation } from "react-i18next"
import { Plus, Trash2, ShieldCheck, KeyRound, Workflow } from "lucide-react"
import { toast } from "sonner"

import {
  useIntegrations,
  useDeleteIntegration,
  useTestIntegration,
} from "../../hooks/useIntegrations"
import { Button } from "../ui/button"
import { Badge } from "../ui/badge"
import { EmptyState } from "../ui/empty-state"
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "../ui/dialog"
import { Input } from "../ui/input"
import { Label } from "../ui/label"

import { NewIntegrationDialog } from "./NewIntegrationDialog"
import { RotateCredentialDialog } from "./RotateCredentialDialog"
import { StatusMappingDialog } from "./StatusMappingDialog"


export function ExternalTrackersSection({ projectId }) {
  const { t } = useTranslation("integrations")
  const { data: integrations = [], isLoading } = useIntegrations(projectId)
  const [creating, setCreating] = useState(false)
  const [pendingDelete, setPendingDelete] = useState(null)
  const [rotating, setRotating] = useState(null)
  const [editingMapping, setEditingMapping] = useState(null)

  return (
    <section className="space-y-3">
      <header className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-200 uppercase tracking-wide">
            {t("trackers.title")}
          </h2>
          <p className="text-xs text-gray-500 dark:text-gray-400">{t("trackers.subtitle")}</p>
        </div>
        <Button size="sm" variant="outline" onClick={() => setCreating(true)}>
          <Plus size={14} /> {t("trackers.new")}
        </Button>
      </header>

      {isLoading ? null : integrations.length === 0 ? (
        <EmptyState
          icon={ShieldCheck}
          title={t("trackers.empty.title")}
          description={t("trackers.empty.description")}
          compact
        />
      ) : (
        <ul className="space-y-2">
          {integrations.map(integration => (
            <TrackerRow
              key={integration.id}
              integration={integration}
              onDelete={() => setPendingDelete(integration)}
              onRotate={() => setRotating(integration)}
              onEditMapping={() => setEditingMapping(integration)}
            />
          ))}
        </ul>
      )}

      {creating && (
        <NewIntegrationDialog projectId={projectId} onClose={() => setCreating(false)} />
      )}
      {pendingDelete && (
        <DeleteTrackerDialog
          projectId={projectId}
          integration={pendingDelete}
          onClose={() => setPendingDelete(null)}
        />
      )}
      {rotating && (
        <RotateCredentialDialog
          projectId={projectId}
          integration={rotating}
          onClose={() => setRotating(null)}
        />
      )}
      {editingMapping && (
        <StatusMappingDialog
          projectId={projectId}
          integration={editingMapping}
          onClose={() => setEditingMapping(null)}
        />
      )}
    </section>
  )
}


function TrackerRow({ integration, onDelete, onRotate, onEditMapping }) {
  const { t } = useTranslation("integrations")
  const test = useTestIntegration()
  const runTest = async () => {
    try {
      await test.mutateAsync(integration.id)
      toast.success(t("trackers.testOk"))
    } catch (error) {
      toast.error(error?.response?.data?.detail ?? t("trackers.testFailed"))
    }
  }
  const slug = slugForConfig(integration)
  return (
    <li className="border rounded-lg px-4 py-3 bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-800 flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
      <div className="min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <h3 className="font-medium text-gray-800 dark:text-gray-100 truncate">{integration.name}</h3>
          <Badge variant="secondary">{integration.provider}</Badge>
          <Badge variant={integration.is_active ? "success" : "secondary"}>
            {t(integration.is_active ? "status.active" : "status.paused")}
          </Badge>
        </div>
        {slug && (
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5 font-mono">{slug}</p>
        )}
        <p className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">
          {integration.credential_last_used_at
            ? t("trackers.lastUsed", { date: new Date(integration.credential_last_used_at).toLocaleString() })
            : t("trackers.neverUsed")}
        </p>
      </div>
      <div className="flex items-center gap-2 shrink-0">
        <Button size="sm" variant="ghost" onClick={runTest} disabled={test.isPending}>
          <ShieldCheck size={14} /> {t("trackers.test")}
        </Button>
        <Button size="sm" variant="ghost" onClick={onEditMapping} title={t("statusMapping.button")}>
          <Workflow size={14} />
        </Button>
        <Button size="sm" variant="ghost" onClick={onRotate}>
          <KeyRound size={14} /> {t("trackers.rotate")}
        </Button>
        <Button size="sm" variant="ghost" onClick={onDelete} className="text-red-500">
          <Trash2 size={14} />
        </Button>
      </div>
    </li>
  )
}


function slugForConfig(integration) {
  const config = integration.config ?? {}
  if (integration.provider === "github" && config.owner && config.repo) {
    return `${config.owner}/${config.repo}`
  }
  if (integration.provider === "jira" && config.project_key) {
    return `${(config.base_url ?? "").replace(/^https?:\/\//, "")} · ${config.project_key}`
  }
  return null
}


function DeleteTrackerDialog({ projectId, integration, onClose }) {
  const { t } = useTranslation("integrations")
  const [name, setName] = useState("")
  const remove = useDeleteIntegration(projectId)
  const matches = name === integration.name
  const confirm = async () => {
    try {
      await remove.mutateAsync(integration.id)
      toast.success(t("trackers.deleted"))
      onClose()
    } catch (error) {
      toast.error(error?.response?.data?.detail ?? t("trackers.deleteFailed"))
    }
  }
  return (
    <Dialog open onOpenChange={open => { if (!open) onClose() }}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{t("trackers.deleteTitle")}</DialogTitle>
        </DialogHeader>
        <p className="text-sm text-gray-700 dark:text-gray-200">
          {t("trackers.deleteBody", { name: integration.name })}
        </p>
        <div className="space-y-1">
          <Label>{t("trackers.deleteConfirmLabel")}</Label>
          <Input
            value={name}
            onChange={event => setName(event.target.value)}
            placeholder={integration.name}
          />
        </div>
        <DialogFooter>
          <Button variant="ghost" onClick={onClose}>{t("actions.cancel")}</Button>
          <Button variant="destructive" onClick={confirm} disabled={!matches || remove.isPending}>
            <Trash2 size={14} /> {t("trackers.delete")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
