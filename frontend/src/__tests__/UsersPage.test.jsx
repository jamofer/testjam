import { describe, it, expect, vi, beforeEach } from "vitest"
import { fireEvent, render, screen, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { MemoryRouter } from "react-router-dom"

import "../i18n"
import { usersApi } from "../api/users"
import { UsersPage } from "../pages/UsersPage"

vi.mock("sonner", () => ({ toast: { success: vi.fn(), error: vi.fn() } }))
vi.mock("../api/users", () => ({
  usersApi: {
    list: vi.fn(),
    restore: vi.fn(() => Promise.resolve({})),
    delete: vi.fn(() => Promise.resolve({})),
  },
}))
vi.mock("../api/groups", () => ({ groupsApi: { list: () => Promise.resolve([]), delete: vi.fn() } }))
vi.mock("../components/admin/AdminProjectsTab", () => ({ AdminProjectsTab: () => null }))

const ACTIVE_USER = { id: 1, username: "alice", email: "alice@test.com", is_active: true, is_admin: true, deleted_at: null }
const DELETED_USER = { id: 2, username: "bob", email: "bob@test.com", is_active: false, is_admin: false, deleted_at: "2026-10-01T00:00:00Z" }

beforeEach(() => {
  vi.clearAllMocks()
  usersApi.list.mockImplementation(({ includeDeleted } = {}) =>
    Promise.resolve(includeDeleted ? [ACTIVE_USER, DELETED_USER] : [ACTIVE_USER]),
  )
})

describe("UsersPage", () => {
  it("lists active users by default", async () => {
    renderPage()

    expect(await screen.findByText("alice")).toBeInTheDocument()
    expect(screen.queryByText("bob")).not.toBeInTheDocument()
  })

  it("shows deleted users on request and restores them", async () => {
    renderPage()
    await screen.findByText("alice")

    fireEvent.click(screen.getByLabelText("Show deleted"))
    fireEvent.click(await screen.findByRole("button", { name: /restore/i }))

    await waitFor(() => expect(usersApi.restore).toHaveBeenCalledWith(2, expect.anything()))
    expect(usersApi.list).toHaveBeenCalledWith({ includeDeleted: true })
  })
})

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <UsersPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}
