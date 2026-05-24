import { describe, it, expect } from "vitest"
import { effectiveExecutionStatus, executionStatusPill } from "../lib/executionStatus"


describe("effectiveExecutionStatus", () => {
  it("passes through aborted runs", () => {
    expect(effectiveExecutionStatus({ status: "aborted", passed: 5 })).toBe("aborted")
  })

  it("passes through in-progress runs", () => {
    expect(effectiveExecutionStatus({ status: "in_progress", passed: 1 })).toBe("in_progress")
  })

  it("passes through pending runs", () => {
    expect(effectiveExecutionStatus({ status: "pending" })).toBe("pending")
  })

  it("derives failed when completed run had at least one failure", () => {
    expect(effectiveExecutionStatus({
      status: "completed", passed: 9, failed: 1, blocked: 0, not_run: 0,
    })).toBe("failed")
  })

  it("derives blocked when completed run had blocked but no failures", () => {
    expect(effectiveExecutionStatus({
      status: "completed", passed: 5, failed: 0, blocked: 2, not_run: 0,
    })).toBe("blocked")
  })

  it("derives passed when completed run only has passed results", () => {
    expect(effectiveExecutionStatus({
      status: "completed", passed: 7, failed: 0, blocked: 0, not_run: 0,
    })).toBe("passed")
  })

  it("falls back to not_run when nothing has run", () => {
    expect(effectiveExecutionStatus({
      status: "completed", passed: 0, failed: 0, blocked: 0, not_run: 5,
    })).toBe("not_run")
  })

  it("returns not_run for an empty item without crashing", () => {
    expect(effectiveExecutionStatus(undefined)).toBe("not_run")
  })
})


describe("executionStatusPill", () => {
  it("reuses the shared STATUS_CONFIG pill for passed/failed/blocked/not_run", () => {
    expect(executionStatusPill("passed")).toContain("green")
    expect(executionStatusPill("failed")).toContain("red")
    expect(executionStatusPill("blocked")).toContain("yellow")
  })

  it("provides extra styles for aborted/in_progress/pending", () => {
    expect(executionStatusPill("aborted")).toContain("red")
    expect(executionStatusPill("in_progress")).toContain("blue")
    expect(executionStatusPill("pending")).toContain("gray")
  })
})
