import { useState } from "react"
import { useTranslation } from "react-i18next"
import { toast } from "sonner"

import { useRotateIntegrationCredential } from "../../hooks/useIntegrations"
import { Button } from "../ui/button"
import { Input } from "../ui/input"
import { Label } from "../ui/label"
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "../ui/dialog"


export function RotateCredentialDialog({ projectId, integration, onClose }) {
  const { t } = useTranslation("integrations")
  const [secret, setSecret] = useState("")
  const rotate = useRotateIntegrationCredential(projectId)
  const submit = async (event) => {
    event.preventDefault()
    try {
      await rotate.mutateAsync({ id: integration.id, secret })
      toast.success(t("trackers.rotated"))
      onClose()
    } catch (error) {
      toast.error(error?.response?.data?.detail ?? t("trackers.rotateFailed"))
    }
  }
  return (
    <Dialog open onOpenChange={open => { if (!open) onClose() }}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{t("trackers.rotateTitle", { name: integration.name })}</DialogTitle>
        </DialogHeader>
        <form className="space-y-3" onSubmit={submit}>
          <div className="space-y-1">
            <Label>{t("trackers.dialog.secret")}</Label>
            <Input
              type="password"
              value={secret}
              onChange={event => setSecret(event.target.value)}
              required
            />
          </div>
          <DialogFooter>
            <Button type="button" variant="ghost" onClick={onClose}>{t("actions.cancel")}</Button>
            <Button type="submit" disabled={!secret || rotate.isPending}>
              {t("trackers.rotate")}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
