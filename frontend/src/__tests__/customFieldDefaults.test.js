import { describe, it, expect } from "vitest"
import { coerceDefault } from "../lib/customFieldDefaults"

describe("coerceDefault bool", () => {
  it.each(["true", "True", "TRUE", "  true  ", "1", "yes", "y", "on", "sí", "Si", "S"])(
    "treats %p as true", input => {
      expect(coerceDefault("bool", input)).toBe(true)
    },
  )

  it.each(["false", "False", "FALSE", "0", "no", "N", "off", "  no  "])(
    "treats %p as false", input => {
      expect(coerceDefault("bool", input)).toBe(false)
    },
  )

  it("treats anything unrecognized as false", () => {
    expect(coerceDefault("bool", "maybe")).toBe(false)
    expect(coerceDefault("bool", "")).toBe(false)
  })
})

describe("coerceDefault multi_select", () => {
  it("splits on the pipe character so commas inside values survive", () => {
    expect(coerceDefault("multi_select", "web, mobile|api|desktop"))
      .toEqual(["web, mobile", "api", "desktop"])
  })

  it("trims whitespace and drops empty segments", () => {
    expect(coerceDefault("multi_select", " p0 |  | p1 "))
      .toEqual(["p0", "p1"])
  })

  it("returns a single-element array for a value without separators", () => {
    expect(coerceDefault("multi_select", "p0")).toEqual(["p0"])
  })
})

describe("coerceDefault other types", () => {
  it("parses number defaults", () => {
    expect(coerceDefault("number", "42")).toBe(42)
  })

  it("returns text defaults verbatim", () => {
    expect(coerceDefault("text", "anything"))
      .toBe("anything")
  })
})
