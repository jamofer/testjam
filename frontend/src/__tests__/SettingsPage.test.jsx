import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { MemoryRouter } from "react-router-dom"
import { SettingsPage } from "../pages/SettingsPage"

vi.mock("sonner", () => ({ toast: { success: vi.fn(), error: vi.fn() } }))

vi.mock("../api/settings", () => ({
  settingsApi: {
    public: vi.fn(() => Promise.resolve({})),
    read: vi.fn(),
    update: vi.fn(() => Promise.resolve({})),
  },
}))

const adminMe = { data: { id: 1, username: "root", is_admin: true } }
const userMe = { data: { id: 2, username: "alice", is_admin: false } }
let currentMe = adminMe

vi.mock("../hooks/useAuth", () => ({
  useMe: () => currentMe,
}))

import { settingsApi } from "../api/settings"

const FULL_SETTINGS = {
  site_url: "https://qa.example.com",
  app_name: "Acme QA",
  allow_registration: true,
  default_environment: "staging",
  default_version_pattern: "v",
  max_upload_mb: 20,
  notifications_retention_days: 90,
  smtp_host: "smtp.example.com",
  smtp_port: 587,
  smtp_user: "noreply",
  smtp_password_set: true,
  smtp_from: "noreply@example.com",
  smtp_use_tls: true,
  updated_at: "2026-05-07T12:00:00Z",
}

function setup(asAdmin = true, initialData = FULL_SETTINGS) {
  currentMe = asAdmin ? adminMe : userMe
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0, staleTime: Infinity } },
  })
  qc.setQueryData(["settings"], initialData)
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={["/settings"]}>
        <SettingsPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe("SettingsPage", () => {
  beforeEach(() => {
    settingsApi.update.mockReset()
    settingsApi.update.mockResolvedValue({})
  })

  it("rejects non-admin users with an empty state", () => {
    setup(false)
    expect(screen.getByText(/admin only/i)).toBeInTheDocument()
  })

  it("renders all sections for admin", () => {
    setup()
    expect(screen.getByText("General")).toBeInTheDocument()
    expect(screen.getByText("Execution defaults")).toBeInTheDocument()
    expect(screen.getByText("Limits")).toBeInTheDocument()
    expect(screen.getByText("Email (SMTP)")).toBeInTheDocument()
  })

  it("submits form payload on save", async () => {
    setup()
    fireEvent.click(screen.getByRole("button", { name: /save/i }))

    await waitFor(() => expect(settingsApi.update).toHaveBeenCalled())
    const payload = settingsApi.update.mock.calls[0][0]
    expect(payload.app_name).toBe("Acme QA")
    expect(payload.site_url).toBe("https://qa.example.com")
    expect(payload.smtp_use_tls).toBe(true)
    expect(payload).not.toHaveProperty("smtp_password")
  })

  it("clears smtp password when 'Clear stored password' is checked", async () => {
    setup()
    fireEvent.click(screen.getByLabelText(/clear stored password/i))
    fireEvent.click(screen.getByRole("button", { name: /save/i }))

    await waitFor(() => expect(settingsApi.update).toHaveBeenCalled())
    expect(settingsApi.update.mock.calls[0][0].smtp_password).toBe("")
  })

  it("sends a new smtp_password when typed", async () => {
    setup()
    const pw = screen.getByPlaceholderText(/set/i)
    fireEvent.change(pw, { target: { value: "new-secret" } })
    fireEvent.click(screen.getByRole("button", { name: /save/i }))

    await waitFor(() => expect(settingsApi.update).toHaveBeenCalled())
    expect(settingsApi.update.mock.calls[0][0].smtp_password).toBe("new-secret")
  })
})
