import { useRef, useState } from "react"
import { Upload } from "lucide-react"
import { useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"
import { executionsApi } from "../../api/executions"
import { Button } from "../ui/button"

export function ImportResultsButton({ executionId }) {
  const junitRef = useRef()
  const rfRef = useRef()
  const qc = useQueryClient()
  const [importing, setImporting] = useState(false)

  const handleImport = async (file, format) => {
    if (!file) return
    setImporting(true)
    try {
      const fn = format === "junit"
        ? executionsApi.importJunit
        : executionsApi.importRobotFramework
      const result = await fn(executionId, file)
      qc.invalidateQueries({ queryKey: ["results", executionId] })
      qc.invalidateQueries({ queryKey: ["executions", executionId] })
      toast.success(`Imported: ${result.created} created, ${result.updated} updated${result.errors?.length ? `, ${result.errors.length} unmatched` : ""}`)
      if (result.errors?.length) {
        console.warn("Unmatched tests:", result.errors)
      }
    } catch (e) {
      toast.error(`Import failed: ${e.response?.data?.detail ?? e.message}`)
    } finally {
      setImporting(false)
      if (junitRef.current) junitRef.current.value = ""
      if (rfRef.current) rfRef.current.value = ""
    }
  }

  return (
    <div className="flex items-center gap-2">
      <input ref={junitRef} type="file" accept=".xml" className="hidden"
        onChange={e => handleImport(e.target.files[0], "junit")} />
      <input ref={rfRef} type="file" accept=".xml" className="hidden"
        onChange={e => handleImport(e.target.files[0], "robotframework")} />
      <Button size="sm" variant="outline" disabled={importing}
        onClick={() => junitRef.current?.click()}>
        <Upload size={13} /> JUnit XML
      </Button>
      <Button size="sm" variant="outline" disabled={importing}
        onClick={() => rfRef.current?.click()}>
        <Upload size={13} /> Robot Framework
      </Button>
    </div>
  )
}
