import { describe, it, expect, beforeEach, afterEach, vi } from "vitest"
import { renderHook, act } from "@testing-library/react"
import { useTheme, initTheme } from "../hooks/useTheme"

const STORAGE_KEY = "testjam.theme"

function setSystemDarkPreference(matches) {
  const listeners = new Set()
  const mql = {
    matches,
    media: "(prefers-color-scheme: dark)",
    onchange: null,
    addEventListener: (_event, fn) => listeners.add(fn),
    removeEventListener: (_event, fn) => listeners.delete(fn),
    dispatchEvent: () => true,
  }
  window.matchMedia = vi.fn(() => mql)
  return {
    emit: (nextMatches) => {
      mql.matches = nextMatches
      listeners.forEach((fn) => fn({ matches: nextMatches }))
    },
  }
}

beforeEach(() => {
  window.localStorage.clear()
  document.documentElement.classList.remove("dark")
  setSystemDarkPreference(false)
})

afterEach(() => {
  document.documentElement.classList.remove("dark")
})

describe("useTheme", () => {
  it("defaults to system when nothing is stored", () => {
    const { result } = renderHook(() => useTheme())

    expect(result.current.theme).toBe("system")
    expect(result.current.appearance).toBe("light")
    expect(document.documentElement.classList.contains("dark")).toBe(false)
  })

  it("reads the persisted theme on first render", () => {
    window.localStorage.setItem(STORAGE_KEY, "dark")

    const { result } = renderHook(() => useTheme())

    expect(result.current.theme).toBe("dark")
    expect(result.current.appearance).toBe("dark")
    expect(document.documentElement.classList.contains("dark")).toBe(true)
  })

  it("applies the dark class and persists when switching to dark", () => {
    const { result } = renderHook(() => useTheme())

    act(() => result.current.setTheme("dark"))

    expect(document.documentElement.classList.contains("dark")).toBe(true)
    expect(window.localStorage.getItem(STORAGE_KEY)).toBe("dark")
  })

  it("removes the dark class when switching back to light", () => {
    window.localStorage.setItem(STORAGE_KEY, "dark")
    const { result } = renderHook(() => useTheme())

    act(() => result.current.setTheme("light"))

    expect(document.documentElement.classList.contains("dark")).toBe(false)
    expect(window.localStorage.getItem(STORAGE_KEY)).toBe("light")
  })

  it("follows prefers-color-scheme when theme is system", () => {
    const media = setSystemDarkPreference(true)
    const { result } = renderHook(() => useTheme())

    expect(result.current.appearance).toBe("dark")
    expect(document.documentElement.classList.contains("dark")).toBe(true)

    act(() => media.emit(false))

    expect(document.documentElement.classList.contains("dark")).toBe(false)
  })

  it("ignores invalid theme values", () => {
    const { result } = renderHook(() => useTheme())

    act(() => result.current.setTheme("neon"))

    expect(result.current.theme).toBe("system")
  })
})

describe("dark variants", () => {
  it("defaults to navy and applies theme-navy when going dark", () => {
    const { result } = renderHook(() => useTheme())

    act(() => result.current.setTheme("dark"))

    expect(result.current.variant).toBe("navy")
    expect(document.documentElement.classList.contains("theme-navy")).toBe(true)
  })

  it("swaps the theme-* class when the user picks another variant", () => {
    const { result } = renderHook(() => useTheme())
    act(() => result.current.setTheme("dark"))

    act(() => result.current.setVariant("dim"))

    expect(document.documentElement.classList.contains("theme-navy")).toBe(false)
    expect(document.documentElement.classList.contains("theme-dim")).toBe(true)
  })

  it("does not apply any theme-* class while in light mode", () => {
    const { result } = renderHook(() => useTheme())

    act(() => result.current.setVariant("dim"))

    expect(document.documentElement.classList.contains("theme-dim")).toBe(false)
  })

  it("rejects unknown variant names", () => {
    const { result } = renderHook(() => useTheme())

    act(() => result.current.setVariant("hotpink"))

    expect(result.current.variant).toBe("navy")
  })

  it("persists the chosen variant across hook instances", () => {
    const first = renderHook(() => useTheme())
    act(() => first.result.current.setVariant("dim"))
    first.unmount()

    const second = renderHook(() => useTheme())

    expect(second.result.current.variant).toBe("dim")
  })
})

describe("initTheme", () => {
  it("applies the stored appearance synchronously", () => {
    window.localStorage.setItem(STORAGE_KEY, "dark")

    initTheme()

    expect(document.documentElement.classList.contains("dark")).toBe(true)
  })

  it("treats unknown stored values as system", () => {
    window.localStorage.setItem(STORAGE_KEY, "garbage")
    setSystemDarkPreference(true)

    initTheme()

    expect(document.documentElement.classList.contains("dark")).toBe(true)
  })
})
