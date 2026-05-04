import { describe, it, expect } from "vitest"
import { render, screen } from "@testing-library/react"
import { MemoryRouter } from "react-router-dom"
import { Breadcrumbs } from "../components/ui/breadcrumbs"

function renderWithRouter(ui) {
  return render(<MemoryRouter>{ui}</MemoryRouter>)
}

describe("Breadcrumbs", () => {
  it("returns nothing when there are no crumbs", () => {
    const { container } = renderWithRouter(<Breadcrumbs crumbs={[]} />)
    expect(container.firstChild).toBeNull()
  })

  it("renders all crumb labels", () => {
    renderWithRouter(
      <Breadcrumbs
        crumbs={[
          { label: "Projects", to: "/projects" },
          { label: "Acme", to: "/projects/1" },
          { label: "Executions" },
        ]}
      />
    )
    expect(screen.getByText("Projects")).toBeInTheDocument()
    expect(screen.getByText("Acme")).toBeInTheDocument()
    expect(screen.getByText("Executions")).toBeInTheDocument()
  })

  it("renders earlier crumbs as links and the last as plain text", () => {
    renderWithRouter(
      <Breadcrumbs
        crumbs={[
          { label: "Projects", to: "/projects" },
          { label: "Current Page" },
        ]}
      />
    )
    expect(screen.getByRole("link", { name: "Projects" })).toBeInTheDocument()
    expect(screen.queryByRole("link", { name: "Current Page" })).toBeNull()
  })

  it("marks the last crumb with aria-current=page", () => {
    renderWithRouter(
      <Breadcrumbs crumbs={[{ label: "A", to: "/a" }, { label: "B" }]} />
    )
    expect(screen.getByText("B").getAttribute("aria-current")).toBe("page")
  })

  it("uses the navigation landmark", () => {
    renderWithRouter(<Breadcrumbs crumbs={[{ label: "Home" }]} />)
    expect(screen.getByRole("navigation", { name: "Breadcrumb" })).toBeInTheDocument()
  })
})
