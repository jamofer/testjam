import { useCallback } from "react"

export function focusSiblingTreeitem(current, delta) {
  const items = Array.from(document.querySelectorAll('[role="treeitem"]'))
  const idx = items.indexOf(current)
  if (idx < 0) return
  const target = items[idx + delta]
  if (target) target.focus()
}

const PREV_KEYS = new Set(["ArrowUp", "k"])
const NEXT_KEYS = new Set(["ArrowDown", "j"])
const COLLAPSE_KEYS = new Set(["ArrowLeft", "h"])
const EXPAND_KEYS = new Set(["ArrowRight", "l"])
const ACTIVATE_KEYS = new Set(["Enter"])
const SELECT_KEYS = new Set([" ", "x"])

export function useTreeItemNav({
  onPrev,
  onNext,
  onCollapse,
  onExpand,
  onActivate,
  onToggleSelect,
  ignoreUnlessSelfTarget = false,
} = {}) {
  return useCallback((event) => {
    if (ignoreUnlessSelfTarget && event.target !== event.currentTarget) return
    const { key } = event
    const fallbackSiblingNav = (delta) => focusSiblingTreeitem(event.currentTarget, delta)
    const dispatch = (handler, fallback) => {
      event.preventDefault()
      ;(handler ?? fallback)?.(event)
    }

    if (PREV_KEYS.has(key)) return dispatch(onPrev, () => fallbackSiblingNav(-1))
    if (NEXT_KEYS.has(key)) return dispatch(onNext, () => fallbackSiblingNav(1))
    if (COLLAPSE_KEYS.has(key)) { if (onCollapse) dispatch(onCollapse); return }
    if (EXPAND_KEYS.has(key)) { if (onExpand) dispatch(onExpand); return }
    if (ACTIVATE_KEYS.has(key)) { if (onActivate) dispatch(onActivate); return }
    if (SELECT_KEYS.has(key)) { if (onToggleSelect) dispatch(onToggleSelect); return }
  }, [onPrev, onNext, onCollapse, onExpand, onActivate, onToggleSelect, ignoreUnlessSelfTarget])
}
