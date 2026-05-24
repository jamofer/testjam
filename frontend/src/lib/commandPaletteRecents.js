// localStorage-backed history for the command palette. Stores the last
// few navigation targets the user picked, so reopening the palette feels
// like cmd+K in Linear / Slack — the things they actually use float to
// the top instead of starting from a cold list every time.

const STORAGE_KEY = "testjam.command-palette.recents"
const MAX_RECENTS = 10


export function loadRecents() {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    if (!Array.isArray(parsed)) return []
    return parsed.filter(isRecentLike).slice(0, MAX_RECENTS)
  } catch {
    return []
  }
}


export function pushRecent(entry) {
  if (!isRecentLike(entry)) return loadRecents()
  const next = [entry, ...loadRecents().filter(existing => !sameEntry(existing, entry))]
    .slice(0, MAX_RECENTS)
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next))
  } catch {
    // localStorage may be full or disabled — silently fall back to
    // returning the in-memory list so callers keep working.
  }
  return next
}


export function clearRecents() {
  try {
    window.localStorage.removeItem(STORAGE_KEY)
  } catch {
    // intentional no-op
  }
}


function isRecentLike(entry) {
  return (
    entry
    && typeof entry === "object"
    && typeof entry.kind === "string"
    && typeof entry.title === "string"
    && typeof entry.url === "string"
  )
}


function sameEntry(a, b) {
  return a.kind === b.kind && a.url === b.url
}
