import { describe, it, expect } from "vitest"
import { render, screen } from "@testing-library/react"
import { MemoryRouter } from "react-router-dom"
import { ResultListResponsive } from "../components/execution/DetailSuiteGroup"

const ITEMS = [
  {
    id: 1,
    test_case_id: 10,
    test_case_title: "Login OK",
    status: "passed",
    executed_by: "alice",
    executed_at: "2026-05-10T08:00:00Z",
    duration_ms: 1234,
  },
  {
    id: 2,
    test_case_id: 11,
    test_case_title: "Logout OK",
    status: "failed",
    executed_by: "bob",
    executed_at: null,
    duration_ms: null,
  },
]

const updateResult = { mutate: () => {} }

function setup() {
  return render(
    <MemoryRouter>
      <ResultListResponsive items={ITEMS} updateResult={updateResult} />
    </MemoryRouter>,
  )
}

describe("ExecutionDetailPage — responsive table+cards", () => {
  it("renders table for md+", () => {
    setup()
    const table = document.querySelector("table.hidden.md\\:table")
    expect(table).toBeInTheDocument()
    expect(table.textContent).toContain("Login OK")
    expect(table.textContent).toContain("Logout OK")
  })

  it("renders mobile cards (md:hidden) with same items", () => {
    setup()
    const mobile = document.querySelector(".md\\:hidden")
    expect(mobile).toBeInTheDocument()
    expect(mobile.textContent).toContain("Login OK")
    expect(mobile.textContent).toContain("Logout OK")
    expect(mobile.textContent).toContain("alice")
  })

  it("renders status select inside both layouts", () => {
    setup()
    const selects = screen.getAllByRole("combobox")
    expect(selects.length).toBe(4)
  })
})
