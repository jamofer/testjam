import { Outlet, Navigate } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { useMe } from '../../hooks/useAuth'

export function AppLayout() {
  const { data: user, isLoading, isError } = useMe()

  if (isLoading) return <div className="flex items-center justify-center h-screen text-gray-500">Loading…</div>
  if (isError) return <Navigate to="/login" replace />

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50">
      <Sidebar user={user} />
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  )
}
