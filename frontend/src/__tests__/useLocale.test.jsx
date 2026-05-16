import { describe, it, expect, beforeEach, afterEach, vi } from "vitest"
import { renderHook, act } from "@testing-library/react"

vi.mock("../hooks/useAuth", () => ({
  useUpdateMe: () => ({ mutate: vi.fn() }),
}))

import { useLocale } from "../hooks/useLocale"
import i18n, { DEFAULT_LOCALE, SUPPORTED_LOCALES } from "../i18n"

const STORAGE_KEY = "testjam.locale"

beforeEach(() => {
  window.localStorage.clear()
})

afterEach(async () => {
  await i18n.changeLanguage(DEFAULT_LOCALE)
})

describe("useLocale", () => {
  it("exposes the active locale", () => {
    const { result } = renderHook(() => useLocale())

    expect(result.current.locale).toBe(i18n.language)
  })

  it("switches the i18n language and persists it", async () => {
    const { result } = renderHook(() => useLocale())

    await act(async () => result.current.setLocale("es"))

    expect(result.current.locale).toBe("es")
    expect(i18n.language).toBe("es")
    expect(window.localStorage.getItem(STORAGE_KEY)).toBe("es")
  })

  it("ignores unsupported locales", async () => {
    const { result } = renderHook(() => useLocale())

    await act(async () => result.current.setLocale("xx"))

    expect(result.current.locale).not.toBe("xx")
  })

  it("exposes ca, gl and eu among supported locales", () => {
    expect(SUPPORTED_LOCALES).toEqual(expect.arrayContaining(["ca", "gl", "eu"]))
  })

  it("switches to Catalan and persists it", async () => {
    const { result } = renderHook(() => useLocale())

    await act(async () => result.current.setLocale("ca"))

    expect(result.current.locale).toBe("ca")
    expect(i18n.language).toBe("ca")
    expect(window.localStorage.getItem(STORAGE_KEY)).toBe("ca")
  })
})
