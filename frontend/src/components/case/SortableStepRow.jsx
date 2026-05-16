import { useState } from "react"
import { Trash2, GripVertical } from "lucide-react"
import { useQueryClient } from "@tanstack/react-query"
import { useSortable } from "@dnd-kit/sortable"
import { CSS } from "@dnd-kit/utilities"
import { toast } from "sonner"
import { casesApi } from "../../api/testcases"
import { MdEditor, MdViewer } from "../MdEditor"
import { Button } from "../ui/button"

const STEP_TYPE_STYLE = {
  setup:    "bg-blue-50 text-blue-600 border-blue-200",
  action:   "bg-gray-50 dark:bg-gray-900 text-gray-500 dark:text-gray-400 border-gray-200 dark:border-gray-700",
  teardown: "bg-orange-50 text-orange-600 border-orange-200",
}

export function SortableStepRow({ step, caseId, onDelete }) {
  const [editing, setEditing] = useState(false)
  const [action, setAction] = useState(step.action)
  const [expected, setExpected] = useState(step.expected_result ?? "")
  const qc = useQueryClient()

  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({ id: step.id, activationConstraint: { distance: 5 } })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  }

  const save = async () => {
    await casesApi.updateStep(caseId, step.id, { action, expected_result: expected, order: step.order })
    qc.invalidateQueries({ queryKey: ["case", caseId] })
    setEditing(false)
    toast.success("Step saved")
  }

  const typeStyle = STEP_TYPE_STYLE[step.step_type] ?? STEP_TYPE_STYLE.action

  return (
    <div ref={setNodeRef} style={style} className="border rounded-lg p-3 space-y-2 bg-white dark:bg-gray-900">
      <div className="flex items-start gap-2">
        <button {...attributes} {...listeners} className="text-gray-300 dark:text-gray-600 hover:text-gray-500 dark:hover:text-gray-400 mt-1 cursor-grab touch-none">
          <GripVertical size={14} />
        </button>
        <span className="text-xs font-mono text-gray-400 dark:text-gray-500 mt-1 w-6">{step.order}.</span>
        <span className={`text-xs px-1.5 py-0.5 rounded border mt-0.5 shrink-0 ${typeStyle}`}>
          {step.step_type}
        </span>
        <div className="flex-1">
          {editing ? (
            <div className="space-y-2">
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Step</p>
                <MdEditor value={action} onChange={setAction} height={120} />
              </div>
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Expected result</p>
                <MdEditor value={expected} onChange={setExpected} height={80} />
              </div>
              <div className="flex gap-2">
                <Button size="sm" onClick={save}>Save</Button>
                <Button size="sm" variant="ghost" onClick={() => setEditing(false)}>Cancel</Button>
              </div>
            </div>
          ) : (
            <div className="cursor-pointer" onClick={() => setEditing(true)}>
              <div className="prose prose-sm text-gray-800 dark:text-gray-100"><MdViewer value={step.action} /></div>
              {step.expected_result && (
                <div className="mt-1 text-xs text-gray-400 dark:text-gray-500 italic">
                  Expected: <MdViewer value={step.expected_result} />
                </div>
              )}
            </div>
          )}
        </div>
        <button onClick={onDelete} className="text-gray-300 dark:text-gray-600 hover:text-red-500 mt-1">
          <Trash2 size={13} />
        </button>
      </div>
    </div>
  )
}
