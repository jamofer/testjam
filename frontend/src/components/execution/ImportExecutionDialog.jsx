import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Upload } from "lucide-react"
import { toast } from "sonner"

import { executionsApi } from "../../api/executions"
import { Button } from "../ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "../ui/dialog"
import { Input } from "../ui/input"
import { Label } from "../ui/label"

const FORMATS = [
  { value: "junit", label: "JUnit XML", accept: ".xml" },
  { value: "robotframework", label: "Robot Framework XML", accept: ".xml" },
]

export function ImportExecutionDialog({ projectId }) {
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
      toast.success(`Imported: ${result.created} created, ${result.updated} updated${result.errors?.length ? `, ${result.errors.length} unmatched` : ""}`)
      setOpen(false)
      reset()
      navigate(`/executions/${execution.id}/run`)
    },
    onError: (error) => {
      toast.error(`Import failed: ${error?.response?.data?.detail ?? error.message}`)
    },
  })

  const canSubmit = title.trim() && file && !importMutation.isPending

  return (
    <Dialog open={open} onOpenChange={(next) => { setOpen(next); if (!next) reset() }}>
      <DialogTrigger asChild>
        <Button size="sm" variant="outline">
          <Upload size={14} /> Import results
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader><DialogTitle>Import test results</DialogTitle></DialogHeader>
        <p className="text-sm text-gray-500 -mt-1">
          Creates an automatic execution and ingests the file in one step.
        </p>
        <div className="space-y-3">
          <div className="space-y-1">
            <Label>Title *</Label>
            <Input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Nightly CI #482" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <Label>Version</Label>
              <Input value={version} onChange={(e) => setVersion(e.target.value)} placeholder="1.4.2" />
            </div>
            <div className="space-y-1">
              <Label>Environment</Label>
              <Input value={environment} onChange={(e) => setEnvironment(e.target.value)} placeholder="staging" />
            </div>
          </div>
          <div className="space-y-1">
            <Label>Format</Label>
            <div className="flex gap-3 text-sm">
              {FORMATS.map((option) => (
                <label key={option.value} className="flex items-center gap-1.5 cursor-pointer">
                  <input
                    type="radio"
                    value={option.value}
                    checked={format === option.value}
                    onChange={() => setFormat(option.value)}
                  />
                  {option.label}
                </label>
              ))}
            </div>
          </div>
          <div className="space-y-1">
            <Label>File *</Label>
            <Input
              type="file"
              accept={FORMATS.find(option => option.value === format)?.accept}
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            />
          </div>
          <Button
            className="w-full"
            onClick={() => importMutation.mutate()}
            disabled={!canSubmit}
            loading={importMutation.isPending}
          >
            Import & open execution
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
