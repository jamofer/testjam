import { describe, it, expect, vi } from "vitest"
import { act, renderHook } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"

vi.mock("../hooks/useTopicSocket", () => {
  const handlers = { current: null }
  return {
    handlersRef: handlers,
    useTopicSocket: (topics, h) => {
      handlers.current = h
      return { connected: true }
    },
  }
})

import { handlersRef } from "../hooks/useTopicSocket"
import { useProjectBugsLive } from "../hooks/useProjectBugsLive"

function wrapperWith(client) {
  return ({ children }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  )
}

describe("useProjectBugsLive", () => {
  it("inserts a newly created bug at the top of the cache", () => {
    const client = new QueryClient()
    client.setQueryData(["bugs", "5", {}], [
      { id: 10, number: 1, title: "First", severity: "low", status: "open" },
    ])

    renderHook(() => useProjectBugsLive("5"), { wrapper: wrapperWith(client) })

    act(() => {
      handlersRef.current["bug.created"]({
        id: 20,
        number: 2,
        title: "Fresh crash",
        severity: "critical",
        status: "open",
      })
    })

    const rows = client.getQueryData(["bugs", "5", {}])
    expect(rows).toHaveLength(2)
    expect(rows[0].title).toBe("Fresh crash")
  })

  it("removes a deleted bug from every list cache", () => {
    const client = new QueryClient()
    client.setQueryData(["bugs", "5", {}], [
      { id: 10, number: 1, title: "First" },
      { id: 11, number: 2, title: "Second" },
    ])
    client.setQueryData(["bug", 10], { id: 10, number: 1, title: "First" })

    renderHook(() => useProjectBugsLive("5"), { wrapper: wrapperWith(client) })

    act(() => {
      handlersRef.current["bug.deleted"]({ id: 10 })
    })

    expect(client.getQueryData(["bugs", "5", {}])).toEqual([
      { id: 11, number: 2, title: "Second" },
    ])
    expect(client.getQueryData(["bug", 10])).toBeUndefined()
  })

  it("merges status_changed updates and invalidates activity", () => {
    const client = new QueryClient()
    client.setQueryData(["bugs", "5", {}], [
      { id: 10, number: 1, status: "open" },
    ])
    client.setQueryData(["bug", 10], { id: 10, status: "open" })
    const invalidateSpy = vi.spyOn(client, "invalidateQueries")

    renderHook(() => useProjectBugsLive("5"), { wrapper: wrapperWith(client) })

    act(() => {
      handlersRef.current["bug.status_changed"]({ id: 10, status: "resolved" })
    })

    expect(client.getQueryData(["bug", 10]).status).toBe("resolved")
    expect(client.getQueryData(["bugs", "5", {}])[0].status).toBe("resolved")
    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ["bug-activity", 10] })
  })
})
