import { describe, it, expect, vi, beforeEach } from "vitest"
import { fireEvent, render, screen, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { MemoryRouter, Route, Routes } from "react-router-dom"

import { executionsApi } from "../api/executions"
import { ExecutionRunPage } from "../pages/ExecutionRunPage"

vi.mock("sonner", () => ({ toast: { success: vi.fn(), error: vi.fn(), warning: vi.fn() } }))
vi.mock("../api/executions", () => ({
  executionsApi: {
    get: vi.fn(),
    listResults: vi.fn(),
    updateResult: vi.fn(() => Promise.resolve({})),
  },
}))
vi.mock("../hooks/useAuth", () => ({ useMe: () => ({ data: { id: 7, username: "alice" } }) }))
vi.mock("../hooks/useMembers", () => ({
  useEffectiveMembers: () => ({ data: [{ user_id: 7, username: "alice" }, { user_id: 8, username: "bob" }] }),
}))
vi.mock("../hooks/useExecutionLive", () => ({ useExecutionLive: () => ({ connected: false }) }))
vi.mock("../hooks/useProjects", () => ({ useProject: () => ({ data: { id: 1, name: "Acme" } }) }))
vi.mock("../hooks/useSuites", () => ({
  useSuitesAll: () => ({ data: [] }),
  useCase: () => ({ data: undefined }),
}))
vi.mock("../hooks/useExportExecution", () => ({
  useExportExecution: () => ({ exportPdf: vi.fn(), exportHtml: vi.fn() }),
}))
vi.mock("../components/environment/EnvironmentBadge", () => ({ EnvironmentBadge: () => null }))

const EXECUTION = {
  id: 9,
  project_id: 1,
  title: "Nightly",
  type: "manual",
  status: "in_progress",
  created_at: "2026-11-01T10:00:00Z",
  summary: { total: 2, passed: 0, failed: 0, blocked: 0, not_run: 2 },
  attachments: [],
  custom_fields: {},
}

const MY_RESULT = {
  id: 101, execution_id: 9, test_case_id: 1, test_case_title: "Pay by card",
  status: "not_run", assigned_to_id: 7, step_results: [], attachments: [],
}
const UNASSIGNED_RESULT = {
  id: 102, execution_id: 9, test_case_id: 2, test_case_title: "Pay by transfer",
  status: "not_run", assigned_to_id: null, step_results: [], attachments: [],
}

beforeEach(() => {
  vi.clearAllMocks()
  executionsApi.get.mockResolvedValue(EXECUTION)
  executionsApi.listResults.mockResolvedValue([MY_RESULT, UNASSIGNED_RESULT])
})

describe("result assignee", () => {
  it("shows the assignee on the result header", async () => {
    renderPage()

    expect(await screen.findByTestId("result-assignee")).toHaveTextContent("alice")
  })

  it("narrows the run to my results", async () => {
    renderPage()
    await screen.findByText("Pay by transfer")

    fireEvent.click(screen.getByRole("button", { name: "Only mine" }))

    expect(screen.getByText("Pay by card")).toBeInTheDocument()
    expect(screen.queryByText("Pay by transfer")).not.toBeInTheDocument()
  })

  it("hides the filter when nothing is assigned to me", async () => {
    executionsApi.listResults.mockResolvedValue([UNASSIGNED_RESULT])

    renderPage()
    await screen.findByText("Pay by transfer")

    expect(screen.queryByRole("button", { name: "Only mine" })).not.toBeInTheDocument()
  })

  it("assigns a result to another member", async () => {
    renderPage()
    fireEvent.click(await screen.findByRole("combobox", { name: "Assignee" }))

    fireEvent.click(screen.getByRole("option", { name: "bob" }))

    await waitFor(() => expect(executionsApi.updateResult).toHaveBeenCalledWith(101, { assigned_to_id: 8 }))
  })

  it("clears the assignee", async () => {
    renderPage()
    fireEvent.click(await screen.findByRole("combobox", { name: "Assignee" }))

    fireEvent.click(screen.getByRole("option", { name: "Unassigned" }))

    await waitFor(() => expect(executionsApi.updateResult).toHaveBeenCalledWith(101, { assigned_to_id: null }))
  })
})

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/executions/9/run"]}>
        <Routes>
          <Route path="/executions/:id/run" element={<ExecutionRunPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}
