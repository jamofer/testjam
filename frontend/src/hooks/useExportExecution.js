import { executionsApi } from "../api/executions"
import { useMe } from "./useAuth"
import { browserTimezone } from "../lib/format"

export function useExportExecution() {
  const { data: me } = useMe()

  const exportPdf = async (execution, results, projectName) => {
    const { exportExecutionPdf } = await import("../lib/exportPdf")
    exportExecutionPdf(execution, results, projectName, {
      timezone: me?.timezone || browserTimezone() || "UTC",
      username: me?.username || "",
    })
  }

  const exportHtml = (executionId, title) => executionsApi.exportHtml(executionId, title)

  return { exportPdf, exportHtml }
}
