import { StepResultRow } from "./StepResultRow"

const STEP_TYPE_LABEL = { setup: "Setup", action: null, teardown: "Teardown" }
const STEP_TYPE_HEADER_COLOR = { setup: "text-blue-600 bg-blue-50", teardown: "text-orange-600 bg-orange-50" }
const STEP_TYPE_GROUP_BORDER = {
  setup: "border-l-4 border-blue-300 pl-3",
  teardown: "border-l-4 border-orange-300 pl-3",
}

export function StepsSection({ steps, stepResults, onUpdate, onSaveComment, isAutomated, focusedStepId = null }) {
  const byType = { setup: [], action: [], teardown: [] }
  steps.forEach(s => { (byType[s.step_type] ?? byType.action).push(s) })

  return (
    <div className="space-y-4">
      {["setup", "action", "teardown"].map(type => {
        const typeSteps = byType[type]
        if (!typeSteps.length) return null
        const label = STEP_TYPE_LABEL[type]
        const headerColor = STEP_TYPE_HEADER_COLOR[type]
        const groupBorder = STEP_TYPE_GROUP_BORDER[type] ?? ""
        return (
          <div key={type} className={groupBorder}>
            {label && (
              <p className={`text-xs font-semibold uppercase tracking-wide px-2 py-1 rounded mb-2 w-fit ${headerColor}`}>
                {label} <span className="font-normal opacity-70">({typeSteps.length})</span>
              </p>
            )}
            <div className="space-y-2">
              {typeSteps.map(step => {
                const sr = stepResults.find(r => r.step_id === step.id)
                return (
                  <StepResultRow key={step.id} step={step} stepResult={sr}
                    onUpdate={onUpdate} onSaveComment={onSaveComment} isAutomated={isAutomated}
                    focused={step.id === focusedStepId} />
                )
              })}
            </div>
          </div>
        )
      })}
    </div>
  )
}
