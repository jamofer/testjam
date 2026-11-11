import { describe, expect, it, vi } from "vitest"
import { fireEvent, render, screen } from "@testing-library/react"
import { StepResultRow } from "../components/execution/StepResultRow"

vi.mock("../components/MdEditor", () => ({
  MdViewer: ({ value }) => <span>{value}</span>,
}))

const STEP = { id: 1, order: 1, action: "Login", step_type: "action" }
const PASSED_WITH_LOG = { id: 9, step_id: 1, status: "passed", duration_ms: 75, log_output: "**[INFO]** done" }

function renderRow({ stepResult = PASSED_WITH_LOG, isAutomated = true } = {}) {
  return render(
    <StepResultRow
      step={STEP}
      stepResult={stepResult}
      onUpdate={() => {}}
      onSaveComment={() => {}}
      isAutomated={isAutomated}
    />,
  )
}


describe("StepResultRow compact layout", () => {
  it("keeps the log collapsed for a finished step", () => {
    renderRow()

    expect(screen.queryByTestId("step-log-output")).not.toBeInTheDocument()
  })

  it("opens the log from the icon toggle", () => {
    renderRow()

    fireEvent.click(screen.getByRole("button", { name: "Show log" }))

    expect(screen.getByTestId("step-log-output")).toHaveTextContent("done")
  })

  it("closes the log again from the same toggle", () => {
    renderRow()
    fireEvent.click(screen.getByRole("button", { name: "Show log" }))

    fireEvent.click(screen.getByRole("button", { name: "Hide log" }))

    expect(screen.queryByTestId("step-log-output")).not.toBeInTheDocument()
  })

  it("offers no log toggle when the step has no log", () => {
    renderRow({ stepResult: { id: 9, step_id: 1, status: "passed", duration_ms: 75 } })

    expect(screen.queryByTestId("step-log-toggle")).not.toBeInTheDocument()
  })

  it("labels the status icon of an automated step", () => {
    renderRow()

    expect(screen.getByLabelText("Pass")).toBeInTheDocument()
  })

  it("exposes the step status on the row", () => {
    renderRow({ stepResult: { id: 9, step_id: 1, status: "failed" } })

    expect(screen.getByTestId("step-row")).toHaveAttribute("data-status", "failed")
  })

  it("keeps the status buttons for a manual step", () => {
    renderRow({ isAutomated: false })

    expect(screen.getByTitle("Fail")).toBeInTheDocument()
  })
})
