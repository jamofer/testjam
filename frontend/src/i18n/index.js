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
import enExecutions from "./locales/en/executions.json"
import enAdmin from "./locales/en/admin.json"
import enUi from "./locales/en/ui.json"
import enEnvironments from "./locales/en/environments.json"
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
import esExecutions from "./locales/es/executions.json"
import esAdmin from "./locales/es/admin.json"
import esUi from "./locales/es/ui.json"
import esEnvironments from "./locales/es/environments.json"
import caCommon from "./locales/ca/common.json"
import caProfile from "./locales/ca/profile.json"
import caAuth from "./locales/ca/auth.json"
import caNav from "./locales/ca/nav.json"
import caProjects from "./locales/ca/projects.json"
import caDashboard from "./locales/ca/dashboard.json"
import caSuites from "./locales/ca/suites.json"
import caCases from "./locales/ca/cases.json"
import caPlans from "./locales/ca/plans.json"
import caVersions from "./locales/ca/versions.json"
import caMembers from "./locales/ca/members.json"
import caExecutions from "./locales/ca/executions.json"
import caAdmin from "./locales/ca/admin.json"
import caUi from "./locales/ca/ui.json"
import caEnvironments from "./locales/ca/environments.json"
import glCommon from "./locales/gl/common.json"
import glProfile from "./locales/gl/profile.json"
import glAuth from "./locales/gl/auth.json"
import glNav from "./locales/gl/nav.json"
import glProjects from "./locales/gl/projects.json"
import glDashboard from "./locales/gl/dashboard.json"
import glSuites from "./locales/gl/suites.json"
import glCases from "./locales/gl/cases.json"
import glPlans from "./locales/gl/plans.json"
import glVersions from "./locales/gl/versions.json"
import glMembers from "./locales/gl/members.json"
import glExecutions from "./locales/gl/executions.json"
import glAdmin from "./locales/gl/admin.json"
import glUi from "./locales/gl/ui.json"
import glEnvironments from "./locales/gl/environments.json"
import euCommon from "./locales/eu/common.json"
import euProfile from "./locales/eu/profile.json"
import euAuth from "./locales/eu/auth.json"
import euNav from "./locales/eu/nav.json"
import euProjects from "./locales/eu/projects.json"
import euDashboard from "./locales/eu/dashboard.json"
import euSuites from "./locales/eu/suites.json"
import euCases from "./locales/eu/cases.json"
import euPlans from "./locales/eu/plans.json"
import euVersions from "./locales/eu/versions.json"
import euMembers from "./locales/eu/members.json"
import euExecutions from "./locales/eu/executions.json"
import euAdmin from "./locales/eu/admin.json"
import euUi from "./locales/eu/ui.json"
import euEnvironments from "./locales/eu/environments.json"

const STORAGE_KEY = "testjam.locale"

export const SUPPORTED_LOCALES = ["en", "es", "ca", "gl", "eu"]
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
    en: { common: enCommon, profile: enProfile, auth: enAuth, nav: enNav, projects: enProjects, dashboard: enDashboard, suites: enSuites, cases: enCases, plans: enPlans, versions: enVersions, members: enMembers, executions: enExecutions, admin: enAdmin, ui: enUi, environments: enEnvironments },
    es: { common: esCommon, profile: esProfile, auth: esAuth, nav: esNav, projects: esProjects, dashboard: esDashboard, suites: esSuites, cases: esCases, plans: esPlans, versions: esVersions, members: esMembers, executions: esExecutions, admin: esAdmin, ui: esUi, environments: esEnvironments },
    ca: { common: caCommon, profile: caProfile, auth: caAuth, nav: caNav, projects: caProjects, dashboard: caDashboard, suites: caSuites, cases: caCases, plans: caPlans, versions: caVersions, members: caMembers, executions: caExecutions, admin: caAdmin, ui: caUi, environments: caEnvironments },
    gl: { common: glCommon, profile: glProfile, auth: glAuth, nav: glNav, projects: glProjects, dashboard: glDashboard, suites: glSuites, cases: glCases, plans: glPlans, versions: glVersions, members: glMembers, executions: glExecutions, admin: glAdmin, ui: glUi, environments: glEnvironments },
    eu: { common: euCommon, profile: euProfile, auth: euAuth, nav: euNav, projects: euProjects, dashboard: euDashboard, suites: euSuites, cases: euCases, plans: euPlans, versions: euVersions, members: euMembers, executions: euExecutions, admin: euAdmin, ui: euUi, environments: euEnvironments },
  },
  lng: detectLocale(),
  fallbackLng: DEFAULT_LOCALE,
  supportedLngs: SUPPORTED_LOCALES,
  ns: ["common", "profile", "auth", "nav", "projects", "dashboard", "suites", "cases", "plans", "versions", "members", "executions", "admin", "ui", "environments"],
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
