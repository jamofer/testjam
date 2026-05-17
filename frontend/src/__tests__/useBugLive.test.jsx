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
import { useBugLive } from "../hooks/useBugLive"

const wrap = (client) => ({ children }) => (
  <QueryClientProvider client={client}>{children}</QueryClientProvider>
)

describe("useBugLive", () => {
  it("appends a new comment to the comments cache", () => {
    const client = new QueryClient()
    client.setQueryData(["bug-comments", 42], [])

    renderHook(() => useBugLive(42), { wrapper: wrap(client) })

    act(() => {
      handlersRef.current["bug.comment.added"]({
        id: 1, bug_id: 42, body: "Repro on staging",
      })
    })

    expect(client.getQueryData(["bug-comments", 42])).toEqual([
      { id: 1, bug_id: 42, body: "Repro on staging" },
    ])
  })

  it("removes a deleted comment", () => {
    const client = new QueryClient()
    client.setQueryData(["bug-comments", 42], [
      { id: 1, bug_id: 42, body: "First" },
      { id: 2, bug_id: 42, body: "Second" },
    ])

    renderHook(() => useBugLive(42), { wrapper: wrap(client) })

    act(() => {
      handlersRef.current["bug.comment.deleted"]({ id: 1 })
    })

    expect(client.getQueryData(["bug-comments", 42])).toEqual([
      { id: 2, bug_id: 42, body: "Second" },
    ])
  })

  it("appends activity entries", () => {
    const client = new QueryClient()
    client.setQueryData(["bug-activity", 42], [])

    renderHook(() => useBugLive(42), { wrapper: wrap(client) })

    act(() => {
      handlersRef.current["bug.activity.added"]({
        id: 7, bug_id: 42, field: "status", from_value: "open", to_value: "resolved",
      })
    })

    expect(client.getQueryData(["bug-activity", 42])).toHaveLength(1)
  })
})
