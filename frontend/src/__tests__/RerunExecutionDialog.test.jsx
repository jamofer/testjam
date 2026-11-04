import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { MemoryRouter, Route, Routes } from "react-router-dom"

import { RerunExecutionDialog } from "../components/execution/RerunExecutionDialog"

vi.mock("sonner", () => ({ toast: { success: vi.fn(), error: vi.fn() } }))
vi.mock("../api/executions", () => ({
  executionsApi: { rerun: vi.fn() },
}))

import { executionsApi } from "../api/executions"

const COMPLETED_EXECUTION = {
  id: 5,
  project_id: 1,
  title: "Nightly",
  status: "completed",
  summary: { passed: 3, failed: 1, blocked: 1, not_run: 0 },
}

describe("RerunExecutionDialog", () => {
  beforeEach(() => {
    executionsApi.rerun.mockReset()
    executionsApi.rerun.mockResolvedValue({ id: 42 })
  })

  it("re-runs every case and opens the new execution", async () => {
    renderDialog(COMPLETED_EXECUTION)
    fireEvent.click(screen.getByRole("button", { name: /re-run/i }))

    fireEvent.click(screen.getByRole("button", { name: "All cases" }))

    expect(await screen.findByText("run page 42")).toBeInTheDocument()
    expect(executionsApi.rerun).toHaveBeenCalledWith(5, "all")
  })

  it("re-runs only the cases that did not pass", async () => {
    renderDialog(COMPLETED_EXECUTION)
    fireEvent.click(screen.getByRole("button", { name: /re-run/i }))

    fireEvent.click(screen.getByRole("button", { name: "Only the 2 cases that did not pass" }))

    expect(await screen.findByText("run page 42")).toBeInTheDocument()
    expect(executionsApi.rerun).toHaveBeenCalledWith(5, "not_passed")
  })

  it("disables the partial re-run when every case passed", () => {
    renderDialog({ ...COMPLETED_EXECUTION, summary: { passed: 5, failed: 0, blocked: 0, not_run: 0 } })

    fireEvent.click(screen.getByRole("button", { name: /re-run/i }))

    expect(screen.getByRole("button", { name: /did not pass/ })).toBeDisabled()
  })
})

function renderDialog(execution) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/executions/5/run"]}>
        <Routes>
          <Route path="/executions/5/run" element={<RerunExecutionDialog execution={execution} />} />
          <Route path="/executions/42/run" element={<p>run page 42</p>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}
