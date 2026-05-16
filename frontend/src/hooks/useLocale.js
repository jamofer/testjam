import { useCallback, useEffect, useState } from "react"
import i18n, { SUPPORTED_LOCALES, setLocale as applyLocale } from "../i18n"
import { useUpdateMe } from "./useAuth"

export function useLocale() {
  const [locale, setLocaleState] = useState(() => i18n.language || SUPPORTED_LOCALES[0])
  const updateMe = useUpdateMe()

  useEffect(() => {
    const onChange = (next) => setLocaleState(next)
    i18n.on("languageChanged", onChange)
    return () => i18n.off("languageChanged", onChange)
  }, [])

  const setLocale = useCallback((next) => {
    if (!SUPPORTED_LOCALES.includes(next)) return
    applyLocale(next)
    updateMe.mutate({ locale: next })
  }, [updateMe])

  return { locale, setLocale, supported: SUPPORTED_LOCALES }
}
