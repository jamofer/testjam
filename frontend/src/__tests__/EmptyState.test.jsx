import { describe, it, expect } from "vitest"
import { render, screen } from "@testing-library/react"
import { FolderOpen } from "lucide-react"
import { EmptyState } from "../components/ui/empty-state"

describe("EmptyState", () => {
  it("renders the title and description", () => {
    render(<EmptyState title="No data" description="Add some" />)
    expect(screen.getByText("No data")).toBeInTheDocument()
    expect(screen.getByText("Add some")).toBeInTheDocument()
  })

  it("renders an icon when provided", () => {
    const { container } = render(<EmptyState icon={FolderOpen} title="Empty" />)
    expect(container.querySelector("svg")).toBeInTheDocument()
  })

  it("renders an action node when provided", () => {
    render(
      <EmptyState
        title="Empty"
        action={<button>Click me</button>}
      />
    )
    expect(screen.getByRole("button", { name: "Click me" })).toBeInTheDocument()
  })

  it("uses status role for accessibility", () => {
    render(<EmptyState title="No data" />)
    expect(screen.getByRole("status")).toBeInTheDocument()
  })

  it("supports compact mode", () => {
    const { container } = render(<EmptyState title="Empty" compact />)
    // compact uses py-6 instead of py-12
    const root = container.firstChild
    expect(root.className).toContain("py-6")
    expect(root.className).not.toContain("py-12")
  })
})
