import { useState } from "react"
import { useTranslation } from "react-i18next"
import { Upload } from "lucide-react"
import { toast } from "sonner"

import { useImportCasesCsv } from "../../hooks/useSuites"
import { toastApiError } from "../../lib/apiError"
import { Button } from "../ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../ui/dialog"
import { Input } from "../ui/input"

const CSV_COLUMNS = "suite, name, description, preconditions, tags, external_id, steps, expected"

export function ImportCasesDialog({ projectId }) {
  const { t } = useTranslation("suites")
  const [open, setOpen] = useState(false)
  const [file, setFile] = useState(null)
  const [report, setReport] = useState(null)
  const importCsv = useImportCasesCsv(projectId)

  const changeOpen = next => {
    setOpen(next)
    if (!next) {
      setFile(null)
      setReport(null)
    }
  }

  const submit = event => {
    event.preventDefault()
    importCsv.mutate(file, {
      onSuccess: result => {
        setReport(result)
        toast.success(t("importCsv.created", { count: result.created }))
      },
      onError: error => toastApiError(error, t("importCsv.failed")),
    })
  }

  return (
    <>
      <Button size="sm" variant="outline" onClick={() => setOpen(true)}>
        <Upload size={13} /> {t("importCsv.open")}
      </Button>
      <Dialog open={open} onOpenChange={changeOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>{t("importCsv.title")}</DialogTitle></DialogHeader>
          {report ? <ImportReport report={report} /> : (
            <form className="space-y-3" onSubmit={submit}>
              <p className="text-sm text-gray-600 dark:text-gray-400">{t("importCsv.description")}</p>
              <code className="block text-xs bg-gray-100 dark:bg-gray-800 rounded px-2 py-1.5 text-gray-600 dark:text-gray-300">
                {CSV_COLUMNS}
              </code>
              <p className="text-xs text-gray-500 dark:text-gray-400">{t("importCsv.hint")}</p>
              <Input
                type="file"
                accept=".csv,text/csv"
                aria-label={t("importCsv.file")}
                onChange={event => setFile(event.target.files[0] ?? null)}
              />
              <div className="flex justify-end">
                <Button type="submit" disabled={!file || importCsv.isPending} loading={importCsv.isPending}>
                  {t("importCsv.submit")}
                </Button>
              </div>
            </form>
          )}
        </DialogContent>
      </Dialog>
    </>
  )
}

function ImportReport({ report }) {
  const { t } = useTranslation("suites")
  return (
    <div className="space-y-2 text-sm">
      <p data-testid="import-summary">
        {t("importCsv.summary", { count: report.created, suites: report.suites_created })}
      </p>
      {report.errors.length > 0 && (
        <ul className="max-h-48 overflow-y-auto space-y-1 text-xs text-red-600 dark:text-red-400">
          {report.errors.map(error => (
            <li key={error.row}>{t("importCsv.rowError", { row: error.row, name: error.name, error: error.error })}</li>
          ))}
        </ul>
      )}
    </div>
  )
}
