import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { useTranslation } from "react-i18next"
import { RotateCcw } from "lucide-react"
import { toast } from "sonner"

import { useRerunExecution } from "../../hooks/useExecutions"
import { toastApiError } from "../../lib/apiError"
import { Button } from "../ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../ui/dialog"

export function RerunExecutionDialog({ execution }) {
  const { t } = useTranslation("executions")
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const rerun = useRerunExecution(execution.project_id)
  const notPassedCount = countNotPassed(execution.summary)

  const start = cases => {
    rerun.mutate({ id: execution.id, cases }, {
      onSuccess: created => {
        setOpen(false)
        toast.success(t("rerun.created"))
        navigate(`/executions/${created.id}/run`)
      },
      onError: error => toastApiError(error, t("rerun.failed")),
    })
  }

  return (
    <>
      <Button variant="outline" onClick={() => setOpen(true)}>
        <RotateCcw size={13} /> {t("rerun.open")}
      </Button>
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>{t("rerun.title")}</DialogTitle></DialogHeader>
          <p className="text-sm text-gray-600 dark:text-gray-400">{t("rerun.description")}</p>
          <div className="flex flex-col gap-2">
            <Button onClick={() => start("all")} disabled={rerun.isPending}>
              {t("rerun.all")}
            </Button>
            <Button
              variant="outline"
              onClick={() => start("not_passed")}
              disabled={rerun.isPending || notPassedCount === 0}
            >
              {t("rerun.notPassed", { count: notPassedCount })}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </>
  )
}

function countNotPassed(summary = {}) {
  return (summary.failed ?? 0) + (summary.blocked ?? 0) + (summary.not_run ?? 0)
}
