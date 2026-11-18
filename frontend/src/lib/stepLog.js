// Parses the text kept in a step result's `log_output` into entries.
//
// Current lines read `2026-11-18T09:15:02.123Z [INFO] message`. Older rows
// carry `**[INFO]** message` (no timestamp) or the listener's old batch format
// `2026-11-18 09:15:02.123 [INFO] message`; all three parse the same way. A
// line that does not start an entry continues the previous one, so multi-line
// messages (tracebacks, JSON) stay together.

const ENTRY_RE = /^(?:(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?) )?\*{0,2}\[([A-Z]+)\]\*{0,2} ?(.*)$/

export function parseStepLog(text) {
  if (!text) return []
  const entries = []
  for (const line of text.split("\n")) {
    const match = ENTRY_RE.exec(line)
    if (match) {
      entries.push({ ts: match[1] ? match[1].replace(" ", "T") : null, level: match[2], message: match[3] })
    } else if (entries.length > 0) {
      entries[entries.length - 1].message += `\n${line}`
    } else {
      entries.push({ ts: null, level: null, message: line })
    }
  }
  return entries
    .map(entry => ({ ...entry, message: entry.message.replace(/\s+$/, "") }))
    .filter(entry => entry.level || entry.message)
}

export function formatStepLogLine(level, message, ts) {
  const date = ts ? new Date(ts) : null
  const stamp = date && !Number.isNaN(date.getTime()) ? `${date.toISOString()} ` : ""
  return `${stamp}[${level}] ${message}`
}

export function fmtLogTime(ts, locale) {
  const date = new Date(ts)
  if (Number.isNaN(date.getTime())) return ts
  return date.toLocaleTimeString(locale || undefined, {
    hour: "2-digit", minute: "2-digit", second: "2-digit", fractionalSecondDigits: 3, hour12: false,
  })
}

export function fmtLogDateTime(ts, locale) {
  const date = new Date(ts)
  if (Number.isNaN(date.getTime())) return ts
  return date.toLocaleString(locale || undefined, {
    dateStyle: "medium", timeStyle: "medium",
  })
}

export const LOG_LEVEL_CLASS = {
  FAIL: "text-red-400",
  ERROR: "text-red-400",
  WARN: "text-amber-300",
  DEBUG: "text-gray-500",
  TRACE: "text-gray-500",
}
