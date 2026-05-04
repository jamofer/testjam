import { describe, it, expect, vi, beforeEach, afterEach } from "vitest"
import { renderHook, act } from "@testing-library/react"
import { useDebounced } from "../hooks/useDebounced"

beforeEach(() => vi.useFakeTimers())
afterEach(() => vi.useRealTimers())

describe("useDebounced", () => {
  it("returns the initial value immediately", () => {
    const { result } = renderHook(() => useDebounced("hello", 100))
    expect(result.current).toBe("hello")
  })

  it("delays the new value by the requested delay", () => {
    const { result, rerender } = renderHook(({ v }) => useDebounced(v, 200), {
      initialProps: { v: "a" },
    })
    rerender({ v: "b" })
    expect(result.current).toBe("a")
    act(() => { vi.advanceTimersByTime(199) })
    expect(result.current).toBe("a")
    act(() => { vi.advanceTimersByTime(1) })
    expect(result.current).toBe("b")
  })

  it("cancels pending updates if the value changes again", () => {
    const { result, rerender } = renderHook(({ v }) => useDebounced(v, 200), {
      initialProps: { v: "a" },
    })
    rerender({ v: "b" })
    act(() => { vi.advanceTimersByTime(100) })
    rerender({ v: "c" })
    act(() => { vi.advanceTimersByTime(100) })
    expect(result.current).toBe("a")  // still old, the "b" update was cancelled
    act(() => { vi.advanceTimersByTime(100) })
    expect(result.current).toBe("c")
  })
})
