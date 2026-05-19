import { useState } from "react"
import { useTranslation } from "react-i18next"
import { Plus, Trash2 } from "lucide-react"
import { toast } from "sonner"

import { useUpdateIntegration } from "../../hooks/useIntegrations"
import { Button } from "../ui/button"
import { Input } from "../ui/input"
import { Label } from "../ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../ui/select"
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "../ui/dialog"


const NORMALIZED_VALUES = ["open", "closed", "unknown"]


export function StatusMappingDialog({ projectId, integration, onClose }) {
  const { t } = useTranslation("integrations")
  const update = useUpdateIntegration(projectId)
  const [rows, setRows] = useState(() =>
    Object.entries(integration.status_mapping ?? {}).map(([source, target]) => ({ source, target })),
  )

  const addRow = () => setRows(prev => [...prev, { source: "", target: "open" }])
  const removeRow = (index) => setRows(prev => prev.filter((_, i) => i !== index))
  const setSource = (index, value) =>
    setRows(prev => prev.map((row, i) => (i === index ? { ...row, source: value } : row)))
  const setTarget = (index, value) =>
    setRows(prev => prev.map((row, i) => (i === index ? { ...row, target: value } : row)))

  const submit = async (event) => {
    event.preventDefault()
    const mapping = {}
    for (const row of rows) {
      const source = row.source.trim()
      if (!source) continue
      mapping[source] = row.target
    }
    try {
      await update.mutateAsync({ id: integration.id, data: { status_mapping: mapping } })
      toast.success(t("statusMapping.saved"))
      onClose()
    } catch (error) {
      toast.error(error?.response?.data?.detail ?? t("statusMapping.saveFailed"))
    }
  }

  return (
    <Dialog open onOpenChange={open => { if (!open) onClose() }}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{t("statusMapping.title", { name: integration.name })}</DialogTitle>
        </DialogHeader>
        <p className="text-xs text-gray-500 dark:text-gray-400">{t("statusMapping.help")}</p>
        <form className="space-y-3" onSubmit={submit}>
          {rows.length === 0 && (
            <p className="text-xs text-gray-400 dark:text-gray-500">{t("statusMapping.empty")}</p>
          )}
          <ul className="space-y-2">
            {rows.map((row, index) => (
              <li key={index} className="flex items-end gap-2">
                <div className="flex-1 space-y-1">
                  <Label className="text-xs">{t("statusMapping.source")}</Label>
                  <Input
                    value={row.source}
                    onChange={event => setSource(index, event.target.value)}
                    placeholder={t("statusMapping.sourcePlaceholder")}
                  />
                </div>
                <div className="w-32 space-y-1">
                  <Label className="text-xs">{t("statusMapping.target")}</Label>
                  <Select value={row.target} onValueChange={value => setTarget(index, value)}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {NORMALIZED_VALUES.map(value => (
                        <SelectItem key={value} value={value}>
                          {t(`bugLinks.status.${value}`)}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => removeRow(index)}
                  className="text-red-500"
                >
                  <Trash2 size={14} />
                </Button>
              </li>
            ))}
          </ul>
          <Button type="button" variant="outline" size="sm" onClick={addRow}>
            <Plus size={13} /> {t("statusMapping.add")}
          </Button>
          <DialogFooter>
            <Button type="button" variant="ghost" onClick={onClose}>{t("actions.cancel")}</Button>
            <Button type="submit" disabled={update.isPending}>{t("statusMapping.save")}</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
