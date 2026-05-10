import { describe, it, expect, vi } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { MemoryRouter, Routes, Route } from "react-router-dom"
import { AppLayout } from "../components/layout/AppLayout"

vi.mock("../hooks/useAuth", () => ({
  useMe: () => ({ data: { id: 1, username: "u", full_name: "U Ser", is_admin: false }, isLoading: false, isError: false }),
  useLogout: () => () => {},
}))

vi.mock("../hooks/useProjects", () => ({
  useProject: () => ({ data: null }),
}))

vi.mock("../hooks/useExecutions", () => ({
  useExecution: () => ({ data: null }),
}))

vi.mock("../hooks/useSuites", () => ({
  useCase: () => ({ data: null }),
  useSuite: () => ({ data: null }),
}))

vi.mock("../api/testplans", () => ({
  plansApi: { get: vi.fn() },
}))

vi.mock("../components/layout/NotificationsBell", () => ({
  NotificationsBell: () => null,
}))

vi.mock("../components/ui/command-palette", () => ({
  CommandPalette: () => null,
}))

function setup() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0, staleTime: Infinity } },
  })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={["/projects"]}>
        <Routes>
          <Route element={<AppLayout />}>
            <Route path="/projects" element={<div>Page</div>} />
          </Route>
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe("AppLayout — mobile sidebar", () => {
  it("renders hamburger toggle and close button", () => {
    setup()
    expect(screen.getByRole("button", { name: /open menu/i })).toBeInTheDocument()
    expect(screen.getByRole("button", { name: /close menu/i })).toBeInTheDocument()
  })

  it("opens sidebar (translates in) and shows backdrop", () => {
    setup()
    const open = screen.getByRole("button", { name: /open menu/i })
    expect(document.querySelector(".bg-black\\/40")).not.toBeInTheDocument()

    fireEvent.click(open)

    expect(document.querySelector(".bg-black\\/40")).toBeInTheDocument()
    const aside = document.querySelector("aside")
    expect(aside.className).toMatch(/translate-x-0/)
    expect(aside.className).not.toMatch(/-translate-x-full(?!\smd:)/)
  })

  it("closes when backdrop clicked", () => {
    setup()
    fireEvent.click(screen.getByRole("button", { name: /open menu/i }))
    const backdrop = document.querySelector(".bg-black\\/40")
    fireEvent.click(backdrop)
    expect(document.querySelector(".bg-black\\/40")).not.toBeInTheDocument()
  })

  it("closes when X clicked", () => {
    setup()
    fireEvent.click(screen.getByRole("button", { name: /open menu/i }))
    fireEvent.click(screen.getByRole("button", { name: /close menu/i }))
    expect(document.querySelector(".bg-black\\/40")).not.toBeInTheDocument()
  })
})
