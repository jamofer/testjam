import { describe, it, expect } from "vitest"
import { STATUS_KEYS, STATUS_CONFIG, statusLabel } from "../lib/statusConfig"

describe("STATUS_KEYS", () => {
  it("contains exactly the four canonical statuses", () => {
    expect(STATUS_KEYS).toEqual(["passed", "failed", "blocked", "not_run"])
  })
})

describe("STATUS_CONFIG", () => {
  it("has an entry for every key in STATUS_KEYS", () => {
    for (const key of STATUS_KEYS) {
      expect(STATUS_CONFIG[key]).toBeDefined()
    }
  })

  it("each entry has the full UI shape", () => {
    for (const key of STATUS_KEYS) {
      const cfg = STATUS_CONFIG[key]
      expect(cfg.label).toBeTruthy()
      expect(cfg.icon).toBeTruthy()  // lucide-react icon component (forwardRef object)
      expect(cfg.badgeVariant).toBeTruthy()
      expect(cfg.iconColor).toMatch(/^text-/)
      expect(cfg.bg).toMatch(/^bg-/)
      expect(cfg.pill).toMatch(/bg-/)
    }
  })

  it("pass and fail use distinct colour families", () => {
    expect(STATUS_CONFIG.passed.iconColor).toContain("green")
    expect(STATUS_CONFIG.failed.iconColor).toContain("red")
    expect(STATUS_CONFIG.blocked.iconColor).toContain("yellow")
    expect(STATUS_CONFIG.not_run.iconColor).toContain("gray")
  })
})

describe("statusLabel", () => {
  it("returns the human-readable label", () => {
    expect(statusLabel("passed")).toBe("Pass")
    expect(statusLabel("failed")).toBe("Fail")
    expect(statusLabel("blocked")).toBe("Blocked")
    expect(statusLabel("not_run")).toBe("Not run")
  })

  it("falls back to the raw key for unknown statuses", () => {
    expect(statusLabel("weird")).toBe("weird")
  })
})
