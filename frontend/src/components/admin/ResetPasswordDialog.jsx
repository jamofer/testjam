import { useState } from "react"
import { useMutation } from "@tanstack/react-query"
import { toast } from "sonner"
import { Copy } from "lucide-react"

import { usersApi } from "../../api/users"
import { Button } from "../ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../ui/dialog"

export function ResetPasswordDialog({ user, onClose }) {
  const [temporary, setTemporary] = useState(null)
  const [sent, setSent] = useState(false)

  const reset = useMutation({
    mutationFn: (mode) => usersApi.resetPassword(user.id, mode),
    onSuccess: (data, mode) => {
      if (mode === "temporary_password") {
        setTemporary(data.temporary_password)
      } else {
        setSent(true)
        toast.success("Reset email queued")
      }
    },
    onError: () => toast.error("Failed to reset password"),
  })

  const copy = () => {
    navigator.clipboard.writeText(temporary)
    toast.success("Copied to clipboard")
  }

  return (
    <Dialog open onOpenChange={(open) => { if (!open) onClose() }}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Reset password for "{user.username}"</DialogTitle>
        </DialogHeader>
        {!temporary && !sent && (
          <>
            <p className="text-sm text-gray-600 dark:text-gray-300 mb-3">
              Sending an email keeps a self-serve audit trail. Showing a temporary password
              works even when SMTP is down, but only once — copy it before closing.
            </p>
            <div className="grid grid-cols-2 gap-3">
              <Button
                variant="outline"
                onClick={() => reset.mutate("email")}
                disabled={reset.isPending}
              >
                Send reset email
              </Button>
              <Button
                onClick={() => reset.mutate("temporary_password")}
                disabled={reset.isPending}
              >
                Show temporary password
              </Button>
            </div>
          </>
        )}
        {sent && (
          <>
            <p className="text-sm text-gray-700 dark:text-gray-200">
              Sent. The link is valid for 24 hours and arrives at <b>{user.email}</b>.
            </p>
            <div className="flex justify-end pt-3">
              <Button onClick={onClose}>Done</Button>
            </div>
          </>
        )}
        {temporary && (
          <>
            <p className="text-sm text-gray-700 dark:text-gray-200 mb-3">
              Share this password securely. It will not be shown again.
            </p>
            <div className="flex items-center gap-2 rounded-md border bg-gray-50 dark:bg-gray-900 p-2 font-mono text-sm">
              <span className="grow break-all">{temporary}</span>
              <Button size="icon" variant="ghost" onClick={copy}><Copy size={14} /></Button>
            </div>
            <div className="flex justify-end pt-3">
              <Button onClick={onClose}>Done</Button>
            </div>
          </>
        )}
      </DialogContent>
    </Dialog>
  )
}
