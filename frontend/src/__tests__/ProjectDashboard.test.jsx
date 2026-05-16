import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { MemoryRouter } from "react-router-dom"

import { ProjectDashboard } from "../components/dashboard/ProjectDashboard"

vi.mock("../api/dashboard", () => ({
  dashboardApi: { get: vi.fn() },
}))
vi.mock("../hooks/useDatePreferences", () => ({
  useDatePreferences: () => ({ timezone: "UTC", useRelativeDates: false }),
}))

import { dashboardApi } from "../api/dashboard"

const PAYLOAD = {
  range_days: 30,
  generated_at: "2026-05-15T00:00:00Z",
  counts: { suites: 4, cases: 12, plans: 1, executions_in_flight: 2, executions_in_range: 10 },
  pass_rate: {
    overall_pass_rate: 0.75,
    total_results: 8,
    series: [
      { date: "2026-05-14", passed: 3, failed: 1, blocked: 0, not_run: 0 },
      { date: "2026-05-15", passed: 3, failed: 1, blocked: 0, not_run: 0 },
    ],
  },
  top_fail: {
    cases: [
      { case_id: 11, case_name: "Login flaky", suite_id: 1, suite_name: "Auth", fail_count: 4 },
    ],
  },
  recent_executions: {
    executions: [
      {
        id: 99, title: "Nightly", status: "completed", version_name: null, environment: null,
        created_at: "2026-05-15T00:00:00Z", started_at: null, finished_at: null,
        duration_ms: 12000, passed: 5, failed: 0, blocked: 0, not_run: 0,
      },
    ],
  },
}

function setup({ onRangeChange = vi.fn() } = {}) {
  dashboardApi.get.mockResolvedValue(PAYLOAD)
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <ProjectDashboard projectId={42} range={30} onRangeChange={onRangeChange} />
      </MemoryRouter>
    </QueryClientProvider>,
  )
  return { onRangeChange }
}

describe("ProjectDashboard", () => {
  beforeEach(() => {
    dashboardApi.get.mockReset()
  })

  it("renders counts, pass rate, top fail, and recent executions", async () => {
    setup()

    expect(await screen.findByText("12")).toBeInTheDocument()
    expect(screen.getByText("75%")).toBeInTheDocument()
    expect(screen.getByText("Login flaky")).toBeInTheDocument()
    expect(screen.getByText("Nightly")).toBeInTheDocument()
  })

  it("calls onRangeChange when a range button is clicked", async () => {
    const { onRangeChange } = setup()

    fireEvent.click(screen.getByRole("radio", { name: "7d" }))

    await waitFor(() => expect(onRangeChange).toHaveBeenCalledWith(7))
  })

  it("fetches with the active range", async () => {
    setup()

    await waitFor(() =>
      expect(dashboardApi.get).toHaveBeenCalledWith(42, { range: 30 }),
    )
  })
})
