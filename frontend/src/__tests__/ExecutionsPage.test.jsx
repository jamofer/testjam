import { describe, it, expect, vi } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { MemoryRouter, Route, Routes } from "react-router-dom"
import { ExecutionsPage } from "../pages/ExecutionsPage"

vi.mock("../api/executions", () => ({
  executionsApi: {
    list: vi.fn(() => Promise.resolve([])),
    exportHtml: vi.fn(),
  },
}))

vi.mock("../hooks/useProjects", () => ({
  useProject: () => ({ data: { id: 1, name: "Acme" } }),
}))

vi.mock("../hooks/useAuth", () => ({
  useMe: () => ({ data: { id: 1, username: "alice" } }),
}))

vi.mock("../hooks/useVersions", () => ({
  useVersions: () => ({ data: [
    { id: 7, name: "v1.0" },
    { id: 8, name: "v2.0" },
  ] }),
}))

const EX = [
  { id: 10, title: "Run A", status: "completed", type: "manual",
    summary: { passed: 1, failed: 0, blocked: 0, not_run: 0 } },
]

function setup(executions = [], { initialEntries = ["/projects/1/executions"], extraSeed } = {}) {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0, staleTime: Infinity } },
  })
  qc.setQueryData(
    ["executions", "1", undefined],
    { pages: [executions], pageParams: [0] },
  )
  qc.setQueryData(
    ["executions", "1", { status: "in_progress" }],
    { pages: [[]], pageParams: [0] },
  )
  if (extraSeed) extraSeed(qc)

  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={initialEntries}>
        <Routes>
          <Route path="/projects/:id/executions" element={<ExecutionsPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe("ExecutionsPage", () => {
  it("keeps filter buttons visible after filtering yields empty result", () => {
    setup(EX)
    expect(screen.getByText("Run A")).toBeTruthy()
    fireEvent.click(screen.getByRole("button", { name: /^in progress$/i }))
    expect(screen.getByRole("button", { name: /^in progress$/i })).toBeTruthy()
    expect(screen.getByRole("button", { name: /^all$/i })).toBeTruthy()
    expect(screen.getByText(/no matches/i)).toBeTruthy()
  })

  it("shows the empty 'No executions yet' state when project has none and no filter active", () => {
    setup([])
    expect(screen.getByText(/no executions yet/i)).toBeTruthy()
    expect(screen.queryByRole("button", { name: /^in progress$/i })).toBeNull()
  })

  it("seeds the version filter from the version_id query string", () => {
    setup(EX, {
      initialEntries: ["/projects/1/executions?version_id=7"],
      extraSeed: (qc) => qc.setQueryData(
        ["executions", "1", { version_id: "7" }],
        { pages: [EX], pageParams: [0] },
      ),
    })

    expect(screen.getByText("v1.0")).toBeTruthy()
  })
})
