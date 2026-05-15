export function fmtDuration(ms) {
  if (ms == null) return null
  if (ms < 1000) return `${ms}ms`
  if (ms < 60000) return `${(ms / 1000).toFixed(2)}s`
  const m = Math.floor(ms / 60000)
  const s = ((ms % 60000) / 1000).toFixed(0)
  return `${m}m ${s}s`
}

export function fmtTime(iso, timezone) {
  if (!iso) return null
  return new Date(iso).toLocaleTimeString(undefined, {
    hour: "2-digit", minute: "2-digit", second: "2-digit",
    timeZone: timezone || undefined,
  })
}

export function fmtDate(iso, timezone) {
  if (!iso) return null
  return new Date(iso).toLocaleString(undefined, {
    dateStyle: "short", timeStyle: "short",
    timeZone: timezone || undefined,
  })
}

export function fmtDateTime(iso, timezone) {
  if (!iso) return null
  return new Date(iso).toLocaleString(undefined, {
    dateStyle: "short", timeStyle: "medium",
    timeZone: timezone || undefined,
  })
}

const RELATIVE_THRESHOLDS = [
  { limit: 60, divisor: 1, unit: "second" },
  { limit: 3600, divisor: 60, unit: "minute" },
  { limit: 86400, divisor: 3600, unit: "hour" },
  { limit: 2592000, divisor: 86400, unit: "day" },
  { limit: 31536000, divisor: 2592000, unit: "month" },
]

export function fmtRelative(iso, now = new Date()) {
  if (!iso) return null
  const date = new Date(iso)
  const seconds = (date.getTime() - now.getTime()) / 1000
  const absSeconds = Math.abs(seconds)
  const formatter = new Intl.RelativeTimeFormat(undefined, { numeric: "auto" })
  for (const { limit, divisor, unit } of RELATIVE_THRESHOLDS) {
    if (absSeconds < limit) {
      return formatter.format(Math.round(seconds / divisor), unit)
    }
  }
  return formatter.format(Math.round(seconds / 31536000), "year")
}

export function browserTimezone() {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || null
  } catch {
    return null
  }
}
