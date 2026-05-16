import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { useTranslation } from "react-i18next"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Upload } from "lucide-react"
import { toast } from "sonner"

import { executionsApi } from "../../api/executions"
import { Button } from "../ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "../ui/dialog"
import { Input } from "../ui/input"
import { Label } from "../ui/label"

const FORMAT_VALUES = [
  { value: "junit", labelKey: "import.junit", accept: ".xml" },
  { value: "robotframework", labelKey: "import.robot", accept: ".xml" },
]

export function ImportExecutionDialog({ projectId }) {
  const { t } = useTranslation("executions")
  const [open, setOpen] = useState(false)
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [title, setTitle] = useState("")
  const [version, setVersion] = useState("")
  const [environment, setEnvironment] = useState("")
  const [format, setFormat] = useState("junit")
  const [file, setFile] = useState(null)

  const reset = () => {
    setTitle("")
    setVersion("")
    setEnvironment("")
    setFormat("junit")
    setFile(null)
  }

  const importMutation = useMutation({
    mutationFn: async () => {
      const created = await executionsApi.create(projectId, {
        title: title.trim(),
        type: "automatic",
        version: version.trim() || undefined,
        environment: environment.trim() || undefined,
        test_case_ids: [],
      })
      const ingestFn = format === "junit"
        ? executionsApi.importJunit
        : executionsApi.importRobotFramework
      const result = await ingestFn(created.id, file)
      return { execution: created, result }
    },
    onSuccess: ({ execution, result }) => {
      queryClient.invalidateQueries({ queryKey: ["executions", projectId] })
      const message = result.errors?.length
        ? t("import.successWithErrors", { created: result.created, updated: result.updated, errors: result.errors.length })
        : t("import.successDetail", { created: result.created, updated: result.updated })
      toast.success(message)
      setOpen(false)
      reset()
      navigate(`/executions/${execution.id}/run`)
    },
    onError: (error) => {
      toast.error(t("import.failed", { message: error?.response?.data?.detail ?? error.message }))
    },
  })

  const canSubmit = title.trim() && file && !importMutation.isPending

  return (
    <Dialog open={open} onOpenChange={(next) => { setOpen(next); if (!next) reset() }}>
      <DialogTrigger asChild>
        <Button size="sm" variant="outline">
          <Upload size={14} /> {t("import.results")}
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader><DialogTitle>{t("import.title")}</DialogTitle></DialogHeader>
        <p className="text-sm text-gray-500 dark:text-gray-400 -mt-1">
          {t("import.subtitle")}
        </p>
        <div className="space-y-3">
          <div className="space-y-1">
            <Label>{t("import.titleField")}</Label>
            <Input value={title} onChange={(event) => setTitle(event.target.value)} placeholder={t("import.titlePlaceholder")} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <Label>{t("import.version")}</Label>
              <Input value={version} onChange={(event) => setVersion(event.target.value)} placeholder={t("import.versionPlaceholder")} />
            </div>
            <div className="space-y-1">
              <Label>{t("import.environment")}</Label>
              <Input value={environment} onChange={(event) => setEnvironment(event.target.value)} placeholder={t("import.environmentPlaceholder")} />
            </div>
          </div>
          <div className="space-y-1">
            <Label>{t("import.format")}</Label>
            <div className="flex gap-3 text-sm">
              {FORMAT_VALUES.map((option) => (
                <label key={option.value} className="flex items-center gap-1.5 cursor-pointer">
                  <input
                    type="radio"
                    value={option.value}
                    checked={format === option.value}
                    onChange={() => setFormat(option.value)}
                  />
                  {t(option.labelKey)}
                </label>
              ))}
            </div>
          </div>
          <div className="space-y-1">
            <Label>{t("import.file")}</Label>
            <Input
              type="file"
              accept={FORMAT_VALUES.find(option => option.value === format)?.accept}
              onChange={(event) => setFile(event.target.files?.[0] ?? null)}
            />
          </div>
          <Button
            className="w-full"
            onClick={() => importMutation.mutate()}
            disabled={!canSubmit}
            loading={importMutation.isPending}
          >
            {t("import.submit")}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
