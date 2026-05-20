import { useMemo, useState } from "react"
import { useTranslation } from "react-i18next"
import { useNavigate } from "react-router-dom"
import { useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"
import { AlertTriangle, Archive, ArchiveRestore, Trash2, UserCog } from "lucide-react"

import {
  useArchiveProject,
  useDeleteProject,
  useTransferProjectOwnership,
  useUnarchiveProject,
} from "../../hooks/useProjects"
import { useMembers } from "../../hooks/useMembers"
import { Button } from "../ui/button"
import { Input } from "../ui/input"
import { Label } from "../ui/label"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "../ui/dialog"

export function DangerZoneTab({ projectId, project }) {
  const { t } = useTranslation("projectSettings")
  return (
    <div className="space-y-6">
      <header className="flex items-start gap-3">
        <AlertTriangle size={20} className="text-amber-500 mt-0.5" />
        <div>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">{t("danger.title")}</h2>
          <p className="text-sm text-gray-500 dark:text-gray-400">{t("danger.intro")}</p>
        </div>
      </header>

      <ArchiveSection projectId={projectId} project={project} />
      <TransferSection projectId={projectId} />
      <DeleteSection projectId={projectId} project={project} />
    </div>
  )
}

function DangerCard({ title, description, children }) {
  return (
    <section className="border border-red-200 dark:border-red-900/50 rounded-xl overflow-hidden bg-white dark:bg-gray-900">
      <header className="px-5 py-4 border-b border-red-100 dark:border-red-900/30">
        <h3 className="font-semibold text-gray-900 dark:text-gray-100">{title}</h3>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{description}</p>
      </header>
      <div className="p-5">{children}</div>
    </section>
  )
}

function ArchiveSection({ projectId, project }) {
  const { t } = useTranslation("projectSettings")
  const archive = useArchiveProject()
  const unarchive = useUnarchiveProject()
  const isArchived = !!project?.archived_at

  const handle = async () => {
    try {
      if (isArchived) {
        await unarchive.mutateAsync(projectId)
        toast.success(t("danger.archive.unarchived"))
      } else {
        await archive.mutateAsync(projectId)
        toast.success(t("danger.archive.archived"))
      }
    } catch (err) {
      toast.error(err?.response?.data?.detail ?? t("danger.archive.failed"))
    }
  }

  return (
    <DangerCard title={t("danger.archive.title")} description={t("danger.archive.description")}>
      <Button
        size="sm"
        variant="outline"
        onClick={handle}
        loading={archive.isPending || unarchive.isPending}
      >
        {isArchived ? <ArchiveRestore size={14} /> : <Archive size={14} />}
        {isArchived ? t("danger.archive.unarchive") : t("danger.archive.archive")}
      </Button>
    </DangerCard>
  )
}

function TransferSection({ projectId }) {
  const { t } = useTranslation("projectSettings")
  const transfer = useTransferProjectOwnership()
  const { data: members = [] } = useMembers(projectId)
  const candidates = useMemo(
    () => members.filter(member => member.role !== "owner"),
    [members],
  )
  const [selected, setSelected] = useState("")
  const [confirming, setConfirming] = useState(false)

  const submit = async () => {
    if (!selected) return
    try {
      await transfer.mutateAsync({ id: projectId, newOwnerId: Number(selected) })
      toast.success(t("danger.transfer.success"))
      setSelected("")
      setConfirming(false)
    } catch (err) {
      toast.error(err?.response?.data?.detail ?? t("danger.transfer.failed"))
    }
  }

  return (
    <DangerCard title={t("danger.transfer.title")} description={t("danger.transfer.description")}>
      <div className="flex flex-col gap-3 md:flex-row md:items-end">
        <div className="flex-1 space-y-1">
          <Label>{t("danger.transfer.newOwner")}</Label>
          <select
            value={selected}
            onChange={event => setSelected(event.target.value)}
            disabled={candidates.length === 0}
            className="w-full rounded-md border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 px-3 py-2 text-sm"
          >
            <option value="">{t("danger.transfer.selectPlaceholder")}</option>
            {candidates.map(member => (
              <option key={member.user_id} value={member.user_id}>
                {member.full_name ? `${member.full_name} (@${member.username})` : `@${member.username}`}
              </option>
            ))}
          </select>
        </div>
        <Button
          variant="destructive"
          size="sm"
          onClick={() => setConfirming(true)}
          disabled={!selected || transfer.isPending}
        >
          <UserCog size={14} /> {t("danger.transfer.submit")}
        </Button>
      </div>

      {confirming && (
        <Dialog open onOpenChange={open => { if (!open) setConfirming(false) }}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{t("danger.transfer.title")}</DialogTitle>
            </DialogHeader>
            <p className="text-sm text-gray-700 dark:text-gray-200">
              {t("danger.transfer.description")}
            </p>
            <DialogFooter>
              <Button variant="ghost" onClick={() => setConfirming(false)}>
                {t("common.cancel")}
              </Button>
              <Button variant="destructive" onClick={submit} loading={transfer.isPending}>
                {t("danger.transfer.submit")}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}
    </DangerCard>
  )
}

function DeleteSection({ projectId, project }) {
  const { t } = useTranslation("projectSettings")
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const remove = useDeleteProject()
  const [open, setOpen] = useState(false)
  const [confirmation, setConfirmation] = useState("")
  const matches = !!project?.name && confirmation.trim() === project.name

  const submit = async () => {
    try {
      await remove.mutateAsync(projectId)
      queryClient.removeQueries({ queryKey: ["projects", projectId] })
      toast.success(t("danger.delete.success"))
      navigate("/projects", { replace: true })
    } catch (err) {
      toast.error(err?.response?.data?.detail ?? t("danger.delete.failed"))
    }
  }

  return (
    <DangerCard title={t("danger.delete.title")} description={t("danger.delete.description")}>
      <Button variant="destructive" size="sm" onClick={() => setOpen(true)}>
        <Trash2 size={14} /> {t("danger.delete.button")}
      </Button>

      {open && (
        <Dialog open onOpenChange={(value) => { if (!value) { setOpen(false); setConfirmation("") } }}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{t("danger.delete.dialogTitle", { name: project?.name ?? "" })}</DialogTitle>
            </DialogHeader>
            <p className="text-sm text-gray-700 dark:text-gray-200">
              {t("danger.delete.intro")}
            </p>
            <div className="space-y-1">
              <Label>{t("danger.delete.namePlaceholder")}</Label>
              <Input
                value={confirmation}
                onChange={event => setConfirmation(event.target.value)}
                placeholder={project?.name ?? ""}
                autoFocus
              />
            </div>
            <DialogFooter>
              <Button variant="ghost" onClick={() => { setOpen(false); setConfirmation("") }}>
                {t("common.cancel")}
              </Button>
              <Button
                variant="destructive"
                disabled={!matches || remove.isPending}
                onClick={submit}
                loading={remove.isPending}
              >
                {t("danger.delete.confirm")}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}
    </DangerCard>
  )
}
