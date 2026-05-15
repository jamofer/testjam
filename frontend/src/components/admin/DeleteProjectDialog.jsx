import { useState } from "react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"

import { projectsApi } from "../../api/projects"
import { Button } from "../ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../ui/dialog"
import { Input } from "../ui/input"
import { Label } from "../ui/label"

export function DeleteProjectDialog({ project, onClose }) {
  const queryClient = useQueryClient()
  const [confirmation, setConfirmation] = useState("")

  const remove = useMutation({
    mutationFn: () => projectsApi.delete(project.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-projects"] })
      queryClient.invalidateQueries({ queryKey: ["projects"] })
      toast.success("Project deleted")
      onClose()
    },
    onError: () => toast.error("Failed to delete project"),
  })

  const matches = confirmation.trim() === project.name

  return (
    <Dialog open onOpenChange={(open) => { if (!open) onClose() }}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Delete project "{project.name}"</DialogTitle>
        </DialogHeader>
        <p className="text-sm text-gray-600 mb-3">
          This permanently removes the project, its suites, cases, and executions. Type the
          project name to confirm.
        </p>
        <div className="space-y-1">
          <Label>Project name</Label>
          <Input
            value={confirmation}
            onChange={(event) => setConfirmation(event.target.value)}
            placeholder={project.name}
          />
        </div>
        <div className="flex justify-end gap-2 pt-3">
          <Button variant="ghost" onClick={onClose}>Cancel</Button>
          <Button
            variant="destructive"
            onClick={() => remove.mutate()}
            disabled={!matches || remove.isPending}
          >
            Delete project
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
