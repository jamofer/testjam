import { useCallback, useEffect, useState } from "react"

const THEME_STORAGE_KEY = "testjam.theme"
const VARIANT_STORAGE_KEY = "testjam.theme.variant"

const VALID_THEMES = ["light", "dark", "system"]
export const DARK_VARIANTS = ["default", "navy", "dim"]
const DEFAULT_VARIANT = "navy"

function readStored(key, valid, fallback) {
  if (typeof window === "undefined") return fallback
  const stored = window.localStorage?.getItem(key)
  return valid.includes(stored) ? stored : fallback
}

function systemPrefersDark() {
  if (typeof window === "undefined" || !window.matchMedia) return false
  return window.matchMedia("(prefers-color-scheme: dark)").matches
}

function resolveAppearance(theme) {
  if (theme === "dark") return "dark"
  if (theme === "light") return "light"
  return systemPrefersDark() ? "dark" : "light"
}

function applyAppearance(appearance, variant) {
  if (typeof document === "undefined") return
  const root = document.documentElement
  if (appearance === "dark") root.classList.add("dark")
  else root.classList.remove("dark")
  for (const name of DARK_VARIANTS) root.classList.remove(`theme-${name}`)
  if (appearance === "dark") root.classList.add(`theme-${variant}`)
}

export function useTheme() {
  const [theme, setThemeState] = useState(() => readStored(THEME_STORAGE_KEY, VALID_THEMES, "system"))
  const [variant, setVariantState] = useState(() => readStored(VARIANT_STORAGE_KEY, DARK_VARIANTS, DEFAULT_VARIANT))
  const [appearance, setAppearance] = useState(() => resolveAppearance(readStored(THEME_STORAGE_KEY, VALID_THEMES, "system")))

  useEffect(() => {
    const next = resolveAppearance(theme)
    setAppearance(next)
    applyAppearance(next, variant)
    window.localStorage?.setItem(THEME_STORAGE_KEY, theme)
  }, [theme, variant])

  useEffect(() => {
    window.localStorage?.setItem(VARIANT_STORAGE_KEY, variant)
  }, [variant])

  useEffect(() => {
    if (theme !== "system" || typeof window === "undefined" || !window.matchMedia) return
    const media = window.matchMedia("(prefers-color-scheme: dark)")
    const onChange = () => {
      const next = media.matches ? "dark" : "light"
      setAppearance(next)
      applyAppearance(next, variant)
    }
    media.addEventListener("change", onChange)
    return () => media.removeEventListener("change", onChange)
  }, [theme, variant])

  const setTheme = useCallback((next) => {
    if (!VALID_THEMES.includes(next)) return
    setThemeState(next)
  }, [])

  const setVariant = useCallback((next) => {
    if (!DARK_VARIANTS.includes(next)) return
    setVariantState(next)
  }, [])

  return { theme, appearance, variant, setTheme, setVariant }
}

export function initTheme() {
  const storedTheme = readStored(THEME_STORAGE_KEY, VALID_THEMES, "system")
  const storedVariant = readStored(VARIANT_STORAGE_KEY, DARK_VARIANTS, DEFAULT_VARIANT)
  applyAppearance(resolveAppearance(storedTheme), storedVariant)
}
