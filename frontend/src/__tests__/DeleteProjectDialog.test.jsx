import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"

import { DeleteProjectDialog } from "../components/admin/DeleteProjectDialog"

vi.mock("sonner", () => ({ toast: { success: vi.fn(), error: vi.fn() } }))
vi.mock("../api/projects", () => ({
  projectsApi: { delete: vi.fn() },
}))

import { projectsApi } from "../api/projects"

function setup() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  const onClose = vi.fn()
  render(
    <QueryClientProvider client={queryClient}>
      <DeleteProjectDialog
        project={{ id: 11, name: "Pegasus" }}
        onClose={onClose}
      />
    </QueryClientProvider>,
  )
  return { onClose }
}

describe("DeleteProjectDialog", () => {
  beforeEach(() => {
    projectsApi.delete.mockReset()
    projectsApi.delete.mockResolvedValue({})
  })

  it("keeps the delete button disabled until the project name is typed", () => {
    setup()
    const deleteButton = screen.getByRole("button", { name: /delete project/i })
    expect(deleteButton).toBeDisabled()

    fireEvent.change(screen.getByPlaceholderText("Pegasus"), { target: { value: "wrong" } })
    expect(deleteButton).toBeDisabled()

    fireEvent.change(screen.getByPlaceholderText("Pegasus"), { target: { value: "Pegasus" } })
    expect(deleteButton).not.toBeDisabled()
  })

  it("calls projectsApi.delete on confirmation", async () => {
    const { onClose } = setup()
    fireEvent.change(screen.getByPlaceholderText("Pegasus"), { target: { value: "Pegasus" } })

    fireEvent.click(screen.getByRole("button", { name: /delete project/i }))

    await waitFor(() => expect(projectsApi.delete).toHaveBeenCalledWith(11))
    await waitFor(() => expect(onClose).toHaveBeenCalled())
  })
})
