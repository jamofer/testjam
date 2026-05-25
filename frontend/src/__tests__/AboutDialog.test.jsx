import { describe, it, expect, vi } from "vitest"
import { render, screen } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"

import { AboutDialog, aboutShortLabel } from "../components/ui/about-dialog"

vi.mock("../api/about", () => ({
  aboutApi: {
    get: vi.fn(),
  },
}))

import { aboutApi } from "../api/about"

function renderDialog() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <AboutDialog open={true} onOpenChange={() => {}} />
    </QueryClientProvider>,
  )
}

describe("aboutShortLabel", () => {
  it("returns the tag when ref is a release tag", () => {
    expect(aboutShortLabel({ ref: "v1.0.0", commit: "abc1234", version: "1.0.0" })).toBe("v1.0.0")
  })

  it("returns ref @ commit when ref is a branch", () => {
    expect(aboutShortLabel({ ref: "master", commit: "abc1234", version: "0.1.0" })).toBe("master @ abc1234")
  })

  it("falls back to package version when ref and commit are unknown", () => {
    expect(aboutShortLabel({ ref: "unknown", commit: "unknown", version: "0.1.0" })).toBe("v0.1.0")
  })

  it("returns null when there is no data", () => {
    expect(aboutShortLabel(null)).toBeNull()
  })
})

describe("AboutDialog", () => {
  it("renders the release tag verbatim when ref looks like a tag", async () => {
    aboutApi.get.mockResolvedValue({
      version: "1.0.0",
      ref: "v1.0.0",
      commit: "abc1234",
      built_at: "2026-05-25T12:00:00Z",
    })

    renderDialog()

    expect(await screen.findByText("v1.0.0")).toBeInTheDocument()
    expect(screen.getByText("abc1234")).toBeInTheDocument()
  })

  it("renders ref @ commit when ref is a branch", async () => {
    aboutApi.get.mockResolvedValue({
      version: "0.1.0",
      ref: "master",
      commit: "abc1234",
      built_at: "unknown",
    })

    renderDialog()

    expect(await screen.findByText("master @ abc1234")).toBeInTheDocument()
  })
})
