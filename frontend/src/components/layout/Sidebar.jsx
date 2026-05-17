import { useEffect, useRef, useState } from "react"
import { NavLink, Link, useMatch } from "react-router-dom"
import { Bug, FolderKanban, Users, LogOut, UserCircle, FolderOpen, LayoutDashboard, PlayCircle, ClipboardList, ChevronLeft, Server, Shield, ChevronUp, Tag, Search, Settings as SettingsIcon, X } from "lucide-react"
import { useTranslation } from "react-i18next"
import { useLogout } from "../../hooks/useAuth"
import { useProject } from "../../hooks/useProjects"
import { useExecution } from "../../hooks/useExecutions"
import { useCase, useSuite } from "../../hooks/useSuites"
import { useQuery } from "@tanstack/react-query"
import { plansApi } from "../../api/testplans"
import { Logo } from "../ui/logo"
import { ThemeToggle } from "../ui/theme-toggle"
import { NotificationsBell } from "./NotificationsBell"

// ── Project-scoped nav items ───────────────────────────────────────────────────

const PROJECT_NAV = [
  { to: (id) => `/projects/${id}`,            icon: LayoutDashboard, labelKey: "project.overview",   end: true },
  { to: (id) => `/projects/${id}/cases`,       icon: FolderOpen,      labelKey: "project.cases"               },
  { to: (id) => `/projects/${id}/plans`,       icon: ClipboardList,   labelKey: "project.plans"               },
  { to: (id) => `/projects/${id}/executions`,  icon: PlayCircle,      labelKey: "project.executions"          },
  { to: (id) => `/projects/${id}/versions`,    icon: Tag,             labelKey: "project.versions"            },
  { to: (id) => `/projects/${id}/environments`, icon: Server,         labelKey: "project.environments"        },
  { to: (id) => `/projects/${id}/bugs`,        icon: Bug,             labelKey: "project.bugs"                },
  { to: (id) => `/projects/${id}/members`,     icon: Shield,          labelKey: "project.members"             },
]

const GLOBAL_NAV = [
  { to: "/projects", icon: FolderKanban, labelKey: "global.projects" },
  { to: "/users",    icon: Users,        labelKey: "global.users"    },
]

// ── Resolve project ID from any route ─────────────────────────────────────────

function useActiveProjectId() {
  // Direct project routes
  const pm1 = useMatch("/projects/:id")
  const pm2 = useMatch("/projects/:id/*")
  const projectId = (pm1 ?? pm2)?.params?.id

  // Execution routes — fetch execution to get project_id
  const em1 = useMatch("/executions/:eid")
  const em2 = useMatch("/executions/:eid/*")
  const executionId = (em1 ?? em2)?.params?.eid
  const { data: execution } = useExecution(projectId ? undefined : executionId)

  // Plan routes — fetch plan to get project_id
  const planM = useMatch("/plans/:pid")
  const planId = (projectId || executionId) ? undefined : planM?.params?.pid
  const { data: plan } = useQuery({
    queryKey: ["plan", parseInt(planId)],
    queryFn: () => plansApi.get(planId),
    enabled: !!planId,
  })

  // Case routes — fetch case → suite → project_id (hits cache if already visited)
  const cm = useMatch("/cases/:cid")
  const caseId = (projectId || executionId || planId) ? undefined : cm?.params?.cid
  const { data: caseData } = useCase(caseId)
  const { data: suite } = useSuite(caseData?.suite_id)

  if (projectId) return projectId
  if (execution?.project_id) return String(execution.project_id)
  if (plan?.project_id) return String(plan.project_id)
  if (suite?.project_id) return String(suite.project_id)
  return null
}

// ── Avatar ────────────────────────────────────────────────────────────────────

function UserAvatar({ user }) {
  const initials = (user?.full_name ?? user?.username ?? "?")
    .split(" ").map(w => w[0]).join("").slice(0, 2).toUpperCase()
  return (
    <div className="w-8 h-8 rounded-full bg-primary-100 text-primary-700 flex items-center justify-center text-xs font-bold shrink-0">
      {initials}
    </div>
  )
}

// ── Sidebar ───────────────────────────────────────────────────────────────────

export function Sidebar({ user, onOpenPalette, mobileOpen = false, onCloseMobile }) {
  const { t } = useTranslation("nav")
  const logout = useLogout()
  const activeProjectId = useActiveProjectId()
  const { data: project } = useProject(activeProjectId)
  const isMac = typeof navigator !== "undefined" && /Mac|iPhone|iPod|iPad/.test(navigator.platform)

  return (
    <aside
      className={`w-56 bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700 dark:border-gray-800 flex flex-col h-full shrink-0 z-50
        fixed inset-y-0 left-0 transform transition-transform duration-200
        md:relative md:translate-x-0
        ${mobileOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"}`}
    >
      <div className="px-5 py-4 border-b border-gray-100 dark:border-gray-800 shrink-0 flex items-center justify-between gap-2">
        <Link to="/projects" className="inline-flex">
          <Logo size={26} />
        </Link>
        <div className="flex items-center gap-1">
          <NotificationsBell enabled={!!user} />
          {onCloseMobile && (
            <button
              type="button"
              aria-label={t("closeMenu")}
              onClick={onCloseMobile}
              className="md:hidden w-8 h-8 flex items-center justify-center rounded-md text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800"
            >
              <X size={16} />
            </button>
          )}
        </div>
      </div>

      {onOpenPalette && (
        <div className="px-3 pt-3">
          <button type="button" onClick={onOpenPalette}
            className="w-full flex items-center gap-2 px-2 py-1.5 rounded-md border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 text-xs text-gray-500 dark:text-gray-400 transition-colors">
            <Search size={13} />
            <span className="flex-1 text-left">{t("search")}</span>
            <kbd className="text-[10px] font-mono bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded px-1 text-gray-400 dark:text-gray-500">
              {isMac ? "⌘K" : "Ctrl K"}
            </kbd>
          </button>
        </div>
      )}

      <nav className="flex-1 px-3 py-4 overflow-y-auto">

        {/* Project context nav */}
        {activeProjectId && (
          <div className="mb-2">
            <Link to="/projects"
              className="flex items-center gap-1.5 px-3 py-1.5 mb-1 text-xs text-gray-400 dark:text-gray-500 hover:text-gray-700 dark:hover:text-gray-200 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
              <ChevronLeft size={12} /> {t("allProjects")}
            </Link>
            <div className="px-3 py-1 mb-2">
              <p className="font-semibold text-gray-900 dark:text-gray-100 text-sm truncate" title={project?.name}>
                {project?.name ?? "…"}
              </p>
            </div>
            <div className="space-y-0.5">
              {PROJECT_NAV.map(({ to, icon: Icon, labelKey, end }) => (
                <NavLink key={labelKey} to={to(activeProjectId)} end={end}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                      isActive
                        ? "bg-primary-50 dark:bg-primary-900/30 text-primary-600 dark:text-primary-300"
                        : "text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-white"
                    }`}>
                  <Icon size={15} />{t(labelKey)}
                </NavLink>
              ))}
            </div>
            <div className="border-t border-gray-100 dark:border-gray-800 my-3" />
          </div>
        )}

        {/* Global nav */}
        <div className="space-y-0.5">
          {GLOBAL_NAV.map(({ to, icon: Icon, labelKey }) => (
            <NavLink key={to} to={to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-primary-50 dark:bg-primary-900/30 text-primary-600 dark:text-primary-300"
                    : "text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-white"
                }`}>
              <Icon size={15} />{t(labelKey)}
            </NavLink>
          ))}
        </div>
      </nav>

      {/* User menu + footer */}
      <UserMenu user={user} logout={logout} isAdmin={!!user?.is_admin} />
    </aside>
  )
}

function UserMenu({ user, logout, isAdmin }) {
  const { t } = useTranslation("nav")
  const [open, setOpen] = useState(false)
  const wrapRef = useRef(null)

  useEffect(() => {
    if (!open) return
    const onDoc = (e) => {
      if (!wrapRef.current?.contains(e.target)) setOpen(false)
    }
    const onKey = (e) => { if (e.key === "Escape") setOpen(false) }
    document.addEventListener("mousedown", onDoc)
    document.addEventListener("keydown", onKey)
    return () => {
      document.removeEventListener("mousedown", onDoc)
      document.removeEventListener("keydown", onKey)
    }
  }, [open])

  return (
    <div ref={wrapRef} className="relative border-t border-gray-100 dark:border-gray-800 p-3 shrink-0 flex items-center gap-1">
      <button
        type="button"
        onClick={() => setOpen(o => !o)}
        aria-haspopup="menu"
        aria-expanded={open}
        className={`flex-1 flex items-center gap-2 px-2 py-2 rounded-lg transition-colors ${
          open ? "bg-gray-100 dark:bg-gray-800" : "hover:bg-gray-50 dark:hover:bg-gray-800"
        }`}
      >
        <UserAvatar user={user} />
        <div className="flex-1 min-w-0 text-left">
          <p className="text-sm font-medium text-gray-800 dark:text-gray-100 truncate">
            {user?.full_name || user?.username}
          </p>
          {user?.full_name && (
            <p className="text-xs text-gray-400 dark:text-gray-500 truncate">@{user.username}</p>
          )}
        </div>
        <ChevronUp size={14}
          className={`text-gray-400 dark:text-gray-500 shrink-0 transition-transform ${open ? "" : "rotate-180"}`} />
      </button>
      {isAdmin && (
        <NavLink to="/settings" title={t("user.settings")}
          className={({ isActive }) => `w-9 h-9 flex items-center justify-center rounded-md transition-colors ${
            isActive
              ? "bg-primary-50 dark:bg-primary-900/30 text-primary-600 dark:text-primary-300"
              : "text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-800 dark:hover:text-gray-100"
          }`}>
          <SettingsIcon size={15} />
        </NavLink>
      )}

      {open && (
        <div role="menu"
          className="absolute bottom-full left-3 right-3 mb-1 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg py-1 z-40">
          <Link to="/profile" role="menuitem" onClick={() => setOpen(false)}
            className="flex items-center gap-2 px-3 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-800">
            <UserCircle size={14} /> {t("user.profile")}
          </Link>
          <div className="my-1 border-t border-gray-100 dark:border-gray-800" />
          <ThemeToggle />
          <div className="my-1 border-t border-gray-100 dark:border-gray-800" />
          <button type="button" role="menuitem"
            onClick={() => { setOpen(false); logout() }}
            className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-red-50 dark:hover:bg-red-900/30 hover:text-red-600 dark:hover:text-red-400">
            <LogOut size={14} /> {t("user.logout")}
          </button>
        </div>
      )}
    </div>
  )
}
