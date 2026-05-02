import { NavLink } from "react-router-dom"
import { FolderKanban, Users, LogOut } from "lucide-react"
import { useLogout } from "../../hooks/useAuth"

const links = [
  { to: "/projects", icon: FolderKanban, label: "Projects" },
  { to: "/users", icon: Users, label: "Users & Groups" },
]

export function Sidebar() {
  const logout = useLogout()
  return (
    <aside className="w-56 bg-white border-r border-gray-200 flex flex-col min-h-screen">
      <div className="px-6 py-5 text-xl font-bold tracking-tight text-primary-600 border-b border-gray-100">
        Testjam
      </div>
      <nav className="flex-1 px-3 py-4 space-y-1">
        {links.map(({ to, icon: Icon, label }) => (
          <NavLink key={to} to={to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                isActive
                  ? "bg-primary-50 text-primary-600"
                  : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
              }`}>
            <Icon size={16} />{label}
          </NavLink>
        ))}
      </nav>
      <button onClick={logout}
        className="flex items-center gap-3 px-6 py-4 text-sm text-gray-400 hover:text-gray-700 border-t border-gray-100 transition-colors">
        <LogOut size={16} /> Logout
      </button>
    </aside>
  )
}
