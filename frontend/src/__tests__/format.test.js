import { describe, it, expect } from "vitest"
import { fmtDuration, fmtTime, fmtDate, fmtRelative, browserTimezone } from "../lib/format"

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

  it("respects an explicit timezone argument", () => {
    const inTokyo = fmtDate("2024-06-01T10:00:00Z", "Asia/Tokyo")
    const inNewYork = fmtDate("2024-06-01T10:00:00Z", "America/New_York")
    expect(inTokyo).not.toBe(inNewYork)
  })
})

describe("fmtRelative", () => {
  it("returns null for falsy input", () => {
    expect(fmtRelative(null)).toBeNull()
  })

  it("formats minutes ago", () => {
    const now = new Date("2024-06-01T12:00:00Z")
    const fiveMinutesAgo = "2024-06-01T11:55:00Z"
    const result = fmtRelative(fiveMinutesAgo, now)
    expect(result).toMatch(/5 minutes ago|5 min/)
  })

  it("formats days ago", () => {
    const now = new Date("2024-06-10T12:00:00Z")
    const threeDaysAgo = "2024-06-07T12:00:00Z"
    expect(fmtRelative(threeDaysAgo, now)).toMatch(/3 days ago|3 d/)
  })
})

describe("browserTimezone", () => {
  it("returns a non-empty IANA-like string", () => {
    const tz = browserTimezone()
    expect(typeof tz).toBe("string")
    expect(tz.length).toBeGreaterThan(0)
  })
})
