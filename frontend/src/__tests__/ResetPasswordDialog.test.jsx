import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"

import { ResetPasswordDialog } from "../components/admin/ResetPasswordDialog"

vi.mock("sonner", () => ({ toast: { success: vi.fn(), error: vi.fn() } }))
vi.mock("../api/users", () => ({
  usersApi: { resetPassword: vi.fn() },
}))

import { usersApi } from "../api/users"

function setup() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  const onClose = vi.fn()
  const utils = render(
    <QueryClientProvider client={queryClient}>
      <ResetPasswordDialog
        user={{ id: 7, username: "alice", email: "alice@example.com" }}
        onClose={onClose}
      />
    </QueryClientProvider>,
  )
  return { onClose, ...utils }
}

describe("ResetPasswordDialog", () => {
  beforeEach(() => {
    usersApi.resetPassword.mockReset()
  })

  it("calls the API with email mode and shows confirmation", async () => {
    usersApi.resetPassword.mockResolvedValue({ mode: "email", temporary_password: null })
    setup()

    fireEvent.click(screen.getByRole("button", { name: /send reset email/i }))

    await waitFor(() =>
      expect(usersApi.resetPassword).toHaveBeenCalledWith(7, "email"),
    )
    expect(await screen.findByText(/alice@example.com/)).toBeInTheDocument()
  })

  it("reveals the temporary password when admin chooses that mode", async () => {
    usersApi.resetPassword.mockResolvedValue({
      mode: "temporary_password",
      temporary_password: "xkcd-correct-horse",
    })
    setup()

    fireEvent.click(screen.getByRole("button", { name: /show temporary password/i }))

    expect(await screen.findByText("xkcd-correct-horse")).toBeInTheDocument()
  })
})
