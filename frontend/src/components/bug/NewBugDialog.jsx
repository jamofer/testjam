import { useState } from "react"
import { useTranslation } from "react-i18next"
import { toast } from "sonner"

import { useCreateBug } from "../../hooks/useBugs"
import { useCustomFields } from "../../hooks/useCustomFields"
import { useVersions } from "../../hooks/useVersions"
import { Button } from "../ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "../ui/dialog"
import { Input } from "../ui/input"
import { Label } from "../ui/label"
import { Textarea } from "../ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../ui/select"
import { Badge } from "../ui/badge"
import { EnvironmentPicker } from "../environment/EnvironmentPicker"
import { CustomFieldsForm } from "../customField/CustomFieldInput"
import { SEVERITIES, SEVERITY_VARIANT } from "../../lib/bugConfig"

const VERSION_NONE = "__none__"

export function NewBugDialog({ projectId, trigger, prefill = {}, onCreated }) {
  const { t } = useTranslation("bugs")
  const [open, setOpen] = useState(false)
  const create = useCreateBug(projectId)
  const [title, setTitle] = useState("")
  const [description, setDescription] = useState(prefill.description ?? "")
  const [severity, setSeverity] = useState(prefill.severity ?? "medium")
  const [tagsInput, setTagsInput] = useState((prefill.tags ?? []).join(", "))
  const [environment, setEnvironment] = useState(prefill.environment ?? null)
  const [affectedVersionId, setAffectedVersionId] = useState(prefill.version_id ?? null)
  const [fixedInVersionId, setFixedInVersionId] = useState(prefill.fixed_in_version_id ?? null)
  const [customFields, setCustomFields] = useState({})
  const { data: versions = [] } = useVersions(projectId)
  const { data: customFieldDefs = [] } = useCustomFields(projectId, "bug")

  const reset = () => {
    setTitle("")
    setDescription(prefill.description ?? "")
    setSeverity(prefill.severity ?? "medium")
    setTagsInput((prefill.tags ?? []).join(", "))
    setEnvironment(prefill.environment ?? null)
    setAffectedVersionId(prefill.version_id ?? null)
    setFixedInVersionId(prefill.fixed_in_version_id ?? null)
    setCustomFields({})
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
        version_id: affectedVersionId,
        fixed_in_version_id: fixedInVersionId,
        custom_fields: Object.keys(customFields).length ? customFields : null,
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
                <SelectTrigger>
                  <Badge variant={SEVERITY_VARIANT[severity] ?? "secondary"}>
                    {t(`severity.${severity}`)}
                  </Badge>
                </SelectTrigger>
                <SelectContent>
                  {SEVERITIES.map(value => (
                    <SelectItem key={value} value={value}>
                      <Badge variant={SEVERITY_VARIANT[value] ?? "secondary"}>{t(`severity.${value}`)}</Badge>
                    </SelectItem>
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
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <Label>{t("fields.affectedVersion")}</Label>
              <Select
                value={affectedVersionId ? String(affectedVersionId) : VERSION_NONE}
                onValueChange={(next) => setAffectedVersionId(next === VERSION_NONE ? null : Number(next))}
              >
                <SelectTrigger aria-label={t("fields.affectedVersion")}><SelectValue placeholder={t("fields.affectedVersionPlaceholder")} /></SelectTrigger>
                <SelectContent>
                  <SelectItem value={VERSION_NONE}>{t("fields.affectedVersionNone")}</SelectItem>
                  {versions.map(version => (
                    <SelectItem key={version.id} value={String(version.id)}>{version.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1">
              <Label>{t("fields.fixedInVersion")}</Label>
              <Select
                value={fixedInVersionId ? String(fixedInVersionId) : VERSION_NONE}
                onValueChange={(next) => setFixedInVersionId(next === VERSION_NONE ? null : Number(next))}
              >
                <SelectTrigger aria-label={t("fields.fixedInVersion")}><SelectValue placeholder={t("fields.fixedInVersionPlaceholder")} /></SelectTrigger>
                <SelectContent>
                  <SelectItem value={VERSION_NONE}>{t("fields.fixedInVersionNone")}</SelectItem>
                  {versions.map(version => (
                    <SelectItem key={version.id} value={String(version.id)}>{version.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          {customFieldDefs.length > 0 && (
            <div className="space-y-2 border-t pt-3">
              <CustomFieldsForm
                definitions={customFieldDefs}
                values={customFields}
                onChange={setCustomFields}
              />
            </div>
          )}
          <Button type="submit" className="w-full" disabled={create.isPending || !title.trim()}>
            {t("actions.save")}
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  )
}
