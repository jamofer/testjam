// Trigger chars map. Order matters only for documentation.
const TRIGGER_KINDS = {
  "@": "user",
  "#": "bug",
  "!": "execution",
  "~": "case",
}

const STOP_CHARS = /[\s,;:()\[\]{}'"`]/

// Given the current textarea value and caret position, decide whether an
// autocomplete popover should be open and what kind/query to send.
//
// Returns `null` when no trigger is active. Otherwise:
//   { kind, query, anchorIndex, caretIndex, triggerChar, parents? }
//
// Composite trigger: when the caret is inside `!<num>/...` the kind narrows
// to `result` (one `/`) or `step_result` (two `/`); the popover uses the
// parent ids in `parents` to scope the search.
//
// Rules:
// - The trigger char must be preceded by whitespace or be the start of value
//   (so an email "alice@host" never triggers the user popover).
// - The query is the substring after the active segment up to the caret.
// - Backspacing past the trigger closes the popover.
export function detectActiveTrigger(value, caret) {
  if (!value || caret <= 0) return null
  for (let cursor = caret - 1; cursor >= 0; cursor -= 1) {
    const char = value[cursor]
    if (TRIGGER_KINDS[char]) {
      if (cursor > 0 && !/\s/.test(value[cursor - 1])) return null
      const body = value.slice(cursor + 1, caret)
      if (STOP_CHARS.test(body)) return null
      if (char === "!" && body.includes("/")) {
        return _detectExecutionComposite(cursor, caret, body)
      }
      return {
        kind: TRIGGER_KINDS[char],
        triggerChar: char,
        query: body,
        anchorIndex: cursor,
        caretIndex: caret,
      }
    }
    if (STOP_CHARS.test(char)) return null
  }
  return null
}

function _detectExecutionComposite(triggerIndex, caret, body) {
  const segments = body.split("/")
  if (segments.length > 3) return null
  for (let i = 0; i < segments.length - 1; i += 1) {
    if (!/^\d+$/.test(segments[i])) return null
  }
  const parents = segments.slice(0, -1).map(Number)
  const query = segments[segments.length - 1]
  const kind = parents.length === 1 ? "result" : "step_result"
  return {
    kind,
    triggerChar: "!",
    query,
    anchorIndex: triggerIndex,
    caretIndex: caret,
    parents,
  }
}

// Build the canonical token to insert when a hit is selected.
// User → `@slug`. Composite execution hits → `!exec/result[/step]`. Otherwise
// `<trigger><id>`.
export function buildCanonicalToken(triggerChar, hit) {
  if (triggerChar === "@" && hit.slug) {
    return `@${hit.slug}`
  }
  if ((hit.kind === "result" || hit.kind === "step_result") && hit.id != null && hit.sub_ids?.length) {
    return `!${hit.id}/${hit.sub_ids.join("/")}`
  }
  if (hit.id != null) {
    return `${triggerChar}${hit.id}`
  }
  return triggerChar
}

export function replaceRange(value, start, end, replacement) {
  return `${value.slice(0, start)}${replacement}${value.slice(end)}`
}
