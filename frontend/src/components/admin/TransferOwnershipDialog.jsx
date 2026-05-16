import { useState } from "react"
import { useTranslation } from "react-i18next"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"

import { adminApi } from "../../api/admin"
import { Button } from "../ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../ui/dialog"
import { Label } from "../ui/label"

export function TransferOwnershipDialog({ project, users, onClose }) {
  const { t } = useTranslation("admin")
  const queryClient = useQueryClient()
  const candidates = users.filter((user) => user.is_active && !user.deleted_at)
  const [newOwnerId, setNewOwnerId] = useState(candidates[0]?.id ?? "")

  const transfer = useMutation({
    mutationFn: () => adminApi.transferOwnership(project.id, Number(newOwnerId)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-projects"] })
      toast.success(t("projects.transfer.transferred"))
      onClose()
    },
    onError: () => toast.error(t("projects.transfer.transferFailed")),
  })

  return (
    <Dialog open onOpenChange={(open) => { if (!open) onClose() }}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{t("projects.transfer.title", { name: project.name })}</DialogTitle>
        </DialogHeader>
        <p className="text-sm text-gray-600 dark:text-gray-300 mb-3">{t("projects.transfer.intro")}</p>
        <div className="space-y-1">
          <Label>{t("projects.transfer.newOwner")}</Label>
          <select
            className="w-full rounded-md border px-3 py-2 text-sm"
            value={newOwnerId}
            onChange={(event) => setNewOwnerId(event.target.value)}
          >
            {candidates.map((user) => (
              <option key={user.id} value={user.id}>{user.username}</option>
            ))}
          </select>
        </div>
        <div className="flex justify-end gap-2 pt-3">
          <Button variant="ghost" onClick={onClose}>{t("projects.transfer.cancel")}</Button>
          <Button
            onClick={() => transfer.mutate()}
            disabled={!newOwnerId || transfer.isPending}
          >
            {t("projects.transfer.submit")}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
