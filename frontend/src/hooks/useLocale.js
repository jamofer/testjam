import { useCallback, useEffect, useState } from "react"
import i18n, { SUPPORTED_LOCALES, setLocale as applyLocale } from "../i18n"

export function useLocale() {
  const [locale, setLocaleState] = useState(() => i18n.language || SUPPORTED_LOCALES[0])

  useEffect(() => {
    const onChange = (next) => setLocaleState(next)
    i18n.on("languageChanged", onChange)
    return () => i18n.off("languageChanged", onChange)
  }, [])

  const setLocale = useCallback((next) => {
    applyLocale(next)
  }, [])

  return { locale, setLocale, supported: SUPPORTED_LOCALES }
}
