import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { MemoryRouter, Route, Routes } from "react-router-dom"
import { SuiteRow } from "../components/project/SuiteRow"

vi.mock("../components/MdEditor", () => ({
  MdEditor: ({ value, onChange }) => (
    <textarea value={value ?? ""} onChange={e => onChange(e.target.value)} />
  ),
  MdViewer: ({ value }) => <span>{value}</span>,
}))

vi.mock("sonner", () => ({ toast: { success: vi.fn(), error: vi.fn() } }))

vi.mock("../api/testcases", () => ({
  casesApi: {
    list: vi.fn(() => Promise.resolve([])),
    delete: vi.fn(),
    bulkDelete: vi.fn(() => Promise.resolve({ deleted: 0 })),
    reorderSteps: vi.fn(),
  },
  suitesApi: {
    listChildren: vi.fn(() => Promise.resolve([])),
    list: vi.fn(() => Promise.resolve([])),
    get: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
    createStep: vi.fn(),
    updateStep: vi.fn(),
    deleteStep: vi.fn(),
    deleteStepsByType: vi.fn(),
    reorderSteps: vi.fn(),
  },
}))

vi.mock("../api/testplans", () => ({
  plansApi: {
    list: vi.fn(() => Promise.resolve([])),
    addCases: vi.fn(() => Promise.resolve({})),
  },
}))

const SUITE = {
  id: 10,
  name: "My Suite",
  tags: [],
  steps: [],
  description: null,
  test_case_ids: [1, 2],
  child_suite_ids: [],
}

const CASES = [
  { id: 1, name: "Login test" },
  { id: 2, name: "Signup test" },
]

function setup(plans = []) {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0, staleTime: Infinity } },
  })
  qc.setQueryData(["cases-list", 10], CASES)
  qc.setQueryData(["plans", "1"], plans)
  qc.setQueryData(["suites-list", "1", 10], [])

  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={["/projects/1"]}>
        <Routes>
          <Route path="/projects/:id" element={<SuiteRow suite={SUITE} projectId="1" />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  )
}

describe("CaseList — Select all", () => {
  beforeEach(() => vi.clearAllMocks())

  it("renders case names", () => {
    setup()
    expect(screen.getByText("Login test")).toBeInTheDocument()
    expect(screen.getByText("Signup test")).toBeInTheDocument()
  })

  it("shows the Delete button in the bulk bar after clicking Select all", () => {
    setup()
    fireEvent.click(screen.getByLabelText(/select all/i))
    // The Delete button only appears in the bulk action bar
    expect(screen.getByRole("button", { name: /delete/i })).toBeInTheDocument()
  })

  it("does not render the plan selector when there are no plans — prevents SelectItem value='' crash", () => {
    setup([])
    fireEvent.click(screen.getByLabelText(/select all/i))
    // With our fix, the Select (combobox) should not exist when plans === []
    expect(screen.queryByRole("combobox")).toBeNull()
  })

  it("renders a plan combobox when plans exist", () => {
    setup([{ id: 5, title: "Sprint 1" }])
    fireEvent.click(screen.getByLabelText(/select all/i))
    // The SelectTrigger renders as role=combobox
    expect(screen.getByRole("combobox")).toBeInTheDocument()
  })

  it("deselects all when clicking Select all a second time, hiding the bulk bar", () => {
    setup()
    const checkbox = screen.getByLabelText(/select all/i)
    fireEvent.click(checkbox)
    expect(screen.getByRole("button", { name: /delete/i })).toBeInTheDocument()
    // Click again to deselect
    fireEvent.click(screen.getByLabelText(/2 selected/i))
    expect(screen.queryByRole("button", { name: /delete/i })).toBeNull()
  })

  it("checkbox becomes indeterminate when only some cases are selected", () => {
    setup()
    const checkboxes = screen.getAllByRole("checkbox")
    // First checkbox is "Select all", rest are individual cases
    fireEvent.click(checkboxes[1])
    const selectAll = screen.getByLabelText(/1 selected/i)
    expect(selectAll.indeterminate).toBe(true)
  })
})
