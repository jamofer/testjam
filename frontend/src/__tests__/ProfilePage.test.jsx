import { describe, it, expect, vi, beforeEach } from "vitest"
import { fireEvent, render, screen, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { MemoryRouter } from "react-router-dom"
import { toast } from "sonner"

import "../i18n"
import { ProfilePage } from "../pages/ProfilePage"

const changePassword = vi.fn()
const updateMe = vi.fn()

vi.mock("sonner", () => ({ toast: { success: vi.fn(), error: vi.fn() } }))
vi.mock("../hooks/useAuth", () => ({
  useMe: () => ({ data: { id: 1, username: "alice", email: "alice@test.com", full_name: "Alice Doe" } }),
  useUpdateMe: () => ({ mutateAsync: updateMe, isPending: false }),
  useChangePassword: () => ({ mutateAsync: changePassword, isPending: false }),
}))
vi.mock("../hooks/useTokens", () => ({
  useUserTokens: () => ({ data: [] }),
  useCreateUserToken: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useRevokeUserToken: () => ({ mutateAsync: vi.fn(), isPending: false }),
}))
vi.mock("../hooks/useNotificationPreferences", () => ({
  useNotificationPreferences: () => ({ data: [] }),
  useUpdateNotificationPreference: () => ({ mutate: vi.fn() }),
}))
vi.mock("../hooks/useSettings", () => ({ usePublicSettings: () => ({ data: { smtp_configured: true } }) }))

beforeEach(() => {
  vi.clearAllMocks()
  changePassword.mockResolvedValue({ access_token: "new" })
  updateMe.mockResolvedValue({})
})

describe("ProfilePage password change", () => {
  it("rejects a confirmation that does not match", async () => {
    renderPage()

    submitPassword("old-password", "new-password-1", "new-password-2")

    await waitFor(() => expect(toast.error).toHaveBeenCalledWith("Passwords don't match"))
    expect(changePassword).not.toHaveBeenCalled()
  })

  it("rejects passwords shorter than eight characters", async () => {
    renderPage()

    submitPassword("old-password", "short", "short")

    await waitFor(() => expect(toast.error).toHaveBeenCalledWith("Password must be at least 8 characters"))
    expect(changePassword).not.toHaveBeenCalled()
  })

  it("changes the password and clears the form", async () => {
    renderPage()

    submitPassword("old-password", "brand-new-pass", "brand-new-pass")

    await waitFor(() => expect(changePassword).toHaveBeenCalledWith({
      current_password: "old-password", new_password: "brand-new-pass",
    }))
    await waitFor(() => expect(screen.getByTestId("new-password")).toHaveValue(""))
  })
})

describe("ProfilePage profile details", () => {
  it("prefills the form with the current user", () => {
    renderPage()

    expect(screen.getByDisplayValue("Alice Doe")).toBeInTheDocument()
    expect(screen.getByDisplayValue("alice@test.com")).toBeInTheDocument()
  })
})

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <ProfilePage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

function submitPassword(current, next, confirmation) {
  fireEvent.change(screen.getByTestId("current-password"), { target: { value: current } })
  fireEvent.change(screen.getByTestId("new-password"), { target: { value: next } })
  fireEvent.change(screen.getByTestId("confirm-password"), { target: { value: confirmation } })
  fireEvent.click(screen.getByRole("button", { name: "Change password" }))
}
