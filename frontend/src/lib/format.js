export function fmtDuration(ms) {
  if (ms == null) return null
  if (ms < 1000) return `${ms}ms`
  if (ms < 60000) return `${(ms / 1000).toFixed(2)}s`
  const m = Math.floor(ms / 60000)
  const s = ((ms % 60000) / 1000).toFixed(0)
  return `${m}m ${s}s`
}

export function fmtTime(iso, timezone, locale) {
  if (!iso) return null
  return new Date(iso).toLocaleTimeString(locale || undefined, {
    hour: "2-digit", minute: "2-digit", second: "2-digit",
    timeZone: timezone || undefined,
  })
}

export function fmtDate(iso, timezone, locale) {
  if (!iso) return null
  return new Date(iso).toLocaleString(locale || undefined, {
    dateStyle: "short", timeStyle: "short",
    timeZone: timezone || undefined,
  })
}

export function fmtDateTime(iso, timezone, locale) {
  if (!iso) return null
  return new Date(iso).toLocaleString(locale || undefined, {
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

export function fmtRelative(iso, now = new Date(), locale) {
  if (!iso) return null
  const date = new Date(iso)
  const seconds = (date.getTime() - now.getTime()) / 1000
  const absSeconds = Math.abs(seconds)
  const formatter = new Intl.RelativeTimeFormat(locale || undefined, { numeric: "auto" })
  for (const { limit, divisor, unit } of RELATIVE_THRESHOLDS) {
    if (absSeconds < limit) {
      return formatter.format(Math.round(seconds / divisor), unit)
    }
  }
  return formatter.format(Math.round(seconds / 31536000), "year")
}

const BYTE_UNITS = ["B", "KB", "MB", "GB", "TB"]

export function fmtBytes(bytes) {
  if (bytes == null) return null
  if (bytes === 0) return "0 B"
  const index = Math.min(Math.floor(Math.log10(bytes) / 3), BYTE_UNITS.length - 1)
  const value = bytes / 1000 ** index
  const precision = value >= 100 || index === 0 ? 0 : 1
  return `${value.toFixed(precision)} ${BYTE_UNITS[index]}`
}

export function browserTimezone() {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || null
  } catch {
    return null
  }
}
