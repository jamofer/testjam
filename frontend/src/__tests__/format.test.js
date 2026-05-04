import { describe, it, expect } from "vitest"
import { fmtDuration, fmtTime, fmtDate } from "../lib/format"

describe("fmtDuration", () => {
  it("returns null for null/undefined input", () => {
    expect(fmtDuration(null)).toBeNull()
    expect(fmtDuration(undefined)).toBeNull()
  })

  it("formats milliseconds under 1s", () => {
    expect(fmtDuration(0)).toBe("0ms")
    expect(fmtDuration(500)).toBe("500ms")
    expect(fmtDuration(999)).toBe("999ms")
  })

  it("formats seconds between 1s and 60s", () => {
    expect(fmtDuration(1000)).toBe("1.00s")
    expect(fmtDuration(1500)).toBe("1.50s")
    expect(fmtDuration(59999)).toBe("60.00s")
  })

  it("formats minutes and seconds", () => {
    expect(fmtDuration(60000)).toBe("1m 0s")
    expect(fmtDuration(90000)).toBe("1m 30s")
    expect(fmtDuration(3661000)).toBe("61m 1s")
  })
})

describe("fmtTime", () => {
  it("returns null for falsy input", () => {
    expect(fmtTime(null)).toBeNull()
    expect(fmtTime("")).toBeNull()
    expect(fmtTime(undefined)).toBeNull()
  })

  it("returns a non-empty string for a valid ISO date", () => {
    const result = fmtTime("2024-01-15T14:30:45Z")
    expect(typeof result).toBe("string")
    expect(result.length).toBeGreaterThan(0)
  })
})

describe("fmtDate", () => {
  it("returns null for null/undefined input", () => {
    expect(fmtDate(null)).toBeNull()
    expect(fmtDate(undefined)).toBeNull()
  })

  it("returns a formatted string for a valid ISO date", () => {
    const result = fmtDate("2024-06-01T10:00:00Z")
    expect(typeof result).toBe("string")
    expect(result.length).toBeGreaterThan(0)
  })
})
