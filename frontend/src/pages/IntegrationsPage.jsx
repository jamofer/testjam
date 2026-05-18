import { useMemo, useState } from "react"
import { useParams } from "react-router-dom"
import { useTranslation } from "react-i18next"
import { Copy, PlayCircle, Plus, RefreshCw, Trash2 } from "lucide-react"
import { toast } from "sonner"

import {
  useCreateWebhook,
  useDeleteWebhook,
  useTestWebhook,
  useUpdateWebhook,
  useWebhookDeliveries,
  useWebhooks,
} from "../hooks/useWebhooks"
import { useProject } from "../hooks/useProjects"
import { ExternalTrackersSection } from "../components/integration/ExternalTrackersSection"
import { WEBHOOK_EVENTS } from "../api/webhooks"
import { PageBody, PageHeader } from "../components/ui/page-header"
import { Button } from "../components/ui/button"
import { Input } from "../components/ui/input"
import { Label } from "../components/ui/label"
import { Badge } from "../components/ui/badge"
import { DateLabel } from "../components/ui/date-label"
import { EmptyState } from "../components/ui/empty-state"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "../components/ui/dialog"


export function IntegrationsPage() {
  const { t } = useTranslation(["integrations", "nav"])
  const { id: projectId } = useParams()
  const { data: project } = useProject(projectId)
  const { data: webhooks = [] } = useWebhooks(projectId)

  const [editing, setEditing] = useState(null)
  const [creating, setCreating] = useState(false)
  const [logFor, setLogFor] = useState(null)
  const [pendingDelete, setPendingDelete] = useState(null)

  return (
    <>
      <PageHeader
        crumbs={[
          { label: t("nav:global.projects"), to: "/projects" },
          { label: project?.name ?? "…", to: `/projects/${projectId}` },
          { label: t("title") },
        ]}
      >
        <div className="max-w-2xl xl:max-w-4xl 2xl:max-w-5xl flex items-center justify-between gap-3 flex-wrap">
          <div>
            <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-100">{t("title")}</h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">{t("subtitle")}</p>
          </div>
          <Button size="sm" onClick={() => setCreating(true)}>
            <Plus size={14} /> {t("new")}
          </Button>
        </div>
      </PageHeader>

      <PageBody>
        <div className="max-w-2xl xl:max-w-4xl 2xl:max-w-5xl space-y-6">
          <ExternalTrackersSection projectId={projectId} />

          <section className="space-y-3">
            <header>
              <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-200 uppercase tracking-wide">
                {t("webhooks.title")}
              </h2>
              <p className="text-xs text-gray-500 dark:text-gray-400">{t("webhooks.subtitle")}</p>
            </header>
          {webhooks.length === 0 ? (
            <EmptyState
              icon={PlayCircle}
              title={t("empty.title")}
              description={t("empty.description")}
            />
          ) : (
            <ul className="space-y-2">
              {webhooks.map(webhook => (
                <WebhookRow
                  key={webhook.id}
                  webhook={webhook}
                  onEdit={() => setEditing(webhook)}
                  onViewLog={() => setLogFor(webhook)}
                  onDelete={() => setPendingDelete(webhook)}
                />
              ))}
            </ul>
          )}
          </section>
        </div>
      </PageBody>

      {creating && (
        <WebhookDialog
          projectId={projectId}
          onClose={() => setCreating(false)}
        />
      )}
      {editing && (
        <WebhookDialog
          projectId={projectId}
          webhook={editing}
          onClose={() => setEditing(null)}
        />
      )}
      {logFor && (
        <DeliveryLogDialog webhook={logFor} onClose={() => setLogFor(null)} />
      )}
      {pendingDelete && (
        <DeleteDialog
          projectId={projectId}
          webhook={pendingDelete}
          onClose={() => setPendingDelete(null)}
        />
      )}
    </>
  )
}


function WebhookRow({ webhook, onEdit, onViewLog, onDelete }) {
  const { t } = useTranslation("integrations")
  const testMutation = useTestWebhook()

  const test = async () => {
    try {
      await testMutation.mutateAsync(webhook.id)
      toast.success(t("toast.testSent"))
    } catch (error) {
      toast.error(error?.response?.data?.detail ?? "Failed")
    }
  }

  return (
    <li className="border rounded-lg px-4 py-3 bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-800 flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
      <div className="min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <h3 className="font-medium text-gray-800 dark:text-gray-100 truncate">{webhook.name}</h3>
          <Badge variant={webhook.is_active ? "success" : "secondary"}>
            {t(webhook.is_active ? "status.active" : "status.paused")}
          </Badge>
        </div>
        <p className="text-xs text-gray-500 dark:text-gray-400 truncate mt-0.5">{webhook.url}</p>
        <div className="flex flex-wrap gap-1 mt-1.5">
          {webhook.events.map(event => (
            <span
              key={event}
              className="text-[11px] px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300 font-mono"
            >
              {event}
            </span>
          ))}
        </div>
      </div>
      <div className="flex items-center gap-2 shrink-0">
        <Button size="sm" variant="ghost" onClick={test} disabled={testMutation.isPending}>
          <PlayCircle size={14} /> {t("actions.test")}
        </Button>
        <Button size="sm" variant="ghost" onClick={onViewLog}>
          <RefreshCw size={14} /> {t("actions.viewLog")}
        </Button>
        <Button size="sm" variant="ghost" onClick={onEdit}>
          {t("actions.edit")}
        </Button>
        <Button size="sm" variant="ghost" onClick={onDelete} className="text-red-500">
          <Trash2 size={14} />
        </Button>
      </div>
    </li>
  )
}


function WebhookDialog({ projectId, webhook, onClose }) {
  const { t } = useTranslation("integrations")
  const isEdit = !!webhook
  const create = useCreateWebhook(projectId)
  const update = useUpdateWebhook(projectId)
  const [form, setForm] = useState({
    name: webhook?.name ?? "",
    url: webhook?.url ?? "",
    events: webhook?.events ?? [],
    is_active: webhook?.is_active ?? true,
  })
  const [createdSecret, setCreatedSecret] = useState(null)

  const submit = async (event) => {
    event.preventDefault()
    try {
      if (isEdit) {
        await update.mutateAsync({ id: webhook.id, data: form })
        toast.success(t("toast.updated"))
        onClose()
      } else {
        const created = await create.mutateAsync(form)
        toast.success(t("toast.created"))
        setCreatedSecret(created.secret)
      }
    } catch (error) {
      toast.error(error?.response?.data?.detail ?? "Failed")
    }
  }

  const toggleEvent = (event) => {
    setForm(prev => ({
      ...prev,
      events: prev.events.includes(event)
        ? prev.events.filter(item => item !== event)
        : [...prev.events, event],
    }))
  }

  return (
    <Dialog open onOpenChange={open => { if (!open) onClose() }}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{t(isEdit ? "dialog.editTitle" : "dialog.createTitle")}</DialogTitle>
        </DialogHeader>

        {createdSecret ? (
          <SecretReveal secret={createdSecret} onClose={onClose} />
        ) : (
          <form className="space-y-3" onSubmit={submit}>
            <div className="space-y-1">
              <Label>{t("form.name")}</Label>
              <Input
                value={form.name}
                onChange={event => setForm(prev => ({ ...prev, name: event.target.value }))}
                required
              />
            </div>
            <div className="space-y-1">
              <Label>{t("form.url")}</Label>
              <Input
                type="url"
                placeholder={t("form.urlPlaceholder")}
                value={form.url}
                onChange={event => setForm(prev => ({ ...prev, url: event.target.value }))}
                required
              />
            </div>
            <div className="space-y-1">
              <Label>{t("form.events")}</Label>
              <p className="text-xs text-gray-400 dark:text-gray-500">{t("form.eventsHelp")}</p>
              <ul className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
                {WEBHOOK_EVENTS.map(event => (
                  <li key={event}>
                    <label className="flex items-center gap-2 text-sm cursor-pointer">
                      <input
                        type="checkbox"
                        checked={form.events.includes(event)}
                        onChange={() => toggleEvent(event)}
                      />
                      <span className="font-mono text-xs">{event}</span>
                    </label>
                  </li>
                ))}
              </ul>
            </div>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={form.is_active}
                onChange={event => setForm(prev => ({ ...prev, is_active: event.target.checked }))}
              />
              {t("form.active")}
            </label>
            <DialogFooter>
              <Button type="button" variant="ghost" onClick={onClose}>{t("actions.cancel")}</Button>
              <Button type="submit" disabled={form.events.length === 0}>
                {t(isEdit ? "actions.save" : "actions.create")}
              </Button>
            </DialogFooter>
          </form>
        )}
      </DialogContent>
    </Dialog>
  )
}


function SecretReveal({ secret, onClose }) {
  const { t } = useTranslation("integrations")
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(secret)
      toast.success(t("form.copied"))
    } catch (error) {
      toast.error("Copy failed")
    }
  }
  return (
    <div className="space-y-3">
      <p className="text-sm text-gray-700 dark:text-gray-200">{t("form.secretRevealed")}</p>
      <div className="space-y-1">
        <Label>{t("form.secretLabel")}</Label>
        <div className="flex gap-2">
          <Input value={secret} readOnly className="font-mono text-xs" />
          <Button type="button" size="sm" variant="outline" onClick={copy}>
            <Copy size={14} /> {t("form.secretCopy")}
          </Button>
        </div>
      </div>
      <DialogFooter>
        <Button onClick={onClose}>{t("actions.cancel")}</Button>
      </DialogFooter>
    </div>
  )
}


function DeliveryLogDialog({ webhook, onClose }) {
  const { t } = useTranslation("integrations")
  const { data: deliveries = [] } = useWebhookDeliveries(webhook.id)

  const rows = useMemo(() => deliveries.slice(0, 25), [deliveries])

  return (
    <Dialog open onOpenChange={open => { if (!open) onClose() }}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>{t("log.title")} · {webhook.name}</DialogTitle>
        </DialogHeader>
        {rows.length === 0 ? (
          <p className="text-sm text-gray-500 dark:text-gray-400">{t("log.empty")}</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead className="text-gray-500 dark:text-gray-400 text-left">
                <tr>
                  <th className="py-1 pr-2">{t("log.when")}</th>
                  <th className="py-1 pr-2">{t("log.event")}</th>
                  <th className="py-1 pr-2">{t("log.status")}</th>
                  <th className="py-1 pr-2">{t("log.attempts")}</th>
                  <th className="py-1 pr-2">{t("log.error")}</th>
                </tr>
              </thead>
              <tbody>
                {rows.map(delivery => (
                  <tr key={delivery.id} className="border-t border-gray-100 dark:border-gray-800">
                    <td className="py-1 pr-2"><DateLabel iso={delivery.completed_at ?? delivery.created_at} mode="relative" /></td>
                    <td className="py-1 pr-2 font-mono">{delivery.event_type}</td>
                    <td className="py-1 pr-2">
                      <DeliveryStatusBadge delivery={delivery} />
                    </td>
                    <td className="py-1 pr-2 text-center">{delivery.attempt_count}</td>
                    <td className="py-1 pr-2 text-red-500 truncate max-w-[260px]" title={delivery.last_error ?? ""}>
                      {delivery.last_error ?? ""}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}


function DeliveryStatusBadge({ delivery }) {
  const { t } = useTranslation("integrations")
  if (delivery.succeeded) {
    return <Badge variant="success">{t("log.succeeded")} · {delivery.status_code}</Badge>
  }
  if (delivery.completed_at) {
    const label = delivery.status_code ?? "?"
    return <Badge variant="destructive">{t("log.failed")} · {label}</Badge>
  }
  return <Badge variant="secondary">{t("log.pending")}</Badge>
}


function DeleteDialog({ projectId, webhook, onClose }) {
  const { t } = useTranslation("integrations")
  const remove = useDeleteWebhook(projectId)
  const confirmDelete = async () => {
    try {
      await remove.mutateAsync(webhook.id)
      toast.success(t("toast.deleted"))
      onClose()
    } catch (error) {
      toast.error(error?.response?.data?.detail ?? "Failed")
    }
  }
  return (
    <Dialog open onOpenChange={open => { if (!open) onClose() }}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{t("dialog.deleteTitle")}</DialogTitle>
        </DialogHeader>
        <p className="text-sm text-gray-700 dark:text-gray-200">
          {t("dialog.deleteBody", { name: webhook.name })}
        </p>
        <DialogFooter>
          <Button variant="ghost" onClick={onClose}>{t("actions.cancel")}</Button>
          <Button variant="destructive" onClick={confirmDelete}>
            {t("actions.delete")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
