import { useState } from "react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"

import { adminApi } from "../../api/admin"
import { Button } from "../ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../ui/dialog"
import { Label } from "../ui/label"

export function TransferOwnershipDialog({ project, users, onClose }) {
  const queryClient = useQueryClient()
  const candidates = users.filter((user) => user.is_active && !user.deleted_at)
  const [newOwnerId, setNewOwnerId] = useState(candidates[0]?.id ?? "")

  const transfer = useMutation({
    mutationFn: () => adminApi.transferOwnership(project.id, Number(newOwnerId)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-projects"] })
      toast.success("Ownership transferred")
      onClose()
    },
    onError: () => toast.error("Failed to transfer ownership"),
  })

  return (
    <Dialog open onOpenChange={(open) => { if (!open) onClose() }}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Transfer ownership of "{project.name}"</DialogTitle>
        </DialogHeader>
        <p className="text-sm text-gray-600 dark:text-gray-300 mb-3">
          The current owner becomes an <b>editor</b>. The new owner gets the <b>owner</b> role.
        </p>
        <div className="space-y-1">
          <Label>New owner</Label>
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
          <Button variant="ghost" onClick={onClose}>Cancel</Button>
          <Button
            onClick={() => transfer.mutate()}
            disabled={!newOwnerId || transfer.isPending}
          >
            Transfer
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
