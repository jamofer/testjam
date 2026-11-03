import { describe, it, expect, vi } from "vitest"
import { fireEvent, render, screen, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { MemoryRouter, Route, Routes } from "react-router-dom"

import "../i18n"
import { CoverageMatrixPage } from "../pages/CoverageMatrixPage"

vi.mock("../hooks/useProjects", () => ({ useProject: () => ({ data: { id: 1, name: "Acme" } }) }))
vi.mock("../hooks/useSuites", () => ({
  useSuitesAll: () => ({
    data: [
      { id: 1, name: "Auth", parent_suite_id: null },
      { id: 2, name: "Billing", parent_suite_id: null },
    ],
  }),
}))
vi.mock("../api/coverage", () => ({
  coverageApi: {
    matrix: () => Promise.resolve({
      versions: [{ id: 7, name: "v1.0" }],
      cases: [
        { id: 10, name: "Login works", suite_id: 1 },
        { id: 20, name: "Invoice totals", suite_id: 2 },
      ],
      cells: [{ case_id: 10, version_id: 7, status: "passed" }],
    }),
  },
}))

describe("CoverageMatrixPage", () => {
  it("hides suites that stop matching the filter without crashing", async () => {
    renderPage()
    await screen.findByText("Billing")

    fireEvent.change(screen.getByPlaceholderText("Filter suites and cases…"), { target: { value: "login" } })

    await waitFor(() => expect(screen.queryByText("Billing")).not.toBeInTheDocument())
    expect(screen.getByText("Auth")).toBeInTheDocument()
  })

  it("shows the suites again when the filter is cleared", async () => {
    renderPage()
    const filter = await screen.findByPlaceholderText("Filter suites and cases…")
    fireEvent.change(filter, { target: { value: "login" } })
    await waitFor(() => expect(screen.queryByText("Billing")).not.toBeInTheDocument())

    fireEvent.change(filter, { target: { value: "" } })

    expect(await screen.findByText("Billing")).toBeInTheDocument()
  })
})

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/projects/1/coverage"]}>
        <Routes>
          <Route path="/projects/:id/coverage" element={<CoverageMatrixPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}
