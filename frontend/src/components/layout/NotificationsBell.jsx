import { useEffect, useState } from "react"
import { createPortal } from "react-dom"
import { Link } from "react-router-dom"
import { Bell, Check, CheckCheck, X } from "lucide-react"
import {
  useNotifications,
  useUnreadCount,
  useMarkRead,
  useMarkAllRead,
  useNotificationsSocket,
} from "../../hooks/useNotifications"
import { fmtDate } from "../../lib/format"

/** Compact icon-only trigger that opens a right-side drawer. */
export function NotificationsBell({ enabled = true }) {
  const [open, setOpen] = useState(false)
  const { data: count } = useUnreadCount()

  useNotificationsSocket(enabled)

  useEffect(() => {
    if (!open) return undefined
    const onKey = (e) => { if (e.key === "Escape") setOpen(false) }
    document.addEventListener("keydown", onKey)
    return () => document.removeEventListener("keydown", onKey)
  }, [open])

  const unread = count?.unread ?? 0

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(o => !o)}
        aria-haspopup="dialog"
        aria-expanded={open}
        aria-label={`Notifications${unread > 0 ? `, ${unread} unread` : ""}`}
        className={`relative w-8 h-8 flex items-center justify-center rounded-md transition-colors ${
          open ? "bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-200" : "text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-800 dark:hover:text-gray-100"
        }`}
      >
        <Bell size={16} />
        {unread > 0 && (
          <span data-testid="unread-badge"
            className="absolute -top-1 -right-1 text-[10px] font-bold bg-rose-500 text-white rounded-full px-1 min-w-[16px] h-[16px] flex items-center justify-center leading-none">
            {unread > 99 ? "99+" : unread}
          </span>
        )}
      </button>

      <NotificationsDrawer open={open} onClose={() => setOpen(false)} />
    </>
  )
}

function NotificationsDrawer({ open, onClose }) {
  const { data: list = [] } = useNotifications()
  const markRead = useMarkRead()
  const markAllRead = useMarkAllRead()

  if (!open) return null

  const unread = list.filter(n => !n.is_read).length

  return createPortal(
    <div className="fixed inset-0 z-[100]" role="dialog" aria-label="Notifications">
      <div
        onClick={onClose}
        className="absolute inset-0 bg-black/20"
      />
      <aside
        className="absolute right-0 top-0 h-full w-full sm:w-96 bg-white dark:bg-gray-900 shadow-xl border-l border-gray-200 dark:border-gray-700 flex flex-col"
      >
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-700 shrink-0">
          <p className="text-sm font-semibold text-gray-800 dark:text-gray-100">Notifications</p>
          <div className="flex items-center gap-3">
            {unread > 0 && (
              <button type="button"
                onClick={() => markAllRead.mutate()}
                className="text-xs text-gray-500 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-100 flex items-center gap-1">
                <CheckCheck size={12} /> Mark all read
              </button>
            )}
            <button type="button"
              onClick={onClose}
              aria-label="Close notifications"
              className="text-gray-400 dark:text-gray-500 hover:text-gray-700 dark:hover:text-gray-200">
              <X size={16} />
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto">
          {list.length === 0 ? (
            <p className="px-4 py-10 text-sm text-gray-400 dark:text-gray-500 text-center">No notifications</p>
          ) : (
            <ul className="divide-y divide-gray-100">
              {list.map(n => (
                <li key={n.id} className={n.is_read ? "" : "bg-rose-50/60"}>
                  <div className="flex items-start gap-2 px-4 py-3">
                    <div className="flex-1 min-w-0">
                      {n.link ? (
                        <Link to={n.link}
                          onClick={() => { if (!n.is_read) markRead.mutate(n.id); onClose() }}
                          className="text-sm text-gray-800 dark:text-gray-100 hover:text-primary-600 block">
                          {n.message}
                        </Link>
                      ) : (
                        <p className="text-sm text-gray-800 dark:text-gray-100">{n.message}</p>
                      )}
                      <p className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">{fmtDate(n.created_at)}</p>
                    </div>
                    {!n.is_read && (
                      <button type="button"
                        onClick={() => markRead.mutate(n.id)}
                        title="Mark as read"
                        className="text-gray-300 dark:text-gray-600 hover:text-gray-600 dark:hover:text-gray-300 mt-0.5">
                        <Check size={14} />
                      </button>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </aside>
    </div>,
    document.body,
  )
}
