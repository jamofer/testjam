import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"

import { LocaleSwitcher } from "../components/ui/locale-switcher"

vi.mock("../hooks/useAuth", () => ({
  useUpdateMe: () => ({ mutate: vi.fn() }),
}))

vi.mock("../i18n", () => ({
  default: { language: "en", on: vi.fn(), off: vi.fn() },
  SUPPORTED_LOCALES: ["en", "es", "ca", "gl", "eu"],
  setLocale: vi.fn(),
}))


function renderSwitcher(props) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <LocaleSwitcher {...props} />
    </QueryClientProvider>,
  )
}


describe("LocaleSwitcher", () => {
  beforeEach(() => {
    window.localStorage.clear()
  })

  it("shows the current locale in its native name", () => {
    renderSwitcher()

    expect(screen.getByRole("combobox")).toHaveTextContent("English")
  })

  it("renders with an accessible language label", () => {
    renderSwitcher()

    expect(screen.getByRole("combobox", { name: /language/i })).toBeInTheDocument()
  })
})
