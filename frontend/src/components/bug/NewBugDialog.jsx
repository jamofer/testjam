import { useState } from "react"
import { useTranslation } from "react-i18next"
import { toast } from "sonner"

import { useCreateBug } from "../../hooks/useBugs"
import { Button } from "../ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "../ui/dialog"
import { Input } from "../ui/input"
import { Label } from "../ui/label"
import { Textarea } from "../ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../ui/select"
import { EnvironmentPicker } from "../environment/EnvironmentPicker"

const SEVERITIES = ["critical", "high", "medium", "low"]

export function NewBugDialog({ projectId, trigger, prefill = {}, onCreated }) {
  const { t } = useTranslation("bugs")
  const [open, setOpen] = useState(false)
  const create = useCreateBug(projectId)
  const [title, setTitle] = useState("")
  const [description, setDescription] = useState(prefill.description ?? "")
  const [severity, setSeverity] = useState(prefill.severity ?? "medium")
  const [tagsInput, setTagsInput] = useState((prefill.tags ?? []).join(", "))
  const [environment, setEnvironment] = useState(prefill.environment ?? null)

  const reset = () => {
    setTitle("")
    setDescription(prefill.description ?? "")
    setSeverity(prefill.severity ?? "medium")
    setTagsInput((prefill.tags ?? []).join(", "))
    setEnvironment(prefill.environment ?? null)
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    if (!title.trim()) return
    const tags = tagsInput
      .split(",")
      .map(value => value.trim())
      .filter(Boolean)
    try {
      const created = await create.mutateAsync({
        title: title.trim(),
        description: description || null,
        severity,
        tags: tags.length ? tags : null,
        environment: environment || null,
        result_id: prefill.result_id ?? null,
        execution_id: prefill.execution_id ?? null,
        version_id: prefill.version_id ?? null,
      })
      toast.success(t("toast.created"))
      setOpen(false)
      reset()
      if (onCreated) onCreated(created)
    } catch (error) {
      toast.error(error?.response?.data?.detail ?? "Could not create bug")
    }
  }

  return (
    <Dialog open={open} onOpenChange={(next) => { setOpen(next); if (!next) reset() }}>
      <DialogTrigger asChild>{trigger}</DialogTrigger>
      <DialogContent>
        <DialogHeader><DialogTitle>{t("report.dialogTitle")}</DialogTitle></DialogHeader>
        <form className="space-y-3" onSubmit={handleSubmit}>
          <div className="space-y-1">
            <Label>{t("fields.title")}</Label>
            <Input value={title} onChange={event => setTitle(event.target.value)} autoFocus />
          </div>
          <div className="space-y-1">
            <Label>{t("fields.description")}</Label>
            <Textarea value={description} onChange={event => setDescription(event.target.value)} rows={5} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <Label>{t("fields.severity")}</Label>
              <Select value={severity} onValueChange={setSeverity}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {SEVERITIES.map(value => (
                    <SelectItem key={value} value={value}>{t(`severity.${value}`)}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1">
              <Label>{t("fields.environment")}</Label>
              <EnvironmentPicker projectId={projectId} value={environment} onChange={setEnvironment} />
            </div>
          </div>
          <div className="space-y-1">
            <Label>{t("fields.tags")}</Label>
            <Input
              value={tagsInput}
              onChange={event => setTagsInput(event.target.value)}
              placeholder="crash, regression"
            />
          </div>
          <Button type="submit" className="w-full" disabled={create.isPending || !title.trim()}>
            {t("actions.save")}
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  )
}
