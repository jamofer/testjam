import { describe, it, expect } from "vitest"
import {
  buildCanonicalToken,
  detectActiveTrigger,
  replaceRange,
} from "../lib/mentions/triggerDetection"

describe("detectActiveTrigger", () => {
  it("activates on @ at start of input", () => {
    const result = detectActiveTrigger("@ali", 4)
    expect(result).toMatchObject({ kind: "user", query: "ali", triggerChar: "@" })
  })

  it("activates on @ after whitespace", () => {
    const result = detectActiveTrigger("hello @bo", 9)
    expect(result).toMatchObject({ kind: "user", query: "bo", anchorIndex: 6 })
  })

  it("does not activate when preceded by non-space", () => {
    expect(detectActiveTrigger("email@host", 10)).toBeNull()
  })

  it("activates on # for bugs", () => {
    const result = detectActiveTrigger("see #4", 6)
    expect(result).toMatchObject({ kind: "bug", query: "4" })
  })

  it("activates on ! for executions", () => {
    const result = detectActiveTrigger("run !17", 7)
    expect(result).toMatchObject({ kind: "execution", query: "17" })
  })

  it("activates on ~ for cases", () => {
    const result = detectActiveTrigger("covered ~91", 11)
    expect(result).toMatchObject({ kind: "case", query: "91" })
  })

  it("closes when caret moves past whitespace", () => {
    expect(detectActiveTrigger("@alice and ", 11)).toBeNull()
  })

  it("returns empty query when caret is right after trigger", () => {
    const result = detectActiveTrigger("ping @", 6)
    expect(result).toMatchObject({ kind: "user", query: "" })
  })
})

describe("detectActiveTrigger composite", () => {
  it("detects !N/ for results", () => {
    const result = detectActiveTrigger("see !17/", 8)
    expect(result).toMatchObject({
      kind: "result", parents: [17], query: "", triggerChar: "!",
    })
  })

  it("detects !N/M with partial query", () => {
    const result = detectActiveTrigger("see !17/91", 10)
    expect(result).toMatchObject({
      kind: "result", parents: [17], query: "91",
    })
  })

  it("detects !N/M/ for step results", () => {
    const result = detectActiveTrigger("step !17/91/", 12)
    expect(result).toMatchObject({
      kind: "step_result", parents: [17, 91], query: "",
    })
  })

  it("detects !N/M/K with partial step query", () => {
    const result = detectActiveTrigger("step !17/91/3", 13)
    expect(result).toMatchObject({
      kind: "step_result", parents: [17, 91], query: "3",
    })
  })

  it("rejects more than two slashes", () => {
    expect(detectActiveTrigger("!17/91/3/4", 10)).toBeNull()
  })
})

describe("buildCanonicalToken", () => {
  it("uses slug for users", () => {
    expect(buildCanonicalToken("@", { kind: "user", slug: "alice" })).toBe("@alice")
  })

  it("uses id for bugs", () => {
    expect(buildCanonicalToken("#", { kind: "bug", id: 42 })).toBe("#42")
  })

  it("uses id for executions", () => {
    expect(buildCanonicalToken("!", { kind: "execution", id: 17 })).toBe("!17")
  })

  it("builds composite for results", () => {
    expect(buildCanonicalToken("!", { kind: "result", id: 17, sub_ids: [91] })).toBe("!17/91")
  })

  it("builds composite for step results", () => {
    expect(buildCanonicalToken("!", { kind: "step_result", id: 17, sub_ids: [91, 3] })).toBe("!17/91/3")
  })
})

describe("replaceRange", () => {
  it("replaces a slice between indices", () => {
    expect(replaceRange("hello @al world", 6, 9, "@alice")).toBe("hello @alice world")
  })
})
