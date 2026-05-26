import { useState } from "react"
import { useTranslation } from "react-i18next"
import { Copy, Link2, Trash2 } from "lucide-react"
import { toast } from "sonner"

import { publicReportsApi } from "../../api/publicReports"
import {
  useCreatePublicReport,
  usePublicReports,
  useRevokePublicReport,
} from "../../hooks/usePublicReports"
import { Button } from "../ui/button"
import { ConfirmDialog } from "../ui/confirm-dialog"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "../ui/dialog"
import { Input } from "../ui/input"
import { Label } from "../ui/label"
import { DateLabel } from "../ui/date-label"


export function PublicReportDialog({
  projectId,
  trigger,
  defaultKind,
  executionId = null,
  versionId = null,
  environment = null,
}) {
  const { t } = useTranslation(["publicReports", "common"])
  const [open, setOpen] = useState(false)
  const [label, setLabel] = useState("")
  const [expiresAt, setExpiresAt] = useState("")
  const [createdToken, setCreatedToken] = useState(null)
  const [sharePendingRevoke, setSharePendingRevoke] = useState(null)

  const filterByExecution = defaultKind === "execution"
  const { data: shares = [], isLoading } = usePublicReports(projectId, { enabled: open })
  const createShare = useCreatePublicReport(projectId)
  const revokeShare = useRevokePublicReport(projectId)

  const relevantShares = shares.filter(share =>
    share.kind === defaultKind && (filterByExecution ? share.execution_id === executionId : true),
  )

  const reset = () => {
    setLabel("")
    setExpiresAt("")
    setCreatedToken(null)
  }

  const handleCreate = async (event) => {
    event.preventDefault()
    if (expiresAt && new Date(expiresAt) <= new Date()) {
      toast.error(t("expiredDateError"))
      return
    }
    try {
      const payload = {
        kind: defaultKind,
        label: label.trim() || null,
      }
      if (filterByExecution) payload.execution_id = executionId
      else {
        if (versionId) payload.version_id = Number(versionId)
        if (environment) payload.environment = environment
      }
      if (expiresAt) payload.expires_at = new Date(expiresAt).toISOString()
      const created = await createShare.mutateAsync(payload)
      setCreatedToken(created.token)
      toast.success(t("created"))
    } catch (error) {
      toast.error(error?.response?.data?.detail ?? t("createFailed"))
    }
  }

  const confirmRevoke = async () => {
    if (!sharePendingRevoke) return
    try {
      await revokeShare.mutateAsync(sharePendingRevoke.id)
      toast.success(t("revoked"))
    } catch (error) {
      toast.error(error?.response?.data?.detail ?? t("revokeFailed"))
    } finally {
      setSharePendingRevoke(null)
    }
  }

  const copy = async (text) => {
    try {
      await navigator.clipboard.writeText(text)
      toast.success(t("copied"))
    } catch {
      toast.error(t("copyFailed"))
    }
  }

  const fullUrl = createdToken ? publicReportsApi.publicUrl(createdToken) : ""

  return (
    <Dialog open={open} onOpenChange={(next) => { setOpen(next); if (!next) reset() }}>
      <DialogTrigger asChild>{trigger}</DialogTrigger>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>{t(`title.${defaultKind}`)}</DialogTitle>
        </DialogHeader>

        <div className="space-y-4 mt-2">
          <p className="text-sm text-gray-600 dark:text-gray-400">{t("description")}</p>

          {createdToken ? (
            <div className="rounded-lg border border-emerald-200 bg-emerald-50 dark:bg-emerald-950/30 dark:border-emerald-800 p-3 space-y-2">
              <div className="text-xs font-semibold text-emerald-800 dark:text-emerald-300">
                {t("newLinkHeading")}
              </div>
              <div className="flex items-center gap-2">
                <Input value={fullUrl} readOnly className="font-mono text-xs" />
                <Button type="button" size="sm" onClick={() => copy(fullUrl)}>
                  <Copy size={13} /> {t("copy")}
                </Button>
              </div>
              <p className="text-xs text-emerald-800/80 dark:text-emerald-300/80">
                {t("tokenOnceWarning")}
              </p>
            </div>
          ) : (
            <form className="space-y-3" onSubmit={handleCreate}>
              <div className="space-y-1">
                <Label>{t("labelField")}</Label>
                <Input
                  value={label}
                  onChange={event => setLabel(event.target.value)}
                  placeholder={t("labelPlaceholder")}
                  maxLength={128}
                />
              </div>
              <div className="space-y-1">
                <Label>{t("expiresField")}</Label>
                <Input
                  type="datetime-local"
                  value={expiresAt}
                  min={new Date().toISOString().slice(0, 16)}
                  onChange={event => setExpiresAt(event.target.value)}
                />
                <p className="text-xs text-gray-500">{t("expiresHelp")}</p>
              </div>
              <Button type="submit" disabled={createShare.isPending}>
                <Link2 size={14} /> {t("generate")}
              </Button>
            </form>
          )}

          <div className="border-t border-gray-200 dark:border-gray-800 pt-3">
            <div className="text-sm font-semibold mb-2">{t("existingHeading")}</div>
            {isLoading ? (
              <div className="text-xs text-gray-500">{t("common:actions.loading")}</div>
            ) : relevantShares.length === 0 ? (
              <div className="text-xs text-gray-500">{t("noneYet")}</div>
            ) : (
              <ul className="space-y-2">
                {relevantShares.map(share => (
                  <li
                    key={share.id}
                    className="flex items-start justify-between gap-3 rounded border border-gray-200 dark:border-gray-800 px-3 py-2"
                  >
                    <div className="min-w-0">
                      <div className="text-sm font-medium truncate">
                        {share.label ?? t("untitled")}
                      </div>
                      <div className="text-xs text-gray-500 flex flex-wrap gap-x-3 gap-y-1 mt-0.5">
                        <span>
                          {t("createdAt")} <DateLabel iso={share.created_at} mode="relative" />
                        </span>
                        {share.expires_at && (
                          <span>
                            {t("expiresAt")} <DateLabel iso={share.expires_at} mode="relative" />
                          </span>
                        )}
                        <span>{t("viewCount", { count: share.view_count })}</span>
                        {share.revoked_at && (
                          <span className="text-rose-600">{t("revokedAt")}</span>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-1 shrink-0">
                      {!share.revoked_at && (
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={() => setSharePendingRevoke(share)}
                          title={t("revoke")}
                        >
                          <Trash2 size={13} />
                        </Button>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </DialogContent>

      <ConfirmDialog
        open={sharePendingRevoke !== null}
        onOpenChange={(next) => { if (!next) setSharePendingRevoke(null) }}
        title={t("revokeTitle")}
        description={t("revokeDescription")}
        confirmLabel={t("revoke")}
        destructive
        busy={revokeShare.isPending}
        onConfirm={confirmRevoke}
      />
    </Dialog>
  )
}
