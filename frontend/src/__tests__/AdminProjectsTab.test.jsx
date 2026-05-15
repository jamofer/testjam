import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { MemoryRouter } from "react-router-dom"

import { AdminProjectsTab } from "../components/admin/AdminProjectsTab"

vi.mock("sonner", () => ({ toast: { success: vi.fn(), error: vi.fn() } }))
vi.mock("../api/admin", () => ({
  adminApi: { listProjects: vi.fn(), transferOwnership: vi.fn() },
}))
vi.mock("../api/projects", () => ({
  projectsApi: {
    archive: vi.fn(),
    unarchive: vi.fn(),
    exportZip: vi.fn(),
    delete: vi.fn(),
  },
}))
vi.mock("../hooks/useDatePreferences", () => ({
  useDatePreferences: () => ({ timezone: "UTC", useRelativeDates: false }),
}))

import { adminApi } from "../api/admin"
import { projectsApi } from "../api/projects"

const PROJECTS = [
  {
    id: 1, name: "Atlas", description: null, archived_at: null,
    owner_username: "alice", member_count: 4, case_count: 12,
    last_execution_at: "2026-05-01T10:00:00Z", created_at: "2026-01-01T00:00:00Z",
  },
  {
    id: 2, name: "Bravo", description: null, archived_at: "2026-04-01T00:00:00Z",
    owner_username: "bob", member_count: 2, case_count: 0,
    last_execution_at: null, created_at: "2026-01-02T00:00:00Z",
  },
]

function setup() {
  adminApi.listProjects.mockResolvedValue(PROJECTS)
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <AdminProjectsTab users={[{ id: 9, username: "carol", is_active: true, deleted_at: null }]} />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe("AdminProjectsTab", () => {
  beforeEach(() => {
    adminApi.listProjects.mockReset()
    projectsApi.archive.mockReset()
    projectsApi.unarchive.mockReset()
    projectsApi.archive.mockResolvedValue({})
    projectsApi.unarchive.mockResolvedValue({})
  })

  it("renders one row per project with owner and counts", async () => {
    setup()

    expect(await screen.findByText("Atlas")).toBeInTheDocument()
    expect(screen.getByText("Bravo")).toBeInTheDocument()
    expect(screen.getByText("alice")).toBeInTheDocument()
    expect(screen.getByText("bob")).toBeInTheDocument()
    expect(screen.getByText("12")).toBeInTheDocument()
  })

  it("calls archive when the active project's archive button is clicked", async () => {
    setup()
    await screen.findByText("Atlas")

    fireEvent.click(screen.getAllByTitle("Archive")[0])

    await waitFor(() => expect(projectsApi.archive).toHaveBeenCalledWith(1))
  })

  it("calls unarchive on an archived project", async () => {
    setup()
    await screen.findByText("Bravo")

    fireEvent.click(screen.getByTitle("Unarchive"))

    await waitFor(() => expect(projectsApi.unarchive).toHaveBeenCalledWith(2))
  })
})
