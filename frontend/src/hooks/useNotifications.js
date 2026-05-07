import { useEffect, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { notificationsApi } from '../api/notifications'

const LIST_KEY = ['notifications']
const COUNT_KEY = ['notifications', 'unread-count']

export function useNotifications() {
  return useQuery({
    queryKey: LIST_KEY,
    queryFn: () => notificationsApi.list({ limit: 50 }),
  })
}

export function useUnreadCount() {
  return useQuery({
    queryKey: COUNT_KEY,
    queryFn: notificationsApi.unreadCount,
    refetchOnWindowFocus: true,
  })
}

export function useMarkRead() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: notificationsApi.markRead,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: LIST_KEY })
      qc.invalidateQueries({ queryKey: COUNT_KEY })
    },
  })
}

export function useMarkAllRead() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: notificationsApi.markAllRead,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: LIST_KEY })
      qc.invalidateQueries({ queryKey: COUNT_KEY })
    },
  })
}

export function useNotificationsSocket(enabled) {
  const qc = useQueryClient()
  const wsRef = useRef(null)

  useEffect(() => {
    if (!enabled) return undefined
    const token = localStorage.getItem('token')
    if (!token) return undefined

    const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
    const url = `${proto}://${window.location.host}/api/v1/notifications/ws?token=${encodeURIComponent(token)}`
    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onmessage = (ev) => {
      try {
        const msg = JSON.parse(ev.data)
        if (msg.event !== 'notification' || !msg.data) return
        qc.setQueryData(LIST_KEY, (prev = []) => [msg.data, ...prev])
        qc.setQueryData(COUNT_KEY, (prev = { unread: 0 }) => ({ unread: (prev?.unread ?? 0) + 1 }))
      } catch {
        /* ignore malformed payload */
      }
    }

    return () => {
      try { ws.close() } catch { /* ignore */ }
      wsRef.current = null
    }
  }, [enabled, qc])
}
