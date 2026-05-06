import { useEffect, useState } from 'react'
import { Outlet, Navigate } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { CommandPalette } from '../ui/command-palette'
import { useMe } from '../../hooks/useAuth'

export function AppLayout() {
  const { data: user, isLoading, isError } = useMe()
  const [paletteOpen, setPaletteOpen] = useState(false)

  useEffect(() => {
    const onKey = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault()
        setPaletteOpen(o => !o)
      }
    }
    window.addEventListener("keydown", onKey)
    return () => window.removeEventListener("keydown", onKey)
  }, [])

  if (isLoading) return <div className="flex items-center justify-center h-screen text-gray-500">Loading…</div>
  if (isError) return <Navigate to="/login" replace />

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50">
      <Sidebar user={user} onOpenPalette={() => setPaletteOpen(true)} />
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
      <CommandPalette open={paletteOpen} onOpenChange={setPaletteOpen} />
    </div>
  )
}
