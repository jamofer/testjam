import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { MemoryRouter, Route, Routes } from "react-router-dom"
import { PlanDetailPage } from "../pages/PlanDetailPage"

vi.mock("sonner", () => ({ toast: { success: vi.fn(), error: vi.fn() } }))

vi.mock("../api/testplans", () => ({
  plansApi: {
    get: vi.fn(),
    update: vi.fn(() => Promise.resolve()),
    addCases: vi.fn(() => Promise.resolve()),
  },
}))

vi.mock("../api/testcases", () => ({
  suitesApi: {
    list: vi.fn(() => Promise.resolve([])),
    listAll: vi.fn(() => Promise.resolve([])),
    listChildren: vi.fn(() => Promise.resolve([])),
  },
  casesApi: {
    get: vi.fn(),
    list: vi.fn(() => Promise.resolve([])),
  },
}))

vi.mock("../hooks/useProjects", () => ({
  useProject: () => ({ data: { id: 1, name: "Acme" } }),
}))

import { plansApi } from "../api/testplans"
import { casesApi, suitesApi } from "../api/testcases"

const PLAN = { id: 42, title: "Sprint 12", project_id: 1, test_case_ids: [10, 11] }
const CASES = [
  { id: 10, name: "Login works", suite_id: 1 },
  { id: 11, name: "Logout works", suite_id: 1 },
]

function setup({ plan = PLAN, cases = CASES, suites = [] } = {}) {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0, staleTime: Infinity } },
  })
  qc.setQueryData(["plan", plan.id], plan)
  qc.setQueryData(["plan-cases", plan.id, plan.test_case_ids], cases)
  qc.setQueryData(["suites-list-all", plan.project_id], suites)

  plansApi.get.mockResolvedValue(plan)
  casesApi.get.mockImplementation(id => Promise.resolve(cases.find(c => c.id === id)))

  return { qc, ...render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[`/plans/${plan.id}`]}>
        <Routes>
          <Route path="/plans/:id" element={<PlanDetailPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  )}
}

beforeEach(() => vi.clearAllMocks())

describe("PlanDetailPage — case list", () => {
  it("shows existing cases", () => {
    setup()
    expect(screen.getByText("Login works")).toBeInTheDocument()
    expect(screen.getByText("Logout works")).toBeInTheDocument()
  })

  it("shows empty state when no cases", () => {
    setup({ plan: { ...PLAN, test_case_ids: [] }, cases: [] })
    expect(screen.getByText(/no test cases/i)).toBeInTheDocument()
  })

  it("shows correct case count", () => {
    setup()
    expect(screen.getByText("2 test cases")).toBeInTheDocument()
  })
})

describe("PlanDetailPage — add cases", () => {
  it("opens add cases dialog on button click", async () => {
    setup()
    fireEvent.click(screen.getByRole("button", { name: /add cases/i }))
    expect(await screen.findByText("Add test cases")).toBeInTheDocument()
  })

  it("calls addCases and invalidates plan query", async () => {
    const suite = { id: 1, name: "Auth Suite", parent_suite_id: null }
    casesApi.list.mockResolvedValue([{ id: 20, name: "New case" }])

    const { qc } = setup({ suites: [suite] })
    const invalidate = vi.spyOn(qc, "invalidateQueries")

    fireEvent.click(screen.getByRole("button", { name: /add cases/i }))

    const summary = await screen.findByText("Auth Suite")
    fireEvent.click(summary)

    const checkbox = await screen.findByRole("checkbox")
    fireEvent.click(checkbox)

    fireEvent.click(screen.getByRole("button", { name: /add to plan/i }))

    await waitFor(() => expect(plansApi.addCases).toHaveBeenCalledWith(42, [20]))
    expect(invalidate).toHaveBeenCalledWith({ queryKey: ["plan", 42] })
  })
})

describe("PlanDetailPage — remove case", () => {
  it("calls update with remaining ids on remove", async () => {
    plansApi.update.mockResolvedValue({ ...PLAN, test_case_ids: [11] })
    setup()

    // Hover reveals the X button for the first case
    const listItem = screen.getByText("Login works").closest("li")
    fireEvent.mouseOver(listItem)
    const removeBtn = listItem.querySelector("button")
    fireEvent.click(removeBtn)

    await waitFor(() =>
      expect(plansApi.update).toHaveBeenCalledWith("42", { test_case_ids: [11] })
    )
  })
})
