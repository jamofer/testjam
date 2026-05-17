import { describe, it, expect, vi } from "vitest"
import { render, screen } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"

import { EnvironmentBadge } from "../components/environment/EnvironmentBadge"

vi.mock("../api/environments", () => ({
  environmentsApi: {
    list: vi.fn(),
  },
}))

import { environmentsApi } from "../api/environments"

function renderBadge(slug) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <EnvironmentBadge projectId={1} slug={slug} />
    </QueryClientProvider>,
  )
}

describe("EnvironmentBadge", () => {
  it("renders nothing without a slug", () => {
    environmentsApi.list.mockResolvedValue([])
    const { container } = renderBadge(null)
    expect(container.firstChild).toBeNull()
  })

  it("renders the raw slug when no catalog match", async () => {
    environmentsApi.list.mockResolvedValue([
      { id: 1, slug: "prod", name: "Production", color: "#10b981" },
    ])
    renderBadge("staging")
    expect(await screen.findByText("staging")).toBeInTheDocument()
  })

  it("renders the catalog name and applies hex color when matched", async () => {
    environmentsApi.list.mockResolvedValue([
      { id: 1, slug: "prod", name: "Production EU", color: "#10b981" },
    ])
    renderBadge("prod")
    const node = await screen.findByText("Production EU")
    expect(node.style.color).toBe("rgb(16, 185, 129)")
  })
})
