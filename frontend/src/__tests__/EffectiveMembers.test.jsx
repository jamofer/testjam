import { describe, it, expect, vi, beforeEach } from "vitest"
import { renderHook, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"

import { membersApi } from "../api/members"
import { useProjectRole } from "../hooks/useProjectRole"

vi.mock("../hooks/useAuth", () => ({
  useMe: () => ({ data: { id: 5, is_admin: false } }),
}))
vi.mock("../api/members", () => ({
  membersApi: { list: vi.fn(), listEffective: vi.fn() },
}))

const PROJECT_ID = 7
const GROUP_TESTER = { user_id: 5, username: "alice", full_name: null, role: "tester" }

function renderRole() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  const wrapper = ({ children }) => <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  return renderHook(() => useProjectRole(PROJECT_ID), { wrapper })
}

describe("useProjectRole with group access", () => {
  beforeEach(() => {
    membersApi.list.mockReset()
    membersApi.listEffective.mockReset()
    membersApi.listEffective.mockResolvedValue([GROUP_TESTER])
  })

  it("lets a user who only has access through a group write", async () => {
    const { result } = renderRole()

    await waitFor(() => expect(result.current.isLoading).toBe(false))
    expect(result.current.role).toBe("tester")
    expect(result.current.canWrite).toBe(true)
  })

  it("reads roles from the effective member list", async () => {
    const { result } = renderRole()

    await waitFor(() => expect(result.current.isLoading).toBe(false))
    expect(membersApi.listEffective).toHaveBeenCalledWith(PROJECT_ID)
    expect(membersApi.list).not.toHaveBeenCalled()
  })
})
