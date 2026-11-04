import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"

import { CustomFieldsPanel } from "../components/customField/CustomFieldsPanel"

vi.mock("sonner", () => ({ toast: { success: vi.fn(), error: vi.fn() } }))
vi.mock("../api/customFields", () => ({
  customFieldsApi: { list: vi.fn(), update: vi.fn() },
}))

import { customFieldsApi } from "../api/customFields"

const PRIORITY_FIELD = {
  id: 7,
  project_id: 1,
  entity_type: "bug",
  key: "priority",
  label: "Priority",
  type: "single_select",
  options: [
    { value: "p0", label: "P0", color: "#ef4444" },
    { value: "p1", label: "P1", color: null },
  ],
  required: false,
  default_value: null,
  position: 0,
  archived_at: null,
}

describe("CustomFieldsPanel option colors", () => {
  beforeEach(() => {
    customFieldsApi.list.mockReset()
    customFieldsApi.update.mockReset()
    customFieldsApi.list.mockResolvedValue([PRIORITY_FIELD])
    customFieldsApi.update.mockResolvedValue(PRIORITY_FIELD)
  })

  it("shows a swatch with the saved color for each option", async () => {
    renderPanel()

    const swatch = await screen.findByLabelText("Color for P0")

    expect(swatch).toHaveValue("#ef4444")
    expect(screen.getByLabelText("Color for P1")).toHaveValue("#9ca3af")
  })

  it("saves the picked color on its option only", async () => {
    renderPanel()
    const swatch = await screen.findByLabelText("Color for P1")

    fireEvent.change(swatch, { target: { value: "#22c55e" } })

    await waitFor(() => expect(customFieldsApi.update).toHaveBeenCalledWith(7, {
      options: [
        { value: "p0", label: "P0", color: "#ef4444" },
        { value: "p1", label: "P1", color: "#22c55e" },
      ],
    }))
  })

  it("saves once with the last color while the picker is dragged", async () => {
    renderPanel()
    const swatch = await screen.findByLabelText("Color for P0")

    fireEvent.change(swatch, { target: { value: "#111111" } })
    fireEvent.change(swatch, { target: { value: "#222222" } })
    fireEvent.change(swatch, { target: { value: "#333333" } })

    await waitFor(() => expect(customFieldsApi.update).toHaveBeenCalledTimes(1))
    const [, payload] = customFieldsApi.update.mock.calls[0]
    expect(payload.options[0].color).toBe("#333333")
  })
})

function renderPanel() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <CustomFieldsPanel projectId={1} />
    </QueryClientProvider>,
  )
}
