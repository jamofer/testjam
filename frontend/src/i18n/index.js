import i18n from "i18next"
import { initReactI18next } from "react-i18next"

import enCommon from "./locales/en/common.json"
import enProfile from "./locales/en/profile.json"
import enAuth from "./locales/en/auth.json"
import enNav from "./locales/en/nav.json"
import enProjects from "./locales/en/projects.json"
import enDashboard from "./locales/en/dashboard.json"
import enSuites from "./locales/en/suites.json"
import enCases from "./locales/en/cases.json"
import enPlans from "./locales/en/plans.json"
import enVersions from "./locales/en/versions.json"
import enMembers from "./locales/en/members.json"
import esCommon from "./locales/es/common.json"
import esProfile from "./locales/es/profile.json"
import esAuth from "./locales/es/auth.json"
import esNav from "./locales/es/nav.json"
import esProjects from "./locales/es/projects.json"
import esDashboard from "./locales/es/dashboard.json"
import esSuites from "./locales/es/suites.json"
import esCases from "./locales/es/cases.json"
import esPlans from "./locales/es/plans.json"
import esVersions from "./locales/es/versions.json"
import esMembers from "./locales/es/members.json"

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
    en: { common: enCommon, profile: enProfile, auth: enAuth, nav: enNav, projects: enProjects, dashboard: enDashboard, suites: enSuites, cases: enCases, plans: enPlans, versions: enVersions, members: enMembers },
    es: { common: esCommon, profile: esProfile, auth: esAuth, nav: esNav, projects: esProjects, dashboard: esDashboard, suites: esSuites, cases: esCases, plans: esPlans, versions: esVersions, members: esMembers },
  },
  lng: detectLocale(),
  fallbackLng: DEFAULT_LOCALE,
  supportedLngs: SUPPORTED_LOCALES,
  ns: ["common", "profile", "auth", "nav", "projects", "dashboard", "suites", "cases", "plans", "versions", "members"],
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
