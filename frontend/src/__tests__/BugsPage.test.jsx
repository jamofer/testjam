import { describe, it, expect, vi } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom"
import { BugsPage } from "../pages/BugsPage"

vi.mock("../api/bugs", () => ({
  bugsApi: { exportHtml: vi.fn(), releaseNotesHtml: vi.fn() },
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

vi.mock("../hooks/useCustomFields", () => ({ useCustomFields: () => ({ data: [] }) }))
vi.mock("../hooks/useCustomFieldColumns", () => ({
  useCustomFieldColumns: () => ({ visibleKeys: [], toggle: vi.fn() }),
}))
vi.mock("../hooks/useProjectBugsLive", () => ({
  useProjectBugsLive: () => ({ connected: false }),
}))

let lastLocation = null
function LocationProbe() {
  lastLocation = useLocation()
  return null
}

function setup({ initialEntries = ["/projects/1/bugs"] } = {}) {
  lastLocation = null
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0, staleTime: Infinity } },
  })
  qc.setQueryData(["bugs", "1", {}], [])
  qc.setQueryData(["bugs", "1", { status: "open" }], [])
  qc.setQueryData(["bugs", "1", { version_id: "7" }], [])
  qc.setQueryData(["bugs", "1", { severity: "critical" }], [])

  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={initialEntries}>
        <Routes>
          <Route path="/projects/:id/bugs" element={<><BugsPage /><LocationProbe /></>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe("BugsPage URL filters", () => {
  it("seeds the status filter from the URL", () => {
    setup({ initialEntries: ["/projects/1/bugs?status=open"] })

    expect(screen.getByLabelText(/status/i)).toHaveTextContent(/open/i)
  })

  it("seeds the version filter from the URL", () => {
    setup({ initialEntries: ["/projects/1/bugs?version_id=7"] })

    expect(screen.getByLabelText(/version/i)).toHaveTextContent(/v1\.0/i)
  })

  it("seeds the severity filter from the URL", () => {
    setup({ initialEntries: ["/projects/1/bugs?severity=critical"] })

    expect(screen.getByLabelText(/severity/i)).toHaveTextContent(/critical/i)
  })

  it("writes selected status to the URL", () => {
    setup()

    fireEvent.click(screen.getByLabelText(/status/i))
    fireEvent.click(screen.getByRole("option", { name: /^open$/i }))

    expect(lastLocation.search).toContain("status=open")
  })

  it("removes the param when status is reset to any", () => {
    setup({ initialEntries: ["/projects/1/bugs?status=open"] })

    fireEvent.click(screen.getByLabelText(/status/i))
    fireEvent.click(screen.getByRole("option", { name: /any status/i }))

    expect(lastLocation.search).not.toContain("status=")
  })
})
