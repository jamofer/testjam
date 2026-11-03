import { describe, it, expect, vi, beforeEach } from "vitest"
import { toast } from "sonner"

import { apiErrorMessage, toastApiError } from "../lib/apiError"

vi.mock("sonner", () => ({ toast: { error: vi.fn() } }))

const FALLBACK = "Could not save"

beforeEach(() => vi.clearAllMocks())

describe("apiErrorMessage", () => {
  it("returns a string detail as is", () => {
    expect(apiErrorMessage(apiError("Name already taken"), FALLBACK)).toBe("Name already taken")
  })

  it("joins the messages of a validation error list", () => {
    const detail = [{ msg: "field required" }, { msg: "value too long" }]

    expect(apiErrorMessage(apiError(detail), FALLBACK)).toBe("field required; value too long")
  })

  it("uses the message of an object detail", () => {
    const detail = { message: "User owns projects", owned_projects: [] }

    expect(apiErrorMessage(apiError(detail), FALLBACK)).toBe("User owns projects")
  })

  it("falls back when the detail is not readable", () => {
    expect(apiErrorMessage(apiError({ code: "expired" }), FALLBACK)).toBe(FALLBACK)
  })

  it("falls back when the request never got a response", () => {
    expect(apiErrorMessage(new Error("timeout of 30000ms exceeded"), FALLBACK)).toBe(FALLBACK)
  })
})

describe("toastApiError", () => {
  it("reuses the toast of an error already reported", () => {
    const error = apiError(undefined)

    toastApiError(error, "Something went wrong")
    toastApiError(error, FALLBACK)

    const [first, second] = toast.error.mock.calls
    expect(second[0]).toBe(FALLBACK)
    expect(second[1].id).toBe(first[1].id)
  })

  it("gives different errors their own toast", () => {
    toastApiError(apiError("first"), FALLBACK)
    toastApiError(apiError("second"), FALLBACK)

    const [first, second] = toast.error.mock.calls
    expect(second[1].id).not.toBe(first[1].id)
  })

  it("lets the caller wrap the message", () => {
    toastApiError(apiError("bad xml"), FALLBACK, message => `Import failed: ${message}`)

    expect(toast.error.mock.calls[0][0]).toBe("Import failed: bad xml")
  })
})

function apiError(detail) {
  return { response: { data: { detail } } }
}
