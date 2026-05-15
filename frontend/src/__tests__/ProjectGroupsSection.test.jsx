import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"

import { ProjectGroupsSection } from "../components/project/ProjectGroupsSection"

vi.mock("sonner", () => ({ toast: { success: vi.fn(), error: vi.fn() } }))
vi.mock("../api/projectGroups", () => ({
  projectGroupsApi: {
    list: vi.fn(),
    add: vi.fn(),
    update: vi.fn(),
    remove: vi.fn(),
  },
}))
vi.mock("../api/client", () => ({
  api: { get: vi.fn() },
}))

import { projectGroupsApi } from "../api/projectGroups"
import { api } from "../api/client"

const ASSIGNMENTS = [
  { id: 1, group_id: 10, group_name: "QA Team", role: "tester", member_count: 3, added_at: "2026-05-01T00:00:00Z" },
]
const ALL_GROUPS = [
  { id: 10, name: "QA Team" },
  { id: 11, name: "Devs" },
]

function setup() {
  projectGroupsApi.list.mockResolvedValue(ASSIGNMENTS)
  api.get.mockResolvedValue({ data: ALL_GROUPS })
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <ProjectGroupsSection projectId={42} />
    </QueryClientProvider>,
  )
}

describe("ProjectGroupsSection", () => {
  beforeEach(() => {
    projectGroupsApi.list.mockReset()
    projectGroupsApi.add.mockReset()
    projectGroupsApi.update.mockReset()
    projectGroupsApi.remove.mockReset()
    api.get.mockReset()
    projectGroupsApi.add.mockResolvedValue({})
    projectGroupsApi.update.mockResolvedValue({})
    projectGroupsApi.remove.mockResolvedValue({})
  })

  it("lists assigned groups with role and member count", async () => {
    setup()

    expect(await screen.findByText("QA Team")).toBeInTheDocument()
    expect(screen.getByText(/3 members/)).toBeInTheDocument()
  })

  it("filters already-assigned groups out of the candidate list", async () => {
    setup()
    await screen.findByText("QA Team")

    const candidateOptions = Array.from(
      screen.getByDisplayValue("Select group…").querySelectorAll("option"),
    ).map(option => option.textContent)
    expect(candidateOptions).toEqual(["Select group…", "Devs"])
  })

  it("posts the chosen group + role on submit", async () => {
    setup()
    await screen.findByText("QA Team")

    fireEvent.change(screen.getByDisplayValue("Select group…"), { target: { value: "11" } })
    fireEvent.click(screen.getByRole("button", { name: /assign/i }))

    await waitFor(() =>
      expect(projectGroupsApi.add).toHaveBeenCalledWith(42, 11, "tester"),
    )
  })

  it("updates role on selector change", async () => {
    setup()
    await screen.findByText("QA Team")

    const [assignmentRoleSelect] = screen.getAllByDisplayValue("tester")
    fireEvent.change(assignmentRoleSelect, { target: { value: "viewer" } })

    await waitFor(() =>
      expect(projectGroupsApi.update).toHaveBeenCalledWith(42, 10, "viewer"),
    )
  })

  it("removes assignment when delete clicked", async () => {
    setup()
    await screen.findByText("QA Team")

    fireEvent.click(screen.getByLabelText("Remove group"))

    await waitFor(() => expect(projectGroupsApi.remove).toHaveBeenCalledWith(42, 10))
  })
})
