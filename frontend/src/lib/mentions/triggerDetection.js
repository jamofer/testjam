// Trigger chars map. Order matters only for documentation.
const TRIGGER_KINDS = {
  "@": "user",
  "#": "bug",
  "!": "execution",
  "~": "case",
}

const STOP_CHARS = /[\s,;:.()\[\]{}'"`]/

// Given the current textarea value and caret position, decide whether an
// autocomplete popover should be open and what kind/query to send.
//
// Returns `null` when no trigger is active. Otherwise:
//   { kind, query, anchorIndex, caretIndex, triggerChar }
//
// Rules:
// - The trigger char must be preceded by whitespace or be the start of value
//   (so an email "alice@host" never triggers the user popover).
// - The query is the substring after the trigger up to (but excluding) the
//   first whitespace/punctuation following it — caps at the caret position.
// - Backspacing past the trigger closes the popover.
export function detectActiveTrigger(value, caret) {
  if (!value || caret <= 0) return null
  for (let cursor = caret - 1; cursor >= 0; cursor -= 1) {
    const char = value[cursor]
    if (TRIGGER_KINDS[char]) {
      if (cursor > 0 && !/\s/.test(value[cursor - 1])) return null
      const query = value.slice(cursor + 1, caret)
      if (STOP_CHARS.test(query)) return null
      return {
        kind: TRIGGER_KINDS[char],
        triggerChar: char,
        query,
        anchorIndex: cursor,
        caretIndex: caret,
      }
    }
    if (STOP_CHARS.test(char)) return null
  }
  return null
}

// Build the canonical token to insert when a hit is selected.
// User → `@slug`. Other kinds → `<trigger><id>`.
export function buildCanonicalToken(triggerChar, hit) {
  if (triggerChar === "@" && hit.slug) {
    return `@${hit.slug}`
  }
  if (hit.id != null) {
    return `${triggerChar}${hit.id}`
  }
  return triggerChar
}

export function replaceRange(value, start, end, replacement) {
  return `${value.slice(0, start)}${replacement}${value.slice(end)}`
}
