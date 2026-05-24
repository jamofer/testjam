import { describe, it, expect } from "vitest"
import { fuzzyScore, fuzzyFilter } from "../lib/fuzzy"

describe("fuzzyScore", () => {
  it("returns 0 for an empty query", () => {
    expect(fuzzyScore("", "anything")).toBe(0)
  })

  it("returns null when the query is not a subsequence", () => {
    expect(fuzzyScore("xyz", "alpha beta")).toBeNull()
  })

  it("matches contiguous substrings with the highest score", () => {
    const contiguous = fuzzyScore("login", "Login broken")
    const scattered = fuzzyScore("lgn", "Login broken")

    expect(contiguous).not.toBeNull()
    expect(scattered).not.toBeNull()
    expect(contiguous).toBeGreaterThan(scattered)
  })

  it("rewards prefix matches over later substrings", () => {
    const prefix = fuzzyScore("plan", "Plan refresh")
    const middle = fuzzyScore("plan", "Test Plan refresh")

    expect(prefix).toBeGreaterThan(middle)
  })

  it("matches a subsequence on word boundaries", () => {
    const score = fuzzyScore("np", "New Project")

    expect(score).not.toBeNull()
    expect(score).toBeGreaterThan(0)
  })
})

describe("fuzzyFilter", () => {
  it("returns every item unchanged when the query is empty", () => {
    const items = [{ name: "alpha" }, { name: "beta" }]

    const result = fuzzyFilter("", items, item => item.name)

    expect(result).toEqual(items)
  })

  it("filters and sorts by match quality", () => {
    const items = [
      { name: "Test Plan refresh" },
      { name: "Plan refresh" },
      { name: "Versions" },
    ]

    const result = fuzzyFilter("plan", items, item => item.name)

    expect(result.map(item => item.name)).toEqual([
      "Plan refresh",
      "Test Plan refresh",
    ])
  })
})
