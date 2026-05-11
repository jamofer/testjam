import { describe, expect, it, vi } from "vitest"
import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { MemoryRouter } from "react-router-dom"
import { ProfilePage } from "../pages/ProfilePage"

const updateNotificationPreference = vi.fn(({ eventType, in_app, email }) =>
  Promise.resolve({ event_type: eventType, in_app, email }),
)
const toastSuccess = vi.fn()
const toastError = vi.fn()

vi.mock("sonner", () => ({
  toast: {
    success: (...args) => toastSuccess(...args),
    error: (...args) => toastError(...args),
  },
}))

vi.mock("../hooks/useAuth", () => ({
  useMe: () => ({ data: { id: 1, username: "alice", email: "a@x.com", full_name: "Alice" } }),
  useUpdateMe: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useChangePassword: () => ({ mutateAsync: vi.fn(), isPending: false }),
}))

vi.mock("../hooks/useTokens", () => ({
  useUserTokens: () => ({ data: [] }),
  useCreateUserToken: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useRevokeUserToken: () => ({ mutateAsync: vi.fn(), isPending: false }),
}))

const publicSettingsState = { smtp_configured: true }
vi.mock("../hooks/useSettings", () => ({
  usePublicSettings: () => ({ data: publicSettingsState }),
}))

vi.mock("../hooks/useNotificationPreferences", () => ({
  useNotificationPreferences: () => ({
    data: [
      { event_type: "execution_assigned", in_app: true, email: true },
      { event_type: "execution_finished", in_app: true, email: false },
      { event_type: "execution_failed", in_app: true, email: true },
    ],
    isLoading: false,
  }),
  useUpdateNotificationPreference: () => ({
    mutateAsync: updateNotificationPreference,
    isPending: false,
  }),
}))

function renderProfile() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0, staleTime: Infinity } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <ProfilePage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe("ProfilePage notification preferences section", () => {
  it("renders one row per known event type with both channel checkboxes", () => {
    publicSettingsState.smtp_configured = true
    renderProfile()
    expect(screen.getByText("Execution assigned to you")).toBeInTheDocument()
    expect(screen.getByText("Execution finished")).toBeInTheDocument()
    expect(screen.getByText("Execution had failed tests")).toBeInTheDocument()
    expect(screen.getByLabelText(/Email for Execution finished/)).not.toBeChecked()
    expect(screen.getByLabelText(/Email for Execution had failed tests/)).toBeChecked()
  })

  it("invokes the update mutation and shows a success toast when a checkbox is toggled", async () => {
    publicSettingsState.smtp_configured = true
    renderProfile()
    fireEvent.click(screen.getByLabelText(/Email for Execution finished/))

    await waitFor(() => expect(updateNotificationPreference).toHaveBeenCalled())
    expect(updateNotificationPreference).toHaveBeenCalledWith({
      eventType: "execution_finished",
      in_app: true,
      email: true,
    })
    await waitFor(() => expect(toastSuccess).toHaveBeenCalledWith("Preferences saved"))
  })

  it("shows the SMTP-not-configured banner when the backend reports it", () => {
    publicSettingsState.smtp_configured = false
    renderProfile()
    expect(screen.getByTestId("smtp-not-configured-banner")).toBeInTheDocument()
  })

  it("disables email checkboxes when SMTP is not configured", () => {
    publicSettingsState.smtp_configured = false
    renderProfile()
    expect(screen.getByLabelText(/Email for Execution finished/)).toBeDisabled()
  })
})
