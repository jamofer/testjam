import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"

import { BugAttachmentsPanel } from "../components/bug/BugAttachmentsPanel"
import { BugAttachmentsContextPanel } from "../components/bug/BugAttachmentsContextPanel"

vi.mock("sonner", () => ({ toast: { success: vi.fn(), error: vi.fn() } }))
vi.mock("../api/bugs", () => ({
  bugsApi: {
    listAttachments: vi.fn(),
    uploadAttachment: vi.fn(),
    deleteAttachment: vi.fn(),
    downloadAttachment: vi.fn(),
  },
}))

import { bugsApi } from "../api/bugs"


function setup(bugId = 7) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <BugAttachmentsPanel bugId={bugId} />
    </QueryClientProvider>,
  )
}

describe("BugAttachmentsPanel", () => {
  beforeEach(() => {
    bugsApi.listAttachments.mockReset()
    bugsApi.uploadAttachment.mockReset()
    bugsApi.deleteAttachment.mockReset()
    bugsApi.downloadAttachment.mockReset()
  })

  it("renders the empty state when no attachments exist", async () => {
    bugsApi.listAttachments.mockResolvedValue([])

    setup()

    expect(await screen.findByText(/No attachments yet/i)).toBeInTheDocument()
  })

  it("lists existing attachments with size + uploader", async () => {
    bugsApi.listAttachments.mockResolvedValue([
      {
        id: 1, bug_id: 7, filename: "crash.log", content_type: "text/plain",
        size_bytes: 2048, uploaded_at: "2026-05-22T10:00:00Z",
        uploaded_by: { id: 9, username: "alice" },
      },
    ])

    setup()

    expect(await screen.findByText("crash.log")).toBeInTheDocument()
    expect(screen.getByText(/alice/)).toBeInTheDocument()
    expect(screen.getByText(/2.0 KB/)).toBeInTheDocument()
  })

  it("copies markdown link from the attachments tab panel", async () => {
    bugsApi.listAttachments.mockResolvedValue([
      {
        id: 12, bug_id: 7, filename: "spec.pdf", content_type: "application/pdf",
        size_bytes: 512, uploaded_at: "2026-05-22T10:00:00Z",
        url: "/api/v1/bugs/7/attachments/12/download",
      },
    ])
    const writeText = vi.fn().mockResolvedValue()
    Object.assign(navigator, { clipboard: { writeText } })

    setup()

    await screen.findByText("spec.pdf")
    fireEvent.click(screen.getByTitle(/Copy markdown link/i))

    await waitFor(() =>
      expect(writeText).toHaveBeenCalledWith(
        `[spec.pdf](${window.location.origin}/api/v1/bugs/7/attachments/12/download)`,
      ),
    )
  })

  it("calls upload api when a file is selected", async () => {
    bugsApi.listAttachments.mockResolvedValue([])
    bugsApi.uploadAttachment.mockResolvedValue({ id: 2, bug_id: 7, filename: "note.txt" })

    setup()

    await screen.findByText(/No attachments yet/i)
    const input = document.querySelector('input[type="file"]')
    const file = new File(["hello"], "note.txt", { type: "text/plain" })
    fireEvent.change(input, { target: { files: [file] } })

    await waitFor(() => expect(bugsApi.uploadAttachment).toHaveBeenCalledWith(7, file))
  })
})


function setupContext(bugId = 7) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <BugAttachmentsContextPanel bugId={bugId} />
    </QueryClientProvider>,
  )
}


describe("BugAttachmentsContextPanel", () => {
  beforeEach(() => {
    bugsApi.listAttachments.mockReset()
  })

  it("copies a markdown link for files using the attachment url", async () => {
    bugsApi.listAttachments.mockResolvedValue([
      {
        id: 4, bug_id: 7, filename: "spec.pdf", content_type: "application/pdf",
        size_bytes: 1024, uploaded_at: "2026-05-22T10:00:00Z",
        url: "/api/v1/bugs/7/attachments/4/download",
      },
    ])
    const writeText = vi.fn().mockResolvedValue()
    Object.assign(navigator, { clipboard: { writeText } })

    setupContext()

    await screen.findByText("spec.pdf")
    fireEvent.click(screen.getByTitle(/Copy markdown link/i))

    await waitFor(() =>
      expect(writeText).toHaveBeenCalledWith(
        `[spec.pdf](${window.location.origin}/api/v1/bugs/7/attachments/4/download)`,
      ),
    )
  })

  it("uses image markdown for image attachments", async () => {
    bugsApi.listAttachments.mockResolvedValue([
      {
        id: 9, bug_id: 7, filename: "screenshot.png", content_type: "image/png",
        size_bytes: 1024, uploaded_at: "2026-05-22T10:00:00Z",
        url: "/api/v1/bugs/7/attachments/9/download",
      },
    ])
    const writeText = vi.fn().mockResolvedValue()
    Object.assign(navigator, { clipboard: { writeText } })

    setupContext()

    await screen.findByText("screenshot.png")
    fireEvent.click(screen.getByTitle(/Copy markdown link/i))

    await waitFor(() =>
      expect(writeText).toHaveBeenCalledWith(
        `![screenshot.png](${window.location.origin}/api/v1/bugs/7/attachments/9/download)`,
      ),
    )
  })

  it("copies the raw URL via the Copy button", async () => {
    bugsApi.listAttachments.mockResolvedValue([
      {
        id: 11, bug_id: 7, filename: "spec.pdf", content_type: "application/pdf",
        size_bytes: 512, uploaded_at: "2026-05-22T10:00:00Z",
        url: "/api/v1/bugs/7/attachments/11/download",
      },
    ])
    const writeText = vi.fn().mockResolvedValue()
    Object.assign(navigator, { clipboard: { writeText } })

    setupContext()

    await screen.findByText("spec.pdf")
    fireEvent.click(screen.getByTitle(/Copy URL/i))

    await waitFor(() =>
      expect(writeText).toHaveBeenCalledWith(
        `${window.location.origin}/api/v1/bugs/7/attachments/11/download`,
      ),
    )
  })
})
