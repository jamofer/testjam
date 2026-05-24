import { describe, it, expect, vi, beforeEach, afterEach } from "vitest"
import { renderHook } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"

import { useStorageAuthSync } from "../hooks/useAuth"


function setup() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  const clearSpy = vi.spyOn(queryClient, "clear")
  const wrapper = ({ children }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
  renderHook(() => useStorageAuthSync(), { wrapper })
  return { clearSpy }
}


function fireStorageEvent({ key, newValue }) {
  const event = new StorageEvent("storage", {
    key,
    newValue,
    oldValue: "previous",
    storageArea: window.localStorage,
  })
  window.dispatchEvent(event)
}


describe("useStorageAuthSync", () => {
  const originalHref = window.location.href

  beforeEach(() => {
    delete window.location
    window.location = { href: originalHref }
  })

  afterEach(() => {
    delete window.location
    window.location = { href: originalHref }
  })

  it("clears the query cache and redirects to /login when the token is removed in another tab", () => {
    const { clearSpy } = setup()

    fireStorageEvent({ key: "token", newValue: null })

    expect(clearSpy).toHaveBeenCalled()
    expect(window.location.href).toBe("/login")
  })

  it("ignores storage events for unrelated keys", () => {
    const { clearSpy } = setup()

    fireStorageEvent({ key: "theme", newValue: null })

    expect(clearSpy).not.toHaveBeenCalled()
    expect(window.location.href).toBe(originalHref)
  })

  it("ignores storage events that set a new token value (login in another tab)", () => {
    const { clearSpy } = setup()

    fireStorageEvent({ key: "token", newValue: "fresh-token" })

    expect(clearSpy).not.toHaveBeenCalled()
    expect(window.location.href).toBe(originalHref)
  })
})
