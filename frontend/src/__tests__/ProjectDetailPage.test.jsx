import { describe, it, expect, vi } from "vitest"
import { render, screen } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { MemoryRouter, Route, Routes } from "react-router-dom"

import { ProjectDetailPage } from "../pages/ProjectDetailPage"

vi.mock("sonner", () => ({ toast: { success: vi.fn(), error: vi.fn() } }))
vi.mock("../api/dashboard", () => ({
  dashboardApi: { get: vi.fn(() => Promise.resolve({
    range_days: 30, generated_at: "2026-05-16T00:00:00Z",
    counts: { suites: 2, cases: 5, plans: 0, executions_in_flight: 0, executions_in_range: 0 },
    pass_rate: { overall_pass_rate: 1, total_results: 1, series: [] },
    top_fail: { cases: [] },
    recent_executions: { executions: [] },
  })) },
}))
vi.mock("../api/projects", () => ({
  projectsApi: {
    get: vi.fn(() => Promise.resolve({ id: 1, name: "Acme" })),
    exportZip: vi.fn(),
  },
}))
vi.mock("../hooks/useDatePreferences", () => ({
  useDatePreferences: () => ({ timezone: "UTC", useRelativeDates: false }),
}))

function setup() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0, staleTime: Infinity } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/projects/1"]}>
        <Routes>
          <Route path="/projects/:id" element={<ProjectDetailPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe("ProjectDetailPage (overview)", () => {
  it("renders project name and the dashboard cards", async () => {
    setup()

    expect(await screen.findByRole("heading", { level: 1, name: "Acme" })).toBeInTheDocument()
    expect(await screen.findByText("Project")).toBeInTheDocument()
    expect(screen.getByText("Pass rate")).toBeInTheDocument()
  })

  it("shows New execution / Test cases / Import results actions", async () => {
    setup()

    await screen.findByText("Project")
    expect(screen.getByRole("link", { name: /new execution/i })).toHaveAttribute("href", "/projects/1/executions/new")
    expect(screen.getByRole("link", { name: /test cases/i })).toHaveAttribute("href", "/projects/1/cases")
    expect(screen.getByRole("button", { name: /import results/i })).toBeInTheDocument()
  })
})
