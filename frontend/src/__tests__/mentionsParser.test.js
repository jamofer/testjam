import { describe, it, expect } from "vitest"
import { parse, usernames } from "../lib/mentions/parser"

describe("mentions parser", () => {
  it("matches @user", () => {
    expect(parse("hey @alice")).toEqual([
      expect.objectContaining({ kind: "user", slug: "alice", raw: "@alice" }),
    ])
  })

  it("ignores email-like @", () => {
    expect(parse("contact admin@example.com")).toEqual([])
  })

  it("matches #bug", () => {
    const [token] = parse("duplicate of #42")
    expect(token).toMatchObject({ kind: "bug", id: 42 })
  })

  it("matches !execution", () => {
    const [token] = parse("see !17")
    expect(token).toMatchObject({ kind: "execution", id: 17 })
  })

  it("matches !run/result", () => {
    const [token] = parse("failed in !17/91")
    expect(token).toMatchObject({ kind: "result", id: 17, sub_ids: [91] })
  })

  it("matches !run/result/step", () => {
    const [token] = parse("step diff !17/91/3")
    expect(token).toMatchObject({
      kind: "step_result", id: 17, sub_ids: [91, 3],
    })
  })

  it("matches ~case", () => {
    const [token] = parse("covered by ~91")
    expect(token).toMatchObject({ kind: "case", id: 91 })
  })

  it("ignores tokens inside fenced code", () => {
    const result = parse("@alice\n```\n#42 here\n```\n@bob")
    expect(result.map(t => t.slug)).toEqual(["alice", "bob"])
    expect(result.find(t => t.kind === "bug")).toBeUndefined()
  })

  it("ignores tokens inside inline code", () => {
    const result = parse("`@admin` then @alice")
    expect(result.map(t => t.slug)).toEqual(["alice"])
  })

  it("dedupes repeated tokens", () => {
    const result = parse("@alice @alice #42 #42")
    expect(result).toHaveLength(2)
  })

  it("ignores markdown heading hash", () => {
    const result = parse("# Title\nbody #42")
    expect(result).toEqual([expect.objectContaining({ kind: "bug", id: 42 })])
  })

  it("usernames helper", () => {
    expect(usernames("ping @alice and @bob_92")).toEqual(["alice", "bob_92"])
  })
})
