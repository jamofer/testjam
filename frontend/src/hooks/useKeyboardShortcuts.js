import { useEffect } from "react"

const TYPING_TAGS = new Set(["INPUT", "TEXTAREA", "SELECT"])

function isTyping(target) {
  if (!target) return false
  if (TYPING_TAGS.has(target.tagName)) return true
  if (target.isContentEditable) return true
  return false
}

/**
 * Bind a map of single-key shortcuts to a handler.
 *
 * shortcuts: { [key]: handler }   — handler receives the KeyboardEvent
 * options.enabled: skip when false
 * options.allowWhileTyping: keys that fire even inside inputs (e.g. "Escape")
 */
export function useKeyboardShortcuts(shortcuts, { enabled = true, allowWhileTyping = [] } = {}) {
  useEffect(() => {
    if (!enabled) return
    const handler = (e) => {
      if (e.metaKey || e.ctrlKey || e.altKey) return
      const fn = shortcuts[e.key]
      if (!fn) return
      if (isTyping(e.target) && !allowWhileTyping.includes(e.key)) return
      e.preventDefault()
      fn(e)
    }
    window.addEventListener("keydown", handler)
    return () => window.removeEventListener("keydown", handler)
  }, [shortcuts, enabled, allowWhileTyping])
}
