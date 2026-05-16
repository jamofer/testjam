import { useCallback, useEffect, useState } from "react"

const STORAGE_KEY = "testjam.theme"
const VALID_THEMES = ["light", "dark", "system"]

function readStoredTheme() {
  if (typeof window === "undefined") return "system"
  const stored = window.localStorage?.getItem(STORAGE_KEY)
  return VALID_THEMES.includes(stored) ? stored : "system"
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

function applyAppearance(appearance) {
  if (typeof document === "undefined") return
  const root = document.documentElement
  if (appearance === "dark") root.classList.add("dark")
  else root.classList.remove("dark")
}

export function useTheme() {
  const [theme, setThemeState] = useState(readStoredTheme)
  const [appearance, setAppearance] = useState(() => resolveAppearance(readStoredTheme()))

  useEffect(() => {
    const next = resolveAppearance(theme)
    setAppearance(next)
    applyAppearance(next)
    window.localStorage?.setItem(STORAGE_KEY, theme)
  }, [theme])

  useEffect(() => {
    if (theme !== "system" || typeof window === "undefined" || !window.matchMedia) return
    const media = window.matchMedia("(prefers-color-scheme: dark)")
    const onChange = () => {
      const next = media.matches ? "dark" : "light"
      setAppearance(next)
      applyAppearance(next)
    }
    media.addEventListener("change", onChange)
    return () => media.removeEventListener("change", onChange)
  }, [theme])

  const setTheme = useCallback((next) => {
    if (!VALID_THEMES.includes(next)) return
    setThemeState(next)
  }, [])

  return { theme, appearance, setTheme }
}

export function initTheme() {
  applyAppearance(resolveAppearance(readStoredTheme()))
}
