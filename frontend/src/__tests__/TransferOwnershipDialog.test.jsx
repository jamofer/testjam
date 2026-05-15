import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"

import { TransferOwnershipDialog } from "../components/admin/TransferOwnershipDialog"

vi.mock("sonner", () => ({ toast: { success: vi.fn(), error: vi.fn() } }))
vi.mock("../api/admin", () => ({
  adminApi: { transferOwnership: vi.fn() },
}))

import { adminApi } from "../api/admin"

const users = [
  { id: 1, username: "alice", is_active: true, deleted_at: null },
  { id: 2, username: "bob", is_active: true, deleted_at: null },
  { id: 3, username: "deleted", is_active: true, deleted_at: "2026-05-01" },
]

function setup() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  const onClose = vi.fn()
  render(
    <QueryClientProvider client={queryClient}>
      <TransferOwnershipDialog
        project={{ id: 42, name: "Atlas" }}
        users={users}
        onClose={onClose}
      />
    </QueryClientProvider>,
  )
  return { onClose }
}

describe("TransferOwnershipDialog", () => {
  beforeEach(() => {
    adminApi.transferOwnership.mockReset()
    adminApi.transferOwnership.mockResolvedValue({})
  })

  it("hides soft-deleted users from the candidate list", () => {
    setup()

    const select = screen.getByRole("combobox")
    const options = Array.from(select.querySelectorAll("option")).map(o => o.textContent)
    expect(options).toEqual(["alice", "bob"])
  })

  it("posts the chosen new owner id", async () => {
    const { onClose } = setup()
    fireEvent.change(screen.getByRole("combobox"), { target: { value: "2" } })

    fireEvent.click(screen.getByRole("button", { name: /^transfer$/i }))

    await waitFor(() =>
      expect(adminApi.transferOwnership).toHaveBeenCalledWith(42, 2),
    )
    await waitFor(() => expect(onClose).toHaveBeenCalled())
  })
})
