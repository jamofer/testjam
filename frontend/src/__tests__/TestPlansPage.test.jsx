import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { MemoryRouter, Route, Routes } from "react-router-dom"
import { TestPlansPage } from "../pages/TestPlansPage"

vi.mock("sonner", () => ({ toast: { success: vi.fn(), error: vi.fn() } }))

// Use vi.fn() directly in factory to avoid hoisting issues
vi.mock("../api/testplans", () => ({
  plansApi: {
    list: vi.fn(() => Promise.resolve([])),
    create: vi.fn(() => Promise.resolve({ id: 99, title: "New Plan", test_case_ids: [] })),
    delete: vi.fn(() => Promise.resolve()),
  },
}))

vi.mock("../api/testcases", () => ({
  suitesApi: {
    list: vi.fn(() => Promise.resolve([])),
    listAll: vi.fn(() => Promise.resolve([])),
    listChildren: vi.fn(() => Promise.resolve([])),
  },
  casesApi: {
    list: vi.fn(() => Promise.resolve([])),
  },
}))

vi.mock("../hooks/useProjects", () => ({
  useProject: () => ({ data: { id: 1, name: "Acme" } }),
}))

import { casesApi } from "../api/testcases"

const SUITES = [
  { id: 1, name: "Auth Suite" },
  { id: 2, name: "Payment Suite" },
]

function setup(plans = [], suites = []) {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0, staleTime: Infinity } },
  })
  qc.setQueryData(["plans", "1"], plans)
  qc.setQueryData(["suites-list-all", "1"], suites)

  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={["/projects/1/plans"]}>
        <Routes>
          <Route path="/projects/:id/plans" element={<TestPlansPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  )
}

beforeEach(() => vi.clearAllMocks())

describe("TestPlansPage — plan list", () => {
  it("lists existing plans with case count", () => {
    setup([{ id: 1, title: "Sprint 12", test_case_ids: [10] }])
    expect(screen.getByText("Sprint 12")).toBeInTheDocument()
    expect(screen.getByText("(1 cases)")).toBeInTheDocument()
  })

  it("shows empty state when there are no plans", () => {
    setup([])
    expect(screen.getByText(/no test plans yet/i)).toBeInTheDocument()
  })
})

describe("CreatePlanDialog — field names (suite.name / tc.name)", () => {
  it("displays suite.name (not suite.title) in the dialog", async () => {
    setup([], SUITES)

    fireEvent.click(screen.getByRole("button", { name: /new plan/i }))

    // Suite names must appear — if code still used suite.title they would be blank
    expect(await screen.findByText("Auth Suite")).toBeInTheDocument()
    expect(screen.getByText("Payment Suite")).toBeInTheDocument()
  })

  it("displays tc.name (not tc.title) for cases inside an expanded suite", async () => {
    casesApi.list.mockImplementation(suiteId =>
      suiteId === 1
        ? Promise.resolve([{ id: 10, name: "Login works" }, { id: 11, name: "Logout works" }])
        : Promise.resolve([])
    )
    setup([], SUITES)

    fireEvent.click(screen.getByRole("button", { name: /new plan/i }))

    // Expand "Auth Suite" <details> by toggling it
    const summary = await screen.findByText("Auth Suite")
    fireEvent.click(summary)

    expect(await screen.findByText("Login works")).toBeInTheDocument()
    expect(screen.getByText("Logout works")).toBeInTheDocument()
  })
})
