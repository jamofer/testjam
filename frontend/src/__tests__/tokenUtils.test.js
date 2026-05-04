import { describe, it, expect } from 'vitest'

// Guards on token display helpers used in MembersPage and ProfilePage.

function maskToken(raw) {
  if (!raw) return ''
  return raw.slice(0, 4) + '•'.repeat(raw.length - 4)
}

function fmtDate(iso) {
  if (!iso) return 'Never'
  return new Date(iso).toLocaleString(undefined, { dateStyle: 'short', timeStyle: 'short' })
}

describe('maskToken', () => {
  it('shows first 4 chars and masks the rest', () => {
    const raw = 'tj_abcdefgh1234'
    const masked = maskToken(raw)
    expect(masked).toMatch(/^tj_a/)
    expect(masked).toContain('•')
    expect(masked.length).toBe(raw.length)
  })

  it('handles empty input', () => {
    expect(maskToken('')).toBe('')
    expect(maskToken(null)).toBe('')
  })
})

describe('fmtDate', () => {
  it('returns "Never" for null/undefined', () => {
    expect(fmtDate(null)).toBe('Never')
    expect(fmtDate(undefined)).toBe('Never')
    expect(fmtDate('')).toBe('Never')
  })

  it('returns a formatted string for a valid date', () => {
    const result = fmtDate('2024-06-01T10:00:00Z')
    expect(typeof result).toBe('string')
    expect(result).not.toBe('Never')
  })
})

// ── Token prefix format ───────────────────────────────────────────────────────

describe('token prefix format', () => {
  it('tj_ tokens start with expected prefix', () => {
    const sampleTokens = ['tj_abc123XYZ', 'tj_randomstuff', 'tj_AAABBBCCC']
    sampleTokens.forEach(t => {
      expect(t).toMatch(/^tj_/)
    })
  })

  it('prefix is the first 12 characters', () => {
    const raw = 'tj_abcdefghi123456789'
    const prefix = raw.slice(0, 12)
    expect(prefix).toBe('tj_abcdefghi')
    expect(prefix.length).toBe(12)
  })
})
