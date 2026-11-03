import { renderHook, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { beforeEach, describe, expect, it, vi } from "vitest"

import { authApi } from "../api/auth"
import { useChangePassword } from "../hooks/useAuth"

vi.mock("../api/auth", () => ({
  authApi: { changePassword: vi.fn() },
}))

function wrapper({ children }) {
  return <QueryClientProvider client={new QueryClient()}>{children}</QueryClientProvider>
}

describe("useChangePassword", () => {
  beforeEach(() => {
    localStorage.setItem("token", "previous-session")
  })

  it("keeps the session by storing the token issued with the new password", async () => {
    authApi.changePassword.mockResolvedValue({ access_token: "new-session" })
    const { result } = renderHook(() => useChangePassword(), { wrapper })

    result.current.mutate({ current_password: "old", new_password: "new" })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(localStorage.getItem("token")).toBe("new-session")
  })
})
