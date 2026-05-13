import { describe, it, expect } from "vitest"
import { scrubEvent } from "../lib/sentry"

describe("scrubEvent", () => {
  it("returns the event untouched when there is no request", () => {
    const event = { message: "boom" }

    expect(scrubEvent(event)).toEqual({ message: "boom" })
  })

  it("scrubs sensitive headers regardless of casing", () => {
    const event = {
      request: {
        headers: {
          Authorization: "Bearer hunter2",
          Cookie: "session=abc",
          "X-API-Key": "tj_secret",
          "Content-Type": "application/json",
        },
      },
    }

    const scrubbed = scrubEvent(event)

    expect(scrubbed.request.headers.Authorization).toBe("[scrubbed]")
    expect(scrubbed.request.headers.Cookie).toBe("[scrubbed]")
    expect(scrubbed.request.headers["X-API-Key"]).toBe("[scrubbed]")
    expect(scrubbed.request.headers["Content-Type"]).toBe("application/json")
  })

  it("scrubs password and token fields in the request body", () => {
    const event = {
      request: {
        data: {
          username: "alice",
          password: "hunter2",
          new_password: "hunter3",
          token: "reset-token",
          api_key: "tj_value",
        },
      },
    }

    const scrubbed = scrubEvent(event)

    expect(scrubbed.request.data.username).toBe("alice")
    expect(scrubbed.request.data.password).toBe("[scrubbed]")
    expect(scrubbed.request.data.new_password).toBe("[scrubbed]")
    expect(scrubbed.request.data.token).toBe("[scrubbed]")
    expect(scrubbed.request.data.api_key).toBe("[scrubbed]")
  })
})
