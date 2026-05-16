import i18n from "i18next"
import { initReactI18next } from "react-i18next"

import enCommon from "./locales/en/common.json"
import enProfile from "./locales/en/profile.json"
import esCommon from "./locales/es/common.json"
import esProfile from "./locales/es/profile.json"

const STORAGE_KEY = "testjam.locale"

export const SUPPORTED_LOCALES = ["en", "es"]
export const DEFAULT_LOCALE = "en"

function detectLocale() {
  if (typeof window === "undefined") return DEFAULT_LOCALE
  const stored = window.localStorage?.getItem(STORAGE_KEY)
  if (SUPPORTED_LOCALES.includes(stored)) return stored
  const browser = window.navigator?.language?.split("-")[0]
  if (SUPPORTED_LOCALES.includes(browser)) return browser
  return DEFAULT_LOCALE
}

i18n.use(initReactI18next).init({
  resources: {
    en: { common: enCommon, profile: enProfile },
    es: { common: esCommon, profile: esProfile },
  },
  lng: detectLocale(),
  fallbackLng: DEFAULT_LOCALE,
  supportedLngs: SUPPORTED_LOCALES,
  ns: ["common", "profile"],
  defaultNS: "common",
  interpolation: { escapeValue: false },
  returnNull: false,
})

export function setLocale(locale) {
  if (!SUPPORTED_LOCALES.includes(locale)) return
  i18n.changeLanguage(locale)
  window.localStorage?.setItem(STORAGE_KEY, locale)
}

export function getLocale() {
  return i18n.language || DEFAULT_LOCALE
}

export default i18n
