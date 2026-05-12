import { describe, it, expect, vi } from "vitest"
import { render, screen } from "@testing-library/react"
import { ShortcutsDialog } from "../components/ui/shortcuts-dialog"

describe("ShortcutsDialog", () => {
  const sections = [
    {
      title: "Navigation",
      rows: [
        { keys: ["j", "↓"], description: "Next item" },
        { keys: ["?"], description: "Toggle help" },
      ],
    },
    {
      title: "Actions",
      rows: [{ keys: ["+"], description: "Expand all" }],
    },
  ]

  it("renders title, descriptions, and one kbd per key", () => {
    render(
      <ShortcutsDialog open onOpenChange={vi.fn()} title="My shortcuts"
        description="Helpful blurb" sections={sections} />
    )

    expect(screen.getByText("My shortcuts")).toBeInTheDocument()
    expect(screen.getByText("Helpful blurb")).toBeInTheDocument()
    expect(screen.getByText("Navigation")).toBeInTheDocument()
    expect(screen.getByText("Actions")).toBeInTheDocument()
    expect(screen.getByText("Next item")).toBeInTheDocument()
    expect(screen.getByText("Expand all")).toBeInTheDocument()

    const jKbd = screen.getByText("j")
    expect(jKbd.tagName).toBe("KBD")
  })

  it("renders nothing when closed", () => {
    render(
      <ShortcutsDialog open={false} onOpenChange={vi.fn()} sections={sections} />
    )
    expect(screen.queryByText("Next item")).not.toBeInTheDocument()
  })
})
