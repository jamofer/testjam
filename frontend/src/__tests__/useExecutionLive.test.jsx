import { afterEach, beforeEach, describe, expect, it } from "vitest"
import { renderHook, act } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { useExecutionLive } from "../hooks/useExecutionLive"

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
  close() {
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

function setupHook(executionId) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0, staleTime: Infinity } },
  })
  const wrapper = ({ children }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
  const utils = renderHook(() => useExecutionLive(executionId), { wrapper })
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

describe("useExecutionLive", () => {
  it("subscribes to the matching execution topic and exposes connected once open", () => {
    const { result, queryClient } = setupHook(42)
    queryClient.setQueryData(["results", "42"], [
      { id: 1, status: "not_run", step_results: [] },
    ])

    expect(sockets[0].url).toContain("/api/v1/ws?token=tok")
    expect(result.current.connected).toBe(false)
    act(() => sockets[0].open())
    expect(result.current.connected).toBe(true)
  })

  it("patches an existing result on result.updated", () => {
    const { queryClient } = setupHook(42)
    queryClient.setQueryData(["results", "42"], [
      { id: 7, status: "not_run", step_results: [] },
    ])
    act(() => sockets[0].open())

    act(() => sockets[0].emit({
      event: "result.updated",
      data: { id: 7, status: "passed", duration_ms: 1234 },
    }))

    const results = queryClient.getQueryData(["results", "42"])
    expect(results[0]).toMatchObject({ id: 7, status: "passed", duration_ms: 1234 })
  })

  it("inserts a new step result on step_result.started", () => {
    const { queryClient } = setupHook(42)
    queryClient.setQueryData(["results", "42"], [
      { id: 7, status: "running", step_results: [] },
    ])
    act(() => sockets[0].open())

    act(() => sockets[0].emit({
      event: "step_result.started",
      data: { id: 9, test_result_id: 7, step_id: 3, status: "running", log_output: null },
    }))

    const results = queryClient.getQueryData(["results", "42"])
    expect(results[0].step_results).toEqual([
      { id: 9, test_result_id: 7, step_id: 3, status: "running", log_output: null },
    ])
  })

  it("appends a single log entry on step_result.log_appended", () => {
    const { queryClient } = setupHook(42)
    queryClient.setQueryData(["results", "42"], [
      {
        id: 7,
        status: "running",
        step_results: [
          { id: 9, test_result_id: 7, step_id: 3, status: "running", log_output: null },
        ],
      },
    ])
    act(() => sockets[0].open())

    act(() => sockets[0].emit({
      event: "step_result.log_appended",
      data: { step_result_id: 9, level: "INFO", message: "logging in" },
    }))
    act(() => sockets[0].emit({
      event: "step_result.log_appended",
      data: { step_result_id: 9, level: "FAIL", message: "boom" },
    }))

    const log = queryClient.getQueryData(["results", "42"])[0].step_results[0].log_output
    expect(log).toBe("**[INFO]** logging in\n\n**[FAIL]** boom")
  })

  it("appends a batched entries array on step_result.log_appended", () => {
    const { queryClient } = setupHook(42)
    queryClient.setQueryData(["results", "42"], [
      {
        id: 7,
        status: "running",
        step_results: [
          { id: 9, test_result_id: 7, step_id: 3, status: "running", log_output: null },
        ],
      },
    ])
    act(() => sockets[0].open())

    act(() => sockets[0].emit({
      event: "step_result.log_appended",
      data: {
        entries: [
          { step_result_id: 9, level: "INFO", message: "first" },
          { step_result_id: 9, level: "WARN", message: "second" },
          { step_result_id: 9, level: "FAIL", message: "third" },
        ],
      },
    }))

    const log = queryClient.getQueryData(["results", "42"])[0].step_results[0].log_output
    expect(log).toBe("**[INFO]** first\n\n**[WARN]** second\n\n**[FAIL]** third")
  })

  it("groups entries from a batched payload by step_result_id", () => {
    const { queryClient } = setupHook(42)
    queryClient.setQueryData(["results", "42"], [
      {
        id: 7,
        status: "running",
        step_results: [
          { id: 9, test_result_id: 7, step_id: 3, status: "running", log_output: null },
          { id: 10, test_result_id: 7, step_id: 4, status: "running", log_output: null },
        ],
      },
    ])
    act(() => sockets[0].open())

    act(() => sockets[0].emit({
      event: "step_result.log_appended",
      data: {
        entries: [
          { step_result_id: 9, level: "INFO", message: "for-9" },
          { step_result_id: 10, level: "INFO", message: "for-10" },
        ],
      },
    }))

    const stepResults = queryClient.getQueryData(["results", "42"])[0].step_results
    expect(stepResults.find(sr => sr.id === 9).log_output).toBe("**[INFO]** for-9")
    expect(stepResults.find(sr => sr.id === 10).log_output).toBe("**[INFO]** for-10")
  })

  it("stores the updated execution under ['executions', id]", () => {
    const { queryClient } = setupHook(42)
    act(() => sockets[0].open())

    act(() => sockets[0].emit({
      event: "execution.updated",
      data: { id: 42, status: "completed", title: "Run" },
    }))

    expect(queryClient.getQueryData(["executions", "42"])).toMatchObject({
      status: "completed",
    })
  })
})
