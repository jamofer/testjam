import { describe, it, expect, vi, beforeEach } from "vitest"
import { fireEvent, render, screen, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { MemoryRouter, Route, Routes, useParams } from "react-router-dom"
import { toast } from "sonner"

import "../i18n"
import { NewExecutionPage } from "../pages/NewExecutionPage"

const createExecution = vi.fn()

vi.mock("sonner", () => ({ toast: { success: vi.fn(), error: vi.fn() } }))
vi.mock("../hooks/useExecutions", () => ({
  useCreateExecution: () => ({ mutateAsync: createExecution, isPending: false }),
}))
vi.mock("../hooks/useVersions", () => ({ useVersions: () => ({ data: [] }) }))
vi.mock("../hooks/useMembers", () => ({ useMembers: () => ({ data: [] }) }))
vi.mock("../hooks/useProjects", () => ({ useProject: () => ({ data: { id: 1, name: "Acme" } }) }))
vi.mock("../hooks/useCustomFields", () => ({ useCustomFields: () => ({ data: [] }) }))
vi.mock("../api/testplans", () => ({ plansApi: { list: () => Promise.resolve([]) } }))
vi.mock("../components/ui/case-picker", () => ({
  CasePicker: ({ onToggle }) => <button type="button" onClick={() => onToggle(7)}>Pick case 7</button>,
}))
vi.mock("../components/environment/EnvironmentPicker", () => ({ EnvironmentPicker: () => null }))
vi.mock("../components/MdEditor", () => ({ MdEditor: () => null }))

beforeEach(() => {
  vi.clearAllMocks()
  createExecution.mockResolvedValue({ id: 42 })
})

describe("NewExecutionPage", () => {
  it("refuses to create a run without a title", async () => {
    renderPage()

    fireEvent.click(screen.getByRole("button", { name: "Create & start execution" }))

    await waitFor(() => expect(toast.error).toHaveBeenCalledWith("Title is required"))
    expect(createExecution).not.toHaveBeenCalled()
  })

  it("creates the run with the picked cases and opens it", async () => {
    renderPage()
    fireEvent.change(screen.getByPlaceholderText("Sprint 23 regression…"), { target: { value: "Sprint 24" } })
    fireEvent.click(screen.getByRole("button", { name: "Pick case 7" }))

    fireEvent.click(screen.getByRole("button", { name: "Create & start execution" }))

    await waitFor(() => expect(createExecution).toHaveBeenCalledWith(
      expect.objectContaining({ title: "Sprint 24", type: "manual", test_case_ids: [7] }),
    ))
    expect(await screen.findByText("run page of 42")).toBeInTheDocument()
  })
})

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/projects/1/executions/new"]}>
        <Routes>
          <Route path="/projects/:id/executions/new" element={<NewExecutionPage />} />
          <Route path="/executions/:id/run" element={<RunPageStub />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

function RunPageStub() {
  const { id } = useParams()
  return <p>run page of {id}</p>
}
