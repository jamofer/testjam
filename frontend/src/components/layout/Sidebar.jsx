import { NavLink, Link, useMatch } from "react-router-dom"
import { FolderKanban, Users, LogOut, UserCircle, FolderOpen, PlayCircle, ClipboardList, ChevronLeft, Shield } from "lucide-react"
import { useLogout } from "../../hooks/useAuth"
import { useProject } from "../../hooks/useProjects"
import { useExecution } from "../../hooks/useExecutions"
import { useCase, useSuite } from "../../hooks/useSuites"
import { useQuery } from "@tanstack/react-query"
import { plansApi } from "../../api/testplans"

// ── Project-scoped nav items ───────────────────────────────────────────────────

const PROJECT_NAV = [
  { to: (id) => `/projects/${id}`,            icon: FolderOpen,    label: "Test Cases",  end: true },
  { to: (id) => `/projects/${id}/plans`,       icon: ClipboardList, label: "Test Plans"            },
  { to: (id) => `/projects/${id}/executions`,  icon: PlayCircle,    label: "Executions"            },
  { to: (id) => `/projects/${id}/members`,     icon: Shield,        label: "Members"               },
]

const GLOBAL_NAV = [
  { to: "/projects", icon: FolderKanban, label: "Projects"       },
  { to: "/users",    icon: Users,        label: "Users & Groups"  },
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

export function Sidebar({ user }) {
  const logout = useLogout()
  const activeProjectId = useActiveProjectId()
  const { data: project } = useProject(activeProjectId)

  return (
    <aside className="w-56 bg-white border-r border-gray-200 flex flex-col h-full shrink-0">
      <div className="px-6 py-5 text-xl font-bold tracking-tight text-primary-600 border-b border-gray-100 shrink-0">
        Testjam
      </div>

      <nav className="flex-1 px-3 py-4 overflow-y-auto">

        {/* Project context nav */}
        {activeProjectId && (
          <div className="mb-2">
            <Link to="/projects"
              className="flex items-center gap-1.5 px-3 py-1.5 mb-1 text-xs text-gray-400 hover:text-gray-700 rounded-md hover:bg-gray-100 transition-colors">
              <ChevronLeft size={12} /> All projects
            </Link>
            <div className="px-3 py-1 mb-2">
              <p className="font-semibold text-gray-900 text-sm truncate" title={project?.name}>
                {project?.name ?? "…"}
              </p>
            </div>
            <div className="space-y-0.5">
              {PROJECT_NAV.map(({ to, icon: Icon, label, end }) => (
                <NavLink key={label} to={to(activeProjectId)} end={end}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                      isActive
                        ? "bg-primary-50 text-primary-600"
                        : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                    }`}>
                  <Icon size={15} />{label}
                </NavLink>
              ))}
            </div>
            <div className="border-t border-gray-100 my-3" />
          </div>
        )}

        {/* Global nav */}
        <div className="space-y-0.5">
          {GLOBAL_NAV.map(({ to, icon: Icon, label }) => (
            <NavLink key={to} to={to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-primary-50 text-primary-600"
                    : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                }`}>
              <Icon size={15} />{label}
            </NavLink>
          ))}
        </div>
      </nav>

      {/* User section */}
      <div className="border-t border-gray-100 p-3 shrink-0">
        <div className="flex items-center gap-2 px-2 py-2 rounded-lg hover:bg-gray-50 transition-colors">
          <UserAvatar user={user} />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-800 truncate">
              {user?.full_name || user?.username}
            </p>
            {user?.full_name && (
              <p className="text-xs text-gray-400 truncate">@{user.username}</p>
            )}
          </div>
        </div>
        <div className="flex gap-1 mt-1 px-2">
          <Link to="/profile"
            className="flex-1 flex items-center justify-center gap-1.5 px-2 py-1.5 text-xs text-gray-500 hover:text-gray-800 hover:bg-gray-100 rounded-md transition-colors">
            <UserCircle size={13} /> Profile
          </Link>
          <button onClick={logout}
            className="flex-1 flex items-center justify-center gap-1.5 px-2 py-1.5 text-xs text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-md transition-colors">
            <LogOut size={13} /> Logout
          </button>
        </div>
      </div>
    </aside>
  )
}
