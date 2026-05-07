/**
 * Minimal line-level diff (Myers-lite, good enough for short prose fields).
 * Returns an array of { type: "eq" | "add" | "del", text }.
 */
export function lineDiff(before, after) {
  const a = (before ?? "").split("\n")
  const b = (after ?? "").split("\n")
  const n = a.length
  const m = b.length

  // Build LCS table.
  const lcs = Array.from({ length: n + 1 }, () => new Int32Array(m + 1))
  for (let i = n - 1; i >= 0; i--) {
    for (let j = m - 1; j >= 0; j--) {
      lcs[i][j] = a[i] === b[j]
        ? lcs[i + 1][j + 1] + 1
        : Math.max(lcs[i + 1][j], lcs[i][j + 1])
    }
  }

  const out = []
  let i = 0, j = 0
  while (i < n && j < m) {
    if (a[i] === b[j]) {
      out.push({ type: "eq", text: a[i] })
      i++; j++
    } else if (lcs[i + 1][j] >= lcs[i][j + 1]) {
      out.push({ type: "del", text: a[i] })
      i++
    } else {
      out.push({ type: "add", text: b[j] })
      j++
    }
  }
  while (i < n) { out.push({ type: "del", text: a[i++] }) }
  while (j < m) { out.push({ type: "add", text: b[j++] }) }
  return out
}
