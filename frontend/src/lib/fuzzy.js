// Lightweight subsequence fuzzy match scoring, in the spirit of fzf/Quick
// Open. Returns null when the query characters don't appear in `target`
// in order. Higher score = better match. The scoring rules are:
//
//   * Exact substring beats everything else.
//   * Prefix matches beat subsequence matches.
//   * Within a subsequence, consecutive matches and word-boundary hits
//     are rewarded (so "np" matches "New Project" highly because both
//     letters land on word starts).
//
// Pure function, no dep — keeps the bundle the same size that pulling in
// fuse.js would have added.

const SUBSTRING_SCORE = 1000
const PREFIX_BONUS = 500
const WORD_BOUNDARY_BONUS = 50
const CONSECUTIVE_BONUS = 30

export function fuzzyScore(query, target) {
  if (!query) return 0
  if (!target) return null
  const q = query.toLowerCase()
  const t = target.toLowerCase()

  const directIndex = t.indexOf(q)
  if (directIndex !== -1) {
    return SUBSTRING_SCORE + (directIndex === 0 ? PREFIX_BONUS : 0) - directIndex
  }

  let score = 0
  let queryCursor = 0
  let previousMatchIndex = -2
  for (let i = 0; i < t.length && queryCursor < q.length; i++) {
    if (t[i] !== q[queryCursor]) continue
    if (i === previousMatchIndex + 1) score += CONSECUTIVE_BONUS
    if (i === 0 || /\W|_/.test(t[i - 1])) score += WORD_BOUNDARY_BONUS
    previousMatchIndex = i
    queryCursor++
  }
  if (queryCursor < q.length) return null
  return score - (t.length - q.length)
}

export function fuzzyFilter(query, items, accessor) {
  if (!query) return items
  const scored = []
  for (const item of items) {
    const score = fuzzyScore(query, accessor(item))
    if (score !== null) scored.push({ item, score })
  }
  scored.sort((a, b) => b.score - a.score)
  return scored.map(entry => entry.item)
}
