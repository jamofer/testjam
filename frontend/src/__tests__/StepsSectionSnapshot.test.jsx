import { describe, expect, it, vi } from "vitest"
import { render, screen } from "@testing-library/react"
import { StepsSection } from "../components/execution/StepsSection"

vi.mock("../components/MdEditor", () => ({
  MdViewer: ({ value }) => <span>{value}</span>,
}))

const EDITED_STEP = { id: 1, order: 1, action: "Logout", expected_result: "Signed out", step_type: "action" }

function renderSection(stepResults) {
  return render(
    <StepsSection
      steps={[EDITED_STEP]}
      stepResults={stepResults}
      onUpdate={() => {}}
      onSaveComment={() => {}}
    />,
  )
}


describe("StepsSection execution snapshot", () => {
  it("shows the step text as it was when executed", () => {
    renderSection([
      { id: 9, step_id: 1, status: "passed", step_action: "Login", step_expected_result: "Dashboard shown" },
    ])

    expect(screen.getByText("Login")).toBeInTheDocument()
    expect(screen.queryByText("Logout")).not.toBeInTheDocument()
  })

  it("falls back to the current step text when there is no snapshot", () => {
    renderSection([])

    expect(screen.getByText("Logout")).toBeInTheDocument()
  })
})
