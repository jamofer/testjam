import { describe, it, expect, vi } from "vitest"
import { render, screen, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { MemoryRouter, Route, Routes } from "react-router-dom"

import { UserProfilePage } from "../pages/UserProfilePage"

vi.mock("../api/users", () => ({
  usersApi: {
    getByUsername: vi.fn(),
  },
}))

import { usersApi } from "../api/users"

function setup(initialEntry = "/users/alice") {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[initialEntry]}>
        <Routes>
          <Route path="/users/:username" element={<UserProfilePage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe("UserProfilePage", () => {
  it("renders profile data fetched by username", async () => {
    usersApi.getByUsername.mockResolvedValue({
      id: 4,
      username: "alice",
      full_name: "Alice Adams",
      email: "alice@x.com",
      is_active: true,
      is_admin: false,
      locale: "es",
      created_at: "2026-01-01T00:00:00Z",
      last_login_at: "2026-05-10T08:00:00Z",
    })

    setup()

    expect(await screen.findByText("Alice Adams")).toBeInTheDocument()
    expect(screen.getByText("@alice")).toBeInTheDocument()
    expect(screen.getByText("es")).toBeInTheDocument()
    expect(usersApi.getByUsername).toHaveBeenCalledWith("alice")
  })

  it("shows not-found state when the API 404s", async () => {
    usersApi.getByUsername.mockRejectedValue(new Error("nope"))

    setup("/users/ghost")

    await waitFor(() => expect(screen.getByText(/user not found/i)).toBeInTheDocument())
  })
})
