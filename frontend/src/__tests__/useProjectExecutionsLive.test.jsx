import { afterEach, beforeEach, describe, expect, it } from "vitest"
import { renderHook, act } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { useProjectExecutionsLive } from "../hooks/useProjectExecutionsLive"

const OriginalWebSocket = global.WebSocket
let sockets = []

class FakeWebSocket {
  static CONNECTING = 0
  static OPEN = 1
  static CLOSED = 3

  constructor(url) {
    this.url = url
    this.readyState = FakeWebSocket.CONNECTING
    sockets.push(this)
  }
  send() {}
  close() { this.readyState = FakeWebSocket.CLOSED; this.onclose?.() }
  addEventListener() {}
  open() { this.readyState = FakeWebSocket.OPEN; this.onopen?.() }
  emit(event) { this.onmessage?.({ data: JSON.stringify(event) }) }
}

function setupHook(projectId) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0, staleTime: Infinity } },
  })
  const wrapper = ({ children }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
  const utils = renderHook(() => useProjectExecutionsLive(projectId), { wrapper })
  return { ...utils, queryClient }
}

beforeEach(() => {
  sockets = []
  global.WebSocket = FakeWebSocket
  localStorage.setItem("token", "tok")
})

afterEach(() => {
  global.WebSocket = OriginalWebSocket
  localStorage.clear()
})

describe("useProjectExecutionsLive", () => {
  it("prepends a new execution on execution.created", () => {
    const { queryClient } = setupHook(3)
    queryClient.setQueryData(["executions", 3, undefined], {
      pages: [[{ id: 1, title: "First" }]],
      pageParams: [0],
    })
    act(() => sockets[0].open())

    act(() => sockets[0].emit({
      event: "execution.created",
      data: { id: 9, title: "New" },
    }))

    const data = queryClient.getQueryData(["executions", 3, undefined])
    expect(data.pages[0]).toEqual([{ id: 9, title: "New" }, { id: 1, title: "First" }])
  })

  it("merges an updated execution into all pages on execution.updated", () => {
    const { queryClient } = setupHook(3)
    queryClient.setQueryData(["executions", 3, undefined], {
      pages: [[{ id: 1, title: "First", status: "pending" }]],
      pageParams: [0],
    })
    act(() => sockets[0].open())

    act(() => sockets[0].emit({
      event: "execution.updated",
      data: { id: 1, status: "completed" },
    }))

    const data = queryClient.getQueryData(["executions", 3, undefined])
    expect(data.pages[0][0]).toMatchObject({ id: 1, status: "completed", title: "First" })
  })

  it("removes the execution on execution.deleted", () => {
    const { queryClient } = setupHook(3)
    queryClient.setQueryData(["executions", 3, undefined], {
      pages: [[{ id: 1 }, { id: 2 }]],
      pageParams: [0],
    })
    act(() => sockets[0].open())

    act(() => sockets[0].emit({
      event: "execution.deleted",
      data: { id: 1, project_id: 3 },
    }))

    const data = queryClient.getQueryData(["executions", 3, undefined])
    expect(data.pages[0]).toEqual([{ id: 2 }])
  })
})
