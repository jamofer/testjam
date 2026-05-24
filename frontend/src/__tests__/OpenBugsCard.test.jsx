import { describe, it, expect, vi } from "vitest"
import { render, screen } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { MemoryRouter } from "react-router-dom"

import { OpenBugsCard } from "../components/dashboard/OpenBugsCard"

vi.mock("../api/bugs", () => ({
  bugsApi: { list: vi.fn() },
}))


function renderCard({ bugs }) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0, staleTime: Infinity } },
  })
  queryClient.setQueryData(["bugs", 5, {}], bugs)
  render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <OpenBugsCard projectId={5} />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}


describe("OpenBugsCard", () => {
  it("renders the empty state when there are no active bugs", () => {
    renderCard({ bugs: [
      { id: 1, number: 1, title: "Closed one", severity: "low", status: "closed" },
    ] })

    expect(screen.getByText(/no open bugs/i)).toBeInTheDocument()
  })

  it("lists active bugs with title, severity, and status badges", () => {
    renderCard({ bugs: [
      { id: 1, number: 7, title: "Login crash", severity: "critical", status: "open" },
      { id: 2, number: 8, title: "Slow report", severity: "medium", status: "in_progress" },
    ] })

    expect(screen.getByText("Login crash")).toBeInTheDocument()
    expect(screen.getByText("Slow report")).toBeInTheDocument()
    expect(screen.getByText("#7")).toBeInTheDocument()
    expect(screen.getByText("#8")).toBeInTheDocument()
    expect(screen.getByText("Critical")).toBeInTheDocument()
    expect(screen.getByText("Open")).toBeInTheDocument()
    expect(screen.getByText("In progress")).toBeInTheDocument()
  })

  it("caps the recent list at 5 even when more bugs exist", () => {
    const many = Array.from({ length: 8 }, (_, index) => ({
      id: index + 1, number: index + 1,
      title: `Bug ${index + 1}`, severity: "low", status: "open",
    }))

    renderCard({ bugs: many })

    expect(screen.getByText("Bug 8")).toBeInTheDocument()
    expect(screen.getByText("Bug 7")).toBeInTheDocument()
    expect(screen.getByText("Bug 4")).toBeInTheDocument()
    expect(screen.queryByText("Bug 3")).toBeNull()
    expect(screen.queryByText("Bug 1")).toBeNull()
  })

  it("links each bug row to the bug detail page", () => {
    renderCard({ bugs: [
      { id: 1, number: 42, title: "Boom", severity: "high", status: "open" },
    ] })

    const link = screen.getByRole("link", { name: /Boom/i })
    expect(link.getAttribute("href")).toBe("/projects/5/bugs/42")
  })

  it("sorts the recent list by bug number descending", () => {
    renderCard({ bugs: [
      { id: 1, number: 3, title: "Older", severity: "low", status: "open" },
      { id: 2, number: 9, title: "Newest", severity: "low", status: "open" },
      { id: 3, number: 5, title: "Middle", severity: "low", status: "open" },
    ] })

    const titles = screen.getAllByRole("link")
      .map(link => link.textContent)
      .filter(text => /Older|Newest|Middle/.test(text))
    expect(titles[0]).toContain("Newest")
    expect(titles[1]).toContain("Middle")
    expect(titles[2]).toContain("Older")
  })
})
