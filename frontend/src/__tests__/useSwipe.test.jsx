import { describe, it, expect, vi, beforeEach, afterEach } from "vitest"
import { render, fireEvent } from "@testing-library/react"
import { useSwipe } from "../hooks/useSwipe"

function Surface({ onLeft, onRight }) {
  const handlers = useSwipe({ onSwipeLeft: onLeft, onSwipeRight: onRight })
  return (
    <div data-testid="surface" style={{ width: 400, height: 300 }} {...handlers}>
      <input data-testid="text-input" />
      <pre data-testid="log">log content</pre>
      content
    </div>
  )
}

function touch(target, x, y) {
  return { clientX: x, clientY: y, target }
}

beforeEach(() => { vi.useFakeTimers({ now: 1_000_000 }) })
afterEach(() => { vi.useRealTimers() })

describe("useSwipe", () => {
  it("fires onSwipeLeft when finger moves >= threshold to the left", () => {
    const onLeft = vi.fn()
    const onRight = vi.fn()
    const { getByTestId } = render(<Surface onLeft={onLeft} onRight={onRight} />)
    const surface = getByTestId("surface")

    fireEvent.touchStart(surface, { touches: [touch(surface, 300, 100)] })
    vi.advanceTimersByTime(120)
    fireEvent.touchEnd(surface, { changedTouches: [touch(surface, 200, 105)] })

    expect(onLeft).toHaveBeenCalledTimes(1)
    expect(onRight).not.toHaveBeenCalled()
  })

  it("fires onSwipeRight when finger moves >= threshold to the right", () => {
    const onLeft = vi.fn()
    const onRight = vi.fn()
    const { getByTestId } = render(<Surface onLeft={onLeft} onRight={onRight} />)
    const surface = getByTestId("surface")

    fireEvent.touchStart(surface, { touches: [touch(surface, 50, 100)] })
    vi.advanceTimersByTime(120)
    fireEvent.touchEnd(surface, { changedTouches: [touch(surface, 200, 110)] })

    expect(onRight).toHaveBeenCalledTimes(1)
    expect(onLeft).not.toHaveBeenCalled()
  })

  it("ignores small horizontal motion (< threshold)", () => {
    const onLeft = vi.fn()
    const onRight = vi.fn()
    const { getByTestId } = render(<Surface onLeft={onLeft} onRight={onRight} />)
    const surface = getByTestId("surface")

    fireEvent.touchStart(surface, { touches: [touch(surface, 100, 100)] })
    vi.advanceTimersByTime(80)
    fireEvent.touchEnd(surface, { changedTouches: [touch(surface, 130, 100)] })

    expect(onLeft).not.toHaveBeenCalled()
    expect(onRight).not.toHaveBeenCalled()
  })

  it("ignores motion that is mostly vertical", () => {
    const onLeft = vi.fn()
    const onRight = vi.fn()
    const { getByTestId } = render(<Surface onLeft={onLeft} onRight={onRight} />)
    const surface = getByTestId("surface")

    fireEvent.touchStart(surface, { touches: [touch(surface, 100, 100)] })
    vi.advanceTimersByTime(120)
    fireEvent.touchEnd(surface, { changedTouches: [touch(surface, 200, 300)] })

    expect(onLeft).not.toHaveBeenCalled()
    expect(onRight).not.toHaveBeenCalled()
  })

  it("ignores swipes that start on interactive controls", () => {
    const onLeft = vi.fn()
    const { getByTestId } = render(<Surface onLeft={onLeft} onRight={() => {}} />)
    const input = getByTestId("text-input")

    fireEvent.touchStart(input, { touches: [touch(input, 300, 100)] })
    vi.advanceTimersByTime(120)
    fireEvent.touchEnd(input, { changedTouches: [touch(input, 200, 100)] })

    expect(onLeft).not.toHaveBeenCalled()
  })

  it("ignores swipes that start inside scrollable code blocks", () => {
    const onLeft = vi.fn()
    const { getByTestId } = render(<Surface onLeft={onLeft} onRight={() => {}} />)
    const log = getByTestId("log")

    fireEvent.touchStart(log, { touches: [touch(log, 300, 100)] })
    vi.advanceTimersByTime(120)
    fireEvent.touchEnd(log, { changedTouches: [touch(log, 200, 100)] })

    expect(onLeft).not.toHaveBeenCalled()
  })

  it("ignores slow swipes (> maxDuration)", () => {
    const onLeft = vi.fn()
    const { getByTestId } = render(<Surface onLeft={onLeft} onRight={() => {}} />)
    const surface = getByTestId("surface")

    fireEvent.touchStart(surface, { touches: [touch(surface, 300, 100)] })
    vi.advanceTimersByTime(800)
    fireEvent.touchEnd(surface, { changedTouches: [touch(surface, 200, 100)] })

    expect(onLeft).not.toHaveBeenCalled()
  })
})
