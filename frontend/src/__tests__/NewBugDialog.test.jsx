import { describe, it, expect, vi } from "vitest"
import { fireEvent, render, screen, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"

vi.mock("../api/bugs", () => ({
  bugsApi: { create: vi.fn().mockResolvedValue({ id: 1, number: 1 }) },
}))
vi.mock("../api/environments", () => ({
  environmentsApi: { list: vi.fn().mockResolvedValue([]) },
}))
vi.mock("../hooks/useVersions", () => ({
  useVersions: () => ({ data: [
    { id: 3, name: "v1.0" },
    { id: 4, name: "v1.1" },
  ] }),
}))
vi.mock("sonner", () => ({ toast: { success: vi.fn(), error: vi.fn() } }))

import { bugsApi } from "../api/bugs"
import { NewBugDialog } from "../components/bug/NewBugDialog"

function setup(prefill) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <NewBugDialog
        projectId={9}
        prefill={prefill}
        trigger={<button>Open</button>}
      />
    </QueryClientProvider>,
  )
}

describe("NewBugDialog", () => {
  it("submits the affected version selected from the UI", async () => {
    bugsApi.create.mockClear()
    setup()

    fireEvent.click(screen.getByText("Open"))
    const inputs = await screen.findAllByRole("textbox")
    fireEvent.change(inputs[0], { target: { value: "Crash on save" } })
    fireEvent.click(screen.getByLabelText(/affected version/i))
    fireEvent.click(screen.getByRole("option", { name: "v1.1" }))
    fireEvent.submit(inputs[0].closest("form"))

    await waitFor(() => expect(bugsApi.create).toHaveBeenCalledTimes(1))
    expect(bugsApi.create).toHaveBeenCalledWith(9, expect.objectContaining({
      title: "Crash on save",
      version_id: 4,
    }))
  })

  it("submits the prefill payload from a failed result", async () => {
    setup({
      result_id: 12,
      execution_id: 7,
      version_id: 3,
      environment: "staging",
      description: "From result Login",
      severity: "high",
    })

    fireEvent.click(screen.getByText("Open"))
    const inputs = await screen.findAllByRole("textbox")
    const titleInput = inputs[0]
    fireEvent.change(titleInput, { target: { value: "Login crash" } })
    fireEvent.submit(titleInput.closest("form"))

    await waitFor(() => expect(bugsApi.create).toHaveBeenCalledTimes(1))
    expect(bugsApi.create).toHaveBeenCalledWith(9, expect.objectContaining({
      title: "Login crash",
      severity: "high",
      result_id: 12,
      execution_id: 7,
      version_id: 3,
      environment: "staging",
      description: "From result Login",
    }))
  })
})
