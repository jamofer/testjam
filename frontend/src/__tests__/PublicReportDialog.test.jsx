import { describe, it, expect, vi } from "vitest"
import { fireEvent, render, screen } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"

import "../i18n"
import { PublicReportDialog } from "../components/share/PublicReportDialog"

vi.mock("../api/publicReports", () => ({
  publicReportsApi: {
    list: vi.fn(() => new Promise(() => {})),
    create: vi.fn(),
    revoke: vi.fn(),
  },
}))
vi.mock("sonner", () => ({ toast: { success: vi.fn(), error: vi.fn() } }))


describe("PublicReportDialog loading state", () => {
  it("renders the resolved Loading… label, not the raw key", () => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    render(
      <QueryClientProvider client={queryClient}>
        <PublicReportDialog
          projectId={1}
          defaultKind="bug_report"
          trigger={<button>Open</button>}
        />
      </QueryClientProvider>,
    )

    fireEvent.click(screen.getByText("Open"))

    expect(screen.getByText("Loading…")).toBeInTheDocument()
    expect(screen.queryByText(/common:loading/)).toBeNull()
  })
})
