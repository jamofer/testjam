import { describe, it, expect } from "vitest"
import { lineDiff } from "../lib/diff"

describe("lineDiff", () => {
  it("returns all eq when strings match", () => {
    expect(lineDiff("a\nb", "a\nb")).toEqual([
      { type: "eq", text: "a" },
      { type: "eq", text: "b" },
    ])
  })

  it("marks deletions and additions", () => {
    const out = lineDiff("a\nb\nc", "a\nx\nc")
    expect(out).toContainEqual({ type: "del", text: "b" })
    expect(out).toContainEqual({ type: "add", text: "x" })
    expect(out.find(d => d.text === "a").type).toBe("eq")
    expect(out.find(d => d.text === "c").type).toBe("eq")
  })

  it("handles pure additions", () => {
    expect(lineDiff("", "a\nb")).toEqual([
      { type: "del", text: "" },
      { type: "add", text: "a" },
      { type: "add", text: "b" },
    ])
  })

  it("handles null inputs as empty", () => {
    expect(lineDiff(null, "x")).toEqual([
      { type: "del", text: "" },
      { type: "add", text: "x" },
    ])
  })
})
