import { describe, it, expect, vi } from "vitest"
import { fireEvent, render, screen } from "@testing-library/react"

import "../i18n"
import { ErrorState } from "../components/ui/error-state"

describe("ErrorState", () => {
  it("falls back to the shared translated title + description", () => {
    render(<ErrorState />)

    expect(screen.getByRole("alert")).toBeInTheDocument()
    expect(screen.getByText(/couldn't load/i)).toBeInTheDocument()
  })

  it("renders an overridden title + description", () => {
    render(<ErrorState title="Custom title" description="Custom body" />)

    expect(screen.getByText("Custom title")).toBeInTheDocument()
    expect(screen.getByText("Custom body")).toBeInTheDocument()
  })

  it("invokes onRetry when the Retry button is clicked", () => {
    const onRetry = vi.fn()
    render(<ErrorState onRetry={onRetry} />)

    fireEvent.click(screen.getByRole("button", { name: /retry/i }))

    expect(onRetry).toHaveBeenCalledOnce()
  })

  it("hides the retry button when onRetry is not supplied", () => {
    render(<ErrorState />)

    expect(screen.queryByRole("button", { name: /retry/i })).toBeNull()
  })
})
