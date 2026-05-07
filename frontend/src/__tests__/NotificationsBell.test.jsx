import { describe, it, expect, vi } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { MemoryRouter } from "react-router-dom"
import { NotificationsBell } from "../components/layout/NotificationsBell"

vi.mock("../api/notifications", () => ({
  notificationsApi: {
    list: vi.fn(),
    unreadCount: vi.fn(),
    markRead: vi.fn(() => Promise.resolve({})),
    markAllRead: vi.fn(() => Promise.resolve({ unread: 0 })),
  },
}))

vi.mock("../hooks/useNotifications", async (importOriginal) => {
  const actual = await importOriginal()
  return {
    ...actual,
    useNotificationsSocket: () => undefined,
  }
})

function setup({ list = [], unread = 0 } = {}) {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0, staleTime: Infinity } },
  })
  qc.setQueryData(["notifications"], list)
  qc.setQueryData(["notifications", "unread-count"], { unread })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <NotificationsBell enabled={false} />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe("NotificationsBell", () => {
  it("shows the unread count badge when there are unread notifications", () => {
    setup({ unread: 3 })
    expect(screen.getByTestId("unread-badge").textContent).toBe("3")
  })

  it("hides the badge when no unread", () => {
    setup({ unread: 0 })
    expect(screen.queryByTestId("unread-badge")).toBeNull()
  })

  it("opens the panel and lists notifications on click", () => {
    setup({
      unread: 1,
      list: [
        { id: 1, type: "execution_assigned", message: "alice assigned you to 'Run'",
          link: "/executions/9/run", is_read: false, created_at: "2026-05-07T12:00:00Z" },
      ],
    })
    fireEvent.click(screen.getByRole("button", { name: /notifications/i }))
    expect(screen.getByText(/assigned you to 'Run'/)).toBeInTheDocument()
    expect(screen.getByText(/mark all read/i)).toBeInTheDocument()
  })

  it("renders empty state when there is nothing", () => {
    setup({ unread: 0, list: [] })
    fireEvent.click(screen.getByRole("button", { name: /notifications/i }))
    expect(screen.getByText(/no notifications/i)).toBeInTheDocument()
  })
})
