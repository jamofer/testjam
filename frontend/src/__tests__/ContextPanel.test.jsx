import { describe, it, expect } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import { Tag } from "lucide-react"
import { ContextPanel } from "../components/ui/context-panel"

describe("ContextPanel", () => {
  it("renders rows for each non-empty value", () => {
    render(
      <ContextPanel
        sections={[
          {
            title: "About",
            rows: [
              { label: "Project", value: "Acme" },
              { label: "Status", value: "completed" },
              { label: "Skipped", value: null },
              { label: "Empty", value: "" },
            ],
          },
        ]}
      />,
    )
    expect(screen.getByText("Acme")).toBeInTheDocument()
    expect(screen.getByText("completed")).toBeInTheDocument()
    expect(screen.queryByText("Skipped")).toBeNull()
    expect(screen.queryByText("Empty")).toBeNull()
  })

  it("collapses a section when its header is clicked", () => {
    render(
      <ContextPanel
        sections={[{ title: "About", rows: [{ label: "Project", value: "Acme" }] }]}
      />,
    )
    expect(screen.getByText("Acme")).toBeInTheDocument()
    fireEvent.click(screen.getByRole("button", { name: /about/i }))
    expect(screen.queryByText("Acme")).toBeNull()
  })

  it("hides itself when the panel is collapsed", () => {
    render(
      <ContextPanel
        sections={[{ title: "About", rows: [{ label: "Project", value: "Acme" }] }]}
      />,
    )
    fireEvent.click(screen.getByRole("button", { name: /collapse context panel/i }))
    expect(screen.queryByText("Acme")).toBeNull()
    expect(screen.getByRole("button", { name: /expand context panel/i })).toBeInTheDocument()
  })

  it("renders a custom body for sections without rows", () => {
    render(
      <ContextPanel
        sections={[{ title: "Tags", body: <span>smoke</span> }]}
      />,
    )
    expect(screen.getByText("smoke")).toBeInTheDocument()
  })

  it("supports an icon on a row", () => {
    render(
      <ContextPanel
        sections={[{
          title: "About",
          rows: [{ label: "Tag", value: "smoke", icon: Tag }],
        }]}
      />,
    )
    expect(screen.getByText("smoke")).toBeInTheDocument()
  })
})
