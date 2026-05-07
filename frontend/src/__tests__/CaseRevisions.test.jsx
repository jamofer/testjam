import { describe, it, expect, vi } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { CaseRevisions } from "../components/case/CaseRevisions"

vi.mock("../api/testcases", () => ({
  casesApi: {
    listRevisions: vi.fn(),
    getRevision: vi.fn(),
  },
}))

import { casesApi } from "../api/testcases"

function setup(revs) {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0, staleTime: Infinity } },
  })
  qc.setQueryData(["case-revisions", "42"], revs)
  return render(
    <QueryClientProvider client={qc}>
      <CaseRevisions caseId="42" />
    </QueryClientProvider>,
  )
}

describe("CaseRevisions", () => {
  it("renders an empty state when no revisions", () => {
    setup([])
    expect(screen.getByText(/no history yet/i)).toBeInTheDocument()
  })

  it("renders a revision row per item", () => {
    setup([
      { id: 2, change_kind: "updated", actor: { id: 1, username: "alice" },
        created_at: "2026-05-07T12:00:00Z" },
      { id: 1, change_kind: "created", actor: { id: 1, username: "alice" },
        created_at: "2026-05-07T11:00:00Z" },
    ])
    expect(screen.getByText(/updated/i)).toBeInTheDocument()
    expect(screen.getByText(/created/i)).toBeInTheDocument()
    expect(screen.getAllByText("alice").length).toBe(2)
  })

  it("expands a revision and renders its diff", async () => {
    casesApi.getRevision.mockImplementation((cid, rid) =>
      Promise.resolve({
        id: rid,
        case_id: 42,
        change_kind: rid === 2 ? "updated" : "created",
        actor: { id: 1, username: "alice" },
        created_at: "2026-05-07T12:00:00Z",
        snapshot: rid === 2
          ? { name: "Login", description: "v2 text", preconditions: null,
              setup: null, teardown: null, external_id: null, tags: [], steps: [] }
          : { name: "Login", description: "v1 text", preconditions: null,
              setup: null, teardown: null, external_id: null, tags: [], steps: [] },
      }),
    )
    setup([
      { id: 2, change_kind: "updated", actor: { id: 1, username: "alice" },
        created_at: "2026-05-07T12:00:00Z" },
      { id: 1, change_kind: "created", actor: { id: 1, username: "alice" },
        created_at: "2026-05-07T11:00:00Z" },
    ])

    fireEvent.click(screen.getAllByRole("button")[0])
    expect(await screen.findByText(/v1 text/, {}, { timeout: 2000 })).toBeInTheDocument()
    expect(await screen.findByText(/v2 text/, {}, { timeout: 2000 })).toBeInTheDocument()
  })
})
