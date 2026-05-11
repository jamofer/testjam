import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import { renderHook, act } from "@testing-library/react"
import { useTopicSocket } from "../hooks/useTopicSocket"

const OriginalWebSocket = global.WebSocket
let sockets = []

class FakeWebSocket {
  static CONNECTING = 0
  static OPEN = 1
  static CLOSED = 3

  constructor(url) {
    this.url = url
    this.readyState = FakeWebSocket.CONNECTING
    this.sent = []
    this.closed = false
    sockets.push(this)
  }

  send(payload) {
    this.sent.push(payload)
  }

  close() {
    this.closed = true
    this.readyState = FakeWebSocket.CLOSED
    this.onclose?.()
  }

  addEventListener() {}

  open() {
    this.readyState = FakeWebSocket.OPEN
    this.onopen?.()
  }

  emit(event) {
    this.onmessage?.({ data: JSON.stringify(event) })
  }
}

beforeEach(() => {
  sockets = []
  global.WebSocket = FakeWebSocket
  localStorage.setItem("token", "token-abc")
  vi.useFakeTimers()
})

afterEach(() => {
  global.WebSocket = OriginalWebSocket
  vi.useRealTimers()
  localStorage.clear()
})

describe("useTopicSocket", () => {
  it("opens a single WebSocket and subscribes to each topic on open", () => {
    renderHook(() => useTopicSocket(["user:1", "project:7"], {}))

    expect(sockets).toHaveLength(1)
    const socket = sockets[0]
    expect(socket.url).toContain("/api/v1/ws?token=token-abc")

    act(() => socket.open())

    expect(socket.sent.map(JSON.parse)).toEqual([
      { action: "subscribe", topic: "user:1" },
      { action: "subscribe", topic: "project:7" },
    ])
  })

  it("dispatches matching events to the registered handler", () => {
    const handler = vi.fn()
    renderHook(() =>
      useTopicSocket(["project:1"], { "execution.created": handler }),
    )
    const socket = sockets[0]
    act(() => socket.open())

    act(() => socket.emit({ event: "execution.created", data: { id: 9 } }))
    act(() => socket.emit({ event: "result.updated", data: { id: 1 } }))

    expect(handler).toHaveBeenCalledTimes(1)
    expect(handler).toHaveBeenCalledWith({ id: 9 }, {
      event: "execution.created", data: { id: 9 },
    })
  })

  it("does not connect when the hook is disabled", () => {
    renderHook(() => useTopicSocket(["user:1"], {}, { enabled: false }))
    expect(sockets).toHaveLength(0)
  })

  it("does not connect when no token is stored", () => {
    localStorage.clear()
    renderHook(() => useTopicSocket(["user:1"], {}))
    expect(sockets).toHaveLength(0)
  })

  it("reconnects with the documented backoff schedule on close", () => {
    renderHook(() => useTopicSocket(["user:1"], {}))
    expect(sockets).toHaveLength(1)
    act(() => sockets[0].close())

    act(() => vi.advanceTimersByTime(1000))
    expect(sockets).toHaveLength(2)
    act(() => sockets[1].close())

    act(() => vi.advanceTimersByTime(1999))
    expect(sockets).toHaveLength(2)
    act(() => vi.advanceTimersByTime(1))
    expect(sockets).toHaveLength(3)

    act(() => sockets[2].close())
    act(() => vi.advanceTimersByTime(5000))
    expect(sockets).toHaveLength(4)

    act(() => sockets[3].close())
    act(() => vi.advanceTimersByTime(15000))
    expect(sockets).toHaveLength(5)

    act(() => sockets[4].close())
    act(() => vi.advanceTimersByTime(30000))
    expect(sockets).toHaveLength(6)
  })

  it("clears the reconnect timer on unmount", () => {
    const { unmount } = renderHook(() => useTopicSocket(["user:1"], {}))
    act(() => sockets[0].close())
    unmount()
    act(() => vi.advanceTimersByTime(60000))
    expect(sockets).toHaveLength(1)
  })

  it("closes the socket on unmount", () => {
    const { unmount } = renderHook(() => useTopicSocket(["user:1"], {}))
    act(() => sockets[0].open())
    unmount()
    expect(sockets[0].closed).toBe(true)
  })

  it("responds to a server ping with a pong action", () => {
    renderHook(() => useTopicSocket(["user:1"], {}))
    const socket = sockets[0]
    act(() => socket.open())
    socket.sent.length = 0

    act(() => socket.emit({ event: "ping" }))

    expect(socket.sent.map(JSON.parse)).toEqual([{ action: "pong" }])
  })

  it("does not forward ping events to user handlers", () => {
    const handler = vi.fn()
    renderHook(() => useTopicSocket(["user:1"], { ping: handler }))
    act(() => sockets[0].open())

    act(() => sockets[0].emit({ event: "ping" }))

    expect(handler).not.toHaveBeenCalled()
  })

  it("closes the socket after 60s without a ping", () => {
    renderHook(() => useTopicSocket(["user:1"], {}))
    act(() => sockets[0].open())

    act(() => vi.advanceTimersByTime(60000))

    expect(sockets[0].closed).toBe(true)
  })

  it("keeps the socket open when pings arrive within the watchdog window", () => {
    renderHook(() => useTopicSocket(["user:1"], {}))
    const socket = sockets[0]
    act(() => socket.open())

    act(() => vi.advanceTimersByTime(50000))
    act(() => socket.emit({ event: "ping" }))
    act(() => vi.advanceTimersByTime(50000))

    expect(socket.closed).toBe(false)
  })
})
