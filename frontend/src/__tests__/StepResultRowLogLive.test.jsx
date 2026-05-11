import { describe, expect, it } from "vitest"
import { render, screen } from "@testing-library/react"
import { StepResultRow } from "../components/execution/StepResultRow"

const STEP = { id: 1, order: 1, action: "Login", step_type: "action" }

function renderRow(stepResult) {
  return render(
    <StepResultRow
      step={STEP}
      stepResult={stepResult}
      onUpdate={() => {}}
      onSaveComment={() => {}}
      isAutomated
    />,
  )
}


describe("StepResultRow live log streaming", () => {
  it("renders the latest log_output prop value", () => {
    renderRow({
      id: 9, step_id: 1, status: "running", duration_ms: null,
      log_output: "**[INFO]** first\n\n**[WARN]** second",
    })

    const panel = screen.getByTestId("step-log-output")
    expect(panel.textContent).toContain("first")
    expect(panel.textContent).toContain("second")
  })

  it("opens the log panel automatically when the step is running", () => {
    renderRow({
      id: 9, step_id: 1, status: "running", duration_ms: null,
      log_output: "**[INFO]** boot",
    })

    expect(screen.getByTestId("step-log-output")).toBeInTheDocument()
  })

  it("updates the panel when new lines arrive via re-render", () => {
    const { rerender } = renderRow({
      id: 9, step_id: 1, status: "running", duration_ms: null,
      log_output: "**[INFO]** first",
    })
    rerender(
      <StepResultRow
        step={STEP}
        stepResult={{
          id: 9, step_id: 1, status: "running", duration_ms: null,
          log_output: "**[INFO]** first\n\n**[INFO]** second",
        }}
        onUpdate={() => {}}
        onSaveComment={() => {}}
        isAutomated
      />,
    )

    expect(screen.getByTestId("step-log-output").textContent).toContain("second")
  })

  it("auto-scrolls the panel to the bottom when log_output grows", () => {
    const { rerender } = renderRow({
      id: 9, step_id: 1, status: "running", duration_ms: null,
      log_output: "**[INFO]** first",
    })
    const panel = screen.getByTestId("step-log-output")
    Object.defineProperty(panel, "scrollHeight", { configurable: true, value: 500 })
    panel.scrollTop = 0

    rerender(
      <StepResultRow
        step={STEP}
        stepResult={{
          id: 9, step_id: 1, status: "running", duration_ms: null,
          log_output: "**[INFO]** first\n\n**[INFO]** second",
        }}
        onUpdate={() => {}}
        onSaveComment={() => {}}
        isAutomated
      />,
    )

    expect(panel.scrollTop).toBe(500)
  })
})
