import { useRef } from "react"

const SKIP_SELECTOR = "input, textarea, select, button, a, [contenteditable], pre, code"

const DEFAULT_OPTIONS = {
  threshold: 60,
  maxOffAxis: 60,
  maxDuration: 600,
}

/**
 * Detect horizontal swipes (left/right) on touch devices.
 * Returns props to spread on a container element.
 *
 * Ignores touches that originate on interactive controls or scrollable
 * code blocks so they keep their native behavior.
 */
export function useSwipe({ onSwipeLeft, onSwipeRight } = {}, options = {}) {
  const opts = { ...DEFAULT_OPTIONS, ...options }
  const start = useRef(null)

  const onTouchStart = (e) => {
    if (e.touches.length !== 1) {
      start.current = null
      return
    }
    if (e.target?.closest?.(SKIP_SELECTOR)) {
      start.current = null
      return
    }
    const t = e.touches[0]
    start.current = { x: t.clientX, y: t.clientY, t: Date.now() }
  }

  const onTouchEnd = (e) => {
    const s = start.current
    start.current = null
    if (!s) return
    const t = e.changedTouches[0]
    if (!t) return
    const dx = t.clientX - s.x
    const dy = t.clientY - s.y
    const dt = Date.now() - s.t
    if (dt > opts.maxDuration) return
    if (Math.abs(dy) > opts.maxOffAxis) return
    if (Math.abs(dx) < opts.threshold) return
    if (dx < 0) onSwipeLeft?.()
    else onSwipeRight?.()
  }

  const onTouchCancel = () => { start.current = null }

  return { onTouchStart, onTouchEnd, onTouchCancel }
}
