import { describe, it, expect, vi, beforeEach } from "vitest"
import { fireEvent, render, screen, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { MemoryRouter, Route, Routes } from "react-router-dom"
import { toast } from "sonner"

import "../i18n"
import { bugsApi } from "../api/bugs"
import { BugDetailPage } from "../pages/BugDetailPage"

vi.mock("sonner", () => ({ toast: { success: vi.fn(), error: vi.fn(), warning: vi.fn() } }))
vi.mock("../api/bugs", () => ({
  bugsApi: {
    get: vi.fn(),
    update: vi.fn(),
    listComments: vi.fn(() => Promise.resolve([])),
    listActivity: vi.fn(() => Promise.resolve([])),
    getContext: vi.fn(() => Promise.resolve(null)),
    listLinks: vi.fn(() => Promise.resolve([])),
    listWatchers: vi.fn(() => Promise.resolve([])),
  },
}))
vi.mock("../hooks/useProjects", () => ({ useProject: () => ({ data: { id: 1, name: "Acme" } }) }))
vi.mock("../hooks/useVersions", () => ({ useVersions: () => ({ data: [] }) }))
vi.mock("../hooks/useAuth", () => ({ useMe: () => ({ data: { id: 1, username: "alice" } }) }))
vi.mock("../hooks/useProjectRole", () => ({ useProjectRole: () => ({ canWrite: true, canDelete: true }) }))
vi.mock("../hooks/useBugLive", () => ({ useBugLive: () => ({ connected: false }) }))
vi.mock("../components/bug/BugAttachmentsContextPanel", () => ({ BugAttachmentsContextPanel: () => null }))
vi.mock("../components/bug/BugAttachmentsPanel", () => ({ BugAttachmentsPanel: () => null }))
vi.mock("../components/bug/BugTimeline", () => ({ BugTimeline: () => null }))
vi.mock("../components/integration/BugExternalLinksPanel", () => ({ BugExternalLinksPanel: () => null }))
vi.mock("../components/customField/CustomFieldInput", () => ({ CustomFieldsEditableBody: () => null }))
vi.mock("../components/environment/EnvironmentBadge", () => ({ EnvironmentBadge: () => null }))

const BUG = {
  id: 5,
  project_id: 1,
  number: 5,
  title: "Crash on save",
  description: "Steps",
  severity: "medium",
  status: "open",
  tags: [],
  custom_fields: {},
  created_at: "2026-11-01T10:00:00Z",
  updated_at: "2026-11-01T10:00:00Z",
}

beforeEach(() => {
  vi.clearAllMocks()
  bugsApi.get.mockResolvedValue(BUG)
})

describe("BugDetailPage title editing", () => {
  it("sends the title it started editing from", async () => {
    bugsApi.update.mockResolvedValue({ ...BUG, title: "Crash on first save" })
    await renderPage()

    renameTitle("Crash on first save")

    await waitFor(() => expect(bugsApi.update).toHaveBeenCalledWith(5, {
      title: "Crash on first save",
      previous_values: { title: "Crash on save" },
    }))
  })

  it("keeps the draft and warns when someone else changed the title", async () => {
    bugsApi.update.mockRejectedValueOnce(editConflict("title", "Teammate title"))
    await renderPage()

    renameTitle("My title")

    await waitFor(() => expect(toast.error).toHaveBeenCalledWith(
      expect.stringContaining("Someone else changed this"), expect.anything(),
    ))
    expect(screen.getByDisplayValue("My title")).toBeInTheDocument()
  })

  it("overwrites on the next save after a conflict", async () => {
    bugsApi.update
      .mockRejectedValueOnce(editConflict("title", "Teammate title"))
      .mockResolvedValueOnce({ ...BUG, title: "My title" })
    await renderPage()
    renameTitle("My title")
    await waitFor(() => expect(toast.error).toHaveBeenCalled())

    fireEvent.keyDown(screen.getByDisplayValue("My title"), { key: "Enter" })

    await waitFor(() => expect(bugsApi.update).toHaveBeenLastCalledWith(5, {
      title: "My title",
      previous_values: { title: "Teammate title" },
    }))
  })
})

async function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/bugs/5"]}>
        <Routes>
          <Route path="/bugs/:bugId" element={<BugDetailPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
  fireEvent.click(await screen.findByText(BUG.title))
}

function renameTitle(title) {
  const input = screen.getByDisplayValue(BUG.title)
  fireEvent.change(input, { target: { value: title } })
  fireEvent.keyDown(input, { key: "Enter" })
}

function editConflict(field, current) {
  return { response: { status: 409, data: { detail: { code: "edit_conflict", field, current } } } }
}
