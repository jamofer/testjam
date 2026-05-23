import { describe, it, expect } from "vitest"
import { render, screen } from "@testing-library/react"
import { MemoryRouter } from "react-router-dom"

import { MentionChip } from "../components/mention/MentionChip"


function renderChip(props) {
  return render(
    <MemoryRouter>
      <MentionChip {...props} />
    </MemoryRouter>,
  )
}


describe("MentionChip", () => {
  it("renders a @user chip linking to the profile route", () => {
    renderChip({ kind: "user", raw: "@alice", slug: "alice" })

    const link = screen.getByRole("link", { name: /@alice/ })
    expect(link).toHaveAttribute("href", "/users/alice")
  })

  it("renders a #bug chip linking to the project bug route", () => {
    renderChip({ kind: "bug", raw: "#42", id: 42, projectId: 7 })

    const link = screen.getByRole("link", { name: /#42/ })
    expect(link).toHaveAttribute("href", "/projects/7/bugs/42")
  })

  it("falls back to a span when no slug or id is available", () => {
    renderChip({ kind: "user", raw: "@unknown" })

    expect(screen.queryByRole("link")).toBeNull()
    expect(screen.getByText("@unknown")).toBeInTheDocument()
  })
})
