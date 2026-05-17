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
})

describe("replaceRange", () => {
  it("replaces a slice between indices", () => {
    expect(replaceRange("hello @al world", 6, 9, "@alice")).toBe("hello @alice world")
  })
})
