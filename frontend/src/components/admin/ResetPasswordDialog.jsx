import { useState } from "react"
import { useTranslation } from "react-i18next"
import { useMutation } from "@tanstack/react-query"
import { toast } from "sonner"
import { Copy } from "lucide-react"

import { usersApi } from "../../api/users"
import { Button } from "../ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../ui/dialog"

export function ResetPasswordDialog({ user, onClose }) {
  const { t } = useTranslation("admin")
  const [temporary, setTemporary] = useState(null)
  const [sent, setSent] = useState(false)

  const reset = useMutation({
    mutationFn: (mode) => usersApi.resetPassword(user.id, mode),
    onSuccess: (data, mode) => {
      if (mode === "temporary_password") {
        setTemporary(data.temporary_password)
      } else {
        setSent(true)
        toast.success(t("users.resetPassword.emailQueued"))
      }
    },
    onError: () => toast.error(t("users.resetPassword.failed")),
  })

  const copy = () => {
    navigator.clipboard.writeText(temporary)
    toast.success(t("users.resetPassword.copied"))
  }

  return (
    <Dialog open onOpenChange={(open) => { if (!open) onClose() }}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{t("users.resetPassword.title", { username: user.username })}</DialogTitle>
        </DialogHeader>
        {!temporary && !sent && (
          <>
            <p className="text-sm text-gray-600 dark:text-gray-300 mb-3">{t("users.resetPassword.intro")}</p>
            <div className="grid grid-cols-2 gap-3">
              <Button
                variant="outline"
                onClick={() => reset.mutate("email")}
                disabled={reset.isPending}
              >
                {t("users.resetPassword.sendEmail")}
              </Button>
              <Button
                onClick={() => reset.mutate("temporary_password")}
                disabled={reset.isPending}
              >
                {t("users.resetPassword.showTemporary")}
              </Button>
            </div>
          </>
        )}
        {sent && (
          <>
            <p className="text-sm text-gray-700 dark:text-gray-200">{t("users.resetPassword.sent", { email: user.email })}</p>
            <div className="flex justify-end pt-3">
              <Button onClick={onClose}>{t("users.resetPassword.done")}</Button>
            </div>
          </>
        )}
        {temporary && (
          <>
            <p className="text-sm text-gray-700 dark:text-gray-200 mb-3">{t("users.resetPassword.share")}</p>
            <div className="flex items-center gap-2 rounded-md border bg-gray-50 dark:bg-gray-900 p-2 font-mono text-sm">
              <span className="grow break-all">{temporary}</span>
              <Button size="icon" variant="ghost" onClick={copy}><Copy size={14} /></Button>
            </div>
            <div className="flex justify-end pt-3">
              <Button onClick={onClose}>{t("users.resetPassword.done")}</Button>
            </div>
          </>
        )}
      </DialogContent>
    </Dialog>
  )
}
