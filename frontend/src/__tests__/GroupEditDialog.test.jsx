import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"

import { GroupEditDialog } from "../components/admin/GroupEditDialog"

vi.mock("sonner", () => ({ toast: { success: vi.fn(), error: vi.fn() } }))
vi.mock("../api/groups", () => ({
  groupsApi: {
    listMembers: vi.fn(),
    update: vi.fn(),
    addMember: vi.fn(),
    removeMember: vi.fn(),
  },
}))
vi.mock("../api/users", () => ({
  usersApi: { list: vi.fn() },
}))

import { groupsApi } from "../api/groups"
import { usersApi } from "../api/users"

const MEMBERS = [{ user_id: 1, username: "alice", role: "member" }]
const USERS = [
  { id: 1, username: "alice", deleted_at: null },
  { id: 2, username: "bob", deleted_at: null },
]

function setup() {
  groupsApi.listMembers.mockResolvedValue(MEMBERS)
  usersApi.list.mockResolvedValue(USERS)
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  const onClose = vi.fn()
  render(
    <QueryClientProvider client={queryClient}>
      <GroupEditDialog
        group={{ id: 10, name: "QA Team", description: "Quality" }}
        onClose={onClose}
      />
    </QueryClientProvider>,
  )
  return { onClose }
}

describe("GroupEditDialog", () => {
  beforeEach(() => {
    groupsApi.listMembers.mockReset()
    groupsApi.update.mockReset()
    groupsApi.addMember.mockReset()
    groupsApi.removeMember.mockReset()
    usersApi.list.mockReset()
    groupsApi.update.mockResolvedValue({})
    groupsApi.addMember.mockResolvedValue({})
    groupsApi.removeMember.mockResolvedValue({})
  })

  it("saves edited name + description", async () => {
    setup()
    await screen.findByText(/members/i)

    fireEvent.change(screen.getByDisplayValue("QA Team"), { target: { value: "QA Squad" } })
    fireEvent.click(screen.getByRole("button", { name: /save details/i }))

    await waitFor(() =>
      expect(groupsApi.update).toHaveBeenCalledWith(10, {
        name: "QA Squad",
        description: "Quality",
      }),
    )
  })

  it("adds a member when one is picked", async () => {
    setup()
    await screen.findByText("alice")

    fireEvent.change(screen.getByDisplayValue("Select user…"), { target: { value: "2" } })
    fireEvent.click(screen.getByRole("button", { name: /add member/i }))

    await waitFor(() => expect(groupsApi.addMember).toHaveBeenCalledWith(10, 2))
  })

  it("removes a member when trash is clicked", async () => {
    setup()
    await screen.findByText("alice")

    fireEvent.click(screen.getByLabelText("Remove alice"))

    await waitFor(() => expect(groupsApi.removeMember).toHaveBeenCalledWith(10, 1))
  })
})
