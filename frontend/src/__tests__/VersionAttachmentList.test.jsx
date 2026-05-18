import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"

import { VersionAttachmentList } from "../components/version/VersionAttachmentList"

vi.mock("sonner", () => ({ toast: { success: vi.fn(), error: vi.fn() } }))
vi.mock("../api/versions", () => ({
  versionsApi: {
    listAttachments: vi.fn(),
    uploadAttachment: vi.fn(),
    deleteAttachment: vi.fn(),
    downloadAttachment: vi.fn(),
  },
}))

import { versionsApi } from "../api/versions"

function setup() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(
    <QueryClientProvider client={queryClient}>
      <VersionAttachmentList versionId={42} />
    </QueryClientProvider>,
  )
}

describe("VersionAttachmentList", () => {
  beforeEach(() => {
    versionsApi.listAttachments.mockReset()
    versionsApi.uploadAttachment.mockReset()
    versionsApi.deleteAttachment.mockReset()
    versionsApi.downloadAttachment.mockReset()
    versionsApi.uploadAttachment.mockResolvedValue({ id: 1 })
    versionsApi.deleteAttachment.mockResolvedValue({})
  })

  it("renders attachments returned by the API", async () => {
    versionsApi.listAttachments.mockResolvedValue([
      { id: 7, filename: "release-notes.pdf", content_type: "application/pdf", size_bytes: 2048 },
    ])

    setup()

    expect(await screen.findByText("release-notes.pdf")).toBeInTheDocument()
    expect(screen.getByText(/2 KB/)).toBeInTheDocument()
  })

  it("uploads the file picked from the input", async () => {
    versionsApi.listAttachments.mockResolvedValue([])
    setup()
    const file = new File(["payload"], "notes.txt", { type: "text/plain" })

    const input = document.querySelector("input[type=file]")
    fireEvent.change(input, { target: { files: [file] } })

    await waitFor(() => expect(versionsApi.uploadAttachment).toHaveBeenCalledWith(42, file))
  })

  it("deletes via the trash button", async () => {
    versionsApi.listAttachments.mockResolvedValue([
      { id: 11, filename: "binary.bin", content_type: null, size_bytes: 0 },
    ])
    setup()

    const trash = await screen.findByTitle(/delete/i)
    fireEvent.click(trash)

    await waitFor(() => expect(versionsApi.deleteAttachment).toHaveBeenCalledWith(42, 11))
  })
})
