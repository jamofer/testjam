import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { MemoryRouter, Route, Routes } from "react-router-dom"
import { ProjectDetailPage } from "../pages/ProjectDetailPage"

vi.mock("sonner", () => ({ toast: { success: vi.fn(), error: vi.fn() } }))

vi.mock("../api/testcases", () => ({
  suitesApi: {
    list: vi.fn(() => Promise.resolve([{ id: 1, name: "Suite A", project_id: 1 }])),
    listAll: vi.fn(() => Promise.resolve([
      { id: 1, name: "Suite A", parent_suite_id: null, project_id: 1 },
      { id: 2, name: "Sub Suite", parent_suite_id: 1, project_id: 1 },
    ])),
  },
  casesApi: {
    search: vi.fn(),
  },
}))

vi.mock("../api/projects", () => ({
  projectsApi: {
    get: vi.fn(() => Promise.resolve({ id: 1, name: "Acme", suite_count: 1, case_count: 0, execution_count: 0 })),
    exportZip: vi.fn(() => Promise.resolve()),
  },
}))

vi.mock("../components/project/SuiteRow", () => ({
  SuiteRow: ({ suite }) => <div data-testid={`suite-${suite.id}`}>{suite.name}</div>,
  SuiteCollapseContext: { Provider: ({ children }) => <>{children}</> },
}))

vi.mock("../components/project/VersionsPanel", () => ({
  VersionsPanel: () => <div />,
}))

import { casesApi } from "../api/testcases"
import { projectsApi } from "../api/projects"

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

  it("renders parent suite hierarchy on each search result", async () => {
    casesApi.search.mockResolvedValue([
      { id: 200, name: "Edge case", description: null, tags: [], suite_id: 2 },
    ])
    setup()
    const input = await screen.findByPlaceholderText(/search test cases/i)
    fireEvent.change(input, { target: { value: "edge" } })

    expect(await screen.findByText("Edge case")).toBeInTheDocument()
    expect(screen.getByText("Suite A")).toBeInTheDocument()
    expect(screen.getByText("Sub Suite")).toBeInTheDocument()
  })
})

describe("ProjectDetailPage export", () => {
  it("calls projectsApi.exportZip when Export button is clicked", async () => {
    projectsApi.exportZip.mockClear()
    setup()
    const button = await screen.findByRole("button", { name: /export/i })
    fireEvent.click(button)
    expect(projectsApi.exportZip).toHaveBeenCalledWith("1")
  })
})

describe("ProjectDetailPage shortcuts", () => {
  it("opens the shortcuts help dialog on '?'", async () => {
    setup()
    await screen.findByTestId("suite-1")

    fireEvent.keyDown(window, { key: "?" })

    expect(await screen.findByText(/keyboard shortcuts/i)).toBeInTheDocument()
  })

  it("focuses the search input on '/'", async () => {
    setup()
    const input = await screen.findByPlaceholderText(/search test cases/i)
    expect(document.activeElement).not.toBe(input)

    fireEvent.keyDown(window, { key: "/" })

    expect(document.activeElement).toBe(input)
  })
})
