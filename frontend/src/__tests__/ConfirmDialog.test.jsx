import { describe, it, expect, vi } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"

import { ConfirmDialog } from "../components/ui/confirm-dialog"


describe("ConfirmDialog", () => {
  it("renders the title and description", () => {
    render(
      <ConfirmDialog
        open
        onOpenChange={() => {}}
        title="Delete bug #5?"
        description="This cannot be undone."
        onConfirm={() => {}}
      />,
    )

    expect(screen.getByText("Delete bug #5?")).toBeInTheDocument()
    expect(screen.getByText("This cannot be undone.")).toBeInTheDocument()
  })

  it("calls onConfirm when the confirm button is clicked", () => {
    const onConfirm = vi.fn()
    render(
      <ConfirmDialog
        open
        onOpenChange={() => {}}
        title="Delete"
        confirmLabel="Delete"
        destructive
        onConfirm={onConfirm}
      />,
    )

    fireEvent.click(screen.getByRole("button", { name: "Delete" }))

    expect(onConfirm).toHaveBeenCalled()
  })

  it("closes via onOpenChange when cancel is clicked", () => {
    const onOpenChange = vi.fn()
    render(
      <ConfirmDialog
        open
        onOpenChange={onOpenChange}
        title="Delete"
        cancelLabel="Nope"
        onConfirm={() => {}}
      />,
    )

    fireEvent.click(screen.getByRole("button", { name: "Nope" }))

    expect(onOpenChange).toHaveBeenCalledWith(false)
  })

  it("disables both buttons when busy", () => {
    render(
      <ConfirmDialog
        open
        onOpenChange={() => {}}
        title="Delete"
        confirmLabel="Yes"
        cancelLabel="No"
        busy
        onConfirm={() => {}}
      />,
    )

    expect(screen.getByRole("button", { name: "Yes" })).toBeDisabled()
    expect(screen.getByRole("button", { name: "No" })).toBeDisabled()
  })
})
