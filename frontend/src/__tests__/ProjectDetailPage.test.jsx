import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { MemoryRouter, Route, Routes } from "react-router-dom"
import { ProjectDetailPage } from "../pages/ProjectDetailPage"

vi.mock("sonner", () => ({ toast: { success: vi.fn(), error: vi.fn() } }))

vi.mock("../api/testcases", () => ({
  suitesApi: {
    list: vi.fn(() => Promise.resolve([{ id: 1, name: "Suite A", project_id: 1 }])),
  },
  casesApi: {
    search: vi.fn(),
  },
}))

vi.mock("../api/projects", () => ({
  projectsApi: {
    get: vi.fn(() => Promise.resolve({ id: 1, name: "Acme", suite_count: 1, case_count: 0, execution_count: 0 })),
  },
}))

vi.mock("../components/project/SuiteRow", () => ({
  SuiteRow: ({ suite }) => <div data-testid={`suite-${suite.id}`}>{suite.name}</div>,
}))

vi.mock("../components/project/VersionsPanel", () => ({
  VersionsPanel: () => <div />,
}))

import { casesApi } from "../api/testcases"

function setup() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0, staleTime: Infinity } },
  })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={["/projects/1"]}>
        <Routes>
          <Route path="/projects/:id" element={<ProjectDetailPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  )
}

describe("ProjectDetailPage search", () => {
  beforeEach(() => {
    casesApi.search.mockReset()
  })

  it("calls search API with debounced query and renders results", async () => {
    casesApi.search.mockResolvedValue([
      { id: 100, name: "Login flow", description: "user logs in", tags: ["smoke"], suite_id: 1 },
    ])
    setup()

    const input = await screen.findByPlaceholderText(/search test cases/i)
    fireEvent.change(input, { target: { value: "login" } })

    expect(await screen.findByText("Login flow", {}, { timeout: 3000 })).toBeInTheDocument()
    expect(casesApi.search).toHaveBeenCalledWith("1", { q: "login", tags: undefined })
    expect(screen.getByText("smoke")).toBeInTheDocument()
  })

  it("shows empty state when no matches", async () => {
    casesApi.search.mockResolvedValue([])
    setup()

    const input = await screen.findByPlaceholderText(/search test cases/i)
    fireEvent.change(input, { target: { value: "zzz" } })

    expect(await screen.findByText(/no test cases match/i)).toBeInTheDocument()
  })

  it("renders suites list when search is empty", async () => {
    setup()
    expect(await screen.findByTestId("suite-1")).toBeInTheDocument()
    expect(casesApi.search).not.toHaveBeenCalled()
  })
})
