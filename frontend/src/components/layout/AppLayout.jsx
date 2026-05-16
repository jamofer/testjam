import { useEffect, useRef, useState } from 'react'
import { Outlet, Navigate, useLocation } from 'react-router-dom'
import { Menu } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { Sidebar } from './Sidebar'
import { CommandPalette } from '../ui/command-palette'
import { useMe, useUpdateMe } from '../../hooks/useAuth'
import { browserTimezone } from '../../lib/format'
import i18n, { setLocale, SUPPORTED_LOCALES } from '../../i18n'

export function AppLayout() {
  const { t } = useTranslation(['nav', 'common'])
  const { data: user, isLoading, isError } = useMe()
  const updateMe = useUpdateMe()
  const detectedTimezoneBootstrapped = useRef(false)
  const [paletteOpen, setPaletteOpen] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const location = useLocation()

  useEffect(() => {
    if (!user || detectedTimezoneBootstrapped.current) return
    if (user.timezone) return
    const detected = browserTimezone()
    if (!detected) return
    detectedTimezoneBootstrapped.current = true
    updateMe.mutate({ timezone: detected })
  }, [user, updateMe])

  useEffect(() => {
    if (!user) return
    if (user.locale && SUPPORTED_LOCALES.includes(user.locale) && user.locale !== i18n.language) {
      setLocale(user.locale)
    }
  }, [user])

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

  useEffect(() => { setMobileOpen(false) }, [location.pathname])

  if (isLoading) return <div className="flex items-center justify-center h-screen text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-950">{t('common:actions.loading')}</div>
  if (isError) return <Navigate to="/login" replace />

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50 dark:bg-gray-950 text-gray-900 dark:text-gray-100">
      <button
        type="button"
        aria-label={t('openMenu')}
        onClick={() => setMobileOpen(true)}
        className="md:hidden fixed top-2.5 left-2.5 z-40 w-9 h-9 flex items-center justify-center rounded-md bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 shadow-sm text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-800"
      >
        <Menu size={18} />
      </button>

      {mobileOpen && (
        <div
          className="md:hidden fixed inset-0 z-40 bg-black/40"
          onClick={() => setMobileOpen(false)}
          aria-hidden="true"
        />
      )}

      <Sidebar
        user={user}
        onOpenPalette={() => setPaletteOpen(true)}
        mobileOpen={mobileOpen}
        onCloseMobile={() => setMobileOpen(false)}
      />

      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
      <CommandPalette open={paletteOpen} onOpenChange={setPaletteOpen} />
    </div>
  )
}
