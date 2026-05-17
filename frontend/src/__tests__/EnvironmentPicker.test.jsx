import { describe, it, expect, vi } from "vitest"
import { render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"

import { EnvironmentPicker } from "../components/environment/EnvironmentPicker"

vi.mock("../api/environments", () => ({
  environmentsApi: { list: vi.fn() },
}))

import { environmentsApi } from "../api/environments"

function setup(initialValue = null, environments = []) {
  environmentsApi.list.mockResolvedValue(environments)
  const onChange = vi.fn()
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  function Wrapper() {
    return (
      <QueryClientProvider client={queryClient}>
        <EnvironmentPicker projectId={1} value={initialValue} onChange={onChange} />
      </QueryClientProvider>
    )
  }
  return { onChange, ...render(<Wrapper />) }
}

describe("EnvironmentPicker", () => {
  it("falls back to free-text input when the value has no catalog match", async () => {
    setup("legacy-value", [{ id: 1, slug: "prod", name: "Production", is_default: false }])

    await waitFor(() =>
      expect(screen.getByPlaceholderText("Custom value")).toHaveValue("legacy-value"),
    )
  })

  it("auto-selects the default environment when no value is provided", async () => {
    const { onChange } = setup(null, [
      { id: 1, slug: "prod", name: "Production", is_default: true },
      { id: 2, slug: "staging", name: "Staging", is_default: false },
    ])

    await waitFor(() => expect(onChange).toHaveBeenCalledWith("prod"))
  })

  it("clears free text when the user switches back to catalog mode", async () => {
    const user = userEvent.setup()
    const { onChange } = setup("legacy-value", [
      { id: 1, slug: "prod", name: "Production", is_default: false },
    ])

    await screen.findByPlaceholderText("Custom value")
    await user.click(screen.getByRole("button", { name: /pick from catalog/i }))

    expect(onChange).toHaveBeenLastCalledWith(null)
  })
})
