export function fmtDuration(ms) {
  if (ms == null) return null
  if (ms < 1000) return `${ms}ms`
  if (ms < 60000) return `${(ms / 1000).toFixed(2)}s`
  const m = Math.floor(ms / 60000)
  const s = ((ms % 60000) / 1000).toFixed(0)
  return `${m}m ${s}s`
}

export function fmtTime(iso) {
  if (!iso) return null
  return new Date(iso).toLocaleTimeString(undefined, {
    hour: "2-digit", minute: "2-digit", second: "2-digit",
  })
}

export function fmtDate(iso) {
  if (!iso) return null
  return new Date(iso).toLocaleString(undefined, { dateStyle: "short", timeStyle: "short" })
}
