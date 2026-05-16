import { describe, it, expect, beforeEach, afterEach, vi } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import { ThemeToggle } from "../components/ui/theme-toggle"

const STORAGE_KEY = "testjam.theme"

function stubMatchMedia(prefersDark = false) {
  window.matchMedia = vi.fn((query) => ({
    matches: query.includes("dark") ? prefersDark : false,
    media: query,
    onchange: null,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: () => true,
  }))
}

beforeEach(() => {
  window.localStorage.clear()
  document.documentElement.classList.remove("dark")
  stubMatchMedia(false)
})

afterEach(() => {
  document.documentElement.classList.remove("dark")
})

describe("ThemeToggle", () => {
  it("renders one radio per theme option with system selected by default", () => {
    render(<ThemeToggle />)

    expect(screen.getByRole("radio", { name: "Light" }).getAttribute("aria-checked")).toBe("false")
    expect(screen.getByRole("radio", { name: "Dark" }).getAttribute("aria-checked")).toBe("false")
    expect(screen.getByRole("radio", { name: "System" }).getAttribute("aria-checked")).toBe("true")
  })

  it("adds the dark class on <html> when the user clicks Dark", () => {
    render(<ThemeToggle />)

    fireEvent.click(screen.getByRole("radio", { name: "Dark" }))

    expect(document.documentElement.classList.contains("dark")).toBe(true)
    expect(window.localStorage.getItem(STORAGE_KEY)).toBe("dark")
  })

  it("removes the dark class when the user clicks Light", () => {
    window.localStorage.setItem(STORAGE_KEY, "dark")
    render(<ThemeToggle />)

    fireEvent.click(screen.getByRole("radio", { name: "Light" }))

    expect(document.documentElement.classList.contains("dark")).toBe(false)
    expect(window.localStorage.getItem(STORAGE_KEY)).toBe("light")
  })

  it("updates the active radio aria-checked when switching theme", () => {
    render(<ThemeToggle />)

    fireEvent.click(screen.getByRole("radio", { name: "Dark" }))

    expect(screen.getByRole("radio", { name: "Dark" }).getAttribute("aria-checked")).toBe("true")
    expect(screen.getByRole("radio", { name: "System" }).getAttribute("aria-checked")).toBe("false")
  })
})
