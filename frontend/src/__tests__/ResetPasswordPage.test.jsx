import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { MemoryRouter, Route, Routes } from "react-router-dom"

vi.mock("sonner", () => ({ toast: { success: vi.fn(), error: vi.fn() } }))

vi.mock("../api/auth", () => ({
  authApi: {
    confirmPasswordReset: vi.fn(),
  },
}))

import { authApi } from "../api/auth"
import { ResetPasswordPage } from "../pages/ResetPasswordPage"

function renderPage(initialPath) {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[initialPath]}>
        <Routes>
          <Route path="/reset-password" element={<ResetPasswordPage />} />
          <Route path="/login" element={<div>Login page</div>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  )
}

beforeEach(() => {
  authApi.confirmPasswordReset.mockReset()
})

describe("ResetPasswordPage", () => {
  it("rejects access without a token in the query string", () => {
    renderPage("/reset-password")

    expect(screen.getByText(/missing reset token/i)).toBeInTheDocument()
  })

  it("disables submit until passwords match and meet length", () => {
    renderPage("/reset-password?token=abc")

    const submit = screen.getByRole("button", { name: /update password/i })
    expect(submit).toBeDisabled()

    fireEvent.change(screen.getByLabelText(/new password/i), { target: { value: "short" } })
    fireEvent.change(screen.getByLabelText(/confirm password/i), { target: { value: "short" } })
    expect(submit).toBeDisabled()

    fireEvent.change(screen.getByLabelText(/new password/i), { target: { value: "long-enough-pw" } })
    fireEvent.change(screen.getByLabelText(/confirm password/i), { target: { value: "long-enough-pw" } })
    expect(submit).not.toBeDisabled()
  })

  it("calls confirm endpoint with token and new password", async () => {
    authApi.confirmPasswordReset.mockResolvedValue()
    renderPage("/reset-password?token=tok-xyz")

    fireEvent.change(screen.getByLabelText(/new password/i), { target: { value: "fresh-secret-12" } })
    fireEvent.change(screen.getByLabelText(/confirm password/i), { target: { value: "fresh-secret-12" } })
    fireEvent.click(screen.getByRole("button", { name: /update password/i }))

    await waitFor(() => expect(authApi.confirmPasswordReset).toHaveBeenCalledWith("tok-xyz", "fresh-secret-12"))
  })

  it("surfaces backend error detail on failure", async () => {
    authApi.confirmPasswordReset.mockRejectedValue({
      response: { data: { detail: "Invalid or expired token" } },
    })
    renderPage("/reset-password?token=bad")

    fireEvent.change(screen.getByLabelText(/new password/i), { target: { value: "fresh-secret-12" } })
    fireEvent.change(screen.getByLabelText(/confirm password/i), { target: { value: "fresh-secret-12" } })
    fireEvent.click(screen.getByRole("button", { name: /update password/i }))

    expect(await screen.findByRole("alert")).toHaveTextContent(/invalid or expired token/i)
  })
})
