import { describe, it, expect, vi } from "vitest"
import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { MemoryRouter } from "react-router-dom"

vi.mock("sonner", () => ({ toast: { success: vi.fn(), error: vi.fn() } }))

vi.mock("../api/auth", () => ({
  authApi: {
    requestPasswordReset: vi.fn(() => Promise.resolve()),
  },
}))

import { authApi } from "../api/auth"
import { ForgotPasswordPage } from "../pages/ForgotPasswordPage"

function renderPage() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <ForgotPasswordPage />
      </MemoryRouter>
    </QueryClientProvider>
  )
}

describe("ForgotPasswordPage", () => {
  it("submits email and shows confirmation message", async () => {
    renderPage()

    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: "alice@x.com" } })
    fireEvent.click(screen.getByRole("button", { name: /send reset link/i }))

    await waitFor(() => expect(authApi.requestPasswordReset).toHaveBeenCalledWith("alice@x.com"))
    expect(await screen.findByText(/sent a reset link/i)).toBeInTheDocument()
  })

  it("links back to sign in", () => {
    renderPage()

    expect(screen.getByRole("link", { name: /back to sign in/i })).toHaveAttribute("href", "/login")
  })
})
