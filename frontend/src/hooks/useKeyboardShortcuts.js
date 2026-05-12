import { useEffect } from "react"

/*
 * Keyboard shortcut conventions across the app:
 *
 *  - `Esc` is owned by dialogs and popovers (Radix Dialog, custom popovers like
 *    NotificationsBell / UserMenu). Page-level handlers must NOT register
 *    `Escape`; preventDefault on a parent listener trips Radix's
 *    DismissableLayer (`event.defaultPrevented` check) and breaks dismissal.
 *
 *  - Page handlers use this hook for global single-key shortcuts (Home/End,
 *    PgUp/PgDn, +, -, /, ?, F/B/U, …). Tree-item navigation (j/k/h/l/arrows
 *    inside a focusable row) goes through `useTreeItemNav`, not here.
 *
 *  - When the page exposes shortcuts, render a `<Keyboard>` icon button in
 *    the header that opens a `ShortcutsDialog`. `?` toggles that dialog.
 *
 *  - Vim single-keys (j/k/h/l) coexist with arrows where natural — both fire
 *    the same handler.
 */

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
