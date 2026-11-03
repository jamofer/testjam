import { describe, it, expect, vi, beforeEach } from "vitest"
import { fireEvent, render, screen, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { MemoryRouter, Route, Routes } from "react-router-dom"

import "../i18n"
import { executionsApi } from "../api/executions"
import { ExecutionRunPage } from "../pages/ExecutionRunPage"

vi.mock("sonner", () => ({ toast: { success: vi.fn(), error: vi.fn(), warning: vi.fn() } }))
vi.mock("../api/executions", () => ({
  executionsApi: {
    get: vi.fn(),
    listResults: vi.fn(),
    update: vi.fn(() => Promise.resolve({})),
    reopen: vi.fn(() => Promise.resolve({})),
    updateResult: vi.fn(() => Promise.resolve({})),
  },
}))
vi.mock("../hooks/useExecutionLive", () => ({ useExecutionLive: () => ({ connected: false }) }))
vi.mock("../hooks/useProjects", () => ({ useProject: () => ({ data: { id: 1, name: "Acme" } }) }))
vi.mock("../hooks/useSuites", () => ({
  useSuitesAll: () => ({ data: [{ id: 3, name: "Checkout", parent_suite_id: null }] }),
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
  summary: { total: 2, passed: 1, failed: 0, blocked: 0, not_run: 1 },
  attachments: [],
  custom_fields: {},
}

const RESULTS = [
  { id: 101, execution_id: 9, test_case_id: 1, test_case_title: "Pay by card", status: "passed", step_results: [], attachments: [] },
  { id: 102, execution_id: 9, test_case_id: 2, test_case_title: "Pay by transfer", status: "not_run", step_results: [], attachments: [] },
]

beforeEach(() => {
  vi.clearAllMocks()
  executionsApi.get.mockResolvedValue(EXECUTION)
  executionsApi.listResults.mockResolvedValue(RESULTS)
})

describe("ExecutionRunPage", () => {
  it("lists every result with the run summary", async () => {
    renderPage()

    expect(await screen.findByText("Pay by card")).toBeInTheDocument()
    expect(screen.getByText("Pay by transfer")).toBeInTheDocument()
    expect(screen.getByTestId("run-summary-passed")).toHaveTextContent("1 passed")
  })

  it("marks the focused result with a keyboard shortcut", async () => {
    renderPage()
    await waitFor(() => expect(focusedCard()).toHaveAttribute("data-result-id", "101"))

    fireEvent.keyDown(window, { key: "f" })

    await waitFor(() => expect(executionsApi.updateResult).toHaveBeenCalledWith(101, expect.objectContaining({ status: "failed" })))
  })

  it("moves the focus to the next result", async () => {
    renderPage()
    await waitFor(() => expect(focusedCard()).toHaveAttribute("data-result-id", "101"))

    fireEvent.keyDown(window, { key: "J" })

    await waitFor(() => expect(focusedCard()).toHaveAttribute("data-result-id", "102"))
  })

  it("finishes the run", async () => {
    renderPage()

    fireEvent.click(await screen.findByRole("button", { name: /finish/i }))

    await waitFor(() => expect(executionsApi.update).toHaveBeenCalledWith("9", expect.objectContaining({ status: "completed" })))
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

function focusedCard() {
  return document.querySelector('[data-testid="result-card"][data-focused="true"]')
}
