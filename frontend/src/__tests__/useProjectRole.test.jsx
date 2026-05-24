import { describe, it, expect, vi } from "vitest"
import { renderHook } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"

import { useProjectRole } from "../hooks/useProjectRole"

vi.mock("../hooks/useAuth", () => ({
  useMe: () => mockMe(),
}))
vi.mock("../hooks/useMembers", () => ({
  useMembers: () => mockMembers(),
}))

let mockMeImpl
let mockMembersImpl
const mockMe = () => mockMeImpl()
const mockMembers = () => mockMembersImpl()


function withClient(hook) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  const wrapper = ({ children }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
  return renderHook(hook, { wrapper })
}


describe("useProjectRole", () => {
  it("returns admin shortcut without consulting member list", () => {
    mockMeImpl = () => ({ data: { id: 1, is_admin: true } })
    mockMembersImpl = () => ({ data: [], isLoading: false })

    const { result } = withClient(() => useProjectRole(7))

    expect(result.current.role).toBe("admin")
    expect(result.current.canWrite).toBe(true)
    expect(result.current.canDelete).toBe(true)
  })

  it("flags owners as writers and deleters", () => {
    mockMeImpl = () => ({ data: { id: 2, is_admin: false } })
    mockMembersImpl = () => ({ data: [
      { user_id: 2, role: "owner" },
      { user_id: 3, role: "tester" },
    ], isLoading: false })

    const { result } = withClient(() => useProjectRole(7))

    expect(result.current.role).toBe("owner")
    expect(result.current.canWrite).toBe(true)
    expect(result.current.canDelete).toBe(true)
  })

  it("flags testers as writers but not deleters", () => {
    mockMeImpl = () => ({ data: { id: 3, is_admin: false } })
    mockMembersImpl = () => ({ data: [
      { user_id: 3, role: "tester" },
    ], isLoading: false })

    const { result } = withClient(() => useProjectRole(7))

    expect(result.current.role).toBe("tester")
    expect(result.current.canWrite).toBe(true)
    expect(result.current.canDelete).toBe(false)
  })

  it("blocks viewers from both write and delete", () => {
    mockMeImpl = () => ({ data: { id: 4, is_admin: false } })
    mockMembersImpl = () => ({ data: [
      { user_id: 4, role: "viewer" },
    ], isLoading: false })

    const { result } = withClient(() => useProjectRole(7))

    expect(result.current.role).toBe("viewer")
    expect(result.current.canWrite).toBe(false)
    expect(result.current.canDelete).toBe(false)
  })

  it("blocks outsiders (no membership row) from both write and delete", () => {
    mockMeImpl = () => ({ data: { id: 99, is_admin: false } })
    mockMembersImpl = () => ({ data: [
      { user_id: 1, role: "owner" },
    ], isLoading: false })

    const { result } = withClient(() => useProjectRole(7))

    expect(result.current.role).toBeNull()
    expect(result.current.canWrite).toBe(false)
    expect(result.current.canDelete).toBe(false)
  })

  it("returns conservative defaults while data is still loading", () => {
    mockMeImpl = () => ({ data: undefined })
    mockMembersImpl = () => ({ data: [], isLoading: true })

    const { result } = withClient(() => useProjectRole(7))

    expect(result.current.canWrite).toBe(false)
    expect(result.current.canDelete).toBe(false)
  })
})
