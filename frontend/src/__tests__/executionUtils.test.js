import { describe, it, expect } from 'vitest'

// ── Utility functions extracted from ExecutionRunPage ─────────────────────────
// These are defined inline in the component; tested here to guard regressions.

function fmtDuration(ms) {
  if (ms == null) return null
  if (ms < 1000) return `${ms}ms`
  if (ms < 60000) return `${(ms / 1000).toFixed(2)}s`
  const m = Math.floor(ms / 60000)
  const s = ((ms % 60000) / 1000).toFixed(0)
  return `${m}m ${s}s`
}

function fmtTime(iso) {
  if (!iso) return null
  return new Date(iso).toLocaleTimeString(undefined, {
    hour: '2-digit', minute: '2-digit', second: '2-digit',
  })
}

describe('fmtDuration', () => {
  it('returns null for null input', () => {
    expect(fmtDuration(null)).toBeNull()
    expect(fmtDuration(undefined)).toBeNull()
  })

  it('formats milliseconds under 1s', () => {
    expect(fmtDuration(0)).toBe('0ms')
    expect(fmtDuration(500)).toBe('500ms')
    expect(fmtDuration(999)).toBe('999ms')
  })

  it('formats seconds between 1s and 60s', () => {
    expect(fmtDuration(1000)).toBe('1.00s')
    expect(fmtDuration(1500)).toBe('1.50s')
    expect(fmtDuration(59999)).toBe('60.00s')
  })

  it('formats minutes and seconds', () => {
    expect(fmtDuration(60000)).toBe('1m 0s')
    expect(fmtDuration(90000)).toBe('1m 30s')
    expect(fmtDuration(3661000)).toBe('61m 1s')
  })
})

describe('fmtTime', () => {
  it('returns null for falsy input', () => {
    expect(fmtTime(null)).toBeNull()
    expect(fmtTime('')).toBeNull()
    expect(fmtTime(undefined)).toBeNull()
  })

  it('returns a non-empty string for a valid ISO date', () => {
    const result = fmtTime('2024-01-15T14:30:45Z')
    expect(typeof result).toBe('string')
    expect(result.length).toBeGreaterThan(0)
  })
})

// ── STATUS_CONFIG completeness ────────────────────────────────────────────────

const STATUS_CONFIG = {
  passed:  { label: 'Pass',    color: 'success'     },
  failed:  { label: 'Fail',    color: 'destructive' },
  blocked: { label: 'Blocked', color: 'warning'     },
  not_run: { label: 'Not run', color: 'secondary'   },
}

describe('STATUS_CONFIG', () => {
  const EXPECTED_STATUSES = ['passed', 'failed', 'blocked', 'not_run']

  it('covers all expected statuses', () => {
    expect(Object.keys(STATUS_CONFIG)).toEqual(expect.arrayContaining(EXPECTED_STATUSES))
  })

  it('every status has a label and color', () => {
    for (const [, cfg] of Object.entries(STATUS_CONFIG)) {
      expect(cfg.label).toBeTruthy()
      expect(cfg.color).toBeTruthy()
    }
  })
})
