import { StepResultRow } from "./StepResultRow"

const STEP_TYPE_LABEL = { setup: "Setup", action: null, teardown: "Teardown" }
const STEP_TYPE_HEADER_COLOR = { setup: "text-blue-600 bg-blue-50", teardown: "text-orange-600 bg-orange-50" }

export function StepsSection({ steps, stepResults, onUpdate, onSaveComment, isAutomated }) {
  const byType = { setup: [], action: [], teardown: [] }
  steps.forEach(s => { (byType[s.step_type] ?? byType.action).push(s) })

  return (
    <div className="space-y-3">
      {["setup", "action", "teardown"].map(type => {
        if (!byType[type].length) return null
        const label = STEP_TYPE_LABEL[type]
        const headerColor = STEP_TYPE_HEADER_COLOR[type]
        return (
          <div key={type}>
            {label && (
              <p className={`text-xs font-semibold uppercase tracking-wide px-2 py-1 rounded mb-1 w-fit ${headerColor}`}>
                {label}
              </p>
            )}
            <div className="space-y-2">
              {byType[type].map(step => {
                const sr = stepResults.find(r => r.step_id === step.id)
                return (
                  <StepResultRow key={step.id} step={step} stepResult={sr}
                    onUpdate={onUpdate} onSaveComment={onSaveComment} isAutomated={isAutomated} />
                )
              })}
            </div>
          </div>
        )
      })}
    </div>
  )
}
