import { executionsApi } from "../api/executions"

export function useExportExecution() {
  const exportPdf = async (execution, results, projectName) => {
    const { exportExecutionPdf } = await import("../lib/exportPdf")
    exportExecutionPdf(execution, results, projectName)
  }

  const exportHtml = (executionId, title) => executionsApi.exportHtml(executionId, title)

  return { exportPdf, exportHtml }
}
