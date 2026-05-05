import { describe, it, expect, vi } from "vitest"
import { renderHook, render } from "@testing-library/react"
import { useKeyboardShortcuts } from "../hooks/useKeyboardShortcuts"

function fireKey(key, target = document) {
  const event = new KeyboardEvent("keydown", { key, bubbles: true, cancelable: true })
  target.dispatchEvent(event)
  return event
}

describe("useKeyboardShortcuts", () => {
  it("invokes the matching handler", () => {
    const onP = vi.fn()
    renderHook(() => useKeyboardShortcuts({ p: onP }))
    fireKey("p")
    expect(onP).toHaveBeenCalledOnce()
  })

  it("ignores keys without a registered handler", () => {
    const onP = vi.fn()
    renderHook(() => useKeyboardShortcuts({ p: onP }))
    fireKey("x")
    expect(onP).not.toHaveBeenCalled()
  })

  it("does not fire when typing in an input", () => {
    const { container } = render(<input data-testid="i" />)
    const input = container.querySelector("input")
    input.focus()
    const onP = vi.fn()
    renderHook(() => useKeyboardShortcuts({ p: onP }))
    const event = new KeyboardEvent("keydown", { key: "p", bubbles: true })
    input.dispatchEvent(event)
    expect(onP).not.toHaveBeenCalled()
  })

  it("does fire inside inputs for keys in allowWhileTyping", () => {
    const { container } = render(<input />)
    const input = container.querySelector("input")
    input.focus()
    const onEsc = vi.fn()
    renderHook(() => useKeyboardShortcuts({ Escape: onEsc }, { allowWhileTyping: ["Escape"] }))
    const event = new KeyboardEvent("keydown", { key: "Escape", bubbles: true })
    input.dispatchEvent(event)
    expect(onEsc).toHaveBeenCalledOnce()
  })

  it("ignores combos with modifier keys", () => {
    const onP = vi.fn()
    renderHook(() => useKeyboardShortcuts({ p: onP }))
    document.dispatchEvent(new KeyboardEvent("keydown", { key: "p", ctrlKey: true, bubbles: true }))
    document.dispatchEvent(new KeyboardEvent("keydown", { key: "p", metaKey: true, bubbles: true }))
    expect(onP).not.toHaveBeenCalled()
  })

  it("does nothing when enabled is false", () => {
    const onP = vi.fn()
    renderHook(() => useKeyboardShortcuts({ p: onP }, { enabled: false }))
    fireKey("p")
    expect(onP).not.toHaveBeenCalled()
  })

  it("removes listener on unmount", () => {
    const onP = vi.fn()
    const { unmount } = renderHook(() => useKeyboardShortcuts({ p: onP }))
    unmount()
    fireKey("p")
    expect(onP).not.toHaveBeenCalled()
  })
})
