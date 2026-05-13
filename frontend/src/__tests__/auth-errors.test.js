import { describe, it, expect } from "vitest"
import { loginErrorMessage } from "../lib/auth-errors"

const lockoutError = (retryAfter) => ({
  response: {
    status: 423,
    headers: retryAfter !== undefined ? { "retry-after": String(retryAfter) } : {},
  },
})

describe("loginErrorMessage", () => {
  it("returns generic message on bad credentials", () => {
    const error = { response: { status: 401, headers: {} } }

    expect(loginErrorMessage(error)).toBe("Invalid credentials")
  })

  it("flags rate limit on 429", () => {
    const error = { response: { status: 429, headers: {} } }

    const message = loginErrorMessage(error)

    expect(message).toMatch(/too many login attempts/i)
  })

  it("formats sub-minute retry as seconds", () => {
    const message = loginErrorMessage(lockoutError(45))

    expect(message).toMatch(/account locked/i)
    expect(message).toMatch(/45 seconds/)
  })

  it("rounds up multi-minute retry to whole minutes", () => {
    const message = loginErrorMessage(lockoutError(125))

    expect(message).toMatch(/3 minutes/)
  })

  it("uses singular for exactly one minute when rounded", () => {
    const message = loginErrorMessage(lockoutError(60))

    expect(message).toMatch(/1 minute\b/)
  })

  it("falls back to a few moments when retry header is missing", () => {
    const message = loginErrorMessage(lockoutError())

    expect(message).toMatch(/a few moments/)
  })

  it("handles unknown errors safely", () => {
    expect(loginErrorMessage(null)).toBe("Invalid credentials")
    expect(loginErrorMessage(undefined)).toBe("Invalid credentials")
    expect(loginErrorMessage({})).toBe("Invalid credentials")
  })
})
