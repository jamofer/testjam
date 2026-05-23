import { describe, it, expect, vi } from "vitest"
import { render, screen } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"

import { BugTimeline } from "../components/bug/BugTimeline"

vi.mock("../api/auth", () => ({
  authApi: { me: vi.fn().mockResolvedValue({ id: 1, locale: "en" }) },
}))


function renderTimeline({ activity = [], comments = [] } = {}) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <BugTimeline
        activity={activity}
        comments={comments}
        statuses={{ open: "Open", resolved: "Resolved" }}
        projectId={1}
      />
    </QueryClientProvider>,
  )
}


describe("BugTimeline", () => {
  it("renders the empty state when nothing has happened", () => {
    renderTimeline()

    expect(screen.getByText(/Nothing has happened yet/i)).toBeInTheDocument()
  })

  it("renders a 'edited a comment' activity row", () => {
    renderTimeline({
      activity: [
        {
          id: 1, field: "comment", to_value: "42", from_value: null,
          changed_at: "2026-05-22T10:00:00Z",
          changed_by: { username: "alice" },
        },
      ],
    })

    expect(screen.getByText(/edited a comment/i)).toBeInTheDocument()
  })

  it("shows an inline diff when the description changes", () => {
    renderTimeline({
      activity: [
        {
          id: 2, field: "description",
          from_value: "First line\nSecond line",
          to_value: "First line\nReplacement",
          changed_at: "2026-05-22T10:00:00Z",
          changed_by: { username: "bob" },
        },
      ],
    })

    expect(screen.getByText(/edited the description/i)).toBeInTheDocument()
    expect(screen.getByText(/- Second line/)).toBeInTheDocument()
    expect(screen.getByText(/\+ Replacement/)).toBeInTheDocument()
  })

  it("renders attachment added activity with filename", () => {
    renderTimeline({
      activity: [
        {
          id: 3, field: "attachment", to_value: "crash.log", from_value: null,
          changed_at: "2026-05-22T10:00:00Z",
          changed_by: { username: "alice" },
        },
      ],
    })

    expect(screen.getByText(/attached crash\.log/i)).toBeInTheDocument()
  })
})
