import { useState } from "react"
import { useTranslation } from "react-i18next"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"

import { projectsApi } from "../../api/projects"
import { Button } from "../ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../ui/dialog"
import { Input } from "../ui/input"
import { Label } from "../ui/label"

export function DeleteProjectDialog({ project, onClose }) {
  const { t } = useTranslation("admin")
  const queryClient = useQueryClient()
  const [confirmation, setConfirmation] = useState("")

  const remove = useMutation({
    mutationFn: () => projectsApi.delete(project.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-projects"] })
      queryClient.invalidateQueries({ queryKey: ["projects"] })
      toast.success(t("projects.deleteDialog.deleted"))
      onClose()
    },
    onError: () => toast.error(t("projects.deleteDialog.deleteFailed")),
  })

  const matches = confirmation.trim() === project.name

  return (
    <Dialog open onOpenChange={(open) => { if (!open) onClose() }}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{t("projects.deleteDialog.title", { name: project.name })}</DialogTitle>
        </DialogHeader>
        <p className="text-sm text-gray-600 dark:text-gray-300 mb-3">
          {t("projects.deleteDialog.intro")}
        </p>
        <div className="space-y-1">
          <Label>{t("projects.deleteDialog.name")}</Label>
          <Input
            value={confirmation}
            onChange={(event) => setConfirmation(event.target.value)}
            placeholder={project.name}
          />
        </div>
        <div className="flex justify-end gap-2 pt-3">
          <Button variant="ghost" onClick={onClose}>{t("projects.deleteDialog.cancel")}</Button>
          <Button
            variant="destructive"
            onClick={() => remove.mutate()}
            disabled={!matches || remove.isPending}
          >
            {t("projects.deleteDialog.confirm")}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
