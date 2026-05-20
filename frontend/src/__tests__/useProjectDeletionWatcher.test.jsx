import { describe, it, expect, vi, beforeEach } from "vitest"
import { act, renderHook } from "@testing-library/react"
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"

vi.mock("../hooks/useTopicSocket", () => {
  const handlers = { current: null }
  const topics = { current: null }
  const enabled = { current: null }
  return {
    handlersRef: handlers,
    topicsRef: topics,
    enabledRef: enabled,
    useTopicSocket: (t, h, opts) => {
      topics.current = t
      handlers.current = h
      enabled.current = opts?.enabled ?? true
      return { connected: true }
    },
  }
})

const toastMock = { warning: vi.fn() }
vi.mock("sonner", () => ({ toast: toastMock }))

import {
  handlersRef,
  topicsRef,
  enabledRef,
} from "../hooks/useTopicSocket"
import { useProjectDeletionWatcher } from "../hooks/useProjectDeletionWatcher"

function wrapperWith(client, initialPath) {
  return ({ children }) => (
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[initialPath]}>
        <Routes>
          <Route path="*" element={<>{children}<LocationProbe /></>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  )
}

let lastLocation = null
function LocationProbe() {
  lastLocation = useLocation()
  return null
}

describe("useProjectDeletionWatcher", () => {
  beforeEach(() => {
    toastMock.warning.mockClear()
    lastLocation = null
  })

  it("subscribes to the project topic when inside a project route", () => {
    const client = new QueryClient()
    renderHook(() => useProjectDeletionWatcher(), {
      wrapper: wrapperWith(client, "/projects/42/bugs"),
    })
    expect(topicsRef.current).toEqual(["project:42"])
    expect(enabledRef.current).toBe(true)
  })

  it("stays disabled when not in a project route", () => {
    const client = new QueryClient()
    renderHook(() => useProjectDeletionWatcher(), {
      wrapper: wrapperWith(client, "/users"),
    })
    expect(topicsRef.current).toEqual([])
    expect(enabledRef.current).toBe(false)
  })

  it("redirects to /projects, toasts and invalidates on project.deleted", () => {
    const client = new QueryClient()
    const invalidateSpy = vi.spyOn(client, "invalidateQueries")
    renderHook(() => useProjectDeletionWatcher(), {
      wrapper: wrapperWith(client, "/projects/42/bugs"),
    })

    act(() => {
      handlersRef.current["project.deleted"]({ id: 42, name: "Acme" })
    })

    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ["projects"] })
    expect(lastLocation?.pathname).toBe("/projects")
    expect(toastMock.warning).toHaveBeenCalledTimes(1)
    expect(toastMock.warning.mock.calls[0][0]).toMatch(/Acme/)
  })

  it("ignores event for a different project id", () => {
    const client = new QueryClient()
    renderHook(() => useProjectDeletionWatcher(), {
      wrapper: wrapperWith(client, "/projects/42/bugs"),
    })

    act(() => {
      handlersRef.current["project.deleted"]({ id: 99, name: "Other" })
    })

    expect(lastLocation?.pathname).toBe("/projects/42/bugs")
    expect(toastMock.warning).not.toHaveBeenCalled()
  })
})
